-- 数据库初始化脚本
-- 此脚本会在PostgreSQL容器启动时自动执行

-- 创建数据库（如果不存在）
-- 注意：PostgreSQL容器启动时会自动创建POSTGRES_DB指定的数据库
-- 这个脚本主要用于创建额外的数据库或进行其他初始化操作

-- 确保数据库存在（PostgreSQL 9.1+）
SELECT 'CREATE DATABASE study_assistant'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'study_assistant')\gexec

-- 连接到study_assistant数据库
\c study_assistant;

-- 创建应用用户（如果不存在）
DO $$
BEGIN
    -- 检查用户是否存在
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lizy') THEN
        -- 创建应用用户
        CREATE USER lizy WITH PASSWORD 'Lzy142857';
        RAISE NOTICE '用户 lizy 创建成功';
    ELSE
        RAISE NOTICE '用户 lizy 已存在';
    END IF;
END $$;

-- 创建只读用户（如果不存在）
DO $$
BEGIN
    -- 检查只读用户是否存在
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'saas_readonly') THEN
        -- 创建只读用户
        CREATE USER saas_readonly WITH PASSWORD 'readonly_password_2024';
        RAISE NOTICE '只读用户 saas_readonly 创建成功';
    ELSE
        RAISE NOTICE '只读用户 saas_readonly 已存在';
    END IF;
END $$;

-- 授予权限
-- 给应用用户授予完整权限
GRANT ALL PRIVILEGES ON DATABASE study_assistant TO lizy;
GRANT ALL PRIVILEGES ON SCHEMA public TO lizy;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lizy;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lizy;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO lizy;

-- 给只读用户授予查询权限
GRANT CONNECT ON DATABASE study_assistant TO saas_readonly;
GRANT USAGE ON SCHEMA public TO saas_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO saas_readonly;

-- 设置默认权限，确保新创建的表也会自动授权
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO lizy;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO lizy;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO lizy;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO saas_readonly;

-- 创建扩展（如果需要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 设置时区
SET timezone = 'UTC';

-- 创建基础表结构（如果需要）
-- 这里可以添加一些基础表的创建语句

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '数据库 study_assistant 初始化完成！';
    RAISE NOTICE '应用用户: lizy';
    RAISE NOTICE '只读用户: saas_readonly';
END $$;
