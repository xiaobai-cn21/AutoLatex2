"""
向量数据库模块
使用 ChromaDB 存储和检索 LaTeX 模板知识库
"""
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import json

class VectorDatabase:
    """向量数据库管理类"""
    
    def __init__(self, persist_directory: str = "data/vector_db", collection_name: str = "latex_templates"):
        """
        初始化向量数据库
        
        Args:
            persist_directory: 数据库持久化目录
            collection_name: 集合名称
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
        )
    
    def add_documents(self, documents: List[str], metadatas: List[Dict], ids: Optional[List[str]] = None):
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档文本列表
            metadatas: 元数据列表
            ids: 文档ID列表（可选）
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        # ChromaDB 会自动生成嵌入向量
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            
        Returns:
            搜索结果列表，每个结果包含文档内容、元数据和相似度分数
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # 格式化返回结果
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        return formatted_results
    
    def get_collection_count(self) -> int:
        """获取集合中的文档数量"""
        return self.collection.count()
    
    def get_all_ids(self) -> List[str]:
        """获取集合中所有文档的ID列表"""
        results = self.collection.get()
        return results.get('ids', []) if results else []
    
    def id_exists(self, doc_id: str) -> bool:
        """检查指定的文档ID是否已存在"""
        try:
            results = self.collection.get(ids=[doc_id])
            return len(results.get('ids', [])) > 0
        except Exception:
            return False
    
    def delete_documents(self, ids: List[str]):
        """
        删除指定的文档
        
        Args:
            ids: 要删除的文档ID列表
        """
        try:
            self.collection.delete(ids=ids)
        except Exception as e:
            raise Exception(f"删除文档失败: {e}")
    
    def clear_collection(self):
        """清空集合（用于重新初始化）"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

