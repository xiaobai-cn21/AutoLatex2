from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .model import DocumentStructure, EquationList 
from autolatex.tools.document_tools import DocumentParserTool, LaTeXCompilerTool
from autolatex.tools.ocr_tool import DeepSeekOCRTool
from autolatex.tools.knowledge_tools import KnowledgeBaseSearchTool

@CrewBase
class Autolatex():
    """Autolatex crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
     # 实例化工具 (也可以在 agent 方法内部实例化，看个人喜好)
    doc_parsing_tool = DocumentParserTool()
    

    #-------------------Agent定义-------------------

    # --- 1. 文档解析 Agent ---
    @agent
    def doc_parser_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['doc_parser_agent'],
            verbose=True,
            # 提示：这里未来需要加读取文件的工具，例如：
            tools=[DocumentParserTool()] 
        )

    # --- 2. 模版研究 Agent ---
    @agent
    def template_researcher_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['template_researcher_agent'],
            verbose=True,
            # 使用知识库搜索工具来查找 LaTeX 模板
            tools=[KnowledgeBaseSearchTool()] 
        )

    # --- 3. LaTeX 排版 Agent ---
    @agent
    def latex_coder_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['latex_coder_agent'],
            verbose=True,
            # 这个 Agent 主要靠 LLM 生成代码，可能不需要外部工具，但为了写入文件可能需要 FileWriteTool
            allow_delegation=False
        )

    # --- 4. LaTeX 编译调试 Agent ---
    @agent
    def latex_debugger_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['latex_debugger_agent'],
            verbose=True,
            # 提示：这个 Agent 必须有执行编译命令的工具
            tools=[LaTeXCompilerTool()] 
        )
    
    # --- 5. deepseek-OCR调用agent ---
    @agent
    def latex_equation_form_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['latex_equation_form_agent'],
            # 关键点：这里必须给它一个能调用 DeepSeek OCR API 的工具
            tools=[DeepSeekOCRTool()], 
            verbose=True
        )
    




    #-------------------任务定义-------------------

    @task
    def doc_parsing_task(self) -> Task:
        return Task(
            config=self.tasks_config['doc_parsing_task'],
            # 2. 这里使用完整的大结构
            # Agent 会生成一个包含 Metadata, Content(列表), Bibliography 的大JSON
            output_pydantic=DocumentStructure 
        )

    @task
    def equation_recognition_task(self) -> Task:
        return Task(
            config=self.tasks_config['equation_recognition_task'],
            # 3. 这里使用小列表
            # Agent 只会返回它识别出来的公式代码和位置索引
            output_pydantic=EquationList, 
            context=[self.doc_parsing_task()] 
        )

    @task
    def template_retrieval_task(self) -> Task:
        return Task(
             config=self.tasks_config['template_retrieval_task'],
            # 🔥 关键点 1：开启异步执行
            # 这意味着当 Crew 运行到这个任务时，会把它扔到后台跑，
            # 然后立刻去运行下一个任务（doc_parsing_task）
            async_execution=True 
        )

    @task
    def latex_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['latex_generation_task'],
            # 🔥 关键点 2：汇总点
            # 这里指定了 context，CrewAI 会强制要求：
            # 只有当 A(Parsing), B(Equation), C(Template) 全部完成时，
            # 这个任务才会开始！
            context=[
                self.doc_parsing_task(), 
                self.equation_recognition_task(), 
                self.template_retrieval_task()
            ],
            output_file='output/draft.tex'
        )

    @task
    def compilation_debugging_task(self) -> Task:
        return Task(
            config=self.tasks_config['compilation_debugging_task'],
            # 调试任务基于生成任务的结果
            context=[self.latex_generation_task()],
            # 最终产出报告和修正后的文件
            output_file='output/final_report.md'
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the Autolatex crew"""

        # 🔥 关键点 3：精心安排的执行顺序
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
           tasks=[
                # 1. 先启动模版任务（它是异步的，所以它一启动，系统就会马上执行下一个）
                self.template_retrieval_task(),
                
                # 2. 紧接着启动文档解析（主线程开始）
                self.doc_parsing_task(),
                
                # 3. 解析完了启动公式识别（B 依赖 A）
                self.equation_recognition_task(),
                
                # 4. 此时系统会检查：
                #    - 模版任务跑完没？
                #    - 公式任务跑完没？
                #    - 文档任务跑完没？
                #    都跑完了，才开始生成 LaTeX
                self.latex_generation_task(),
                
                # 5. 最后编译
                self.compilation_debugging_task()
            ],
            process=Process.sequential,
            verbose=True
        )
