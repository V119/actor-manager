# Glacier AI Actor

本项目为前后端分离的 AI Actor 管理系统：
- 前端：Vue 3 + Vite + Tailwind CSS
- 后端：FastAPI + Peewee Async
- 依赖服务：PostgreSQL + MinIO
- Python 依赖管理：`uv`（已切换）

## 0. 环境要求

- Docker
- `uv` >= 0.9
- Node.js >= 18

## 0.1 目录边界（便于前后端分开部署）

- `backend/`：后端代码、配置、迁移、初始化脚本
- `frontend/`：前端代码与构建产物
- 根目录：仓库级文件（如 `README.md`、`pyproject.toml`、`uv.lock`）

## 1. 将已拉取镜像重命名为常用标签

你已经拉取了以下镜像：
- `docker.1ms.run/minio/minio:latest`
- `docker.1ms.run/postgres:15.17`

执行重命名：

```bash
docker tag docker.1ms.run/minio/minio:latest minio/minio:latest
docker tag docker.1ms.run/postgres:15.17 postgres:15.17
```

## 2. 启动 PostgreSQL 和 MinIO

先清理同名旧容器（可重复执行）：

```bash
docker rm -f actor-manager-postgres actor-manager-minio 2>/dev/null || true
```

启动数据库：

```bash
docker run -d \
  --name actor-manager-postgres \
  -e POSTGRES_DB=glacier_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15.17
```

启动对象存储：

```bash
docker run -d \
  --name actor-manager-minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -p 9000:9000 \
  -p 9001:9001 \
  minio/minio:latest server /data --console-address ":9001"
```

检查容器：

```bash
docker ps --format '{{.Names}} {{.Image}} {{.Status}}'
```

## 3. 使用 uv 安装后端依赖

在项目根目录执行（当前 `uv` 项目元数据在根目录）：

```bash
uv lock
uv sync --all-groups
```

## 4. 配置文件（统一从 YAML 读取）

后端所有配置项统一从配置文件读取：

- 公共配置：[backend/configs/common.yml](/Users/haoyang/src/python/actor-manager/backend/configs/common.yml)
- 环境覆盖配置（默认 dev）：[backend/configs/config-dev.yml](/Users/haoyang/src/python/actor-manager/backend/configs/config-dev.yml)
- 后端不再使用 `.env` / `.env.example` 作为配置入口
- 三视图素材存储采用分桶：
  - `minio.buckets.portrait_raw`（原始三张图）
  - `minio.buckets.portrait_generated`（4:3 合成图）
- 三视图拼接参数可配置：
  - `portrait.compose.width` / `portrait.compose.height`
  - `portrait.compose.order`（默认 `front,left,right`）
- 风格实验室（百炼）配置项：
  - `style_generation.model.base_url`（默认 `https://dashscope.aliyuncs.com`）
  - `style_generation.model.prompt_base_url`（默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`）
  - `style_generation.model.image_api_path`（默认 `/api/v1/services/aigc/multimodal-generation/generation`）
  - `style_generation.model.image_model`（默认 `wan2.7-image`）
  - `style_generation.image.size`（默认 `1024*1024`）
- 风格生成输入策略：
  - 使用“已发布三视图”的三张原始半身图（左/正/右）分别作为多图参考输入给大模型
  - 不再将三图拼接后的合成图作为单一输入参考

可通过环境变量切换环境配置文件：

```bash
export ACTOR_MANAGER_ENV=dev
```

并支持按键路径覆盖，前缀为 `ACTOR_MANAGER_CONFIG_`（例如 `ACTOR_MANAGER_CONFIG_API_PORT=18000`）。

## 5. 数据初始化（迁移 + 建表 + MinIO Bucket + 种子数据）

在项目根目录执行：

```bash
uv run python -m backend.scripts.bootstrap
```

该命令会自动执行：
- Alembic migration（`alembic upgrade head`）
- 缺失表兜底创建（safe create）
- MinIO bucket（默认 `glacier`）创建
- 种子数据写入（User/Actor/Style/Protocol）

该步骤是幂等的，可重复执行。

### 初始化后的默认账号

- 普通用户：读取 `seed.users.individual`（默认 `actor_user` / `123456`）
- 企业用户：读取 `seed.users.enterprise`（默认 `enterprise_user` / `123456`）

## 5.1 角色权限说明

- 普通用户登录后可访问：`肖像上传`、`协议管理`、`风格实验室`
- 企业用户登录后可访问：`演员发布广场`、`协议管理`
- 协议流程：
  - 企业用户在协议管理中创建协议并指定普通用户
  - 普通用户在协议管理中签署企业指定协议

## 6. 启动后端

在项目根目录执行：

```bash
uv run python backend/server.py
```

后端默认地址：`http://127.0.0.1:8000`

## 7. 启动前端

新开一个终端：

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

