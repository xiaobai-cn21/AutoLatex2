// 页面加载时获取期刊列表
async function loadJournalList() {
    const dropdown = document.getElementById('journal-dropdown');
    if (!dropdown) return;
    
    try {
        const response = await fetch('/api/get-journals');
        const result = await response.json();
        
        // 清空下拉框
        dropdown.innerHTML = '';
        
        if (result.success && result.journals && result.journals.length > 0) {
            // 添加所有期刊选项
            result.journals.forEach(journal => {
                const option = document.createElement('option');
                option.value = journal;
                option.textContent = journal;
                dropdown.appendChild(option);
            });
            
            // 设置默认选中第一个
            if (dropdown.options.length > 0) {
                dropdown.selectedIndex = 0;
            }
        } else {
            // 如果获取失败，只显示"自定义模板"
            const option = document.createElement('option');
            option.value = '自定义模板';
            option.textContent = '自定义模板';
            dropdown.appendChild(option);
            console.warn('获取期刊列表失败，只显示自定义模板:', result.error);
        }
    } catch (error) {
        console.error('加载期刊列表时出错:', error);
        // 如果出错，只显示"自定义模板"
        dropdown.innerHTML = '';
        const option = document.createElement('option');
        option.value = '自定义模板';
        option.textContent = '自定义模板';
        dropdown.appendChild(option);
    }
}

// 页面加载完成后获取期刊列表
document.addEventListener('DOMContentLoaded', function() {
    loadJournalList();
});

// 侧边栏切换功能
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

// 图片上传区域展开/收起
function toggleImageUpload() {
    const content = document.getElementById('image-upload-content');
    const toggle = document.getElementById('image-upload-toggle');
    const isExpanded = content.classList.contains('image-upload-content-expanded');

    if (isExpanded) {
        content.classList.remove('image-upload-content-expanded');
        content.classList.add('image-upload-content-collapsed');
        toggle.textContent = '▼';
    } else {
        content.classList.remove('image-upload-content-collapsed');
        content.classList.add('image-upload-content-expanded');
        toggle.textContent = '▲';
    }
}

// 文件上传处理
let uploadedFile = null;
function handleFileChange(event) {
    const file = event.target.files[0];
    if (file) {
        uploadedFile = file;
        document.getElementById('delete-button-row').style.display = 'flex';
        
        // 显示文件名和扩展名
        const fileName = file.name;
        const fileExtension = fileName.split('.').pop().toUpperCase();
        const fileNameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
        
        const uploadedFileInfo = document.getElementById('uploaded-file-info');
        const uploadedFileName = document.getElementById('uploaded-file-name');
        uploadedFileName.textContent = `已上传: ${fileNameWithoutExt}.${fileExtension}`;
        uploadedFileInfo.style.display = 'block';
        
        // 清空输出区域
        // 输出区域已删除
    }
}

function deleteFile() {
    uploadedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('delete-button-row').style.display = 'none';
    document.getElementById('uploaded-file-info').style.display = 'none';
    // 输出区域已删除
}

// 图片上传处理
let uploadedImages = [];
function handleImageUpload(event) {
    const files = Array.from(event.target.files);
    files.forEach(file => {
        if (file.type === 'image/png') {
            const reader = new FileReader();
            reader.onload = function(e) {
                uploadedImages.push({
                    name: file.name,
                    data: e.target.result,
                    file: file  // 保存原始文件对象以便上传
                });
                updateImageGallery();
            };
            reader.readAsDataURL(file);
        }
    });
}

function updateImageGallery() {
    const gallery = document.getElementById('image-display');
    if (uploadedImages.length === 0) {
        gallery.innerHTML = '<div class="empty-gallery-message">暂无公式图片，请上传</div>';
        return;
    }

    let html = '<div class="image-gallery-container">';
    uploadedImages.forEach((img, index) => {
        html += `
            <div class="image-item-wrapper">
                <img src="${img.data}" alt="${img.name}">
                <button class="image-delete-btn" onclick="deleteImage(${index})">×</button>
            </div>
        `;
    });
    html += '</div>';
    gallery.innerHTML = html;
}

function deleteImage(index) {
    uploadedImages.splice(index, 1);
    updateImageGallery();
}

// 预览模板
async function previewTemplate() {
    const templateName = document.getElementById('journal-dropdown').value;
    const previewDiv = document.getElementById('template-preview');
    const previewContent = document.getElementById('template-preview-content');
    
    if (!templateName || templateName === "自定义模板") {
        previewContent.textContent = "请选择一个模板名称进行预览";
        previewDiv.classList.add('visible');
        return;
    }
    
    previewContent.textContent = '正在加载模板预览...';
    previewDiv.classList.add('visible');
    
    try {
        const response = await fetch('/api/preview-template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ template_name: templateName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            previewContent.textContent = result.content;
        } else {
            previewContent.textContent = `预览失败: ${result.content}`;
        }
    } catch (error) {
        previewContent.textContent = `预览失败: ${error.message}`;
    }
}

