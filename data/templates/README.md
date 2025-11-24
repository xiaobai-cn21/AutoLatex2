# LaTeX 模板文件目录

本目录包含各种期刊和会议的 LaTeX 模板文件。

## 模板文件列表

### 国际会议模板
- `ieee_conference.tex` - IEEE 会议模板
- `neurips.tex` - NeurIPS 会议模板
- `cvpr.tex` - CVPR 会议模板
- `acm_sigconf.tex` - ACM SIG 会议模板
- `aaai.tex` - AAAI 会议模板
- `icml.tex` - ICML 会议模板

### 中文期刊模板
- `chinese_journal.tex` - 中文期刊通用模板（适用于计算机学报、软件学报等）

## 使用方法

这些模板文件可以通过 `TemplateTools` 类读取：

```python
from src.autolatex.tools.template_tools import TemplateTools

tool = TemplateTools()
template_content = tool._run("ieee_conference")
```

## 添加新模板

1. 在 `data/templates/` 目录下创建新的 `.tex` 文件
2. 在 `src/autolatex/tools/knowledge_base.py` 的 `LATEX_TEMPLATE_KNOWLEDGE` 列表中添加对应的元数据

## 注意事项

- 模板文件名应该与知识库中的 `template_name` 对应
- 中文模板需要使用 `ctex` 或 `xeCJK` 宏包支持中文
- 确保模板文件包含完整的 LaTeX 文档结构

