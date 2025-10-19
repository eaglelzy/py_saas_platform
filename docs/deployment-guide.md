# 阿里云部署指南

## 📋 概述

本指南说明如何使用 GitHub Actions 自动部署留学助手平台到阿里云，支持测试环境和生产环境的自动部署。

## 🔧 环境配置

### GitHub Secrets 配置

在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加以下 Secrets：

#### 通用配置
```
ACR_USERNAME=your_acr_username
ACR_PASSWORD=your_acr_password
ACR_REGISTRY=registry.cn-hangzhou.aliyuncs.com
```

#### 测试环境配置
```
TEST_ECS_HOST=test-server-ip
TEST_ECS_USERNAME=root
TEST_ECS_SSH_KEY=your_ssh_private_key
TEST_ECS_PORT=22
TEST_PROJECT_PATH=/opt/saas_platform_test
TEST_APP_PORT=3001
TEST_DATABASE_URL=postgresql://test_user:test_password@localhost:5432/test_db
TEST_SECRET_KEY=your_test_secret_key
TEST_POSTGRES_DB=test_db
TEST_POSTGRES_USER=test_user
TEST_POSTGRES_PASSWORD=test_password
```

#### 生产环境配置
```
PROD_ECS_HOST=prod-server-ip
PROD_ECS_USERNAME=root
PROD_ECS_SSH_KEY=your_ssh_private_key
PROD_ECS_PORT=22
PROD_PROJECT_PATH=/opt/saas_platform_prod
PROD_APP_PORT=8000
PROD_DATABASE_URL=postgresql://prod_user:prod_password@localhost:5432/prod_db
PROD_SECRET_KEY=your_prod_secret_key
PROD_POSTGRES_DB=prod_db
PROD_POSTGRES_USER=prod_user
PROD_POSTGRES_PASSWORD=prod_password
```

### GitHub Environments 配置

在 GitHub 仓库的 Settings > Environments 中创建两个环境：

1. **test** - 测试环境
2. **production** - 生产环境

为每个环境配置保护规则和审批流程。

## 🚀 部署流程

### 自动部署触发条件

| 分支/标签 | 环境 | 触发条件 |
|-----------|------|----------|
| `develop` | 测试环境 | 推送代码到 develop 分支 |
| `main` | 生产环境 | 推送代码到 main 分支 |
| `release/*` | 生产环境 | 推送到 release/* 分支 |
| `v*` | 生产环境 | 推送版本标签 |
| 手动触发 | 可选择 | 通过 GitHub Actions 手动触发 |

### 部署步骤

1. **环境判断**: 根据分支或手动选择确定部署环境
2. **镜像构建**: 构建 Docker 镜像并推送到阿里云容器镜像仓库
3. **环境部署**: 根据环境类型执行相应的部署流程
4. **健康检查**: 验证部署是否成功
5. **通知**: 发送部署状态通知

## 📊 环境差异

### 测试环境
- **调试模式**: `DEBUG=true`
- **日志级别**: `DEBUG`
- **端口**: 3001
- **数据库**: 测试数据库
- **健康检查**: 10次重试，每次间隔10秒

### 生产环境
- **调试模式**: `DEBUG=false`
- **日志级别**: `INFO`
- **端口**: 8000
- **数据库**: 生产数据库
- **健康检查**: 15次重试，每次间隔15秒
- **数据备份**: 部署前自动备份数据库
- **优雅停止**: 部署前优雅停止现有服务

## 🔍 监控和日志

### 查看部署状态
1. 访问 GitHub Actions 页面查看部署进度
2. 查看部署日志了解详细信息
3. 通过通知了解部署结果

### 服务器日志
```bash
# 查看应用日志
docker-compose -f docker-compose.prod.yml logs app

# 查看数据库日志
docker-compose -f docker-compose.prod.yml logs db

# 查看 Redis 日志
docker-compose -f docker-compose.prod.yml logs redis
```

### 健康检查
- 测试环境: `http://test-server-ip:3001/health`
- 生产环境: `http://prod-server-ip:8000/health`

## 🛠️ 故障排除

### 常见问题

1. **部署失败**
   - 检查 GitHub Secrets 配置是否正确
   - 验证服务器 SSH 连接
   - 查看部署日志中的错误信息

2. **健康检查失败**
   - 检查应用是否正常启动
   - 验证端口配置
   - 查看应用日志

3. **数据库连接失败**
   - 检查数据库服务状态
   - 验证数据库连接字符串
   - 确认数据库用户权限

### 回滚操作

如果需要回滚到上一个版本：

```bash
# 在服务器上执行
cd /opt/saas_platform_prod  # 或测试环境路径
git log --oneline  # 查看提交历史
git checkout <previous-commit-hash>
docker-compose -f docker-compose.prod.yml up -d
```

## 📝 最佳实践

1. **分支管理**
   - 使用 `develop` 分支进行开发
   - 使用 `main` 分支进行生产部署
   - 使用 `release/*` 分支进行发布准备

2. **安全**
   - 定期轮换 SSH 密钥和密码
   - 使用强密码和复杂密钥
   - 限制服务器访问权限

3. **监控**
   - 设置服务器监控告警
   - 定期检查应用健康状态
   - 监控资源使用情况

4. **备份**
   - 定期备份数据库
   - 保留多个版本的备份
   - 测试备份恢复流程

## 🔄 维护操作

### 手动部署
1. 访问 GitHub Actions 页面
2. 选择 "Deploy to Aliyun (Test & Production)" 工作流
3. 点击 "Run workflow"
4. 选择目标环境
5. 点击 "Run workflow" 开始部署

### 清理操作
```bash
# 清理未使用的 Docker 镜像
docker image prune -f

# 清理未使用的容器
docker container prune -f

# 清理未使用的卷
docker volume prune -f
```

## 📞 支持

如果遇到部署问题，请：
1. 查看 GitHub Actions 日志
2. 检查服务器日志
3. 联系技术支持团队
