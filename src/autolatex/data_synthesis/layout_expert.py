# src/autolatex/data_synthesis/layout_expert.py

from crewai import Agent
from autolatex.tools.template_tools import TemplateTools

class LayoutExpertAgents:
    def make_layout_expert(self, llm):
        template_tool = TemplateTools()
        return Agent(
            role="LaTeX 排版专家 (LaTeX Layout Expert)",
            goal="""将一份结构化的JSON文档，根据指定的期刊LaTeX模板，转换成一个完整且语法正确的.tex文件。
                  你必须精确地将JSON中的每一个部分（标题、作者、摘要、章节、公式、图表等）映射到模板的相应命令中。""",
            backstory="""你是一位经验丰富的科研出版专家，精通各种主流学术期刊（如IEEE, ACM, Springer）的LaTeX模板。
                         你的工作是自动化论文版流程，确保输出的.tex文件无需任何手动修改即可直接编译成PDF。
                         你对细节有极致的追求，尤其是公式、表格和引文的格式。""",
            verbose=True,
            allow_delegation=False,
            tools=[template_tool],
            llm=llm
        )