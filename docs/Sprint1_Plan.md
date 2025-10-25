# Sprint 1 单兵作战计划

**周期**：第 1–2 周  
**个人目标**：在一人团队条件下，用最短路径交付租户入驻、成员邀请、基础 RBAC、审计日志雏形和前端可演示骨架，确保端到端打通一条最小可用流程。

---

## 里程碑与优先级
1. **核心链路打通（优先级 P0）**  
   租户申请 → 平台审核 → `owner` 登录 → 邀请成员 → 审计记录可查。
2. **安全与多租户基线（P1）**  
   JWT 登录/刷新、Redis 黑名单、RLS 会话上下文、成员上限校验。
3. **可演示界面与自动化（P2）**  
   Vue 前端骨架、表单交互、GitHub Actions 和 Docker Compose 雏形。

Stretch（若提前完成）：RabbitMQ 占位、告警/监控模板、Storybook。

---

## 时间安排概览
| 周次 | 时间段 | 目标 | 关键输出 |
| --- | --- | --- | --- |
| 第 1 周（天 1-3） | 架构与后端基础 | 数据库建模、Alembic 初始化、Auth/RLS 中间件 | `users/tenants/audit` 模型与迁移、JWT 工具、`/auth/*`、`/health` |
| 第 1 周（天 4-7） | 租户入驻链路 | 申请/审核 API、租户创建、审计记录、站内通知占位 | `POST /tenants/applications`、`PATCH /admin/tenant-applications/{id}`、审计写入 |
| 第 2 周（天 8-10） | 成员与邀请 | 成员模型、邀请 Token、套餐上限校验 | `POST /members/invitations`、`POST /invitations/{token}/accept`、Redis token 管理 |
| 第 2 周（天 11-12） | 前端框架 & Demo | Vue 工程初始化、登录/申请/审核界面雏形、API SDK | 前端仓库结构、基础路由、登录+申请+审核页面、统一主题 |
| 第 2 周（天 13-14） | 测试与收尾 | Pytest 覆盖、集成演示、文档整理 | 单元/集成测试、操作手册、Demo 脚本 |

---

## 工作项明细（按执行顺序）

### 阶段一：环境与后端基线
1. **数据库与迁移**
   - 初始化 Alembic；编写 `users`, `tenants`, `tenant_applications`, `audit_logs` 基础迁移。
   - 创建 `tenant_members`, `member_invitations`, `user_tenants` 迁移（可随阶段推进补充）。
2. **认证模块**
   - 实现 `POST /api/v1/auth/login|logout|refresh|tenants`。
   - 封装 JWT 工具、密码校验、Redis 黑名单；完成退出/刷新逻辑测试。
3. **多租户上下文**
   - 中间件注入 `tenant_id`，执行 `SET app.current_tenant`。
   - 预留 RLS 策略 SQL（可先在迁移中占位）。

### 阶段二：租户入驻端到端
1. **租户申请 API**
   - `POST /api/v1/tenants/applications` 校验并保存申请记录，状态默认为 `pending`。
   - 触发审计记录（事件类型 `TENANT_APPLY`），异步通知占位（写入队列待发送或落日志）。
2. **审核 API**
   - `GET /api/v1/admin/tenant-applications` 支持分页、状态筛选。
   - `PATCH /api/v1/admin/tenant-applications/{id}` 将申请标记为通过/拒绝；通过时创建租户、初始化 `owner` 用户、绑定套餐。
   - 写入审计（`TENANT_APPROVED`/`TENANT_REJECTED`）。
3. **测试/文档**
   - Pytest：申请成功、字段缺失、审核权限、重复审批。
   - 更新 Docs：入驻流程、API 参数、状态流转。

### 阶段三：成员邀请与 RBAC 验证
1. **成员模型与服务**
   - `tenant_members`, `member_invitations`, `role_assignments`（如需）。
   - 服务层校验成员数量不超 `plan.member_limit`（默认免费 5 人）。
2. **邀请流程**
   - `POST /api/v1/tenants/{tenant_id}/members/invitations` 创建邀请，生成 token 存 Redis（含 TTL、手动失效）。
   - `POST /api/v1/invitations/{token}/accept` 完成账号创建/绑定，写审计。
3. **RBAC/中间件补充**
   - 权限表及校验装饰器；缓存 15 分钟。
   - 测试涵盖邀请超限、重复邀请、token 过期。

### 阶段四：前端骨架 & Demo
1. **工程搭建**
   - Vite + Vue3 + TS + Pinia + Vue Router；配置 ESLint/Prettier/Commitlint。
   - Axios SDK 封装、鉴权拦截器（存储 Access/Refresh Token）。
2. **界面雏形**
   - 登录页、租户申请页、平台审核列表与详情。
   - 成员列表与邀请对话框占位（可先展示数据/表单写入）。
3. **样式与文档**
   - 统一主题（Tailwind/Element Plus 选型后集成）。
   - README/Docs 更新：前端开发指南、脚本说明。

### 阶段五：测试、Demo、自动化
1. **后端测试**：构建核心流程 Pytest，使用 `client`/`db` fixtures。
2. **前端测试**：配置 Vitest（单测）与 Cypress 占位（可延后真实用例）。
3. **CI/CD**：GitHub Actions 工作流草稿（后端测试、前端 Lint/Test、Docker Build）。
4. **Docker Compose**：整合 FastAPI、Postgres、Redis、RabbitMQ（可占位）、Mailhog，确保本地一键演示。
5. **Demo 脚本**：记录从注册到邀请的演示步骤，用于每周同步。

---

## 每日例行
- **开始前**：回顾燃尽与阻塞项，更新 TODO（建议用 Kanban 工具或 Markdown 清单）。
- **收工前**：运行快速测试（后端 Pytest、前端 Lint）、同步审计日志与 API 文档。
- **周末收尾**：录制 5 分钟 Demo，更新 `CHANGELOG`（如有）、整理下周优先事项。

---

## 风险与应对（单人视角）
- **任务堆叠风险**：严格按顺序推进，避免同时开发前后端；后端接口稳定后再补前端。
- **测试压力**：先编写最小可运行测试，避免临近截止堆积；使用工厂/fixture 降低重复。
- **上下游缺失**：RabbitMQ/邮件可先记录日志替代，确保主链路可演示；待后续 Sprint 再补。
- **时间溢出**：若 P1 项未完成，优先保障租户申请→邀请闭环，前端可降低细节（先用表单 + 简单表格）。

---

> 该计划假设每日可投入 6–8 小时开发时间。若出现大规模不可控因素（例如基础设施不可用），优先保证核心链路 P0，其他事项顺延到 Sprint 1.5 或 Sprint 2。
