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

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

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
    
    # 主键字段
    id = Column(Integer, primary_key=True, comment="租户唯一标识符")
    
    # 租户基本信息
    name = Column(
        String(100), 
        nullable=False, 
        comment="租户名称（公司或组织名称）"
    )

    # 关系映射
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
    students = relationship(
        "Student", 
        # back_populates: 建立双向关系映射
        # - 在 Tenant 模型中，students 指向该租户的所有学生
        # - 在 Student 模型中，tenant 指向该学生所属的租户
        # - 双向关系确保数据一致性，避免关系断裂
        back_populates="tenant", 
        
        # cascade: 级联操作设置
        # 当租户被删除时，所有关联的学生记录也会被删除
        # 这确保了数据完整性，避免出现"孤儿"学生记录
        # 在实际业务中，可能需要考虑软删除或数据迁移策略
        cascade="all, delete-orphan",
        
        # lazy: 延迟加载策略
        # 使用动态加载避免在查询租户时立即加载所有学生数据
        # 这对于有大量学生的租户来说非常重要
        lazy="dynamic"
    )
    
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