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
- 部署到服务器并由 Nginx 统一接入时，需要设置：
  - `minio.public_base_url`（默认空；服务器部署脚本默认设置为 `/minio`）
  - 这样前端拿到的上传/预览 URL 会是同域 `/minio/...`，不会暴露内部 `localhost:9000`
- 三视图拼接参数可配置：
  - `portrait.compose.width` / `portrait.compose.height`
  - `portrait.compose.order`（默认 `left,front,right`）
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
- 种子数据写入（User/Actor/Style）

该步骤是幂等的，可重复执行。

### 初始化后的默认三端登录入口与账号

登录路径（路由）：
- 普通演员端：`/login/individual`
- 企业用户端：`/login/enterprise`
- 后台管理端：`/admin/login`

本地前端开发环境（`http://127.0.0.1:5173`）可直接访问：
- `http://127.0.0.1:5173/login/individual`
- `http://127.0.0.1:5173/login/enterprise`
- `http://127.0.0.1:5173/admin/login`

若使用一体化部署（Nginx，默认 `http://127.0.0.1:8000`），对应访问路径相同：
- `http://127.0.0.1:8000/login/individual`
- `http://127.0.0.1:8000/login/enterprise`
- `http://127.0.0.1:8000/admin/login`

默认账号密码来自配置（`seed.users.*` 与 `auth.admin.*`）：
- 普通演员端：`actor_user` / `123456`
- 企业用户端：`enterprise_user` / `123456`
- 后台管理端：`admin` / `Admin@123456`

## 5.1 角色权限说明

- 普通用户登录后可访问：`基本信息`、`协议签署`、`素材管理`、`风格实验室`
- 企业用户登录后可访问：`协议签署`、`演员发布广场`
- 协议流程：
  - 管理员配置演员协议模板与企业协议模板
  - 演员签署平台与演员协议后，才可发布资料与素材
  - 企业签署平台与企业协议后，才可访问演员发布广场与演员详情

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
- 业务日志：三视图上传、视频上传、协议签署、历史查询
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

## 11. 支付与结算能力（新增）

后端已新增电商化支付主链路（当前为 Mock 网关实现，便于联调）：

- 企业侧：
  - 签约演员后自动入购物车
  - 购物车管理：`GET/POST/DELETE /api/enterprise/cart`
  - 订单预览：`POST /api/enterprise/orders/preview`
  - 创建订单：`POST /api/enterprise/orders`
  - 订单查询：`GET /api/enterprise/orders`、`GET /api/enterprise/orders/{order_no}`
  - 发起支付（微信/支付宝）：`POST /api/enterprise/orders/{order_no}/pay`
  - 企业验收（可提前触发放款倒计时）：`POST /api/enterprise/orders/{order_no}/accept`

- 管理侧：
  - 支付配置读取/更新：`GET/PUT /api/admin/payments/config`
  - 订单总览：`GET /api/admin/payments/orders`、`GET /api/admin/payments/orders/{order_no}`
  - 退款工单：`GET /api/admin/payments/refunds`
  - 发起退款：`POST /api/admin/payments/refunds`
  - 审核退款：`POST /api/admin/payments/refunds/approve`
  - 跑批结算：`POST /api/admin/payments/settlements/run`

默认支付规则配置（`backend/configs/common.yml`）：

- `payment.use_mock`：是否启用 Mock 支付通道（`true` 时微信/支付宝均走 Mock）
- `payment.fee_rate_bps`：平台手续费率（基点，10000=100%）
- `payment.auto_accept_hours`：自动验收时长
- `payment.dispute_protect_hours`：争议保护时长
- `payment.max_hold_hours`：最大冻结时长
- `payment.settlement_safety_buffer_hours`：放款安全缓冲时长
- `payment.allowed_channels`：启用通道（`wechat` / `alipay`）
- `payment.mock_channel_auto_success`：Mock 通道自动成功开关

Mock 支付建议（用于完整链路联调）：

- 本地联调请设置：`payment.use_mock: true`
- 需要“下单即成功”以跑通全流程时，设置：`payment.mock_channel_auto_success: true`
- 若切换为 `payment.use_mock: false`，系统会拒绝发起支付/退款/结算，并提示未接入真实微信/支付宝网关

当前结算释放时间计算为：

- `release_at = min(accepted_or_auto_accept + dispute_protect_hours, paid_at + max_hold_hours - safety_buffer_hours)`

说明：

- 本次实现采用“支付通道适配层 + 业务状态机”模式，已预留真实微信/支付宝接入位置（`backend/application/payment_service.py` 的 `MockChannelGateway`）。
- 接入真实支付时，仅需替换 gateway 实现并补充异步回调/验签，不需要推翻业务表结构。

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
