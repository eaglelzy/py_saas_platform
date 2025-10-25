# 使用官方 Python 3.12-slim 镜像作为基础镜像，便于快速获取运行时环境
FROM python:3.12-slim AS base

# 设置 Python 相关环境变量，提升容器运行效率
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 切换工作目录至应用根路径
WORKDIR /app

# 安装编译依赖，确保 psycopg2 等库可以正确构建
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖定义文件，提前安装依赖以利用 Docker 构建缓存
COPY requirements.txt /app/requirements.txt

# 升级 pip 并安装项目依赖
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# 复制项目源代码到容器中
COPY . /app

# 暴露服务端口，默认供容器编排工具映射
EXPOSE 8000

# 定义容器启动命令，使用 Uvicorn 运行 FastAPI 应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
