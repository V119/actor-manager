from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _extract_env_override(argv: list[str]) -> str:
    for index, arg in enumerate(argv):
        if arg == "--env" and index + 1 < len(argv):
            return str(argv[index + 1] or "").strip()
        if arg.startswith("--env="):
            return str(arg.split("=", 1)[1] or "").strip()
    return ""


_env_override = _extract_env_override(sys.argv[1:])
if _env_override:
    os.environ["ACTOR_MANAGER_ENV"] = _env_override

from backend.application.services import PortraitService
from backend.infrastructure.config import settings
from backend.infrastructure.orm_models import database
from backend.infrastructure.repositories import PeeweePortraitRepository
from backend.infrastructure.storage import StorageClient
from backend.logging_config import setup_logging_config

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill historical three-view preview/avatar variants.")
    parser.add_argument("--user-id", type=int, default=None, help="Only process sessions of this user.")
    parser.add_argument("--actor-id", type=int, default=None, help="Only process sessions of this actor.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of sessions to scan; 0 means all.")
    parser.add_argument("--dry-run", action="store_true", help="Scan and validate only without writing changes.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild variants even if a session already looks complete.",
    )
    parser.add_argument(
        "--env",
        type=str,
        default="",
        help="Optional ACTOR_MANAGER_ENV override (for example: dev/test/prod).",
    )
    return parser.parse_args()


def build_portrait_service() -> PortraitService:
    storage_client = StorageClient(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY,
        settings.MINIO_BUCKET,
        secure=settings.MINIO_SECURE,
        public_base_url=settings.MINIO_PUBLIC_BASE_URL,
    )
    return PortraitService(PeeweePortraitRepository(), storage_client)


async def run_backfill(args: argparse.Namespace) -> int:
    setup_logging_config()
    database.init(
        settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
    )
    if database.is_closed():
        database.connect(reuse_if_open=True)

    service = build_portrait_service()
    try:
        result = await service.backfill_three_view_variants(
            user_id=args.user_id,
            actor_id=args.actor_id,
            limit=args.limit,
            dry_run=bool(args.dry_run),
            force=bool(args.force),
        )
    finally:
        if not database.is_closed():
            database.close()

    logger.info(
        "Backfill summary scanned_sessions=%s updated_sessions=%s skipped_sessions=%s failed_sessions=%s scanned_assets=%s updated_assets=%s dry_run=%s force=%s",
        result["scanned_sessions"],
        result["updated_sessions"],
        result["skipped_sessions"],
        result["failed_sessions"],
        result["scanned_assets"],
        result["updated_assets"],
        bool(args.dry_run),
        bool(args.force),
    )
    return 1 if int(result["failed_sessions"]) > 0 else 0


def main() -> int:
    args = parse_args()
    return asyncio.run(run_backfill(args))


if __name__ == "__main__":
    raise SystemExit(main())
