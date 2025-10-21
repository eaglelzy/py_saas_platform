# 测试数据库管理变更日志

## 2024-10-21

### 新增功能
- ✅ 创建了专门的测试数据库目录 `tests/test_databases/`
- ✅ 实现了测试数据库管理器 `db_manager.py`
- ✅ 添加了自动清理脚本 `cleanup.py`
- ✅ 创建了Pytest插件 `pytest_plugin.py`
- ✅ 更新了 `.gitignore` 配置

### 解决的问题
- ✅ 测试数据库文件不再在项目根目录生成
- ✅ 所有测试数据库文件统一管理在 `tests/test_databases/` 目录
- ✅ 自动清理测试数据库文件，避免磁盘空间浪费
- ✅ 支持并发测试，每个测试使用独立的数据库文件

### 配置变更
- 更新了 `tests/conftest.py` 中的数据库路径配置
- 添加了 `.gitignore` 规则忽略测试数据库文件
- 创建了完整的测试数据库管理工具链

### 使用说明
1. **自动管理**: 测试运行时自动创建和清理数据库文件
2. **手动清理**: 使用 `python tests/test_databases/cleanup.py` 手动清理
3. **调试支持**: 测试失败时数据库文件会保留，便于调试
4. **并发安全**: 每个测试使用独立的数据库文件

### 文件结构
```
tests/test_databases/
├── __init__.py          # 包初始化
├── db_manager.py        # 数据库管理器
├── cleanup.py          # 清理脚本
├── pytest_plugin.py    # Pytest插件
├── README.md           # 使用说明
├── CHANGELOG.md        # 变更日志
└── *.db               # 测试数据库文件（自动生成）
```

### 向后兼容性
- ✅ 现有测试代码无需修改
- ✅ 测试配置自动适配新的数据库路径
- ✅ 保持原有的测试功能不变
