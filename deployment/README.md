# Deployment 说明

本目录用于存放部署相关配置。当前提供了 Nginx 作为统一接入层（Ingress）配置，覆盖前后端一体部署的核心需求，并预留前后端拆分部署的改造点。

## 目录结构

```text
deployment/
  README.md
  scripts/
    deploy_update.sh
  nginx/
    nginx.conf
    conf.d/
      upstreams.conf
      actor-manager.conf
    snippets/
      proxy_common.conf
```

## 当前架构职责

- `Nginx`：统一入口，负责静态前端分发、`/api/` 转发、基础安全头、限流与访问日志。
- `Backend (FastAPI)`：业务 API（登录注册、肖像上传、视频上传、协议管理、风格实验室、企业发现广场等）。
- `Frontend (Vue/Vite)`：SPA 应用，通过 Nginx 访问并调用同域 `/api`。

## 一键更新部署脚本（服务器）

脚本路径：`deployment/scripts/deploy_update.sh`

能力：

- 拉取 GitHub 最新代码（`main`）
- 自动处理服务器工作区脏文件（先 stash）
- 拉取并重标记 Postgres/MinIO/Nginx 镜像
- 重建并启动 `postgres`、`minio`、`nginx` 容器
- 执行 `uv sync`、数据库迁移与初始化
- 构建前端并同步 Nginx 配置
- 重启后端 `systemd` 服务并执行健康检查

在服务器执行：

```bash
cd /opt/actor-manager/app/actor-manager
bash deployment/scripts/deploy_update.sh
```

可选环境变量（覆盖默认值）：

- `APP_ROOT`（默认 `/opt/actor-manager/app/actor-manager`）
- `RUNTIME_ROOT`（默认 `/opt/actor-manager/runtime`）
- `DATA_ROOT`（默认 `/opt/actor-manager/data`）
- `BRANCH`（默认 `main`）
- `PUBLIC_PORT`（默认 `8000`）
- `BACKEND_PORT`（默认 `18000`）

## Nginx 配置能力（对应当前功能）

- 前后端统一接入：
  - `/api/` -> 后端服务
  - 其他路径 -> 前端静态文件（SPA History 路由回退到 `index.html`）
- 上传与生成场景适配：
  - `client_max_body_size 256m`
  - API 代理超时提升到 300s（风格生成、上传等长耗时请求）
  - `proxy_request_buffering off`，减少大文件中转磁盘开销
- 认证安全：
  - 对 `/api/auth/login`、`/api/auth/register` 增加 IP 维度限流
- 可观测性：
  - JSON access log
  - 透传并记录 `X-Request-Id` / `X-Trace-Id`，便于和后端日志关联排障
- 基础安全响应头：
  - `X-Content-Type-Options`
  - `X-Frame-Options`
  - `Referrer-Policy`
  - `Permissions-Policy`

## 部署前准备

1. 后端可访问地址与端口（默认）：`host.docker.internal:18000`（Nginx 容器回源宿主机）
2. 前端构建产物目录：`frontend/dist`
3. 如果前后端拆分部署：
   - 修改 `deployment/nginx/conf.d/upstreams.conf` 中的 `server` 地址为真实后端地址。

## 前端构建（必须）

前端需要以相对 API 路径打包，确保通过 Nginx 同域转发：

```bash
cd frontend
VITE_API_BASE_URL=/api npm run build
```

## 后端启动建议（示例）

生产建议关闭 reload：

```bash
cd /Users/haoyang/src/python/actor-manager
ACTOR_MANAGER_CONFIG_API_PORT=18000 ACTOR_MANAGER_CONFIG_API_RELOAD=false uv run python backend/server.py
```

## Nginx 语法校验

```bash
docker run --rm \
  -v /Users/haoyang/src/python/actor-manager/deployment/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /Users/haoyang/src/python/actor-manager/deployment/nginx/conf.d:/etc/nginx/conf.d:ro \
  -v /Users/haoyang/src/python/actor-manager/deployment/nginx/snippets:/etc/nginx/snippets:ro \
  nginx:1.27-alpine nginx -t
```

## 运行示例（容器方式）

> 当前示例默认 Nginx 容器回源宿主机后端 `host.docker.internal:18000`。

```bash
docker run -d --name actor-manager-nginx \
  -p 8000:80 \
  --add-host=host.docker.internal:host-gateway \
  -v /Users/haoyang/src/python/actor-manager/deployment/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /Users/haoyang/src/python/actor-manager/deployment/nginx/conf.d:/etc/nginx/conf.d:ro \
  -v /Users/haoyang/src/python/actor-manager/deployment/nginx/snippets:/etc/nginx/snippets:ro \
  -v /Users/haoyang/src/python/actor-manager/frontend/dist:/srv/actor-manager/frontend-dist:ro \
  nginx:1.27-alpine
```

## 验收清单

1. 基础健康检查：
   - `curl -i http://127.0.0.1:8000/healthz` 返回 `200 ok`
2. 前端入口：
   - 访问 `http://127.0.0.1:8000/login/individual` 可正常返回页面
   - 刷新 `http://127.0.0.1:8000/login/enterprise` 不应 404（SPA 回退生效）
3. API 转发：
   - `curl -i http://127.0.0.1:8000/api/auth/me`（未登录应返回 401，但路径应命中后端）
4. Trace 链路：
   - API 响应头包含 `X-Trace-Id` 与 `X-Request-Id`
   - Nginx access log 中可看到 `request_id` / `trace_id` 字段

## 工程化维护建议

- 变更策略：
  - 全局策略放 `nginx.conf`
  - 站点路由放 `conf.d/actor-manager.conf`
  - 复用代理参数放 `snippets/proxy_common.conf`
- 未来拆分部署：
  - 仅需调整 `upstreams.conf`（后端地址）与前端打包参数，无需改业务代码。
- 生产建议：
  - 在上游或 Nginx 层接入 TLS 证书。
  - 结合业务流量调优 `limit_req`、`client_max_body_size`、超时与日志采样策略。
