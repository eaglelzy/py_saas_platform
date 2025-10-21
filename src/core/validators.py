"""
通用校验函数库

提供可在整个应用程序中复用的 Pydantic 校验逻辑和基于 Annotated 的校验类型。
"""

import re
from typing import Any, Annotated
from pydantic.functional_validators import AfterValidator

# --- 预编译正则表达式以提高性能 ---
_RESERVED_SUBDOMAINS = {'www', 'api', 'admin', 'app', 'mail', 'ftp', 'blog', 'shop'}
_SUBDOMAIN_REGEX = re.compile(r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$')
_EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$')
# 中国手机号校验正则表达式
_CHINA_MOBILE_REGEX = re.compile(r'^1[3-9]\d{9}$')
# 中国座机号校验正则表达式
_LANDLINE_REGEX = re.compile(r'^(\d{3,4})-?(\d{7,8})(?:-(\d{1,4}))?$')

def validate_china_mobile_or_landline(v: str) -> str:
    """
    联合校验中国手机号和座机号
    
    支持格式：
    手机号：13800138000
    座机号：010-12345678, 400-1234567, 800-1234567
    带分机：010-12345678-1234
    """
    if not isinstance(v, str):
        raise ValueError('电话号码必须是字符串类型')
    
    v = v.strip()
    
    if not v:
        raise ValueError('电话号码不能为空')
    
    # 尝试手机号校验
    if is_mobile_number(v):
        return validate_china_mobile(v)
    
    # 尝试座机号校验
    elif is_landline_number(v):
        return validate_china_landline(v)
    
    else:
        raise ValueError('请输入有效的手机号或座机号')

def is_mobile_number(v: str) -> bool:
    """判断是否为手机号格式"""
    # 清理格式
    cleaned = re.sub(r'[\s\-\(\)\+]', '', v)
    return len(cleaned) == 11 and cleaned.isdigit() and cleaned.startswith('1')

def is_landline_number(v: str) -> bool:
    """判断是否为座机号格式"""
    # 支持多种分隔符
    normalized = re.sub(r'[\s\-\(\)]', '-', v)
    match = _LANDLINE_REGEX.match(normalized)
    if not match:
        return False
    
    area_code, main_number, extension = match.groups()
    # 座机号区号必须以0开头
    return area_code.startswith('0')

def validate_china_landline(v: str) -> str:
    """校验中国座机号码格式"""
    v = v.strip()
    
    if not v:
        raise ValueError('座机号不能为空')
    
    # 支持多种分隔符
    v = re.sub(r'[\s\-\(\)]', '-', v)
    
    # 检查格式
    match = _LANDLINE_REGEX.match(v)
    if not match:
        raise ValueError('请输入有效的座机号码格式（如：010-12345678）')
    
    area_code, main_number, extension = match.groups()
    
    # 验证区号
    if not validate_area_code(area_code):
        raise ValueError(f'区号 "{area_code}" 格式不正确')
    
    # 验证主号码
    if not validate_main_number(main_number, area_code):
        raise ValueError(f'主号码 "{main_number}" 格式不正确')
    
    # 验证分机号（如果存在）
    if extension and not validate_extension(extension):
        raise ValueError(f'分机号 "{extension}" 格式不正确')
    
    return v

def validate_area_code(area_code: str) -> bool:
    """验证区号"""
    if len(area_code) == 3:
        # 3位区号：直辖市和特殊服务号码
        return area_code in ['010', '020', '021', '022', '023', '024', '025', '027', '028', '029', '400', '800']
    elif len(area_code) == 4:
        # 4位区号：其他城市
        return area_code.startswith('0') and area_code[1] in '3456789'
    return False

def validate_main_number(main_number: str, area_code: str) -> bool:
    """验证主号码"""
    if area_code in ['400', '800']:
        # 400/800电话：7位数字
        return len(main_number) == 7 and main_number.isdigit()
    else:
        # 普通座机：8位数字
        return len(main_number) == 8 and main_number.isdigit()

def validate_extension(extension: str) -> bool:
    """验证分机号"""
    return len(extension) <= 4 and extension.isdigit()

def validate_china_mobile(v: str) -> str:
    """
    校验中国手机号格式
    
    规则：
    - 11位数字
    - 以1开头
    - 第二位数字为3-9
    - 支持常见运营商号段
    """
    if not isinstance(v, str):
        raise ValueError('手机号必须是字符串类型')
    
    # 去除空格和特殊字符
    v = v.strip()
    
    # 去除常见的分隔符
    v = re.sub(r'[\s\-\(\)\+]', '', v)
    
    # 检查是否为空
    if not v:
        raise ValueError('手机号不能为空')
    
    # 检查长度
    if len(v) != 11:
        raise ValueError('手机号必须是11位数字')
    
    # 检查是否全为数字
    if not v.isdigit():
        raise ValueError('手机号只能包含数字')
    
    # 检查格式（1开头，第二位3-9）
    if not _CHINA_MOBILE_REGEX.match(v):
        raise ValueError('请输入有效的中国手机号（以1开头，第二位为3-9）')
    
    return v

# 优化建议
def validate_not_empty(v: str, field_name: str = "字段") -> str:
    v = v.strip()
    if not v:
        raise ValueError(f'{field_name} 不能为空')
    
    if len(v) > 1000:  # 防止过长的输入
        raise ValueError(f'{field_name} 长度不能超过1000个字符')
    
    return v

def validate_subdomain(v: str) -> str:
    """校验子域名格式和保留字"""
    v = validate_not_empty(v, '子域名')
    
    # 检查是否包含大写字母
    if any(c.isupper() for c in v):
        raise ValueError('子域名只能包含小写字母、数字和连字符')
    
    v = v.lower()
    
    # 添加长度检查
    if len(v) < 3:
        raise ValueError('子域名至少需要3个字符')
    if len(v) > 100:
        raise ValueError('子域名不能超过100个字符')

    if not _SUBDOMAIN_REGEX.match(v):
        raise ValueError('子域名只能包含小写字母、数字和连字符，且不能以连字符开头或结尾')
    
    if v in _RESERVED_SUBDOMAINS:
        raise ValueError(f'子域名 "{v}" 是保留字，不可使用')
        
    return v

def validate_email(v: str) -> str:
    """校验邮箱格式"""
    v = validate_not_empty(v, '邮箱地址').lower()
    
    if not _EMAIL_REGEX.match(v):
        raise ValueError('请输入有效的邮箱地址')
        
    return v

# --- 创建可复用的、自带校验的类型 (Annotated) ---

# 创建一个 EmailStr 类型，它本质是 str，但会自动使用 validate_email 函数进行校验
EmailStr = Annotated[str, AfterValidator(validate_email)]

# 创建一个 SubdomainStr 类型
SubdomainStr = Annotated[str, AfterValidator(validate_subdomain)]

# 创建一个 PhoneStr 类型(中国手机号)
PhoneStr = Annotated[str, AfterValidator(validate_china_mobile)]

# 创建一个 LandlineStr 类型(中国座机号)
LandlineStr = Annotated[str, AfterValidator(validate_china_landline)]

# 创建一个 PhoneOrLandlineStr 类型(中国手机号或座机号)
PhoneOrLandlineStr = Annotated[str, AfterValidator(validate_china_mobile_or_landline)]

# 创建一个 NotEmptyStr 类型
# 注意：这里 validate_not_empty 需要 field_name 参数，但 AfterValidator 只能接收一个参数
# 所以我们用 lambda 包装一下，或者为 NotEmptyStr 创建一个专门的单参数校验函数
# 为了简化，这里直接使用 lambda，实际项目中可以考虑更优雅的封装
NotEmptyStr = Annotated[str, AfterValidator(lambda v: validate_not_empty(v, '字段'))]
