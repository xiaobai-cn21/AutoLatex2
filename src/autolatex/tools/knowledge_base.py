"""
知识库初始化和管理模块
"""
import os
import json
from typing import List, Dict
from .vector_db import VectorDatabase

# LaTeX 模板知识库数据
LATEX_TEMPLATE_KNOWLEDGE = [

    {
        "journal": "IEEE Access",
        "document": """
IEEE Access 必须使用特定的文档类和宏包配置。请严格遵守以下骨架代码：

\\documentclass{ieeeaccess}
\\usepackage{cite}
\\usepackage{amsmath,amssymb,amsfonts}
\\usepackage{algorithmic}
\\usepackage{graphicx}
\\usepackage{textcomp}
\\def\\BibTeX{{\\rm B\\kern-.05em{\\sc i\\kern-.025em b}\\kern-.08em
    T\\kern-.1667em\\lower.7ex\\hbox{E}\\kern-.125emX}}

\\begin{document}
% 必须包含历史日期和DOI
\\history{Date of publication xxxx 00, 0000, date of current version xxxx 00, 0000.}
\\doi{10.1109/ACCESS.2017.DOI}

\\title{你的论文标题}

% 注意 IEEE Access 的特殊作者写法
\\author{\\uppercase{First A. Author}\\authorrefmark{1}, \\IEEEmembership{Fellow, IEEE},
\\uppercase{Second B. Author\\authorrefmark{2}, and Third C. Author,
Jr}.\\authorrefmark{3},
\\IEEEmembership{Member, IEEE}}

\\address[1]{National Institute of Standards and Technology, Boulder, CO 80305 USA}
\\address[2]{Department of Physics, Colorado State University, Fort Collins, CO 80523 USA}
\\address[3]{Electrical Engineering Department, University of Colorado, Boulder, CO 80309 USA}

% 必须包含通讯作者
\\corresp{Corresponding author: First A. Author (e-mail: author@boulder.nist.gov).}

\\begin{abstract}
摘要内容...
\\end{abstract}

\\begin{keywords}
关键词1, 关键词2...
\\end{keywords}

\\titlepgskip=-15pt
\\maketitle

\\section{Introduction}
...
\\EOD
\\end{document}
""",
        "metadata": {
            "journal_name": "IEEE Access",
            "template_type": "journal",
            "documentclass": "ieeeaccess",
            "key_packages": "ieeeaccess, cite, amsmath, amssymb, amsfonts, algorithmic, graphicx, textcomp",
            "template_dir_path": "模板\\IEEE_Access_LaTeX_template"
        },
        "requirements":"""
        1. 使用所给模板完成论文编写
        2. 图片插入需要严格按照这种格式
        \\Figure[t!](topskip=0pt, botskip=0pt, midskip=0pt){图片}
{图片描述}}
        3. 引用参考文档应使用\\cite{}而不是\\citep{}
        """
    },
    {
        "journal": "CVPR 2026",
        "document": """
% CVPR 2026 Paper Template; see https://github.com/cvpr-org/author-kit

\\documentclass[10pt,twocolumn,letterpaper]{article}

%%%%%%%%% PAPER TYPE

% \\usepackage{cvpr}              % Camera-ready

\\usepackage[review]{cvpr}        % Review version

% \\usepackage[pagenumbers]{cvpr} % Page numbers for arXiv

% Additional packages (edit in preamble.tex)

\\input{preamble}

% Hyperref

\\definecolor{cvprblue}{rgb}{0.21,0.49,0.74}

\\usepackage[pagebackref,breaklinks,colorlinks,allcolors=cvprblue]{hyperref}

%%%%%%%%% PAPER METADATA

\\def\\paperID{*****}

\\def\\confName{CVPR}

\\def\\confYear{2026}

%%%%%%%%% TITLE

\\title{<TITLE>}

%%%%%%%%% AUTHORS

\\author{

<AUTHOR 1 NAME> \\\\

<INSTITUTION 1> \\\\

{\\tt\\small <EMAIL 1>}

\\and

<AUTHOR 2 NAME> \\\\

<INSTITUTION 2> \\\\

{\\tt\\small <EMAIL 2>}

}

\\begin{document}

\\maketitle

%%%%%%%%% SECTION INPUTS

\\input{sec/0_abstract}

\\input{sec/1_intro}

\\input{sec/2_formatting}

\\input{sec/3_finalcopy}

%%%%%%%%% BIBLIOGRAPHY

{

    \\small

    \\bibliographystyle{ieeenat_fullname}

    \\bibliography{main}

}

%%%%%%%%% SUPPLEMENTARY (optional)

% \\input{sec/X_suppl}

\\end{document}
""",
        "metadata": {
            "journal_name": "CVPR_2026",
            "template_type": "conference",
            "documentclass": "article",
            "key_packages": "cvpr, hyperref, preamble, xcolor",
            "template_dir_path": "CVPR_2026"
        }
    },
    {
        "journal": "arvix",
        "document": """
arXiv LaTeX 模版核心规范（基于官方 arxiv.sty）：

1. 文档类：

   - 必须使用 \\documentclass{article}。

   - 必须加载 \\usepackage{arxiv}，否则不符合 arXiv 官方排版。

2. 编码与基础宏包：

   - 推荐使用 \\usepackage[utf8]{inputenc}。

   - 字体编码使用 \\usepackage[T1]{fontenc}。

   - 超链接使用 \\usepackage{hyperref}。

3. 参考文献（⚠️ 与 IEEE 模版完全不同）：

   - **允许且推荐**使用 natbib：\\usepackage{natbib}。

   - 允许使用 \\citep{} 与 \\citet{}。

   - 参考文献样式通常使用 \\bibliographystyle{unsrtnat}。

   - bibtex 是 arXiv 官方支持方式。

4. 作者信息：

   - 使用标准 \\author{...}。

   - 支持 \\thanks{}、ORCID、\\href{}。

   - 多作者使用 \\And 分隔。

5. 图片与表格：

   - 使用标准 figure / table 环境。

   - 推荐加载 \\usepackage{graphicx} 与 \\usepackage{booktabs}。

6. 常见避坑指南：

   - 不要使用 IEEE / ACM 专用 documentclass。

   - 不要删除 arxiv.sty 却仍声称是 arXiv 模版。

   - 不要混用 biblatex 与 natbib。
""",
        "metadata": {
            "journal_name": "arvix",
            "template_type": "preprint",
            "documentclass": "article",
            "key_packages": "arxiv, natbib, graphicx, hyperref, booktabs",
            "template_dir_path": "arXiv_LaTeX_template",
            "main_tex_path": "main.tex",
            "paper_template_specification": {
                "document_class": "article",
                "required_packages": ["arxiv", "natbib", "graphicx"],
                "citation_commands": ["\\citep", "\\citet", "\\cite"],
                "forbidden_packages": ["biblatex"],
                "bib_style": "unsrtnat",
                "image_folder": "figures"
            }
        }
    },
    {
        "journal": "Scientific Reports",
        "document": """
Scientific Reports LaTeX 模版核心规范（基于官方 wlscirep.cls）：

1. 文档类：

   - 必须使用 \\documentclass[fleqn,10pt]{wlscirep}。

   - 该 documentclass 为 Nature / Scientific Reports 官方样式。

2. 编码与基础宏包：

   - 推荐使用 \\usepackage[utf8]{inputenc}。

   - 字体编码使用 \\usepackage[T1]{fontenc}。

   - 超链接通常由模板内部或 hyperref 自动管理。

3. 作者与机构信息（⚠️ 与 arXiv / IEEE 不同）：

   - 使用 \\author[<affil>]{Name} 声明作者。

   - 使用 \\affil[<id>]{Affiliation} 定义机构。

   - 通讯作者使用 \\affil[*]{email}。

   - 共同贡献作者使用 \\affil[+]{...}。

   - 不使用 \\thanks{}。

4. 章节结构规范：

   - 使用无编号章节：\\section*{}。

   - 允许最多三级无编号结构：

     - \\section*

     - \\subsection*

     - \\subsubsection*

   - Introduction 与 Discussion 不允许子标题。

5. 摘要规范：

   - 使用 \\begin{abstract} ... \\end{abstract}。

   - 摘要中不得包含引用或子标题。

6. 参考文献：

   - 使用 \\bibliography{sample}。

   - 使用 BibTeX 管理文献。

   - 引用命令使用 \\cite{}。

   - 参考文献样式由 wlscirep 自动控制（不可手动更换）。

7. 图片与表格：

   - 使用标准 figure / table 环境。

   - 图片使用 \\includegraphics。

   - 图注与表注最大 350 字。

   - 使用 \\label{} + \\ref{} 进行交叉引用。

8. 必须包含的附加章节：

   - Acknowledgements（可选）

   - Author contributions statement（强制）

   - Additional information（强制，含 Competing interests）

9. 常见避坑指南：

   - 不要改用 article / revtex / IEEE 类。

   - 不要给章节编号。

   - 不要在 Abstract 中使用 \\cite{}。

   - 不要手动加载不兼容的 bibliography 样式。
""",
        "metadata": {
            "journal_name": "Scientific Reports",
            "publisher": "Nature Portfolio",
            "template_type": "journal_article",
            "documentclass": "wlscirep",
            "documentclass_options": ["fleqn", "10pt"],
            "key_packages": "inputenc, fontenc",
            "template_dir_path": "ScientificReports_LaTeX_template",
            "main_tex_path": "main.tex",
            "paper_template_specification": {
                "document_class": "wlscirep",
                "required_packages": ["inputenc", "fontenc"],
                "citation_commands": ["\\cite"],
                "forbidden_packages": ["biblatex", "natbib"],
                "bib_style": "wlscirep default",
                "image_folder": "figures",
                "sectioning_rules": {
                    "numbered_sections": False,
                    "max_subsection_level": 3
                },
                "mandatory_sections": [
                    "Author contributions statement",
                    "Additional information"
                ]
            }
        }
    }
]

