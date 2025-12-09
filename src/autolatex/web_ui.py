import gradio as gr
import os
import sys
import shutil
from pathlib import Path
import requests

# 添加项目根目录到路径，以便支持直接运行和模块导入
# 计算项目根目录（src/ 的父目录）
current_file = Path(__file__).resolve()
# web_ui.py 位于: src/autolatex/web_ui.py
# 向上2级到达 src/，再向上1级到达项目根目录
src_dir = current_file.parent.parent  # src/
project_root = src_dir.parent  # 项目根目录

# 添加 src 目录到路径（用于绝对导入 autolatex.*）
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 导入模板工具
from autolatex.tools.template_manager import list_available_journals
from autolatex.tools.template_tools import TemplateRetrievalTool

# 自定义 CSS 样式
custom_css = """
/* 整体布局 */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    max-width: 100% !important;
}

/* 主容器 */
.main-container {
    display: flex;
    height: 100vh;
    overflow: hidden;
}

/* 左侧边栏 */
.sidebar {
    width: 250px !important;
    background: #ffffff;
    border-right: 1px solid #e5e5e5;
    display: flex;
    flex-direction: column;
    height: 100vh;
    position: fixed !important;
    left: 0 !important;
    top: 0 !important;
    z-index: 1000;
    overflow-y: auto;
    transition: left 0.3s ease, display 0.3s ease;
}

.sidebar-header {
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #e5e5e5;
}

.logo-container {
    display: flex;
    align-items: center;
    gap: 10px;
}

.logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 20px;
}

.logo-text {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
}

.collapse-icon {
    color: #9ca3af;
    cursor: pointer;
    font-size: 18px;
    user-select: none;
    transition: color 0.2s;
}

.collapse-icon:hover {
    color: #6b7280;
}

/* 导航菜单 */
.nav-menu {
    flex: 1;
    padding: 10px 0;
    overflow-y: auto;
}

.nav-item {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    transition: background 0.2s;
    position: relative;
}

.nav-item:hover {
    background: #f9fafb;
}

.nav-item.active {
    background: #f0f0ff;
    border-left: 3px solid #8b5cf6;
}

.nav-item-icon {
    font-size: 20px;
    width: 24px;
    text-align: center;
}

.nav-item-content {
    flex: 1;
}

.nav-item-title {
    font-size: 14px;
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 2px;
}

.nav-item-desc {
    font-size: 12px;
    color: #6b7280;
}

.nav-item-arrow {
    color: #9ca3af;
    font-size: 14px;
}

/* 底部链接 */
.sidebar-footer {
    padding: 20px;
    border-top: 1px solid #e5e5e5;
}

.footer-item {
    padding: 10px 0;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #1f2937;
    font-size: 14px;
    cursor: pointer;
}

.footer-item:hover {
    color: #8b5cf6;
}

/* 主内容区 */
.main-content {
    margin-left: 250px;
    flex: 1;
    background: #f5f5f5;
    min-height: 100vh;
    position: relative;
    padding: 30px 40px;
    width: calc(100% - 250px);
    transition: margin-left 0.3s ease, width 0.3s ease;
}

/* 点状网格背景 */
.main-content::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: radial-gradient(circle, #d1d5db 1px, transparent 1px);
    background-size: 20px 20px;
    opacity: 0.3;
    pointer-events: none;
}

.content-wrapper {
    position: relative;
    z-index: 1;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
}

/* 横幅 */
.banner {
    background: linear-gradient(135deg, #ffc107 0%, #ffb300 100%);
    border-radius: 12px;
    padding: 15px 20px;
    margin-bottom: 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.banner-text {
    color: #1f2937;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
}

.banner-close {
    color: #1f2937;
    cursor: pointer;
    font-size: 20px;
    font-weight: bold;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background 0.2s;
}

.banner-close:hover {
    background: rgba(0,0,0,0.1);
}

/* 标题区域 */
.title-section {
    text-align: center;
    margin-bottom: 20px;
}

.main-title {
    font-size: 36px;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 12px;
}

.subtitle {
    font-size: 16px;
    color: #6b7280;
}

/* 上传卡片 */
.upload-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 45px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.pdf-icon-container {
    text-align: center;
    margin-bottom: 10px;
}

.pdf-icon {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 40px;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.upload-button {
    width: auto !important;
    min-width: 280px;
    padding: 12px 24px !important;
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin: 0 auto 12px auto;
    transition: transform 0.2s, box-shadow 0.2s;
}

.upload-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
}

.file-info {
    text-align: center;
    color: #6b7280;
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 10px;
}

.model-section {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #e5e5e5;
}

.model-label {
    font-size: 14px;
    color: #1f2937;
    font-weight: 500;
    white-space: nowrap;
}

.model-dropdown {
    flex: 1;
}

.translate-button {
    padding: 10px 20px;
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
    transition: transform 0.2s, box-shadow 0.2s;
}

.translate-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

/* 隐藏 Gradio 默认样式 */
.hide-gradio-default {
    display: none !important;
}

/* 隐藏 Gradio 页脚链接 */
footer {
    display: none !important;
}

.gradio-footer {
    display: none !important;
}

a[href*="api"], a[href*="gradio"], a[href*="settings"] {
    display: none !important;
}

/* 使用 JavaScript 隐藏包含特定文本的元素 */

/* 调整 Gradio 组件样式 */
.gradio-container .main {
    padding: 0 !important;
}

/* 文件上传组件样式调整 */
input[type="file"] {
    display: none;
}

/* 下拉框样式 */
select, .gradio-dropdown {
    padding: 10px 12px;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    background: #ffffff;
    font-size: 14px;
    color: #1f2937;
}

/* 确保侧边栏在最上层 */
.sidebar {
    z-index: 1000;
}

/* 调整主内容区域以适应侧边栏 */
#root > div > div {
    margin-left: 250px;
}

/* 覆盖 Gradio 默认主题 */
.dark {
    --background-fill-primary: #f5f5f5;
}

/* 确保 body 和 html 没有默认边距 */
body, html {
    margin: 0;
    padding: 0;
    overflow-x: hidden;
}

/* 调整 Gradio Blocks 容器 */
.gradio-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* 主内容区域样式增强 */
.main-content {
    padding: 30px 40px;
}

.sidebar-collapsed .main-content {
    margin-left: 0 !important;
    width: 100% !important;
}

.sidebar-collapsed #root > div > div {
    margin-left: 0 !important;
}

/* 按钮样式覆盖 */
button.upload-button {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
    border: none !important;
    color: white !important;
}

button.translate-button {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
    border: none !important;
    color: white !important;
}

button.delete-button {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    border: none !important;
    color: white !important;
    padding: 10px 20px !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    white-space: nowrap;
    transition: transform 0.2s, box-shadow 0.2s;
    margin-top: 1px;
}

button.delete-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.delete-button-container {
    text-align: center;
    margin-top: 8px;
}

/* 删除按钮行样式 - 减少间距 */
.delete-button-row {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

.delete-button-row > div {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* 展开侧边栏按钮（当侧边栏隐藏时显示） */
.expand-sidebar-btn {
    position: fixed;
    left: 0;
    top: 20px;
    width: 30px;
    height: 40px;
    background: #ffffff;
    border: 1px solid #e5e5e5;
    border-left: none;
    border-radius: 0 8px 8px 0;
    display: none;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 999;
    color: #6b7280;
    font-size: 16px;
    box-shadow: 2px 0 4px rgba(0,0,0,0.1);
    transition: all 0.2s;
}

.expand-sidebar-btn:hover {
    background: #f9fafb;
    color: #8b5cf6;
}

/* 处理结果输出框可拖拽缩放样式 */
.resizable-output {
    position: relative;
}

.resizable-output textarea {
    resize: both;
    min-height: 42px;  /* 约等于单行高度，便于收缩到最小 */
    max-height: 70vh;
    min-width: 320px;
    padding: 14px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    background: #ffffff;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    font-family: "Fira Code", "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    line-height: 1.5;
}

.resizable-output textarea:focus {
    outline: none;
    border-color: #8b5cf6;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.25);
}
"""

# HTML 模板
sidebar_html = """
<div class="sidebar">
    <div class="sidebar-header">
        <div class="logo-container">
            <div class="logo-icon">AT</div>
            <div class="logo-text">AutoTex</div>
        </div>
        <div class="collapse-icon" id="sidebar-toggle" onclick="window.toggleSidebar()">←</div>
    </div>
    <div class="nav-menu">
        <div class="nav-item active">
            <div class="nav-item-icon">📝</div>
            <div class="nav-item-content">
                <div class="nav-item-title">LaTeX排版</div>
                <div class="nav-item-desc">智能转换论文格式</div>
            </div>
            <div class="nav-item-arrow">→</div>
        </div>
        <div class="nav-item">
            <div class="nav-item-icon">📚</div>
            <div class="nav-item-content">
                <div class="nav-item-title">期刊模板</div>
                <div class="nav-item-desc">支持多种期刊格式</div>
            </div>
            <div class="nav-item-arrow">→</div>
        </div>
        <div class="nav-item">
            <div class="nav-item-icon">⚙️</div>
            <div class="nav-item-content">
                <div class="nav-item-title">格式设置</div>
                <div class="nav-item-desc">自定义排版参数</div>
            </div>
            <div class="nav-item-arrow">→</div>
        </div>
    </div>
    <div class="sidebar-footer">
        <div class="footer-item">
            <span>📖</span>
            <span>使用文档</span>
        </div>
        <div class="footer-item">
            <span>👤</span>
            <span>登录/注册</span>
        </div>
    </div>
</div>
"""

title_html = """
<div class="title-section">
    <div class="main-title">LaTeX智能排版专家</div>
    <div class="subtitle">将Word/Markdown/Txt论文智能转换为符合期刊要求的LaTeX格式</div>
</div>
"""

def get_available_templates():
    """获取所有可用的模板列表"""
    try:
        templates = list_available_journals()
        if templates:
            return templates
        return ["IEEE Transactions", "ACM Conference", "Springer LNCS", "Elsevier Article", "Nature", "Science", "自定义模板"]
    except Exception as e:
        # 如果获取失败，返回默认列表
        return ["IEEE Transactions", "ACM Conference", "Springer LNCS", "Elsevier Article", "Nature", "Science", "自定义模板"]

def preview_template(template_name: str) -> str:
    """预览模板内容"""
    if not template_name or template_name == "自定义模板":
        return "请选择一个模板名称进行预览"
    
    try:
        tool = TemplateRetrievalTool()
        template_content = tool._run(template_name)
        
        # 如果内容太长，只显示前5000个字符
        if len(template_content) > 5000:
            return f"{template_content[:5000]}\n\n... (内容已截断，共 {len(template_content)} 个字符)"
        return template_content
    except Exception as e:
        return f"预览模板失败: {str(e)}"

def process_file(file, journal_type):
    """处理上传的文件并生成LaTeX（通过后端 REST API 上传 + 转换）"""
    print("[Web UI] process_file 被调用")  # 调试日志
    if file is None:
        print("[Web UI] 未选择文件")
        return "请先上传论文文件"

    # 1. 调用后端 /api/v1/paper/upload 接口上传文件
    api_base = os.environ.get("AUTOLATEX_API_BASE", "http://127.0.0.1:8000")
    upload_url = f"{api_base}/api/v1/paper/upload"
    convert_url = f"{api_base}/api/v1/paper/convert"

    try:
        # Gradio `file` 为一个带临时路径的对象，file.name 为临时文件路径
        # 尝试获取原始文件名（部分 Gradio 版本会带有 orig_name）
        orig_name = getattr(file, "orig_name", None) or os.path.basename(file.name)

        print(f"[Web UI] 准备上传文件: {orig_name}, 临时路径: {file.name}")
        with open(file.name, "rb") as f:
            files = {"file": (orig_name, f, "application/octet-stream")}
            resp = requests.post(upload_url, files=files, timeout=60)

        if resp.status_code != 200:
            print(f"[Web UI] 上传接口 HTTP {resp.status_code}: {resp.text}")
            return f"❌ 调用上传接口失败，HTTP {resp.status_code}: {resp.text}"

        data = resp.json()
        print(f"[Web UI] 上传接口返回: {data}")
        if not data.get("success"):
            return f"❌ 上传接口返回失败: {data.get('message') or data}"

        file_path = data.get("file_path")
        filename = data.get("filename", orig_name)
    except Exception as e:
        print(f"[Web UI] 通过 REST API 上传文件失败: {e}")
        return f"❌ 通过 REST API 上传文件失败: {str(e)}"

    # 2. 调用 /api/v1/paper/convert 进行论文转换
    try:
        payload = {
            "file_path": file_path,
            "journal_name": journal_type or "",
            "topic": "自动将word、txt、markdown格式论文转化为Latex格式论文",
        }
        print(f"[Web UI] 调用转换接口, payload={payload}")
        resp_conv = requests.post(convert_url, json=payload, timeout=600)
        if resp_conv.status_code != 200:
            print(f"[Web UI] 转换接口 HTTP {resp_conv.status_code}: {resp_conv.text}")
            return (
                "✅ 文件上传成功，但转换接口调用失败。\n"
                f"文件名: {filename}\n"
                f"后端保存路径: {file_path}\n\n"
                f"调用 /api/v1/paper/convert 失败，HTTP {resp_conv.status_code}: {resp_conv.text}"
            )

        conv_data = resp_conv.json()
        print(f"[Web UI] 转换接口返回: {conv_data}")
        if not conv_data.get("success"):
            return (
                "✅ 文件上传成功，但转换失败。\n"
                f"文件名: {filename}\n"
                f"后端保存路径: {file_path}\n\n"
                f"转换消息: {conv_data.get('message')}\n"
                f"错误信息: {conv_data.get('error')}"
            )

        output_path = conv_data.get("output_path")
        message = conv_data.get("message", "论文转换成功")

        return (
            f"✅ 论文文件已通过 REST API 上传并转换成功。\n"
            f"文件名: {filename}\n"
            f"上传保存路径: {file_path}\n\n"
            f"转换结果: {message}\n"
            f"LaTeX 输出路径: {output_path}"
        )
    except Exception as e:
        print(f"[Web UI] 调用转换接口异常: {e}")
        return (
            "✅ 文件上传成功，但在调用转换接口时发生异常。\n"
            f"文件名: {filename}\n"
            f"后端保存路径: {file_path}\n\n"
            f"异常信息: {str(e)}"
        )

