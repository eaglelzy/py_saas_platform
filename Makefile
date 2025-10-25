# 项目常用脚本入口，使用 `make <target>` 调用

PYTHON ?= python
UVICORN ?= uvicorn
ENV_FILE ?= env/.env.development

.PHONY: help install format lint test superuser run docker-up docker-down

help:
	@echo "可用命令:"
	@echo "  make install       安装依赖 (pip install -r requirements.txt)"
	@echo "  make format        运行 code formatter (目前预留)"
	@echo "  make lint          运行静态检查 (预留)"
	@echo "  make test          运行单元测试"
	@echo "  make superuser     读取 ENV_FILE 创建超级管理员"
	@echo "  make build-app     构建 app 服务"
	@echo "  make build-up-app  构建并启动 app 服务"
	@echo "  make up-app     	启动 app 服务"
	@echo "  make up-all      	启动所有服务"

install:
	pip install -r requirements.txt

format:
	@echo "暂未配置具体格式化工具"

lint:
	@echo "暂未配置具体静态检查"

test:
	$(PYTHON) -m pytest tests/unit

superuser:
	docker compose run --rm -e ENV_FILE=$(ENV_FILE) app python scripts/create_superuser.py

build-app:
	docker compose build app

build-up-app:
	docker compose up -d --build app

up-app:
	docker compose up -d app

up-all:
	docker compose up -d