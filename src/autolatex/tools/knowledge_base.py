"""
知识库初始化和管理模块
"""
import os
from typing import List, Dict
from .vector_db import VectorDatabase

# LaTeX 模板知识库数据
LATEX_TEMPLATE_KNOWLEDGE = [
    {
        "journal": "NeurIPS",
        "document": "NeurIPS (Neural Information Processing Systems) 会议模板。使用 \\documentclass{article}。关键宏包包括：times, graphicx, hyperref, amsmath, amssymb。摘要部分应使用 \\begin{abstract} 环境。标题格式：\\title{Your Title}，作者信息使用 \\author{} 命令。参考文献使用 natbib 宏包。",
        "metadata": {
            "journal_name": "NeurIPS",
            "template_type": "conference",
            "documentclass": "article",
            "key_packages": "times, graphicx, hyperref, amsmath, amssymb, natbib"
        }
    },
    {
        "journal": "CVPR",
        "document": "CVPR (Computer Vision and Pattern Recognition) 会议模板。使用 \\documentclass[10pt,twocolumn,letterpaper]{article}。必须包含的宏包：graphicx, amsmath, amssymb, natbib, times, epsfig, psfrag, algorithm, algorithmic, array, url。双栏格式，摘要限制在150-200字。",
        "metadata": {
            "journal_name": "CVPR",
            "template_type": "conference",
            "documentclass": "article",
            "key_packages": "graphicx, amsmath, amssymb, natbib, times, epsfig, psfrag, algorithm, algorithmic, array, url",
            "format": "twocolumn"
        }
    },
    {
        "journal": "ICML",
        "document": "ICML (International Conference on Machine Learning) 会议模板。使用 \\documentclass{article}。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref。支持单栏和双栏格式。摘要应简洁明了，通常限制在200字以内。",
        "metadata": {
            "journal_name": "ICML",
            "template_type": "conference",
            "documentclass": "article",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref"
        }
    },
    {
        "journal": "IEEE",
        "document": "IEEE 期刊和会议模板。使用 \\documentclass[journal]{IEEEtran} 或 \\documentclass[conference]{IEEEtran}。必须包含的宏包：graphicx, amsmath, amssymb, cite, url。IEEE 格式要求严格，包括特定的标题格式、作者信息和参考文献样式。",
        "metadata": {
            "journal_name": "IEEE",
            "template_type": "journal/conference",
            "documentclass": "IEEEtran",
            "key_packages": "graphicx, amsmath, amssymb, cite, url"
        }
    },
    {
        "journal": "ACM",
        "document": "ACM (Association for Computing Machinery) 会议和期刊模板。使用 \\documentclass[sigconf]{acmart} 或 \\documentclass[journal]{acmart}。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref。ACM 格式支持多种样式，包括 sigconf, siggraph, sigplan 等。",
        "metadata": {
            "journal_name": "ACM",
            "template_type": "journal/conference",
            "documentclass": "acmart",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref"
        }
    },
    {
        "journal": "Nature",
        "document": "Nature 期刊模板。使用 \\documentclass[12pt]{article}。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref, url。Nature 格式要求单栏，摘要通常分为 Background, Results, Conclusions 等部分。",
        "metadata": {
            "journal_name": "Nature",
            "template_type": "journal",
            "documentclass": "article",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref, url",
            "format": "single column"
        }
    },
    {
        "journal": "AAAI",
        "document": "AAAI (Association for the Advancement of Artificial Intelligence) 会议模板。使用 \\documentclass[letterpaper]{article}。关键宏包：graphicx, amsmath, amssymb, natbib, times, url。双栏格式，摘要限制在150字以内。",
        "metadata": {
            "journal_name": "AAAI",
            "template_type": "conference",
            "documentclass": "article",
            "key_packages": "graphicx, amsmath, amssymb, natbib, times, url",
            "format": "twocolumn"
        }
    },
    {
        "journal": "ICLR",
        "document": "ICLR (International Conference on Learning Representations) 会议模板。使用 \\documentclass{article}。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref, url。支持单栏和双栏格式，摘要应清晰描述研究贡献。",
        "metadata": {
            "journal_name": "ICLR",
            "template_type": "conference",
            "documentclass": "article",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref, url"
        }
    },
    # 更多国际会议
    {
        "journal": "KDD",
        "document": "KDD (Knowledge Discovery and Data Mining) 会议模板。使用 \\documentclass[sigconf]{acmart} 或 \\documentclass{article}。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref, algorithm, algorithmic。双栏格式，摘要限制在200字以内。",
        "metadata": {
            "journal_name": "KDD",
            "template_type": "conference",
            "documentclass": "acmart",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref, algorithm, algorithmic",
            "format": "twocolumn"
        }
    },
    {
        "journal": "ACL",
        "document": "ACL (Association for Computational Linguistics) 会议模板。使用 \\documentclass[11pt]{article}。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref, url, xcolor。单栏格式，摘要限制在150字以内。",
        "metadata": {
            "journal_name": "ACL",
            "template_type": "conference",
            "documentclass": "article",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref, url, xcolor",
            "format": "single column"
        }
    },
    {
        "journal": "WWW",
        "document": "WWW (World Wide Web Conference) 会议模板。使用 \\documentclass[sigconf]{acmart}。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref, url。双栏格式，摘要限制在200字以内。",
        "metadata": {
            "journal_name": "WWW",
            "template_type": "conference",
            "documentclass": "acmart",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref, url",
            "format": "twocolumn"
        }
    },
    {
        "journal": "SIGGRAPH",
        "document": "SIGGRAPH 会议模板。使用 \\documentclass[siggraph]{acmart}。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref, url。双栏格式，摘要限制在150字以内。",
        "metadata": {
            "journal_name": "SIGGRAPH",
            "template_type": "conference",
            "documentclass": "acmart",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref, url",
            "format": "twocolumn"
        }
    },
    # 中文期刊和会议
    {
        "journal": "计算机学报",
        "document": "计算机学报 (Journal of Computer Science) 中文期刊模板。使用 \\documentclass[12pt]{ctexart} 或 \\documentclass[12pt]{article} 配合 ctex 宏包。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK（用于中文支持）。单栏格式，摘要分为中文摘要和英文摘要两部分。",
        "metadata": {
            "journal_name": "计算机学报",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "软件学报",
        "document": "软件学报 (Journal of Software) 中文期刊模板。使用 \\documentclass[12pt]{ctexart}。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK, biblatex。单栏格式，需要中英文摘要。",
        "metadata": {
            "journal_name": "软件学报",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK, biblatex",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "中国科学",
        "document": "中国科学 (Science China) 中文期刊模板。使用 \\documentclass[12pt]{ctexart}。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK。单栏格式，支持中英文双语。",
        "metadata": {
            "journal_name": "中国科学",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "自动化学报",
        "document": "自动化学报 (Acta Automatica Sinica) 中文期刊模板。使用 \\documentclass[12pt]{ctexart}。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK, algorithm, algorithmic。单栏格式，需要中英文摘要。",
        "metadata": {
            "journal_name": "自动化学报",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK, algorithm, algorithmic",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "电子学报",
        "document": "电子学报 (Acta Electronica Sinica) 中文期刊模板。使用 \\documentclass[12pt]{ctexart}。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK。单栏格式，支持中英文双语。",
        "metadata": {
            "journal_name": "电子学报",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "通信学报",
        "document": "通信学报 (Journal on Communications) 中文期刊模板。使用 \\documentclass[12pt]{ctexart}。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK。单栏格式，需要中英文摘要。",
        "metadata": {
            "journal_name": "通信学报",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "计算机研究与发展",
        "document": "计算机研究与发展 (Journal of Computer Research and Development) 中文期刊模板。使用 \\documentclass[12pt]{ctexart}。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK。单栏格式，需要中英文摘要。",
        "metadata": {
            "journal_name": "计算机研究与发展",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "中文信息学报",
        "document": "中文信息学报 (Journal of Chinese Information Processing) 中文期刊模板。使用 \\documentclass[12pt]{ctexart}。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK。单栏格式，需要中英文摘要。",
        "metadata": {
            "journal_name": "中文信息学报",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "模式识别与人工智能",
        "document": "模式识别与人工智能 (Pattern Recognition and Artificial Intelligence) 中文期刊模板。使用 \\documentclass[12pt]{ctexart}。关键宏包：ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK, algorithm, algorithmic。单栏格式，需要中英文摘要。",
        "metadata": {
            "journal_name": "模式识别与人工智能",
            "template_type": "journal",
            "documentclass": "ctexart",
            "key_packages": "ctex, graphicx, amsmath, amssymb, natbib, hyperref, url, xeCJK, algorithm, algorithmic",
            "format": "single column",
            "language": "chinese"
        }
    },
    {
        "journal": "CCF",
        "document": "CCF (中国计算机学会) 推荐会议模板。通常使用 \\documentclass{article} 或 \\documentclass{ctexart}（中文）。关键宏包：graphicx, amsmath, amssymb, natbib, hyperref, url, ctex, xeCJK（中文支持）。根据具体会议可能有单栏或双栏格式。",
        "metadata": {
            "journal_name": "CCF",
            "template_type": "conference",
            "documentclass": "article",
            "key_packages": "graphicx, amsmath, amssymb, natbib, hyperref, url, ctex, xeCJK",
            "language": "chinese/english"
        }
    },
    {
        "journal": "BIThesis-Graduate",
        "document": "BIThesis 研究生学位论文模板 Graduate Thesis Template - 北京理工大学研究生专用。3.8.3 版本。适用于硕士和博士研究生，不适用于本科生。使用 \\documentclass[type=master]{bithesis}（硕士）或 \\documentclass[type=doctor]{bithesis}（博士）。这是研究生版本，与本科生版本不同。master degree thesis, doctor degree thesis, graduate student thesis template。bithesis 类基于 ctexbook，支持盲审格式（blindPeerReview=true）和双面打印（twoside=true）。关键宏包：expl3, l3keys2e, geometry, xcolor, xeCJK, zhlineskip, indentfirst, titletoc, graphicx, fancyhdr, pdfpages, setspace, booktabs, multirow, tikz, etoolbox, hyperref, caption, array, amsmath, amssymb, pifont, amsthm, listings, enumitem, fmtcount, unicode-math, ifplatform, datetime2, biblatex。参考文献使用 biblatex 配合 gb7714-2015 样式（中文引用标准）。编译流程：xelatex -> biber -> xelatex -> xelatex（必须使用 XeLaTeX，不支持 pdfLaTeX）。模板包含封面、摘要、目录、正文、参考文献、附录、个人成果、致谢等完整结构，符合北京理工大学研究生学位论文撰写规范。\n\n模板文件路径：BIThesis-graduate-thesis-template-3.8.3/1-BIThesis-论文模板-3.8.3/\n主文件：main.tex\n类文件：bithesis.cls\n\n必需目录结构：\n- chapters/ (章节文件：abstract.tex, chapter1.tex, chapter2.tex 等)\n- reference/ (参考文献：main.bib, pub.bib)\n- misc/ (其他文件：0_symbols.tex, 1_conclusion.tex, 2_reference.tex, 3_appendices.tex, 4_pub.tex, 5_acknowledgements.tex, 6_resume.tex)\n- figures/ (图片文件)\n\n最小工作示例：\n\\documentclass[type=master,twoside=false]{bithesis}\n\\BITSetup{\n  info = {\n    title = 论文标题,\n    titleEn = Paper Title,\n    author = 作者名,\n    authorEn = Author Name,\n    studentId = 学号,\n    school = 学院名称,\n    schoolEn = School Name,\n    supervisor = 导师姓名,\n    supervisorEn = Supervisor Name,\n    degreeType = academic,  % 或 professional\n    degree = 学位名称,\n    degreeEn = Degree Name,\n    major = 专业名称,\n    majorEn = Major Name,\n    keywords = {关键词1；关键词2},\n    keywordsEn = keyword1; keyword2,\n  }\n}\n\\usepackage[backend=biber,style=gb7714-2015]{biblatex}\n\\addbibresource{reference/main.bib}\n\\usepackage{graphicx}\n\\begin{document}\n\\MakeCover\n\\MakeTitle\n\\MakeOriginality\n\\frontmatter\n\\input{./chapters/abstract.tex}\n\\MakeTOC\n\\listoffigures\n\\listoftables\n\\mainmatter\n\\input{./chapters/chapter1.tex}\n\\backmatter\n\\input{./misc/2_reference.tex}\n\\input{./misc/3_appendices.tex}\n\\input{./misc/5_acknowledgements.tex}\n\\end{document}\n\n常用配置选项：\n- type: master (硕士) 或 doctor (博士)\n- twoside: true/false (双面打印模式)\n- blindPeerReview: true (开启盲审格式)\n- ctex={fontset=windows} (Windows 字体设置，用于 Linux/macOS)\n\n重要注意事项：\n1. 必须使用 XeLaTeX 编译，不支持 pdfLaTeX\n2. 需要 biber 处理参考文献（不是 bibtex）\n3. 编译方式有两种：\n   - 推荐方式：使用 latexmk 命令（自动处理编译流程）\n   - 手动方式：xelatex -> biber -> xelatex -> xelatex（需要编译多次）\n4. latexmkrc 文件已配置好，使用 latexmk 时会自动使用 XeLaTeX 和 biber\n5. 中文支持需要 xeCJK 和相应中文字体\n6. 在 Linux/macOS 下可能需要安装中易字库或使用 ctex={fontset=windows} 选项\n7. macOS 用户建议使用 TeX Live/MacTeX 2023 或更新版本，否则参考文献可能被错误查重\n8. 参考文献样式使用 gb7714-2015（中国国家标准）\n9. 模板支持学术型（academic）和专业型（professional）两种学位类型\n10. 项目地址：https://github.com/BITNP/BIThesis\n11. 使用手册和文档：https://bithesis.bitnp.net\n\n章节结构和使用模式：\n\n摘要结构（chapters/abstract.tex）：\n\\begin{abstract}\n  中文摘要内容（硕士500-800字，博士1000-1200字）\n\\end{abstract}\n\\begin{abstractEn}\n  English abstract content (must match Chinese abstract)\n\\end{abstractEn}\n\n章节结构（chapters/chapter*.tex）：\n\\chapter{章节标题}  % 一级标题\n\\label{chap:label}  % 可选标签\n\\section{节标题}  % 二级标题\n\\subsection{小节标题}  % 三级标题\n\\subsubsection{四级节标题}  % 四级标题（可选）\n\n常用LaTeX元素：\n- 引用：\\cite{key}（方括号引用）或 \\parencite{key}（圆括号引用）\n- 交叉引用：\\ref{label}（编号）或 \\autoref{label}（自动类型+编号）\n- 图片：\\begin{figure}[hbt]\\centering\\includegraphics[width=0.75\\textwidth]{figures/filename}\\caption{标题}\\label{fig:label}\\end{figure}\n- 表格：\\begin{table}[hbt]\\centering\\caption{标题}\\label{tab:label}\\begin{tabular*}{0.9\\textwidth}{@{\\extracolsep{\\fill}}cccc}\\toprule...\\midrule...\\bottomrule\\end{tabular*}\\end{table}\n- 定理：\\begin{them}[定理名]\\label{thm:label}...\\end{them}\n- 证明：\\begin{proof}...\\qedhere\\end{proof}\n- 公式：\\begin{equation}\\label{eq:label}...\\end{equation}\n- 多行公式：\\begin{subequations}\\begin{eqnarray}...\\end{eqnarray}\\end{subequations}\n\n参考文献结构（reference/main.bib）：\n使用 biblatex 格式，支持 @article, @inproceedings, @book 等类型。示例：\n@article{key,\n  title = {标题},\n  author = {作者1 and 作者2},\n  journal = {期刊名},\n  volume = {卷号},\n  number = {期号},\n  pages = {页码},\n  year = {年份},\n}\n\n参考文献显示（misc/2_reference.tex）：\n\\begin{bibprint}\n  \\printbibliography[heading=none,notcategory=mypub,resetnumbers=true]\n\\end{bibprint}\n\n结论（misc/1_conclusion.tex）：\n\\begin{conclusion}\n  结论内容（不加章号，单独排写）\n\\end{conclusion}\n\n附录（misc/3_appendices.tex）：\n\\begin{appendices}\n  \\chapter{附录标题}\n  附录内容\n\\end{appendices}\n\n个人成果（misc/4_pub.tex）：\n\\begin{publications}\n  \\addpubs{citeKey1,citeKey2}  % 在 reference/pub.bib 中定义\n  \\printbibliography[heading=none,category=mypub,resetnumbers=true]\n\\end{publications}\n\n致谢（misc/5_acknowledgements.tex）：\n\\begin{acknowledgements}\n  致谢内容\n\\end{acknowledgements}\n\n文件组织：\n- chapters/abstract.tex：摘要（中英文）\n- chapters/chapter1.tex, chapter2.tex...：各章节内容\n- reference/main.bib：正文参考文献\n- reference/pub.bib：个人成果清单\n- misc/0_symbols.tex：主要符号对照表\n- misc/1_conclusion.tex：结论\n- misc/2_reference.tex：参考文献列表\n- misc/3_appendices.tex：附录\n- misc/4_pub.tex：攻读学位期间发表论文与研究成果清单\n- misc/5_acknowledgements.tex：致谢\n- misc/6_resume.tex：个人简介（仅博士生）\n- figures/：存放所有图片文件",
        "metadata": {
            "journal_name": "BIThesis-Graduate",
            "degree_level": "graduate",
            "template_type": "thesis",
            "documentclass": "bithesis",
            "base_class": "ctexbook",
            "key_packages": "expl3, l3keys2e, geometry, xcolor, xeCJK, zhlineskip, indentfirst, titletoc, graphicx, fancyhdr, pdfpages, setspace, booktabs, multirow, tikz, etoolbox, hyperref, caption, array, amsmath, amssymb, pifont, amsthm, listings, enumitem, fmtcount, unicode-math, ifplatform, datetime2, biblatex",
            "biblatex_style": "gb7714-2015",
            "format": "single column",
            "language": "chinese",
            "compiler": "XeLaTeX",
            "compilation_sequence": "xelatex -> biber -> xelatex -> xelatex",
            "institution": "北京理工大学",
            "version": "3.8.3",
            "supports_blind_review": True,
            "supports_twoside": True,
            "template_path": "BIThesis-graduate-thesis-template-3.8.3/1-BIThesis-论文模板-3.8.3/",
            "main_file": "main.tex",
            "class_file": "bithesis.cls",
            "required_directories": "chapters/, reference/, misc/, figures/",
            "degree_types": "academic, professional",
            "compilation_tools": "latexmk (recommended) or manual xelatex",
            "latexmkrc_file": "latexmkrc (configured for XeLaTeX + biber)",
            "documentation_url": "https://bithesis.bitnp.net",
            "github_url": "https://github.com/BITNP/BIThesis",
            "abstract_environments": "abstract (Chinese), abstractEn (English)",
            "chapter_structure": "\\chapter{}, \\section{}, \\subsection{}, \\subsubsection{}",
            "citation_commands": "\\cite{}, \\parencite{}",
            "cross_reference_commands": "\\ref{}, \\autoref{}",
            "figure_environment": "figure with \\includegraphics, \\caption, \\label",
            "table_environment": "table with tabular*, \\toprule, \\midrule, \\bottomrule",
            "theorem_environments": "them, proof",
            "equation_environments": "equation, subequations, eqnarray",
            "bibliography_files": "main.bib (references), pub.bib (publications)",
            "misc_files": "0_symbols.tex, 1_conclusion.tex, 2_reference.tex, 3_appendices.tex, 4_pub.tex, 5_acknowledgements.tex, 6_resume.tex"
        }
    },
    {
        "journal": "BIThesis-Undergraduate",
        "document": "BIThesis 本科生毕业设计（论文）模板 Undergraduate Thesis Template - 北京理工大学本科生专用。使用 \\documentclass[type=bachelor]{bithesis}。这是本科生版本，与研究生版本不同。本科生毕业设计（论文）模板，bachelor degree thesis template，undergraduate graduation project。适用于本科生，不适用于研究生。使用 type=bachelor 选项，不是 type=master 或 type=doctor。bithesis 类基于 ctexbook，支持盲审格式（blindPeerReview=true）。关键宏包：expl3, l3keys2e, geometry, xcolor, zhlineskip, titletoc, graphicx, fancyhdr, pdfpages, setspace, booktabs, multirow, tikz, etoolbox, hyperref, caption, array, amsmath, amssymb, pifont, amsthm, listings, enumitem, fmtcount, unicode-math, ifplatform, datetime2, biblatex。参考文献使用 biblatex 配合 gb7714-2015 样式（中文引用标准）。编译流程：xelatex -> biber -> xelatex -> xelatex（必须使用 XeLaTeX，不支持 pdfLaTeX）。模板包含封面、原创性声明、摘要、目录、正文、结论、参考文献、附录、致谢等完整结构，符合北京理工大学本科生毕业设计（论文）书写规范。\n\n模板文件路径：undergraduate_thesis__1_/\n主文件：main.tex\n类文件：bithesis.cls\n必需字体文件：STXIHEI.TTF（华文细黑，用于封面标题）\n\n必需目录结构：\n- chapters/ (章节文件：0_abstract.tex, 1_chapter1.tex, 2_chapter2.tex 等)\n- misc/ (其他文件：1_originality.tex, 2_conclusion.tex, 3_reference.tex, 4_appendix.tex, 5_acknowledgements.tex, ref.bib)\n- images/ (图片文件：header.png 封面头部图片，bit_logo.png 等)\n\n最小工作示例：\n\\documentclass[type=bachelor]{bithesis}\n\\BITSetup{\n  cover = {\n    headerImage = images/header.png,\n    xiheiFont = STXIHEI.TTF,\n  },\n  info = {\n    title = 论文标题,\n    titleEn = Paper Title,\n    school = 学院名称,\n    major = 专业名称,\n    class = 班级,\n    author = 作者名,\n    studentId = 学号,\n    supervisor = 导师姓名,\n    keywords = {关键词1；关键词2},\n    keywordsEn = keyword1; keyword2,\n  },\n}\n\\usepackage[backend=biber,style=gb7714-2015]{biblatex}\n\\addbibresource{misc/ref.bib}\n\\begin{document}\n\\MakeCover\n\\begin{blindPeerReview}\n  \\includepdf{misc/1_originality.pdf}\n\\end{blindPeerReview}\n\\frontmatter\n\\input{chapters/0_abstract.tex}\n\\MakeTOC\n\\mainmatter\n\\input{chapters/1_chapter1.tex}\n\\backmatter\n\\input{misc/2_conclusion.tex}\n\\input{misc/3_reference.tex}\n\\input{misc/4_appendix.tex}\n\\input{misc/5_acknowledgements.tex}\n\\end{document}\n\n常用配置选项：\n- type: bachelor (本科生)\n- blindPeerReview: true (开启盲审格式)\n\n重要注意事项：\n1. 必须使用 XeLaTeX 编译，不支持 pdfLaTeX\n2. 需要 biber 处理参考文献（不是 bibtex）\n3. 编译方式有两种：\n   - 推荐方式：使用 latexmk 命令（自动处理编译流程）\n   - 手动方式：xelatex -> biber -> xelatex -> xelatex（需要编译多次）\n4. latexmkrc 文件已配置好，使用 latexmk 时会自动使用 XeLaTeX 和 biber\n5. 需要 STXIHEI.TTF 字体文件用于封面标题\n6. 需要 images/header.png 图片文件用于封面头部\n7. 中文支持需要相应中文字体\n8. 在 Linux/macOS 下可能需要安装中易字库或使用 ctex={fontset=windows} 选项\n9. macOS 用户建议使用 TeX Live/MacTeX 2023 或更新版本，否则参考文献可能被错误查重\n10. 参考文献样式使用 gb7714-2015（中国国家标准）\n11. 项目地址：https://github.com/BITNP/BIThesis\n12. 使用手册和文档：https://bithesis.bitnp.net\n\n章节结构和使用模式：\n\n摘要结构（chapters/0_abstract.tex）：\n\\begin{abstract}\n  中文摘要内容（本科生建议300-500字）\n\\end{abstract}\n\\begin{abstractEn}\n  English abstract content (must match Chinese abstract)\n\\end{abstractEn}\n\n章节结构（chapters/1_chapter*.tex）：\n\\chapter{章节标题}  % 一级标题\n\\label{chap:label}  % 可选标签\n\\section{节标题}  % 二级标题\n\\subsection{小节标题}  % 三级标题\n\n常用LaTeX元素：\n- 引用：\\cite{key}\n- 交叉引用：\\ref{label} 或 \\autoref{label}\n- 图片：\\begin{figure}[hbt]\\centering\\includegraphics[width=0.75\\textwidth]{images/filename}\\caption{标题}\\label{fig:label}\\end{figure}\n- 表格：\\begin{table}[hbt]\\centering\\caption{标题}\\label{tab:label}\\begin{tabular*}{0.9\\textwidth}{@{\\extracolsep{\\fill}}cccc}\\toprule...\\midrule...\\bottomrule\\end{tabular*}\\end{table}\n- 公式：\\begin{equation}\\label{eq:label}...\\end{equation}\n\n参考文献结构（misc/ref.bib）：\n使用 biblatex 格式，支持 @article, @inproceedings, @book 等类型。示例：\n@article{key,\n  title = {标题},\n  author = {作者1 and 作者2},\n  journal = {期刊名},\n  volume = {卷号},\n  number = {期号},\n  pages = {页码},\n  year = {年份},\n}\n\n参考文献显示（misc/3_reference.tex）：\n\\begin{bibprint}\n  \\printbibliography[heading=none]\n\\end{bibprint}\n\n结论（misc/2_conclusion.tex）：\n结论内容（单独排写）\n\n附录（misc/4_appendix.tex）：\n附录内容（可选）\n\n致谢（misc/5_acknowledgements.tex）：\n致谢内容\n\n文件组织：\n- chapters/0_abstract.tex：摘要（中英文）\n- chapters/1_chapter1.tex, 2_chapter2.tex...：各章节内容\n- misc/ref.bib：参考文献（与研究生模板不同，本科生只有一个 ref.bib 文件）\n- misc/1_originality.tex：原创性声明\n- misc/2_conclusion.tex：结论\n- misc/3_reference.tex：参考文献列表\n- misc/4_appendix.tex：附录（可选）\n- misc/5_acknowledgements.tex：致谢\n- images/：存放所有图片文件（包括封面需要的 header.png）\n\n与研究生模板的主要区别：\n1. 文档类选项：type=bachelor（本科生）vs type=master/doctor（研究生）\n2. 文件结构：本科生使用 misc/ref.bib，研究生使用 reference/main.bib 和 reference/pub.bib\n3. 章节文件命名：本科生使用 0_abstract.tex, 1_chapter1.tex，研究生使用 abstract.tex, chapter1.tex\n4. 封面配置：本科生需要 headerImage 和 xiheiFont，研究生不需要\n5. 后置部分：本科生没有个人成果清单和个人简介，研究生有\n6. 摘要字数：本科生300-500字，研究生硕士500-800字，博士1000-1200字",
        "metadata": {
            "journal_name": "BIThesis-Undergraduate",
            "template_type": "thesis",
            "documentclass": "bithesis",
            "base_class": "ctexbook",
            "key_packages": "expl3, l3keys2e, geometry, xcolor, zhlineskip, titletoc, graphicx, fancyhdr, pdfpages, setspace, booktabs, multirow, tikz, etoolbox, hyperref, caption, array, amsmath, amssymb, pifont, amsthm, listings, enumitem, fmtcount, unicode-math, ifplatform, datetime2, biblatex",
            "biblatex_style": "gb7714-2015",
            "format": "single column",
            "language": "chinese",
            "compiler": "XeLaTeX",
            "compilation_sequence": "xelatex -> biber -> xelatex -> xelatex",
            "institution": "北京理工大学",
            "degree_level": "undergraduate",
            "supports_blind_review": True,
            "template_path": "undergraduate_thesis__1_/",
            "main_file": "main.tex",
            "class_file": "bithesis.cls",
            "required_directories": "chapters/, misc/, images/",
            "required_fonts": "STXIHEI.TTF",
            "required_images": "images/header.png",
            "compilation_tools": "latexmk (recommended) or manual xelatex",
            "latexmkrc_file": "latexmkrc (configured for XeLaTeX + biber)",
            "documentation_url": "https://bithesis.bitnp.net",
            "github_url": "https://github.com/BITNP/BIThesis",
            "abstract_environments": "abstract (Chinese), abstractEn (English)",
            "chapter_structure": "\\chapter{}, \\section{}, \\subsection{}",
            "citation_commands": "\\cite{}",
            "cross_reference_commands": "\\ref{}, \\autoref{}",
            "figure_environment": "figure with \\includegraphics, \\caption, \\label",
            "table_environment": "table with tabular*, \\toprule, \\midrule, \\bottomrule",
            "equation_environments": "equation",
            "bibliography_files": "misc/ref.bib (single file, unlike graduate template)",
            "misc_files": "1_originality.tex, 2_conclusion.tex, 3_reference.tex, 4_appendix.tex, 5_acknowledgements.tex"
        }
    }
]

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
        metadatas = [item["metadata"] for item in LATEX_TEMPLATE_KNOWLEDGE]
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
                new_metadatas.append(item["metadata"])
                new_ids.append(template_id)
            elif item['journal'] in ['BIThesis-Graduate', 'BIThesis-Undergraduate']:
                # BIThesis 模板需要更新（删除旧的后添加新的）
                try:
                    db.delete_documents(ids=[template_id])
                    updated_templates.append(item['journal'])
                    new_documents.append(item["document"])
                    new_metadatas.append(item["metadata"])
                    new_ids.append(template_id)
                except Exception as e:
                    # 如果删除失败（可能不存在），仍然尝试添加
                    print(f"更新 {item['journal']} 时删除旧条目失败（可能不存在）: {e}")
                    updated_templates.append(item['journal'])
                    new_documents.append(item["document"])
                    new_metadatas.append(item["metadata"])
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

