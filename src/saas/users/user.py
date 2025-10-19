# src/saas/users/user.py
"""
用户（User）数据模型定义

用户是 SaaS 平台中的核心实体，代表系统中的顾问或管理员。
每个用户都属于特定的租户，负责管理该租户下的学生。

在 SaaS 多租户架构中：
- 用户是系统访问的主体
- 通过 tenant_id 实现租户数据隔离
- 通过 is_superuser 标志区分普通用户和管理员
- 用户可以管理多个学生
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

# 从核心模块导入基础类和 Mixin
from src.core.db import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    用户（User）模型类
    
    用户是 SaaS 平台中的核心实体，代表系统中的顾问或管理员。
    每个用户都属于特定的租户，负责管理该租户下的学生。
    
    继承关系：
    - Base: SQLAlchemy 的基础类，提供 ORM 映射功能
    - TimestampMixin: 自动提供 created_at 和 updated_at 时间戳字段
    
    数据库表结构：
    - id: 主键，自增整数
    - name: 用户姓名
    - email: 电子邮箱（唯一）
    - password: 加密后的密码
    - is_active: 账户是否激活
    - is_superuser: 是否为超级用户（跨租户权限）
    - last_login: 最后登录时间
    - tenant_id: 所属租户ID（外键）
    - created_at: 创建时间（来自 TimestampMixin）
    - updated_at: 更新时间（来自 TimestampMixin）
    
    关系映射：
    - tenant: 所属租户（多对一关系）
    - assigned_students: 负责的学生（一对多关系）
    
    使用示例：
    ```python
    # 创建新用户
    user = User(
        name="张三",
        email="zhangsan@example.com",
        password="hashed_password",
        tenant_id=1
    )
    db.add(user)
    db.commit()
    
    # 查询用户及其关联数据
    user = db.query(User).filter(User.email == "zhangsan@example.com").first()
    print(f"用户: {user.name}")
    print(f"所属租户: {user.tenant.name}")
    print(f"负责学生数量: {user.assigned_students.count()}")
    
    # 检查用户权限
    if user.has_superuser_privileges():
        print("用户拥有超级用户权限")
    
    # 更新登录时间
    user.update_last_login()
    db.commit()
    print(f"最后登录时间: {user.get_last_login_display()}")
    
    # 检查登录状态
    if user.has_never_logged_in():
        print("用户从未登录过")
    else:
        days = user.get_days_since_last_login()
        print(f"距离上次登录已过去 {days} 天")
    ```
    """
    __tablename__ = "users"
    
    # 主键字段
    id = Column(Integer, primary_key=True, comment="用户唯一标识符", index=True)
    
    # 基本信息字段
    name = Column(
        String(100), 
        nullable=False, 
        comment="用户姓名"
    )
    email = Column(
        String(100), 
        nullable=False, 
        unique=True,  # 邮箱地址必须唯一
        comment="电子邮箱地址（唯一）",
        index=True
    )
    password = Column(
        String(255),  # 增加长度以支持哈希密码
        nullable=False, 
        comment="加密后的密码"
    )
    is_active = Column(
        Boolean, 
        default=True,
        nullable=False,
        comment="账户是否激活"
    )
    is_superuser = Column(
        Boolean, 
        default=False,
        nullable=False,
        comment="是否为超级用户（跨租户权限）"
    )
    
    # 登录信息字段
    last_login = Column(
        DateTime,
        nullable=True,
        comment="最后登录时间"
    )
    
    # 外键关系字段
    # 租户关系：用户属于某个租户
    tenant_id = Column(
        Integer, 
        ForeignKey("tenants.id"), 
        nullable=False,
        comment="所属租户ID"
    )
    tenant = relationship(
        "Tenant", 
        back_populates="users",
        comment="所属租户"
    )
    
    # 学生关系：用户负责管理多个学生
    assigned_students = relationship(
        "Student", 
        back_populates="user",
        lazy="dynamic",  # 使用动态加载，避免一次性加载所有学生
        comment="负责的学生"
    )
    
    def __repr__(self):
        """
        返回对象的"官方"字符串表示，主要用于调试和开发
        
        Returns:
            str: 格式化的用户技术描述字符串
        """
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', is_active='{self.is_active}', is_superuser='{self.is_superuser}', last_login='{self.last_login}')>"
    
    def __str__(self):
        """
        返回对象的"用户友好"字符串表示，主要用于最终用户显示
        
        Returns:
            str: 用户姓名（用户友好的表示）
        """
        return self.name
    
    # =============================================================================
    # 权限检查方法
    # =============================================================================
    
    def is_admin(self):
        """
        检查用户是否为管理员
        
        在简化后的模型中，管理员通过 is_superuser 标志来识别。
        
        Returns:
            bool: 如果用户是超级用户则返回 True，否则返回 False
        """
        return self.is_superuser
   
    def has_superuser_privileges(self):
        """
        检查用户是否拥有超级用户权限
        
        超级用户可以跨租户访问数据，拥有系统级权限。
        
        Returns:
            bool: 如果用户是超级用户则返回 True，否则返回 False
        """
        return self.is_superuser
    
    # =============================================================================
    # 业务操作方法
    # =============================================================================
    
    def activate(self):
        """
        激活用户账户
        
        将用户状态设置为激活，用户可以正常登录和使用系统。
        """
        self.is_active = True
    
    def deactivate(self):
        """
        停用用户账户
        
        将用户状态设置为非激活，用户无法登录系统。
        """
        self.is_active = False
    
    def update_last_login(self):
        """
        更新最后登录时间
        
        在用户成功登录时调用此方法，记录当前时间作为最后登录时间。
        """
        self.last_login = datetime.utcnow()
    
    def get_last_login_display(self):
        """
        获取最后登录时间的中文显示格式
        
        Returns:
            str: 格式化的最后登录时间字符串
        """
        if self.last_login:
            return self.last_login.strftime("%Y-%m-%d %H:%M:%S")
        return "从未登录"
    
    def has_never_logged_in(self):
        """
        检查用户是否从未登录过
        
        Returns:
            bool: 如果用户从未登录过则返回 True，否则返回 False
        """
        return self.last_login is None
    
    def get_days_since_last_login(self):
        """
        获取距离上次登录的天数
        
        Returns:
            int: 距离上次登录的天数，如果从未登录则返回 None
        """
        if self.last_login:
            delta = datetime.utcnow() - self.last_login
            return delta.days
        return None
    
    # 统计和查询方法
    # =============================================================================
    
    def get_student_count(self):
        """
        获取用户负责的学生数量
        
        Returns:
            int: 负责的学生总数
        """
        return self.assigned_students.count()
    
    def get_active_student_count(self):
        """
        获取用户负责的活跃学生数量
        
        Returns:
            int: 负责的活跃学生数量
        """
        return self.assigned_students.filter_by(status="active").count()
    
    def get_recent_students(self, limit=5):
        """
        获取用户最近负责的学生
        
        Args:
            limit (int): 返回的学生数量限制
            
        Returns:
            list: 最近的学生列表
        """
        return self.assigned_students.order_by(
            self.assigned_students.property.mapper.class_.created_at.desc()
        ).limit(limit).all()
   
    def get_status_display(self):
        """
        获取用户状态的中文显示名称
        
        Returns:
            str: 状态的中文显示名称
        """
        return "激活" if self.is_active else "停用"
    
    def to_dict(self):
        """
        将用户对象转换为字典格式
        
        用于 API 响应或数据序列化。
        
        Returns:
            dict: 包含用户信息的字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "is_active": self.is_active,
            "status_display": self.get_status_display(),
            "is_superuser": self.is_superuser,
            "is_admin": self.is_admin(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "tenant_id": self.tenant_id,
            "student_count": self.get_student_count(),
            "active_student_count": self.get_active_student_count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }