# 架构决策文档 (Architecture Decision Record - ADR)

本文档记录了本项目在演进过程中的关键架构决策。

---

## 1. 核心架构：分层“即插即用”模式

**决策**: 保持不变。我们将继续采用`src`目录下`saas/`, `app/`, `ai/`的分层结构，以实现平台与应用的分离，保证未来的可扩展性。

---

## 2. 产品愿景：面向留学中介的智能SaaS工作台 (B2B)

**产品定位**: 本产品是一个企业级(B2B)SaaS平台，旨在为留学中介公司提供一套完整的、智能化的客户（学生）申请管理工作台。

**用户画像**:
- **租户 (Tenant)**: 一个留学中介公司。
- **用户 (User)**: 中介公司内的顾问/申请员。
- **核心业务对象**: 顾问所服务的客户，即“学生 (Student)”。

**核心价值**: 赋能顾问，使其能高效管理多个学生的申请流程，并通过AI辅助功能提升服务质量和申请成功率。

**分阶段路线图**:
1.  **第一阶段：多租户CRM骨架 (MVP)**: 实现以“中介公司”为单位的租户隔离。顾问可以登录自己的工作台，创建和管理名下的学生档案，并为每个学生追踪多所学校的申请状态。
2.  **第二阶段：注入智能**: 为**顾问**提供AI辅助工具。例如：根据学生情况智能推荐学校、一键检查申请材料是否齐全、文书版本管理与优化建议。
3.  **第三阶段：协同与管理**: 增加“管理员”角色（如中介老板），可以查看公司内所有学生和顾问的进度，分配学生给不同顾问，并查看统计报告。
4.  **第四阶段：商业化**: 基于“租户”（中介公司）进行收费，主要按“席位”（顾问数量）或“活跃学生数量”来设计订阅套餐。

---

## 3. 核心数据模型：多租户与顾问-学生（一对多）关系

这是本次架构更新的核心。数据模型必须反映真实世界的业务关系。

**关系总览**:
- 一个**租户(Tenant)** 拥有多个**顾问(User)**。
- 一个**租户(Tenant)** 也拥有多个**学生(Student)**。
- 一个**顾问(User)** 被指派跟进多个**学生(Student)** (一对多关系)。

**`saas/tenants/models.py` 中的 `Tenant` 模型**:
```python
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # ...其他公司信息

    users = relationship("User", back_populates="tenant")
    students = relationship("Student", back_populates="tenant")
```

**`saas/users/models.py` 中的 `User` (顾问) 模型**:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    # ...其他字段

    # 关键：顾问必须属于一个租户
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", back_populates="users")

    # 关键：一个顾问可以管理多个学生
    assigned_students = relationship("Student", back_populates="agent")
```

**`app/students/models.py` 中的 `Student` (客户) 模型**:
```python
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    # ...学生档案信息

    # 关键：学生档案必须属于一个租户，实现数据隔离
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", back_populates="students")

    # 关键：学生被指派给一个顾问
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent = relationship("User", back_populates="assigned_students")
```

---

## 4. (保留) SQLAlchemy 集成最佳实践

*(此处保留 `GEMINI.md` 中原有的关于 SQLAlchemy `engine`, `SessionLocal`, `Base` 和 `get_db` 的说明。)*
