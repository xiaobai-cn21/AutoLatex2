"""
测试知识库搜索功能
"""
import sys
import os

# 添加 src 目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from autolatex.tools.knowledge_base import knowledge_base_search, initialize_knowledge_base

def test_knowledge_base():
    """测试知识库功能"""
    print("=" * 50)
    print("知识库功能测试")
    print("=" * 50)
    
    # 测试初始化
    print("\n1. 测试知识库初始化...")
    try:
        db = initialize_knowledge_base()
        print(f"✅ 知识库初始化成功，包含 {db.get_collection_count()} 个文档")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 测试搜索
    test_journals = ["NeurIPS", "CVPR", "IEEE", "ACM", "Nature", "Unknown Journal"]
    
    print("\n2. 测试知识库搜索...")
    for journal in test_journals:
        print(f"\n搜索期刊: {journal}")
        print("-" * 50)
        try:
            result = knowledge_base_search(journal_name=journal, n_results=2)
            print(result)
            print("✅ 搜索成功")
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    test_knowledge_base()

