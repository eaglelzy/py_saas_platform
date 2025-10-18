# 方案：按功能/领域划分 (Package by Feature)

本方案采纳了“按功能/领域划分”（也称为“垂直切片”）的目录结构。这是更现代且更适应微服务演进的架构。

其核心思想是：**将与单一业务领域（如“用户管理”）相关的所有代码（API、CRUD、模型、数据结构）都放在同一个包（目录）中**。这创建了高内聚、低耦合的独立功能模块。

---

### 推荐的目录结构

```
/py_saas_platform/
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── alembic/
│   ├── versions/
│   └── ...
│
├── src/
│   ├── __init__.py
│   ├── main.py             # FastAPI 应用入口, 聚合所有功能模块的路由
│   │
│   ├── core/               # 存放所有跨领域共享的代码
│   │   ├── __init__.py
│   │   ├── config.py       # 应用配置加载
│   │   ├── db.py           # 数据库会话、引擎、基类
│   │   └── security.py     # 密码哈希, JWT 核心逻辑
│   │
│   ├── auth/               # 认证功能模块
│   │   ├── __init__.py
│   │   ├── api.py          # 登录、刷新Token的API端点
│   │   ├── schemas.py      # Token相关的数据结构
│   │   └── service.py      # 认证业务逻辑
│   │
│   ├── users/              # “用户”领域模块 (限界上下文)
│   │   ├── __init__.py
│   │   ├── api.py          # 用户的API路由
│   │   ├── crud.py         # 用户的CRUD数据库操作
│   │   ├── models.py       # 用户的SQLAlchemy模型
│   │   └── schemas.py      # 用户的Pydantic数据结构
│   │
│   ├── tenants/            # “租户”领域模块 (限界上下文)
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── crud.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   └── subscriptions/      # “订阅”领域模块 (限界上下文)
│       ├── __init__.py
│       ├── api.py
│       ├── crud.py
│       ├── models.py
│       ├── schemas.py
│       └── service.py      # 对接支付网关的业务逻辑
│
└── tests/                  # 测试目录, 结构与src镜像
    ├── __init__.py
    ├── conftest.py         # 全局测试配置和Fixtures
    │
    ├── users/              # 针对用户模块的测试
    │   ├── test_api.py
    │   └── test_crud.py
    │
    └── tenants/            # 针对租户模块的测试
        ├── test_api.py
        └── test_crud.py
```

---

### 方案说明

*   **高内聚性**: 这是此结构最大的优点。所有与“用户”功能相关的代码都封装在 `src/users/` 目录中，形成一个独立的模块。这使得代码更容易理解、维护和测试。

*   **为微服务而生**: 这种结构完美地映射了领域驱动设计（DDD）中的“限界上下文”（Bounded Context）概念。当您决定将“用户管理”拆分为一个独立的微服务时，您几乎可以直接将 `src/users/` 目录复制到一个新项目中，稍作配置即可，迁移成本极低。

*   **`src/core/` - 共享核心**: 此目录至关重要，它用于存放所有跨功能模块的共享代码。例如，数据库连接 (`db.py`)、应用配置 (`config.py`)、通用的安全功能 (`security.py`) 都放在这里，避免在各个功能模块中重复造轮子。

*   **`src/main.py` - 应用组装器**: 主入口文件变得非常简洁。它的主要职责是创建 FastAPI 应用实例，并从各个功能模块（`users.api`, `tenants.api` 等）导入并包含它们的路由（Router）。

*   **清晰的职责**:
    *   **功能模块 (e.g., `src/users/`)**: 负责实现一个完整的垂直业务功能。
    *   **核心模块 (`src/core/`)**: 提供横向的基础设施和共享能力。

*   **独立的测试**: `tests/` 目录的结构镜像了 `src/` 目录，使得对每个功能模块的测试都可以独立编写和运行，非常清晰。

对于一个目标是随时可能演进为微服务架构的复杂SaaS平台，这个方案是当前业界公认的最佳实践。

---

### SQLAlchemy 集成最佳实践方案

这个方案的核心思想是：**集中管理数据库连接，分散定义领域模型**。

---

#### 1. 核心连接与会话管理 (`src/core/db.py`)

这个文件是数据库设置的心脏。它的职责是：

