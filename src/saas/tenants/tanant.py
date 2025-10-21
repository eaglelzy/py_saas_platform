# src/saas/tenants/models.py
"""
租户（Tenant）数据模型定义

租户是 SaaS 平台中的核心概念，代表一个独立的企业或组织。
每个租户都有自己独立的数据空间，实现多租户数据隔离。

在 SaaS 架构中：
- 租户是数据隔离的基本单位
- 每个租户拥有独立的用户、学生和其他业务数据
- 通过 tenant_id 外键实现数据的逻辑隔离
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

# 从核心模块导入基础类和 Mixin
from src.core.db import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """
    租户（Tenant）模型类
    
    租户代表 SaaS 平台中的一个独立企业或组织，是数据隔离的基本单位。
    每个租户拥有自己的用户、和其他业务数据。
    
    继承关系：
    - Base: SQLAlchemy 的基础类，提供 ORM 映射功能
    - TimestampMixin: 自动提供 created_at 和 updated_at 时间戳字段
    
    数据库表结构：
    - id: 主键，自增整数
    - company_name: 租户名称（公司或组织名称），必填
    - company_address: 公司地址，必填
    - company_phone: 公司电话，必填
    - company_email: 公司邮箱，必填
    - company_website: 公司网站，可选
    - company_logo: 公司Logo URL，可选
    - contact_person: 联系人姓名，必填
    - contact_phone: 联系人电话，必填
    - subdomain: 子域名，必填且唯一
    - is_active: 租户激活状态，默认True
    - is_deleted: 软删除标记，默认False
    - deleted_at: 软删除时间，可选
    - created_at: 创建时间（来自 TimestampMixin）
    - updated_at: 更新时间（来自 TimestampMixin）
    
    关系映射：
    - users: 该租户下的所有用户（顾问）
    
    使用示例：
    ```python
    # 创建新租户
    tenant = Tenant(
        company_name="ABC 教育公司",
        company_address="北京市朝阳区xxx街道",
        company_phone="010-12345678",
        company_email="contact@abc.com",
        contact_person="张三",
        contact_phone="13800138000",
        subdomain="abc-edu"
    )
    db.add(tenant)
    db.commit()
    
    # 查询租户及其关联数据
    tenant = db.query(Tenant).filter(Tenant.company_name == "ABC 教育公司").first()
    print(f"租户: {tenant.company_name}")
    print(f"用户数量: {tenant.get_user_count()}")
    print(f"子域名URL: {tenant.get_subdomain_url()}")
    ```
    """
    __tablename__ = "tenants"
    
    # 1. 主键字段（必须第一个）
    id = Column(Integer, primary_key=True, comment="租户唯一标识符，自增整数主键")
    
    # 2. 公司基本信息（核心业务字段）
    company_name = Column(
        String(100), 
        nullable=False, 
        comment="租户名称（公司或组织名称），必填字段，用于标识租户"
    )
    company_address = Column(
        String(255),
        nullable=False,
        comment="公司地址，必填字段，用于记录公司物理位置"
    )
    company_phone = Column(
        String(20),
        nullable=False,
        comment="公司电话，必填字段，用于联系公司"
    )
    company_email = Column(
        String(100),
        nullable=False,
        comment="公司邮箱，必填字段，用于官方邮件联系"
    )
    company_website = Column(
        String(255),
        nullable=True,
        comment="公司网站，可选字段，存储公司官网URL"
    )
    company_logo = Column(
        String(255),
        nullable=True,
        comment="公司Logo，可选字段，存储Logo图片URL"
    )

    # 3. 联系人信息（业务对接人员）
    contact_person = Column(
        String(20),
        nullable=False,
        comment="联系人姓名，必填字段，指定与租户对接的具体人员"
    )
    contact_phone = Column(
        String(20),
        nullable=False,
        comment="联系人电话，必填字段，用于直接联系对接人员"
    )

    # 4. 多租户配置（SaaS架构核心字段）
    subdomain = Column(
        String(100),
        nullable=False,
        unique=True,  # 添加唯一约束，确保子域名不重复
        comment="子域名，必填字段，用于多租户URL路由（如：abc.yoursaas.com）"
    )

    # 5. 状态字段（租户生命周期管理）
    is_active = Column(
        Boolean, 
        default=True,
        nullable=False,
        comment="租户激活状态，True=可用，False=停用，控制租户访问权限"
    )
    is_deleted = Column(
        Boolean, 
        default=False,
        nullable=False,
        comment="软删除标记，True=已删除，False=正常，实现数据安全删除"
    )
    
    # 6. 时间字段（TimestampMixin 会自动添加 created_at, updated_at）
    # 其他时间字段
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="软删除时间，记录租户被软删除的具体时间戳"
    )

    # 7. 表级索引（数据库性能优化）
    __table_args__ = (
        # 单列索引（提高单字段查询性能）
        Index('ix_tenants_company_name', 'company_name'),  # 租户名称查询
        Index('ix_tenants_subdomain', 'subdomain'),        # 子域名查询（唯一）
        Index('ix_tenants_is_active', 'is_active'),        # 激活状态查询
        Index('ix_tenants_is_deleted', 'is_deleted'),      # 删除状态查询
        Index('ix_tenants_created_at', 'created_at'),      # 创建时间排序
        
        # 复合索引（优化多字段组合查询）
        Index('ix_tenants_active_not_deleted', 'is_active', 'is_deleted'),  # 可用租户查询
        Index('ix_tenants_name_active', 'company_name', 'is_active'),        # 名称+状态查询
        Index('ix_tenants_subdomain_active', 'subdomain', 'is_active'),      # 子域名+状态查询
        
        # 表注释
        {'comment': '租户表 - 支持多租户数据隔离，SaaS架构核心表'}
    )

    # 8. 关系映射（ORM关联关系配置）
    # 一个租户拥有多个用户（顾问）
    users = relationship(
        "User", 
        back_populates="tenant",  # 双向关系映射，User.tenant <-> Tenant.users
        cascade="all, delete-orphan",  # 级联操作：删除租户时自动删除所有关联用户
        lazy="dynamic"  # 延迟加载：返回查询对象而非列表，支持分页和过滤
    )
    
    
    def __repr__(self):
        """调试用字符串表示，用于日志和调试输出"""
        return f"<Tenant(id={self.id}, company_name='{self.company_name}')>"
    
    def __str__(self):
        """用户友好字符串表示，用于前端显示"""
        return self.company_name
    
    # =============================================================================
    # 状态管理方法（租户生命周期管理）
    # =============================================================================
    
    def activate(self):
        """激活租户，允许租户正常使用系统"""
        self.is_active = True
    
    def deactivate(self):
        """停用租户，禁止租户访问系统"""
        self.is_active = False
    
    def soft_delete(self):
        """软删除租户，标记删除但不物理删除数据"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self):
        """恢复软删除的租户，重新激活租户"""
        self.is_deleted = False
        self.deleted_at = None
    
    def is_available(self):
        """检查租户是否可用（激活且未删除），用于权限验证"""
        return self.is_active and not self.is_deleted
    
    def get_status_display(self):
        """获取租户状态的中文显示名称，用于前端展示"""
        if self.is_deleted:
            return "已删除"
        elif not self.is_active:
            return "已停用"
        else:
            return "正常"
    
    def get_deleted_display(self):
        """获取删除时间的格式化显示，用于前端展示"""
        if self.deleted_at:
            return self.deleted_at.strftime("%Y-%m-%d %H:%M:%S")
        return "未删除"
    
    # =============================================================================
    # 业务逻辑方法（扩展功能）
    # =============================================================================
    
    def get_user_count(self):
        """获取租户下的活跃用户数量"""
        return self.users.filter_by(is_deleted=False).count()
    
    def can_add_user(self, max_users=None):
        """检查是否可以添加新用户（基于配额限制）"""
        if max_users is None:
            return True  # 无限制
        return self.get_user_count() < max_users
    
    def get_subdomain_url(self, base_domain="yoursaas.com"):
        """获取租户的完整子域名URL"""
        if self.subdomain:
            return f"https://{self.subdomain}.{base_domain}"
        return None
    
    def is_subdomain_available(self, subdomain):
        """检查子域名是否可用（用于验证）"""
        # 这个方法需要在实际使用时结合数据库查询
        return subdomain and len(subdomain) >= 3
    
    def get_contact_info(self):
        """获取完整的联系信息字典"""
        return {
            "company_name": self.company_name,
            "company_phone": self.company_phone,
            "company_email": self.company_email,
            "company_address": self.company_address,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone
        }