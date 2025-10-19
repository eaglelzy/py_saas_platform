from fastapi import APIRouter
from src.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/auth/test")
def auth_test():
    """测试 GET 请求"""
    logger.info("收到 GET /auth/test 请求")
    return {"message": "Auth router GET is working!"}

@router.post("/auth/test")
def auth_test_post():
    """测试 POST 请求"""
    logger.info("收到 POST /auth/test 请求")
    return {"message": "Auth router POST is working!"}

@router.get("/auth/error-test")
def auth_error_test():
    """测试错误日志记录"""
    logger.error("这是一个测试错误日志")
    return {"message": "Error test completed"}

@router.get("/auth/warning-test")
def auth_warning_test():
    """测试警告日志记录"""
    logger.warning("这是一个测试警告日志")
    return {"message": "Warning test completed"}