"""
validators.py 单元测试

测试所有校验函数和 Annotated 类型
"""

from pydantic import BaseModel, ValidationError
import pytest
from src.core.validators import (
    validate_china_mobile,
    validate_china_landline,
    validate_china_mobile_or_landline,
    validate_email,
    validate_subdomain,
    validate_not_empty,
    is_mobile_number,
    is_landline_number,
    validate_area_code,
    validate_main_number,
    validate_extension,
    # Annotated 类型
    EmailStr,
    SubdomainStr,
    PhoneStr,
    LandlineStr,
    PhoneOrLandlineStr,
    NotEmptyStr
)


class TestValidateChinaMobile:
    """测试中国手机号校验"""
    
    def test_valid_mobile_numbers(self):
        """测试有效手机号"""
        valid_mobiles = [
            "13800138000",  # 移动
            "18612345678",  # 联通
            "18912345678",  # 电信
            "17712345678",  # 电信
            "15512345678",  # 联通
            "19812345678",  # 移动
        ]
        
        for mobile in valid_mobiles:
            result = validate_china_mobile(mobile)
            assert result == mobile
            print(f"✅ {mobile} -> {result}")
    
    def test_invalid_mobile_numbers(self):
        """测试无效手机号"""
        invalid_mobiles = [
            "12345678901",      # 第二位不是3-9
            "12800138000",      # 第二位不是3-9
            "1380013800",       # 长度不足
            "138001380000",     # 长度超长
            "1380013800a",      # 包含字母
            "",                 # 空字符串
            "1234567890",       # 长度不足
            "123456789012",     # 长度超长
        ]
        
        for mobile in invalid_mobiles:
            with pytest.raises(ValueError) as exc_info:
                validate_china_mobile(mobile)
            print(f"❌ {mobile} -> {exc_info.value}")
    
    def test_mobile_type_check(self):
        """测试手机号类型判断"""
        assert is_mobile_number("13800138000") == True
        assert is_mobile_number("138-0013-8000") == True
        assert is_mobile_number("010-12345678") == False
        assert is_mobile_number("12345678901") == True


class TestValidateChinaLandline:
    """测试中国座机号校验"""
    
    def test_valid_landline_numbers(self):
        """测试有效座机号"""
        valid_landlines = [
            "010-12345678",      # 北京
            "021-12345678",      # 上海
            "0311-12345678",     # 石家庄
            "0755-12345678",     # 深圳
            "400-1234567",       # 400电话
            "800-1234567",       # 800电话
            "010-12345678-1234", # 带分机号
        ]
        
        for landline in valid_landlines:
            result = validate_china_landline(landline)
            assert result is not None
            print(f"✅ {landline} -> {result}")
    
    def test_invalid_landline_numbers(self):
        """测试无效座机号"""
        invalid_landlines = [
            "123-12345678",      # 区号错误
            "010-1234567",       # 主号码长度错误
            "010-123456789",     # 主号码长度错误
            "010-12345678-12345", # 分机号过长
            "010-12345678-abc",  # 分机号包含字母
            "",                  # 空字符串
            "01012345678",       # 缺少分隔符
        ]
        
        for landline in invalid_landlines:
            with pytest.raises(ValueError) as exc_info:
                validate_china_landline(landline)
            print(f"❌ {landline} -> {exc_info.value}")
    
    def test_landline_type_check(self):
        """测试座机号类型判断"""
        assert is_landline_number("010-12345678") == True
        assert is_landline_number("010 12345678") == True
        assert is_landline_number("13800138000") == False
        assert is_landline_number("123-12345678") == True  # 格式正确但区号可能无效


class TestValidateChinaMobileOrLandline:
    """测试联合校验"""
    
    def test_valid_phone_numbers(self):
        """测试有效电话号码（手机号或座机号）"""
        valid_phones = [
            # 手机号
            "13800138000",
            "18612345678",
            "18912345678",
            # 座机号
            "010-12345678",
            "021-12345678",
            "0755-12345678",
            "400-1234567",
            "800-1234567",
            "010-12345678-1234",
        ]
        
        for phone in valid_phones:
            result = validate_china_mobile_or_landline(phone)
            assert result is not None
            print(f"✅ {phone} -> {result}")
    
    def test_invalid_phone_numbers(self):
        """测试无效电话号码"""
        invalid_phones = [
            "12345678901",      # 手机号格式错误
            "12800138000",      # 手机号第二位错误
            "123-12345678",     # 座机号区号错误
            "010-1234567",      # 座机号主号码长度错误
            "",                 # 空字符串
            "abc123",           # 包含字母
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValueError) as exc_info:
                validate_china_mobile_or_landline(phone)
            print(f"❌ {phone} -> {exc_info.value}")


