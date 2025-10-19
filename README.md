# Python SaaS 平台

这是一个基于 FastAPI 构建的、可扩展的 SaaS 平台基础架构。

## ✨ 功能特性

- **现代技术栈**: 基于 Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Alembic 和 Pydantic。
- **模块化架构**: 采用“按功能打包”的垂直切片架构，代码高内聚、低耦合，易于维护和扩展。
- **多租户支持**: 基础架构已为多租户系统做好准备。
- **容器化**: 完全使用 Docker 和 Docker Compose 进行环境管理。
- **自动化 CI/CD**: 集成了 GitHub Actions，可自动构建、测试和部署到服务器。

## 🏛️ 项目架构

本项目采用 "src layout" 和“按功能打包”的目录结构，核心业务代码位于 `src` 目录中。

- `src/main.py`: 应用主入口。
- `src/core/`: 存放跨领域共享的核心代码（数据库会话、配置、安全等）。
- `src/auth/`: 负责认证（登录、JWT）的功能模块。
- `src/users/`: 负责用户管理的功能模块。
- `src/tenants/`: 负责租户管理的功能模块。
- `...` (其他业务模块)

这种结构使得每个业务模块都可以独立开发和测试，并且在未来可以轻松地将某个模块拆分为微服务。

## 🚀 本地开发环境

### 1. 先决条件

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 2. 启动步骤

1.  **克隆仓库**
    ```bash
    git clone <your-repository-url>
    cd py_saas_platform
    ```

2.  **配置环境变量**
    从模板文件复制一份新的 `.env` 文件。
    ```bash
    cp .env.example .env
    ```
    > **注意**: `docker-compose.yml` 中已为开发环境配置了默认的数据库连接，通常您无需修改 `.env` 文件即可启动。

3.  **启动服务**
    使用 `docker-compose` 一键启动所有服务（FastAPI 应用, PostgreSQL 数据库, Redis）。
    ```bash
    docker-compose up -d --build
    ```
    服务启动后，您可以通过 `http://localhost:3000` 访问 API 文档。

4.  **查看日志**
    ```bash
    docker-compose logs -f app
    ```

5.  **停止服务**
    ```bash
    docker-compose down
    ```

## 🗄️ 数据库迁移

本项目使用 Alembic 管理数据库结构变更。

1.  **生成迁移脚本**
    当您修改了 `src/*/models.py` 中的数据模型后，运行以下命令自动生成迁移脚本：
    ```bash
    # 首先，进入正在运行的 app 容器
    docker-compose exec app bash

    # 在容器内，运行 alembic
    alembic revision --autogenerate -m "描述你的模型变更"
    ```

2.  **应用迁移**
    将变更应用到数据库：
    ```bash
    # 在容器内运行
    alembic upgrade head
    ```

## 🧪 运行测试

(此处未来可以补充测试运行指令)

## ⚙️ 部署

本项目的部署流程已通过 GitHub Actions 实现自动化。

- **触发条件**: 当代码被推送到 `release/*` 分支或被标记为 `v*.*.*` (如 `v1.0.0`) 时，CI/CD 会自动触发。
- **流程**:
    1.  **构建镜像**: 使用 `Dockerfile` 构建一个生产级别的 Docker 镜像。
    2.  **推送镜像**: 将镜像推送到容器镜像仓库（ACR）。
    3.  **部署更新**: 登录到目标服务器，拉取最新镜像，并以 `docker run` 的方式重启应用容器。

开发者无需手动介入部署过程。

## 🤝 参与贡献

1.  Fork 本仓库
2.  创建 `feat/xxx` 或 `fix/xxx` 分支
3.  提交代码
4.  创建 Pull Request