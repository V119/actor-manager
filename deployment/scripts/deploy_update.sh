#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/actor-manager/app/actor-manager}"
RUNTIME_ROOT="${RUNTIME_ROOT:-/opt/actor-manager/runtime}"
DATA_ROOT="${DATA_ROOT:-/opt/actor-manager/data}"

BRANCH="${BRANCH:-main}"

BACKEND_PORT="${BACKEND_PORT:-18000}"
PUBLIC_HTTP_PORT="${PUBLIC_HTTP_PORT:-80}"
PUBLIC_HTTPS_PORT="${PUBLIC_HTTPS_PORT:-443}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
UV_INDEX_URL="${UV_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api}"
MINIO_PUBLIC_BASE_URL="${MINIO_PUBLIC_BASE_URL:-/minio}"
TLS_CERT_DIR="${TLS_CERT_DIR:-/opt/actor-manager/certs/nginx}"

POSTGRES_IMAGE_SOURCE="${POSTGRES_IMAGE_SOURCE:-docker.1ms.run/postgres:15.17}"
POSTGRES_IMAGE_LOCAL="${POSTGRES_IMAGE_LOCAL:-postgres:15.17}"
MINIO_IMAGE_SOURCE="${MINIO_IMAGE_SOURCE:-docker.1ms.run/minio/minio:latest}"
MINIO_IMAGE_LOCAL="${MINIO_IMAGE_LOCAL:-minio/minio:latest}"
NGINX_IMAGE_SOURCE="${NGINX_IMAGE_SOURCE:-docker.1ms.run/library/nginx:1.27-alpine}"
NGINX_IMAGE_LOCAL="${NGINX_IMAGE_LOCAL:-nginx:1.27-alpine}"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

wait_for_postgres() {
  local retries=60
  while (( retries > 0 )); do
    if docker exec actor-manager-postgres pg_isready -U postgres -d glacier_db >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    retries=$((retries - 1))
  done
  echo "PostgreSQL startup timeout" >&2
  return 1
}

wait_for_minio() {
  local retries=60
  while (( retries > 0 )); do
    if curl -fsS "http://127.0.0.1:9000/minio/health/live" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    retries=$((retries - 1))
  done
  echo "MinIO startup timeout" >&2
  return 1
}

wait_for_backend() {
  local retries=60
  local code
  while (( retries > 0 )); do
    code="$(curl -s -o /tmp/actor-manager-backend-check.json -w '%{http_code}' "http://127.0.0.1:${BACKEND_PORT}/api/auth/me" || true)"
    if [[ "$code" == "401" ]]; then
      return 0
    fi
    sleep 1
    retries=$((retries - 1))
  done
  echo "Backend startup timeout, last status=${code:-n/a}" >&2
  return 1
}

wait_for_nginx_auth() {
  local retries=60
  local code
  while (( retries > 0 )); do
    code="$(curl -s -o /tmp/actor-manager-auth-check.json -w '%{http_code}' "http://127.0.0.1:${PUBLIC_HTTP_PORT}/api/auth/me" || true)"
    if [[ "$code" == "401" ]]; then
      return 0
    fi
    sleep 1
    retries=$((retries - 1))
  done
  echo "Nginx auth check timeout, last status=${code:-n/a}" >&2
  return 1
}

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Please run as root" >&2
  exit 1
fi

require_command git
require_command docker
require_command uv
require_command npm
require_command rsync
require_command curl
require_command systemctl

if [[ ! -d "$APP_ROOT/.git" ]]; then
  echo "APP_ROOT is not a git repository: $APP_ROOT" >&2
  exit 1
fi

log "Updating source code in $APP_ROOT"
cd "$APP_ROOT"

git fetch origin "$BRANCH"
if [[ -n "$(git status --porcelain)" ]]; then
  STASH_NAME="auto-deploy-$(date '+%Y%m%d-%H%M%S')"
  git stash push -u -m "$STASH_NAME" >/dev/null
  log "Working tree was dirty; stashed as $STASH_NAME"
fi
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

