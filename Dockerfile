# --- 第一阶段：构建器 (Builder) ---
# 使用一个完整的 Python 镜像作为“构建器”
FROM python:3.12-slim as builder

WORKDIR /app

# 先只复制依赖文件
COPY requirements.txt .

# 在这个阶段安装所有依赖到一个临时的虚拟环境中
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# --- 第二阶段：最终镜像 (Final Image) ---
# 使用AlmaLinux 8 (CentOS 8的另一个替代品，完全兼容)
FROM almalinux:8

# 安装Python和必要的系统工具
RUN dnf update -y && dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    gcc \
    git \
    curl \
    wget \
    && dnf clean all

# 设置Python3为默认python
RUN ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# 只从“构建器”阶段复制已安装好的依赖库
COPY --from=builder /opt/venv /opt/venv

# 只复制我们需要的源代码目录
COPY ./src ./src

# 设置环境变量，让应用使用我们复制过来的虚拟环境
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

# CMD 保持不变
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]