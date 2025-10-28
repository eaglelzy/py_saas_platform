# 项目常用脚本入口，使用 `make <target>` 调用

ENV_FILE ?= env/.env.development
PYTHON ?= python

.PHONY: help install format lint test superuser build-app build-up-app up-app up-all docker-down migrate

help:
	@echo "可用命令:"
	@echo "  make install       安装依赖 (pip install -r requirements.txt)"
	@echo "  make format        运行 code formatter (占位)"
	@echo "  make lint          运行静态检查 (占位)"
	@echo "  make test          运行单元测试"
	@echo "  make superuser     在容器内执行超级管理员脚本"
	@echo "  make build-app     构建 app 镜像"
	@echo "  make build-up-app  构建并启动 app 服务"
	@echo "  make up-app        启动 app 服务"
	@echo "  make up-all        启动全部服务"
	@echo "  make docker-down   停止所有 docker 服务"
	@echo "  make logs-app      查看 app 服务日志"
	@echo "  make migrate       容器内执行 alembic upgrade head"

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

logs-app:
	docker compose logs -f app

docker-down:
	docker compose down

migrate:
	docker compose run --rm -e ENV_FILE=$(ENV_FILE) app alembic upgrade head
