# 日志系统说明

## 目标
- 统一输出格式，包含 `tenant_id`、`user_id`、`request_id` 等关键上下文，便于多租户排障。
- 提供请求级别日志，记录请求耗时、状态码、异常信息。
- 支持在业务逻辑中手动绑定租户/用户上下文，确保审计链路完整。

## 组件
- `app/core/logging/logger.py`：封装 Loguru 配置，注入上下文补丁，标准化输出格式。
- `app/core/logging/context.py`：基于 `ContextVar` 保存请求范围的租户、用户、请求 ID。
- `app/core/logging/middleware.py`：HTTP 中间件自动生成 Request ID，输出请求开始/结束日志。
- `app/core/logging/__init__.py`：导出常用函数与中间件，供业务模块调用。

## 使用方式
1. 在应用启动时调用 `configure_logging()`（已在 `app/main.py` 中处理）。
2. FastAPI 应用会自动挂载 `RequestLoggingMiddleware`，无需额外配置。
3. 在需要补全上下文的地方调用：
   ```python
   from app.saas.core.logging import set_log_context

   # 示例：认证后绑定租户与用户信息
   set_log_context(tenant_id="tenant_123", user_id="user_456")
   ```
4. 若在任务或后台线程中需要重置上下文，可调用 `reset_log_context()`。

## 日志示例
```
2025-10-24 16:08:21.123 | INFO     | tenant=tenant_123 user=user_456 req=bd11e9b7 | app.core.api:handler:42 - 请求处理完成
```

## 后续建议
- 按需将日志重定向到文件或集中式日志系统（如 ELK、Loki）。
- 在认证、租户加载逻辑中调用 `set_log_context`，确保全链路上下文正确。
- 为关键审计事件设计专用日志函数或事件上报机制。