# JavaScript 代码用于布局调整
sidebar_toggle_js = """
<script>
window.toggleSidebar = window.toggleSidebar || function() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    let expandBtn = document.getElementById('expand-sidebar-btn');
    const body = document.body;

    if (!expandBtn) {
        expandBtn = document.createElement('div');
        expandBtn.id = 'expand-sidebar-btn';
        expandBtn.className = 'expand-sidebar-btn';
        expandBtn.textContent = '→';
        expandBtn.onclick = function() { window.showSidebar(); };
        expandBtn.style.display = 'none';
        document.body.appendChild(expandBtn);
    }

    if (sidebar && mainContent) {
        sidebar.style.display = 'none';
        sidebar.style.left = '-250px';
        mainContent.style.marginLeft = '0';
        mainContent.style.width = '100%';
        expandBtn.style.display = 'flex';
        if (body) {
            body.classList.add('sidebar-collapsed');
        }
    }
};

window.showSidebar = window.showSidebar || function() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const expandBtn = document.getElementById('expand-sidebar-btn');
    const body = document.body;

    if (sidebar && mainContent) {
        sidebar.style.display = 'flex';
        sidebar.style.left = '0';
        mainContent.style.marginLeft = '250px';
        mainContent.style.width = 'calc(100% - 250px)';
        if (expandBtn) {
            expandBtn.style.display = 'none';
        }
        if (body) {
            body.classList.remove('sidebar-collapsed');
        }
    }
};
</script>
"""


