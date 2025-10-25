# API v1 文档概览

> Base URL: `/api/v1`

## 系统
| Method | Path | 描述 | 认证 |
| --- | --- | --- | --- |
| GET | `/system/health` | 健康检查，返回 `{ "status": "ok" }` | 无 |

## 认证
| Method | Path | 描述 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| POST | `/auth/login` | 用户登录，发放 Access/Refresh Token | `AuthLoginRequest` | `AuthenticatedResponse`
| POST | `/auth/refresh` | 刷新 Access Token | `TokenRefreshRequest` | `AuthTokenPair`
| POST | `/auth/logout` | 登出并撤销 Refresh Token | `LogoutRequest` | `{detail}`
| POST | `/auth/activate` | 激活账号并设置密码 | `AccountActivationRequest` | `ActivationResponse`
| POST | `/auth/password/change` | 登录态修改密码 | `PasswordChangeRequest` | `{detail}`
| POST | `/auth/password/reset/request` | 发起密码重置 | `PasswordResetRequest` | `{detail}`
| POST | `/auth/password/reset/confirm` | 使用 token 重置密码 | `PasswordResetConfirm` | `{detail}`

## 租户入驻申请
| Method | Path | 描述 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| POST | `/tenant-applications` | 提交入驻申请 | `TenantApplicationSubmit` | `TenantApplicationRead`
| GET | `/tenant-applications` | 列出申请，支持 `status_filter`, `page`, `size` | query | `PaginatedResponse[TenantApplicationRead]`
| GET | `/tenant-applications/{id}` | 查看单个申请 | - | `TenantApplicationRead`
| POST | `/tenant-applications/{id}/review` | 审核申请（通过/拒绝） | `TenantApplicationReview` | `TenantApplicationRead`

## 租户管理
| Method | Path | 描述 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| POST | `/tenants` | 手动创建租户 | `TenantCreate` | `TenantRead`
| GET | `/tenants` | 分页查询租户，支持 `status_filter`, `search` | query | `PaginatedResponse[TenantRead]`
| GET | `/tenants/{tenant_id}` | 查看租户详情 | - | `TenantRead`
| PATCH | `/tenants/{tenant_id}` | 更新租户资料 | `TenantUpdate` | `TenantRead`
| POST | `/tenants/{tenant_id}/status` | 变更租户状态 | `TenantStatusUpdate` | `TenantRead`
| POST | `/tenants/{tenant_id}/plan` | 调整套餐及成员上限 | `TenantPlanUpdate` | `TenantRead`

## 租户成员
| Method | Path | 描述 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| POST | `/tenants/{tenant_id}/members` | 直接添加成员 | `TenantMemberCreate` | `TenantMemberRead`
| GET | `/tenants/{tenant_id}/members` | 列表成员，`status_filter`, `page`, `size` | query | `PaginatedResponse[TenantMemberRead]`
| PATCH | `/tenants/{tenant_id}/members/{member_id}` | 更新成员角色/状态 | `TenantMemberUpdate` | `TenantMemberRead`
| DELETE | `/tenants/{tenant_id}/members/{member_id}` | 移除成员（标记 REMOVED） | - | `TenantMemberRead`
| POST | `/tenants/{tenant_id}/invitations` | 发送邀请邮件 | `MemberInvitationCreate` | `MemberInvitationRead`
| GET | `/tenants/{tenant_id}/invitations` | 列出邀请，支持 `status_filter`, `page`, `size` | query | `PaginatedResponse[MemberInvitationRead]`
| POST | `/tenants/{tenant_id}/invitations/{token}/revoke` | 撤销邀请 | - | `MemberInvitationRead`
| POST | `/tenants/{tenant_id}/invitations/{token}/accept` | 受邀用户通过链接接受邀请（必要时设置密码） | `InvitationAcceptRequest` | `InvitationAcceptResponse`

## 订阅套餐
| Method | Path | 描述 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| POST | `/subscription-plans` | 创建套餐 | `SubscriptionPlanCreate` | `SubscriptionPlanRead`
| GET | `/subscription-plans` | 列出套餐，支持 `only_active`, `page`, `size` | query | `PaginatedResponse[SubscriptionPlanRead]`
| GET | `/subscription-plans/{plan_id}` | 查询套餐详情 | - | `SubscriptionPlanRead`
| PATCH | `/subscription-plans/{plan_id}` | 更新套餐配置 | `SubscriptionPlanUpdate` | `SubscriptionPlanRead`
| POST | `/subscription-plans/{plan_id}/toggle` | 启用/停用套餐 | query `is_active` | `SubscriptionPlanRead`

## 租户订阅
| Method | Path | 描述 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| POST | `/tenants/{tenant_id}/subscriptions` | 新建租户订阅（切换套餐/生效时间） | `TenantSubscriptionCreate` | `TenantSubscriptionRead`
| GET | `/tenants/{tenant_id}/subscriptions` | 列表订阅历史 | query | `PaginatedResponse[TenantSubscriptionRead]`
| GET | `/tenants/{tenant_id}/subscriptions/{subscription_id}` | 查看订阅详情 | - | `TenantSubscriptionRead`
| PATCH | `/tenants/{tenant_id}/subscriptions/{subscription_id}` | 更新订阅（状态/结束时间等） | `TenantSubscriptionUpdate` | `TenantSubscriptionRead`

## 订阅订单
| Method | Path | 描述 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| POST | `/subscription-orders` | 提交升级/续费订单 | `SubscriptionOrderCreate` | `SubscriptionOrderRead`
| GET | `/subscription-orders` | 列出订单，支持 `tenant_id`, `status_filter`, `page`, `size` | query | `PaginatedResponse[SubscriptionOrderRead]`
| GET | `/subscription-orders/{order_id}` | 查询订单详情 | - | `SubscriptionOrderRead`
| POST | `/subscription-orders/{order_id}/process` | 运营审核/标记支付，并触发订阅切换 | `SubscriptionOrderProcess` | `SubscriptionOrderRead`

## 通用说明
- 所有分页接口返回 `PaginatedResponse`，字段包含 `items`（数据列表）与 `meta`（`total`, `page`, `size`, `has_next`, `has_prev`）。
- 字段与枚举定义请参考 `app/schemas` 目录中的 Pydantic 模型。
- 目前未启用鉴权/RBAC，后续接入时可在路由依赖中添加认证与角色校验。
