# 日志配置说明

本项目的日志系统支持通过环境变量进行灵活配置，可以根据不同的环境自动调整日志行为。

## 环境变量配置

### 主要环境变量

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DEBUG` | `false` | 是否启用调试模式。设置为 `true`、`1`、`yes` 或 `on` 时启用 |
| `LOG_LEVEL` | `INFO` | 日志级别：`DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL` |
| `ENV` | `development` | 环境类型：`development`、`test`、`production` |

### 环境变量行为

#### DEBUG 环境变量
- `DEBUG=true` 时：
  - 自动设置日志级别为 `DEBUG`
  - 启用彩色输出
  - 在开发环境启用文件日志
- `DEBUG=false` 时：
  - 使用 `LOG_LEVEL` 环境变量设置的日志级别
  - 根据环境类型决定是否使用彩色输出

#### LOG_LEVEL 环境变量
- 当 `DEBUG=false` 时生效
- 支持的值：`DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`
- 不区分大小写

#### ENV 环境变量
- `development`：启用彩色输出，根据DEBUG设置文件日志
- `test`：启用文件日志，根据DEBUG设置彩色输出
- `production`：禁用彩色输出，启用文件日志

## 使用方法

### 方法1: 环境变量自动配置（推荐）

```python
from src.core.logging import init_logging_from_env, get_logger

# 在应用程序启动时调用
init_logging_from_env()

# 获取日志器
logger = get_logger(__name__)
logger.info("应用程序启动")
```

### 方法2: 手动配置

```python
from src.core.logging import setup_logging, get_logger

# 手动设置日志配置
setup_logging(
    log_level="DEBUG",
    use_colors=True,
    log_to_file=True,
    environment="development"
)

logger = get_logger(__name__)
logger.debug("调试信息")
```

### 方法3: 使用默认配置

```python
from src.core.logging import LOGGING_CONFIG
import logging.config

# 使用基于环境变量的默认配置
logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)
logger.info("使用默认配置")
```

## 配置文件示例

### .env.test (测试环境)
```bash
DEBUG=true
LOG_LEVEL=DEBUG
ENV=test
```

### .env.prod (生产环境)
```bash
DEBUG=false
LOG_LEVEL=INFO
ENV=production
```

## 日志输出特性

### 开发环境 (ENV=development)
- 彩色控制台输出
- 根据DEBUG设置日志级别
- 可选的文件日志

### 测试环境 (ENV=test)
- 彩色控制台输出（如果DEBUG=true）
- 文件日志记录
- 通常使用DEBUG级别

### 生产环境 (ENV=production)
- 无彩色控制台输出
- JSON格式的文件日志
- 错误日志单独记录
- 通常使用INFO或WARNING级别

## 日志文件

当启用文件日志时，会在 `logs/` 目录下创建以下文件：
- `app.log`: 所有日志记录
- `error.log`: 错误级别以上的日志

## 高级功能

### 上下文日志
```python
from src.core.logging import get_logger

# 带额外信息的日志器
logger = get_logger(__name__, {"user_id": 123, "tenant_id": 456})
logger.info("用户操作", extra={"action": "login"})
```

### 用户操作日志
```python
from src.core.logging import log_user_action

log_user_action(logger, user_id=123, action="login", tenant_id=456)
```

### API请求日志
```python
from src.core.logging import log_api_request

log_api_request(logger, method="GET", path="/api/users", status_code=200, user_id=123)
```

## 注意事项

1. 不要在模块导入时自动调用 `setup_logging()`，这会导致重复初始化
2. 在应用程序启动时调用一次 `init_logging_from_env()` 即可
3. 生产环境建议使用 `DEBUG=false` 和 `LOG_LEVEL=INFO` 或 `WARNING`
4. 测试环境可以使用 `DEBUG=true` 来获取详细的调试信息
