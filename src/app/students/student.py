# src/app/students/student.py
"""
学生（Student）数据模型定义

学生是 SaaS 教育平台中的核心业务实体，代表接受教育服务的客户。
每个学生都属于特定的租户，并由指定的顾问（用户）负责跟进。

在 SaaS 多租户架构中：
- 学生是业务数据的基本单位
- 通过 tenant_id 实现租户数据隔离
- 通过 user_id 建立学生与顾问的关联关系
- 支持中英文双语姓名存储
"""

import enum
from datetime import date
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import SQLAlchemyEnum

# 从核心模块导入基础类和 Mixin
from src.core.db import Base, TimestampMixin


class StudentStatus(str, enum.Enum):
    """
    学生状态枚举类
    
    定义学生在系统中的状态，用于业务逻辑控制和数据管理。
    
    状态说明：
    - ACTIVE: 活跃状态，学生正在接受服务
    - ARCHIVED: 归档状态，学生已停止服务或毕业
    
    使用示例：
    ```python
    # 创建学生时默认状态为活跃
    student = Student(first_name_zh="张三", ...)
    print(student.status)  # StudentStatus.ACTIVE
    
    # 修改学生状态
    student.status = StudentStatus.ARCHIVED
    ```
    """
    ACTIVE = "active"      # 活跃状态：学生正在接受服务
    ARCHIVED = "archived"  # 归档状态：学生已停止服务或毕业


class Student(Base, TimestampMixin):
    """
    学生（Student）模型类
    
    学生是教育 SaaS 平台中的核心业务实体，代表接受教育服务的客户。
    每个学生都属于特定的租户，并由指定的顾问负责跟进。
    
    继承关系：
    - Base: SQLAlchemy 的基础类，提供 ORM 映射功能
    - TimestampMixin: 自动提供 created_at 和 updated_at 时间戳字段
    
    数据库表结构：
    - id: 主键，自增整数
    - first_name_zh: 中文名字
    - last_name_zh: 中文姓氏
    - first_name_en: 英文名字
    - last_name_en: 英文姓氏
    - email: 电子邮箱
    - phone: 电话号码
    - date_of_birth: 出生日期
    - status: 学生状态（活跃/归档）
    - tenant_id: 所属租户ID（外键）
    - user_id: 负责顾问ID（外键）
    - created_at: 创建时间（来自 TimestampMixin）
    - updated_at: 更新时间（来自 TimestampMixin）
    
    关系映射：
    - tenant: 所属租户（多对一关系）
    - user: 负责顾问（多对一关系）
    
    使用示例：
    ```python
    # 创建新学生
    student = Student(
        first_name_zh="张三",
        last_name_zh="张",
        first_name_en="San",
        last_name_en="Zhang",
        email="zhangsan@example.com",
        phone="13800138000",
        date_of_birth=date(2000, 1, 1),
        tenant_id=1,
        user_id=1
    )
    db.add(student)
    db.commit()
    
    # 查询学生及其关联数据
    student = db.query(Student).filter(Student.email == "zhangsan@example.com").first()
    print(f"学生: {student.first_name_zh} {student.last_name_zh}")
    print(f"所属租户: {student.tenant.name}")
    print(f"负责顾问: {student.user.name}")
    ```
    """
    __tablename__ = "students"
    
    # 主键字段
    id = Column(Integer, primary_key=True, comment="学生唯一标识符")
    
    # 中文姓名字段
    first_name_zh = Column(
        String(10), 
        nullable=False, 
        comment="中文名字"
    )
    last_name_zh = Column(
        String(10), 
        nullable=False, 
        comment="中文姓氏"
    )
    
    # 英文姓名字段
    first_name_en = Column(
        String(50), 
        nullable=False, 
        comment="英文名字"
    )
    last_name_en = Column(
        String(50), 
        nullable=False, 
        comment="英文姓氏"
    )
    
    # 联系信息字段
    email = Column(
        String(100), 
        nullable=False, 
        comment="电子邮箱地址"
    )
    phone = Column(
        String(100), 
        nullable=False, 
        comment="电话号码"
    )
    
    # 个人信息字段
    date_of_birth = Column(
        Date, 
        nullable=False, 
        comment="出生日期"
    )
    
    # 状态字段
    status = Column(
        SQLAlchemyEnum(StudentStatus, name="student_status_enum", native_enum=False),
        nullable=False,
        default=StudentStatus.ACTIVE,
        comment="学生状态（活跃/归档）",
    )
    
    # 外键关系字段
    # 租户关系：学生属于某个租户
    tenant_id = Column(
        Integer, 
        ForeignKey("tenants.id"), 
        nullable=False,
        comment="所属租户ID"
    )
    tenant = relationship(
        "Tenant", 
        back_populates="students",
        comment="所属租户"
    )

    # 顾问关系：学生由某个顾问负责
    user_id = Column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False,
        comment="负责顾问ID"
    )
    user = relationship(
        "User", 
        back_populates="students",
        comment="负责顾问"
    )
    
    def __repr__(self):
        """
        返回对象的"官方"字符串表示，主要用于调试和开发
        
        Returns:
            str: 格式化的学生技术描述字符串
        """
        return f"<Student(id={self.id}, name='{self.first_name_zh} {self.last_name_zh}', email='{self.email}')>"
    
    def __str__(self):
        """
        返回对象的"用户友好"字符串表示，主要用于最终用户显示
        
        Returns:
            str: 学生中文姓名（用户友好的表示）
        """
        return f"{self.first_name_zh} {self.last_name_zh}"
    
    @property
    def full_name_zh(self):
        """
        获取学生的完整中文姓名
        
        Returns:
            str: 完整的中文姓名
        """
        return f"{self.last_name_zh}{self.first_name_zh}"
    
    @property
    def full_name_en(self):
        """
        获取学生的完整英文姓名
        
        Returns:
            str: 完整的英文姓名
        """
        return f"{self.first_name_en} {self.last_name_en}"
    
    @property
    def age(self):
        """
        计算学生年龄
        
        Returns:
            int: 学生年龄
        """
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def is_active(self):
        """
        检查学生是否为活跃状态
        
        Returns:
            bool: 如果学生状态为活跃则返回 True，否则返回 False
        """
        return self.status == StudentStatus.ACTIVE
    
    def archive(self):
        """
        归档学生（将状态设置为归档）
        
        这个方法提供了一个业务层面的操作接口，
        使得状态变更更加语义化和易于理解。
        """
        self.status = StudentStatus.ARCHIVED
    
    def activate(self):
        """
        激活学生（将状态设置为活跃）
        
        这个方法提供了一个业务层面的操作接口，
        使得状态变更更加语义化和易于理解。
        """
        self.status = StudentStatus.ACTIVE