layout_js = """
<script>
// 确保函数在全局作用域中定义
window.toggleSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    let expandBtn = document.getElementById('expand-sidebar-btn');
    const body = document.body;
    
    if (!expandBtn) {
        expandBtn = document.createElement('div');
        expandBtn.id = 'expand-sidebar-btn';
        expandBtn.className = 'expand-sidebar-btn';
        expandBtn.textContent = '→';
        expandBtn.onclick = function() { window.showSidebar(); };
        expandBtn.style.display = 'none';
        document.body.appendChild(expandBtn);
    }
    
    if (sidebar && mainContent) {
        sidebar.style.display = 'none';
        sidebar.style.left = '-250px';
        mainContent.style.marginLeft = '0';
        mainContent.style.width = '100%';
        expandBtn.style.display = 'flex';
        if (body) {
            body.classList.add('sidebar-collapsed');
        }
    }
};

window.showSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const expandBtn = document.getElementById('expand-sidebar-btn');
    const body = document.body;
    
    if (sidebar && mainContent) {
        sidebar.style.display = 'flex';
        sidebar.style.left = '0';
        mainContent.style.marginLeft = '250px';
        mainContent.style.width = 'calc(100% - 250px)';
        if (expandBtn) {
            expandBtn.style.display = 'none';
        }
        if (body) {
            body.classList.remove('sidebar-collapsed');
        }
    }
};

(function() {
    // 等待 DOM 加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLayout);
    } else {
        initLayout();
    }
    
    function initLayout() {
        // 确保侧边栏固定在左侧
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.style.position = 'fixed';
            sidebar.style.left = '0';
            sidebar.style.top = '0';
            sidebar.style.height = '100vh';
            sidebar.style.zIndex = '1000';
        }
        
        // 调整主内容区域的左边距
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.marginLeft = '250px';
        }
        
        // 调整 Gradio 容器
        const gradioContainer = document.querySelector('.gradio-container');
        if (gradioContainer) {
            gradioContainer.style.maxWidth = '100%';
            gradioContainer.style.padding = '0';
        }
        
        // 隐藏 Gradio 页脚链接
        const footer = document.querySelector('footer');
        if (footer) {
            footer.style.display = 'none';
        }
        
        // 隐藏所有包含特定文本的链接
        const allLinks = document.querySelectorAll('a');
        allLinks.forEach(link => {
            const text = link.textContent || link.innerText;
            if (text.includes('APIを介して使用') || 
                text.includes('Gradioで作成') || 
                text.includes('設定') ||
                link.href.includes('/api') ||
                link.href.includes('/gradio') ||
                link.href.includes('/settings')) {
                link.style.display = 'none';
                // 也隐藏父元素（如果是单独的链接容器）
                if (link.parentElement && link.parentElement.tagName === 'SPAN') {
                    link.parentElement.style.display = 'none';
                }
            }
        });
        
        // 隐藏整个页脚容器
        const footerContainers = document.querySelectorAll('footer, .gradio-footer');
        footerContainers.forEach(container => {
            container.style.display = 'none';
        });
        
    }
    
    // 监听 Gradio 加载完成事件
    window.addEventListener('load', initLayout);
    
    // 使用 MutationObserver 监听 DOM 变化
    const observer = new MutationObserver(function(mutations) {
        initLayout();
        // 确保事件绑定
        setupSidebarToggle();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // 单独的函数来设置侧边栏切换
    function setupSidebarToggle() {
        const sidebarToggle = document.getElementById('sidebar-toggle');
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        
        if (sidebarToggle && sidebar && mainContent && !sidebarToggle.dataset.listenerAttached) {
            sidebarToggle.dataset.listenerAttached = 'true';
            
            // 创建展开按钮
            let expandBtn = document.getElementById('expand-sidebar-btn');
            if (!expandBtn) {
                expandBtn = document.createElement('div');
                expandBtn.id = 'expand-sidebar-btn';
                expandBtn.className = 'expand-sidebar-btn';
                expandBtn.textContent = '→';
                expandBtn.style.display = 'none';
                document.body.appendChild(expandBtn);
            }
            
            function hideSidebar() {
                if (sidebar && mainContent && expandBtn) {
                    sidebar.style.display = 'none';
                    sidebar.style.left = '-250px';
                    mainContent.style.marginLeft = '0';
                    mainContent.style.width = '100%';
                    expandBtn.style.display = 'flex';
                }
            }
            
            function showSidebar() {
                if (sidebar && mainContent && expandBtn) {
                    sidebar.style.display = 'flex';
                    sidebar.style.left = '0';
                    mainContent.style.marginLeft = '250px';
                    mainContent.style.width = 'calc(100% - 250px)';
                    expandBtn.style.display = 'none';
                }
            }
            
            sidebarToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Toggle clicked');
                window.toggleSidebar();
            });
            
            expandBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                window.showSidebar();
            });
        }
    }
    
    // 使用事件委托作为备用方案
    document.addEventListener('click', function(e) {
        if (e.target && (e.target.id === 'sidebar-toggle' || e.target.classList.contains('collapse-icon'))) {
            e.preventDefault();
            e.stopPropagation();
            window.toggleSidebar();
        }
        if (e.target && e.target.id === 'expand-sidebar-btn') {
            e.preventDefault();
            e.stopPropagation();
            window.showSidebar();
        }
    });
    
    // 立即尝试设置
    setupSidebarToggle();
    
    // 延迟设置，确保 Gradio 完全加载
    setTimeout(setupSidebarToggle, 500);
    setTimeout(setupSidebarToggle, 1000);
    setTimeout(setupSidebarToggle, 2000);
    setInterval(setupSidebarToggle, 3000);
})();
</script>
"""