如需分开部署，前端通过环境变量配置后端地址（默认 `http://127.0.0.1:8000/api`）：

```bash
echo 'VITE_API_BASE_URL=http://127.0.0.1:8000/api' > frontend/.env.local
```

前端地址：`http://127.0.0.1:5173`

## 8. 运行校验

后端健康检查：

```bash
curl http://127.0.0.1:8000/
```

说明：
- `/api/actors` 仅企业用户可访问
- `/api/styles` 仅普通用户可访问
- 已接入 `TraceIdMiddleware` 与 `LogRequestMiddleware`
- 普通用户三视图上传接口：
  - `GET /api/portraits/three-view/current`（获取当前生效三视图）
  - `POST /api/portraits/three-view/presign`（获取三图直传 MinIO 的预签名地址）
  - `POST /api/portraits/three-view/jobs`（创建异步合成任务）
  - `GET /api/portraits/three-view/jobs/{job_key}`（轮询异步合成状态）
  - `POST /api/portraits/three-view`（后端直传兜底接口，兼容无 CORS 环境）
  - `POST /api/portraits/three-view/recompose`（当已有历史三视图时，支持仅上传要替换的角度，后端自动复用其余角度并重新生成新合成图）
  - `DELETE /api/portraits/three-view/history?purge_storage=true`（仅清理历史三视图，不影响当前生效数据）
  - `GET /api/portraits/videos/current`（获取当前生效视频）
  - `POST /api/portraits/videos/presign`（获取视频直传 MinIO 的预签名地址）
  - `POST /api/portraits/videos/commit`（直传后落库）
  - `POST /api/portraits/videos`（后端流式上传兜底接口）
  - `DELETE /api/portraits/videos/history?purge_storage=true`（仅清理历史视频，不影响当前生效数据）
  - `GET /api/portraits/three-view/history`（后端保留历史查询能力，便于未来前端开放历史版本）
  - `GET /api/portraits/videos`（查询当前登录用户的视频素材列表）
  - 前端默认优先走“浏览器直传 MinIO + 异步任务”，若直传链路不可用（例如 CORS/网络限制），会自动回退到后端上传接口，保证上传流程可用

### 8.1 日志与问题排查（新增）

后端已增强关键排障日志，覆盖：
- 请求链路日志：`request.start` / `request.end` / `request.error`
  - 包含：`request_id`、`trace_id`、`method`、`path`、`status`、`duration_ms`
- 鉴权与权限日志：注册/登录/登出、角色校验失败、会话失效
- 业务日志：三视图上传、视频上传、协议创建与签署、历史查询
- 存储日志：MinIO bucket 创建、对象上传开始与完成
- 初始化日志：bootstrap 的迁移、建表、分桶、种子数据

请求日志配置项（`backend/configs/common.yml`）：

```yaml
logging:
  level: INFO
  request:
    enabled: true
    body_preview_limit: 2048
    max_capture_bytes: 65536
```

说明：
- 会自动脱敏敏感字段（如 `authorization`、`password`、`token` 等）
- multipart / 视频 / 图片请求体默认不打印原文，只记录类型与大小，避免大包体影响性能
- 响应头会返回 `X-Trace-Id` 与 `X-Request-Id`，可用于端到端串联日志

后端测试：

```bash
uv run pytest -q
```

## 9. 大规模上传优化（1/2/3/4 已实现）

已落地的优化项：
- `1` 浏览器直传 MinIO（预签名 URL），后端不再承接大文件正文
- `2` 三视图异步合成任务化（创建任务 + 轮询状态），避免请求长时间阻塞
- `3` 后端流式上传路径（视频接口不再 `await file.read()` 一次性读入内存）
- `4` 数据库热点路径优化（新增组合索引 + 时间维度 BRIN 索引，迁移文件：`backend/migrations/versions/b2f4a6c1d9e7_add_compose_jobs_and_hot_path_indexes.py`）

本地验证命令：

```bash
uv run python -m backend.scripts.bootstrap
uv run pytest -q
cd frontend && npm run build
```

### 9.1 当前与历史数据隔离（新增）

- 三视图会话与视频资产已增加状态字段：`is_current`、`superseded_at`
- 系统始终只将 `is_current=true` 作为“当前生效数据”
- 每次上传新素材会自动将旧版本标记为历史（`is_current=false`）
- 清理接口仅删除历史数据（`is_current=false`），不会删除当前生效版本
- 清理时会做 MinIO 对象引用检查，若对象仍被当前数据引用则跳过删除，避免误删

对应迁移文件：
- `backend/migrations/versions/e7d1b2f0c4a9_add_current_history_flags_for_portrait_assets.py`

## 10. 停止与清理

```bash
docker stop actor-manager-postgres actor-manager-minio
docker rm actor-manager-postgres actor-manager-minio
```
