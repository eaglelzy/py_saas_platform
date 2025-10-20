# GitHub Actions 部署脚本测试指南

## 🧪 测试方法

### 1. 本地逻辑测试

运行我们提供的测试脚本来验证部署逻辑：

```bash
# 运行测试脚本
./test-deploy-logic.sh
```

这个脚本会测试所有可能的触发场景，验证部署逻辑是否正确。

### 2. 使用 Act 工具进行本地测试

#### 安装 Act
```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows (使用 Chocolatey)
choco install act-cli
```

#### 配置测试环境
```bash
# 创建测试用的 secrets 文件
cat > .secrets << EOF
ACR_REGISTRY=your-registry.com
ACR_USERNAME=your-username
ACR_PASSWORD=your-password
TEST_ECS_SERVER_IP=your-test-server-ip
TEST_ECS_USERNAME=your-username
TEST_ECS_SSH_PRIVATE_KEY=your-ssh-private-key
TEST_PROJECT_PATH=/path/to/test/project
TEST_APP_PORT=8080
TEST_DATABASE_URL=postgresql://user:pass@host:port/db
TEST_SECRET_KEY=your-secret-key
TEST_POSTGRES_DB=test_db
TEST_POSTGRES_USER=test_user
TEST_POSTGRES_PASSWORD=test_password
ECS_SERVER_IP=your-prod-server-ip
ECS_USERNAME=your-prod-username
ECS_SSH_PRIVATE_KEY=your-prod-ssh-private-key
PROD_PROJECT_PATH=/path/to/prod/project
PROD_APP_PORT=8888
PROD_DATABASE_URL=postgresql://user:pass@host:port/prod_db
PROD_SECRET_KEY=your-prod-secret-key
PROD_POSTGRES_DB=prod_db
PROD_POSTGRES_USER=prod_user
PROD_POSTGRES_PASSWORD=prod_password
EOF
```

#### 运行测试
```bash
# 测试 release 分支推送（测试环境部署）
act push -e .secrets --env GITHUB_REF=refs/heads/release/1.0.0

# 测试 main 分支标签推送（生产环境部署）
act push -e .secrets --env GITHUB_REF=refs/tags/v1.0.0

# 测试其他分支标签推送（应该不触发部署）
act push -e .secrets --env GITHUB_REF=refs/tags/v1.0.0-beta

# 测试手动触发
act workflow_dispatch -e .secrets --input environment=test
```

### 3. GitHub Actions 实际测试

#### 测试分支推送
```bash
# 1. 测试 release 分支推送
git checkout -b release/test-1.0.0
echo "test change" >> README.md
git add README.md
git commit -m "test: add test change"
git push origin release/test-1.0.0

# 2. 测试 develop 分支推送
git checkout develop
echo "dev change" >> README.md
git add README.md
git commit -m "dev: add dev change"
git push origin develop
```

#### 测试标签推送
```bash
# 1. 测试 main 分支的标签（生产环境）
git checkout main
git tag v1.0.0-test
git push origin v1.0.0-test

# 2. 测试其他分支的标签（应该不触发部署）
git checkout -b feature/test-tag
git tag v1.0.0-feature
git push origin v1.0.0-feature
```

#### 手动触发测试
1. 进入 GitHub 仓库的 **Actions** 页面
2. 选择 **Deploy to Aliyun (Test & Production)** 工作流
3. 点击 **Run workflow** 按钮
4. 选择部署环境并执行

### 4. 分步验证测试

#### 验证部署逻辑
```bash
# 验证不同触发条件的结果
echo "测试 release 分支推送..."
act push -e .secrets --env GITHUB_REF=refs/heads/release/1.0.0 --dry-run

echo "测试 main 分支标签推送..."
act push -e .secrets --env GITHUB_REF=refs/tags/v1.0.0 --dry-run

echo "测试其他分支标签推送..."
act push -e .secrets --env GITHUB_REF=refs/tags/v1.0.0-beta --dry-run
```

#### 验证环境变量传递
```bash
# 检查环境变量是否正确传递到各个任务
act push -e .secrets --env GITHUB_REF=refs/heads/release/1.0.0 --verbose
```

### 5. 集成测试

#### 端到端测试流程
```bash
# 1. 创建测试分支
git checkout -b test/deployment-pipeline

# 2. 修改代码
echo "# Deployment Test" >> DEPLOYMENT_TEST.md
git add DEPLOYMENT_TEST.md
git commit -m "test: add deployment test file"

# 3. 推送到 release 分支
git checkout -b release/test-deployment
git push origin release/test-deployment

# 4. 观察 GitHub Actions 执行
# 5. 验证部署结果
```

## 🔍 测试检查清单

### 部署逻辑测试
- [ ] Release 分支推送 → 测试环境部署
- [ ] Main 分支标签推送 → 生产环境部署
- [ ] 其他分支标签推送 → 不触发部署
- [ ] Develop 分支推送 → 测试环境部署
- [ ] 手动触发 → 用户选择环境
- [ ] 其他分支推送 → 不触发部署

### 环境变量测试
- [ ] 镜像标签生成正确
- [ ] 环境变量传递正确
- [ ] Secrets 配置正确
- [ ] 缓存配置正确

### 部署流程测试
- [ ] Docker 镜像构建成功
- [ ] 镜像推送到注册表成功
- [ ] SSH 连接成功
- [ ] 环境变量文件生成正确
- [ ] 数据库迁移成功
- [ ] 应用启动成功
- [ ] 健康检查通过
- [ ] 通知发送成功

## 🚨 常见问题排查

### 1. 部署不触发
- 检查分支名称是否正确
- 检查标签格式是否为 `v*`
- 检查 GitHub Actions 是否启用

### 2. 环境判断错误
- 检查 Git 分支检查逻辑
- 验证 `git branch -r --contains` 命令结果

### 3. 镜像构建失败
- 检查 Dockerfile 是否存在
- 检查 Docker 构建上下文
- 检查阿里云镜像仓库配置

### 4. 部署失败
- 检查 SSH 连接配置
- 检查服务器环境变量
- 检查 Docker Compose 文件
- 检查数据库连接

## 📊 测试报告模板

```markdown
# 部署脚本测试报告

## 测试环境
- 测试时间: YYYY-MM-DD HH:MM:SS
- 测试分支: release/test-1.0.0
- 测试标签: v1.0.0-test

## 测试结果
- [ ] 部署逻辑正确
- [ ] 环境变量传递正确
- [ ] 镜像构建成功
- [ ] 部署执行成功
- [ ] 健康检查通过

## 问题记录
- 无

## 建议
- 无
```

## 🎯 最佳实践

1. **先本地测试**: 使用 `act` 工具在本地测试部署逻辑
2. **分步验证**: 逐个测试不同的触发条件
3. **记录结果**: 记录每次测试的结果和问题
4. **渐进测试**: 从简单的逻辑测试开始，逐步进行完整测试
5. **回滚准备**: 准备回滚方案，以防测试影响生产环境
