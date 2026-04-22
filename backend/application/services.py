from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timedelta
import hashlib
import hmac
from io import BytesIO
import json
import logging
from pathlib import Path
from typing import Any, BinaryIO, List, Optional, TypedDict
import uuid

from PIL import Image, ImageOps

from backend.domain.models import Actor, GeneratedResult, Portrait, Style
from backend.domain.repositories import (
    ActorRepository,
    GeneratedResultRepository,
    PortraitRepository,
    StyleRepository,
)
from backend.application.style_generation import LangChainStyleImageGenerator, StyleReferenceImage
from backend.application.agreement_service import (
    ensure_actor_agreement_signed,
)
from backend.infrastructure.config import settings
from backend.infrastructure.orm_models import (
    ActorModel,
    GeneratedResultModel,
    PortraitAudioAssetModel,
    PortraitComposeJobModel,
    PortraitUploadAssetModel,
    PortraitUploadSessionModel,
    PortraitVideoAssetModel,
    StyleModel,
    UserModel,
    database,
)
from backend.infrastructure.storage import StorageClient


logger = logging.getLogger(__name__)


STYLE_CATALOG_DEFAULTS: list[dict[str, str]] = [
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
    {
        "name": "自定义",
        "description": "手动上传自定义图片，统一管理展示、发布与删除状态。",
        "preview_url": "/style-custom-preview.svg",
        "category": "custom",
    },
]

VIDEO_TYPE_INTRO = "intro"
VIDEO_TYPE_SHOWREEL = "showreel"
VIDEO_TYPE_ALL = (VIDEO_TYPE_INTRO, VIDEO_TYPE_SHOWREEL)
VIDEO_TYPE_LABELS = {
    VIDEO_TYPE_INTRO: "真人自我介绍",
    VIDEO_TYPE_SHOWREEL: "妆造/演戏混剪",
}
THREE_VIEW_MIN_LONG_EDGE_PX = 2000
THREE_VIEW_RAW_TARGET_WIDTHS: dict[str, int] = {
    "grid": 480,
    "card": 720,
}
THREE_VIEW_COMPOSITE_TARGET_WIDTHS: dict[str, int] = {
    "card": 720,
    "detail": 1080,
}
THREE_VIEW_VARIANT_JPEG_QUALITY = 82
THREE_VIEW_AVATAR_SIZE = 320
THREE_VIEW_AVATAR_JPEG_QUALITY = 84


class PortraitUploadPayload(TypedDict):
    data: bytes
    filename: str
    content_type: str


class DirectUploadFileMeta(TypedDict):
    filename: str
    content_type: str
    size: int
    view_angle: str


class DirectUploadTarget(TypedDict):
    view_angle: str
    bucket_name: str
    object_key: str
    source_filename: str
    mime_type: str
    file_size: int
    image_url: str
    upload_url: str
    upload_method: str


class UploadPlanPayload(TypedDict):
    mode: str
    user_id: int
    actor_id: int
    upload_batch_key: str
    expires_at: int
    files: list[dict[str, Any]]


class GeneratedImageVariant(TypedDict):
    key: str
    object_key: str
    width: int
    height: int
    file_size: int
    mime_type: str


class ActorService:
    def __init__(self, actor_repo: ActorRepository):
        self.actor_repo = actor_repo

    async def get_actor(self, actor_id: int) -> Optional[Actor]:
        return await self.actor_repo.get_by_id(actor_id)

    async def list_actors(self, tag: Optional[str] = None) -> List[Actor]:
        return await self.actor_repo.list_actors(tag=tag)


