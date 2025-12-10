"""
模板管理器模块

提供读取和管理期刊模板文件的功能。
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


def get_journal_template_files(journal_name: str, base_path: Optional[str] = None) -> Dict[str, str]:
    """
    读取指定期刊模板文件夹中的所有文件。
    
    Args:
        journal_name: 期刊名称（例如 'cvpr', 'ieee'）
        base_path: 模板基础路径，默认为 None（使用默认路径）
    
    Returns:
        字典，键为文件相对路径，值为文件内容
    
    Raises:
        FileNotFoundError: 如果模板目录不存在
    """
    if base_path is None:
        # 默认路径：项目根目录/模板/{journal_name}
        # 通过 __file__ 动态计算项目根目录
        # __file__ 位于: src/autolatex/tools/template_manager/manager.py
        # 向上5级到达项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        template_dir = project_root / "模板" / journal_name
    else:
        template_dir = Path(base_path) / journal_name
    
    if not template_dir.exists() or not template_dir.is_dir():
        raise FileNotFoundError(f"模板目录不存在: {template_dir}")
    
    template_files: Dict[str, str] = {}
    
    # 递归遍历模板目录中的所有文件
    for file_path in template_dir.rglob("*"):
        if file_path.is_file():
            # 计算相对路径（相对于模板目录）
            relative_path = file_path.relative_to(template_dir)
            try:
                # 读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    template_files[str(relative_path)] = f.read()
            except (UnicodeDecodeError, PermissionError):
                # 跳过二进制文件或无法读取的文件
                continue
    
    return template_files


def get_journal_template_dir(journal_name: str, base_path: Optional[str] = None) -> str:
    """
    获取指定期刊模板文件夹的绝对路径。
    
    Args:
        journal_name: 期刊名称（例如 'cvpr', 'ieee'）
        base_path: 模板基础路径，默认为 None（使用默认路径）
    
    Returns:
        模板目录的绝对路径字符串
    
    Raises:
        FileNotFoundError: 如果模板目录不存在
    """
    if base_path is None:
        # 默认路径：项目根目录/模板/{journal_name}
        # 通过 __file__ 动态计算项目根目录
        # __file__ 位于: src/autolatex/tools/template_manager/manager.py
        # 向上5级到达项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        template_dir = project_root / "模板" / journal_name
    else:
        template_dir = Path(base_path) / journal_name
    
    template_dir = template_dir.resolve()
    
    if not template_dir.exists() or not template_dir.is_dir():
        raise FileNotFoundError(f"模板目录不存在: {template_dir}")
    
    return str(template_dir)


def list_available_journals(base_path: Optional[str] = None) -> List[str]:
    """
    列出所有可用的期刊模板。
    
    Args:
        base_path: 模板基础路径，默认为 None（使用默认路径）
    
    Returns:
        期刊名称列表
    """
    if base_path is None:
        # 默认路径：项目根目录/模板/
        # 通过 __file__ 动态计算项目根目录
        # __file__ 位于: src/autolatex/tools/template_manager/manager.py
        # 向上5级到达项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        journals_dir = project_root / "模板"
    else:
        journals_dir = Path(base_path)
    
    if not journals_dir.exists():
        return []
    
    journals = []
    for item in journals_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            journals.append(item.name)
    
    return sorted(journals)