*   **创建数据库引擎 (`engine`)**: 从配置文件 (`core/config.py`) 中读取数据库连接字符串 (如 `postgresql://user:password@host/db`)，并创建全局唯一的 SQLAlchemy `engine`。
*   **创建会话工厂 (`SessionLocal`)**: 使用 `sessionmaker` 创建一个 `SessionLocal` 类。这个类的实例就是一个独立的数据库会v话。我们应该为每个请求创建一个新的会话，并在请求结束后关闭它。
*   **声明基类 (`Base`)**: 创建一个声明性的模型基类 `Base = declarative_base()`。未来所有的数据模型（ORM classes）都将继承自这个 `Base`。这使得 Alembic 等迁移工具能够发现我们的模型。
*   **提供会话依赖 (`get_db`)**: 编写一个 FastAPI 依赖项函数（Dependency），例如 `def get_db():`。这个函数负责：
    1.  从 `SessionLocal` 创建一个数据库会话 (`db`)。
    2.  使用 `yield db` 将会话提供给 API 路径操作函数。
    3.  在请求处理完毕后（无论成功或失败），通过 `finally` 块确保 `db.close()` 被调用，从而释放连接。

#### 2. 配置管理 (`src/core/config.py`)

此文件负责安全地加载配置，特别是数据库凭据：

*   **使用 Pydantic 的 `BaseSettings`**: 创建一个设置类，例如 `class Settings(BaseSettings):`。
*   **从环境变量加载**: `Settings` 类会自动从环境变量或 `.env` 文件中读取配置项（如数据库 URL、用户名、密码）。这避免了将敏感信息硬编码在代码中。
*   `db.py` 将会导入这个 `Settings` 对象来获取数据库连接信息。

#### 3. 数据模型定义 (例如 `src/users/models.py`)

每个功能模块都应该有自己的 `models.py` 文件，用来定义与该功能相关的数据库表。

*   **继承 `Base`**: `users/models.py` 中的 `User` 模型、`tenants/models.py` 中的 `Tenant` 模型等，都必须继承自 `src.core.db.Base`。
*   **定义表结构**: 在模型类中，使用 SQLAlchemy 的 `Column`, `String`, `Integer`, `ForeignKey` 等来定义表的字段、类型和关系。

#### 4. 数据操作层 (例如 `src/users/crud.py`)

为了实现职责分离，所有直接与数据库交互的逻辑（增删改查）都应封装在 `crud.py` 文件中。

*   **函数签名**: CRUD 函数都应该接受一个 `db: Session` 对象作为参数，例如 `def create_user(db: Session, user: UserCreateSchema):`。
*   **执行数据库操作**: 函数内部使用传入的 `db` 会话对象来执行查询、添加、更新和删除操作（例如 `db.query(User).filter(...).first()` 或 `db.add(db_user)`)。
*   **返回数据**: 函数将 SQLAlchemy 模型对象返回给调用它的 API 层。

#### 5. API 接口层 (例如 `src/users/api.py`)

API 层（路由）负责处理 HTTP 请求，但不直接操作数据库。

*   **注入 `db` 会话**: 在路径操作函数中，使用 `db: Session = Depends(get_db)` 来获取数据库会话。FastAPI 会自动调用我们之前在 `core/db.py` 中定义的 `get_db` 函数。
*   **调用 CRUD**: API 函数会调用 `crud.py` 中相应的函数来完成业务逻辑，并把 `db` 会话传递过去。例如：`return crud.create_user(db=db, user=user)`。

#### 6. 数据库迁移 (`alembic/` 和 `alembic.ini`)

这是管理数据库结构变更的关键。

*   **Alembic**: 是 SQLAlchemy 的官方迁移工具。当您修改了 `models.py` 中的表结构（例如，给 `User` 表增加一个字段）后，您不需要手动去数据库里改。
*   **工作流程**:
    1.  运行 `alembic revision --autogenerate -m "Add new column to User"`，Alembic 会自动检测模型变化并生成一个迁移脚本。
    2.  运行 `alembic upgrade head`，Alembic 会执行该脚本，将变更应用到数据库。
*   `alembic.ini` 文件用于配置 Alembic，告诉它数据库在哪里以及如何找到我们的模型。

---

### 总结：数据流转路径

1.  **启动**: 应用启动时，`core/db.py` 创建全局 `engine`。
2.  **请求进入**: 一个 `/users/` 的 API 请求进来。
3.  **获取会话**: FastAPI 调用 `get_db` 依赖，创建一个新的 `db` 会话。
4.  **处理逻辑**: `users/api.py` 中的路径函数接收到 `db` 会话，然后带着这个会话调用 `users/crud.py` 中的函数。
5.  **数据库交互**: `crud.py` 中的函数使用 `db` 会话执行 SQL 操作。
6.  **返回响应**: API 函数返回结果。
7.  **关闭会话**: `get_db` 中的 `finally` 块确保 `db` 会话被关闭，连接被归还到连接池。

这个方案实现了高度的模块化和关注点分离，使得代码清晰、可维护、易于测试，并且完美契合您现有的项目结构。