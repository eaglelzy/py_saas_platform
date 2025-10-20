#!/bin/bash
# 数据库初始化脚本
# 此脚本用于在部署时自动创建和初始化数据库

set -e

echo "🚀 开始数据库初始化..."

# 等待PostgreSQL服务启动
echo "⏳ 等待PostgreSQL服务启动..."
until pg_isready -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres}; do
  echo "PostgreSQL服务未就绪，等待中..."
  sleep 2
done

echo "✅ PostgreSQL服务已就绪"

# 检查数据库是否存在
DB_EXISTS=$(psql -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres} -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB:-study_assistant}'")

if [ "$DB_EXISTS" = "1" ]; then
    echo "✅ 数据库 ${POSTGRES_DB:-study_assistant} 已存在"
else
    echo "📦 创建数据库 ${POSTGRES_DB:-study_assistant}..."
    createdb -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-study_assistant}
    echo "✅ 数据库 ${POSTGRES_DB:-study_assistant} 创建成功"
fi

# 检查并创建应用用户
echo "🔍 检查应用用户..."
USER_EXISTS=$(psql -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres} -tAc "SELECT 1 FROM pg_roles WHERE rolname='saas_user'")

if [ "$USER_EXISTS" = "1" ]; then
    echo "✅ 应用用户 saas_user 已存在"
else
    echo "👤 创建应用用户 saas_user..."
    psql -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres} -c "CREATE USER saas_user WITH PASSWORD 'saas_password_2024';"
    echo "✅ 应用用户 saas_user 创建成功"
fi

# 检查并创建只读用户
echo "🔍 检查只读用户..."
READONLY_USER_EXISTS=$(psql -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres} -tAc "SELECT 1 FROM pg_roles WHERE rolname='saas_readonly'")

if [ "$READONLY_USER_EXISTS" = "1" ]; then
    echo "✅ 只读用户 saas_readonly 已存在"
else
    echo "👤 创建只读用户 saas_readonly..."
    psql -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres} -c "CREATE USER saas_readonly WITH PASSWORD 'readonly_password_2024';"
    echo "✅ 只读用户 saas_readonly 创建成功"
fi

# 授予权限
echo "🔐 设置用户权限..."
psql -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-study_assistant} << EOF
-- 给应用用户授予完整权限
GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB:-study_assistant} TO saas_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO saas_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO saas_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO saas_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO saas_user;

-- 给只读用户授予查询权限
GRANT CONNECT ON DATABASE ${POSTGRES_DB:-study_assistant} TO saas_readonly;
GRANT USAGE ON SCHEMA public TO saas_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO saas_readonly;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO saas_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO saas_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO saas_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO saas_readonly;
EOF

echo "✅ 用户权限设置完成"

# 运行初始化SQL脚本
if [ -f "/app/scripts/init-database.sql" ]; then
    echo "🔄 执行数据库初始化脚本..."
    psql -h localhost -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-study_assistant} -f /app/scripts/init-database.sql
    echo "✅ 数据库初始化脚本执行完成"
fi

# 运行Alembic迁移
if [ -f "/app/alembic.ini" ]; then
    echo "🔄 运行数据库迁移..."
    cd /app
    alembic upgrade head
    echo "✅ 数据库迁移完成"
fi

echo "🎉 数据库初始化完成！"
echo "📋 创建的用户："
echo "   - 应用用户: saas_user (密码: saas_password_2024)"
echo "   - 只读用户: saas_readonly (密码: readonly_password_2024)"
