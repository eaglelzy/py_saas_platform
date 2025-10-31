# 前端技术栈清单（Angular）

针对 `frontend-angular` 工作区当前及计划使用的依赖整理如下，便于团队对齐后续安装与维护策略。

## 核心框架
- **Angular 20 LTS**：`@angular/core`, `@angular/common`, `@angular/router`, `@angular/forms`, `@angular/platform-browser`, `@angular/platform-server`
- **Angular CLI 20**：`@angular/cli`, `@angular/build`（Vite + esbuild 工具链）
- **TypeScript 5.9**：与 Angular 20 官方兼容版本
- **RxJS 7.8**：Angular 标配响应式库

> 当前 `package.json` 已包含上述依赖。后续升级统一使用 `npx ng update`。

## UI 与样式层
- **Angular Material 20 + CDK**（已安装）：提供基础组件、无障碍支持、Overlay/Portal 能力  
  已执行：`npx ng add @angular/material@latest --skip-confirmation`
- **Tailwind CSS 3**（计划引入）：用于快速布局和主题定制  
  安装命令示例：`npm install -D tailwindcss postcss autoprefixer` + `npx ng generate config tailwind`
- **SCSS 全局样式**：保留 Angular 默认 `styles.scss`，用于变量、混入与自定义主题补充

## 状态管理与数据访问
- **NgRx Store + Effects + Entity**（已安装）：集中管理租户上下文、RBAC 权限缓存、订阅状态  
  已集成依赖：`@ngrx/store`, `@ngrx/effects`, `@ngrx/entity`, `@ngrx/store-devtools`（开发环境按需启用）  
  Init 命令示例：`npx ng add @ngrx/store@latest`（已执行） + `npm install @ngrx/effects @ngrx/entity @ngrx/store-devtools`
- **Angular Signals/SignalStore**（辅助）：用于组件局部状态、轻量级派生数据
- **Angular `HttpClient` 拦截器**：统一注入 JWT、`X-Tenant-ID`、统一错误处理（自实现）

## 表单与多语言
- **Reactive Forms**：默认表单方案，定制密码强度、邀请码等 Validator
- **多语言**：暂不启用；后续若有需求可评估 `@ngx-translate` 或 Angular 内置 i18n

## 质量与测试
- **Karma + Jasmine**：Angular 默认单元测试框架（已在 `devDependencies` 中）
- **Jest Builder**（可选）：若需要与后端统一断言风格  
  安装命令示例：`npm install -D jest @types/jest jest-preset-angular @angular-builders/jest`
- **Cypress / Playwright**（计划）：E2E 验证租户与运营台核心流程
- **ESLint + Angular ESLint**：`npx ng add @angular-eslint/schematics`（建议在初始化后执行）
- **Prettier**：项目已包含基础配置，按团队规范扩展

## 可观察性与集成
- **@sentry/angular-ivy**（计划）：统一前端错误追踪，附带 `tenant_id`/`user_id` 标签
- **@ngx-pwa/local-storage** 或自封装方案（可选）：安全存储 Token、会话信息
- **环境变量管理**：使用 `src/environments`，并在 CI/CD 中覆盖 `environment.prod.ts`

## Node 与工具版本建议
- **Node.js**：>= 20.11 LTS（配合 Angular 20 官方要求）
- **npm**：>= 10，或使用 `pnpm`/`yarn`（如更换需同步 CI 脚本）
- **浏览器支持**：Chromium 114+, Firefox 113+, Safari 16.4+

> 安装任何计划依赖前，请先确认是否需要加入 GitHub Actions、Docker 镜像或 `package-lock.json`，避免 CI 构建失败。