class TestValidateEmail:
    """测试邮箱校验"""
    
    def test_valid_emails(self):
        """测试有效邮箱"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "user123@test-domain.com",
        ]
        
        for email in valid_emails:
            result = validate_email(email)
            assert result == email.lower()
            print(f"✅ {email} -> {result}")
    
    def test_invalid_emails(self):
        """测试无效邮箱"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user@domain.",
            "",
            "user@domain..com",
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValueError) as exc_info:
                validate_email(email)
            print(f"❌ {email} -> {exc_info.value}")


class TestValidateSubdomain:
    """测试子域名校验"""
    
    def test_valid_subdomains(self):
        """测试有效子域名"""
        valid_subdomains = [
            "mycompany",
            "test-123",
            "abc123",
            "company-name",
            "test123",
        ]
        
        for subdomain in valid_subdomains:
            result = validate_subdomain(subdomain)
            assert result == subdomain.lower()
            print(f"✅ {subdomain} -> {result}")
    
    def test_invalid_subdomains(self):
        """测试无效子域名"""
        invalid_subdomains = [
            "www",              # 保留字
            "api",              # 保留字
            "admin",            # 保留字
            "ab",               # 长度不足
            "-company",         # 以连字符开头
            "company-",         # 以连字符结尾
            "company_name",     # 包含下划线
            "Company",          # 包含大写字母
            "",                 # 空字符串
        ]
        
        for subdomain in invalid_subdomains:
            with pytest.raises(ValueError) as exc_info:
                validate_subdomain(subdomain)
            print(f"❌ {subdomain} -> {exc_info.value}")


class TestValidateNotEmpty:
    """测试非空字符串校验"""
    
    def test_valid_strings(self):
        """测试有效字符串"""
        valid_strings = [
            "hello",
            "test 123",
            "中文字符",
            "a" * 100,  # 100个字符
        ]
        
        for string in valid_strings:
            result = validate_not_empty(string, "测试字段")
            assert result == string.strip()
            print(f"✅ '{string}' -> '{result}'")
    
    def test_invalid_strings(self):
        """测试无效字符串"""
        invalid_strings = [
            "",                 # 空字符串
            "   ",             # 只有空格
            "a" * 1001,        # 长度超长
        ]
        
        for string in invalid_strings:
            with pytest.raises(ValueError) as exc_info:
                validate_not_empty(string, "测试字段")
            print(f"❌ '{string}' -> {exc_info.value}")


class TestAnnotatedTypes:
    """测试 Annotated 类型"""
    
    def test_email_str_type(self):
        """测试 EmailStr 类型"""
        class TestModel(BaseModel):
            email: EmailStr
        
        # 有效邮箱
        model = TestModel(email="test@example.com")
        assert model.email == "test@example.com"
        
        # 无效邮箱
        with pytest.raises(ValidationError):
            TestModel(email="invalid-email")
    
    def test_phone_str_type(self):
        """测试 PhoneStr 类型"""
        class TestModel(BaseModel):
            phone: PhoneStr
        
        # 有效手机号
        model = TestModel(phone="13800138000")
        assert model.phone == "13800138000"
        
        # 无效手机号
        with pytest.raises(ValidationError):
            TestModel(phone="12345678901")
    
    def test_landline_str_type(self):
        """测试 LandlineStr 类型"""
        class TestModel(BaseModel):
            landline: LandlineStr
        
        # 有效座机号
        model = TestModel(landline="010-12345678")
        assert model.landline == "010-12345678"
        
        # 无效座机号
        with pytest.raises(ValidationError):
            TestModel(landline="123-12345678")
    
    def test_phone_or_landline_str_type(self):
        """测试 PhoneOrLandlineStr 类型"""
        class TestModel(BaseModel):
            phone: PhoneOrLandlineStr
        
        # 有效手机号
        model = TestModel(phone="13800138000")
        assert model.phone == "13800138000"
        
        # 有效座机号
        model = TestModel(phone="010-12345678")
        assert model.phone == "010-12345678"
        
        # 无效电话号码
        with pytest.raises(ValidationError):
            TestModel(phone="12345678901")
    
    def test_subdomain_str_type(self):
        """测试 SubdomainStr 类型"""
        class TestModel(BaseModel):
            subdomain: SubdomainStr
        
        # 有效子域名
        model = TestModel(subdomain="mycompany")
        assert model.subdomain == "mycompany"
        
        # 无效子域名
        with pytest.raises(ValidationError):
            TestModel(subdomain="www")
    
    def test_not_empty_str_type(self):
        """测试 NotEmptyStr 类型"""
        class TestModel(BaseModel):
            name: NotEmptyStr
        
        # 有效字符串
        model = TestModel(name="test")
        assert model.name == "test"
        
        # 无效字符串
        with pytest.raises(ValidationError):
            TestModel(name="")


