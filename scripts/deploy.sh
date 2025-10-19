#!/bin/bash
# 阿里云部署脚本

set -e

echo "🚀 开始部署留学助手到阿里云..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查必要的环境变量
check_env() {
    echo "🔍 检查环境变量..."
    
    required_vars=("DATABASE_URL" "SECRET_KEY" "POSTGRES_PASSWORD")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo -e "${RED}❌ 错误: 环境变量 $var 未设置${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ 环境变量检查通过${NC}"
}

# 构建镜像
build_image() {
    echo "🔨 构建 Docker 镜像..."
    
    docker build -f Dockerfile.prod -t study-assistant:latest .
    
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

# 停止现有服务
stop_services() {
    echo "⏹️ 停止现有服务..."
    
    docker-compose -f docker-compose.prod.yml down || true
    
    echo -e "${GREEN}✅ 现有服务已停止${NC}"
}

# 启动服务
start_services() {
    echo "▶️ 启动服务..."
    
    docker-compose -f docker-compose.prod.yml up -d
    
    echo -e "${GREEN}✅ 服务启动完成${NC}"
}

# 健康检查
health_check() {
    echo "🏥 执行健康检查..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 健康检查通过${NC}"
            return 0
        fi
        
        echo "⏳ 等待服务启动... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    echo -e "${RED}❌ 健康检查失败${NC}"
    return 1
}

# 清理旧镜像
cleanup() {
    echo "🧹 清理旧镜像..."
    
    docker image prune -f
    
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 显示部署信息
show_info() {
    echo ""
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo ""
    echo "📋 服务信息:"
    echo "  - 应用地址: http://localhost:8000"
    echo "  - 健康检查: http://localhost:8000/health"
    echo "  - API 文档: http://localhost:8000/docs"
    echo ""
    echo "📊 查看日志:"
    echo "  - 应用日志: docker-compose -f docker-compose.prod.yml logs app"
    echo "  - 数据库日志: docker-compose -f docker-compose.prod.yml logs db"
    echo "  - Redis 日志: docker-compose -f docker-compose.prod.yml logs redis"
    echo ""
    echo "🔧 管理命令:"
    echo "  - 停止服务: docker-compose -f docker-compose.prod.yml down"
    echo "  - 重启服务: docker-compose -f docker-compose.prod.yml restart"
    echo "  - 查看状态: docker-compose -f docker-compose.prod.yml ps"
}

# 主函数
main() {
    echo -e "${YELLOW}📦 留学助手阿里云部署脚本${NC}"
    echo "=================================="
    
    check_env
    build_image
    stop_services
    start_services
    
    if health_check; then
        cleanup
        show_info
    else
        echo -e "${RED}❌ 部署失败，请检查日志${NC}"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# 错误处理
trap 'echo -e "${RED}❌ 部署过程中发生错误${NC}"; exit 1' ERR

# 执行主函数
main "$@"
