"""
Flask application for LaTeX智能排版专家 (LaTeX Intelligent Typesetting Expert)
A simple Flask app that serves the main index page and proxies API requests to backend.
"""

import os
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 从环境变量获取配置，默认值
API_BASE = os.environ.get("AUTOLATEX_API_BASE", "http://127.0.0.1:8000")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))


@app.route('/')
def index():
    """Render the main index page."""
    return render_template('index.html')


@app.route('/api/generate-latex', methods=['POST'])
def generate_latex():
    """
    处理文件上传和 LaTeX 生成
    代理到后端 FastAPI 的 /api/v1/paper/upload 和 /api/v1/paper/convert
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({"error": "缺少文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400
        
        # 获取期刊类型
        journal_type = request.form.get('journal_type', '')
        
        # 1. 上传文件到后端 API
        upload_url = f"{API_BASE}/api/v1/paper/upload"
        
        # 准备文件上传
        files = {'file': (file.filename, file.stream, file.content_type)}
        
        # 添加图片文件（如果有）
        image_index = 0
        for key in request.files:
            if key.startswith('images'):
                image_file = request.files[key]
                if image_file.filename:
                    files[f'image_{image_index}'] = (image_file.filename, image_file.stream, image_file.content_type)
                    image_index += 1
        
        # 发送上传请求
        upload_response = requests.post(upload_url, files=files, timeout=120)
        
        if upload_response.status_code != 200:
            return jsonify({
                "error": f"文件上传失败: {upload_response.text}",
                "status_code": upload_response.status_code
            }), upload_response.status_code
        
        upload_data = upload_response.json()
        
        if not upload_data.get("success"):
            return jsonify({
                "error": f"文件上传失败: {upload_data.get('message', '未知错误')}"
            }), 400
        
        file_path = upload_data.get("file_path")
        uploaded_image_paths = upload_data.get("image_paths", [])
        
        # 2. 调用转换接口
        convert_url = f"{API_BASE}/api/v1/paper/convert"
        
        payload = {
            "file_path": file_path,
            "journal_name": journal_type or "",
            "topic": "自动将word、txt、markdown格式论文转化为Latex格式论文",
        }
        
        # 如果有图片，添加到 payload
        if uploaded_image_paths:
            payload["image_paths"] = uploaded_image_paths
        
        # 发送转换请求（设置更长的超时时间，因为转换过程可能需要很长时间）
        convert_response = requests.post(convert_url, json=payload, timeout=3600)  # 1小时超时
        
        if convert_response.status_code != 200:
            return jsonify({
                "error": f"转换失败: {convert_response.text}",
                "status_code": convert_response.status_code,
                "file_path": file_path
            }), convert_response.status_code
        
        convert_data = convert_response.json()
        
        if not convert_data.get("success"):
            return jsonify({
                "error": convert_data.get("message", "转换失败"),
                "file_path": file_path
            }), 400
        
        # 构建成功响应
        result = {
            "success": True,
            "message": convert_data.get("message", "生成成功"),
            "file_path": file_path,
            "output_path": convert_data.get("output_path"),
            "pdf_url": convert_data.get("pdf_url"),
            "pdf_filename": convert_data.get("pdf_filename"),
            "tex_zip_url": convert_data.get("tex_zip_url"),
            "image_count": len(uploaded_image_paths)
        }
        
        return jsonify(result)
        
    except requests.exceptions.Timeout as e:
        return jsonify({"error": "处理时间过长，请稍后重试"}), 500
    except requests.exceptions.ConnectionError as e:
        return jsonify({"error": "无法连接到服务器，请检查后端服务是否运行"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "服务器连接错误，请稍后重试"}), 500
    except Exception as e:
        return jsonify({"error": f"处理请求时发生错误: {str(e)}"}), 500


@app.route('/api/get-journals', methods=['GET'])
def get_journals():
    """
    获取所有可用的期刊列表
    代理到后端 FastAPI 的 /api/v1/knowledge/journals 接口
    """
    try:
        journals_url = f"{API_BASE}/api/v1/knowledge/journals"
        response = requests.get(journals_url, timeout=30)
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "journals": [],
                "error": f"获取期刊列表失败: {response.text}"
            }), response.status_code
        
        data = response.json()
        
        if data.get("success"):
            # 添加"自定义模板"选项
            journals = data.get("journals", [])
            journals.append("自定义模板")
            return jsonify({
                "success": True,
                "journals": journals,
                "count": len(journals)
            })
        else:
            return jsonify({
                "success": False,
                "journals": ["自定义模板"],
                "error": data.get("message", "获取失败")
            })
            
    except requests.exceptions.RequestException as e:
        # 如果连接失败，只返回"自定义模板"
        return jsonify({
            "success": False,
            "journals": ["自定义模板"],
            "error": f"连接后端API失败: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "journals": ["自定义模板"],
            "error": f"获取期刊列表时发生错误: {str(e)}"
        })


@app.route('/api/preview-template', methods=['POST'])
def preview_template():
    """
    预览模板
    代理到后端 FastAPI 的知识库搜索接口
    """
    try:
        data = request.get_json()
        template_name = data.get('template_name', '')
        
        if not template_name or template_name == "自定义模板":
            return jsonify({
                "success": False,
                "content": "请选择一个模板名称进行预览"
            })
        
        # 调用后端知识库搜索接口
        search_url = f"{API_BASE}/api/v1/knowledge/search"
        payload = {"journal_name": template_name}
        
        response = requests.post(search_url, json=payload, timeout=30)
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "content": f"预览模板失败: {response.text}"
            })
        
        search_data = response.json()
        
        if search_data.get("success") and search_data.get("template_content"):
            template_content = search_data.get("template_content", "")
            # 如果内容太长，只显示前5000个字符
            if len(template_content) > 5000:
                template_content = f"{template_content[:5000]}\n\n... (内容已截断，共 {len(template_content)} 个字符)"
            
            return jsonify({
                "success": True,
                "content": template_content
            })
        else:
            return jsonify({
                "success": False,
                "content": f"预览模板失败: {search_data.get('message', '未知错误')}"
            })
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "content": f"连接后端API失败: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "content": f"预览模板时发生错误: {str(e)}"
        })


if __name__ == '__main__':
    print(f"Flask 应用启动在端口 {FLASK_PORT}")
    print(f"后端 API 地址: {API_BASE}")
    app.run(debug=True, host='0.0.0.0', port=FLASK_PORT)

