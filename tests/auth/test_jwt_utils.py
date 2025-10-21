"""
JWT工具模块的单元测试
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from src.saas.auth.jwt_utils import JWTManager, jwt_manager
from src.core.config import settings


class TestJWTManager:
    """JWT管理器测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.jwt_manager = JWTManager()
        self.test_user_data = {
            "sub": "123",
            "email": "test@example.com",
            "tenant_id": 1,
            "is_superuser": False
        }
    
    def test_create_access_token_success(self):
        """
        测试创建访问令牌 - 成功场景
        完整实现，其他方法保持空结构
        """
        # 准备测试数据
        test_data = self.test_user_data.copy()
        
        # 执行测试
        token = self.jwt_manager.create_access_token(test_data)
        
        # 验证结果
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌可以正确解码
        payload = self.jwt_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == test_data["sub"]
        assert payload["email"] == test_data["email"]
        assert payload["tenant_id"] == test_data["tenant_id"]
        assert payload["is_superuser"] == test_data["is_superuser"]
        
        # 验证过期时间
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60  # 允许1分钟的误差
    
    def test_create_access_token_with_custom_expiry(self):
        """测试创建访问令牌 - 自定义过期时间"""
        test_data = self.test_user_data.copy()

        token = self.jwt_manager.create_access_token(test_data, timedelta(minutes=10))

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        payload = self.jwt_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == test_data["sub"]
        assert payload["email"] == test_data["email"]
        assert payload["tenant_id"] == test_data["tenant_id"]
        assert payload["is_superuser"] == test_data["is_superuser"]

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=10)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60  # 允许1分钟的误差
    
    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        test_data = self.test_user_data.copy()

        token = self.jwt_manager.create_refresh_token(test_data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        payload = self.jwt_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == test_data["sub"]
        assert payload["email"] == test_data["email"]
        assert payload["tenant_id"] == test_data["tenant_id"]
        assert payload["is_superuser"] == test_data["is_superuser"]

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(days=7)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60  # 允许1分钟的误差
    
    def test_verify_token_valid(self):
        """测试验证令牌 - 有效令牌"""
        test_data = self.test_user_data.copy()
        token = self.jwt_manager.create_access_token(test_data)

        payload = self.jwt_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == test_data["sub"]
        assert payload["email"] == test_data["email"]
        assert payload["tenant_id"] == test_data["tenant_id"]
        assert payload["is_superuser"] == test_data["is_superuser"]
    
    def test_verify_token_invalid(self):
        """测试验证令牌 - 无效令牌"""
        token = "invalid_token"
        payload = self.jwt_manager.verify_token(token)
        assert payload is None

    def test_verify_token_expired(self):
        """测试验证令牌 - 过期令牌"""
        test_data = self.test_user_data.copy()
        token = self.jwt_manager.create_access_token(test_data, timedelta(seconds=-1))

        payload = self.jwt_manager.verify_token(token)
        assert payload is None
    
    def test_verify_token_wrong_secret(self):
        """测试验证令牌 - 错误密钥"""
        # 准备测试数据
        test_data = self.test_user_data.copy()
        
        # 使用正确的密钥创建令牌
        token = self.jwt_manager.create_access_token(test_data)
        assert token is not None
        
        # 创建一个使用错误密钥的JWT管理器
        wrong_jwt_manager = JWTManager()
        wrong_jwt_manager.secret_key = "wrong_secret_key_12345"
        
        # 使用错误的密钥验证令牌
        payload = wrong_jwt_manager.verify_token(token)
        
        # 验证结果：应该返回None，因为密钥不匹配
        assert payload is None
    
    def test_verify_refresh_token_valid(self):
        """测试验证刷新令牌 - 有效刷新令牌"""
        # 准备测试数据
        test_data = self.test_user_data.copy()
        
        # 创建刷新令牌
        refresh_token = self.jwt_manager.create_refresh_token(test_data)
        assert refresh_token is not None
        
        # 验证刷新令牌
        payload = self.jwt_manager.verify_refresh_token(refresh_token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["sub"] == test_data["sub"]
        assert payload["email"] == test_data["email"]
    
    def test_verify_refresh_token_invalid_type(self):
        """测试验证刷新令牌 - 无效类型（访问令牌）"""
        # 准备测试数据
        test_data = self.test_user_data.copy()
        
        # 创建访问令牌（不是刷新令牌）
        access_token = self.jwt_manager.create_access_token(test_data)
        assert access_token is not None
        
        # 尝试用刷新令牌验证方法验证访问令牌
        payload = self.jwt_manager.verify_refresh_token(access_token)
        
        # 验证结果：应该返回None，因为不是刷新令牌
        assert payload is None
    
    def test_verify_refresh_token_expired(self):
        """测试验证刷新令牌 - 过期刷新令牌"""
        # 准备测试数据
        test_data = self.test_user_data.copy()
        
        # 创建已过期的刷新令牌（1小时前过期）
        from datetime import timedelta
        expired_token = self.jwt_manager.create_refresh_token(test_data)
        
        # 模拟过期：修改令牌使其过期
        # 注意：这里我们创建一个负过期时间的令牌
        expired_data = test_data.copy()
        expired_token = self.jwt_manager.create_refresh_token(expired_data)
        
        # 由于JWT库会自动验证过期时间，我们直接测试过期场景
        # 创建一个已经过期的令牌
        import time
        expired_payload = {
            **test_data,
            "exp": int(time.time()) - 3600,  # 1小时前过期
            "type": "refresh"
        }
        
        # 手动创建一个过期的令牌（仅用于测试）
        from jose import jwt
        expired_token = jwt.encode(expired_payload, self.jwt_manager.secret_key, algorithm=self.jwt_manager.algorithm)
        
        # 验证过期的刷新令牌
        payload = self.jwt_manager.verify_refresh_token(expired_token)
        
        # 验证结果：应该返回None，因为令牌已过期
        assert payload is None
    
    def test_verify_password_correct(self):
        """测试验证密码 - 正确密码"""
        # 准备测试数据
        plain_password = "test_password_123"
        
        # 生成密码哈希
        hashed_password = self.jwt_manager.get_password_hash(plain_password)
        assert hashed_password is not None
        assert hashed_password != plain_password  # 确保密码被哈希了
        
        # 验证密码
        is_valid = self.jwt_manager.verify_password(plain_password, hashed_password)
        
        # 验证结果：应该返回True
        assert is_valid is True
    
    def test_verify_password_incorrect(self):
        """测试验证密码 - 错误密码"""
        # 准备测试数据
        correct_password = "correct_password_123"
        wrong_password = "wrong_password_456"
        
        # 生成密码哈希
        hashed_password = self.jwt_manager.get_password_hash(correct_password)
        assert hashed_password is not None
        
        # 验证错误密码
        is_valid = self.jwt_manager.verify_password(wrong_password, hashed_password)
        
        # 验证结果：应该返回False
        assert is_valid is False
        
        # 额外测试：确保正确密码仍然有效
        is_correct_valid = self.jwt_manager.verify_password(correct_password, hashed_password)
        assert is_correct_valid is True
    
    def test_get_password_hash(self):
        """测试生成密码哈希"""
        # 准备测试数据
        test_passwords = [
            "simple_password",
            "Complex_P@ssw0rd!",
            "中文密码123",
            "123456789",
            ""  # 空密码
        ]
        
        for password in test_passwords:
            # 生成密码哈希
            hashed = self.jwt_manager.get_password_hash(password)
            
            # 验证哈希结果
            assert hashed is not None
            assert hashed != password  # 确保密码被哈希了
            assert len(hashed) > 0  # 确保哈希不为空
            
            # 验证哈希格式（应该包含冒号分隔的迭代次数、盐值和哈希值）
            parts = hashed.split(':')
            assert len(parts) == 3, f"密码哈希格式不正确: {hashed}"
            
            # 验证各部分都是有效的
            assert parts[0].isdigit(), "迭代次数应该是数字"
            assert int(parts[0]) > 0, "迭代次数应该大于0"
            
            # 验证可以正确验证密码
            is_valid = self.jwt_manager.verify_password(password, hashed)
            assert is_valid is True, f"密码验证失败: {password}"
    
    def test_create_access_token_empty_data(self):
        """测试创建访问令牌 - 空数据"""
        # 测试空字典
        empty_data = {}
        token = self.jwt_manager.create_access_token(empty_data)
        
        # 验证令牌仍然可以创建（JWT允许空payload）
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌可以解码
        payload = self.jwt_manager.verify_token(token)
        assert payload is not None
        
        # 验证payload只包含exp字段
        assert "exp" in payload
        # 验证没有其他字段（除了exp）
        payload_without_exp = {k: v for k, v in payload.items() if k != "exp"}
        assert len(payload_without_exp) == 0
    
    def test_create_access_token_missing_sub(self):
        """测试创建访问令牌 - 缺少sub字段"""
        # 准备测试数据（缺少sub字段）
        test_data = {
            "email": "test@example.com",
            "tenant_id": 1,
            "is_superuser": False
            # 注意：故意缺少 "sub" 字段
        }
        
        # 创建令牌（应该成功，因为JWT不强制要求sub字段）
        token = self.jwt_manager.create_access_token(test_data)
        
        # 验证令牌创建成功
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌可以解码
        payload = self.jwt_manager.verify_token(token)
        assert payload is not None
        
        # 验证payload包含所有提供的字段
        assert payload["email"] == test_data["email"]
        assert payload["tenant_id"] == test_data["tenant_id"]
        assert payload["is_superuser"] == test_data["is_superuser"]
        assert "exp" in payload  # 过期时间字段
        
        # 验证确实缺少sub字段
        assert "sub" not in payload
    
    def test_verify_token_none(self):
        """测试验证令牌 - None值"""
        # 测试None值
        payload = self.jwt_manager.verify_token(None)
        
        # 验证结果：应该返回None
        assert payload is None
    
    def test_verify_token_empty_string(self):
        """测试验证令牌 - 空字符串"""
        # 测试空字符串
        payload = self.jwt_manager.verify_token("")
        
        # 验证结果：应该返回None
        assert payload is None
        
        # 测试只包含空格的字符串
        payload_whitespace = self.jwt_manager.verify_token("   ")
        
        # 验证结果：应该返回None（因为strip后为空）
        assert payload_whitespace is None
    
    def test_verify_token_malformed(self):
        """测试验证令牌 - 格式错误的令牌"""
        # 测试各种格式错误的令牌
        malformed_tokens = [
            "invalid.token",  # 只有两部分
            "invalid",  # 只有一部分
            "invalid.token.malformed.extra",  # 超过三部分
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",  # 有效头部，无效载荷
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.invalid",  # 有效头部和载荷，无效签名
            "not.a.jwt.token",  # 随机字符串
            "a.b.c.d.e.f",  # 太多部分
        ]
        
        for token in malformed_tokens:
            payload = self.jwt_manager.verify_token(token)
            assert payload is None, f"格式错误的令牌应该返回None: {token}"
    
    def test_password_hash_consistency(self):
        """测试密码哈希的一致性"""
        # 准备测试数据
        test_password = "consistent_password_123"
        
        # 生成多个哈希
        hash1 = self.jwt_manager.get_password_hash(test_password)
        hash2 = self.jwt_manager.get_password_hash(test_password)
        hash3 = self.jwt_manager.get_password_hash(test_password)
        
        # 验证哈希都不相同（因为每次生成不同的盐值）
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3
        
        # 验证所有哈希都能正确验证原密码
        assert self.jwt_manager.verify_password(test_password, hash1) is True
        assert self.jwt_manager.verify_password(test_password, hash2) is True
        assert self.jwt_manager.verify_password(test_password, hash3) is True
        
        # 验证错误密码在所有哈希上都验证失败
        assert self.jwt_manager.verify_password("wrong_password", hash1) is False
        assert self.jwt_manager.verify_password("wrong_password", hash2) is False
        assert self.jwt_manager.verify_password("wrong_password", hash3) is False
    
    def test_password_hash_uniqueness(self):
        """测试密码哈希的唯一性"""
        # 准备测试数据
        passwords = [
            "password1",
            "password2",
            "Password1",  # 大小写不同
            "password1 ",  # 末尾有空格
            " password1",  # 开头有空格
            "PASSWORD1",  # 全大写
            "123456",
            "abcdef",
            "!@#$%^&*()",
            "中文密码",
            "",  # 空密码
        ]
        
        # 生成所有密码的哈希
        hashes = []
        for password in passwords:
            hash_value = self.jwt_manager.get_password_hash(password)
            hashes.append(hash_value)
        
        # 验证所有哈希都是唯一的
        unique_hashes = set(hashes)
        assert len(unique_hashes) == len(hashes), "所有密码哈希应该是唯一的"
        
        # 验证每个哈希都能正确验证对应的密码
        for i, password in enumerate(passwords):
            assert self.jwt_manager.verify_password(password, hashes[i]) is True
            # 验证其他密码不能验证这个哈希
            for j, other_password in enumerate(passwords):
                if i != j:
                    assert self.jwt_manager.verify_password(other_password, hashes[i]) is False


class TestJWTManagerIntegration:
    """JWT管理器集成测试类"""
    
    def test_full_auth_flow(self):
        """测试完整的认证流程"""
        # 准备测试数据
        user_data = {
            "sub": "123",
            "email": "test@example.com",
            "tenant_id": 1,
            "is_superuser": False
        }
        
        # 1. 创建访问令牌
        access_token = jwt_manager.create_access_token(user_data)
        assert access_token is not None
        
        # 2. 创建刷新令牌
        refresh_token = jwt_manager.create_refresh_token(user_data)
        assert refresh_token is not None
        
        # 3. 验证访问令牌
        payload = jwt_manager.verify_token(access_token)
        assert payload is not None
        assert payload["sub"] == user_data["sub"]
        assert payload["email"] == user_data["email"]
        
        # 4. 验证刷新令牌
        refresh_payload = jwt_manager.verify_token(refresh_token)
        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["sub"] == user_data["sub"]
        
        # 5. 使用刷新令牌生成新的访问令牌（使用不同的过期时间）
        new_access_token = jwt_manager.create_access_token(user_data, timedelta(minutes=30))
        assert new_access_token is not None
        # 注意：由于数据相同且时间相近，令牌可能相同，这是正常的JWT行为
        
        # 6. 验证新令牌
        new_payload = jwt_manager.verify_token(new_access_token)
        assert new_payload is not None
        assert new_payload["sub"] == user_data["sub"]
    
    def test_token_refresh_flow(self):
        """测试令牌刷新流程"""
        # 准备测试数据
        user_data = {
            "sub": "456",
            "email": "refresh@example.com",
            "tenant_id": 2,
            "is_superuser": True
        }
        
        # 1. 创建刷新令牌
        refresh_token = jwt_manager.create_refresh_token(user_data)
        assert refresh_token is not None
        
        # 2. 验证刷新令牌
        refresh_payload = jwt_manager.verify_token(refresh_token)
        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"
        
        # 3. 使用刷新令牌创建新的访问令牌
        new_access_token = jwt_manager.create_access_token(user_data)
        assert new_access_token is not None
        
        # 4. 验证新访问令牌
        access_payload = jwt_manager.verify_token(new_access_token)
        assert access_payload is not None
        assert access_payload["sub"] == user_data["sub"]
        assert "type" not in access_payload or access_payload.get("type") != "refresh"  # 访问令牌不应该有type字段
        
        # 5. 验证刷新令牌仍然有效
        assert jwt_manager.verify_token(refresh_token) is not None
    
    def test_multiple_tokens_same_user(self):
        """测试同一用户的多个令牌"""
        # 准备测试数据
        user_data = {
            "sub": "789",
            "email": "multi@example.com",
            "tenant_id": 3,
            "is_superuser": False
        }
        
        # 创建多个访问令牌（使用不同的过期时间）
        tokens = []
        for i in range(5):
            # 使用不同的过期时间确保令牌不同
            token = jwt_manager.create_access_token(user_data, timedelta(minutes=30 + i))
            tokens.append(token)
            assert token is not None
        
        # 验证所有令牌都是不同的
        unique_tokens = set(tokens)
        assert len(unique_tokens) == len(tokens), "使用不同过期时间的令牌应该是唯一的"
        
        # 验证所有令牌都能正确解码
        for token in tokens:
            payload = jwt_manager.verify_token(token)
            assert payload is not None
            assert payload["sub"] == user_data["sub"]
            assert payload["email"] == user_data["email"]
            assert payload["tenant_id"] == user_data["tenant_id"]
        
        # 创建多个刷新令牌（添加时间戳确保唯一性）
        refresh_tokens = []
        for i in range(3):
            # 添加时间戳字段确保令牌唯一性
            user_data_with_timestamp = user_data.copy()
            user_data_with_timestamp["timestamp"] = f"refresh_{i}"
            refresh_token = jwt_manager.create_refresh_token(user_data_with_timestamp)
            refresh_tokens.append(refresh_token)
            assert refresh_token is not None
        
        # 验证刷新令牌也是唯一的
        unique_refresh_tokens = set(refresh_tokens)
        assert len(unique_refresh_tokens) == len(refresh_tokens), "使用不同时间戳的刷新令牌应该是唯一的"
    
    def test_different_users_tokens(self):
        """测试不同用户的令牌"""
        # 准备多个用户的测试数据
        users_data = [
            {
                "sub": "101",
                "email": "user1@example.com",
                "tenant_id": 1,
                "is_superuser": False
            },
            {
                "sub": "102",
                "email": "user2@example.com",
                "tenant_id": 2,
                "is_superuser": True
            },
            {
                "sub": "103",
                "email": "user3@example.com",
                "tenant_id": 1,
                "is_superuser": False
            }
        ]
        
        # 为每个用户创建令牌
        all_tokens = []
        for user_data in users_data:
            access_token = jwt_manager.create_access_token(user_data)
            refresh_token = jwt_manager.create_refresh_token(user_data)
            
            assert access_token is not None
            assert refresh_token is not None
            
            all_tokens.extend([access_token, refresh_token])
            
            # 验证令牌内容正确
            access_payload = jwt_manager.verify_token(access_token)
            refresh_payload = jwt_manager.verify_token(refresh_token)
            
            assert access_payload["sub"] == user_data["sub"]
            assert access_payload["email"] == user_data["email"]
            assert access_payload["tenant_id"] == user_data["tenant_id"]
            
            assert refresh_payload["sub"] == user_data["sub"]
            assert refresh_payload["type"] == "refresh"
        
        # 验证所有令牌都是唯一的
        unique_tokens = set(all_tokens)
        assert len(unique_tokens) == len(all_tokens), "不同用户的所有令牌应该是唯一的"
        
        # 验证令牌隔离性：一个用户的令牌不应该能验证其他用户的数据
        for i, user_data in enumerate(users_data):
            user_tokens = all_tokens[i*2:(i+1)*2]  # 每个用户有2个令牌
            
            for token in user_tokens:
                payload = jwt_manager.verify_token(token)
                assert payload["sub"] == user_data["sub"]
                
                # 验证其他用户的数据不能匹配
                for j, other_user_data in enumerate(users_data):
                    if i != j:
                        assert payload["sub"] != other_user_data["sub"]
                        assert payload["email"] != other_user_data["email"]


class TestJWTManagerEdgeCases:
    """JWT管理器边界情况测试类"""
    
    def test_very_long_email(self):
        """测试超长邮箱地址"""
        # 创建超长邮箱地址（超过正常邮箱长度）
        long_email = "a" * 100 + "@" + "example.com"
        assert len(long_email) > 100
        
        user_data = {
            "sub": "long_email_user",
            "email": long_email,
            "tenant_id": 1,
            "is_superuser": False
        }
        
        # 创建令牌
        token = jwt_manager.create_access_token(user_data)
        assert token is not None
        
        # 验证令牌
        payload = jwt_manager.verify_token(token)
        assert payload is not None
        assert payload["email"] == long_email
        assert payload["sub"] == user_data["sub"]
    
    def test_very_long_tenant_id(self):
        """测试超长租户ID"""
        # 创建超长租户ID（虽然是数字，但测试大数值）
        large_tenant_id = 999999999999999999
        
        user_data = {
            "sub": "large_tenant_user",
            "email": "large_tenant@example.com",
            "tenant_id": large_tenant_id,
            "is_superuser": False
        }
        
        # 创建令牌
        token = jwt_manager.create_access_token(user_data)
        assert token is not None
        
        # 验证令牌
        payload = jwt_manager.verify_token(token)
        assert payload is not None
        assert payload["tenant_id"] == large_tenant_id
        assert payload["sub"] == user_data["sub"]
    
    def test_special_characters_in_data(self):
        """测试数据中的特殊字符"""
        # 测试包含特殊字符的数据
        special_user_data = {
            "sub": "special_user_!@#$%^&*()",
            "email": "test+special@example-domain.co.uk",
            "tenant_id": 1,
            "is_superuser": False
        }
        
        # 创建令牌
        token = jwt_manager.create_access_token(special_user_data)
        assert token is not None
        
        # 验证令牌
        payload = jwt_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == special_user_data["sub"]
        assert payload["email"] == special_user_data["email"]
        
        # 测试Unicode字符
        unicode_user_data = {
            "sub": "unicode_user_测试",
            "email": "测试@example.com",
            "tenant_id": 2,
            "is_superuser": True
        }
        
        # 创建Unicode令牌
        unicode_token = jwt_manager.create_access_token(unicode_user_data)
        assert unicode_token is not None
        
        # 验证Unicode令牌
        unicode_payload = jwt_manager.verify_token(unicode_token)
        assert unicode_payload is not None
        assert unicode_payload["sub"] == unicode_user_data["sub"]
        assert unicode_payload["email"] == unicode_user_data["email"]
    
    def test_unicode_characters(self):
        """测试Unicode字符"""
        # Unicode测试已经在test_special_characters_in_data中实现了
        # 这里添加更多Unicode测试用例
        unicode_test_cases = [
            "用户_123",
            "用户名@example.com",
            "🚀🚀🚀",
            "测试用户_αβγδε",
            "مستخدم_اختبار",  # 阿拉伯语
            "ユーザー_テスト",  # 日语
            "사용자_테스트",   # 韩语
        ]
        
        for i, unicode_text in enumerate(unicode_test_cases):
            user_data = {
                "sub": f"unicode_user_{i}",
                "email": f"{unicode_text}@example.com",
                "tenant_id": i + 1,
                "is_superuser": False
            }
            
            # 创建令牌
            token = jwt_manager.create_access_token(user_data)
            assert token is not None
            
            # 验证令牌
            payload = jwt_manager.verify_token(token)
            assert payload is not None
            assert payload["sub"] == user_data["sub"]
            assert payload["email"] == user_data["email"]
    
    def test_zero_expiry_time(self):
        """测试零过期时间"""
        user_data = {
            "sub": "zero_expiry_user",
            "email": "zero@example.com",
            "tenant_id": 1,
            "is_superuser": False
        }
        
        # 创建零过期时间的令牌
        token = jwt_manager.create_access_token(user_data, timedelta(seconds=0))
        assert token is not None
        
        # 验证令牌可以创建（这是主要测试目标）
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌可以解码（即使可能已过期）
        payload = jwt_manager.verify_token(token)
        # 注意：令牌可能已过期，但我们主要测试创建功能
        # 如果payload为None，说明令牌已过期，这也是正常的
        if payload is not None:
            # 验证payload结构正确
            assert "exp" in payload
            assert payload["sub"] == user_data["sub"]
    
    def test_negative_expiry_time(self):
        """测试负过期时间"""
        user_data = {
            "sub": "negative_expiry_user",
            "email": "negative@example.com",
            "tenant_id": 1,
            "is_superuser": False
        }
        
        # 创建负过期时间的令牌（已经过期）
        token = jwt_manager.create_access_token(user_data, timedelta(seconds=-3600))  # 1小时前过期
        assert token is not None
        
        # 验证令牌（应该已经过期）
        payload = jwt_manager.verify_token(token)
        # 令牌应该已经过期，所以payload应该为None
        assert payload is None, "负过期时间的令牌应该已经过期"


# 全局实例测试
class TestGlobalJWTManager:
    """全局JWT管理器实例测试类"""
    
    def test_global_instance_exists(self):
        """测试全局实例存在"""
        # 验证全局实例存在
        assert jwt_manager is not None
        assert isinstance(jwt_manager, JWTManager)
        
        # 验证全局实例有必要的属性
        assert hasattr(jwt_manager, 'secret_key')
        assert hasattr(jwt_manager, 'algorithm')
        assert hasattr(jwt_manager, 'access_token_expire_minutes')
        
        # 验证属性值不为空
        assert jwt_manager.secret_key is not None
        assert jwt_manager.algorithm is not None
        assert jwt_manager.access_token_expire_minutes > 0
    
    def test_global_instance_singleton(self):
        """测试全局实例单例模式"""
        # 注意：当前实现不是真正的单例模式，而是模块级别的全局实例
        # 这里测试全局实例的一致性
        
        # 验证多次导入得到的是同一个实例
        from src.saas.auth.jwt_utils import jwt_manager as jwt_manager2
        assert jwt_manager is jwt_manager2, "全局实例应该是一致的"
        
        # 验证实例的功能正常
        test_data = {"sub": "singleton_test", "email": "test@example.com"}
        token1 = jwt_manager.create_access_token(test_data)
        token2 = jwt_manager2.create_access_token(test_data)
        
        # 两个实例创建的令牌都应该能正确验证
        payload1 = jwt_manager.verify_token(token1)
        payload2 = jwt_manager2.verify_token(token2)
        
        assert payload1 is not None
        assert payload2 is not None
        assert payload1["sub"] == test_data["sub"]
        assert payload2["sub"] == test_data["sub"]
    
    def test_global_instance_configuration(self):
        """测试全局实例配置"""
        # 验证全局实例的配置正确性
        assert jwt_manager.secret_key is not None
        assert len(jwt_manager.secret_key) > 0
        
        # 验证算法配置
        assert jwt_manager.algorithm in ["HS256", "HS384", "HS512"]
        
        # 验证过期时间配置
        assert isinstance(jwt_manager.access_token_expire_minutes, int)
        assert jwt_manager.access_token_expire_minutes > 0
        
        # 验证配置的一致性
        from src.core.config import settings
        assert jwt_manager.secret_key == settings.SECRET_KEY
        assert jwt_manager.algorithm == settings.ALGORITHM
        assert jwt_manager.access_token_expire_minutes == settings.ACCESS_TOKEN_EXPIRE_MINUTES


# 配置测试
class TestJWTConfiguration:
    """JWT配置测试类"""
    
    def test_default_algorithm(self):
        """测试默认算法"""
        # TODO: 实现默认算法的测试
        pass
    
    def test_default_expiry_time(self):
        """测试默认过期时间"""
        # TODO: 实现默认过期时间的测试
        pass
    
    def test_secret_key_required(self):
        """测试密钥必需性"""
        # TODO: 实现密钥必需性的测试
        pass
    
    def test_configuration_validation(self):
        """测试配置验证"""
        # TODO: 实现配置验证的测试
        pass


# 性能测试
class TestJWTPerformance:
    """JWT性能测试类"""
    
    def test_token_creation_performance(self):
        """测试令牌创建性能"""
        # TODO: 实现令牌创建性能的测试
        pass
    
    def test_token_verification_performance(self):
        """测试令牌验证性能"""
        # TODO: 实现令牌验证性能的测试
        pass
    
    def test_password_hashing_performance(self):
        """测试密码哈希性能"""
        # TODO: 实现密码哈希性能的测试
        pass
    
    def test_concurrent_token_creation(self):
        """测试并发令牌创建"""
        # TODO: 实现并发令牌创建的测试
        pass