class PortraitService:
    _compose_job_tasks: dict[str, asyncio.Task] = {}
    _compose_job_semaphore: asyncio.Semaphore | None = None

    def __init__(self, portrait_repo: PortraitRepository, storage_client: StorageClient):
        self.portrait_repo = portrait_repo
        self.storage_client = storage_client
        if self.__class__._compose_job_semaphore is None:
            self.__class__._compose_job_semaphore = asyncio.Semaphore(
                max(1, settings.PORTRAIT_COMPOSE_WORKER_CONCURRENCY)
            )
        self.storage_client.ensure_buckets(
            [
                settings.MINIO_BUCKET,
                settings.MINIO_PORTRAIT_RAW_BUCKET,
                settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                settings.MINIO_PORTRAIT_VIDEO_BUCKET,
                settings.MINIO_PORTRAIT_AUDIO_BUCKET,
            ]
        )
        logger.debug(
            "PortraitService initialized with buckets raw=%s generated=%s video=%s audio=%s worker_concurrency=%s",
            settings.MINIO_PORTRAIT_RAW_BUCKET,
            settings.MINIO_PORTRAIT_GENERATED_BUCKET,
            settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            settings.MINIO_PORTRAIT_AUDIO_BUCKET,
            settings.PORTRAIT_COMPOSE_WORKER_CONCURRENCY,
        )

    async def upload_portrait(self, actor_id: int, portrait_type: str, file_data: bytes, filename: str) -> Portrait:
        image_url = await self.storage_client.upload_file(
            f"actors/{actor_id}/{filename}",
            file_data,
            "image/jpeg",
            bucket=settings.MINIO_BUCKET,
        )
        portrait = Portrait(
            id=None,
            actor_id=actor_id,
            image_url=image_url,
            portrait_type=portrait_type,
        )
        logger.info(
            "Single portrait uploaded actor_id=%s portrait_type=%s filename=%s size=%s",
            actor_id,
            portrait_type,
            filename,
            len(file_data),
        )
        return await self.portrait_repo.save(portrait)

    async def get_actor_portraits(self, actor_id: int) -> List[Portrait]:
        return await self.portrait_repo.get_by_actor(actor_id)

    async def prepare_three_view_direct_upload(
        self,
        user_id: int,
        user_display_name: str,
        files: list[DirectUploadFileMeta],
    ) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        if not files:
            raise ValueError("请至少提供一张图片文件。")

        upload_batch_key = uuid.uuid4().hex
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        base_prefix = self._build_portrait_storage_prefix(
            user_id=user_id,
            actor_id=actor_id,
            date_prefix=date_prefix,
            session_key=upload_batch_key,
        )
        uploads: list[DirectUploadTarget] = []
        seen_angles: set[str] = set()

        for file_meta in files:
            angle = str(file_meta.get("view_angle", "")).strip().lower()
            if angle not in {"front", "left", "right"}:
                raise ValueError(f"非法角度: {angle}")
            if angle in seen_angles:
                raise ValueError(f"角度重复: {angle}")
            seen_angles.add(angle)

            filename = str(file_meta.get("filename") or f"{angle}.jpg")
            content_type = str(file_meta.get("content_type") or "application/octet-stream")
            if not content_type.startswith("image/"):
                raise ValueError(f"角度 {angle} 的文件不是图片类型。")

            size = max(0, int(file_meta.get("size", 0)))
            extension = self._guess_extension(filename, content_type, "jpeg")
            object_key = self._build_raw_object_key(base_prefix, angle, extension)
            uploads.append(
                {
                    "view_angle": angle,
                    "bucket_name": settings.MINIO_PORTRAIT_RAW_BUCKET,
                    "object_key": object_key,
                    "source_filename": filename,
                    "mime_type": content_type,
                    "file_size": size,
                    "image_url": f"{settings.MINIO_PORTRAIT_RAW_BUCKET}/{object_key}",
                    "upload_url": self.storage_client.presigned_put_url(
                        object_key,
                        bucket=settings.MINIO_PORTRAIT_RAW_BUCKET,
                        expires=timedelta(seconds=settings.MINIO_PRESIGN_EXPIRES_SECONDS),
                    ),
                    "upload_method": "PUT",
                }
            )

        plan: UploadPlanPayload = {
            "mode": "three_view",
            "user_id": user_id,
            "actor_id": actor_id,
            "upload_batch_key": upload_batch_key,
            "expires_at": int(datetime.now().timestamp()) + settings.UPLOAD_PLAN_EXPIRES_SECONDS,
            "files": uploads,
        }
        plan_token = self._sign_upload_plan(plan)
        logger.info(
            "Prepared three-view direct upload plan user_id=%s actor_id=%s upload_batch_key=%s file_count=%s",
            user_id,
            actor_id,
            upload_batch_key,
            len(uploads),
        )
        return {
            "upload_plan_token": plan_token,
            "upload_batch_key": upload_batch_key,
            "expires_in_seconds": settings.UPLOAD_PLAN_EXPIRES_SECONDS,
            "uploads": uploads,
        }

    async def prepare_video_direct_upload(
        self,
        user_id: int,
        user_display_name: str,
        video_type: str,
        filename: str,
        content_type: str,
        size: int,
    ) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        normalized_video_type = self._normalize_video_type(video_type)
        normalized_content_type = content_type or "application/octet-stream"
        if not normalized_content_type.startswith("video/"):
            raise ValueError("请上传视频文件。")

        extension = Path(filename).suffix.lower().lstrip(".") or "mp4"
        upload_batch_key = uuid.uuid4().hex
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = (
            f"portraits/video/user_{user_id}/actor_{actor_id}/{normalized_video_type}/{date_prefix}/"
            f"{upload_batch_key}.{extension}"
        )
        upload_target = {
            "view_angle": "video",
            "video_type": normalized_video_type,
            "bucket_name": settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            "object_key": object_key,
            "source_filename": filename or f"{normalized_video_type}_video.{extension}",
            "mime_type": normalized_content_type,
            "file_size": max(0, int(size)),
            "image_url": f"{settings.MINIO_PORTRAIT_VIDEO_BUCKET}/{object_key}",
            "upload_url": self.storage_client.presigned_put_url(
                object_key,
                bucket=settings.MINIO_PORTRAIT_VIDEO_BUCKET,
                expires=timedelta(seconds=settings.MINIO_PRESIGN_EXPIRES_SECONDS),
            ),
            "upload_method": "PUT",
        }
        plan: UploadPlanPayload = {
            "mode": "video",
            "user_id": user_id,
            "actor_id": actor_id,
            "upload_batch_key": upload_batch_key,
            "expires_at": int(datetime.now().timestamp()) + settings.UPLOAD_PLAN_EXPIRES_SECONDS,
            "files": [upload_target],
        }
        logger.info(
            "Prepared video direct upload plan user_id=%s actor_id=%s video_type=%s upload_batch_key=%s",
            user_id,
            actor_id,
            normalized_video_type,
            upload_batch_key,
        )
        return {
            "upload_plan_token": self._sign_upload_plan(plan),
            "upload_batch_key": upload_batch_key,
            "expires_in_seconds": settings.UPLOAD_PLAN_EXPIRES_SECONDS,
            "upload": upload_target,
        }

    async def create_three_view_compose_job(
        self,
        user_id: int,
        user_display_name: str,
        upload_plan_token: str,
        reuse_latest_missing: bool,
    ) -> dict[str, Any]:
        _ = user_display_name
        plan = self._verify_upload_plan(upload_plan_token, expected_mode="three_view", expected_user_id=user_id)
        provided_angles = {str(item.get("view_angle", "")).lower() for item in plan["files"]}
        if reuse_latest_missing:
            if not provided_angles:
                raise ValueError("请至少上传一张要替换的图片。")
        elif provided_angles != {"front", "left", "right"}:
            raise ValueError("首次上传必须包含左侧、正面、右侧三张图片。")

        job_key = uuid.uuid4().hex
        with database.allow_sync():
            job = PortraitComposeJobModel.create(
                job_key=job_key,
                actor_id=plan["actor_id"],
                user_id=user_id,
                status="pending",
                request_payload={
                    "upload_plan": plan,
                    "reuse_latest_missing": reuse_latest_missing,
                },
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        self._enqueue_compose_job(job.id, job.job_key)
        logger.info(
            "Compose job created job_key=%s user_id=%s actor_id=%s reuse_latest_missing=%s",
            job_key,
            user_id,
            plan["actor_id"],
            reuse_latest_missing,
        )
        return self._serialize_compose_job(job, result=None)

    async def get_three_view_compose_job(self, user_id: int, job_key: str) -> Optional[dict[str, Any]]:
        with database.allow_sync():
            job = (
                PortraitComposeJobModel.select()
                .where(
                    (PortraitComposeJobModel.job_key == job_key)
                    & (PortraitComposeJobModel.user_id == user_id)
                )
                .first()
            )
            if not job:
                return None

            session = None
            assets: list[PortraitUploadAssetModel] = []
            if job.result_session_id:
                session = PortraitUploadSessionModel.get_or_none(PortraitUploadSessionModel.id == job.result_session_id)
                if session:
                    assets = list(
                        PortraitUploadAssetModel.select()
                        .where(PortraitUploadAssetModel.session_id == session.id)
                        .order_by(PortraitUploadAssetModel.created_at.asc())
                    )

        result = self._serialize_three_view_session(session, assets) if session else None
        return self._serialize_compose_job(job, result=result)

    async def upload_three_view_set(
        self,
        user_id: int,
        user_display_name: str,
        images: dict[str, PortraitUploadPayload],
    ) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        session_key = uuid.uuid4().hex
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        logger.info(
            "Three-view upload started user_id=%s actor_id=%s session_key=%s",
            user_id,
            actor_id,
            session_key,
        )

        source_map: dict[str, dict[str, Any]] = {}
        for angle in ("front", "left", "right"):
            payload = images.get(angle)
            if not payload:
                logger.warning("Three-view upload missing angle user_id=%s actor_id=%s angle=%s", user_id, actor_id, angle)
                raise ValueError(f"Missing required image for angle: {angle}")
            file_data = payload["data"]
            if not file_data:
                logger.warning(
                    "Three-view upload empty file user_id=%s actor_id=%s angle=%s",
                user_id,
                actor_id,
                angle,
            )
                raise ValueError(f"Empty file for angle: {angle}")

            image, width, height, image_format = self._read_image(file_data)
            self._validate_three_view_source_resolution(angle=angle, width=width, height=height)
            extension = self._guess_extension(payload["filename"], payload["content_type"], image_format)
            source_map[angle] = {
                "data": file_data,
                "bucket_name": settings.MINIO_PORTRAIT_RAW_BUCKET,
                "object_key": "",
                "source_filename": payload["filename"] or f"{angle}.{extension}",
                "mime_type": payload["content_type"] or "application/octet-stream",
                "file_size": len(file_data),
                "width": width,
                "height": height,
                "extension": extension,
            }

        assembled = await self._assemble_three_view_assets(
            user_id=user_id,
            actor_id=actor_id,
            session_key=session_key,
            date_prefix=date_prefix,
            source_map=source_map,
        )

        with database.allow_sync():
            now = datetime.now()
            retired = (
                PortraitUploadSessionModel.update(
                    is_current=False,
                    superseded_at=now,
                )
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
                )
                .execute()
            )
            if retired:
                logger.info(
                    "Three-view current session rotated user_id=%s actor_id=%s retired_count=%s",
                    user_id,
                    actor_id,
                    retired,
                )
            session = PortraitUploadSessionModel.create(
                actor_id=actor_id,
                user_id=user_id,
                session_key=session_key,
                is_current=True,
                superseded_at=None,
                composite_bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                composite_object_key=assembled["composite_object_key"],
                composite_image_url=assembled["composite_image_url"],
                composite_preview_bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                composite_preview_object_key=assembled["composite_preview_object_key"],
                composite_preview_image_url=assembled["composite_preview_image_url"],
                composite_preview_file_size=assembled["composite_preview_file_size"],
                composite_variant_map=assembled["composite_variant_map"],
                composite_file_size=assembled["composite_file_size"],
                composite_width=assembled["compose_width"],
                composite_height=assembled["compose_height"],
                avatar_bucket_name=assembled["avatar_bucket_name"],
                avatar_object_key=assembled["avatar_object_key"],
                avatar_image_url=assembled["avatar_image_url"],
                avatar_mime_type=assembled["avatar_mime_type"],
                avatar_width=assembled["avatar_width"],
                avatar_height=assembled["avatar_height"],
                avatar_file_size=assembled["avatar_file_size"],
                avatar_variant_map=assembled["avatar_variant_map"],
                created_at=now,
            )
            assets = [
                PortraitUploadAssetModel.create(
                    session_id=session.id,
                    actor_id=actor_id,
                    user_id=user_id,
                    created_at=now,
                    **record,
                )
                for record in assembled["raw_asset_records"]
            ]

        logger.info(
            "Three-view upload completed user_id=%s actor_id=%s session_id=%s raw_count=%s",
            user_id,
            actor_id,
            session.id,
            len(assets),
        )
        await self._purge_superseded_three_view_versions(user_id=user_id, actor_id=actor_id)
        return self._serialize_three_view_session(session, assets)

    async def list_three_view_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        include_current: bool = False,
    ) -> list[dict[str, Any]]:
        with database.allow_sync():
            condition = PortraitUploadSessionModel.user_id == user_id
            if not include_current:
                condition = condition & PortraitUploadSessionModel.superseded_at.is_null(False)
            sessions = list(
                PortraitUploadSessionModel.select()
                .where(condition)
                .order_by(PortraitUploadSessionModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            if not sessions:
                logger.info(
                    "Three-view history empty user_id=%s limit=%s offset=%s include_current=%s",
                    user_id,
                    limit,
                    offset,
                    include_current,
                )
                return []

            session_ids = [session.id for session in sessions]
            asset_models = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id.in_(session_ids))
                .order_by(PortraitUploadAssetModel.created_at.asc())
            )

        assets_by_session: dict[int, list[PortraitUploadAssetModel]] = {}
        for asset in asset_models:
            assets_by_session.setdefault(asset.session_id, []).append(asset)

        logger.info(
            "Three-view history listed user_id=%s sessions=%s assets=%s limit=%s offset=%s include_current=%s",
            user_id,
            len(sessions),
            len(asset_models),
            limit,
            offset,
            include_current,
        )
        return [
            self._serialize_three_view_session(session, assets_by_session.get(session.id, []))
            for session in sessions
        ]

    async def get_current_three_view(self, user_id: int) -> Optional[dict[str, Any]]:
        with database.allow_sync():
            session = (
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
                )
                .order_by(PortraitUploadSessionModel.created_at.desc())
                .first()
            )
            if not session:
                return None

            assets = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id == session.id)
                .order_by(PortraitUploadAssetModel.created_at.asc())
            )
        return self._serialize_three_view_session(session, assets)

    async def get_three_view_state(self, user_id: int) -> dict[str, Any]:
        with database.allow_sync():
            draft_session = (
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
                )
                .order_by(PortraitUploadSessionModel.created_at.desc())
                .first()
            )
            published_session = (
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.is_current == False)  # noqa: E712
                    & PortraitUploadSessionModel.superseded_at.is_null(True)
                )
                .order_by(PortraitUploadSessionModel.created_at.desc())
                .first()
            )

            target_session_ids = [
                session.id
                for session in (draft_session, published_session)
                if session is not None
            ]
            assets_by_session: dict[int, list[PortraitUploadAssetModel]] = {}
            if target_session_ids:
                raw_assets = list(
                    PortraitUploadAssetModel.select()
                    .where(PortraitUploadAssetModel.session_id.in_(target_session_ids))
                    .order_by(PortraitUploadAssetModel.created_at.asc())
                )
                for asset in raw_assets:
                    assets_by_session.setdefault(asset.session_id, []).append(asset)

        return {
            "draft": (
                self._serialize_three_view_session(
                    draft_session,
                    assets_by_session.get(draft_session.id, []),
                )
                if draft_session
                else None
            ),
            "published": (
                self._serialize_three_view_session(
                    published_session,
                    assets_by_session.get(published_session.id, []),
                )
                if published_session
                else None
            ),
        }

    async def publish_current_three_view(self, user_id: int, user_display_name: str) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        ensure_actor_agreement_signed(actor_id)
        with database.allow_sync():
            now = datetime.now()
            draft_session = (
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
                )
                .order_by(PortraitUploadSessionModel.created_at.desc())
                .first()
            )
            if not draft_session:
                raise ValueError("暂无可发布的三视图草稿，请先上传基础照。")

            (
                PortraitUploadSessionModel.update(superseded_at=now)
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & (PortraitUploadSessionModel.is_current == False)  # noqa: E712
                    & PortraitUploadSessionModel.superseded_at.is_null(True)
                )
                .execute()
            )

            draft_session.is_current = False
            draft_session.superseded_at = None
            draft_session.save()

            (
                ActorModel.update(is_published=True)
                .where(ActorModel.id == actor_id)
                .execute()
            )

            assets = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id == draft_session.id)
                .order_by(PortraitUploadAssetModel.created_at.asc())
            )

        await self._purge_superseded_three_view_versions(user_id=user_id, actor_id=actor_id)
        logger.info(
            "Three-view draft published user_id=%s actor_id=%s session_id=%s",
            user_id,
            actor_id,
            draft_session.id,
        )
        return self._serialize_three_view_session(draft_session, assets)

    async def get_published_three_view_for_actor(self, actor_id: int) -> Optional[dict[str, Any]]:
        with database.allow_sync():
            session = (
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.actor_id == actor_id)
                    & (PortraitUploadSessionModel.is_current == False)  # noqa: E712
                    & PortraitUploadSessionModel.superseded_at.is_null(True)
                )
                .order_by(PortraitUploadSessionModel.created_at.desc())
                .first()
            )
            if not session:
                return None
            assets = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id == session.id)
                .order_by(PortraitUploadAssetModel.created_at.asc())
            )
        return self._serialize_three_view_session(session, assets)

    async def recompose_three_view_set(
        self,
        user_id: int,
        user_display_name: str,
        images: dict[str, PortraitUploadPayload],
    ) -> dict[str, Any]:
        replace_count = sum(1 for angle in ("left", "front", "right") if angle in images)
        if replace_count == 0:
            raise ValueError("请至少上传一张需要替换的图片。")
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)

        with database.allow_sync():
            latest_session = self._get_recompose_base_session(user_id=user_id, actor_id=actor_id)
            if not latest_session:
                raise ValueError("暂无可修改的三视图，请先完成首次上传。")

            latest_assets = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id == latest_session.id)
                .order_by(PortraitUploadAssetModel.created_at.asc())
            )

        existing_map = {asset.view_angle: asset for asset in latest_assets}
        complete_images: dict[str, PortraitUploadPayload] = {}
        for angle in ("front", "left", "right"):
            replacement = images.get(angle)
            if replacement and replacement.get("data"):
                complete_images[angle] = replacement
                continue

            existing = existing_map.get(angle)
            if not existing:
                raise ValueError(f"历史素材缺少角度: {angle}，请重新上传三张图片。")
            download_bucket = existing.bucket_name
            download_object_key = existing.object_key
            if existing.preview_bucket_name and existing.preview_object_key:
                download_bucket = existing.preview_bucket_name
                download_object_key = existing.preview_object_key
            try:
                existing_data = await self.storage_client.download_file(
                    download_object_key,
                    bucket=download_bucket,
                )
            except Exception as exc:
                logger.exception(
                    "Three-view recompose failed to read historical asset user_id=%s session_id=%s angle=%s bucket=%s object_key=%s",
                    user_id,
                    latest_session.id,
                    angle,
                    download_bucket,
                    download_object_key,
                )
                raise ValueError("历史素材读取失败，请重新上传三张图片。") from exc
            complete_images[angle] = {
                "data": existing_data,
                "filename": existing.source_filename,
                "content_type": existing.mime_type,
            }

        logger.info(
            "Three-view recompose started user_id=%s base_session_id=%s replace_count=%s",
            user_id,
            latest_session.id,
            replace_count,
        )
        return await self.upload_three_view_set(
            user_id=user_id,
            user_display_name=user_display_name,
            images=complete_images,
        )

    async def upload_portrait_video(
        self,
        user_id: int,
        user_display_name: str,
        video_type: str,
        file_data: bytes,
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        if not file_data:
            logger.warning("Portrait video upload failed: empty file user_id=%s", user_id)
            raise ValueError("视频文件不能为空。")
        normalized_video_type = self._normalize_video_type(video_type)
        normalized_content_type = content_type or "application/octet-stream"
        if not normalized_content_type.startswith("video/"):
            logger.warning(
                "Portrait video upload failed: invalid content type user_id=%s content_type=%s",
                user_id,
                normalized_content_type,
            )
            raise ValueError("请上传视频文件。")

        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        extension = Path(filename).suffix.lower().lstrip(".") or "mp4"
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = (
            f"portraits/video/user_{user_id}/actor_{actor_id}/{normalized_video_type}/{date_prefix}/"
            f"{uuid.uuid4().hex}.{extension}"
        )
        logger.info(
            "Portrait video upload started user_id=%s actor_id=%s video_type=%s filename=%s size=%s content_type=%s",
            user_id,
            actor_id,
            normalized_video_type,
            filename,
            len(file_data),
            normalized_content_type,
        )
        await self.storage_client.upload_file(
            object_key,
            file_data,
            normalized_content_type,
            bucket=settings.MINIO_PORTRAIT_VIDEO_BUCKET,
        )
        return await self._create_video_asset_record(
            actor_id=actor_id,
            user_id=user_id,
            video_type=normalized_video_type,
            bucket_name=settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            object_key=object_key,
            source_filename=filename or f"{normalized_video_type}_video.{extension}",
            mime_type=normalized_content_type,
            file_size=len(file_data),
        )

    async def upload_portrait_video_stream(
        self,
        user_id: int,
        user_display_name: str,
        video_type: str,
        upload_stream: BinaryIO,
        filename: str,
        content_type: str,
        declared_size: int | None = None,
    ) -> dict[str, Any]:
        normalized_video_type = self._normalize_video_type(video_type)
        normalized_content_type = content_type or "application/octet-stream"
        if not normalized_content_type.startswith("video/"):
            raise ValueError("请上传视频文件。")

        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        extension = Path(filename).suffix.lower().lstrip(".") or "mp4"
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = (
            f"portraits/video/user_{user_id}/actor_{actor_id}/{normalized_video_type}/{date_prefix}/"
            f"{uuid.uuid4().hex}.{extension}"
        )
        size = self._resolve_stream_size(upload_stream, declared_size)
        logger.info(
            "Portrait video stream upload started user_id=%s actor_id=%s video_type=%s filename=%s size=%s content_type=%s",
            user_id,
            actor_id,
            normalized_video_type,
            filename,
            size,
            normalized_content_type,
        )
        await self.storage_client.upload_file_stream(
            object_key,
            upload_stream,
            length=size,
            content_type=normalized_content_type,
            bucket=settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            part_size=settings.STREAM_UPLOAD_PART_SIZE,
        )
        stat = self.storage_client.stat_object(
            object_key,
            bucket=settings.MINIO_PORTRAIT_VIDEO_BUCKET,
        )
        final_size = int(stat.get("size", size if size > 0 else 0))
        return await self._create_video_asset_record(
            actor_id=actor_id,
            user_id=user_id,
            video_type=normalized_video_type,
            bucket_name=settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            object_key=object_key,
            source_filename=filename or f"{normalized_video_type}_video.{extension}",
            mime_type=normalized_content_type,
            file_size=final_size,
        )

    async def commit_video_direct_upload(
        self,
        user_id: int,
        user_display_name: str,
        upload_plan_token: str,
    ) -> dict[str, Any]:
        _ = user_display_name
        plan = self._verify_upload_plan(upload_plan_token, expected_mode="video", expected_user_id=user_id)
        if not plan["files"]:
            raise ValueError("上传计划中没有视频文件。")
        item = dict(plan["files"][0])
        bucket_name = str(item.get("bucket_name"))
        object_key = str(item.get("object_key"))
        source_filename = str(item.get("source_filename") or "portrait_video.mp4")
        mime_type = str(item.get("mime_type") or "application/octet-stream")
        video_type = self._normalize_video_type(str(item.get("video_type") or VIDEO_TYPE_INTRO))

        stat = self.storage_client.stat_object(object_key, bucket=bucket_name)
        file_size = int(stat.get("size", item.get("file_size", 0)) or 0)
        logger.info(
            "Commit video direct upload user_id=%s actor_id=%s video_type=%s bucket=%s object_key=%s size=%s",
            user_id,
            plan["actor_id"],
            video_type,
            bucket_name,
            object_key,
            file_size,
        )
        return await self._create_video_asset_record(
            actor_id=plan["actor_id"],
            user_id=user_id,
            video_type=video_type,
            bucket_name=bucket_name,
            object_key=object_key,
            source_filename=source_filename,
            mime_type=mime_type,
            file_size=file_size,
        )

    async def list_portrait_videos(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        include_current: bool = False,
        video_type: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized_video_type = self._normalize_video_type(video_type) if video_type else None
        with database.allow_sync():
            condition = PortraitVideoAssetModel.user_id == user_id
            if normalized_video_type:
                condition = condition & (PortraitVideoAssetModel.video_type == normalized_video_type)
            if not include_current:
                condition = condition & PortraitVideoAssetModel.superseded_at.is_null(False)
            assets = list(
                PortraitVideoAssetModel.select()
                .where(condition)
                .order_by(PortraitVideoAssetModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        logger.info(
            "Portrait videos listed user_id=%s count=%s limit=%s offset=%s include_current=%s",
            user_id,
            len(assets),
            limit,
            offset,
            include_current,
        )
        return [self._serialize_video_asset(asset) for asset in assets]

    async def get_current_portrait_video(
        self,
        user_id: int,
        video_type: str | None = None,
    ) -> Optional[dict[str, Any]]:
        normalized_video_type = self._normalize_video_type(video_type) if video_type else None
        with database.allow_sync():
            condition = (
                (PortraitVideoAssetModel.user_id == user_id)
                & (PortraitVideoAssetModel.is_current == True)  # noqa: E712
            )
            if normalized_video_type:
                condition = condition & (PortraitVideoAssetModel.video_type == normalized_video_type)
            asset = (
                PortraitVideoAssetModel.select()
                .where(condition)
                .order_by(PortraitVideoAssetModel.created_at.desc())
                .first()
            )
            if not asset:
                return None
        return self._serialize_video_asset(asset)

    async def get_video_state(self, user_id: int) -> dict[str, Any]:
        state: dict[str, dict[str, Optional[dict[str, Any]]]] = {}
        with database.allow_sync():
            for video_type in VIDEO_TYPE_ALL:
                draft = (
                    PortraitVideoAssetModel.select()
                    .where(
                        (PortraitVideoAssetModel.user_id == user_id)
                        & (PortraitVideoAssetModel.video_type == video_type)
                        & (PortraitVideoAssetModel.is_current == True)  # noqa: E712
                    )
                    .order_by(PortraitVideoAssetModel.created_at.desc())
                    .first()
                )
                published = (
                    PortraitVideoAssetModel.select()
                    .where(
                        (PortraitVideoAssetModel.user_id == user_id)
                        & (PortraitVideoAssetModel.video_type == video_type)
                        & (PortraitVideoAssetModel.is_current == False)  # noqa: E712
                        & PortraitVideoAssetModel.superseded_at.is_null(True)
                    )
                    .order_by(PortraitVideoAssetModel.created_at.desc())
                    .first()
                )
                state[video_type] = {
                    "draft": self._serialize_video_asset(draft) if draft else None,
                    "published": self._serialize_video_asset(published) if published else None,
                }
        return {
            "intro": state[VIDEO_TYPE_INTRO],
            "showreel": state[VIDEO_TYPE_SHOWREEL],
            "both_published_ready": all(state[item]["published"] for item in VIDEO_TYPE_ALL),
        }

    async def publish_current_video(self, user_id: int, user_display_name: str, video_type: str) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        ensure_actor_agreement_signed(actor_id)
        normalized_video_type = self._normalize_video_type(video_type)
        with database.allow_sync():
            now = datetime.now()
            draft = (
                PortraitVideoAssetModel.select()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.actor_id == actor_id)
                    & (PortraitVideoAssetModel.video_type == normalized_video_type)
                    & (PortraitVideoAssetModel.is_current == True)  # noqa: E712
                )
                .order_by(PortraitVideoAssetModel.created_at.desc())
                .first()
            )
            if not draft:
                label = VIDEO_TYPE_LABELS.get(normalized_video_type, "该类型")
                raise ValueError(f"暂无可发布的{label}草稿，请先上传视频。")

            (
                PortraitVideoAssetModel.update(superseded_at=now)
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.actor_id == actor_id)
                    & (PortraitVideoAssetModel.video_type == normalized_video_type)
                    & (PortraitVideoAssetModel.is_current == False)  # noqa: E712
                    & PortraitVideoAssetModel.superseded_at.is_null(True)
                )
                .execute()
            )

            draft.is_current = False
            draft.superseded_at = None
            draft.save()

            (
                ActorModel.update(is_published=True)
                .where(ActorModel.id == actor_id)
                .execute()
            )

        await self._purge_superseded_video_versions(user_id=user_id, actor_id=actor_id)
        logger.info(
            "Portrait video draft published user_id=%s actor_id=%s video_type=%s asset_id=%s",
            user_id,
            actor_id,
            normalized_video_type,
            draft.id,
        )
        return self._serialize_video_asset(draft)

    async def get_published_videos_for_actor(self, actor_id: int) -> list[dict[str, Any]]:
        assets: list[PortraitVideoAssetModel] = []
        with database.allow_sync():
            for video_type in VIDEO_TYPE_ALL:
                asset = (
                    PortraitVideoAssetModel.select()
                    .where(
                        (PortraitVideoAssetModel.actor_id == actor_id)
                        & (PortraitVideoAssetModel.video_type == video_type)
                        & (PortraitVideoAssetModel.is_current == False)  # noqa: E712
                        & PortraitVideoAssetModel.superseded_at.is_null(True)
                    )
                    .order_by(PortraitVideoAssetModel.created_at.desc())
                    .first()
                )
                if asset:
                    assets.append(asset)
        return [self._serialize_video_asset(asset) for asset in assets]

    def pick_primary_published_video(self, videos: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        if not videos:
            return None
        by_type = {str(item.get("video_type")): item for item in videos}
        if by_type.get(VIDEO_TYPE_SHOWREEL):
            return by_type[VIDEO_TYPE_SHOWREEL]
        if by_type.get(VIDEO_TYPE_INTRO):
            return by_type[VIDEO_TYPE_INTRO]
        return sorted(videos, key=lambda item: item.get("created_at") or datetime.min, reverse=True)[0]

    async def get_published_video_for_actor(self, actor_id: int) -> Optional[dict[str, Any]]:
        published = await self.get_published_videos_for_actor(actor_id)
        return self.pick_primary_published_video(published)

    async def upload_portrait_audio_stream(
        self,
        user_id: int,
        user_display_name: str,
        upload_stream: BinaryIO,
        filename: str,
        content_type: str,
        declared_size: int | None = None,
    ) -> dict[str, Any]:
        normalized_content_type = content_type or "application/octet-stream"
        if not normalized_content_type.startswith("audio/"):
            raise ValueError("请上传音频文件。")

        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        extension = Path(filename).suffix.lower().lstrip(".") or "mp3"
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = (
            f"portraits/audio/user_{user_id}/actor_{actor_id}/{date_prefix}/"
            f"{uuid.uuid4().hex}.{extension}"
        )
        size = self._resolve_stream_size(upload_stream, declared_size)
        logger.info(
            "Portrait audio stream upload started user_id=%s actor_id=%s filename=%s size=%s content_type=%s",
            user_id,
            actor_id,
            filename,
            size,
            normalized_content_type,
        )
        await self.storage_client.upload_file_stream(
            object_key,
            upload_stream,
            length=size,
            content_type=normalized_content_type,
            bucket=settings.MINIO_PORTRAIT_AUDIO_BUCKET,
            part_size=settings.STREAM_UPLOAD_PART_SIZE,
        )
        stat = self.storage_client.stat_object(
            object_key,
            bucket=settings.MINIO_PORTRAIT_AUDIO_BUCKET,
        )
        final_size = int(stat.get("size", size if size > 0 else 0))
        return await self._create_audio_asset_record(
            actor_id=actor_id,
            user_id=user_id,
            bucket_name=settings.MINIO_PORTRAIT_AUDIO_BUCKET,
            object_key=object_key,
            source_filename=filename or f"portrait_audio.{extension}",
            mime_type=normalized_content_type,
            file_size=final_size,
        )

    async def list_portrait_audios(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        with database.allow_sync():
            assets = list(
                PortraitAudioAssetModel.select()
                .where(
                    (PortraitAudioAssetModel.user_id == user_id)
                    & PortraitAudioAssetModel.superseded_at.is_null(True)
                )
                .order_by(PortraitAudioAssetModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        logger.info(
            "Portrait audios listed user_id=%s count=%s limit=%s offset=%s",
            user_id,
            len(assets),
            limit,
            offset,
        )
        return [self._serialize_audio_asset(asset) for asset in assets]

    async def toggle_portrait_audio_publish(
        self,
        user_id: int,
        user_display_name: str,
        audio_id: int,
        published: bool,
    ) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        if published:
            ensure_actor_agreement_signed(actor_id)
        with database.allow_sync():
            asset = (
                PortraitAudioAssetModel.select()
                .where(
                    (PortraitAudioAssetModel.id == audio_id)
                    & (PortraitAudioAssetModel.user_id == user_id)
                    & (PortraitAudioAssetModel.actor_id == actor_id)
                    & PortraitAudioAssetModel.superseded_at.is_null(True)
                )
                .first()
            )
            if not asset:
                raise ValueError("录音素材不存在或无权限操作。")

            asset.is_published = bool(published)
            asset.save()

            if published:
                (
                    ActorModel.update(is_published=True)
                    .where(ActorModel.id == actor_id)
                    .execute()
                )

        logger.info(
            "Portrait audio publish state changed user_id=%s actor_id=%s audio_id=%s published=%s",
            user_id,
            actor_id,
            audio_id,
            published,
        )
        return self._serialize_audio_asset(asset)

    async def delete_portrait_audio(
        self,
        user_id: int,
        user_display_name: str,
        audio_id: int,
    ) -> None:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        with database.allow_sync():
            asset = (
                PortraitAudioAssetModel.select()
                .where(
                    (PortraitAudioAssetModel.id == audio_id)
                    & (PortraitAudioAssetModel.user_id == user_id)
                    & (PortraitAudioAssetModel.actor_id == actor_id)
                    & PortraitAudioAssetModel.superseded_at.is_null(True)
                )
                .first()
            )
            if not asset:
                raise ValueError("录音素材不存在或已删除。")

            bucket_name = str(asset.bucket_name or "")
            object_key = str(asset.object_key or "")
            asset.delete_instance()

        if bucket_name and object_key:
            try:
                await self.storage_client.remove_object(object_key, bucket=bucket_name)
            except Exception:
                logger.exception(
                    "Failed to delete portrait audio object bucket=%s object_key=%s audio_id=%s",
                    bucket_name,
                    object_key,
                    audio_id,
                )

    async def get_published_audios_for_actor(self, actor_id: int, limit: int = 100) -> list[dict[str, Any]]:
        with database.allow_sync():
            assets = list(
                PortraitAudioAssetModel.select()
                .where(
                    (PortraitAudioAssetModel.actor_id == actor_id)
                    & (PortraitAudioAssetModel.is_published == True)  # noqa: E712
                    & PortraitAudioAssetModel.superseded_at.is_null(True)
                )
                .order_by(PortraitAudioAssetModel.created_at.desc())
                .limit(max(1, limit))
            )
        return [self._serialize_audio_asset(asset) for asset in assets]

    async def cleanup_three_view_history(self, user_id: int, purge_storage: bool = True) -> dict[str, int]:
        with database.allow_sync():
            history_sessions = list(
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & PortraitUploadSessionModel.superseded_at.is_null(False)
                )
            )
            if not history_sessions:
                return {"deleted_records": 0, "deleted_objects": 0, "skipped_objects": 0}

            history_session_ids = [session.id for session in history_sessions]
            history_assets = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id.in_(history_session_ids))
            )

            candidate_objects: set[tuple[str, str]] = {
                (session.composite_bucket, session.composite_object_key)
                for session in history_sessions
            }
            candidate_objects.update(
                (session.composite_preview_bucket, session.composite_preview_object_key)
                for session in history_sessions
                if session.composite_preview_bucket and session.composite_preview_object_key
            )
            candidate_objects.update(
                (session.avatar_bucket_name, session.avatar_object_key)
                for session in history_sessions
                if session.avatar_bucket_name and session.avatar_object_key
            )
            for session in history_sessions:
                session_composite_variants = dict(session.composite_variant_map or {})
                for item in session_composite_variants.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        candidate_objects.add((bucket_name, object_key))
                session_avatar_variants = dict(session.avatar_variant_map or {})
                for item in session_avatar_variants.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        candidate_objects.add((bucket_name, object_key))
            candidate_objects.update(
                (asset.bucket_name, asset.object_key)
                for asset in history_assets
            )
            candidate_objects.update(
                (asset.preview_bucket_name, asset.preview_object_key)
                for asset in history_assets
                if asset.preview_bucket_name and asset.preview_object_key
            )
            for asset in history_assets:
                variant_map = dict(asset.variant_map or {})
                for item in variant_map.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        candidate_objects.add((bucket_name, object_key))

            deletable_objects = set(candidate_objects)
            skipped_objects = set()
            if purge_storage and candidate_objects:
                in_use_sessions = list(
                    PortraitUploadSessionModel.select(
                        PortraitUploadSessionModel.composite_bucket,
                        PortraitUploadSessionModel.composite_object_key,
                        PortraitUploadSessionModel.composite_preview_bucket,
                        PortraitUploadSessionModel.composite_preview_object_key,
                        PortraitUploadSessionModel.avatar_bucket_name,
                        PortraitUploadSessionModel.avatar_object_key,
                        PortraitUploadSessionModel.composite_variant_map,
                        PortraitUploadSessionModel.avatar_variant_map,
                    ).where(
                        (PortraitUploadSessionModel.user_id == user_id)
                        & (~(PortraitUploadSessionModel.id.in_(history_session_ids)))
                    )
                )
                in_use_objects: set[tuple[str, str]] = {
                    (session.composite_bucket, session.composite_object_key)
                    for session in in_use_sessions
                }
                for session in in_use_sessions:
                    if session.composite_preview_bucket and session.composite_preview_object_key:
                        in_use_objects.add((session.composite_preview_bucket, session.composite_preview_object_key))
                    if session.avatar_bucket_name and session.avatar_object_key:
                        in_use_objects.add((session.avatar_bucket_name, session.avatar_object_key))
                    composite_variant_map = dict(session.composite_variant_map or {})
                    for item in composite_variant_map.values():
                        if not isinstance(item, dict):
                            continue
                        bucket_name = str(item.get("bucket_name") or "")
                        object_key = str(item.get("object_key") or "")
                        if bucket_name and object_key:
                            in_use_objects.add((bucket_name, object_key))
                    avatar_variant_map = dict(session.avatar_variant_map or {})
                    for item in avatar_variant_map.values():
                        if not isinstance(item, dict):
                            continue
                        bucket_name = str(item.get("bucket_name") or "")
                        object_key = str(item.get("object_key") or "")
                        if bucket_name and object_key:
                            in_use_objects.add((bucket_name, object_key))
                in_use_assets = list(
                    PortraitUploadAssetModel.select(
                        PortraitUploadAssetModel.bucket_name,
                        PortraitUploadAssetModel.object_key,
                        PortraitUploadAssetModel.preview_bucket_name,
                        PortraitUploadAssetModel.preview_object_key,
                        PortraitUploadAssetModel.variant_map,
                    ).where(
                        (PortraitUploadAssetModel.user_id == user_id)
                        & (~(PortraitUploadAssetModel.session_id.in_(history_session_ids)))
                    )
                )
                in_use_objects.update((asset.bucket_name, asset.object_key) for asset in in_use_assets)
                for asset in in_use_assets:
                    if asset.preview_bucket_name and asset.preview_object_key:
                        in_use_objects.add((asset.preview_bucket_name, asset.preview_object_key))
                    variant_map = dict(asset.variant_map or {})
                    for item in variant_map.values():
                        if not isinstance(item, dict):
                            continue
                        bucket_name = str(item.get("bucket_name") or "")
                        object_key = str(item.get("object_key") or "")
                        if bucket_name and object_key:
                            in_use_objects.add((bucket_name, object_key))
                skipped_objects = candidate_objects & in_use_objects
                deletable_objects = candidate_objects - in_use_objects

            # Historical sessions may still be referenced by completed compose jobs.
            # Detach the nullable FK before deleting history sessions.
            (
                PortraitComposeJobModel.update(result_session_id=None)
                .where(PortraitComposeJobModel.result_session_id.in_(history_session_ids))
                .execute()
            )

            deleted_records = (
                PortraitUploadSessionModel.delete()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & PortraitUploadSessionModel.superseded_at.is_null(False)
                )
                .execute()
            )

        deleted_objects = 0
        if purge_storage and deletable_objects:
            deleted_objects = await self._remove_storage_objects(deletable_objects)

        logger.info(
            "Three-view history cleanup completed user_id=%s deleted_sessions=%s deleted_objects=%s skipped_objects=%s",
            user_id,
            deleted_records,
            deleted_objects,
            len(skipped_objects),
        )
        return {
            "deleted_records": int(deleted_records),
            "deleted_objects": int(deleted_objects),
            "skipped_objects": int(len(skipped_objects)),
        }

    async def backfill_three_view_variants(
        self,
        *,
        user_id: int | None = None,
        actor_id: int | None = None,
        limit: int = 0,
        dry_run: bool = False,
        force: bool = False,
    ) -> dict[str, int]:
        max_limit = max(0, int(limit or 0))
        with database.allow_sync():
            condition = PortraitUploadSessionModel.id > 0
            if user_id is not None:
                condition = condition & (PortraitUploadSessionModel.user_id == int(user_id))
            if actor_id is not None:
                condition = condition & (PortraitUploadSessionModel.actor_id == int(actor_id))

            query = (
                PortraitUploadSessionModel.select()
                .where(condition)
                .order_by(PortraitUploadSessionModel.created_at.asc())
            )
            if max_limit > 0:
                query = query.limit(max_limit)
            sessions = list(query)

            if not sessions:
                return {
                    "scanned_sessions": 0,
                    "updated_sessions": 0,
                    "skipped_sessions": 0,
                    "failed_sessions": 0,
                    "scanned_assets": 0,
                    "updated_assets": 0,
                }

            session_ids = [session.id for session in sessions]
            assets = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id.in_(session_ids))
                .order_by(PortraitUploadAssetModel.created_at.asc())
            )

        assets_by_session: dict[int, list[PortraitUploadAssetModel]] = {}
        for asset in assets:
            assets_by_session.setdefault(asset.session_id, []).append(asset)

        summary = {
            "scanned_sessions": len(sessions),
            "updated_sessions": 0,
            "skipped_sessions": 0,
            "failed_sessions": 0,
            "scanned_assets": len(assets),
            "updated_assets": 0,
        }

        for session in sessions:
            session_assets = assets_by_session.get(session.id, [])
            try:
                session_changed, updated_asset_count = await self._backfill_single_three_view_session(
                    session=session,
                    assets=session_assets,
                    dry_run=dry_run,
                    force=force,
                )
            except Exception:
                summary["failed_sessions"] += 1
                logger.exception(
                    "Three-view historical backfill failed session_id=%s user_id=%s actor_id=%s",
                    session.id,
                    session.user_id,
                    session.actor_id,
                )
                continue

            if session_changed:
                summary["updated_sessions"] += 1
                summary["updated_assets"] += int(updated_asset_count)
            else:
                summary["skipped_sessions"] += 1

        logger.info(
            "Three-view historical backfill finished dry_run=%s force=%s scanned_sessions=%s updated_sessions=%s skipped_sessions=%s failed_sessions=%s scanned_assets=%s updated_assets=%s",
            dry_run,
            force,
            summary["scanned_sessions"],
            summary["updated_sessions"],
            summary["skipped_sessions"],
            summary["failed_sessions"],
            summary["scanned_assets"],
            summary["updated_assets"],
        )
        return summary

    async def _backfill_single_three_view_session(
        self,
        *,
        session: PortraitUploadSessionModel,
        assets: list[PortraitUploadAssetModel],
        dry_run: bool,
        force: bool,
    ) -> tuple[bool, int]:
        asset_by_angle = {str(asset.view_angle or "").lower(): asset for asset in assets}
        missing_angles = [angle for angle in ("front", "left", "right") if angle not in asset_by_angle]
        if missing_angles:
            logger.warning(
                "Skip historical backfill due to missing angles session_id=%s missing=%s",
                session.id,
                ",".join(missing_angles),
            )
            return False, 0

        if not force and not self._session_requires_backfill(session=session, assets=assets):
            return False, 0

        date_prefix = (session.created_at or datetime.now()).strftime("%Y/%m/%d")

        normalized_source_map: dict[str, dict[str, Any]] = {}
        for angle in ("front", "left", "right"):
            source_asset = asset_by_angle[angle]
            source_data, source_bucket_name, source_object_key = await self._load_backfill_source_bytes(source_asset)
            image, width, height, image_format = self._read_image(source_data)
            extension = self._guess_extension(
                str(source_asset.source_filename or f"{angle}.jpg"),
                str(source_asset.mime_type or "application/octet-stream"),
                image_format,
            )
            normalized_source_map[angle] = {
                "data": source_data,
                "bucket_name": source_bucket_name,
                "object_key": source_object_key,
                "image_url": source_asset.image_url,
                "source_filename": source_asset.source_filename,
                "mime_type": source_asset.mime_type,
                "file_size": int(source_asset.file_size or len(source_data)),
                "width": int(source_asset.width or width),
                "height": int(source_asset.height or height),
                "extension": extension,
            }

        if dry_run:
            logger.info(
                "Three-view historical backfill dry-run session_id=%s user_id=%s actor_id=%s",
                session.id,
                session.user_id,
                session.actor_id,
            )
            return True, 0

        assembled = await self._assemble_three_view_assets(
            user_id=int(session.user_id),
            actor_id=int(session.actor_id),
            session_key=str(session.session_key),
            date_prefix=date_prefix,
            source_map=normalized_source_map,
        )

        updated_assets = 0
        with database.allow_sync():
            session_model = PortraitUploadSessionModel.get_or_none(PortraitUploadSessionModel.id == session.id)
            if not session_model:
                logger.warning(
                    "Skip backfill persistence because session was removed session_id=%s",
                    session.id,
                )
                return False, 0

            raw_records_by_angle = {
                str(item.get("view_angle") or "").lower(): item
                for item in assembled.get("raw_asset_records", [])
                if isinstance(item, dict)
            }

            for angle in ("front", "left", "right"):
                source_asset = asset_by_angle[angle]
                generated = raw_records_by_angle.get(angle)
                if not generated:
                    continue
                source_asset.preview_bucket_name = str(generated.get("preview_bucket_name") or "")
                source_asset.preview_object_key = str(generated.get("preview_object_key") or "")
                source_asset.preview_image_url = str(generated.get("preview_image_url") or "")
                source_asset.preview_mime_type = str(generated.get("preview_mime_type") or "")
                source_asset.preview_width = int(generated.get("preview_width") or 0)
                source_asset.preview_height = int(generated.get("preview_height") or 0)
                source_asset.preview_file_size = int(generated.get("preview_file_size") or 0)
                source_asset.variant_map = dict(generated.get("variant_map") or {})
                source_asset.save()
                updated_assets += 1

            session_model.composite_bucket = settings.MINIO_PORTRAIT_GENERATED_BUCKET
            session_model.composite_object_key = str(assembled.get("composite_object_key") or "")
            session_model.composite_image_url = str(assembled.get("composite_image_url") or "")
            session_model.composite_file_size = int(assembled.get("composite_file_size") or 0)
            session_model.composite_width = int(assembled.get("compose_width") or session_model.composite_width or 0)
            session_model.composite_height = int(assembled.get("compose_height") or session_model.composite_height or 0)
            session_model.composite_preview_bucket = settings.MINIO_PORTRAIT_GENERATED_BUCKET
            session_model.composite_preview_object_key = str(assembled.get("composite_preview_object_key") or "")
            session_model.composite_preview_image_url = str(assembled.get("composite_preview_image_url") or "")
            session_model.composite_preview_file_size = int(assembled.get("composite_preview_file_size") or 0)
            session_model.composite_variant_map = dict(assembled.get("composite_variant_map") or {})

            session_model.avatar_bucket_name = str(assembled.get("avatar_bucket_name") or "")
            session_model.avatar_object_key = str(assembled.get("avatar_object_key") or "")
            session_model.avatar_image_url = str(assembled.get("avatar_image_url") or "")
            session_model.avatar_mime_type = str(assembled.get("avatar_mime_type") or "")
            session_model.avatar_width = int(assembled.get("avatar_width") or 0)
            session_model.avatar_height = int(assembled.get("avatar_height") or 0)
            session_model.avatar_file_size = int(assembled.get("avatar_file_size") or 0)
            session_model.avatar_variant_map = dict(assembled.get("avatar_variant_map") or {})

            session_model.save()

        logger.info(
            "Three-view historical backfill persisted session_id=%s user_id=%s actor_id=%s updated_assets=%s",
            session.id,
            session.user_id,
            session.actor_id,
            updated_assets,
        )
        return True, updated_assets

    async def _load_backfill_source_bytes(
        self,
        asset: PortraitUploadAssetModel,
    ) -> tuple[bytes, str, str]:
        candidates: list[tuple[str, str]] = []
        raw_bucket = str(asset.bucket_name or "")
        raw_key = str(asset.object_key or "")
        if raw_bucket and raw_key:
            candidates.append((raw_bucket, raw_key))
        preview_bucket = str(asset.preview_bucket_name or "")
        preview_key = str(asset.preview_object_key or "")
        if preview_bucket and preview_key:
            candidates.append((preview_bucket, preview_key))

        last_error: Exception | None = None
        for bucket_name, object_key in candidates:
            try:
                payload = await self.storage_client.download_file(object_key, bucket=bucket_name)
                if payload:
                    return payload, bucket_name, object_key
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Historical source download failed session_id=%s asset_id=%s angle=%s bucket=%s object_key=%s",
                    asset.session_id,
                    asset.id,
                    asset.view_angle,
                    bucket_name,
                    object_key,
                )

        if last_error is not None:
            raise last_error
        raise ValueError(f"无法读取历史素材：session={asset.session_id} asset={asset.id} angle={asset.view_angle}")

    def _session_requires_backfill(
        self,
        *,
        session: PortraitUploadSessionModel,
        assets: list[PortraitUploadAssetModel],
    ) -> bool:
        for asset in assets:
            if not str(asset.preview_object_key or ""):
                return True
            if not str(asset.preview_bucket_name or ""):
                return True
            if int(asset.preview_width or 0) <= 0 or int(asset.preview_height or 0) <= 0:
                return True
            if int(asset.preview_file_size or 0) <= 0:
                return True
            variant_map = dict(asset.variant_map or {})
            if not variant_map:
                return True
            for variant_key in THREE_VIEW_RAW_TARGET_WIDTHS.keys():
                item = variant_map.get(variant_key)
                if not isinstance(item, dict):
                    return True
                if not str(item.get("object_key") or "") or not str(item.get("bucket_name") or ""):
                    return True

        if not str(session.composite_preview_object_key or ""):
            return True
        if not str(session.composite_preview_bucket or ""):
            return True
        if int(session.composite_preview_file_size or 0) <= 0:
            return True

        composite_variant_map = dict(session.composite_variant_map or {})
        for variant_key in THREE_VIEW_COMPOSITE_TARGET_WIDTHS.keys():
            item = composite_variant_map.get(variant_key)
            if not isinstance(item, dict):
                return True
            if not str(item.get("object_key") or "") or not str(item.get("bucket_name") or ""):
                return True

        if not str(session.avatar_object_key or ""):
            return True
        if not str(session.avatar_bucket_name or ""):
            return True
        if int(session.avatar_width or 0) <= 0 or int(session.avatar_height or 0) <= 0:
            return True
        if int(session.avatar_file_size or 0) <= 0:
            return True

        avatar_variant_map = dict(session.avatar_variant_map or {})
        for variant_key in ("thumb", "profile"):
            item = avatar_variant_map.get(variant_key)
            if not isinstance(item, dict):
                return True
            if not str(item.get("object_key") or "") or not str(item.get("bucket_name") or ""):
                return True

        return False

    async def cleanup_video_history(self, user_id: int, purge_storage: bool = True) -> dict[str, int]:
        with database.allow_sync():
            history_assets = list(
                PortraitVideoAssetModel.select()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & PortraitVideoAssetModel.superseded_at.is_null(False)
                )
            )
            if not history_assets:
                return {"deleted_records": 0, "deleted_objects": 0, "skipped_objects": 0}

            history_ids = [asset.id for asset in history_assets]
            candidate_objects: set[tuple[str, str]] = {
                (asset.bucket_name, asset.object_key)
                for asset in history_assets
            }

            deletable_objects = set(candidate_objects)
            skipped_objects = set()
            if purge_storage and candidate_objects:
                in_use_objects: set[tuple[str, str]] = {
                    (asset.bucket_name, asset.object_key)
                    for asset in PortraitVideoAssetModel.select(
                        PortraitVideoAssetModel.bucket_name,
                        PortraitVideoAssetModel.object_key,
                    ).where(
                        (PortraitVideoAssetModel.user_id == user_id)
                        & (~(PortraitVideoAssetModel.id.in_(history_ids)))
                    )
                }
                skipped_objects = candidate_objects & in_use_objects
                deletable_objects = candidate_objects - in_use_objects

            deleted_records = (
                PortraitVideoAssetModel.delete()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & PortraitVideoAssetModel.superseded_at.is_null(False)
                )
                .execute()
            )

        deleted_objects = 0
        if purge_storage and deletable_objects:
            deleted_objects = await self._remove_storage_objects(deletable_objects)

        logger.info(
            "Portrait video history cleanup completed user_id=%s deleted_records=%s deleted_objects=%s skipped_objects=%s",
            user_id,
            deleted_records,
            deleted_objects,
            len(skipped_objects),
        )
        return {
            "deleted_records": int(deleted_records),
            "deleted_objects": int(deleted_objects),
            "skipped_objects": int(len(skipped_objects)),
        }

    async def _purge_superseded_three_view_versions(self, user_id: int, actor_id: int) -> dict[str, int]:
        with database.allow_sync():
            superseded_sessions = list(
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & PortraitUploadSessionModel.superseded_at.is_null(False)
                )
            )
            if not superseded_sessions:
                return {"deleted_records": 0, "deleted_objects": 0, "skipped_objects": 0}

            session_ids = [session.id for session in superseded_sessions]
            superseded_assets = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id.in_(session_ids))
            )

            candidate_objects: set[tuple[str, str]] = {
                (session.composite_bucket, session.composite_object_key)
                for session in superseded_sessions
            }
            candidate_objects.update(
                (session.composite_preview_bucket, session.composite_preview_object_key)
                for session in superseded_sessions
                if session.composite_preview_bucket and session.composite_preview_object_key
            )
            candidate_objects.update(
                (session.avatar_bucket_name, session.avatar_object_key)
                for session in superseded_sessions
                if session.avatar_bucket_name and session.avatar_object_key
            )
            for session in superseded_sessions:
                composite_variant_map = dict(session.composite_variant_map or {})
                for item in composite_variant_map.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        candidate_objects.add((bucket_name, object_key))
                avatar_variant_map = dict(session.avatar_variant_map or {})
                for item in avatar_variant_map.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        candidate_objects.add((bucket_name, object_key))
            candidate_objects.update(
                (asset.bucket_name, asset.object_key)
                for asset in superseded_assets
            )
            candidate_objects.update(
                (asset.preview_bucket_name, asset.preview_object_key)
                for asset in superseded_assets
                if asset.preview_bucket_name and asset.preview_object_key
            )
            for asset in superseded_assets:
                variant_map = dict(asset.variant_map or {})
                for item in variant_map.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        candidate_objects.add((bucket_name, object_key))

            in_use_sessions = list(
                PortraitUploadSessionModel.select(
                    PortraitUploadSessionModel.composite_bucket,
                    PortraitUploadSessionModel.composite_object_key,
                    PortraitUploadSessionModel.composite_preview_bucket,
                    PortraitUploadSessionModel.composite_preview_object_key,
                    PortraitUploadSessionModel.avatar_bucket_name,
                    PortraitUploadSessionModel.avatar_object_key,
                    PortraitUploadSessionModel.composite_variant_map,
                    PortraitUploadSessionModel.avatar_variant_map,
                ).where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & (~(PortraitUploadSessionModel.id.in_(session_ids)))
                )
            )
            in_use_objects: set[tuple[str, str]] = {
                (session.composite_bucket, session.composite_object_key)
                for session in in_use_sessions
            }
            for session in in_use_sessions:
                if session.composite_preview_bucket and session.composite_preview_object_key:
                    in_use_objects.add((session.composite_preview_bucket, session.composite_preview_object_key))
                if session.avatar_bucket_name and session.avatar_object_key:
                    in_use_objects.add((session.avatar_bucket_name, session.avatar_object_key))
                composite_variant_map = dict(session.composite_variant_map or {})
                for item in composite_variant_map.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        in_use_objects.add((bucket_name, object_key))
                avatar_variant_map = dict(session.avatar_variant_map or {})
                for item in avatar_variant_map.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        in_use_objects.add((bucket_name, object_key))
            in_use_assets = list(
                PortraitUploadAssetModel.select(
                    PortraitUploadAssetModel.bucket_name,
                    PortraitUploadAssetModel.object_key,
                    PortraitUploadAssetModel.preview_bucket_name,
                    PortraitUploadAssetModel.preview_object_key,
                    PortraitUploadAssetModel.variant_map,
                ).where(
                    (PortraitUploadAssetModel.user_id == user_id)
                    & (PortraitUploadAssetModel.actor_id == actor_id)
                    & (~(PortraitUploadAssetModel.session_id.in_(session_ids)))
                )
            )
            in_use_objects.update((asset.bucket_name, asset.object_key) for asset in in_use_assets)
            for asset in in_use_assets:
                if asset.preview_bucket_name and asset.preview_object_key:
                    in_use_objects.add((asset.preview_bucket_name, asset.preview_object_key))
                variant_map = dict(asset.variant_map or {})
                for item in variant_map.values():
                    if not isinstance(item, dict):
                        continue
                    bucket_name = str(item.get("bucket_name") or "")
                    object_key = str(item.get("object_key") or "")
                    if bucket_name and object_key:
                        in_use_objects.add((bucket_name, object_key))

            skipped_objects = candidate_objects & in_use_objects
            deletable_objects = candidate_objects - in_use_objects

            (
                PortraitComposeJobModel.update(result_session_id=None)
                .where(PortraitComposeJobModel.result_session_id.in_(session_ids))
                .execute()
            )

            deleted_records = (
                PortraitUploadSessionModel.delete()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & PortraitUploadSessionModel.superseded_at.is_null(False)
                )
                .execute()
            )

        deleted_objects = 0
        if deletable_objects:
            deleted_objects = await self._remove_storage_objects(deletable_objects)

        logger.info(
            "Superseded three-view versions purged user_id=%s actor_id=%s deleted_records=%s deleted_objects=%s skipped_objects=%s",
            user_id,
            actor_id,
            deleted_records,
            deleted_objects,
            len(skipped_objects),
        )
        return {
            "deleted_records": int(deleted_records),
            "deleted_objects": int(deleted_objects),
            "skipped_objects": int(len(skipped_objects)),
        }

    async def _purge_superseded_video_versions(self, user_id: int, actor_id: int) -> dict[str, int]:
        with database.allow_sync():
            superseded_assets = list(
                PortraitVideoAssetModel.select()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.actor_id == actor_id)
                    & PortraitVideoAssetModel.superseded_at.is_null(False)
                )
            )
            if not superseded_assets:
                return {"deleted_records": 0, "deleted_objects": 0, "skipped_objects": 0}

            asset_ids = [asset.id for asset in superseded_assets]
            candidate_objects: set[tuple[str, str]] = {
                (asset.bucket_name, asset.object_key)
                for asset in superseded_assets
            }
            in_use_objects: set[tuple[str, str]] = {
                (asset.bucket_name, asset.object_key)
                for asset in PortraitVideoAssetModel.select(
                    PortraitVideoAssetModel.bucket_name,
                    PortraitVideoAssetModel.object_key,
                ).where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.actor_id == actor_id)
                    & (~(PortraitVideoAssetModel.id.in_(asset_ids)))
                )
            }

            skipped_objects = candidate_objects & in_use_objects
            deletable_objects = candidate_objects - in_use_objects

            deleted_records = (
                PortraitVideoAssetModel.delete()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.actor_id == actor_id)
                    & PortraitVideoAssetModel.superseded_at.is_null(False)
                )
                .execute()
            )

        deleted_objects = 0
        if deletable_objects:
            deleted_objects = await self._remove_storage_objects(deletable_objects)

        logger.info(
            "Superseded portrait videos purged user_id=%s actor_id=%s deleted_records=%s deleted_objects=%s skipped_objects=%s",
            user_id,
            actor_id,
            deleted_records,
            deleted_objects,
            len(skipped_objects),
        )
        return {
            "deleted_records": int(deleted_records),
            "deleted_objects": int(deleted_objects),
            "skipped_objects": int(len(skipped_objects)),
        }

    async def _remove_storage_objects(self, objects: set[tuple[str, str]]) -> int:
        deleted = 0
        for bucket_name, object_key in sorted(objects):
            try:
                await self.storage_client.remove_object(object_key, bucket=bucket_name)
                deleted += 1
            except Exception:
                logger.exception(
                    "Failed to purge historical object bucket=%s object_key=%s",
                    bucket_name,
                    object_key,
                )
        return deleted

    async def _create_video_asset_record(
        self,
        actor_id: int,
        user_id: int,
        video_type: str,
        bucket_name: str,
        object_key: str,
        source_filename: str,
        mime_type: str,
        file_size: int,
    ) -> dict[str, Any]:
        normalized_video_type = self._normalize_video_type(video_type)
        video_url = f"{bucket_name}/{object_key}"
        with database.allow_sync():
            now = datetime.now()
            retired = (
                PortraitVideoAssetModel.update(
                    is_current=False,
                    superseded_at=now,
                )
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.actor_id == actor_id)
                    & (PortraitVideoAssetModel.video_type == normalized_video_type)
                    & (PortraitVideoAssetModel.is_current == True)  # noqa: E712
                )
                .execute()
            )
            if retired:
                logger.info(
                    "Portrait video current asset rotated user_id=%s actor_id=%s video_type=%s retired_count=%s",
                    user_id,
                    actor_id,
                    normalized_video_type,
                    retired,
                )
            asset = PortraitVideoAssetModel.create(
                actor_id=actor_id,
                user_id=user_id,
                video_type=normalized_video_type,
                is_current=True,
                superseded_at=None,
                bucket_name=bucket_name,
                object_key=object_key,
                video_url=video_url,
                source_filename=source_filename,
                mime_type=mime_type,
                file_size=file_size,
                created_at=now,
            )
        logger.info(
            "Portrait video asset persisted user_id=%s actor_id=%s video_type=%s asset_id=%s bucket=%s object_key=%s",
            user_id,
            actor_id,
            normalized_video_type,
            asset.id,
            bucket_name,
            object_key,
        )
        await self._purge_superseded_video_versions(user_id=user_id, actor_id=actor_id)
        return self._serialize_video_asset(asset)

    def _normalize_video_type(self, video_type: str | None) -> str:
        normalized = str(video_type or "").strip().lower()
        if normalized not in VIDEO_TYPE_ALL:
            raise ValueError("视频类型非法，仅支持 intro 或 showreel。")
        return normalized

    def _resolve_stream_size(self, upload_stream: BinaryIO, declared_size: int | None) -> int:
        if declared_size is not None and declared_size > 0:
            return int(declared_size)
        if not hasattr(upload_stream, "seek") or not hasattr(upload_stream, "tell"):
            return -1
        upload_stream.seek(0, 2)
        size = upload_stream.tell()
        upload_stream.seek(0)
        return int(size) if size > 0 else -1

    def _sign_upload_plan(self, payload: UploadPlanPayload) -> str:
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(
            settings.UPLOAD_PLAN_SECRET.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8")
        return f"{encoded_payload}.{signature}"

    def _verify_upload_plan(
        self,
        token: str,
        expected_mode: str,
        expected_user_id: int,
    ) -> UploadPlanPayload:
        try:
            encoded_payload, signature = token.split(".", 1)
            payload_bytes = base64.urlsafe_b64decode(encoded_payload.encode("utf-8"))
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as exc:
            raise ValueError("上传计划无效，请重新上传。") from exc

        expected_signature = hmac.new(
            settings.UPLOAD_PLAN_SECRET.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            raise ValueError("上传计划签名校验失败，请重新上传。")

        if payload.get("mode") != expected_mode:
            raise ValueError("上传计划类型不匹配。")
        if int(payload.get("user_id", -1)) != expected_user_id:
            raise ValueError("上传计划用户不匹配。")
        if int(payload.get("expires_at", 0)) < int(datetime.now().timestamp()):
            raise ValueError("上传计划已过期，请重新上传。")
        files = payload.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("上传计划文件为空。")
        return payload  # type: ignore[return-value]

    def _enqueue_compose_job(self, job_id: int, job_key: str) -> None:
        async def _runner() -> None:
            try:
                await self._run_compose_job(job_id=job_id, job_key=job_key)
            finally:
                self.__class__._compose_job_tasks.pop(job_key, None)

        task = asyncio.create_task(_runner(), name=f"portrait-compose-{job_key}")
        self.__class__._compose_job_tasks[job_key] = task

    async def _run_compose_job(self, job_id: int, job_key: str) -> None:
        semaphore = self.__class__._compose_job_semaphore
        assert semaphore is not None

        async with semaphore:
            with database.allow_sync():
                job = PortraitComposeJobModel.get_or_none(PortraitComposeJobModel.id == job_id)
                if not job:
                    logger.warning("Compose job not found job_id=%s job_key=%s", job_id, job_key)
                    return
                job.status = "processing"
                job.updated_at = datetime.now()
                job.error_message = None
                job.save()

            try:
                session, assets = await self._compose_session_from_job(job)
            except Exception as exc:
                logger.exception("Compose job failed job_key=%s", job_key)
                with database.allow_sync():
                    failed_job = PortraitComposeJobModel.get_or_none(PortraitComposeJobModel.id == job_id)
                    if failed_job:
                        failed_job.status = "failed"
                        failed_job.error_message = str(exc)
                        failed_job.updated_at = datetime.now()
                        failed_job.save()
                return

            with database.allow_sync():
                completed_job = PortraitComposeJobModel.get_or_none(PortraitComposeJobModel.id == job_id)
                if completed_job:
                    completed_job.status = "completed"
                    completed_job.result_session_id = session.id
                    completed_job.updated_at = datetime.now()
                    completed_job.save()
            logger.info(
                "Compose job completed job_key=%s session_id=%s raw_count=%s",
                job_key,
                session.id,
                len(assets),
            )

    async def _compose_session_from_job(
        self,
        job: PortraitComposeJobModel,
    ) -> tuple[PortraitUploadSessionModel, list[PortraitUploadAssetModel]]:
        request_payload = dict(job.request_payload or {})
        upload_plan = dict(request_payload.get("upload_plan") or {})
        reuse_latest_missing = bool(request_payload.get("reuse_latest_missing", False))
        files = upload_plan.get("files") or []
        provided: dict[str, dict[str, Any]] = {
            str(item.get("view_angle", "")).lower(): dict(item)
            for item in files
        }

        latest_assets_by_angle: dict[str, PortraitUploadAssetModel] = {}
        if reuse_latest_missing:
            with database.allow_sync():
                latest_session = self._get_recompose_base_session(user_id=job.user_id, actor_id=job.actor_id)
                if latest_session:
                    latest_assets = list(
                        PortraitUploadAssetModel.select()
                        .where(PortraitUploadAssetModel.session_id == latest_session.id)
                        .order_by(PortraitUploadAssetModel.created_at.asc())
                    )
                    latest_assets_by_angle = {asset.view_angle: asset for asset in latest_assets}

        source_map: dict[str, dict[str, Any]] = {}
        for angle in ("front", "left", "right"):
            if angle in provided:
                item = provided[angle]
                bucket_name = str(item.get("bucket_name", settings.MINIO_PORTRAIT_RAW_BUCKET))
                object_key = str(item.get("object_key"))
                if not object_key:
                    raise ValueError(f"角度 {angle} 缺少对象路径。")
                # Validate that uploaded object exists before composing.
                stat = self.storage_client.stat_object(object_key, bucket=bucket_name)
                file_data = await self.storage_client.download_file(object_key, bucket=bucket_name)
                source_map[angle] = {
                    "data": file_data,
                    "bucket_name": bucket_name,
                    "object_key": object_key,
                    "source_filename": str(item.get("source_filename") or f"{angle}.jpg"),
                    "mime_type": str(item.get("mime_type") or "application/octet-stream"),
                    "file_size": int(stat.get("size", item.get("file_size", 0)) or 0),
                    "image_url": f"{bucket_name}/{object_key}",
                }
            elif reuse_latest_missing:
                existing = latest_assets_by_angle.get(angle)
                if not existing:
                    raise ValueError(f"历史素材中缺少角度 {angle}，请重新上传完整三视图。")
                source_map[angle] = {
                    "data": await self.storage_client.download_file(
                        existing.object_key,
                        bucket=existing.bucket_name,
                    ),
                    "bucket_name": existing.bucket_name,
                    "object_key": existing.object_key,
                    "source_filename": existing.source_filename,
                    "mime_type": existing.mime_type,
                    "file_size": existing.file_size,
                    "image_url": existing.image_url,
                }
            else:
                raise ValueError(f"缺少角度 {angle} 的文件。")

        return await self._create_three_view_session_from_sources(
            user_id=job.user_id,
            actor_id=job.actor_id,
            source_map=source_map,
        )

    async def _create_three_view_session_from_sources(
        self,
        user_id: int,
        actor_id: int,
        source_map: dict[str, dict[str, Any]],
    ) -> tuple[PortraitUploadSessionModel, list[PortraitUploadAssetModel]]:
        session_key = uuid.uuid4().hex
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        normalized_source_map: dict[str, dict[str, Any]] = {}
        for angle in ("front", "left", "right"):
            source = source_map[angle]
            bucket_name = str(source["bucket_name"])
            object_key = str(source["object_key"])
            file_data = bytes(source.get("data") or b"")
            if not file_data:
                file_data = await self.storage_client.download_file(object_key, bucket=bucket_name)
            image, width, height, image_format = self._read_image(file_data)
            self._validate_three_view_source_resolution(angle=angle, width=width, height=height)
            source_filename = str(source.get("source_filename") or f"{angle}.jpg")
            mime_type = str(source.get("mime_type") or "application/octet-stream")
            extension = self._guess_extension(source_filename, mime_type, image_format)
            normalized_source_map[angle] = {
                "data": file_data,
                "bucket_name": bucket_name,
                "object_key": object_key,
                "image_url": str(source.get("image_url") or f"{bucket_name}/{object_key}"),
                "source_filename": source_filename,
                "mime_type": mime_type,
                "file_size": int(source.get("file_size") or len(file_data)),
                "width": width,
                "height": height,
                "extension": extension,
            }

        assembled = await self._assemble_three_view_assets(
            user_id=user_id,
            actor_id=actor_id,
            session_key=session_key,
            date_prefix=date_prefix,
            source_map=normalized_source_map,
        )

        with database.allow_sync():
            now = datetime.now()
            retired = (
                PortraitUploadSessionModel.update(
                    is_current=False,
                    superseded_at=now,
                )
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
                )
                .execute()
            )
            if retired:
                logger.info(
                    "Three-view current session rotated via compose job user_id=%s actor_id=%s retired_count=%s",
                    user_id,
                    actor_id,
                    retired,
                )
            session = PortraitUploadSessionModel.create(
                actor_id=actor_id,
                user_id=user_id,
                session_key=session_key,
                is_current=True,
                superseded_at=None,
                composite_bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                composite_object_key=assembled["composite_object_key"],
                composite_image_url=assembled["composite_image_url"],
                composite_preview_bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                composite_preview_object_key=assembled["composite_preview_object_key"],
                composite_preview_image_url=assembled["composite_preview_image_url"],
                composite_preview_file_size=assembled["composite_preview_file_size"],
                composite_variant_map=assembled["composite_variant_map"],
                composite_file_size=assembled["composite_file_size"],
                composite_width=assembled["compose_width"],
                composite_height=assembled["compose_height"],
                avatar_bucket_name=assembled["avatar_bucket_name"],
                avatar_object_key=assembled["avatar_object_key"],
                avatar_image_url=assembled["avatar_image_url"],
                avatar_mime_type=assembled["avatar_mime_type"],
                avatar_width=assembled["avatar_width"],
                avatar_height=assembled["avatar_height"],
                avatar_file_size=assembled["avatar_file_size"],
                avatar_variant_map=assembled["avatar_variant_map"],
                created_at=now,
            )
            assets = [
                PortraitUploadAssetModel.create(
                    session_id=session.id,
                    actor_id=actor_id,
                    user_id=user_id,
                    created_at=now,
                    **record,
                )
                for record in assembled["raw_asset_records"]
            ]
        await self._purge_superseded_three_view_versions(user_id=user_id, actor_id=actor_id)
        return session, assets

    def _serialize_compose_job(
        self,
        job: PortraitComposeJobModel,
        result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "job_key": job.job_key,
            "status": job.status,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "result": result,
        }

    def _resolve_actor_for_user(self, user_id: int, user_display_name: str) -> int:
        actor_external_id = f"USER-{user_id}"
        with database.allow_sync():
            actor, _created = ActorModel.get_or_create(
                external_id=actor_external_id,
                defaults={
                    "name": user_display_name or f"user_{user_id}",
                    "age": 0,
                    "location": "unknown",
                    "hometown": "",
                    "height": 0,
                    "weight_kg": 0,
                    "bust_cm": 0,
                    "waist_cm": 0,
                    "hip_cm": 0,
                    "shoe_size": "",
                    "bio": "Auto-created actor profile for individual uploads.",
                    "acting_requirements": "",
                    "rejected_requirements": "",
                    "availability_note": "",
                    "pricing_unit": "project",
                    "pricing_amount": 0,
                    "tags": ["self-upload"],
                    "is_published": False,
                },
            )
        if _created:
            logger.info("Auto-created actor for user user_id=%s actor_id=%s", user_id, actor.id)
        else:
            logger.debug("Resolved existing actor for user user_id=%s actor_id=%s", user_id, actor.id)
        return int(actor.id)

    async def get_actor_basic_info(self, user_id: int, user_display_name: str) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        with database.allow_sync():
            actor = ActorModel.get_or_none(ActorModel.id == actor_id)
            if not actor:
                raise ValueError("演员资料不存在，请稍后重试。")
            avatar_session = self._get_recompose_base_session(user_id=user_id, actor_id=actor_id)
        return self._serialize_actor_basic_info(actor=actor, avatar_session=avatar_session)

    async def get_actor_basic_info_by_actor_id(self, actor_id: int) -> dict[str, Any] | None:
        with database.allow_sync():
            actor = ActorModel.get_or_none(ActorModel.id == actor_id)
            if not actor:
                return None
            avatar_session = self._get_latest_actor_avatar_session(actor_id=actor_id)
        return self._serialize_actor_basic_info(actor=actor, avatar_session=avatar_session)

    async def update_actor_basic_info(
        self,
        user_id: int,
        user_display_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        with database.allow_sync():
            actor = ActorModel.get_or_none(ActorModel.id == actor_id)
            if not actor:
                raise ValueError("演员资料不存在，请稍后重试。")

            actor.name = self._clamp_text(payload.get("name"), max_len=64) or actor.name
            actor.age = self._clamp_int(payload.get("age"), min_value=0, max_value=100)
            actor.height = self._clamp_int(payload.get("height"), min_value=0, max_value=250)
            actor.weight_kg = self._clamp_int(payload.get("weight_kg"), min_value=0, max_value=300)
            actor.location = self._clamp_text(payload.get("location"), max_len=64)
            actor.hometown = self._clamp_text(payload.get("hometown"), max_len=64)
            actor.bust_cm = self._clamp_int(payload.get("bust_cm"), min_value=0, max_value=200)
            actor.waist_cm = self._clamp_int(payload.get("waist_cm"), min_value=0, max_value=200)
            actor.hip_cm = self._clamp_int(payload.get("hip_cm"), min_value=0, max_value=220)
            actor.shoe_size = self._clamp_text(payload.get("shoe_size"), max_len=16)
            actor.bio = self._clamp_text(payload.get("bio"), max_len=2000)
            actor.acting_requirements = self._clamp_text(payload.get("acting_requirements"), max_len=2000)
            actor.rejected_requirements = self._clamp_text(payload.get("rejected_requirements"), max_len=2000)
            actor.availability_note = self._clamp_text(payload.get("availability_note"), max_len=1000)
            actor.pricing_unit = self._normalize_pricing_unit(payload.get("pricing_unit"))
            actor.pricing_amount = self._clamp_int(payload.get("pricing_amount"), min_value=0, max_value=100000000)
            actor.tags = self._normalize_tags(payload.get("tags"))
            actor.save()

            avatar_session = self._get_recompose_base_session(user_id=user_id, actor_id=actor_id)

        logger.info("Actor basic info updated user_id=%s actor_id=%s", user_id, actor_id)
        return self._serialize_actor_basic_info(actor=actor, avatar_session=avatar_session)

    def _serialize_actor_basic_info(
        self,
        actor: ActorModel,
        avatar_session: PortraitUploadSessionModel | None,
    ) -> dict[str, Any]:
        avatar_url = None
        avatar_original_url = None
        avatar_variant_urls: dict[str, str] = {}
        avatar_source = "none"
        if avatar_session:
            if avatar_session.avatar_object_key and avatar_session.avatar_bucket_name:
                avatar_url = self.storage_client.get_url(
                    avatar_session.avatar_object_key,
                    bucket=avatar_session.avatar_bucket_name,
                )
                avatar_original_url = avatar_url
            elif avatar_session.composite_preview_object_key:
                avatar_url = self.storage_client.get_url(
                    avatar_session.composite_preview_object_key,
                    bucket=avatar_session.composite_preview_bucket or avatar_session.composite_bucket,
                )
            elif avatar_session.composite_object_key:
                avatar_url = self.storage_client.get_url(
                    avatar_session.composite_object_key,
                    bucket=avatar_session.composite_bucket,
                )

            avatar_variant_map = dict(avatar_session.avatar_variant_map or {})
            for key, item in avatar_variant_map.items():
                if not isinstance(item, dict):
                    continue
                object_key = str(item.get("object_key") or "")
                bucket_name = str(item.get("bucket_name") or avatar_session.avatar_bucket_name or "")
                if not object_key or not bucket_name:
                    continue
                avatar_variant_urls[str(key)] = self.storage_client.get_url(object_key, bucket=bucket_name)
            avatar_source = "three_view"
        return {
            "actor_id": actor.id,
            "external_id": actor.external_id,
            "name": actor.name,
            "age": int(actor.age or 0),
            "height": int(actor.height or 0),
            "weight_kg": int(actor.weight_kg or 0),
            "location": actor.location or "",
            "hometown": actor.hometown or "",
            "bust_cm": int(actor.bust_cm or 0),
            "waist_cm": int(actor.waist_cm or 0),
            "hip_cm": int(actor.hip_cm or 0),
            "shoe_size": actor.shoe_size or "",
            "bio": actor.bio or "",
            "tags": list(actor.tags or []),
            "acting_requirements": actor.acting_requirements or "",
            "rejected_requirements": actor.rejected_requirements or "",
            "availability_note": actor.availability_note or "",
            "pricing_unit": self._normalize_pricing_unit(actor.pricing_unit),
            "pricing_amount": int(actor.pricing_amount or 0),
            "avatar_url": avatar_url,
            "avatar_original_url": avatar_original_url or avatar_url,
            "avatar_variant_urls": avatar_variant_urls,
            "avatar_source": avatar_source,
            "created_at": actor.created_at,
        }

    def _clamp_int(self, value: Any, min_value: int, max_value: int) -> int:
        try:
            parsed = int(value)
        except Exception:
            return min_value
        if parsed < min_value:
            return min_value
        if parsed > max_value:
            return max_value
        return parsed

    def _clamp_text(self, value: Any, max_len: int) -> str:
        text = str(value or "").strip()
        if len(text) <= max_len:
            return text
        return text[:max_len]

    def _normalize_tags(self, raw_tags: Any) -> list[str]:
        if not isinstance(raw_tags, list):
            return []
        normalized: list[str] = []
        for item in raw_tags:
            tag = self._clamp_text(item, max_len=24)
            if not tag:
                continue
            if tag in normalized:
                continue
            normalized.append(tag)
            if len(normalized) >= 20:
                break
        return normalized

    def _normalize_pricing_unit(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"day", "project"}:
            return "project"
        return normalized

    def _validate_three_view_source_resolution(self, angle: str, width: int, height: int) -> None:
        long_edge = max(int(width or 0), int(height or 0))
        if long_edge <= THREE_VIEW_MIN_LONG_EDGE_PX:
            angle_label_map = {
                "left": "左侧面图",
                "front": "正面图",
                "right": "右侧面图",
            }
            label = angle_label_map.get(str(angle).lower(), "该角度图片")
            raise ValueError(
                f"{label}清晰度不足：长边需大于 2000 像素，当前为 {width}x{height}。"
            )

    def _build_portrait_storage_prefix(
        self,
        user_id: int,
        actor_id: int,
        date_prefix: str,
        session_key: str,
    ) -> str:
        return f"portraits/user_{user_id}/actor_{actor_id}/{date_prefix}/{session_key}"

    def _build_raw_object_key(self, base_prefix: str, angle: str, extension: str) -> str:
        return f"{base_prefix}/raw/{angle}/original.{extension}"

    def _build_raw_variant_object_key(self, base_prefix: str, angle: str, variant_key: str) -> str:
        return f"{base_prefix}/raw/{angle}/variants/{variant_key}.jpg"

    def _build_composite_original_object_key(self, base_prefix: str) -> str:
        return f"{base_prefix}/composite/original.jpg"

    def _build_composite_variant_object_key(self, base_prefix: str, variant_key: str) -> str:
        return f"{base_prefix}/composite/variants/{variant_key}.jpg"

    def _build_avatar_object_key(self, base_prefix: str, variant_key: str) -> str:
        return f"{base_prefix}/avatar/{variant_key}.jpg"

    async def _upload_jpeg_variant(
        self,
        object_key: str,
        image: Image.Image,
        *,
        quality: int = THREE_VIEW_VARIANT_JPEG_QUALITY,
        bucket: str = settings.MINIO_PORTRAIT_GENERATED_BUCKET,
    ) -> tuple[str, int]:
        output = BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)
        payload = output.getvalue()
        image_url = await self.storage_client.upload_file(
            object_key,
            payload,
            "image/jpeg",
            bucket=bucket,
        )
        return image_url, len(payload)

    async def _generate_and_upload_variants(
        self,
        image: Image.Image,
        *,
        target_widths: dict[str, int],
        object_key_builder: Any,
        bucket: str,
        quality: int,
    ) -> tuple[dict[str, str], dict[str, GeneratedImageVariant], str | None]:
        variant_urls: dict[str, str] = {}
        variant_meta: dict[str, GeneratedImageVariant] = {}
        preferred_variant_key: str | None = None
        source_width, source_height = image.size
        for variant_key, target_width in target_widths.items():
            if target_width <= 0:
                continue
            if source_width <= target_width:
                resized = image.copy()
            else:
                target_height = max(1, int(round(source_height * (target_width / source_width))))
                resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            object_key = object_key_builder(variant_key)
            variant_url, file_size = await self._upload_jpeg_variant(
                object_key,
                resized,
                quality=quality,
                bucket=bucket,
            )
            width, height = resized.size
            variant_urls[variant_key] = variant_url
            variant_meta[variant_key] = {
                "key": variant_key,
                "object_key": object_key,
                "width": int(width),
                "height": int(height),
                "file_size": int(file_size),
                "mime_type": "image/jpeg",
            }
            if preferred_variant_key is None:
                preferred_variant_key = variant_key
        return variant_urls, variant_meta, preferred_variant_key

    def _extract_front_avatar_from_source(self, image: Image.Image) -> Image.Image:
        width, height = image.size
        side = min(width, max(1, height // 2))
        left = max(0, (width - side) // 2)
        top = 0
        right = left + side
        bottom = top + side
        return image.crop((left, top, right, bottom))

    async def _generate_avatar_variants(
        self,
        source_image: Image.Image,
        *,
        base_prefix: str,
        bucket: str,
    ) -> tuple[dict[str, str], dict[str, GeneratedImageVariant], str | None]:
        avatar_square = self._extract_front_avatar_from_source(source_image)
        target_widths = {
            "thumb": 160,
            "profile": THREE_VIEW_AVATAR_SIZE,
        }
        return await self._generate_and_upload_variants(
            avatar_square,
            target_widths=target_widths,
            object_key_builder=lambda key: self._build_avatar_object_key(base_prefix, key),
            bucket=bucket,
            quality=THREE_VIEW_AVATAR_JPEG_QUALITY,
        )

    async def _generate_composite_assets(
        self,
        panels: dict[str, Image.Image],
        *,
        compose_width: int,
        compose_height: int,
        compose_order: tuple[str, str, str],
        base_prefix: str,
        bucket: str,
    ) -> dict[str, Any]:
        composite_image = self._compose_three_view_canvas(
            panels=panels,
            width=compose_width,
            height=compose_height,
            order=compose_order,
        )
        original_object_key = self._build_composite_original_object_key(base_prefix)
        composite_image_url, composite_file_size = await self._upload_jpeg_variant(
            original_object_key,
            composite_image,
            quality=95,
            bucket=bucket,
        )
        variant_urls, variant_meta, preferred_variant_key = await self._generate_and_upload_variants(
            composite_image,
            target_widths=THREE_VIEW_COMPOSITE_TARGET_WIDTHS,
            object_key_builder=lambda key: self._build_composite_variant_object_key(base_prefix, key),
            bucket=bucket,
            quality=THREE_VIEW_VARIANT_JPEG_QUALITY,
        )
        preferred_variant_url = variant_urls.get(preferred_variant_key or "", "")
        return {
            "image": composite_image,
            "image_url": composite_image_url,
            "object_key": original_object_key,
            "file_size": int(composite_file_size),
            "variant_urls": variant_urls,
            "variant_meta": variant_meta,
            "preferred_variant_key": preferred_variant_key,
            "preferred_variant_url": preferred_variant_url,
        }

    async def _assemble_three_view_assets(
        self,
        *,
        user_id: int,
        actor_id: int,
        session_key: str,
        date_prefix: str,
        source_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        compose_width = max(300, settings.PORTRAIT_COMPOSE_WIDTH)
        compose_height = max(225, settings.PORTRAIT_COMPOSE_HEIGHT)

        panel_width = compose_width // 3
        panel_height = int(panel_width * 16 / 9)
        if panel_height > compose_height:
            panel_height = compose_height
            panel_width = int(panel_height * 9 / 16)

        base_prefix = self._build_portrait_storage_prefix(
            user_id=user_id,
            actor_id=actor_id,
            date_prefix=date_prefix,
            session_key=session_key,
        )

        raw_asset_records: list[dict[str, Any]] = []
        panels: dict[str, Image.Image] = {}
        front_source_image: Image.Image | None = None
        for angle in ("front", "left", "right"):
            source = source_map[angle]
            source_data = bytes(source["data"])
            source_filename = str(source.get("source_filename") or f"{angle}.jpg")
            source_content_type = str(source.get("mime_type") or "application/octet-stream")
            source_extension = str(source.get("extension") or "jpg")
            source_width = int(source.get("width") or 0)
            source_height = int(source.get("height") or 0)
            source_file_size = int(source.get("file_size") or len(source_data))
            source_bucket_name = str(source.get("bucket_name") or settings.MINIO_PORTRAIT_RAW_BUCKET)
            source_object_key = str(source.get("object_key") or "")

            original_object_key = self._build_raw_object_key(base_prefix, angle, source_extension)
            if (
                source_bucket_name == settings.MINIO_PORTRAIT_RAW_BUCKET
                and source_object_key == original_object_key
            ):
                image_url = str(
                    source.get("image_url")
                    or f"{settings.MINIO_PORTRAIT_RAW_BUCKET}/{original_object_key}"
                )
            else:
                image_url = await self.storage_client.upload_file(
                    original_object_key,
                    source_data,
                    source_content_type,
                    bucket=settings.MINIO_PORTRAIT_RAW_BUCKET,
                )

            source_image = Image.open(BytesIO(source_data)).convert("RGB")
            if angle == "front":
                front_source_image = source_image.copy()
            panels[angle] = ImageOps.fit(
                source_image,
                (panel_width, panel_height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )

            preview_urls, preview_meta, preferred_preview_key = await self._generate_and_upload_variants(
                source_image,
                target_widths=THREE_VIEW_RAW_TARGET_WIDTHS,
                object_key_builder=lambda key, _angle=angle: self._build_raw_variant_object_key(base_prefix, _angle, key),
                bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                quality=THREE_VIEW_VARIANT_JPEG_QUALITY,
            )
            preferred_preview_url = preview_urls.get(preferred_preview_key or "", "")
            raw_asset_records.append(
                {
                    "view_angle": angle,
                    "bucket_name": settings.MINIO_PORTRAIT_RAW_BUCKET,
                    "object_key": original_object_key,
                    "image_url": image_url,
                    "source_filename": source_filename,
                    "mime_type": source_content_type,
                    "file_size": source_file_size,
                    "width": source_width,
                    "height": source_height,
                    "expected_ratio": settings.PORTRAIT_EXPECTED_SINGLE_RATIO,
                    "preview_bucket_name": settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                    "preview_object_key": str(
                        preview_meta.get(preferred_preview_key or "", {}).get("object_key", "")
                    ),
                    "preview_image_url": preferred_preview_url,
                    "preview_mime_type": "image/jpeg" if preferred_preview_url else source_content_type,
                    "preview_width": int(preview_meta.get(preferred_preview_key or "", {}).get("width", source_width)),
                    "preview_height": int(preview_meta.get(preferred_preview_key or "", {}).get("height", source_height)),
                    "preview_file_size": int(preview_meta.get(preferred_preview_key or "", {}).get("file_size", source_file_size)),
                    "variant_map": {
                        variant_key: {
                            "bucket_name": settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                            "object_key": meta["object_key"],
                            "image_url": preview_urls[variant_key],
                            "mime_type": meta["mime_type"],
                            "width": meta["width"],
                            "height": meta["height"],
                            "file_size": meta["file_size"],
                        }
                        for variant_key, meta in preview_meta.items()
                    },
                }
            )

        if front_source_image is None:
            raise ValueError("缺少正面图，无法生成头像。")

        composite_assets = await self._generate_composite_assets(
            panels=panels,
            compose_width=compose_width,
            compose_height=compose_height,
            compose_order=settings.PORTRAIT_COMPOSE_ORDER,
            base_prefix=base_prefix,
            bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
        )
        avatar_urls, avatar_meta, avatar_preferred_key = await self._generate_avatar_variants(
            front_source_image,
            base_prefix=base_prefix,
            bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
        )
        avatar_preferred_meta = avatar_meta.get(avatar_preferred_key or "", {})
        avatar_preview_url = avatar_urls.get(avatar_preferred_key or "", "")

        return {
            "compose_width": compose_width,
            "compose_height": compose_height,
            "raw_asset_records": raw_asset_records,
            "composite_object_key": composite_assets["object_key"],
            "composite_image_url": composite_assets["image_url"],
            "composite_file_size": composite_assets["file_size"],
            "composite_preview_object_key": str(
                composite_assets["variant_meta"].get(
                    composite_assets["preferred_variant_key"] or "",
                    {},
                ).get("object_key", "")
            ),
            "composite_preview_image_url": composite_assets["preferred_variant_url"],
            "composite_preview_file_size": int(
                composite_assets["variant_meta"].get(
                    composite_assets["preferred_variant_key"] or "",
                    {},
                ).get("file_size", composite_assets["file_size"])
            ),
            "composite_variant_map": {
                variant_key: {
                    "bucket_name": settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                    "object_key": meta["object_key"],
                    "image_url": composite_assets["variant_urls"][variant_key],
                    "mime_type": meta["mime_type"],
                    "width": meta["width"],
                    "height": meta["height"],
                    "file_size": meta["file_size"],
                }
                for variant_key, meta in composite_assets["variant_meta"].items()
            },
            "avatar_bucket_name": settings.MINIO_PORTRAIT_GENERATED_BUCKET,
            "avatar_object_key": avatar_preferred_meta.get("object_key", ""),
            "avatar_image_url": avatar_preview_url,
            "avatar_mime_type": avatar_preferred_meta.get("mime_type", "image/jpeg"),
            "avatar_width": int(avatar_preferred_meta.get("width", 0)),
            "avatar_height": int(avatar_preferred_meta.get("height", 0)),
            "avatar_file_size": int(avatar_preferred_meta.get("file_size", 0)),
            "avatar_variant_map": {
                variant_key: {
                    "bucket_name": settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                    "object_key": meta["object_key"],
                    "image_url": avatar_urls[variant_key],
                    "mime_type": meta["mime_type"],
                    "width": meta["width"],
                    "height": meta["height"],
                    "file_size": meta["file_size"],
                }
                for variant_key, meta in avatar_meta.items()
            },
        }

    def _get_recompose_base_session(
        self,
        user_id: int,
        actor_id: int,
    ) -> PortraitUploadSessionModel | None:
        draft_session = (
            PortraitUploadSessionModel.select()
            .where(
                (PortraitUploadSessionModel.user_id == user_id)
                & (PortraitUploadSessionModel.actor_id == actor_id)
                & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
            )
            .order_by(PortraitUploadSessionModel.created_at.desc())
            .first()
        )
        if draft_session:
            return draft_session
        return (
            PortraitUploadSessionModel.select()
            .where(
                (PortraitUploadSessionModel.user_id == user_id)
                & (PortraitUploadSessionModel.actor_id == actor_id)
                & (PortraitUploadSessionModel.is_current == False)  # noqa: E712
                & PortraitUploadSessionModel.superseded_at.is_null(True)
            )
            .order_by(PortraitUploadSessionModel.created_at.desc())
            .first()
        )

    def _get_latest_actor_avatar_session(self, actor_id: int) -> PortraitUploadSessionModel | None:
        current_session = (
            PortraitUploadSessionModel.select()
            .where(
                (PortraitUploadSessionModel.actor_id == actor_id)
                & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
            )
            .order_by(PortraitUploadSessionModel.created_at.desc())
            .first()
        )
        if current_session:
            return current_session
        return (
            PortraitUploadSessionModel.select()
            .where(
                (PortraitUploadSessionModel.actor_id == actor_id)
                & (PortraitUploadSessionModel.is_current == False)  # noqa: E712
                & PortraitUploadSessionModel.superseded_at.is_null(True)
            )
            .order_by(PortraitUploadSessionModel.created_at.desc())
            .first()
        )

    def _read_image(self, file_data: bytes) -> tuple[Image.Image, int, int, str]:
        try:
            image = Image.open(BytesIO(file_data))
            image.load()
        except Exception as exc:
            logger.warning("Invalid image upload bytes=%s", len(file_data))
            raise ValueError("上传文件必须是可读取的图片格式。") from exc

        image_format = (image.format or "").lower()
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        if width <= 0 or height <= 0:
            logger.warning("Invalid image dimensions width=%s height=%s", width, height)
            raise ValueError("上传图片尺寸非法。")
        return rgb_image, width, height, image_format

    def _guess_extension(self, filename: str, content_type: str, image_format: str) -> str:
        suffix = Path(filename).suffix.lower().lstrip(".")
        if suffix in {"jpg", "jpeg", "png", "webp"}:
            return "jpg" if suffix == "jpeg" else suffix

        mime_mapping = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }
        if content_type in mime_mapping:
            return mime_mapping[content_type]

        format_mapping = {
            "jpeg": "jpg",
            "png": "png",
            "webp": "webp",
        }
        return format_mapping.get(image_format, "jpg")

    def _compose_three_view_canvas(
        self,
        panels: dict[str, Image.Image],
        width: int,
        height: int,
        order: tuple[str, str, str],
    ) -> Image.Image:
        panel_width = width // 3
        panel_height = int(panel_width * 16 / 9)
        if panel_height > height:
            panel_height = height
            panel_width = int(panel_height * 9 / 16)

        canvas = Image.new("RGB", (width, height), "#0b1220")
        x_start = (width - panel_width * 3) // 2
        y_start = (height - panel_height) // 2
        for index, angle in enumerate(order):
            panel = ImageOps.fit(
                panels[angle],
                (panel_width, panel_height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            canvas.paste(panel, (x_start + index * panel_width, y_start))
        return canvas

    def _compose_three_view_image(
        self,
        panels: dict[str, Image.Image],
        width: int,
        height: int,
        order: tuple[str, str, str],
    ) -> bytes:
        canvas = self._compose_three_view_canvas(
            panels=panels,
            width=width,
            height=height,
            order=order,
        )
        output = BytesIO()
        canvas.save(output, format="JPEG", quality=95, optimize=True)
        return output.getvalue()

    def _serialize_three_view_session(
        self,
        session: PortraitUploadSessionModel,
        assets: list[PortraitUploadAssetModel],
    ) -> dict[str, Any]:
        composite_original_url = self.storage_client.get_url(
            session.composite_object_key,
            bucket=session.composite_bucket,
        )
        preview_bucket = session.composite_preview_bucket or session.composite_bucket
        preview_object_key = session.composite_preview_object_key or session.composite_object_key
        composite_preview_url = self.storage_client.get_url(
            preview_object_key,
            bucket=preview_bucket,
        )
        composite_variant_urls: dict[str, str] = {}
        for key, item in dict(session.composite_variant_map or {}).items():
            if not isinstance(item, dict):
                continue
            object_key = str(item.get("object_key") or "")
            bucket_name = str(item.get("bucket_name") or preview_bucket or "")
            if not object_key or not bucket_name:
                continue
            composite_variant_urls[str(key)] = self.storage_client.get_url(object_key, bucket=bucket_name)

        avatar_url = None
        avatar_original_url = None
        avatar_variant_urls: dict[str, str] = {}
        if session.avatar_object_key and session.avatar_bucket_name:
            avatar_url = self.storage_client.get_url(
                session.avatar_object_key,
                bucket=session.avatar_bucket_name,
            )
            avatar_original_url = avatar_url
        for key, item in dict(session.avatar_variant_map or {}).items():
            if not isinstance(item, dict):
                continue
            object_key = str(item.get("object_key") or "")
            bucket_name = str(item.get("bucket_name") or session.avatar_bucket_name or "")
            if not object_key or not bucket_name:
                continue
            avatar_variant_urls[str(key)] = self.storage_client.get_url(object_key, bucket=bucket_name)

        raw_images = [
            {
                "id": asset.id,
                "view_angle": asset.view_angle,
                "image_url": asset.image_url,
                "original_url": self.storage_client.get_url(asset.object_key, bucket=asset.bucket_name),
                "preview_url": self.storage_client.get_url(
                    asset.preview_object_key or asset.object_key,
                    bucket=asset.preview_bucket_name or asset.bucket_name,
                ),
                "bucket_name": asset.bucket_name,
                "object_key": asset.object_key,
                "preview_bucket_name": asset.preview_bucket_name or asset.bucket_name,
                "preview_object_key": asset.preview_object_key or asset.object_key,
                "preview_image_url": asset.preview_image_url or asset.image_url,
                "preview_mime_type": asset.preview_mime_type or asset.mime_type,
                "preview_width": int(asset.preview_width or asset.width),
                "preview_height": int(asset.preview_height or asset.height),
                "preview_file_size": int(asset.preview_file_size or asset.file_size),
                "variant_urls": {
                    str(key): self.storage_client.get_url(
                        str((value or {}).get("object_key")),
                        bucket=str((value or {}).get("bucket_name")),
                    )
                    for key, value in dict(asset.variant_map or {}).items()
                    if isinstance(value, dict)
                    and str((value or {}).get("object_key") or "")
                    and str((value or {}).get("bucket_name") or "")
                },
                "source_filename": asset.source_filename,
                "mime_type": asset.mime_type,
                "file_size": asset.file_size,
                "width": asset.width,
                "height": asset.height,
                "expected_ratio": asset.expected_ratio,
                "created_at": asset.created_at,
            }
            for asset in assets
        ]

        return {
            "session_id": session.id,
            "session_key": session.session_key,
            "actor_id": session.actor_id,
            "is_current": bool(session.is_current),
            "superseded_at": session.superseded_at,
            "composite_image_url": session.composite_image_url,
            "composite_original_url": composite_original_url,
            "composite_preview_url": composite_preview_url,
            "composite_variant_urls": composite_variant_urls,
            "composite_bucket": session.composite_bucket,
            "composite_object_key": session.composite_object_key,
            "composite_preview_bucket": preview_bucket,
            "composite_preview_object_key": preview_object_key,
            "composite_preview_image_url": session.composite_preview_image_url or session.composite_image_url,
            "composite_file_size": int(session.composite_file_size or 0),
            "composite_preview_file_size": int(session.composite_preview_file_size or session.composite_file_size or 0),
            "composite_width": session.composite_width,
            "composite_height": session.composite_height,
            "avatar_url": avatar_url,
            "avatar_original_url": avatar_original_url or avatar_url,
            "avatar_variant_urls": avatar_variant_urls,
            "expected_composite_ratio": settings.PORTRAIT_EXPECTED_COMPOSITE_RATIO,
            "expected_single_ratio": settings.PORTRAIT_EXPECTED_SINGLE_RATIO,
            "detection_note": "当前不做自动检测，后续版本可能会增加检测规则。",
            "raw_images": raw_images,
            "created_at": session.created_at,
        }

    def _serialize_video_asset(self, asset: PortraitVideoAssetModel) -> dict[str, Any]:
        return {
            "id": asset.id,
            "actor_id": asset.actor_id,
            "user_id": asset.user_id,
            "video_type": asset.video_type,
            "is_current": bool(asset.is_current),
            "superseded_at": asset.superseded_at,
            "bucket_name": asset.bucket_name,
            "object_key": asset.object_key,
            "video_url": asset.video_url,
            "preview_url": self.storage_client.get_url(asset.object_key, bucket=asset.bucket_name),
            "source_filename": asset.source_filename,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
            "created_at": asset.created_at,
        }

    async def _create_audio_asset_record(
        self,
        actor_id: int,
        user_id: int,
        bucket_name: str,
        object_key: str,
        source_filename: str,
        mime_type: str,
        file_size: int,
    ) -> dict[str, Any]:
        audio_url = f"{bucket_name}/{object_key}"
        with database.allow_sync():
            asset = PortraitAudioAssetModel.create(
                actor_id=actor_id,
                user_id=user_id,
                is_published=False,
                superseded_at=None,
                bucket_name=bucket_name,
                object_key=object_key,
                audio_url=audio_url,
                source_filename=source_filename,
                mime_type=mime_type,
                file_size=file_size,
                created_at=datetime.now(),
            )
        logger.info(
            "Portrait audio asset persisted user_id=%s actor_id=%s audio_id=%s bucket=%s object_key=%s",
            user_id,
            actor_id,
            asset.id,
            bucket_name,
            object_key,
        )
        return self._serialize_audio_asset(asset)

    def _serialize_audio_asset(self, asset: PortraitAudioAssetModel) -> dict[str, Any]:
        return {
            "id": asset.id,
            "actor_id": asset.actor_id,
            "user_id": asset.user_id,
            "is_published": bool(asset.is_published),
            "superseded_at": asset.superseded_at,
            "bucket_name": asset.bucket_name,
            "object_key": asset.object_key,
            "audio_url": asset.audio_url,
            "preview_url": self.storage_client.get_url(asset.object_key, bucket=asset.bucket_name),
            "source_filename": asset.source_filename,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
            "created_at": asset.created_at,
        }


class StyleService:
    _image_generator: LangChainStyleImageGenerator | None = None

    def __init__(
        self,
        style_repo: StyleRepository,
        result_repo: GeneratedResultRepository,
        storage_client: StorageClient,
    ):
        self.style_repo = style_repo
        self.result_repo = result_repo
        self.storage_client = storage_client
        if self.__class__._image_generator is None:
            self.__class__._image_generator = LangChainStyleImageGenerator()
        self.storage_client.ensure_buckets(
            [
                settings.MINIO_BUCKET,
                settings.MINIO_PORTRAIT_RAW_BUCKET,
                settings.MINIO_PORTRAIT_GENERATED_BUCKET,
                settings.MINIO_STYLE_GENERATED_BUCKET,
            ]
        )

    async def list_styles(self) -> List[Style]:
        self._ensure_default_style_catalog()
        styles = await self.style_repo.list_styles()
        style_map = {style.name: style for style in styles}
        ordered: list[Style] = []
        for item in STYLE_CATALOG_DEFAULTS:
            style = style_map.get(item["name"])
            if style:
                ordered.append(style)
        return ordered

    async def generate_result(
        self,
        user_id: int,
        user_display_name: str,
        style_id: int,
        custom_prompt: str = "",
    ) -> dict[str, Any]:
        self._ensure_default_style_catalog()
        style = await self.style_repo.get_by_id(style_id)
        if not style:
            raise ValueError("风格不存在。")
        if str(style.category or "").lower() == "custom":
            raise ValueError("自定义风格仅支持图片上传。")

        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        published_session = self._get_published_portrait_session(user_id=user_id, actor_id=actor_id)
        if not published_session:
            raise ValueError("请先发布三视图（左/正/右）后再生成风格效果图。")

        reference_images = await self._load_style_reference_images_from_published_session(published_session)
        generator = self.__class__._image_generator
        assert generator is not None
        generation = await generator.generate(
            style_id=style.id or style_id,
            style_name=style.name,
            style_description=style.description,
            style_category=style.category,
            reference_images=reference_images,
            custom_prompt=custom_prompt,
        )

        extension = self._guess_image_extension(generation.mime_type, generation.image_bytes)
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = (
            f"styles/generated/user_{user_id}/actor_{actor_id}/{date_prefix}/"
            f"style_{style_id}_{uuid.uuid4().hex}.{extension}"
        )
        image_url = await self.storage_client.upload_file(
            object_key,
            generation.image_bytes,
            generation.mime_type,
            bucket=settings.MINIO_STYLE_GENERATED_BUCKET,
        )

        with database.allow_sync():
            now = datetime.now()
            saved = GeneratedResultModel.create(
                actor_id=actor_id,
                user_id=user_id,
                style_id=style_id,
                image_url=image_url,
                lifecycle_state="draft",
                superseded_at=None,
                published_at=None,
                custom_prompt=self._sanitize_custom_prompt(custom_prompt),
                created_at=now,
            )
        logger.info(
            "Style generated user_id=%s actor_id=%s style_id=%s result_id=%s prompt_key=%s",
            user_id,
            actor_id,
            style_id,
            saved.id,
            generation.prompt_template_key,
        )
        return self._serialize_generated_result(saved, style)

    async def upload_custom_result(
        self,
        user_id: int,
        user_display_name: str,
        style_id: int,
        file_data: bytes,
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        self._ensure_default_style_catalog()
        style = await self.style_repo.get_by_id(style_id)
        if not style:
            raise ValueError("风格不存在。")
        if str(style.category or "").lower() != "custom":
            raise ValueError("仅自定义风格支持手动上传图片。")
        if not file_data:
            raise ValueError("请先选择一张图片后再上传。")
        if content_type and not str(content_type).lower().startswith("image/"):
            raise ValueError("上传文件必须是图片格式。")

        self._validate_reference_image(file_data)
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        extension = self._guess_image_extension(content_type, file_data)
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = (
            f"styles/generated/user_{user_id}/actor_{actor_id}/{date_prefix}/"
            f"custom_style_{uuid.uuid4().hex}.{extension}"
        )
        image_url = await self.storage_client.upload_file(
            object_key,
            file_data,
            content_type or "image/jpeg",
            bucket=settings.MINIO_STYLE_GENERATED_BUCKET,
        )

        with database.allow_sync():
            now = datetime.now()
            saved = GeneratedResultModel.create(
                actor_id=actor_id,
                user_id=user_id,
                style_id=style_id,
                image_url=image_url,
                lifecycle_state="draft",
                superseded_at=None,
                published_at=None,
                custom_prompt="自定义上传图片",
                created_at=now,
            )

        logger.info(
            "Custom style image uploaded user_id=%s actor_id=%s style_id=%s result_id=%s filename=%s content_type=%s",
            user_id,
            actor_id,
            style_id,
            saved.id,
            filename,
            content_type,
        )
        return self._serialize_generated_result(saved, style)

    async def list_results_grouped(self, user_id: int, user_display_name: str, limit_per_style: int) -> dict[str, Any]:
        self._ensure_default_style_catalog()
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        with database.allow_sync():
            rows = list(
                GeneratedResultModel.select()
                .where(
                    (GeneratedResultModel.user_id == user_id)
                    & (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.lifecycle_state.in_(["draft", "published"]))
                )
                .order_by(GeneratedResultModel.created_at.desc())
            )

        styles = await self.list_styles()
        style_map = {
            int(style.id): style
            for style in styles
            if style.id is not None
        }
        grouped_state: dict[int, list[dict[str, Any]]] = {}
        grouped_count: dict[int, int] = {}
        for row in rows:
            style = style_map.get(int(row.style_id))
            if not style:
                continue
            style_key = int(row.style_id)
            current = grouped_count.get(style_key, 0)
            if current >= max(1, int(limit_per_style)):
                continue
            bucket = grouped_state.setdefault(style_key, [])
            bucket.append(self._serialize_generated_result(row, style))
            grouped_count[style_key] = current + 1

        groups = []
        for style in styles:
            if style.id is None:
                continue
            groups.append(
                {
                    "style_id": int(style.id),
                    "style_name": style.name,
                    "style_category": style.category,
                    "results": grouped_state.get(int(style.id), []),
                }
            )
        return {"groups": groups}

    async def publish_draft_result(self, user_id: int, user_display_name: str, style_id: int) -> dict[str, Any]:
        self._ensure_default_style_catalog()
        style = await self.style_repo.get_by_id(style_id)
        if not style:
            raise ValueError("风格不存在。")

        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        ensure_actor_agreement_signed(actor_id)
        with database.allow_sync():
            now = datetime.now()
            draft = (
                GeneratedResultModel.select()
                .where(
                    (GeneratedResultModel.user_id == user_id)
                    & (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.style_id == style_id)
                    & (GeneratedResultModel.lifecycle_state == "draft")
                )
                .order_by(GeneratedResultModel.created_at.desc())
                .first()
            )
            if not draft:
                raise ValueError("该风格暂无可发布草稿，请先生成后再发布。")

            draft.lifecycle_state = "published"
            draft.superseded_at = None
            draft.published_at = now
            draft.save()

            (
                ActorModel.update(is_published=True)
                .where(ActorModel.id == actor_id)
                .execute()
            )

        logger.info(
            "Style draft published user_id=%s actor_id=%s style_id=%s result_id=%s",
            user_id,
            actor_id,
            style_id,
            draft.id,
        )
        return self._serialize_generated_result(draft, style)

    async def toggle_result_state(
        self,
        user_id: int,
        user_display_name: str,
        result_id: int,
        published: bool,
    ) -> dict[str, Any]:
        self._ensure_default_style_catalog()
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        if published:
            ensure_actor_agreement_signed(actor_id)
        with database.allow_sync():
            row = (
                GeneratedResultModel.select()
                .where(
                    (GeneratedResultModel.id == result_id)
                    & (GeneratedResultModel.user_id == user_id)
                    & (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.lifecycle_state.in_(["draft", "published"]))
                )
                .first()
            )
            if not row:
                raise ValueError("图片不存在或无权限操作。")

            now = datetime.now()
            if published:
                row.lifecycle_state = "published"
                row.published_at = now
            else:
                row.lifecycle_state = "draft"
                row.published_at = None
            row.superseded_at = None
            row.save()

            if published:
                (
                    ActorModel.update(is_published=True)
                    .where(ActorModel.id == actor_id)
                    .execute()
                )

        style = await self.style_repo.get_by_id(int(row.style_id))
        if not style:
            raise ValueError("风格不存在。")
        return self._serialize_generated_result(row, style)

    async def delete_result(
        self,
        user_id: int,
        user_display_name: str,
        result_id: int,
    ) -> None:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        with database.allow_sync():
            row = (
                GeneratedResultModel.select()
                .where(
                    (GeneratedResultModel.id == result_id)
                    & (GeneratedResultModel.user_id == user_id)
                    & (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.lifecycle_state.in_(["draft", "published"]))
                )
                .first()
            )
            if not row:
                raise ValueError("图片不存在或无权限删除。")
            image_url = str(row.image_url or "")
            row.delete_instance()

        bucket_name, object_key = self._split_bucket_object(image_url)
        if bucket_name and object_key:
            try:
                await self.storage_client.remove_object(object_key, bucket=bucket_name)
            except Exception:
                logger.exception(
                    "Failed to delete style image object bucket=%s object_key=%s result_id=%s",
                    bucket_name,
                    object_key,
                    result_id,
                )

    async def list_published_results_by_actor(self, actor_id: int, limit: int = 20) -> list[dict[str, Any]]:
        with database.allow_sync():
            rows = list(
                GeneratedResultModel.select()
                .where(
                    (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.lifecycle_state == "published")
                )
                .order_by(
                    GeneratedResultModel.published_at.desc(),
                    GeneratedResultModel.created_at.desc(),
                )
                .limit(max(1, limit))
            )
        if not rows:
            return []

        style_ids = sorted({int(row.style_id) for row in rows})
        style_map: dict[int, Style] = {}
        for style_id in style_ids:
            style = await self.style_repo.get_by_id(style_id)
            if style:
                style_map[style_id] = style

        items: list[dict[str, Any]] = []
        for row in rows:
            style = style_map.get(int(row.style_id))
            if not style:
                continue
            items.append(self._serialize_generated_result(row, style))
        return items

    async def get_published_result_summary_for_actor(self, actor_id: int) -> tuple[dict[str, Any] | None, int]:
        with database.allow_sync():
            count = (
                GeneratedResultModel.select()
                .where(
                    (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.lifecycle_state == "published")
                )
                .count()
            )
            latest = (
                GeneratedResultModel.select()
                .where(
                    (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.lifecycle_state == "published")
                )
                .order_by(
                    GeneratedResultModel.published_at.desc(),
                    GeneratedResultModel.created_at.desc(),
                )
                .first()
            )
        if not latest:
            return None, int(count)

        style = await self.style_repo.get_by_id(int(latest.style_id))
        if not style:
            return None, int(count)
        return self._serialize_generated_result(latest, style), int(count)

    def _resolve_actor_for_user(self, user_id: int, user_display_name: str) -> int:
        actor_external_id = f"USER-{user_id}"
        with database.allow_sync():
            actor, _created = ActorModel.get_or_create(
                external_id=actor_external_id,
                defaults={
                    "name": user_display_name or f"user_{user_id}",
                    "age": 0,
                    "location": "unknown",
                    "height": 0,
                    "bio": "Auto-created actor profile for individual uploads.",
                    "tags": ["self-upload"],
                    "is_published": False,
                },
            )
        if _created:
            logger.info("Auto-created actor for style generation user_id=%s actor_id=%s", user_id, actor.id)
        return int(actor.id)

    def _get_published_portrait_session(
        self,
        user_id: int,
        actor_id: int,
    ) -> PortraitUploadSessionModel | None:
        with database.allow_sync():
            session = (
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & (PortraitUploadSessionModel.is_current == False)  # noqa: E712
                    & PortraitUploadSessionModel.superseded_at.is_null(True)
                )
                .order_by(PortraitUploadSessionModel.created_at.desc())
                .first()
            )
        return session

    async def _load_style_reference_images_from_published_session(
        self,
        session: PortraitUploadSessionModel,
    ) -> list[StyleReferenceImage]:
        with database.allow_sync():
            assets = list(
                PortraitUploadAssetModel.select()
                .where(PortraitUploadAssetModel.session_id == session.id)
                .order_by(PortraitUploadAssetModel.created_at.asc())
            )

        assets_by_angle = {
            str(asset.view_angle).lower(): asset
            for asset in assets
        }
        compose_order = settings.PORTRAIT_COMPOSE_ORDER
        missing_angles = [angle for angle in compose_order if angle not in assets_by_angle]
        if missing_angles:
            logger.warning(
                "Published three-view missing angles user_id=%s actor_id=%s session_id=%s missing=%s",
                session.user_id,
                session.actor_id,
                session.id,
                ",".join(missing_angles),
            )
            raise ValueError("已发布三视图不完整，请先补齐左/正/右基础照并发布。")

        try:
            raw_images = await asyncio.gather(
                *[
                    self.storage_client.download_file(
                        assets_by_angle[angle].object_key,
                        bucket=assets_by_angle[angle].bucket_name,
                    )
                    for angle in compose_order
                ]
            )
        except Exception as exc:
            logger.exception(
                "Failed to download published raw images user_id=%s actor_id=%s session_id=%s",
                session.user_id,
                session.actor_id,
                session.id,
            )
            raise ValueError("读取已发布基础照失败，请重新发布三视图后再试。") from exc

        references: list[StyleReferenceImage] = []
        for angle, payload in zip(compose_order, raw_images):
            self._validate_reference_image(payload)
            source_filename = str(assets_by_angle[angle].source_filename or f"{angle}.jpg")
            references.append(
                StyleReferenceImage(
                    data=payload,
                    filename=source_filename,
                )
            )
        return references

    @staticmethod
    def _validate_reference_image(file_data: bytes) -> None:
        try:
            image = Image.open(BytesIO(file_data))
            image.load()
        except Exception as exc:
            raise ValueError("已发布基础照文件不可读，请重新上传并发布后再试。") from exc

    @staticmethod
    def _guess_image_extension(mime_type: str, image_bytes: bytes) -> str:
        mime = (mime_type or "").lower()
        if "png" in mime:
            return "png"
        if "webp" in mime:
            return "webp"
        if "jpeg" in mime or "jpg" in mime:
            return "jpg"
        # Fallback by signature
        if image_bytes.startswith(b"\x89PNG"):
            return "png"
        if image_bytes.startswith(b"\xff\xd8\xff"):
            return "jpg"
        return "png"

    def _serialize_generated_result(self, result: Any, style: Style) -> dict[str, Any]:
        bucket_name, object_key = self._split_bucket_object(result.image_url)
        preview_url = result.image_url
        if bucket_name and object_key:
            preview_url = self.storage_client.get_url(object_key, bucket=bucket_name)
        return {
            "id": result.id,
            "actor_id": result.actor_id,
            "style_id": result.style_id,
            "style_name": style.name,
            "style_category": style.category,
            "image_url": result.image_url,
            "preview_url": preview_url,
            "custom_prompt": str(getattr(result, "custom_prompt", "") or ""),
            "lifecycle_state": getattr(result, "lifecycle_state", "published"),
            "published_at": getattr(result, "published_at", None),
            "created_at": result.created_at,
        }

    @staticmethod
    def _sanitize_custom_prompt(value: str) -> str:
        return (value or "").strip()[:1000]

    @staticmethod
    def _split_bucket_object(image_url: str) -> tuple[str, str]:
        if not image_url or "/" not in image_url:
            return "", ""
        bucket_name, object_key = image_url.split("/", 1)
        return bucket_name, object_key

    def _ensure_default_style_catalog(self) -> None:
        with database.allow_sync():
            for style_data in STYLE_CATALOG_DEFAULTS:
                style, _created = StyleModel.get_or_create(
                    name=style_data["name"],
                    defaults=style_data,
                )
                update_fields: dict[str, Any] = {}
                if style.description != style_data["description"]:
                    update_fields["description"] = style_data["description"]
                if style.preview_url != style_data["preview_url"]:
                    update_fields["preview_url"] = style_data["preview_url"]
                if style.category != style_data["category"]:
                    update_fields["category"] = style_data["category"]
                if update_fields:
                    (
                        StyleModel.update(**update_fields)
                        .where(StyleModel.id == style.id)
                        .execute()
                    )

    async def _purge_superseded_style_versions(
        self,
        user_id: int,
        actor_id: int,
        style_id: int | None = None,
    ) -> dict[str, int]:
        with database.allow_sync():
            condition = (
                (GeneratedResultModel.user_id == user_id)
                & (GeneratedResultModel.actor_id == actor_id)
                & (GeneratedResultModel.lifecycle_state == "superseded")
            )
            if style_id is not None:
                condition = condition & (GeneratedResultModel.style_id == style_id)
            superseded_rows = list(
                GeneratedResultModel.select().where(condition)
            )
            if not superseded_rows:
                return {"deleted_records": 0, "deleted_objects": 0, "skipped_objects": 0}

            row_ids = [int(row.id) for row in superseded_rows]
            candidate_objects: set[tuple[str, str]] = set()
            for row in superseded_rows:
                bucket, object_key = self._split_bucket_object(str(row.image_url))
                if bucket and object_key:
                    candidate_objects.add((bucket, object_key))

            active_condition = (
                (GeneratedResultModel.user_id == user_id)
                & (GeneratedResultModel.actor_id == actor_id)
                & (GeneratedResultModel.lifecycle_state.in_(["draft", "published"]))
            )
            if style_id is not None:
                active_condition = active_condition & (GeneratedResultModel.style_id == style_id)
            in_use_objects: set[tuple[str, str]] = set()
            for row in GeneratedResultModel.select(
                GeneratedResultModel.image_url,
            ).where(active_condition):
                bucket, object_key = self._split_bucket_object(str(row.image_url))
                if bucket and object_key:
                    in_use_objects.add((bucket, object_key))

            skipped_objects = candidate_objects & in_use_objects
            deletable_objects = candidate_objects - in_use_objects

            deleted_records = (
                GeneratedResultModel.delete()
                .where(GeneratedResultModel.id.in_(row_ids))
                .execute()
            )

        deleted_objects = 0
        for bucket_name, object_key in sorted(deletable_objects):
            try:
                await self.storage_client.remove_object(object_key, bucket=bucket_name)
                deleted_objects += 1
            except Exception:
                logger.exception(
                    "Failed to purge superseded style image bucket=%s object_key=%s",
                    bucket_name,
                    object_key,
                )

        return {
            "deleted_records": int(deleted_records),
            "deleted_objects": int(deleted_objects),
            "skipped_objects": int(len(skipped_objects)),
        }
