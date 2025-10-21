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
    每个租户拥有自己的用户、学生和其他业务数据。
    
    继承关系：
    - Base: SQLAlchemy 的基础类，提供 ORM 映射功能
    - TimestampMixin: 自动提供 created_at 和 updated_at 时间戳字段
    
    数据库表结构：
    - id: 主键，自增整数
    - name: 租户名称（公司或组织名称）
    - created_at: 创建时间（来自 TimestampMixin）
    - updated_at: 更新时间（来自 TimestampMixin）
    
    关系映射：
    - users: 该租户下的所有用户（顾问）
    - students: 该租户下的所有学生（客户）
    
    使用示例：
    ```python
    # 创建新租户
    tenant = Tenant(name="ABC 教育公司")
    db.add(tenant)
    db.commit()
    
    # 查询租户及其关联数据
    tenant = db.query(Tenant).filter(Tenant.name == "ABC 教育公司").first()
    print(f"租户: {tenant.name}")
    print(f"用户数量: {len(tenant.users)}")
    print(f"学生数量: {len(tenant.students)}")
    ```
    """
    __tablename__ = "tenants"
    
    # 1. 主键字段（必须第一个）
    id = Column(Integer, primary_key=True, comment="租户唯一标识符")
    
    # 2. 业务标识字段（最常用的查询字段）
    name = Column(
        String(100), 
        nullable=False, 
        comment="租户名称（公司或组织名称）"
    )
    
    # 3. 状态字段（按查询频率排序）
    is_active = Column(
        Boolean, 
        default=True,
        nullable=False,
        comment="租户是否激活"
    )
    
    is_deleted = Column(
        Boolean, 
        default=False,
        nullable=False,
        comment="是否已删除（软删除）"
    )
    
    # 4. 时间字段（TimestampMixin 会自动添加 created_at, updated_at）
    # 其他时间字段
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="删除时间"
    )

    # 5. 表级索引（性能优化）
    __table_args__ = (
        # 单列索引
        Index('ix_tenants_name', 'name'),
        Index('ix_tenants_is_active', 'is_active'),
        Index('ix_tenants_is_deleted', 'is_deleted'),
        Index('ix_tenants_created_at', 'created_at'),
        
        # 复合索引（常用查询组合）
        Index('ix_tenants_active_not_deleted', 'is_active', 'is_deleted'),
        Index('ix_tenants_name_active', 'name', 'is_active'),
        
        # 表注释
        {'comment': '租户表 - 支持多租户数据隔离'}
    )

    # 6. 关系映射
    # 一个租户拥有多个用户（顾问）
    users = relationship(
        "User", 
        # back_populates: 建立双向关系映射
        # - 在 Tenant 模型中，users 指向该租户的所有用户
        # - 在 User 模型中，tenant 指向该用户所属的租户
        # - 当修改任一端的对象时，另一端会自动同步更新
        # - 例如：user.tenant = new_tenant 会自动更新 tenant.users 列表
        back_populates="tenant", 
        
        # cascade: 级联操作设置
        # "all" 表示所有操作都会级联到关联对象
        # - save-update: 保存租户时，自动保存关联的用户
        # - merge: 合并租户时，自动合并关联的用户
        # - expunge: 从会话中移除租户时，自动移除关联的用户
        # - refresh: 刷新租户时，自动刷新关联的用户
        # - delete: 删除租户时，自动删除关联的用户
        # "delete-orphan": 删除孤儿记录
        # - 当用户与租户的关系被移除时（user.tenant = None），自动删除该用户
        # - 这确保不会有"无主"的用户记录存在
        cascade="all, delete-orphan",
        
        # lazy: 延迟加载策略
        # "dynamic": 返回一个查询对象而不是实际的用户列表
        # - 优点：可以进一步过滤和分页，性能更好
        # - 用法：tenant.users.filter(User.is_active == True).all()
        lazy="dynamic"
    )
    
    # 一个租户拥有多个学生（客户）
    # 注意：Student 模型尚未创建，暂时注释掉此关系
    # students = relationship(
    #     "Student", 
    #     # back_populates: 建立双向关系映射
    #     # - 在 Tenant 模型中，students 指向该租户的所有学生
    #     # - 在 Student 模型中，tenant 指向该学生所属的租户
    #     # - 双向关系确保数据一致性，避免关系断裂
    #     back_populates="tenant", 
    #     
    #     # cascade: 级联操作设置
    #     # 当租户被删除时，所有关联的学生记录也会被删除
    #     # 这确保了数据完整性，避免出现"孤儿"学生记录
    #     # 在实际业务中，可能需要考虑软删除或数据迁移策略
    #     cascade="all, delete-orphan",
    #     
    #     # lazy: 延迟加载策略
    #     # 使用动态加载避免在查询租户时立即加载所有学生数据
    #     # 这对于有大量学生的租户来说非常重要
    #     lazy="dynamic"
    # )
    
    def __repr__(self):
        """
        返回对象的字符串表示，用于调试和日志记录
        
        Returns:
            str: 格式化的租户信息字符串
        """
        return f"<Tenant(id={self.id}, name='{self.name}')>"
    
    def __str__(self):
        """
        返回对象的用户友好字符串表示
        
        Returns:
            str: 租户名称
        """
        return self.name
    
    # =============================================================================
    # 状态管理方法
    # =============================================================================
    
    def activate(self):
        """
        激活租户
        
        将租户状态设置为激活，租户可以正常使用系统。
        """
        self.is_active = True
    
    def deactivate(self):
        """
        停用租户
        
        将租户状态设置为非激活，租户无法使用系统。
        """
        self.is_active = False
    
    def soft_delete(self):
        """
        软删除租户
        
        标记租户为已删除，但不从数据库中物理删除。
        软删除的租户不会在正常查询中显示。
        """
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self):
        """
        恢复软删除的租户
        
        取消软删除标记，租户重新可见。
        """
        self.is_deleted = False
        self.deleted_at = None
    
    def is_available(self):
        """
        检查租户是否可用
        
        租户可用需要同时满足：
        1. 已激活 (is_active = True)
        2. 未删除 (is_deleted = False)
        
        Returns:
            bool: 租户可用返回 True，否则返回 False
        """
        return self.is_active and not self.is_deleted
    
    def get_status_display(self):
        """
        获取租户状态的中文显示名称
        
        Returns:
            str: 状态的中文显示名称
        """
        if self.is_deleted:
            return "已删除"
        elif not self.is_active:
            return "已停用"
        else:
            return "正常"
    
    def get_deleted_display(self):
        """
        获取删除时间的中文显示格式
        
        Returns:
            str: 格式化的删除时间字符串
        """
        if self.deleted_at:
            return self.deleted_at.strftime("%Y-%m-%d %H:%M:%S")
        return "未删除"