def create_interface():
    with gr.Blocks(
        css=custom_css,
        theme=gr.themes.Soft(),
        head=sidebar_toggle_js + layout_js,
    ) as app:
        # 添加侧边栏 HTML（固定在左侧）
        gr.HTML(sidebar_html)
        
        # 主内容区域
        with gr.Column(elem_classes=["main-content"]):
            content_wrapper = gr.Column(elem_classes=["content-wrapper"])
            with content_wrapper:
                # 标题
                gr.HTML(title_html)
                
                # 上传卡片
                with gr.Column(elem_classes=["upload-card"]):
                    gr.HTML("""
                    <div class="pdf-icon-container">
                        <div class="pdf-icon">📄</div>
                    </div>
                    """)
                    
                    # 文件上传组件（隐藏默认样式）
                    file_upload = gr.File(
                        label="",
                        file_types=[".doc", ".docx", ".txt", ".md", ".markdown"],
                        elem_classes=["hide-gradio-default"]
                    )
                    
                    # 自定义上传按钮和删除按钮（居中显示）
                    with gr.Column():
                        with gr.Row():
                            gr.HTML('<div style="flex: 1;"></div>')
                            upload_btn = gr.Button(
                                "上传论文文件 ↑",
                                elem_classes=["upload-button"],
                                scale=0
                            )
                            gr.HTML('<div style="flex: 1;"></div>')
                        
                        # 删除按钮容器（初始隐藏，紧贴上传按钮）
                        with gr.Row(elem_classes=["delete-button-row"]):
                            gr.HTML('<div style="flex: 1;"></div>')
                            delete_btn = gr.Button(
                                "删除文件 ✕",
                                elem_classes=["delete-button"],
                                scale=0,
                                visible=False
                            )
                            gr.HTML('<div style="flex: 1;"></div>')
                    
                    gr.HTML("""
                    <div class="file-info">
                        <div>支持文件类型: Word (.doc, .docx) | Markdown (.md, .markdown) | 文本 (.txt)</div>
                        <div>最大文件大小: 50MB</div>
                    </div>
                    """)
                    
                    # 期刊类型选择和生成按钮
                    with gr.Row(elem_classes=["model-section"]):
                        gr.HTML('<div class="model-label">期刊类型</div>')
                        # 动态获取模板列表
                        available_templates = get_available_templates()
                        journal_dropdown = gr.Dropdown(
                            choices=available_templates,
                            value=available_templates[0] if available_templates else "自定义模板",
                            label="",
                            scale=2,
                            elem_classes=["model-dropdown"],
                            container=False,
                            allow_custom_value=True,
                            info="从下拉列表选择或输入自定义模板名称"
                        )
                        preview_btn = gr.Button(
                            "预览模板 👁️",
                            elem_classes=["translate-button"],
                            scale=0,
                            size="sm"
                        )
                        generate_btn = gr.Button(
                            "生成LaTeX 📦",
                            elem_classes=["translate-button"],
                            scale=0
                        )
                
                # 模板预览区域
                template_preview = gr.Code(
                    label="模板预览",
                    language="latex",
                    visible=False,
                    lines=15,
                    interactive=False
                )
                
                # 输出区域（用于显示处理结果）
                output = gr.Textbox(
                    label="处理结果",
                    visible=True,   # 默认显示，便于直接看到上传/转换结果
                    interactive=False,
                    elem_classes=["resizable-output"]
                )
                
                # 绑定事件
                def trigger_upload():
                    return gr.update()
                
                upload_btn.click(
                    fn=trigger_upload,
                    inputs=[],
                    outputs=[],
                    js="() => { const fileInput = document.querySelector('input[type=file]'); if(fileInput) fileInput.click(); }"
                )
                
                # 文件上传/删除处理函数
                def handle_file_change(file):
                    """处理文件变化：显示/隐藏删除按钮，更新输出信息"""
                    if file is not None:
                        return (
                            gr.update(visible=True),  # 显示删除按钮
                            f"文件已上传: {os.path.basename(file.name)}"
                        )
                    else:
                        return (
                            gr.update(visible=False),  # 隐藏删除按钮
                            "请上传文件"
                        )
                
                def delete_file():
                    """删除文件：清除文件选择并隐藏删除按钮"""
                    return (
                        None,  # 清除文件
                        gr.update(visible=False),  # 隐藏删除按钮
                        "文件已删除，请重新上传文件"
                    )
                
                # 文件上传变化事件
                file_upload.change(
                    fn=handle_file_change,
                    inputs=[file_upload],
                    outputs=[delete_btn, output]
                )
                
                # 删除按钮点击事件
                delete_btn.click(
                    fn=delete_file,
                    inputs=[],
                    outputs=[file_upload, delete_btn, output]
                )
                
                # 预览模板按钮事件
                def show_template_preview(template_name):
                    preview_content = preview_template(template_name)
                    return gr.update(value=preview_content, visible=True)
                
                preview_btn.click(
                    fn=show_template_preview,
                    inputs=[journal_dropdown],
                    outputs=[template_preview]
                )
                
                generate_btn.click(
                    fn=process_file,
                    inputs=[file_upload, journal_dropdown],
                    outputs=[output]
                )
    
    return app

# 向后兼容：保留 create_ui 作为别名
def create_ui() -> gr.Blocks:
    """创建 Gradio Web UI（向后兼容别名）"""
    return create_interface()

if __name__ == "__main__":
    app = create_interface()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)

