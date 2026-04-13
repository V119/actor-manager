from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request

from backend.config import get_config, set_trace_id


logger = logging.getLogger(__name__)

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie"}
SENSITIVE_BODY_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "access_key",
}


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}...(truncated)"


def _safe_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: "***" if key.lower() in SENSITIVE_HEADERS else value
        for key, value in headers.items()
    }


def _mask_sensitive_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        masked: dict[str, Any] = {}
        for key, value in payload.items():
            if str(key).lower() in SENSITIVE_BODY_KEYS:
                masked[key] = "***"
            else:
                masked[key] = _mask_sensitive_payload(value)
        return masked
    if isinstance(payload, list):
        return [_mask_sensitive_payload(item) for item in payload]
    return payload


def _set_request_body_for_downstream(request: Request, body: bytes) -> None:
    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = receive  # type: ignore[attr-defined]


def _should_capture_body(method: str, content_type: str, content_length: int) -> bool:
    if method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    if "multipart/form-data" in content_type:
        return False
    if "application/octet-stream" in content_type:
        return False
    if content_type.startswith("image/") or content_type.startswith("video/"):
        return False
    if "application/json" in content_type or "application/x-www-form-urlencoded" in content_type:
        max_capture_bytes = int(get_config("logging.request.max_capture_bytes", 65536))
        return content_length <= 0 or content_length <= max_capture_bytes
    return False


def _summarize_body(content_type: str, body: bytes) -> str:
    if not body:
        return "<empty>"
    preview_limit = int(get_config("logging.request.body_preview_limit", 2048))

    if "application/json" in content_type:
        try:
            parsed = json.loads(body.decode("utf-8"))
            safe_payload = _mask_sensitive_payload(parsed)
            return _truncate(json.dumps(safe_payload, ensure_ascii=False), preview_limit)
        except Exception:
            return _truncate(body.decode("utf-8", errors="replace"), preview_limit)

    if "application/x-www-form-urlencoded" in content_type or content_type.startswith("text/"):
        return _truncate(body.decode("utf-8", errors="replace"), preview_limit)

    return f"<binary {len(body)} bytes>"


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", "") or request.headers.get("X-Request-Id", uuid.uuid4().hex)
        trace_id = getattr(request.state, "trace_id", "") or request.headers.get("X-Trace-Id", request_id)
        set_trace_id(trace_id)
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Request-Id"] = request_id
        return response


class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if not bool(get_config("logging.request.enabled", True)):
            return await call_next(request)

        started_at = time.perf_counter()
        method = request.method
        path = request.url.path
        request_id = getattr(request.state, "request_id", "") or request.headers.get("X-Request-Id", uuid.uuid4().hex)
        trace_id = getattr(request.state, "trace_id", "") or request.headers.get("X-Trace-Id", request_id)
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        set_trace_id(trace_id)
        query_params = str(request.query_params)
        content_type = request.headers.get("content-type", "")
        raw_content_length = request.headers.get("content-length", "0")
        content_length = int(raw_content_length) if raw_content_length.isdigit() else 0
        client_ip = request.client.host if request.client else "-"
        user_agent = request.headers.get("user-agent", "-")
        headers = _safe_headers(dict(request.headers.items()))

        body_summary = "<not-captured>"
        if _should_capture_body(method, content_type, content_length):
            try:
                body_bytes = await request.body()
                _set_request_body_for_downstream(request, body_bytes)
                body_summary = _summarize_body(content_type, body_bytes)
            except Exception:
                logger.exception("Failed to capture request body", extra={"path": path, "method": method})
                body_summary = "<capture-failed>"
        elif "multipart/form-data" in content_type:
            body_summary = f"<multipart body omitted, content_length={content_length}>"
        elif content_type.startswith("image/") or content_type.startswith("video/"):
            body_summary = f"<media body omitted, content_length={content_length}>"

        logger.info(
            "request.start request_id=%s trace_id=%s method=%s path=%s query=%s client_ip=%s user_agent=%s content_type=%s content_length=%s headers=%s body=%s",
            request_id,
            trace_id,
            method,
            path,
            query_params,
            client_ip,
            user_agent,
            content_type or "-",
            content_length,
            headers,
            body_summary,
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            logger.exception(
                "request.error request_id=%s trace_id=%s method=%s path=%s duration_ms=%.2f",
                request_id,
                trace_id,
                method,
                path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        response_size = response.headers.get("content-length", "-")
        logger.info(
            "request.end request_id=%s trace_id=%s method=%s path=%s status=%s duration_ms=%.2f response_size=%s",
            request_id,
            trace_id,
            method,
            path,
            response.status_code,
            elapsed_ms,
            response_size,
        )
        return response