// 生成 LaTeX
async function generateLatex() {
    const downloadContainer = document.getElementById('download-link-container');
    const downloadLink = document.getElementById('download-link');
    const generateBtn = document.getElementById('generate-btn');
    
    if (!uploadedFile) {
        alert('请先上传文件');
        return;
    }
    
    // 改变按钮状态：显示"产生文件中"并禁用按钮
    if (generateBtn) {
        generateBtn.textContent = '产生文件中...';
        generateBtn.disabled = true;
        generateBtn.style.opacity = '0.7';
        generateBtn.style.cursor = 'not-allowed';
    }
    
    // 保存图片副本（在清除显示之前）
    const imagesToUpload = [...uploadedImages];
    
    // 清除图片显示
    uploadedImages = [];
    updateImageGallery();
    
    downloadContainer.style.display = 'none'; // 隐藏下载链接
    const downloadTexBtn = document.getElementById('download-tex-btn');
    if (downloadTexBtn) {
        downloadTexBtn.style.display = 'none'; // 隐藏 TeX 下载按钮
    }
    
    try {
        // 创建 FormData 对象
        const formData = new FormData();
        formData.append('file', uploadedFile);
        
        // 添加期刊类型
        const journalType = document.getElementById('journal-dropdown').value;
        formData.append('journal_type', journalType);
        
        // 添加图片（使用保存的副本）
        imagesToUpload.forEach((img, index) => {
            // 如果存在原始文件对象，直接使用；否则从 base64 转换
            if (img.file) {
                // 使用原始文件名
                formData.append('images', img.file, img.file.name);
            } else {
                // 将 base64 数据转换为 Blob
                const byteString = atob(img.data.split(',')[1]);
                const mimeString = img.data.split(',')[0].split(':')[1].split(';')[0];
                const ab = new ArrayBuffer(byteString.length);
                const ia = new Uint8Array(ab);
                for (let i = 0; i < byteString.length; i++) {
                    ia[i] = byteString.charCodeAt(i);
                }
                const blob = new Blob([ab], { type: mimeString });
                // 使用原始文件名，如果没有则使用默认名称
                const filename = img.name || `image_${index + 1}.png`;
                formData.append('images', blob, filename);
            }
        });
        
        // 发送请求到后端（设置很长的超时时间，因为转换过程可能需要很长时间）
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 7200000); // 2小时超时
        
        const response = await fetch('/api/generate-latex', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // 显示下载按钮（如果有 PDF）
            if (result.pdf_url) {
                const pdfUrl = result.pdf_url.startsWith('http') 
                    ? result.pdf_url 
                    : `http://127.0.0.1:8000${result.pdf_url}`;
                const pdfName = result.pdf_filename || '生成结果.pdf';
                
                downloadLink.href = pdfUrl;
                downloadLink.download = pdfName;
                downloadContainer.style.display = 'block';
            }
            
            // 显示下载 TeX 文件按钮（如果有 tex_zip_url）
            const downloadTexBtn = document.getElementById('download-tex-btn');
            const downloadTexLink = document.getElementById('download-tex-link');
            if (result.tex_zip_url && downloadTexBtn && downloadTexLink) {
                const texUrl = result.tex_zip_url.startsWith('http')
                    ? result.tex_zip_url
                    : `http://127.0.0.1:8000${result.tex_zip_url}`;
                
                downloadTexLink.href = texUrl;
                downloadTexLink.download = 'latex_source.zip';
                downloadTexBtn.style.display = 'inline-block';
            }
        } else {
            // 简化错误信息，移除技术细节
            let errorMsg = result.error || '未知错误';
            // 移除 HTTPConnectionPool 等技术错误信息
            if (errorMsg.includes('HTTPConnectionPool') || errorMsg.includes('Read timed out')) {
                errorMsg = '生成失败：处理时间过长，请稍后重试';
            } else if (errorMsg.includes('连接后端API失败')) {
                errorMsg = '生成失败：无法连接到服务器，请检查后端服务是否运行';
            } else if (errorMsg.includes('timeout')) {
                errorMsg = '生成失败：处理超时，请稍后重试';
            }
            alert(`❌ ${errorMsg}`);
            downloadContainer.style.display = 'none';
        }
    } catch (error) {
        // 简化错误信息
        let errorMsg = error.message;
        if (error.name === 'AbortError') {
            errorMsg = '生成失败：处理时间过长（超过2小时），请稍后重试';
        } else if (errorMsg.includes('HTTPConnectionPool') || errorMsg.includes('Read timed out')) {
            errorMsg = '生成失败：处理时间过长，请稍后重试';
        } else if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
            errorMsg = '生成失败：网络连接错误，请检查网络连接';
        }
        alert(`❌ ${errorMsg}`);
        downloadContainer.style.display = 'none';
    } finally {
        // 恢复按钮状态：显示"生成LaTeX 📦"并启用按钮
        if (generateBtn) {
            generateBtn.textContent = '生成LaTeX 📦';
            generateBtn.disabled = false;
            generateBtn.style.opacity = '1';
            generateBtn.style.cursor = 'pointer';
        }
    }
}

