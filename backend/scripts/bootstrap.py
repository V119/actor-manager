from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
import subprocess

from backend.config import get_config
from backend.infrastructure.config import settings
from backend.infrastructure.orm_models import (
    ActorModel,
    GeneratedResultModel,
    PortraitComposeJobModel,
    PortraitGuidanceSampleModel,
    PortraitModel,
    PortraitUploadAssetModel,
    PortraitUploadSessionModel,
    PortraitVideoAssetModel,
    ProtocolModel,
    SessionModel,
    StyleModel,
    UserModel,
    database,
)
from backend.infrastructure.security import hash_password
from backend.infrastructure.storage import StorageClient
from backend.logging_config import setup_logging_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
logger = logging.getLogger(__name__)


def run_migrations() -> None:
    logger.info("Running alembic migrations")
    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(BACKEND_DIR),
            check=True,
        )
    except subprocess.CalledProcessError:
        logger.warning("Alembic upgrade failed; applying legacy stamp fallback")
        # Legacy compatibility: older local setups may have schema created before
        # Alembic revisions were tracked. Stamp to the initial revision first,
        # then upgrade to the latest head.
        subprocess.run(
            ["alembic", "stamp", "6f3144afe3bc"],
            cwd=str(BACKEND_DIR),
            check=True,
        )
        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(BACKEND_DIR),
            check=True,
        )
    logger.info("Alembic migrations completed")


def connect_database() -> None:
    logger.info(
        "Connecting database host=%s port=%s db=%s user=%s",
        settings.DB_HOST,
        settings.DB_PORT,
        settings.DB_NAME,
        settings.DB_USER,
    )
    database.init(
        settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
    )
    if database.is_closed():
        database.connect(reuse_if_open=True)
    logger.info("Database connected")


def ensure_bucket() -> None:
    logger.info("Ensuring MinIO buckets")
    storage = StorageClient(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY,
        settings.MINIO_BUCKET,
        secure=settings.MINIO_SECURE,
    )
    storage.ensure_buckets(
        [
            settings.MINIO_PORTRAIT_RAW_BUCKET,
            settings.MINIO_PORTRAIT_GENERATED_BUCKET,
            settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            settings.MINIO_PORTRAIT_GUIDANCE_BUCKET,
            settings.MINIO_STYLE_GENERATED_BUCKET,
        ]
    )
    logger.info(
        "MinIO buckets ensured default=%s raw=%s generated=%s video=%s guidance=%s style=%s",
        settings.MINIO_BUCKET,
        settings.MINIO_PORTRAIT_RAW_BUCKET,
        settings.MINIO_PORTRAIT_GENERATED_BUCKET,
        settings.MINIO_PORTRAIT_VIDEO_BUCKET,
        settings.MINIO_PORTRAIT_GUIDANCE_BUCKET,
        settings.MINIO_STYLE_GENERATED_BUCKET,
    )


def ensure_tables() -> None:
    logger.info("Ensuring database tables")
    with database.allow_sync():
        database.create_tables(
            [
                ActorModel,
                StyleModel,
                PortraitModel,
                PortraitUploadSessionModel,
                PortraitUploadAssetModel,
                PortraitComposeJobModel,
                PortraitVideoAssetModel,
                PortraitGuidanceSampleModel,
                GeneratedResultModel,
                UserModel,
                SessionModel,
                ProtocolModel,
            ],
            safe=True,
        )
    logger.info("Database tables ensured")


