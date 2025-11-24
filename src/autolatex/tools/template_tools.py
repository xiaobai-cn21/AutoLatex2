# src/autolatex/tools/template_tools.py
from crewai.tools import BaseTool


# 所有的自定义工具都继承自 BaseTool
class TemplateTools(BaseTool):
    name: str = "期刊模板读取工具"

    description: str = "根据模板名称（例如 'ieee_conference'），读取并返回对应的LaTeX模板文件的完整内容字符串。"

    # 3. _run() 方法: 这是工具实际执行的代码。
    #    当Agent决定使用这个工具时，CrewAI框架就会调用这个方法。
    def _run(self, template_name: str) -> str:
        # 它接收一个参数 `template_name`，这是Agent传递过来的。
        template_path = f"data/templates/{template_name}.tex"
        try:
            # 这里是真正的文件I/O操作，是Agent本身做不到的。
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"错误：找不到名为 {template_name} 的模板文件。"