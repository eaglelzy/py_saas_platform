# 日志模块使用指南

## 📖 概述

`src/core/logging.py` 提供了 SaaS 平台的统一日志配置，支持结构化日志记录、JSON 格式输出和中文显示。

## 🚀 快速开始

### 1. 基本使用

```python
from src.core.logging import get_logger

# 获取日志器
logger = get_logger(__name__)

# 记录日志
logger.info("用户登录成功")
logger.error("登录失败")
```

### 2. 配置日志系统

```python
from src.core.logging import setup_logging

# 开发环境：带颜色的控制台输出
setup_logging(log_level="DEBUG", use_colors=True)

# 生产环境：JSON 格式文件输出
setup_logging(log_level="INFO", use_colors=False)
```

## 📋 主要功能

### 1. JsonFormatter - JSON 格式日志

自动生成结构化的 JSON 日志，便于日志聚合系统处理：

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "message": "用户登录成功",
  "name": "src.auth.login",
  "module": "login",
  "function": "authenticate_user",
  "line": 45,
  "process_id": 1234,
  "thread_id": 140234567890,
  "extra_info": {
    "user_id": 123,
    "tenant_id": 1
  }
}
```

### 2. 便捷日志函数

#### 用户操作日志

```python
from src.core.logging import log_user_action

log_user_action(
    logger=logger,
    user_id=123,
    action="登录",
    tenant_id=1,
    ip_address="192.168.1.100"
)
```

#### API 请求日志

```python
from src.core.logging import log_api_request

log_api_request(
    logger=logger,
    method="POST",
    path="/api/v1/auth/login",
    status_code=200,
    user_id=123,
    tenant_id=1
)
```

### 3. 异常日志记录

```python
try:
    risky_operation()
except Exception as e:
    # 包含完整堆栈跟踪
    logger.error("操作失败", exc_info=True)
    
    # 或者只记录异常信息
    logger.error(f"操作失败: {str(e)}")
```

### 4. 上下文日志

```python
# 创建带上下文信息的日志器
logger = get_logger(__name__, {
    'tenant_id': 1,
    'service': 'user-management'
})

# 所有日志都会自动包含上下文信息
logger.info("服务启动")
```

## 🎯 使用场景

### 1. 用户认证

```python
def authenticate_user(email: str, password: str):
    logger = get_logger(__name__)
    
    logger.info(f"用户尝试登录: {email}")
    
    try:
        user = verify_credentials(email, password)
        logger.info(
            "用户登录成功",
            extra={
                'extra_info': {
                    'user_id': user.id,
                    'tenant_id': user.tenant_id,
                    'email': email
                }
            }
        )
        return user
    except AuthenticationError as e:
        logger.warning(
            f"登录失败: {str(e)}",
            extra={'extra_info': {'email': email, 'error': str(e)}}
        )
        raise
```

### 2. 数据库操作

```python
def create_student(student_data: dict):
    logger = get_logger(__name__)
    
    logger.info(
        "开始创建学生",
        extra={
            'extra_info': {
                'operation': 'create_student',
                'student_name': student_data.get('name')
            }
        }
    )
    
    try:
        student = Student(**student_data)
        db.add(student)
        db.commit()
        
        logger.info(
            "学生创建成功",
            extra={
                'extra_info': {
                    'operation': 'create_student',
                    'student_id': student.id,
                    'success': True
                }
            }
        )
        return student
    except Exception as e:
        logger.error(
            "学生创建失败",
            extra={
                'extra_info': {
                    'operation': 'create_student',
                    'error': str(e),
                    'success': False
                }
            },
            exc_info=True
        )
        raise
```

### 3. API 中间件

```python
from fastapi import Request
import time

async def log_requests(request: Request, call_next):
    logger = get_logger(__name__)
    
    start_time = time.time()
    
    # 记录请求开始
    logger.info(
        f"API 请求开始: {request.method} {request.url.path}",
        extra={
            'extra_info': {
                'method': request.method,
                'path': request.url.path,
                'client_ip': request.client.host
            }
        }
    )
    
    try:
        response = await call_next(request)
        
        # 计算处理时间
        process_time = (time.time() - start_time) * 1000
        
        # 记录请求完成
        log_api_request(
            logger=logger,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time=process_time,
            client_ip=request.client.host
        )
        
        return response
    except Exception as e:
        logger.error(
            f"API 请求异常: {request.method} {request.url.path}",
            extra={
                'extra_info': {
                    'method': request.method,
                    'path': request.url.path,
                    'error': str(e)
                }
            },
            exc_info=True
        )
        raise
```

## ⚙️ 配置选项

### 1. 日志级别

```python
# 支持的日志级别（从低到高）
setup_logging(log_level="DEBUG")    # 调试信息
setup_logging(log_level="INFO")     # 一般信息（默认）
setup_logging(log_level="WARNING")  # 警告信息
setup_logging(log_level="ERROR")    # 错误信息
setup_logging(log_level="CRITICAL") # 严重错误
```

### 2. 输出格式

```python
# JSON 格式（生产环境推荐）
setup_logging(use_colors=False)

# 彩色格式（开发环境推荐）
setup_logging(use_colors=True)
```

### 3. 文件输出

日志文件会自动创建在 `logs/` 目录下：
- `logs/app.log` - 应用日志
- `logs/error.log` - 错误日志

## 🔧 最佳实践

### 1. 日志级别使用

- **DEBUG**: 详细的调试信息，只在开发时使用
- **INFO**: 记录重要的业务事件和状态变化
- **WARNING**: 需要注意但不影响程序运行的情况
- **ERROR**: 错误情况，但程序可以继续运行
- **CRITICAL**: 严重错误，程序可能无法继续

### 2. 结构化日志

```python
# ✅ 好的做法：结构化信息
logger.info(
    "用户操作完成",
    extra={
        'extra_info': {
            'user_id': 123,
            'action': 'create_student',
            'student_id': 456,
            'tenant_id': 1
        }
    }
)

# ❌ 不好的做法：非结构化信息
logger.info(f"用户 123 在租户 1 中创建了学生 456")
```

### 3. 敏感信息处理

```python
# ✅ 好的做法：不记录敏感信息
logger.info(
    "用户登录成功",
    extra={
        'extra_info': {
            'user_id': user.id,
            'email_domain': user.email.split('@')[1]  # 只记录域名
        }
    }
)

# ❌ 不好的做法：记录敏感信息
logger.info(f"用户 {user.email} 使用密码 {password} 登录成功")
```

## 📁 运行示例

```bash
# 运行完整示例
python examples/logging_usage.py

# 查看日志文件
tail -f logs/app.log
tail -f logs/error.log
```

## 🎨 输出示例

### 控制台输出（彩色模式）

```
2024-01-15 10:30:45 - src.auth.login - INFO - 用户登录成功
2024-01-15 10:30:46 - src.students.create - INFO - 学生创建成功
2024-01-15 10:30:47 - src.api.middleware - WARNING - API 请求异常
```

### 文件输出（JSON 模式）

```json
{"timestamp": "2024-01-15T10:30:45.123456", "level": "INFO", "message": "用户登录成功", "name": "src.auth.login", "module": "login", "function": "authenticate_user", "line": 45, "process_id": 1234, "thread_id": 140234567890, "extra_info": {"user_id": 123, "tenant_id": 1}}
```

这个日志系统为您的 SaaS 平台提供了企业级的日志记录能力，支持结构化输出、中文显示、异常跟踪和便捷的使用接口！