def seed_data() -> dict[str, int]:
    individual_seed = dict(get_config("seed.users.individual", {}))
    enterprise_seed = dict(get_config("seed.users.enterprise", {}))
    admin_seed = dict(get_config("seed.users.admin", {}))

    individual_username = str(individual_seed.get("username", "actor_user"))
    individual_password = str(individual_seed.get("password", "123456"))
    individual_display_name = str(individual_seed.get("display_name", "示例普通用户"))

    enterprise_username = str(enterprise_seed.get("username", "enterprise_user"))
    enterprise_password = str(enterprise_seed.get("password", "123456"))
    enterprise_display_name = str(enterprise_seed.get("display_name", "示例企业用户"))
    enterprise_company_intro = str(enterprise_seed.get("company_intro", "示例企业简介"))

    admin_username = str(admin_seed.get("username", "admin"))
    admin_password = str(admin_seed.get("password", "Admin@123456"))
    admin_display_name = str(admin_seed.get("display_name", "系统管理员"))

    logger.info("Seeding baseline data")
    with database.allow_sync():
        individual_user, individual_created = UserModel.get_or_create(
            username=individual_username,
            defaults={
                "password_hash": hash_password(individual_password),
                "role": "individual",
                "display_name": individual_display_name,
                "company_intro": "",
            },
        )
        enterprise_user, enterprise_created = UserModel.get_or_create(
            username=enterprise_username,
            defaults={
                "password_hash": hash_password(enterprise_password),
                "role": "enterprise",
                "display_name": enterprise_display_name,
                "company_intro": enterprise_company_intro,
            },
        )
        _admin_user, admin_created = UserModel.get_or_create(
            username=admin_username,
            defaults={
                "password_hash": hash_password(admin_password),
                "role": "admin",
                "display_name": admin_display_name,
                "company_intro": "",
            },
        )

        actor, actor_created = ActorModel.get_or_create(
            external_id="GL-928374",
            defaults={
                "name": "Su Zheyuan",
                "age": 24,
                "location": "Shanghai",
                "height": 182,
                "bio": "Seed actor for local development.",
                "tags": ["seed", "demo", "featured"],
                "is_published": True,
            },
        )

        styles = [
            {
                "name": "古装魅影",
                "description": "古装叙事风格，强调电影感布光与历史服饰氛围。",
                "preview_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuD00KMgUb0Pckf9vLFC8_RU4BlI3xMCYS05fAaxWQombg-8VnMusIk_SfJCNs51mZ7SxuBB85MYyuA8HkAHVqxgrls1VSCnliNKV_377DH5AI-D8FhjE_E-5n2mjFG_AJibwqJwE2kd6Vf4N_jZleRfUW-1gYLBx-UyetLcO_tx-y0tnfy2KMRYN7gWapcZ2Kje906S1MO9pTNC3eiAxYAyGEmEDSvwdWsyU7Lw4x6L9NFSbPALwLofjPmBk-mPKtGWndQL4XLSDduj",
                "category": "cinematic",
            },
            {
                "name": "现代极简",
                "description": "现代商业人像风格，干净背景与高质感时尚表达。",
                "preview_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuCCZs5TPGFVy7JxseOoRpt8ezORT4adYH1cLjLsfp5HwenWR0EAzvRjQR22wI00LqEbbaqgGEwUtgeEcKoBAtPUwM_dtJiibusH0TJNBU30sYtrvL40xAqi-Ns0c7JLTOV3h72DXvX6Toa22BbBPgoLiTJinqUdqbV99A7QQCry8kajB7T_Va_xaPcJtSlgEhwhJ545kIY4-tCXPMzNs9VZ5Uwqkchx2O96uByo3QsrVZrypve84zqpWcUXqELIEha4NgOjby9qGD7N",
                "category": "commercial",
            },
            {
                "name": "科幻纪元",
                "description": "赛博科幻风格，强调未来科技感与霓虹视觉元素。",
                "preview_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuC7z6PepGrJ0qBZXFAYCy4QFm1wBJZdCOwQCHYnedhZNDcAvQNL4iGlLWGD-tXGIvRQ4RNyEcHcFte2alc8rvInBo2OHqY-XQqyL5hi55R-cqeBUjQReBS18zlAGWumtnG9no_Ltj4CajfiTZ-q388miAWEewFK3PlYjQrYWkj_gTJBLiTShCSSxv9gbyKHWuHIqy6CcJKQ46FHVfRL8GFzafZ7EKhnIX7fo_0sNsgV7ahhNP5Cq9QrsloDNf9fibTGk5NiIMFOCFzI",
                "category": "sci-fi",
            },
            {
                "name": "黑色电影",
                "description": "经典黑色电影质感，强调高反差与戏剧化光影。",
                "preview_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuAiMkiCMGfe655OOompjW1VvTAU0RU3YE8YjQmjzszegWx9nORlWnhZ2Z0Tp_Dp4sxZbX9ZSJfSZOUp4CErcsW2P3p8OdO9Lb3znojkfBDi2h28Hp3low-6kaHCwW8KAS9sesuve6UHV1ihr6h8a3pRcwGht0Vy8ZN5VCrNGbX2lzA6DWpSf_wHKRx0iC6O5MRYRuHwVTB6M-bSkJa0EDkI8af9KgR0QtR969HHnFC4ajnKR1joR43QaVgFaUY2GKyThGWLF2dYU_E1",
                "category": "noir",
            },
            {
                "name": "油画质感",
                "description": "油画纹理风格，突出笔触、颗粒与艺术化色彩。",
                "preview_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuC9ipTxbm-qu6iG2QPAj3nqp4AOHKOW90w-SWgTR1EcK5dwWhFfyX8PJQPzY-B0OfbKxN2sgUtQJqqMKBXbUdMqUoBsQ9VeRE6gkRhc7fkFOz4sxTTopU3Dz1QFbGH05fD8X4y0PqFzcZxDo2LdCx-B4szCAnJHuUosFvTXKctdMun_ymrRWle9pKy63DTN_3mXGJQgmR4JcALzmtYRg8egVqJuPHExwmfjx31EOZvUgNbJvYcNahq54dK1nka59YiPX9SzSsrLJ4RE",
                "category": "oil-painting",
            },
        ]

        style_created_count = 0
        for style in styles:
            model, created = StyleModel.get_or_create(name=style["name"], defaults=style)
            if not created:
                (
                    StyleModel.update(
                        description=style["description"],
                        preview_url=style["preview_url"],
                        category=style["category"],
                    )
                    .where(StyleModel.id == model.id)
                    .execute()
                )
            style_created_count += int(created)

        _, protocol_created = ProtocolModel.get_or_create(
            actor=actor,
            company_name="Glacier Studio",
            title="Seed Portrait Licensing Agreement",
            defaults={
                "content": "This agreement is generated for local development data seeding.",
                "status": "pending",
                "created_at": datetime.now(),
            },
        )

        _, assigned_protocol_created = ProtocolModel.get_or_create(
            enterprise_user=enterprise_user,
            target_user=individual_user,
            title="企业签约样例协议",
            defaults={
                "actor": actor,
                "company_name": enterprise_user.display_name,
                "content": "示例企业向普通用户发起的签约协议，用于本地联调验证。",
                "status": "pending",
                "created_at": datetime.now(),
            },
        )

    summary = {
        "users_created": int(individual_created) + int(enterprise_created) + int(admin_created),
        "actors_created": int(actor_created),
        "styles_created": style_created_count,
        "protocols_created": int(protocol_created) + int(assigned_protocol_created),
    }
    logger.info("Seeding completed summary=%s", summary)
    return summary


def main() -> None:
    setup_logging_config()
    logger.info("Bootstrap started env=%s", get_config("env", "dev"))
    run_migrations()
    connect_database()
    try:
        ensure_tables()
        ensure_bucket()
        summary = seed_data()
    finally:
        if not database.is_closed():
            database.close()
            logger.info("Database connection closed")

    print("Bootstrap completed.")
    print(
        "Created records:"
        f" users={summary['users_created']},"
        f" actors={summary['actors_created']},"
        f" styles={summary['styles_created']},"
        f" protocols={summary['protocols_created']}"
    )


if __name__ == "__main__":
    main()
