"""
真正的 QLoRA 微调脚本：

- 使用 MixTex/ZhEn-Latex-OCR 作为基础模型（VisionEncoderDecoderModel）。
- 从 linxy/LaTeX_OCR 数据集加载图像 + LaTeX 文本作为训练样本。
- 通过 bitsandbytes 将基础模型以 4bit 量化的方式加载。
- 利用 PEFT/LoRA 仅训练少量适配层，降低显存占用。
- 支持梯度累积、余弦学习率调度、BF16/FP16 自动混合精度。

运行前准备：
    pip install -r requirements.txt
    pip install bitsandbytes peft accelerate
    （确保有一块 24GB 左右显存的 GPU，QLoRA 仍依赖 CUDA）

推荐先用「保守配置 + 小规模 debug」验证，再放大样本数：
    # Debug 小试运行（建议先跑这个，确认不会把基线模型拉坏）
    python scripts/finetune_mixtex_qlora.py ^
        --subset-name small ^
        --max-train-samples 500 ^
        --output-dir checkpoints/mixtex_qlora_debug ^
        --num-epochs 1 ^
        --train-batch-size 2 ^
        --gradient-accumulation-steps 16 ^
        --learning-rate 3e-5 ^
        --warmup-ratio 0.1

    # 正式 10k 训练（在 debug 效果 OK 后再跑）
    python scripts/finetune_mixtex_qlora.py ^
        --subset-name full ^
        --max-train-samples 10000 ^
        --output-dir checkpoints/mixtex_qlora ^
        --num-epochs 2 ^
        --train-batch-size 2 ^
        --gradient-accumulation-steps 32 ^
        --learning-rate 3e-5 ^
        --warmup-ratio 0.1

运行后会在 output-dir 下保存：
    - epoch_X/ : 每个 epoch 的 LoRA 适配器权重
    - training_history.json : Loss 记录
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
from PIL import Image
from datasets import load_dataset
from torch.utils.data import Dataset, DataLoader
from tqdm.auto import tqdm
try:
    import requests
except ImportError:
    requests = None
from transformers import (
    AutoImageProcessor,
    AutoTokenizer,
    BitsAndBytesConfig,
    VisionEncoderDecoderModel,
    get_cosine_schedule_with_warmup,
)

from peft import (
    LoraConfig,
    PeftModel,
    TaskType,
    get_peft_model,
    prepare_model_for_kbit_training,
)


# 默认将 HuggingFace 访问改为国内镜像，避免直连失败
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

@dataclass
class TrainConfig:
    # 数据 / 模型
    model_name: str = "MixTex/ZhEn-Latex-OCR"
    local_model_path: Optional[str] = None  # 如果提供，直接使用本地路径，避免网络连接
    local_dataset_path: Optional[str] = None  # 如果提供，直接使用本地数据集路径，避免网络连接
    subset_name: str = "small"
    split: str = "train"
    max_train_samples: Optional[int] = 1000

    # 训练
    output_dir: str = "checkpoints/mixtex_qlora"
    num_epochs: int = 1
    train_batch_size: int = 2
    # 之前使用 2e-4 在 10k 小样本上容易破坏基线能力，这里默认更保守的 3e-5
    learning_rate: float = 3e-5
    weight_decay: float = 0.0
    # 稍长一点的 warmup，有利于前期稳定
    warmup_ratio: float = 0.10
    gradient_accumulation_steps: int = 16
    max_length: int = 256
    log_every_n_steps: int = 25

    # 精度 / 设备
    mixed_precision: str = "bf16"  # choices: none | fp16 | bf16
    gradient_checkpointing: bool = True
    seed: int = 42

    # QLoRA 专属
    use_qlora: bool = True
    load_in_4bit: bool = True
    bnb_quant_type: str = "nf4"
    bnb_compute_dtype: str = "bfloat16"
    bnb_use_double_quant: bool = True

    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "out_proj",
            "fc1",
            "fc2",
            "dense",
        ]
    )

    # 持久化配置
    resume_from_checkpoint: Optional[str] = None
    save_steps: int = 0  # >0 时在训练过程中按步保存临时 checkpoint


class LatexOCRDataset(Dataset):
    """简单的图像 + LaTeX 文本数据集封装，用于 DataLoader。"""

    def __init__(self, items: List[Dict]):
        self.items = items

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        sample = self.items[idx]
        return {"image": sample["image"], "text": sample["text"]}


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_latexo_cr_subset(cfg: TrainConfig) -> List[Dict]:
    """加载 linxy/LaTeX_OCR 子集，并返回 PIL Image + 文本。"""

    # 优先使用本地数据集路径，避免网络连接问题
    if cfg.local_dataset_path:
        print(
            f"[DATA] Loading dataset from local path: {cfg.local_dataset_path}, "
            f"subset={cfg.subset_name}, split={cfg.split}"
        )
        # 从本地路径加载数据集
        ds = load_dataset(cfg.local_dataset_path, name=cfg.subset_name, split=cfg.split)
    else:
        print(
            f"[DATA] Loading linxy/LaTeX_OCR subset={cfg.subset_name}, split={cfg.split} "
            f"(will use cache if available)"
        )
        try:
            # 尝试加载数据集，会自动使用本地缓存
            ds = load_dataset(
                "linxy/LaTeX_OCR", 
                name=cfg.subset_name, 
                split=cfg.split
            )
        except Exception as e:
            # 检查是否是网络连接错误
            error_str = str(e).lower()
            is_connection_error = (
                "connection" in error_str or
                "连接" in error_str or
                "10054" in error_str or
                "connectionreset" in error_str or
                "connection aborted" in error_str
            )
            
            if is_connection_error:
                print(f"[WARN] 网络连接失败: {e}")
                print("[INFO] 尝试强制使用本地缓存（离线模式）...")
                try:
                    # 使用离线模式强制使用本地缓存
                    from datasets import DownloadConfig
                    download_config = DownloadConfig(
                        local_files_only=True  # 只使用本地文件，不进行网络请求
                    )
                    ds = load_dataset(
                        "linxy/LaTeX_OCR", 
                        name=cfg.subset_name, 
                        split=cfg.split,
                        download_config=download_config
                    )
                    print("[INFO] 成功从本地缓存加载数据集！")
                except Exception as e2:
                    print(f"[ERROR] 无法从本地缓存加载: {e2}")
                    print("[INFO] 解决方案：")
                    print("  1. 确保数据集已下载到本地缓存")
                    print("  2. 或使用 --local-dataset-path 参数指定本地数据集路径")
                    print("  3. 数据集缓存通常在: C:\\Users\\Ding\\.cache\\huggingface\\datasets\\")
                    raise
            else:
                # 其他错误直接抛出
                raise
    
    # ---------> START: 关键修复代码 - 先洗牌 <---------
    print(f"[DATA] Shuffling the dataset with seed={cfg.seed}...")
    ds = ds.shuffle(seed=cfg.seed)
    print("[DATA] Shuffle complete.")
    # ---------> END: 关键修复代码 <---------
    
    total = len(ds)
    if total == 0:
        raise RuntimeError("Dataset is empty. Check subset/split.")

    limit = (
        min(cfg.max_train_samples, total)
        if cfg.max_train_samples is not None
        else total
    )
    ds = ds.select(range(limit))

    items: List[Dict] = []
    for row in ds:
        image = row["image"]
        if not isinstance(image, Image.Image):
            image = Image.fromarray(image)
        items.append(
            {
                "image": image.convert("RGB"),
                "text": row["text"].strip(),
            }
        )

    print(f"[DATA] Loaded {len(items)} samples.")
    return items


def make_collate_fn(tokenizer, feature_extractor, max_length: int):
    def collate(batch: List[Dict]):
        images = [b["image"] for b in batch]
        texts = [b["text"] for b in batch]

        pixel_values = feature_extractor(images=images, return_tensors="pt").pixel_values

        tokenized = tokenizer(
            texts,
            padding="max_length",
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )

        labels = tokenized.input_ids
        attention_mask = tokenized.attention_mask

        # 将 padding 位置标记为 -100，使其在 loss 计算中被忽略；
        # 同时保留 attention_mask 供 decoder 使用，避免模型关注到 padding token。
        labels[labels == tokenizer.pad_token_id] = -100
        return {
            "pixel_values": pixel_values,
            "labels": labels,
            "attention_mask": attention_mask,
        }

    return collate


def get_amp_settings(cfg: TrainConfig, use_cuda: bool):
    if not use_cuda:
        return False, None, None
    mp = cfg.mixed_precision.lower()
    if mp == "bf16":
        return True, torch.bfloat16, None  # scaler not needed
    if mp == "fp16":
        return True, torch.float16, torch.cuda.amp.GradScaler()
    return False, None, None


def build_model_and_tokenizer(cfg: TrainConfig):
    # 优先使用本地路径，避免网络连接问题
    model_path = cfg.local_model_path if cfg.local_model_path else cfg.model_name
    if cfg.local_model_path:
        print(f"[MODEL] Using local model path: {model_path}")
    else:
        print(f"[MODEL] Loading from HuggingFace Hub: {model_path} (will use cache if available)")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    image_processor = AutoImageProcessor.from_pretrained(model_path)

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    # Tokenizer 配置自检，方便排查 PAD/EOS/BOS 相关问题
    print(
        "[TOKENIZER] PAD token: %r (id=%s), EOS token: %r (id=%s), BOS token: %r (id=%s)"
        % (
            getattr(tokenizer, "pad_token", None),
            getattr(tokenizer, "pad_token_id", None),
            getattr(tokenizer, "eos_token", None),
            getattr(tokenizer, "eos_token_id", None),
            getattr(tokenizer, "bos_token", None),
            getattr(tokenizer, "bos_token_id", None),
        )
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        print(
            f"[TOKENIZER] pad_token is None, set pad_token to eos_token: {tokenizer.pad_token!r} "
            f"(id={tokenizer.pad_token_id})"
        )

    load_kwargs = {}
    # QLoRA (4bit) 模式：需要 bitsandbytes + CUDA
    if cfg.use_qlora and cfg.load_in_4bit:
        if not use_cuda:
            raise EnvironmentError(
                "QLoRA 4bit 量化需要 CUDA/GPU 环境。\n"
                "解决方案：使用 --no-4bit 参数禁用 4bit 量化，使用普通 LoRA 训练。"
            )
        
        # 检查 bitsandbytes 是否安装
        try:
            import bitsandbytes
        except ImportError:
            raise ImportError(
                "bitsandbytes 未安装。QLoRA 4bit 量化需要 bitsandbytes 库。\n"
                "解决方案：\n"
                "  1. 使用 --no-4bit 参数禁用 4bit 量化（推荐，适合 CPU 环境）\n"
                "  2. 或安装 bitsandbytes: pip install bitsandbytes（需要 CUDA GPU）"
            )

        compute_dtype = (
            torch.bfloat16 if cfg.bnb_compute_dtype == "bfloat16" else torch.float16
        )

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=cfg.bnb_use_double_quant,
            bnb_4bit_quant_type=cfg.bnb_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
        )
        load_kwargs.update(
            {
                "quantization_config": quant_config,
                "device_map": "auto",
            }
        )

    print("[MODEL] Loading base VisionEncoderDecoderModel...")
    model = VisionEncoderDecoderModel.from_pretrained(model_path, **load_kwargs)

    # ---------> START: 关键修复代码 - 设置解码器起始符ID <---------
    if model.config.decoder_start_token_id is None:
        if tokenizer.bos_token_id is None:
            raise ValueError(
                "Tokenizer 需要一个 bos_token_id，但它是 None。"
                "请检查 tokenizer 配置。"
            )
        print(
            f"[CONFIG] model.config.decoder_start_token_id 是 None。"
            f"设置为 tokenizer.bos_token_id: {tokenizer.bos_token_id}"
        )
        model.config.decoder_start_token_id = tokenizer.bos_token_id
    else:
        print(
            f"[CONFIG] model.config.decoder_start_token_id 已定义为: "
            f"{model.config.decoder_start_token_id}"
        )
    # ---------> END: 关键修复代码 <---------

    # 确保 pad_token_id 也正确设置
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False

    if cfg.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    # LoRA 适配：
    # - 4bit QLoRA：依赖 bitsandbytes，目前主要用于 Linux 环境；
    # - 非 4bit 的普通 LoRA：仅在 decoder 上挂 LoRA，encoder 仍保持全参。
    if cfg.use_qlora:
        # 这里只在文本解码器上应用 LoRA，避免破坏 VisionEncoderDecoderModel 的调用签名。
        decoder = model.decoder
        decoder = prepare_model_for_kbit_training(
            decoder, use_gradient_checkpointing=cfg.gradient_checkpointing
        )

        lora_config = LoraConfig(
            r=cfg.lora_r,
            lora_alpha=cfg.lora_alpha,
            lora_dropout=cfg.lora_dropout,
            bias="none",
            task_type=TaskType.SEQ_2_SEQ_LM,
            target_modules=cfg.lora_target_modules,
        )

        decoder = get_peft_model(decoder, lora_config)
        decoder.print_trainable_parameters()
        model.decoder = decoder
        
        # 明确冻结encoder，确保只有decoder的LoRA适配器可训练
        for name, param in model.encoder.named_parameters():
            param.requires_grad = False
        print("[MODEL] Encoder已冻结，只有decoder的LoRA适配器可训练")

    # 如果不是 4bit QLoRA（即普通 LoRA 或全参训练），明确将模型放到 device 上；
    # 4bit QLoRA 场景下交给 bitsandbytes 的 device_map="auto" 处理。
    if not (cfg.use_qlora and cfg.load_in_4bit):
        model.to(device)

    return model, tokenizer, image_processor


def train(cfg: TrainConfig):
    os.makedirs(cfg.output_dir, exist_ok=True)
    set_seed(cfg.seed)

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    if use_cuda:
        torch.backends.cuda.matmul.allow_tf32 = True

    items = load_latexo_cr_subset(cfg)
    dataset = LatexOCRDataset(items)

    model, tokenizer, image_processor = build_model_and_tokenizer(cfg)

    start_epoch = 0
    if cfg.resume_from_checkpoint:
        ckpt_path = Path(cfg.resume_from_checkpoint)
        if not ckpt_path.exists():
            raise FileNotFoundError(f"指定的 checkpoint 不存在: {ckpt_path}")
        print(f"[RESUME] Loading LoRA weights from {ckpt_path}")
        
        # 从checkpoint恢复时，只加载decoder的LoRA适配器权重
        # 避免对整个model进行重新包装，防止encoder forward参数传递问题
        if cfg.use_qlora:
            # LoRA模式下，decoder已经是PeftModel
            # 优先尝试 load_adapter；若需 adapter_name，使用默认名称 "default"
            if hasattr(model.decoder, "load_adapter"):
                try:
                    model.decoder.load_adapter(str(ckpt_path), adapter_name="default", is_trainable=True)
                except TypeError:
                    # 兼容老版本签名 (path, adapter_name)
                    model.decoder.load_adapter(str(ckpt_path), "default")
            else:
                # 旧版本PEFT：重新构造 PeftModel
                base_decoder = model.decoder.base_model if hasattr(model.decoder, "base_model") else model.decoder
                model.decoder = PeftModel.from_pretrained(base_decoder, str(ckpt_path), is_trainable=True)
        else:
            # 非LoRA模式，直接加载整个模型
            model = PeftModel.from_pretrained(model, str(ckpt_path), is_trainable=True)
        
        # 重新冻结encoder（防止resume时encoder被意外解冻）
        if cfg.use_qlora:
            for name, param in model.encoder.named_parameters():
                param.requires_grad = False
            print("[RESUME] Encoder已重新冻结")
        
        try:
            if ckpt_path.name.startswith("epoch_"):
                start_epoch = int(ckpt_path.name.split("_")[-1])
        except ValueError:
            start_epoch = 0

    collate_fn = make_collate_fn(
        tokenizer=tokenizer,
        feature_extractor=image_processor,
        max_length=cfg.max_length,
    )

    dataloader = DataLoader(
        dataset,
        batch_size=cfg.train_batch_size,
        shuffle=True,
        num_workers=4 if os.name != "nt" else 0,
        pin_memory=use_cuda,
        collate_fn=collate_fn,
    )

    # 优化器 & 学习率调度
    # 只优化可训练参数（LoRA适配器），确保encoder被冻结
    if cfg.use_qlora:
        # LoRA模式下，只优化decoder的可训练参数
        trainable_params = [p for p in model.parameters() if p.requires_grad]
        # 确保encoder参数被冻结
        for name, param in model.named_parameters():
            if 'encoder' in name:
                param.requires_grad = False
        trainable_params = [p for p in model.parameters() if p.requires_grad]
        print(f"[OPTIMIZER] 可训练参数数量: {len(trainable_params)}")
        if len(trainable_params) == 0:
            raise RuntimeError("没有可训练参数！请检查LoRA配置。")
        optimizer = torch.optim.AdamW(
            trainable_params,
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay,
        )
    else:
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay,
        )

    total_steps = (
        math.ceil(len(dataloader) / cfg.gradient_accumulation_steps) * cfg.num_epochs
    )
    warmup_steps = int(total_steps * cfg.warmup_ratio)
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    use_amp, amp_dtype, scaler = get_amp_settings(cfg, use_cuda)

    training_history = {
        "config": asdict(cfg),
        "loss_history": [],
        "epoch_losses": [],
    }

    global_step = 0
    completed_epochs = start_epoch

    if cfg.resume_from_checkpoint:
        state_file = Path(cfg.resume_from_checkpoint).parent / "training_state.json"
        if state_file.exists():
            try:
                state_data = json.loads(state_file.read_text(encoding="utf-8"))
                global_step = state_data.get("global_step", global_step)
                completed_epochs = state_data.get("completed_epochs", completed_epochs)
            except json.JSONDecodeError:
                print(f"[WARN] 无法解析 {state_file}，global_step 将从 0 重新计数。")
        else:
            print("[INFO] 未找到 training_state.json，global_step 将从 0 重新计数。")

    def save_checkpoint(tag: str):
        save_dir = Path(cfg.output_dir) / tag
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果使用LoRA，只保存decoder的LoRA适配器权重
        if cfg.use_qlora and hasattr(model.decoder, 'save_pretrained'):
            # LoRA适配器在decoder上，保存decoder的LoRA权重
            model.decoder.save_pretrained(save_dir)
        else:
            # 全量模型，保存整个模型
            model.save_pretrained(save_dir)
        
        tokenizer.save_pretrained(save_dir)
        image_processor.save_pretrained(save_dir)
        with open(Path(cfg.output_dir) / "last_checkpoint.txt", "w", encoding="utf-8") as f:
            f.write(str(save_dir.resolve()))
        print(f"[CHECKPOINT] Saved adapter to {save_dir}")

    if start_epoch >= cfg.num_epochs:
        print(
            f"[INFO] 检测到 resume_from_checkpoint={cfg.resume_from_checkpoint} "
            "已经完成目标 epoch 数，若需继续训练请提高 --num-epochs。"
        )

    # 训练前验证：检查模型参数状态
    if cfg.use_qlora:
        trainable_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_count = sum(p.numel() for p in model.parameters())
        print(f"[VERIFY] 可训练参数: {trainable_count:,} / 总参数: {total_count:,} ({100*trainable_count/total_count:.2f}%)")
        encoder_trainable = sum(p.numel() for name, p in model.encoder.named_parameters() if p.requires_grad)
        if encoder_trainable > 0:
            print(f"[WARN] Encoder有 {encoder_trainable:,} 个可训练参数，应该被冻结！")
        else:
            print("[VERIFY] ✓ Encoder已正确冻结")

    for epoch in range(start_epoch, cfg.num_epochs):
        model.train()
        epoch_loss = 0.0
        progress = tqdm(dataloader, desc=f"Epoch {epoch + 1}/{cfg.num_epochs}")

        optimizer.zero_grad()

        for step, batch in enumerate(progress):
            pixel_values = batch["pixel_values"].to(device, non_blocking=True)
            labels = batch["labels"].to(device, non_blocking=True)
            attention_mask = batch["attention_mask"].to(device, non_blocking=True)

            # 使用新的autocast API（兼容旧版本）
            if hasattr(torch.amp, 'autocast'):
                autocast_context = torch.amp.autocast('cuda', enabled=use_amp, dtype=amp_dtype)
            else:
                autocast_context = torch.cuda.amp.autocast(enabled=use_amp, dtype=amp_dtype)
            
            with autocast_context:
                # 显式传入 decoder_attention_mask，避免 decoder 将 padding token 当作有效输入。
                outputs = model(
                    pixel_values=pixel_values,
                    labels=labels,
                    decoder_attention_mask=attention_mask,
                )
                loss = outputs.loss
                # 保存原始loss用于统计
                raw_loss = loss.item()
                # 除以gradient_accumulation_steps用于梯度累积
                loss = loss / cfg.gradient_accumulation_steps

            if scaler is not None:
                scaler.scale(loss).backward()
            else:
                loss.backward()

            # 累加原始loss用于统计（不是除以gradient_accumulation_steps的loss）
            epoch_loss += raw_loss

            if (step + 1) % cfg.gradient_accumulation_steps == 0:
                if scaler is not None:
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1

            if global_step > 0 and global_step % cfg.log_every_n_steps == 0:
                avg_loss = epoch_loss / (step + 1)
                progress.set_postfix({"loss": f"{avg_loss:.4f}"})
                training_history["loss_history"].append(
                    {
                        "epoch": epoch + 1,
                        "step": step + 1,
                        "global_step": global_step,
                        "loss": raw_loss,  # 使用原始loss
                        "avg_loss": avg_loss,
                    }
                )

            if cfg.save_steps > 0 and global_step > 0 and global_step % cfg.save_steps == 0:
                save_checkpoint(f"step_{global_step}")

        avg_epoch_loss = epoch_loss / max(1, len(dataloader))
        training_history["epoch_losses"].append(
            {"epoch": epoch + 1, "avg_loss": avg_epoch_loss}
        )
        print(f"[EPOCH] {epoch + 1} average loss: {avg_epoch_loss:.4f}")

        save_checkpoint(f"epoch_{epoch + 1}")
        completed_epochs = epoch + 1

    history_path = Path(cfg.output_dir) / "training_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(training_history, f, indent=2, ensure_ascii=False)
    print(f"[DONE] Training history saved to {history_path}")

    state_path = Path(cfg.output_dir) / "training_state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "completed_epochs": completed_epochs,
                "global_step": global_step,
                "last_checkpoint": Path(cfg.output_dir, f"epoch_{completed_epochs}").as_posix(),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"[DONE] Training state saved to {state_path}")


def parse_args() -> TrainConfig:
    parser = argparse.ArgumentParser(
        description="QLoRA finetuning for MixTex/ZhEn-Latex-OCR on linxy/LaTeX_OCR dataset"
    )
    parser.add_argument("--model-name", default=TrainConfig.model_name, help="HuggingFace Hub 模型名称，例如 'MixTex/ZhEn-Latex-OCR'")
    parser.add_argument("--local-model-path", type=str, default=None, help="本地模型路径（如果提供，将优先使用本地路径，避免网络连接问题）")
    parser.add_argument("--local-dataset-path", type=str, default=None, help="本地数据集路径（如果提供，将优先使用本地路径，避免网络连接问题）")
    parser.add_argument("--subset-name", default=TrainConfig.subset_name)
    parser.add_argument("--split", default=TrainConfig.split)
    parser.add_argument("--max-train-samples", type=int, default=TrainConfig.max_train_samples)
    parser.add_argument("--output-dir", default=TrainConfig.output_dir)
    parser.add_argument("--num-epochs", type=int, default=TrainConfig.num_epochs)
    parser.add_argument("--train-batch-size", type=int, default=TrainConfig.train_batch_size)
    parser.add_argument("--learning-rate", type=float, default=TrainConfig.learning_rate)
    parser.add_argument("--weight-decay", type=float, default=TrainConfig.weight_decay)
    parser.add_argument("--warmup-ratio", type=float, default=TrainConfig.warmup_ratio)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=TrainConfig.gradient_accumulation_steps)
    parser.add_argument("--max-length", type=int, default=TrainConfig.max_length)
    parser.add_argument("--log-every-n-steps", type=int, default=TrainConfig.log_every_n_steps)
    parser.add_argument("--mixed-precision", choices=["none", "fp16", "bf16"], default=TrainConfig.mixed_precision)
    parser.add_argument("--no-gradient-checkpointing", action="store_true")
    parser.add_argument("--seed", type=int, default=TrainConfig.seed)
    parser.add_argument("--lora-r", type=int, default=TrainConfig.lora_r)
    parser.add_argument("--lora-alpha", type=int, default=TrainConfig.lora_alpha)
    parser.add_argument("--lora-dropout", type=float, default=TrainConfig.lora_dropout)
    parser.add_argument(
        "--lora-target-modules",
        type=str,
        default=",".join(TrainConfig().lora_target_modules),
        help="逗号分隔的模块名列表，例如 q_proj,k_proj,v_proj,o_proj,fc1,fc2,out_proj",
    )
    parser.add_argument("--no-qlora", action="store_true", help="调试用途：禁用QLoRA，直接全参训练")
    parser.add_argument("--no-4bit", action="store_true", help="禁用4bit量化（QLoRA模式下不建议）")
    parser.add_argument("--bnb-quant-type", default=TrainConfig.bnb_quant_type, choices=["nf4", "fp4"])
    parser.add_argument("--bnb-compute-dtype", default=TrainConfig.bnb_compute_dtype, choices=["bfloat16", "float16"])
    parser.add_argument("--bnb-no-double-quant", action="store_true")
    parser.add_argument("--resume-from-checkpoint", type=str, default=None, help="设置为某个 epoch_x 目录以继续训练")
    parser.add_argument("--save-steps", type=int, default=TrainConfig.save_steps, help="每隔多少 global steps 保存一次临时 checkpoint (0 表示不保存)")

    args = parser.parse_args()
    cfg = TrainConfig()
    cfg.model_name = args.model_name
    cfg.local_model_path = args.local_model_path
    cfg.local_dataset_path = args.local_dataset_path
    cfg.subset_name = args.subset_name
    cfg.split = args.split
    cfg.max_train_samples = args.max_train_samples
    cfg.output_dir = args.output_dir
    cfg.num_epochs = args.num_epochs
    cfg.train_batch_size = args.train_batch_size
    cfg.learning_rate = args.learning_rate
    cfg.weight_decay = args.weight_decay
    cfg.warmup_ratio = args.warmup_ratio
    cfg.gradient_accumulation_steps = args.gradient_accumulation_steps
    cfg.max_length = args.max_length
    cfg.log_every_n_steps = args.log_every_n_steps
    cfg.mixed_precision = args.mixed_precision
    cfg.gradient_checkpointing = not args.no_gradient_checkpointing
    cfg.seed = args.seed
    cfg.use_qlora = not args.no_qlora
    cfg.load_in_4bit = not args.no_4bit
    cfg.lora_r = args.lora_r
    cfg.lora_alpha = args.lora_alpha
    cfg.lora_dropout = args.lora_dropout
    cfg.lora_target_modules = [m.strip() for m in args.lora_target_modules.split(",") if m.strip()]
    cfg.bnb_quant_type = args.bnb_quant_type
    cfg.bnb_compute_dtype = args.bnb_compute_dtype
    cfg.bnb_use_double_quant = not args.bnb_no_double_quant
    cfg.resume_from_checkpoint = args.resume_from_checkpoint
    cfg.save_steps = args.save_steps

    return cfg


if __name__ == "__main__":
    cfg = parse_args()
    train(cfg)