def _clean_metadata(metadata: Dict) -> Dict:
    """
    清理 metadata，将嵌套字典转换为 JSON 字符串
    
    ChromaDB 的 metadata 只支持基本类型（str, int, float, bool, None），
    不支持嵌套字典或列表。需要将嵌套结构转换为 JSON 字符串。
    
    Args:
        metadata: 原始 metadata 字典
        
    Returns:
        清理后的 metadata 字典
    """
    cleaned = {}
    for key, value in metadata.items():
        if isinstance(value, (dict, list)):
            # 将嵌套字典或列表转换为 JSON 字符串
            cleaned[key] = json.dumps(value, ensure_ascii=False)
        else:
            # 基本类型直接保留
            cleaned[key] = value
    return cleaned

def initialize_knowledge_base(persist_directory: str = "data/vector_db") -> VectorDatabase:
    """
    初始化知识库
    
    Args:
        persist_directory: 向量数据库持久化目录
        
    Returns:
        初始化好的 VectorDatabase 实例
    """
    db = VectorDatabase(persist_directory=persist_directory)
    
    # 如果数据库为空，则初始化所有数据
    if db.get_collection_count() == 0:
        documents = [item["document"] for item in LATEX_TEMPLATE_KNOWLEDGE]
        metadatas = [_clean_metadata(item["metadata"]) for item in LATEX_TEMPLATE_KNOWLEDGE]
        ids = [f"template_{item['journal'].lower().replace(' ', '_')}" for item in LATEX_TEMPLATE_KNOWLEDGE]
        
        db.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"知识库已初始化，共添加 {len(documents)} 个模板")
    else:
        # 检查并添加缺失的模板，或更新已存在的模板
        existing_count = db.get_collection_count()
        new_templates = []
        updated_templates = []
        new_documents = []
        new_metadatas = []
        new_ids = []
        
        # 首先检查并删除旧的 "BIThesis" 条目（如果存在）
        old_bithesis_id = "template_bithesis"
        if db.id_exists(old_bithesis_id):
            try:
                db.delete_documents(ids=[old_bithesis_id])
                print(f"已删除旧的 BIThesis 条目")
            except Exception as e:
                print(f"删除旧 BIThesis 条目时出错: {e}")
        
        for item in LATEX_TEMPLATE_KNOWLEDGE:
            template_id = f"template_{item['journal'].lower().replace(' ', '_')}"
            if not db.id_exists(template_id):
                # 新模板
                new_templates.append(item['journal'])
                new_documents.append(item["document"])
                new_metadatas.append(_clean_metadata(item["metadata"]))
                new_ids.append(template_id)
            elif item['journal'] in ['BIThesis-Graduate', 'BIThesis-Undergraduate', 'BIThesis-Undergraduate-English']:
                # BIThesis 模板需要更新（删除旧的后添加新的）
                try:
                    db.delete_documents(ids=[template_id])
                    updated_templates.append(item['journal'])
                    new_documents.append(item["document"])
                    new_metadatas.append(_clean_metadata(item["metadata"]))
                    new_ids.append(template_id)
                except Exception as e:
                    # 如果删除失败（可能不存在），仍然尝试添加
                    print(f"更新 {item['journal']} 时删除旧条目失败（可能不存在）: {e}")
                    updated_templates.append(item['journal'])
                    new_documents.append(item["document"])
                    new_metadatas.append(_clean_metadata(item["metadata"]))
                    new_ids.append(template_id)
        
        if new_templates or updated_templates:
            if new_documents:
                db.add_documents(
                    documents=new_documents,
                    metadatas=new_metadatas,
                    ids=new_ids
                )
            if new_templates:
                print(f"知识库已更新，新增 {len(new_templates)} 个模板: {', '.join(new_templates)}")
            if updated_templates:
                print(f"知识库已更新，更新 {len(updated_templates)} 个模板: {', '.join(updated_templates)}")
            print(f"知识库当前包含 {db.get_collection_count()} 个文档")
        else:
            print(f"知识库已存在，当前包含 {db.get_collection_count()} 个文档，所有模板已是最新")
    
    return db

