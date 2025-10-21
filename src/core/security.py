# src/core/security.py
"""
密码安全模块

提供密码哈希和验证功能，使用现代的安全算法，避免使用已废弃的 crypt 模块。
"""

import hashlib
import secrets
import base64
from typing import Union


class PasswordHasher:
    """密码哈希器，使用 PBKDF2-SHA256 算法"""
    
    def __init__(self, iterations: int = 100000):
        """
        初始化密码哈希器
        
        Args:
            iterations: PBKDF2 迭代次数，默认 100000
        """
        self.iterations = iterations
    
    def hash_password(self, password: str) -> str:
        """
        对密码进行哈希
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码（包含盐值和迭代次数信息）
        """
        # 生成随机盐值
        salt = secrets.token_bytes(32)
        
        # 使用 PBKDF2-SHA256 进行哈希
        password_bytes = password.encode('utf-8')
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password_bytes,
            salt,
            self.iterations
        )
        
        # 将盐值、迭代次数和哈希值组合并编码为字符串
        # 格式: iterations:salt:hash (base64编码)
        salt_b64 = base64.b64encode(salt).decode('ascii')
        hash_b64 = base64.b64encode(hash_bytes).decode('ascii')
        
        return f"{self.iterations}:{salt_b64}:{hash_b64}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed_password: 哈希后的密码
            
        Returns:
            bool: 密码是否匹配
        """
        try:
            # 解析哈希字符串
            parts = hashed_password.split(':')
            if len(parts) != 3:
                return False
            
            stored_iterations = int(parts[0])
            salt = base64.b64decode(parts[1])
            stored_hash = base64.b64decode(parts[2])
            
            # 使用相同的参数重新计算哈希
            password_bytes = password.encode('utf-8')
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password_bytes,
                salt,
                stored_iterations
            )
            
            # 使用 secrets.compare_digest 进行安全的比较
            return secrets.compare_digest(stored_hash, computed_hash)
            
        except (ValueError, TypeError):
            return False


# 创建全局密码哈希器实例
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    对密码进行哈希（便捷函数）
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return password_hasher.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    验证密码（便捷函数）
    
    Args:
        password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    return password_hasher.verify_password(password, hashed_password)


def is_password_hashed(password: str) -> bool:
    """
    检查字符串是否已经是哈希格式
    
    Args:
        password: 要检查的字符串
        
    Returns:
        bool: 是否为哈希格式
    """
    try:
        parts = password.split(':')
        if len(parts) != 3:
            return False
        
        int(parts[0])  # 检查迭代次数是否为整数
        base64.b64decode(parts[1])  # 检查盐值是否为有效的base64
        base64.b64decode(parts[2])  # 检查哈希值是否为有效的base64
        
        return True
    except (ValueError, TypeError):
        return False


# 测试函数
def test_password_hashing():
    """测试密码哈希功能"""
    test_password = "test_password_123"
    
    # 测试哈希
    hashed = hash_password(test_password)
    print(f"原始密码: {test_password}")
    print(f"哈希后: {hashed}")
    
    # 测试验证
    is_valid = verify_password(test_password, hashed)
    print(f"验证结果: {is_valid}")
    
    # 测试错误密码
    is_invalid = verify_password("wrong_password", hashed)
    print(f"错误密码验证: {is_invalid}")
    
    # 测试哈希格式检查
    is_hashed = is_password_hashed(hashed)
    print(f"是否为哈希格式: {is_hashed}")


if __name__ == "__main__":
    test_password_hashing()
