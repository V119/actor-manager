import os
from contextvars import ContextVar
from pathlib import Path
from typing import Any

import yaml


BACKEND_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = BACKEND_ROOT / "configs"
CONFIG_PREFIX = "ACTOR_MANAGER_CONFIG_"


def get_env() -> str:
    return os.getenv("ACTOR_MANAGER_ENV", "dev")


ENV = get_env()
COMMON_CONFIG_FILE = CONFIG_DIR / "common.yml"
ENV_CONFIG_FILE = CONFIG_DIR / f"config-{ENV}.yml"
if not ENV_CONFIG_FILE.is_file():
    ENV_CONFIG_FILE = CONFIG_DIR / "config-dev.yml"

_CONFIG: dict[str, Any] | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _merge(default: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(default.get(key), dict):
            _merge(default[key], value)
        else:
            default[key] = value
    return default


def load_config() -> None:
    global _CONFIG
    if _CONFIG is not None:
        return
    common = _load_yaml(COMMON_CONFIG_FILE)
    env_config = _load_yaml(ENV_CONFIG_FILE)
    _CONFIG = _merge(common, env_config)


def _parse_env_override(raw: str) -> Any:
    parsed = yaml.safe_load(raw)
    return parsed


def _replace_value_by_environ(value: Any, env_name: str) -> Any:
    if isinstance(value, dict):
        if env_name in os.environ:
            return _parse_env_override(os.environ[env_name])
        replaced = {}
        for key, item in value.items():
            sub_env_name = f"{env_name}_{str(key).replace('.', '_').replace('-', '_').upper()}"
            replaced[key] = _replace_value_by_environ(item, sub_env_name)
        return replaced

    if env_name in os.environ:
        return _parse_env_override(os.environ[env_name])
    return value


def get_config(key_string: str = "", default: Any = None) -> Any:
    load_config()
    assert _CONFIG is not None

    keys = [key.strip() for key in key_string.split(".") if key.strip()]
    result: Any = _CONFIG
    for key in keys:
        result = result.get(key) if isinstance(result, dict) else None

    env_name = f"{CONFIG_PREFIX}{key_string.replace('.', '_').replace('-', '_').upper()}"
    result = _replace_value_by_environ(result, env_name)

    if result is None:
        return default
    return result


trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str | None:
    return trace_id_var.get()


def set_trace_id(value: str) -> None:
    trace_id_var.set(value)
