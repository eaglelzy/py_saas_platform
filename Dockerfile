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
FROM python:3.12-slim

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