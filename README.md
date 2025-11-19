# 项目使用指南
## 1. CrewAI使用方法（官方提供）

Welcome to the Autolatex Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

### Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
#### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/autolatex/config/agents.yaml` to define your agents
- Modify `src/autolatex/config/tasks.yaml` to define your tasks
- Modify `src/autolatex/crew.py` to add your own logic, tools and specific args
- Modify `src/autolatex/main.py` to add custom inputs for your agents and tasks

### Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the autolatex Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The autolatex Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

### Support

For support, questions, or feedback regarding the Autolatex Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.

## 2. 项目结构
```cmd
autolatex/
├── .gitignore
├── knowledge/
├── pyproject.toml
├── README.md
├── .env
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
## 3. 关于与B、D同学的接口函数部分
在src\autolatex\tools\document_tools.py和tools\knowledge_tools.py中