log "Preparing runtime directories"
mkdir -p "$DATA_ROOT/postgres" "$DATA_ROOT/minio" "$RUNTIME_ROOT/nginx" "$TLS_CERT_DIR"
mkdir -p /opt/actor-manager/logs/backend /opt/actor-manager/logs/nginx
touch /opt/actor-manager/logs/backend/backend.log
touch /opt/actor-manager/logs/nginx/access.log /opt/actor-manager/logs/nginx/error.log
chmod 755 /opt/actor-manager/logs /opt/actor-manager/logs/backend /opt/actor-manager/logs/nginx
chmod 644 /opt/actor-manager/logs/backend/backend.log
chown 101:101 /opt/actor-manager/logs/nginx /opt/actor-manager/logs/nginx/access.log /opt/actor-manager/logs/nginx/error.log || true
chmod 664 /opt/actor-manager/logs/nginx/access.log /opt/actor-manager/logs/nginx/error.log

log "Pulling and tagging images"
docker pull "$POSTGRES_IMAGE_SOURCE"
docker pull "$MINIO_IMAGE_SOURCE"
docker pull "$NGINX_IMAGE_SOURCE"
docker tag "$POSTGRES_IMAGE_SOURCE" "$POSTGRES_IMAGE_LOCAL"
docker tag "$MINIO_IMAGE_SOURCE" "$MINIO_IMAGE_LOCAL"
docker tag "$NGINX_IMAGE_SOURCE" "$NGINX_IMAGE_LOCAL"

log "Restarting PostgreSQL container"
docker rm -f actor-manager-postgres >/dev/null 2>&1 || true
docker run -d \
  --name actor-manager-postgres \
  --restart unless-stopped \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=glacier_db \
  -v "$DATA_ROOT/postgres:/var/lib/postgresql/data" \
  -p 5432:5432 \
  "$POSTGRES_IMAGE_LOCAL" >/dev/null
wait_for_postgres

log "Restarting MinIO container"
docker rm -f actor-manager-minio >/dev/null 2>&1 || true
docker run -d \
  --name actor-manager-minio \
  --restart unless-stopped \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -v "$DATA_ROOT/minio:/data" \
  -p 9000:9000 \
  -p 9001:9001 \
  "$MINIO_IMAGE_LOCAL" server /data --console-address ":9001" >/dev/null
wait_for_minio

log "Syncing Python dependencies"
export UV_INDEX_URL
export UV_PYTHON="$PYTHON_VERSION"
uv python install "$PYTHON_VERSION"
if ! uv sync --all-groups --locked; then
  log "Locked sync failed, fallback to normal sync"
  uv sync --all-groups
  git restore --staged --worktree uv.lock >/dev/null 2>&1 || true
fi

log "Running database migration and bootstrap"
uv run --no-sync python -m backend.scripts.bootstrap

log "Building frontend assets"
pushd frontend >/dev/null
npm ci
VITE_API_BASE_URL="$VITE_API_BASE_URL" npm run build
popd >/dev/null

log "Syncing Nginx config"
rsync -az --delete --exclude certs "$APP_ROOT/deployment/nginx/" "$RUNTIME_ROOT/nginx/"

log "Syncing TLS certs"
TLS_SRC_CERT="$APP_ROOT/deployment/nginx/pem/fullchain.pem"
TLS_SRC_KEY=""
if [[ -f "$APP_ROOT/deployment/nginx/pem/privkey.pem" ]]; then
  TLS_SRC_KEY="$APP_ROOT/deployment/nginx/pem/privkey.pem"
elif [[ -f "$APP_ROOT/deployment/nginx/pem/default.pem" ]]; then
  TLS_SRC_KEY="$APP_ROOT/deployment/nginx/pem/default.pem"
fi

if [[ ! -f "$TLS_SRC_CERT" || -z "$TLS_SRC_KEY" ]]; then
  echo "Missing TLS cert files in $APP_ROOT/deployment/nginx/pem (required: fullchain.pem and privkey.pem or default.pem)" >&2
  exit 1
fi