class TestUtilityFunctions:
    """测试工具函数"""
    
    def test_validate_area_code(self):
        """测试区号验证"""
        # 有效区号
        assert validate_area_code("010") == True  # 北京
        assert validate_area_code("021") == True  # 上海
        assert validate_area_code("0755") == True  # 深圳
        
        # 无效区号
        assert validate_area_code("123") == False
        assert validate_area_code("0123") == False
        assert validate_area_code("1234") == False
    
    def test_validate_main_number(self):
        """测试主号码验证"""
        # 有效主号码
        assert validate_main_number("12345678", "010") == True  # 普通座机
        assert validate_main_number("1234567", "400") == True  # 400电话
        assert validate_main_number("1234567", "800") == True  # 800电话
        
        # 无效主号码
        assert validate_main_number("1234567", "010") == False  # 普通座机应该是8位
        assert validate_main_number("12345678", "400") == False  # 400电话应该是7位
    
    def test_validate_extension(self):
        """测试分机号验证"""
        # 有效分机号
        assert validate_extension("1234") == True
        assert validate_extension("123") == True
        assert validate_extension("1") == True
        
        # 无效分机号
        assert validate_extension("12345") == False  # 长度超长
        assert validate_extension("abc") == False    # 包含字母
        assert validate_extension("") == False       # 空字符串


class TestEdgeCases:
    """测试边界情况"""
    
    def test_whitespace_handling(self):
        """测试空格处理"""
        # 手机号
        result = validate_china_mobile("  13800138000  ")
        assert result == "13800138000"
        
        # 座机号
        result = validate_china_landline("  010-12345678  ")
        assert result == "010-12345678"
        
        # 邮箱
        result = validate_email("  test@example.com  ")
        assert result == "test@example.com"
    
    def test_case_sensitivity(self):
        """测试大小写敏感性"""
        # 子域名应该转换为小写
        result = validate_subdomain("MyCompany")
        assert result == "mycompany"
        
        # 邮箱应该转换为小写
        result = validate_email("Test@Example.COM")
        assert result == "test@example.com"
    
    def test_special_characters(self):
        """测试特殊字符处理"""
        # 手机号中的特殊字符应该被清理
        result = validate_china_mobile("138-0013-8000")
        assert result == "13800138000"
        
        # 座机号中的特殊字符应该被标准化
        result = validate_china_landline("010 12345678")
        assert result == "010-12345678"


# 运行测试的辅助函数
def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行 validators.py 单元测试...")
    print("=" * 50)
    
    # 运行各个测试类
    test_classes = [
        TestValidateChinaMobile,
        TestValidateChinaLandline,
        TestValidateChinaMobileOrLandline,
        TestValidateEmail,
        TestValidateSubdomain,
        TestValidateNotEmpty,
        TestAnnotatedTypes,
        TestUtilityFunctions,
        TestEdgeCases,
    ]
    
    for test_class in test_classes:
        print(f"\n📋 运行 {test_class.__name__}...")
        test_instance = test_class()
        
        # 获取所有测试方法
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"✅ {method_name} 通过")
            except Exception as e:
                print(f"❌ {method_name} 失败: {e}")
    
    print("\n🎉 所有测试完成！")


if __name__ == "__main__":
    run_all_tests()