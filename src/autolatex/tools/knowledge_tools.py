from crewai.tools import BaseTool
from .knowledge_base import knowledge_base_search
from crewai.tools import BaseTool

class KnowledgeBaseSearchTool(BaseTool):
    name: str = "LaTeX Template Knowledge Base Search"
    description: str = "根据期刊名称，从向量数据库中搜索最相关的 LaTeX 模板信息和排版建议。"

    def _run(self, journal_name: str) -> str:
        """
        在向量数据库中搜索期刊模板信息
        
        Args:
            journal_name: 期刊名称（如 "NeurIPS", "CVPR", "IEEE" 等）
            
        Returns:
            格式化的搜索结果字符串，包含模板信息、关键宏包和排版建议
        """
        print(f"--- [知识库搜索] 正在搜索: {journal_name} ---")
        try:
            result = knowledge_base_search(journal_name=journal_name, n_results=3)
            print(f"--- [知识库搜索] 搜索完成 ---")
            return result
        except Exception as e:
            error_msg = f"知识库搜索出错: {str(e)}"
            print(f"--- [知识库搜索] {error_msg} ---")
            return error_msg

