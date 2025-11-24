"""
更新知识库脚本
用于添加新的模板到向量数据库
"""
import sys
import os

# 添加 src 目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# 直接使用 ChromaDB，避免导入问题
import chromadb
from chromadb.config import Settings

def update_knowledge_base():
    """更新知识库"""
    print("=" * 60)
    print("更新向量数据库知识库")
    print("=" * 60)
    
    # 直接使用 ChromaDB
    persist_directory = "data/vector_db"
    os.makedirs(persist_directory, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_or_create_collection(
        name="latex_templates",
        metadata={"hnsw:space": "cosine"}
    )
    
    existing_count = collection.count()
    print(f"\n当前知识库包含 {existing_count} 个模板")
    
    # 导入知识库数据
    from autolatex.tools.knowledge_base import LATEX_TEMPLATE_KNOWLEDGE
    
    # 获取所有现有ID
    existing_results = collection.get()
    existing_ids = set(existing_results.get('ids', [])) if existing_results else set()
    
    new_templates = []
    new_documents = []
    new_metadatas = []
    new_ids = []
    
    # 需要更新的模板（删除旧的后添加新的）
    templates_to_update = []
    
    for item in LATEX_TEMPLATE_KNOWLEDGE:
        template_id = f"template_{item['journal'].lower().replace(' ', '_')}"
        if template_id not in existing_ids:
            new_templates.append(item['journal'])
            new_documents.append(item["document"])
            new_metadatas.append(item["metadata"])
            new_ids.append(template_id)
        elif item['journal'] == 'BIThesis':
            # BIThesis 需要更新
            templates_to_update.append({
                'id': template_id,
                'document': item["document"],
                'metadata': item["metadata"]
            })
    
    # 更新 BIThesis 模板（删除旧的后添加新的）
    if templates_to_update:
        for template in templates_to_update:
            try:
                # 删除旧的
                collection.delete(ids=[template['id']])
                print(f"已删除旧的 {template['id']} 条目")
            except Exception as e:
                print(f"删除旧条目时出错（可能不存在）: {e}")
            # 添加新的
            new_templates.append('BIThesis (已更新)')
            new_documents.append(template['document'])
            new_metadatas.append(template['metadata'])
            new_ids.append(template['id'])
    
    if new_templates or templates_to_update:
        if new_documents:
            collection.add(
                documents=new_documents,
                metadatas=new_metadatas,
                ids=new_ids
            )
            print(f"\n✅ 新增/更新 {len(new_templates)} 个模板: {', '.join(new_templates)}")
        print(f"知识库现在包含 {collection.count()} 个模板")
    else:
        print("\n✅ 所有模板已是最新，无需更新")
    
    # 测试搜索 BIThesis
    print("\n" + "=" * 60)
    print("测试搜索 BIThesis 模板")
    print("=" * 60)
    results = collection.query(
        query_texts=["BIThesis"],
        n_results=3
    )
    
    if results['documents'] and len(results['documents'][0]) > 0:
        for i, doc in enumerate(results['documents'][0], 1):
            metadata = results['metadatas'][0][i-1] if results['metadatas'] else {}
            distance = results['distances'][0][i-1] if results['distances'] else 0
            similarity = 1 - distance if distance else 1.0
            print(f"\n【结果 {i}】相似度: {similarity:.2%}")
            print(f"期刊: {metadata.get('journal_name', 'Unknown')}")
            print(f"模板类型: {metadata.get('template_type', 'Unknown')}")
            print(f"文档类: {metadata.get('documentclass', 'Unknown')}")
            print(f"编译方式: {metadata.get('compiler', 'Unknown')}")
            print(f"详细信息: {doc[:200]}...")
    else:
        print("未找到结果")
    
    print("\n" + "=" * 60)
    print("更新完成！")
    print("=" * 60)

if __name__ == "__main__":
    update_knowledge_base()
