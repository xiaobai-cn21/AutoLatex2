# Dockerfile for LaTeX Compilation Sandbox
FROM ubuntu:latest

# 安装满足项目需求的核心 TeX Live 组件及工具
# 使用国内镜像以提升稳定性/速度
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/* && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ noble main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ noble-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ noble-backports main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ noble-security main restricted universe multiverse" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-bibtex-extra \
    biber \
    latexmk \
    make \
    wget \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 创建低权限用户
RUN useradd -ms /bin/bash latexuser

USER latexuser
WORKDIR /home/latexuser/compile_env

# 默认命令（编译时会通过 docker run 指定）

