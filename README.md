# 目前更新
整理了一下项目结构

# 项目使用指南
## 1. 项目结构
整体结构
```cmd
autolatex/
├── .gitignore
├── knowledge/
├── pyproject.toml
├── README.md
├── .env -- 到这里之前都是一些Crewai的文件
├── data/ -- 这是白同学以前存放论文模版的文件夹（似乎要改）
├── docs/ -- markdown格式的说明（包括帮助我配置的guideline和已完成的任务报告）
├── knowledge/ -- crewai自己建的关于用户的一些信息
├── Agent输出/ -- 我们的Agent的输出
├── 模板/ -- 目前存放的是一些BIT毕业论文模版
├── test_data/ -- hbk同学创建的用来测试的word、txt、markdown文件
├── vendor/ --有个deepseek-OCR的文件
└── src/
    └── autolatex/
        ├── __init__.py
        ├── main.py
        ├── crew.py
        ├── tools/
        │   ├── custom_tool.py
        │   └── __init__.py
        └── config/
            ├── agents.yaml
            └── tasks.yaml
```

.env 需要放入你的api和key
我用的deepseek
```cmd
MODEL=openai/deepseek-chat
OPENAI_API_KEY = <填入你的key>
OPENAI_API_BASE=https://api.deepseek.com
```
## 2. 关于与B、D同学的接口函数部分
在src\autolatex\tools\document_tools.py和tools\knowledge_tools.py中