TLS_CERT_MODULUS="$(openssl x509 -noout -modulus -in "$TLS_SRC_CERT" 2>/dev/null | openssl md5 | awk '{print $2}')"
TLS_KEY_MODULUS="$(openssl rsa -noout -modulus -in "$TLS_SRC_KEY" 2>/dev/null | openssl md5 | awk '{print $2}')"
if [[ -z "$TLS_CERT_MODULUS" || -z "$TLS_KEY_MODULUS" || "$TLS_CERT_MODULUS" != "$TLS_KEY_MODULUS" ]]; then
  echo "TLS certificate and private key mismatch: cert=$TLS_SRC_CERT key=$TLS_SRC_KEY" >&2
  exit 1
fi
install -m 0644 "$TLS_SRC_CERT" "$TLS_CERT_DIR/fullchain.pem"
install -m 0600 "$TLS_SRC_KEY" "$TLS_CERT_DIR/privkey.pem"

log "Restarting Nginx container"
docker rm -f actor-manager-nginx >/dev/null 2>&1 || true
docker run -d \
  --name actor-manager-nginx \
  --restart unless-stopped \
  -p "${PUBLIC_HTTP_PORT}:80" \
  -p "${PUBLIC_HTTPS_PORT}:443" \
  --add-host=host.docker.internal:host-gateway \
  -v "$RUNTIME_ROOT/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" \
  -v "$RUNTIME_ROOT/nginx/conf.d:/etc/nginx/conf.d:ro" \
  -v "$RUNTIME_ROOT/nginx/snippets:/etc/nginx/snippets:ro" \
  -v "$TLS_CERT_DIR:/etc/nginx/certs:ro" \
  -v "/opt/actor-manager/logs/nginx:/var/log/nginx" \
  -v "$APP_ROOT/frontend/dist:/srv/actor-manager/frontend-dist:ro" \
  "$NGINX_IMAGE_LOCAL" >/dev/null

log "Writing backend systemd service"
cat >/etc/systemd/system/actor-manager-backend.service <<EOF
[Unit]
Description=Actor Manager Backend (FastAPI)
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_ROOT}
Environment=ACTOR_MANAGER_CONFIG_API_HOST=0.0.0.0
Environment=ACTOR_MANAGER_CONFIG_API_PORT=${BACKEND_PORT}
Environment=ACTOR_MANAGER_CONFIG_API_RELOAD=false
Environment=ACTOR_MANAGER_CONFIG_MINIO_PUBLIC_BASE_URL=${MINIO_PUBLIC_BASE_URL}
Environment=ACTOR_MANAGER_CONFIG_LOGGING_FILE_ENABLED=true
Environment=ACTOR_MANAGER_CONFIG_LOGGING_FILE_PATH=/opt/actor-manager/logs/backend/backend.log
Environment=ACTOR_MANAGER_CONFIG_LOGGING_FILE_ALSO_STDOUT=true
Environment=UV_PYTHON=${PYTHON_VERSION}
Environment=UV_INDEX_URL=${UV_INDEX_URL}
ExecStart=/usr/local/bin/uv run --no-sync python backend/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable actor-manager-backend >/dev/null
systemctl restart actor-manager-backend
wait_for_backend

log "Writing logrotate policy"
rm -f /etc/logrotate.d/actor-manager

install -m 0644 "$APP_ROOT/deployment/logrotate/actor-manager-backend" /etc/logrotate.d/actor-manager-backend
install -m 0644 "$APP_ROOT/deployment/logrotate/actor-manager-nginx" /etc/logrotate.d/actor-manager-nginx

log "Running health checks"
curl -fsS "http://127.0.0.1:${PUBLIC_HTTP_PORT}/healthz" >/dev/null
curl -fsS "http://127.0.0.1:${PUBLIC_HTTP_PORT}/" >/dev/null
curl -kfsS "https://127.0.0.1:${PUBLIC_HTTPS_PORT}/healthz" >/dev/null
wait_for_nginx_auth

log "Deployment completed"
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | awk 'NR==1 || $1 ~ /^actor-manager-/'
systemctl --no-pager --full status actor-manager-backend | sed -n '1,12p'
log "Entry URL: http://<server-ip>:${PUBLIC_HTTP_PORT}"
log "Entry URL: https://<server-ip>:${PUBLIC_HTTPS_PORT}"