def get_all_journal_names() -> List[str]:
    """
    获取知识库中所有可用的期刊/会议名称列表
    
    Returns:
        期刊名称列表，按字母顺序排序
    """
    journal_names = [item["journal"] for item in LATEX_TEMPLATE_KNOWLEDGE]
    # 按字母顺序排序，中文期刊排在后面
    sorted_names = sorted(journal_names, key=lambda x: (not x.isascii(), x))
    return sorted_names

def knowledge_base_search(journal_name: str, n_results: int = 3) -> str:
    """
    在知识库中搜索期刊模板信息
    
    Args:
        journal_name: 期刊名称
        n_results: 返回结果数量
        
    Returns:
        格式化的搜索结果字符串
    """
    # 初始化或加载知识库
    db = initialize_knowledge_base()
    
    # 首先尝试精确匹配（通过元数据过滤）
    exact_match = None
    query_lower = journal_name.lower().strip()
    
    # 检查是否有精确匹配的 journal_name
    try:
        all_results = db.collection.get()
        if all_results and all_results.get('ids'):
            for i, metadata in enumerate(all_results.get('metadatas', [])):
                if metadata and metadata.get('journal_name', '').lower() == query_lower:
                    # 找到精确匹配，获取完整信息
                    doc_id = all_results['ids'][i]
                    doc_text = all_results['documents'][i] if all_results.get('documents') else ""
                    exact_match = {
                        'document': doc_text,
                        'metadata': metadata,
                        'distance': 0.0,
                        'id': doc_id
                    }
                    break
    except Exception as e:
        print(f"精确匹配检查时出错: {e}")
    
    # 执行向量搜索
    vector_results = db.search(query=journal_name, n_results=n_results * 2)  # 获取更多结果以便过滤
    
    # 合并结果：如果有精确匹配，将其放在第一位
    if exact_match:
        # 移除向量搜索结果中的精确匹配（如果存在）
        filtered_results = [r for r in vector_results 
                          if r.get('metadata', {}).get('journal_name', '').lower() != query_lower]
        results = [exact_match] + filtered_results[:n_results - 1]
    else:
        results = vector_results[:n_results]
    
    if not results:
        return f"未找到与 '{journal_name}' 相关的 LaTeX 模板信息。"
    
    # 格式化返回结果
    output_parts = []
    for i, result in enumerate(results, 1):
        doc = result['document']
        metadata = result.get('metadata', {})
        distance = result.get('distance', 0)
        similarity = 1 - distance if distance else 1.0  # 转换为相似度分数
        
        # 如果是精确匹配，标注出来
        match_type = "（精确匹配）" if i == 1 and exact_match and result == exact_match else ""
        
        output_parts.append(f"【结果 {i}】相似度: {similarity:.2%}{match_type}")
        output_parts.append(f"期刊: {metadata.get('journal_name', 'Unknown')}")
        output_parts.append(f"模板类型: {metadata.get('template_type', 'Unknown')}")
        output_parts.append(f"文档类: {metadata.get('documentclass', 'Unknown')}")
        output_parts.append(f"关键宏包: {metadata.get('key_packages', 'N/A')}")
        output_parts.append(f"详细信息: {doc}")
        output_parts.append("")  # 空行分隔
    
    return "\n".join(output_parts)

