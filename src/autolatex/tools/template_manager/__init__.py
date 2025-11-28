"""
模板管理器模块

提供读取和管理期刊模板文件的功能。
"""

from .manager import (
    get_journal_template_files,
    get_journal_template_dir,
    list_available_journals,
)

__all__ = [
    "get_journal_template_files",
    "get_journal_template_dir",
    "list_available_journals",
]

