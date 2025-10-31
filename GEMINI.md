# Gemini Project Context: Enterprise SaaS Platform

This document provides context for the Gemini AI assistant to effectively contribute to the project.

## 1. Project Overview

- **Vision**: Build a multi-tenant SaaS platform for small and medium-sized enterprises (SMEs) focusing on account and subscription management.
- **Core MVP Features**:
    - Tenant management (onboarding, approval).
    - Role-Based Access Control (RBAC) with three fixed roles: `owner`, `admin`, `member`.
    - Subscription management with fixed plans (Free and Professional) and a manual upgrade process.
    - Audit logging for critical events.
    - A platform admin console for internal operations.
- **Key Assumption**: SMEs are accepting of a manual, offline process for tenant approval and payment for the MVP.

## 2. Technology Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Database**: PostgreSQL (with Row-Level Security for multi-tenancy)
- **Cache**: Redis (for JWT blocklists, rate limiting)
- **Async Tasks**: RabbitMQ (for notifications, can be mocked initially)
- **Frontend**: Angular 20, TypeScript, Angular CLI, NgRx
- **Deployment**: Docker Compose, GitHub Actions for CI

## 3. Development Plan & Priorities

The project follows a sprint-based approach. The immediate focus is on **Sprint 1**:

- **P0 Priority**: End-to-end flow for tenant application, approval, owner login, and member invitation.
- **P1 Priority**: Implement security and multi-tenancy foundations (JWT, RLS, Redis blocklist).
- **P2 Priority**: Set up the basic frontend skeleton for demonstration purposes.

**Key development sequence:**
1.  Database models and migrations (Alembic).
2.  Authentication endpoints (`/auth/*`).
3.  Tenant application and approval APIs.
4.  Member invitation flow.
5.  Basic frontend UI for the above flows.

## 4. Coding & Logging Guidelines

- **Logging**:
    - Use the structured logging setup provided in `app.core.logging`.
    - All log messages must include `tenant_id`, `user_id`, and `request_id`.
    - Use `set_log_context(tenant_id=..., user_id=...)` after authentication or when the context is known to enrich logs.
    - The `RequestLoggingMiddleware` automatically handles `request_id` and basic request/response logging.
- **Multi-tenancy**:
    - A middleware sets the `app.current_tenant` in the database session based on the JWT.
    - Database queries must be tenant-aware, relying on the RLS policies.
- **Security**:
    - Passwords must be hashed (PBKDF2).
    - All inputs must be validated.
    - Admin operations should require confirmation.

## 5. User Preferences

- **Package Name**: The user prefers `com.eagle.saas` instead of `com.example`. (This is a remembered preference).
- **Language**: Respond in Chinese.
