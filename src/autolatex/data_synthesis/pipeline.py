# src/autolatex/data_synthesis/pipeline.py

import os
import json
from crewai import Task, Crew, LLM
from dotenv import load_dotenv

# --- 导入所需模块 ---
from autolatex.tools.document_tools import parse_document  # <-- 已修正
from autolatex.tools.ocr_handler import recognize_image_to_latex
from autolatex.data_synthesis.layout_expert import LayoutExpertAgents
from autolatex.tools.template_tools import TemplateTools

# --- 预加载 .env 配置 ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=False)


def process_single_paper(paper_dir: str, template_name: str):
    """
    处理单篇已经存在的伪论文，将其转换为训练数据对。
    """
    print(f"\n--- 正在处理: {paper_dir} ---")

    try:
        # 假设每个目录下有一个主 .md 文件
        markdown_files = [f for f in os.listdir(paper_dir) if f.endswith('.md')]
        if not markdown_files:
            print(f"  - 警告: 在 {paper_dir} 中未找到 .md 文件，跳过。")
            return
        markdown_path = os.path.join(paper_dir, markdown_files[0])

        # 1. 解析为JSON (现在这行代码可以正确工作了)
        print(f"  - 步骤1: 解析文档 {markdown_path}")
        document_json = parse_document(markdown_path)  # 返回的是一个字典

        # 2. 增强JSON (OCR)
        print("  - 步骤2: 执行OCR并增强JSON")
        for item in document_json.get("content", []):
            if item.get("type") in ["equation", "table"] and "image_path" in item:
                # 路径需要拼接
                full_image_path = os.path.join(paper_dir, item["image_path"])
                if os.path.exists(full_image_path):
                    item["latex"] = recognize_image_to_latex(full_image_path)

        # 3. 调用"排版专家"Agent
        print("  - 步骤3: 调用排版专家Agent生成LaTeX代码")
        agents = LayoutExpertAgents()
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise EnvironmentError("未检测到 DEEPSEEK_API_KEY，请在项目根目录的 .env 文件或环境变量中配置 DeepSeek API Key。")
        layout_llm = LLM(
            model=os.getenv("CREW_LLM_MODEL", "deepseek-chat"),
            api_key=deepseek_api_key,
            base_url=os.getenv("CREW_LLM_BASE_URL", "https://api.deepseek.com"),
        )
        layout_expert = agents.make_layout_expert(layout_llm)

        layout_task = Task(
            description=f"""
            请将以下JSON文档内容，严格按照名为 '{template_name}' 的LaTeX模板进行排版。
            首先，使用你的工具读取 '{template_name}' 模板的内容。
            然后，一步步地将JSON中的内容填充到模板中，生成最终的.tex文件代码。

            这是你需要处理的JSON内容:
            ---
            {json.dumps(document_json, ensure_ascii=False, indent=2)}
            ---
            """,
            expected_output="一个完整的、可以直接编译的LaTeX代码字符串。代码不应包含任何解释性文字或评论。",
            agent=layout_expert
        )
        final_latex_code = Crew(agents=[layout_expert], tasks=[layout_task], verbose=1).kickoff()

        # 4. 保存训练数据对
        print("  - 步骤4: 保存训练数据对")
        paper_id = os.path.basename(paper_dir)
        output_dir = f"data/training_pairs/{paper_id}/"
        os.makedirs(output_dir, exist_ok=True)

        # 修正这里的JSON保存方式
        with open(f"{output_dir}/source.json", 'w', encoding='utf-8') as f:
            json.dump(document_json, f, ensure_ascii=False, indent=2)

        # 修正这里的TEX保存方式
        with open(f"{output_dir}/target.tex", 'w', encoding='utf-8') as f:
            f.write(final_latex_code)

        print(f"--- 成功处理 {paper_id} ---")

    except Exception as e:
        print(f"!!!!!! 处理 {paper_dir} 时发生严重错误: {e} !!!!!!")


def main():
    # 使用计算出的绝对路径
    source_dir = os.path.join(PROJECT_ROOT, "data", "generated_papers")
    target_dir = os.path.join(PROJECT_ROOT, "data", "training_pairs")
    # --- 修改结束 ---

    if not os.path.exists(source_dir):
        # 现在的错误提示会显示完整的、绝对的路径，更容易调试
        print(f"错误：源目录 '{source_dir}' 不存在。请先运行 batch_generate.py 生成伪论文。")
        return

    for paper_id in os.listdir(source_dir):
        paper_path = os.path.join(source_dir, paper_id)
        if not os.path.isdir(paper_path):
            continue

        if os.path.exists(os.path.join(target_dir, paper_id)):
            print(f"跳过已处理的论文: {paper_id}")
            continue

        process_single_paper(paper_path, template_name="ieee_conference")


if __name__ == "__main__":
    main()