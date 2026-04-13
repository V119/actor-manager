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

from backend.domain.models import Actor, GeneratedResult, Portrait, Protocol, Style
from backend.domain.repositories import (
    ActorRepository,
    GeneratedResultRepository,
    PortraitRepository,
    ProtocolRepository,
    StyleRepository,
)
from backend.application.style_generation import LangChainStyleImageGenerator, StyleReferenceImage
from backend.infrastructure.config import settings
from backend.infrastructure.orm_models import (
    ActorModel,
    GeneratedResultModel,
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
]


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
            ]
        )
        logger.debug(
            "PortraitService initialized with buckets raw=%s generated=%s video=%s worker_concurrency=%s",
            settings.MINIO_PORTRAIT_RAW_BUCKET,
            settings.MINIO_PORTRAIT_GENERATED_BUCKET,
            settings.MINIO_PORTRAIT_VIDEO_BUCKET,
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
            object_key = (
                f"portraits/raw/user_{user_id}/actor_{actor_id}/{date_prefix}/{upload_batch_key}/"
                f"{angle}_{uuid.uuid4().hex}.{extension}"
            )
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
        filename: str,
        content_type: str,
        size: int,
    ) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        normalized_content_type = content_type or "application/octet-stream"
        if not normalized_content_type.startswith("video/"):
            raise ValueError("请上传视频文件。")

        extension = Path(filename).suffix.lower().lstrip(".") or "mp4"
        upload_batch_key = uuid.uuid4().hex
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = (
            f"portraits/video/user_{user_id}/actor_{actor_id}/{date_prefix}/"
            f"{upload_batch_key}.{extension}"
        )
        upload_target = {
            "view_angle": "video",
            "bucket_name": settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            "object_key": object_key,
            "source_filename": filename or f"portrait_video.{extension}",
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
            "Prepared video direct upload plan user_id=%s actor_id=%s upload_batch_key=%s",
            user_id,
            actor_id,
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
        compose_width = max(300, settings.PORTRAIT_COMPOSE_WIDTH)
        compose_height = max(225, settings.PORTRAIT_COMPOSE_HEIGHT)
        session_key = uuid.uuid4().hex
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        logger.info(
            "Three-view upload started user_id=%s actor_id=%s session_key=%s compose=%sx%s",
            user_id,
            actor_id,
            session_key,
            compose_width,
            compose_height,
        )

        panel_width = compose_width // 3
        panel_height = int(panel_width * 16 / 9)
        if panel_height > compose_height:
            panel_height = compose_height
            panel_width = int(panel_height * 9 / 16)

        raw_asset_records: list[dict[str, Any]] = []
        panels: dict[str, Image.Image] = {}
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
            extension = self._guess_extension(payload["filename"], payload["content_type"], image_format)
            logger.debug(
                "Three-view source parsed user_id=%s actor_id=%s angle=%s filename=%s size=%s resolution=%sx%s format=%s",
                user_id,
                actor_id,
                angle,
                payload["filename"],
                len(file_data),
                width,
                height,
                image_format,
            )
            object_key = (
                f"portraits/raw/user_{user_id}/actor_{actor_id}/{date_prefix}/{session_key}/"
                f"{angle}_{uuid.uuid4().hex}.{extension}"
            )
            image_url = await self.storage_client.upload_file(
                object_key,
                file_data,
                payload["content_type"] or "application/octet-stream",
                bucket=settings.MINIO_PORTRAIT_RAW_BUCKET,
            )
            logger.debug(
                "Three-view raw image uploaded user_id=%s actor_id=%s angle=%s bucket=%s object_key=%s",
                user_id,
                actor_id,
                angle,
                settings.MINIO_PORTRAIT_RAW_BUCKET,
                object_key,
            )

            panels[angle] = ImageOps.fit(
                image,
                (panel_width, panel_height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            raw_asset_records.append(
                {
                    "view_angle": angle,
                    "bucket_name": settings.MINIO_PORTRAIT_RAW_BUCKET,
                    "object_key": object_key,
                    "image_url": image_url,
                    "source_filename": payload["filename"] or f"{angle}.{extension}",
                    "mime_type": payload["content_type"] or "application/octet-stream",
                    "file_size": len(file_data),
                    "width": width,
                    "height": height,
                    "expected_ratio": settings.PORTRAIT_EXPECTED_SINGLE_RATIO,
                }
            )

        composite_bytes = self._compose_three_view_image(
            panels=panels,
            width=compose_width,
            height=compose_height,
            order=settings.PORTRAIT_COMPOSE_ORDER,
        )
        composite_object_key = (
            f"portraits/generated/user_{user_id}/actor_{actor_id}/{date_prefix}/{session_key}/"
            f"upper_body_three_view_{uuid.uuid4().hex}.jpg"
        )
        composite_image_url = await self.storage_client.upload_file(
            composite_object_key,
            composite_bytes,
            "image/jpeg",
            bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
        )
        logger.debug(
            "Three-view composite uploaded user_id=%s actor_id=%s bucket=%s object_key=%s size=%s",
            user_id,
            actor_id,
            settings.MINIO_PORTRAIT_GENERATED_BUCKET,
            composite_object_key,
            len(composite_bytes),
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
                composite_object_key=composite_object_key,
                composite_image_url=composite_image_url,
                composite_width=compose_width,
                composite_height=compose_height,
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
                for record in raw_asset_records
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

        with database.allow_sync():
            latest_session = (
                PortraitUploadSessionModel.select()
                .where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
                )
                .order_by(PortraitUploadSessionModel.created_at.desc())
                .first()
            )
            if not latest_session:
                raise ValueError("暂无可修改的历史三视图，请先完成首次上传。")

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
            try:
                existing_data = await self.storage_client.download_file(
                    existing.object_key,
                    bucket=existing.bucket_name,
                )
            except Exception as exc:
                logger.exception(
                    "Three-view recompose failed to read historical asset user_id=%s session_id=%s angle=%s bucket=%s object_key=%s",
                    user_id,
                    latest_session.id,
                    angle,
                    existing.bucket_name,
                    existing.object_key,
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
        file_data: bytes,
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        if not file_data:
            logger.warning("Portrait video upload failed: empty file user_id=%s", user_id)
            raise ValueError("视频文件不能为空。")
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
            f"portraits/video/user_{user_id}/actor_{actor_id}/{date_prefix}/"
            f"{uuid.uuid4().hex}.{extension}"
        )
        logger.info(
            "Portrait video upload started user_id=%s actor_id=%s filename=%s size=%s content_type=%s",
            user_id,
            actor_id,
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
            bucket_name=settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            object_key=object_key,
            source_filename=filename or f"portrait_video.{extension}",
            mime_type=normalized_content_type,
            file_size=len(file_data),
        )

    async def upload_portrait_video_stream(
        self,
        user_id: int,
        user_display_name: str,
        upload_stream: BinaryIO,
        filename: str,
        content_type: str,
        declared_size: int | None = None,
    ) -> dict[str, Any]:
        normalized_content_type = content_type or "application/octet-stream"
        if not normalized_content_type.startswith("video/"):
            raise ValueError("请上传视频文件。")

        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        extension = Path(filename).suffix.lower().lstrip(".") or "mp4"
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = (
            f"portraits/video/user_{user_id}/actor_{actor_id}/{date_prefix}/"
            f"{uuid.uuid4().hex}.{extension}"
        )
        size = self._resolve_stream_size(upload_stream, declared_size)
        logger.info(
            "Portrait video stream upload started user_id=%s actor_id=%s filename=%s size=%s content_type=%s",
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
            bucket_name=settings.MINIO_PORTRAIT_VIDEO_BUCKET,
            object_key=object_key,
            source_filename=filename or f"portrait_video.{extension}",
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

        stat = self.storage_client.stat_object(object_key, bucket=bucket_name)
        file_size = int(stat.get("size", item.get("file_size", 0)) or 0)
        logger.info(
            "Commit video direct upload user_id=%s actor_id=%s bucket=%s object_key=%s size=%s",
            user_id,
            plan["actor_id"],
            bucket_name,
            object_key,
            file_size,
        )
        return await self._create_video_asset_record(
            actor_id=plan["actor_id"],
            user_id=user_id,
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
    ) -> list[dict[str, Any]]:
        with database.allow_sync():
            condition = PortraitVideoAssetModel.user_id == user_id
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

    async def get_current_portrait_video(self, user_id: int) -> Optional[dict[str, Any]]:
        with database.allow_sync():
            asset = (
                PortraitVideoAssetModel.select()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.is_current == True)  # noqa: E712
                )
                .order_by(PortraitVideoAssetModel.created_at.desc())
                .first()
            )
            if not asset:
                return None
        return self._serialize_video_asset(asset)

    async def get_video_state(self, user_id: int) -> dict[str, Any]:
        with database.allow_sync():
            draft = (
                PortraitVideoAssetModel.select()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.is_current == True)  # noqa: E712
                )
                .order_by(PortraitVideoAssetModel.created_at.desc())
                .first()
            )
            published = (
                PortraitVideoAssetModel.select()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.is_current == False)  # noqa: E712
                    & PortraitVideoAssetModel.superseded_at.is_null(True)
                )
                .order_by(PortraitVideoAssetModel.created_at.desc())
                .first()
            )
        return {
            "draft": self._serialize_video_asset(draft) if draft else None,
            "published": self._serialize_video_asset(published) if published else None,
        }

    async def publish_current_video(self, user_id: int, user_display_name: str) -> dict[str, Any]:
        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
        with database.allow_sync():
            now = datetime.now()
            draft = (
                PortraitVideoAssetModel.select()
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.actor_id == actor_id)
                    & (PortraitVideoAssetModel.is_current == True)  # noqa: E712
                )
                .order_by(PortraitVideoAssetModel.created_at.desc())
                .first()
            )
            if not draft:
                raise ValueError("暂无可发布的视频草稿，请先上传视频。")

            (
                PortraitVideoAssetModel.update(superseded_at=now)
                .where(
                    (PortraitVideoAssetModel.user_id == user_id)
                    & (PortraitVideoAssetModel.actor_id == actor_id)
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
            "Portrait video draft published user_id=%s actor_id=%s asset_id=%s",
            user_id,
            actor_id,
            draft.id,
        )
        return self._serialize_video_asset(draft)

    async def get_published_video_for_actor(self, actor_id: int) -> Optional[dict[str, Any]]:
        with database.allow_sync():
            asset = (
                PortraitVideoAssetModel.select()
                .where(
                    (PortraitVideoAssetModel.actor_id == actor_id)
                    & (PortraitVideoAssetModel.is_current == False)  # noqa: E712
                    & PortraitVideoAssetModel.superseded_at.is_null(True)
                )
                .order_by(PortraitVideoAssetModel.created_at.desc())
                .first()
            )
            if not asset:
                return None
        return self._serialize_video_asset(asset)

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
                (asset.bucket_name, asset.object_key)
                for asset in history_assets
            )

            deletable_objects = set(candidate_objects)
            skipped_objects = set()
            if purge_storage and candidate_objects:
                in_use_objects: set[tuple[str, str]] = {
                    (session.composite_bucket, session.composite_object_key)
                    for session in PortraitUploadSessionModel.select(
                        PortraitUploadSessionModel.composite_bucket,
                        PortraitUploadSessionModel.composite_object_key,
                    ).where(
                        (PortraitUploadSessionModel.user_id == user_id)
                        & (~(PortraitUploadSessionModel.id.in_(history_session_ids)))
                    )
                }
                in_use_objects.update(
                    (asset.bucket_name, asset.object_key)
                    for asset in PortraitUploadAssetModel.select(
                        PortraitUploadAssetModel.bucket_name,
                        PortraitUploadAssetModel.object_key,
                    ).where(
                        (PortraitUploadAssetModel.user_id == user_id)
                        & (~(PortraitUploadAssetModel.session_id.in_(history_session_ids)))
                    )
                )
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
                (asset.bucket_name, asset.object_key)
                for asset in superseded_assets
            )

            in_use_objects: set[tuple[str, str]] = {
                (session.composite_bucket, session.composite_object_key)
                for session in PortraitUploadSessionModel.select(
                    PortraitUploadSessionModel.composite_bucket,
                    PortraitUploadSessionModel.composite_object_key,
                ).where(
                    (PortraitUploadSessionModel.user_id == user_id)
                    & (PortraitUploadSessionModel.actor_id == actor_id)
                    & (~(PortraitUploadSessionModel.id.in_(session_ids)))
                )
            }
            in_use_objects.update(
                (asset.bucket_name, asset.object_key)
                for asset in PortraitUploadAssetModel.select(
                    PortraitUploadAssetModel.bucket_name,
                    PortraitUploadAssetModel.object_key,
                ).where(
                    (PortraitUploadAssetModel.user_id == user_id)
                    & (PortraitUploadAssetModel.actor_id == actor_id)
                    & (~(PortraitUploadAssetModel.session_id.in_(session_ids)))
                )
            )

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
        bucket_name: str,
        object_key: str,
        source_filename: str,
        mime_type: str,
        file_size: int,
    ) -> dict[str, Any]:
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
                    & (PortraitVideoAssetModel.is_current == True)  # noqa: E712
                )
                .execute()
            )
            if retired:
                logger.info(
                    "Portrait video current asset rotated user_id=%s actor_id=%s retired_count=%s",
                    user_id,
                    actor_id,
                    retired,
                )
            asset = PortraitVideoAssetModel.create(
                actor_id=actor_id,
                user_id=user_id,
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
            "Portrait video asset persisted user_id=%s actor_id=%s asset_id=%s bucket=%s object_key=%s",
            user_id,
            actor_id,
            asset.id,
            bucket_name,
            object_key,
        )
        await self._purge_superseded_video_versions(user_id=user_id, actor_id=actor_id)
        return self._serialize_video_asset(asset)

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
                latest_session = (
                    PortraitUploadSessionModel.select()
                    .where(
                        (PortraitUploadSessionModel.user_id == job.user_id)
                        & (PortraitUploadSessionModel.is_current == True)  # noqa: E712
                    )
                    .order_by(PortraitUploadSessionModel.created_at.desc())
                    .first()
                )
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
                source_map[angle] = {
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
        compose_width = max(300, settings.PORTRAIT_COMPOSE_WIDTH)
        compose_height = max(225, settings.PORTRAIT_COMPOSE_HEIGHT)
        session_key = uuid.uuid4().hex
        date_prefix = datetime.now().strftime("%Y/%m/%d")

        panel_width = compose_width // 3
        panel_height = int(panel_width * 16 / 9)
        if panel_height > compose_height:
            panel_height = compose_height
            panel_width = int(panel_height * 9 / 16)

        panels: dict[str, Image.Image] = {}
        raw_asset_records: list[dict[str, Any]] = []
        for angle in ("front", "left", "right"):
            source = source_map[angle]
            bucket_name = str(source["bucket_name"])
            object_key = str(source["object_key"])
            file_data = await self.storage_client.download_file(object_key, bucket=bucket_name)
            image, width, height, _ = self._read_image(file_data)
            panels[angle] = ImageOps.fit(
                image,
                (panel_width, panel_height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            raw_asset_records.append(
                {
                    "view_angle": angle,
                    "bucket_name": bucket_name,
                    "object_key": object_key,
                    "image_url": str(source.get("image_url") or f"{bucket_name}/{object_key}"),
                    "source_filename": str(source.get("source_filename") or f"{angle}.jpg"),
                    "mime_type": str(source.get("mime_type") or "application/octet-stream"),
                    "file_size": int(source.get("file_size") or len(file_data)),
                    "width": width,
                    "height": height,
                    "expected_ratio": settings.PORTRAIT_EXPECTED_SINGLE_RATIO,
                }
            )

        composite_bytes = self._compose_three_view_image(
            panels=panels,
            width=compose_width,
            height=compose_height,
            order=settings.PORTRAIT_COMPOSE_ORDER,
        )
        composite_object_key = (
            f"portraits/generated/user_{user_id}/actor_{actor_id}/{date_prefix}/{session_key}/"
            f"upper_body_three_view_{uuid.uuid4().hex}.jpg"
        )
        composite_image_url = await self.storage_client.upload_file(
            composite_object_key,
            composite_bytes,
            "image/jpeg",
            bucket=settings.MINIO_PORTRAIT_GENERATED_BUCKET,
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
                composite_object_key=composite_object_key,
                composite_image_url=composite_image_url,
                composite_width=compose_width,
                composite_height=compose_height,
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
                for record in raw_asset_records
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
                    "height": 0,
                    "bio": "Auto-created actor profile for individual uploads.",
                    "tags": ["self-upload"],
                    "is_published": False,
                },
            )
        if _created:
            logger.info("Auto-created actor for user user_id=%s actor_id=%s", user_id, actor.id)
        else:
            logger.debug("Resolved existing actor for user user_id=%s actor_id=%s", user_id, actor.id)
        return int(actor.id)

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

    def _compose_three_view_image(
        self,
        panels: dict[str, Image.Image],
        width: int,
        height: int,
        order: tuple[str, str, str],
    ) -> bytes:
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

        output = BytesIO()
        canvas.save(output, format="JPEG", quality=95, optimize=True)
        return output.getvalue()

    def _serialize_three_view_session(
        self,
        session: PortraitUploadSessionModel,
        assets: list[PortraitUploadAssetModel],
    ) -> dict[str, Any]:
        raw_images = [
            {
                "id": asset.id,
                "view_angle": asset.view_angle,
                "image_url": asset.image_url,
                "preview_url": self.storage_client.get_url(asset.object_key, bucket=asset.bucket_name),
                "bucket_name": asset.bucket_name,
                "object_key": asset.object_key,
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
            "composite_preview_url": self.storage_client.get_url(
                session.composite_object_key,
                bucket=session.composite_bucket,
            ),
            "composite_bucket": session.composite_bucket,
            "composite_object_key": session.composite_object_key,
            "composite_width": session.composite_width,
            "composite_height": session.composite_height,
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

    async def generate_result(self, user_id: int, user_display_name: str, style_id: int) -> dict[str, Any]:
        self._ensure_default_style_catalog()
        style = await self.style_repo.get_by_id(style_id)
        if not style:
            raise ValueError("风格不存在。")

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
            (
                GeneratedResultModel.update(
                    lifecycle_state="superseded",
                    superseded_at=now,
                )
                .where(
                    (GeneratedResultModel.user_id == user_id)
                    & (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.style_id == style_id)
                    & (GeneratedResultModel.lifecycle_state == "draft")
                )
                .execute()
            )
            saved = GeneratedResultModel.create(
                actor_id=actor_id,
                user_id=user_id,
                style_id=style_id,
                image_url=image_url,
                lifecycle_state="draft",
                superseded_at=None,
                published_at=None,
                created_at=now,
            )

        await self._purge_superseded_style_versions(
            user_id=user_id,
            actor_id=actor_id,
            style_id=style_id,
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
        grouped_state: dict[int, dict[str, dict[str, Any] | None]] = {}
        for row in rows:
            style = style_map.get(int(row.style_id))
            if not style:
                continue
            bucket = grouped_state.setdefault(
                int(row.style_id),
                {"draft": None, "published": None},
            )
            if row.lifecycle_state == "draft" and bucket["draft"] is None:
                bucket["draft"] = self._serialize_generated_result(row, style)
            elif row.lifecycle_state == "published" and bucket["published"] is None:
                bucket["published"] = self._serialize_generated_result(row, style)

        groups = []
        for style in styles:
            if style.id is None:
                continue
            state_bucket = grouped_state.get(int(style.id), {"draft": None, "published": None})
            groups.append(
                {
                    "style_id": int(style.id),
                    "style_name": style.name,
                    "style_category": style.category,
                    "draft_result": state_bucket["draft"],
                    "published_result": state_bucket["published"],
                }
            )
        return {"groups": groups}

    async def publish_draft_result(self, user_id: int, user_display_name: str, style_id: int) -> dict[str, Any]:
        self._ensure_default_style_catalog()
        style = await self.style_repo.get_by_id(style_id)
        if not style:
            raise ValueError("风格不存在。")

        actor_id = self._resolve_actor_for_user(user_id=user_id, user_display_name=user_display_name)
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

            (
                GeneratedResultModel.update(
                    lifecycle_state="superseded",
                    superseded_at=now,
                )
                .where(
                    (GeneratedResultModel.user_id == user_id)
                    & (GeneratedResultModel.actor_id == actor_id)
                    & (GeneratedResultModel.style_id == style_id)
                    & (GeneratedResultModel.lifecycle_state == "published")
                )
                .execute()
            )

            draft.lifecycle_state = "published"
            draft.superseded_at = None
            draft.published_at = now
            draft.save()

            (
                ActorModel.update(is_published=True)
                .where(ActorModel.id == actor_id)
                .execute()
            )

        await self._purge_superseded_style_versions(
            user_id=user_id,
            actor_id=actor_id,
            style_id=style_id,
        )
        logger.info(
            "Style draft published user_id=%s actor_id=%s style_id=%s result_id=%s",
            user_id,
            actor_id,
            style_id,
            draft.id,
        )
        return self._serialize_generated_result(draft, style)

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
            "lifecycle_state": getattr(result, "lifecycle_state", "published"),
            "published_at": getattr(result, "published_at", None),
            "created_at": result.created_at,
        }

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


class ProtocolService:
    def __init__(self, protocol_repo: ProtocolRepository):
        self.protocol_repo = protocol_repo

    async def list_protocols(self, actor_id: int) -> List[Protocol]:
        return await self.protocol_repo.list_by_actor(actor_id)

    async def get_protocol(self, protocol_id: int) -> Optional[Protocol]:
        return await self.protocol_repo.get_by_id(protocol_id)

    async def sign_protocol(self, protocol_id: int) -> bool:
        return await self.protocol_repo.update_status(protocol_id, "signed")

    async def reject_protocol(self, protocol_id: int) -> bool:
        return await self.protocol_repo.update_status(protocol_id, "rejected")
