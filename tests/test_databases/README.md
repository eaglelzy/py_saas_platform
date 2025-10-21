# 测试数据库管理

这个目录用于存储测试过程中生成的SQLite数据库文件。

## 目录结构

```
tests/test_databases/
├── __init__.py          # 包初始化文件
├── db_manager.py        # 数据库管理器
├── cleanup.py          # 清理脚本
├── README.md           # 说明文档
└── *.db               # 测试数据库文件（自动生成）
```

## 功能说明

### 1. 自动数据库管理
- 测试运行时自动在此目录创建数据库文件
- 每个测试使用独立的数据库文件，避免数据冲突
- 测试完成后自动清理数据库文件

### 2. 数据库管理器 (`db_manager.py`)
提供以下功能：
- `create_test_database(test_name)`: 为特定测试创建数据库
- `create_temp_database()`: 创建临时数据库
- `cleanup_database(db_path)`: 清理指定数据库
- `cleanup_all_databases()`: 清理所有数据库
- `get_database_list()`: 获取数据库文件列表

### 3. 清理脚本 (`cleanup.py`)
用于手动清理测试数据库文件：

```bash
# 查看将要删除的文件
python tests/test_databases/cleanup.py --dry-run

# 清理所有数据库文件
python tests/test_databases/cleanup.py

# 显示详细信息
python tests/test_databases/cleanup.py -v
```

## 配置说明

### 环境变量
测试配置通过以下环境变量控制：
- `DATABASE_URL`: 数据库连接URL，默认为 `sqlite:///tests/test_databases/test.db`
- `ENV`: 环境标识，测试时设置为 `unit-test`

### Git忽略
所有 `.db` 文件都被 `.gitignore` 忽略，不会提交到版本控制。

## 使用示例

### 在测试中使用
```python
from tests.test_databases.db_manager import test_db_manager

def test_something():
    # 创建测试数据库
    engine, session_factory = test_db_manager.create_test_database("my_test")
    
    # 使用数据库进行测试
    # ...
    
    # 测试完成后自动清理
```

### 手动清理
```bash
# 进入项目根目录
cd /path/to/project

# 清理测试数据库
python tests/test_databases/cleanup.py -v
```

## 注意事项

1. **自动清理**: 测试框架会自动清理数据库文件，通常不需要手动清理
2. **并发安全**: 每个测试使用独立的数据库文件，支持并发测试
3. **性能考虑**: SQLite数据库文件较小，不会影响测试性能
4. **调试支持**: 测试失败时数据库文件会保留，便于调试

## 故障排除

### 数据库文件未清理
如果发现数据库文件未被清理，可以手动运行清理脚本：
```bash
python tests/test_databases/cleanup.py -v
```

### 权限问题
如果遇到权限问题，确保对 `tests/test_databases/` 目录有写权限：
```bash
chmod 755 tests/test_databases/
```

### 磁盘空间
如果磁盘空间不足，可以定期清理测试数据库：
```bash
# 查看数据库文件大小
du -sh tests/test_databases/*.db

# 清理所有数据库文件
python tests/test_databases/cleanup.py
```
