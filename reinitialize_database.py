"""
重新初始化向量数据库脚本
删除现有数据库并重新创建，确保包含所有最新模板
"""
import sys
import os
import shutil
import json
import re

# 添加 src 目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# 直接使用 ChromaDB，避免导入 crewai
import chromadb
from chromadb.config import Settings

def extract_template_knowledge():
    """直接从文件提取 LATEX_TEMPLATE_KNOWLEDGE 数据"""
    knowledge_file = os.path.join(src_path, "autolatex", "tools", "knowledge_base.py")
    
    with open(knowledge_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式找到 LATEX_TEMPLATE_KNOWLEDGE = [...] 的部分
    # 匹配从 LATEX_TEMPLATE_KNOWLEDGE = [ 开始到对应的 ] 结束
    pattern = r'LATEX_TEMPLATE_KNOWLEDGE\s*=\s*\['
    match = re.search(pattern, content)
    
    if not match:
        raise ValueError("Cannot find LATEX_TEMPLATE_KNOWLEDGE in file")
    
    start_idx = match.end() - 1  # 包含 [
    
    # 找到匹配的结束括号
    bracket_count = 0
    end_idx = start_idx
    
    for i, char in enumerate(content[start_idx:], start_idx):
        if char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end_idx = i + 1
                break
    
    # 提取列表字符串
    list_str = content[start_idx:end_idx]
    
    # 创建一个安全的执行环境
    safe_dict = {
        '__builtins__': {
            'True': True,
            'False': False,
            'None': None,
        }
    }
    
    # 执行提取的代码
    try:
        exec(f"LATEX_TEMPLATE_KNOWLEDGE = {list_str}", safe_dict)
        return safe_dict['LATEX_TEMPLATE_KNOWLEDGE']
    except Exception as e:
        print(f"解析模板数据时出错: {e}")
        # 如果失败，尝试使用 json（但需要先转换）
        raise

def reinitialize_database():
    """重新初始化数据库"""
    print("=" * 60)
    print("重新初始化向量数据库")
    print("=" * 60)
    
    # 删除现有数据库目录
    db_path = "data/vector_db"
    if os.path.exists(db_path):
        print(f"\n正在删除现有数据库: {db_path}")
        try:
            shutil.rmtree(db_path)
            print("✅ 数据库目录已删除")
        except Exception as e:
            print(f"❌ 删除数据库目录失败: {e}")
            return
    else:
        print(f"\n数据库目录不存在: {db_path}")
    
    # 重新创建数据库
    print("\n正在重新创建数据库...")
    os.makedirs(db_path, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_or_create_collection(
        name="latex_templates",
        metadata={"hnsw:space": "cosine"}
    )
    
    # 提取模板数据
    print("正在读取模板数据...")
    try:
        LATEX_TEMPLATE_KNOWLEDGE = extract_template_knowledge()
        print(f"✅ 成功读取 {len(LATEX_TEMPLATE_KNOWLEDGE)} 个模板")
    except Exception as e:
        print(f"❌ 读取模板数据失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 添加所有模板
    print("\n正在添加模板到数据库...")
    documents = [item["document"] for item in LATEX_TEMPLATE_KNOWLEDGE]
    metadatas = [item["metadata"] for item in LATEX_TEMPLATE_KNOWLEDGE]
    ids = [f"template_{item['journal'].lower().replace(' ', '_')}" for item in LATEX_TEMPLATE_KNOWLEDGE]
    
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    count = collection.count()
    print(f"\n✅ 数据库重新初始化成功！")
    print(f"   共包含 {count} 个模板")
    
    # 列出所有模板
    print("\n模板列表:")
    print("-" * 60)
    for item in LATEX_TEMPLATE_KNOWLEDGE:
        print(f"  - {item['journal']}")
    
    # 测试搜索
    print("\n" + "=" * 60)
    print("测试搜索 BIThesis-Undergraduate")
    print("=" * 60)
    results = collection.query(
        query_texts=["BIThesis-Undergraduate"],
        n_results=3
    )
    
    if results['documents'] and len(results['documents'][0]) > 0:
        for i, doc in enumerate(results['documents'][0], 1):
            metadata = results['metadatas'][0][i-1] if results['metadatas'] else {}
            distance = results['distances'][0][i-1] if results['distances'] else 0
            similarity = 1 - distance if distance else 1.0
            print(f"\n【结果 {i}】相似度: {similarity:.2%}")
            print(f"期刊: {metadata.get('journal_name', 'Unknown')}")
            print(f"学位级别: {metadata.get('degree_level', 'Unknown')}")
            print(f"详细信息: {doc[:150]}...")
    else:
        print("未找到结果")
    
    print("\n" + "=" * 60)
    print("测试搜索 BIThesis-Graduate")
    print("=" * 60)
    results = collection.query(
        query_texts=["BIThesis-Graduate"],
        n_results=3
    )
    
    if results['documents'] and len(results['documents'][0]) > 0:
        for i, doc in enumerate(results['documents'][0], 1):
            metadata = results['metadatas'][0][i-1] if results['metadatas'] else {}
            distance = results['distances'][0][i-1] if results['distances'] else 0
            similarity = 1 - distance if distance else 1.0
            print(f"\n【结果 {i}】相似度: {similarity:.2%}")
            print(f"期刊: {metadata.get('journal_name', 'Unknown')}")
            print(f"学位级别: {metadata.get('degree_level', 'Unknown')}")
            print(f"详细信息: {doc[:150]}...")
    
    print("\n" + "=" * 60)
    print("重新初始化完成！")
    print("=" * 60)
    print("\n现在可以搜索:")
    print("  - 'BIThesis-Undergraduate' 或 '本科生' 来查找本科生模板")
    print("  - 'BIThesis-Graduate' 或 '研究生' 来查找研究生模板")

if __name__ == "__main__":
    reinitialize_database()
