# 服务层概览

本目录概述核心领域服务及其职责，帮助快速理解调用方式。

## 租户领域
- `TenantService`：租户 CRUD、状态与套餐调整。
- `TenantApplicationService`：入驻申请提交、列表、审核。
  - 审核通过时自动创建租户（默认免费套餐），并触发通知占位。

## 成员领域
- `TenantMemberService`：成员增删改查、配额校验。
- `MemberInvitationService`：邀请创建、撤销、接受以及配额管控。
  - 新用户会在邀请阶段自动建号并发送激活链接，接受时可设置密码。

## 认证领域
- 登录、刷新、登出、修改密码、重置密码 API。与 `ActivationTokenService`、`RefreshTokenService` 配合，发放/撤销 JWT 与刷新令牌。
- 激活/重置邮件通过 `NotificationService` 发送（当前日志占位）。
- 审计通过 `AuditService` 落表并记录关键事件（登录、激活、重置等）。

## 订阅领域
- `SubscriptionPlanService`：套餐配置管理、启停控制。
- `TenantSubscriptionService`：租户订阅创建、状态切换、当前订阅查询。
- `SubscriptionOrderService`：订阅订单提交流程、运营审核、支付联动。

> 后续可在此文件继续补充调用示例、业务规则说明及与 API 层的映射关系。
