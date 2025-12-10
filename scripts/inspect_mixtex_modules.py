from transformers import VisionEncoderDecoderModel


def main():
    model_name = "MixTex/ZhEn-Latex-OCR"
    print(f"Loading model: {model_name}")
    model = VisionEncoderDecoderModel.from_pretrained(model_name)

    print("\n=== First 200 module names (for figuring out LoRA target_modules) ===")
    for i, (name, module) in enumerate(model.named_modules()):
        print(i, ":", name, "->", module.__class__.__name__)
        if i >= 199:
            break


if __name__ == "__main__":
    main()









