from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
import logging
from typing import List, Literal, Optional
from backend.application.agreement_service import ensure_enterprise_agreement_signed, is_actor_agreement_currently_signed
from backend.interface.api.schemas import (
    ActorBasicInfoSchema,
    ActorBasicInfoUpdateRequest,
    ActorSchema,
    EnterpriseActorSigningActionSchema,
    EnterpriseSignedActorCardSchema,
    GenerateStyleRequest,
    GeneratedResultSchema,
    HistoryCleanupResultSchema,
    PortraitAudioListSchema,
    PortraitAudioPublishToggleRequest,
    PortraitAudioSchema,
    PublishedActorCardSchema,
    PublishedActorDetailSchema,
    PortraitSchema,
    PortraitVideoDirectUploadCommitRequest,
    PortraitVideoDirectUploadPlanRequest,
    PortraitVideoDirectUploadPlanSchema,
    PortraitVideoListSchema,
    PortraitVideoPublishRequest,
    PortraitVideoSchema,
    PortraitVideoStateSchema,
    StylePublishRequest,
    StyleResultStateToggleRequest,
    StyleResultGroupListSchema,
    SignedEnterpriseSchema,
    StyleSchema,
    ThreeViewComposeJobCreateRequest,
    ThreeViewComposeJobSchema,
    ThreeViewDirectUploadPlanRequest,
    ThreeViewDirectUploadPlanSchema,
    ThreeViewHistorySchema,
    ThreeViewStateSchema,
    ThreeViewUploadSchema,
)
from backend.application.services import ActorService, PortraitService, StyleService
from backend.interface.api.auth_routes import require_enterprise_user, require_individual_user
from backend.infrastructure.repositories import (
    PeeweeActorRepository, PeeweePortraitRepository,
    PeeweeStyleRepository,
    PeeweeGeneratedResultRepository
)
from backend.infrastructure.orm_models import ActorModel, EnterpriseActorSigningModel, UserModel, database

router = APIRouter()
logger = logging.getLogger(__name__)

def get_actor_service():
    return ActorService(PeeweeActorRepository())

def get_portrait_service():
    from backend.infrastructure.storage import StorageClient
    from backend.infrastructure.config import settings
    storage_client = StorageClient(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY,
        settings.MINIO_BUCKET,
        secure=settings.MINIO_SECURE,
        public_base_url=settings.MINIO_PUBLIC_BASE_URL,
    )
    return PortraitService(PeeweePortraitRepository(), storage_client)

def get_style_service():
    from backend.infrastructure.storage import StorageClient
    from backend.infrastructure.config import settings
    storage_client = StorageClient(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY,
        settings.MINIO_BUCKET,
        secure=settings.MINIO_SECURE,
        public_base_url=settings.MINIO_PUBLIC_BASE_URL,
    )
    return StyleService(
        PeeweeStyleRepository(),
        PeeweeGeneratedResultRepository(),
        storage_client,
    )


async def _build_actor_card_payload(
    actor: ActorModel,
    portrait_service: PortraitService,
    style_service: StyleService,
    *,
    require_visible_materials: bool,
    signed_at: datetime | None = None,
) -> dict | None:
    published_three = await portrait_service.get_published_three_view_for_actor(actor.id)
    published_videos = await portrait_service.get_published_videos_for_actor(actor.id)
    published_video = portrait_service.pick_primary_published_video(published_videos)
    published_audios = await portrait_service.get_published_audios_for_actor(actor.id)
    style_preview, style_count = await style_service.get_published_result_summary_for_actor(actor.id)
    has_visible_materials = bool(published_three or published_video or style_preview or published_audios)
    if require_visible_materials and not has_visible_materials:
        return None

    cover_image_url = None
    if style_preview:
        cover_image_url = style_preview.get("preview_url") or style_preview.get("image_url")
    elif published_three:
        cover_image_url = published_three.get("composite_preview_url") or published_three.get("composite_image_url")
    elif published_video:
        cover_image_url = published_video.get("preview_url") or published_video.get("video_url")

    updated_at = actor.created_at
    timestamps = []
    if published_three and published_three.get("created_at"):
        timestamps.append(published_three["created_at"])
    for video in published_videos:
        if video.get("created_at"):
            timestamps.append(video["created_at"])
    for audio in published_audios:
        if audio.get("created_at"):
            timestamps.append(audio["created_at"])
    if style_preview and style_preview.get("published_at"):
        timestamps.append(style_preview["published_at"])
    if timestamps:
        updated_at = max(timestamps)

    payload = {
        "actor_id": actor.id,
        "name": actor.name,
        "external_id": actor.external_id,
        "tags": actor.tags or [],
        "cover_image_url": cover_image_url,
        "published_three_view_url": (
            published_three.get("composite_preview_url")
            if published_three else None
        ),
        "published_video_url": (
            published_video.get("preview_url")
            if published_video else None
        ),
        "published_style_count": int(style_count),
        "published_audio_count": len(published_audios),
        "updated_at": updated_at,
    }
    if signed_at is not None:
        payload["signed_at"] = signed_at
    return payload


def _serialize_signed_enterprise(user: UserModel, signed_at: datetime) -> dict:
    return {
        "enterprise_user_id": int(user.id),
        "company_name": user.display_name,
        "company_intro": user.company_intro or "",
        "credit_code": str(getattr(user, "company_credit_code", "") or ""),
        "registered_address": str(getattr(user, "company_registered_address", "") or ""),
        "signed_at": signed_at,
        "created_at": user.created_at,
    }

@router.get("/actors", response_model=List[ActorSchema])
async def list_actors(
    tag: Optional[str] = None,
    service: ActorService = Depends(get_actor_service),
    _current_user=Depends(require_enterprise_user),
):
    actors = await service.list_actors(tag=tag)
    logger.info("Actors listed count=%s tag=%s", len(actors), tag or "-")
    return actors

@router.get("/actors/{actor_id}", response_model=ActorSchema)
async def get_actor(
    actor_id: int,
    service: ActorService = Depends(get_actor_service),
    _current_user=Depends(require_enterprise_user),
):
    actor = await service.get_actor(actor_id)
    if not actor:
        logger.warning("Actor not found actor_id=%s", actor_id)
        raise HTTPException(status_code=404, detail="Actor not found")
    logger.info("Actor fetched actor_id=%s", actor_id)
    return actor


@router.get("/actors/me/basic-info", response_model=ActorBasicInfoSchema)
async def get_my_actor_basic_info(
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    return await service.get_actor_basic_info(
        user_id=current_user.id,
        user_display_name=current_user.display_name,
    )


@router.put("/actors/me/basic-info", response_model=ActorBasicInfoSchema)
async def update_my_actor_basic_info(
    req: ActorBasicInfoUpdateRequest,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        return await service.update_actor_basic_info(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            payload=req.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/enterprise/discovery/actors", response_model=List[PublishedActorCardSchema])
async def list_published_actor_cards(
    limit: int = Query(default=100, ge=1, le=500),
    portrait_service: PortraitService = Depends(get_portrait_service),
    style_service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_enterprise_user),
):
    try:
        ensure_enterprise_agreement_signed(current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    with database.allow_sync():
        actors = list(
            ActorModel.select()
            .where(ActorModel.is_published == True)  # noqa: E712
            .order_by(ActorModel.created_at.desc())
            .limit(limit)
        )

    cards: list[dict] = []
    for actor in actors:
        if not is_actor_agreement_currently_signed(int(actor.id)):
            continue
        payload = await _build_actor_card_payload(
            actor,
            portrait_service,
            style_service,
            require_visible_materials=True,
        )
        if payload:
            cards.append(payload)
    return cards


@router.get("/enterprise/discovery/actors/{actor_id}", response_model=PublishedActorDetailSchema)
async def get_published_actor_detail(
    actor_id: int,
    portrait_service: PortraitService = Depends(get_portrait_service),
    style_service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_enterprise_user),
):
    try:
        ensure_enterprise_agreement_signed(current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    actor = await portrait_service.get_actor_basic_info_by_actor_id(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    with database.allow_sync():
        is_signed_by_current_enterprise = bool(
            EnterpriseActorSigningModel.get_or_none(
                (EnterpriseActorSigningModel.enterprise_user == current_user.id)
                & (EnterpriseActorSigningModel.actor == actor_id)
            )
        )
    is_publicly_visible = is_actor_agreement_currently_signed(actor_id)
    if not is_publicly_visible and not is_signed_by_current_enterprise:
        raise HTTPException(status_code=404, detail="Actor not found")

    published_three = await portrait_service.get_published_three_view_for_actor(actor_id)
    published_videos = await portrait_service.get_published_videos_for_actor(actor_id)
    published_video = portrait_service.pick_primary_published_video(published_videos)
    published_audios = await portrait_service.get_published_audios_for_actor(actor_id)
    published_styles = await style_service.list_published_results_by_actor(actor_id=actor_id, limit=200)
    if not published_three and not published_video and not published_audios and not published_styles and not is_signed_by_current_enterprise:
        raise HTTPException(status_code=404, detail="No published materials for this actor")

    return {
        "actor": actor,
        "published_three_view": published_three,
        "published_video": published_video,
        "published_videos": published_videos,
        "published_audios": published_audios,
        "published_styles": published_styles,
        "is_signed_by_current_enterprise": is_signed_by_current_enterprise,
    }


@router.post("/enterprise/signed-actors/{actor_id}", response_model=EnterpriseActorSigningActionSchema)
async def sign_actor_for_enterprise(
    actor_id: int,
    current_user: UserModel = Depends(require_enterprise_user),
):
    try:
        ensure_enterprise_agreement_signed(current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    with database.allow_sync():
        actor = ActorModel.get_or_none(ActorModel.id == actor_id)
        if not actor or not actor.is_published:
            raise HTTPException(status_code=404, detail="演员不存在或暂不可签约。")
    if not is_actor_agreement_currently_signed(actor_id):
        raise HTTPException(status_code=400, detail="该演员当前未完成协议签署，暂不可签约。")

    with database.allow_sync():
        signing, created = EnterpriseActorSigningModel.get_or_create(
            enterprise_user=current_user,
            actor=actor,
            defaults={"signed_at": datetime.now()},
        )

    return {
        "actor_id": int(actor.id),
        "enterprise_user_id": int(current_user.id),
        "signed_at": signing.signed_at,
        "already_signed": not created,
        "message": "已签约该演员，可在签约演员中查看。" if created else "该演员已在签约列表中。",
    }


@router.get("/enterprise/signed-actors", response_model=List[EnterpriseSignedActorCardSchema])
async def list_enterprise_signed_actors(
    portrait_service: PortraitService = Depends(get_portrait_service),
    style_service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_enterprise_user),
):
    try:
        ensure_enterprise_agreement_signed(current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    with database.allow_sync():
        signings = list(
            EnterpriseActorSigningModel.select(EnterpriseActorSigningModel, ActorModel)
            .join(ActorModel)
            .where(EnterpriseActorSigningModel.enterprise_user == current_user.id)
            .order_by(EnterpriseActorSigningModel.signed_at.desc())
        )

    cards: list[dict] = []
    for signing in signings:
        payload = await _build_actor_card_payload(
            signing.actor,
            portrait_service,
            style_service,
            require_visible_materials=False,
            signed_at=signing.signed_at,
        )
        if payload:
            cards.append(payload)
    return cards


@router.get("/actors/me/signed-enterprises", response_model=List[SignedEnterpriseSchema])
async def list_actor_signed_enterprises(
    current_user: UserModel = Depends(require_individual_user),
):
    actor_external_id = f"USER-{current_user.id}"
    with database.allow_sync():
        actor = ActorModel.get_or_none(ActorModel.external_id == actor_external_id)
        if not actor:
            return []
        signings = list(
            EnterpriseActorSigningModel.select(EnterpriseActorSigningModel, UserModel)
            .join(UserModel, on=(EnterpriseActorSigningModel.enterprise_user == UserModel.id))
            .where(EnterpriseActorSigningModel.actor == actor.id)
            .order_by(EnterpriseActorSigningModel.signed_at.desc())
        )

    return [
        _serialize_signed_enterprise(signing.enterprise_user, signing.signed_at)
        for signing in signings
    ]


@router.get("/actors/me/signed-enterprises/{enterprise_user_id}", response_model=SignedEnterpriseSchema)
async def get_actor_signed_enterprise_detail(
    enterprise_user_id: int,
    current_user: UserModel = Depends(require_individual_user),
):
    actor_external_id = f"USER-{current_user.id}"
    with database.allow_sync():
        actor = ActorModel.get_or_none(ActorModel.external_id == actor_external_id)
        if not actor:
            raise HTTPException(status_code=404, detail="未找到当前演员资料。")
        signing = (
            EnterpriseActorSigningModel.select(EnterpriseActorSigningModel, UserModel)
            .join(UserModel, on=(EnterpriseActorSigningModel.enterprise_user == UserModel.id))
            .where(
                (EnterpriseActorSigningModel.actor == actor.id)
                & (EnterpriseActorSigningModel.enterprise_user == enterprise_user_id)
            )
            .first()
        )
    if not signing:
        raise HTTPException(status_code=404, detail="未找到该企业的签约记录。")

    return _serialize_signed_enterprise(signing.enterprise_user, signing.signed_at)

@router.post("/portraits", response_model=PortraitSchema)
async def upload_portrait(
    actor_id: int,
    portrait_type: str,
    file: UploadFile = File(...),
    service: PortraitService = Depends(get_portrait_service),
    _current_user=Depends(require_individual_user),
):
    data = await file.read()
    logger.info(
        "Portrait upload received actor_id=%s portrait_type=%s filename=%s size=%s",
        actor_id,
        portrait_type,
        file.filename,
        len(data),
    )
    return await service.upload_portrait(actor_id, portrait_type, data, file.filename)


@router.post("/portraits/three-view/presign", response_model=ThreeViewDirectUploadPlanSchema)
async def prepare_three_view_direct_upload_plan(
    req: ThreeViewDirectUploadPlanRequest,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        logger.info(
            "Prepare three-view direct upload plan user_id=%s file_count=%s",
            current_user.id,
            len(req.files),
        )
        return await service.prepare_three_view_direct_upload(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            files=[item.model_dump() for item in req.files],
        )
    except ValueError as exc:
        logger.warning("Prepare three-view upload plan rejected user_id=%s reason=%s", current_user.id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portraits/three-view", response_model=ThreeViewUploadSchema)
async def upload_three_view_portraits(
    left_image: UploadFile = File(...),
    front_image: UploadFile = File(...),
    right_image: UploadFile = File(...),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    payload = {
        "left": {
            "data": await left_image.read(),
            "filename": left_image.filename or "left.jpg",
            "content_type": left_image.content_type or "application/octet-stream",
        },
        "front": {
            "data": await front_image.read(),
            "filename": front_image.filename or "front.jpg",
            "content_type": front_image.content_type or "application/octet-stream",
        },
        "right": {
            "data": await right_image.read(),
            "filename": right_image.filename or "right.jpg",
            "content_type": right_image.content_type or "application/octet-stream",
        },
    }
    try:
        logger.info(
            "Three-view upload received user_id=%s files=(%s,%s,%s)",
            current_user.id,
            left_image.filename,
            front_image.filename,
            right_image.filename,
        )
        return await service.upload_three_view_set(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            images=payload,
        )
    except ValueError as exc:
        logger.warning("Three-view upload rejected user_id=%s reason=%s", current_user.id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/portraits/three-view/history", response_model=ThreeViewHistorySchema)
async def get_three_view_portrait_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_current: bool = Query(default=False),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    logger.info(
        "Three-view history query user_id=%s limit=%s offset=%s include_current=%s",
        current_user.id,
        limit,
        offset,
        include_current,
    )
    items = await service.list_three_view_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        include_current=include_current,
    )
    return {"items": items}


@router.get("/portraits/three-view/current", response_model=Optional[ThreeViewUploadSchema])
async def get_three_view_current(
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    return await service.get_current_three_view(user_id=current_user.id)


@router.get("/portraits/three-view/state", response_model=ThreeViewStateSchema)
async def get_three_view_state(
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    return await service.get_three_view_state(user_id=current_user.id)


@router.post("/portraits/three-view/publish", response_model=ThreeViewUploadSchema)
async def publish_three_view_draft(
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        return await service.publish_current_three_view(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portraits/three-view/jobs", response_model=ThreeViewComposeJobSchema)
async def create_three_view_compose_job(
    req: ThreeViewComposeJobCreateRequest,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        logger.info(
            "Create three-view compose job user_id=%s reuse_latest_missing=%s",
            current_user.id,
            req.reuse_latest_missing,
        )
        return await service.create_three_view_compose_job(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            upload_plan_token=req.upload_plan_token,
            reuse_latest_missing=req.reuse_latest_missing,
        )
    except ValueError as exc:
        logger.warning("Create compose job rejected user_id=%s reason=%s", current_user.id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/portraits/three-view/jobs/{job_key}", response_model=ThreeViewComposeJobSchema)
async def get_three_view_compose_job(
    job_key: str,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    job = await service.get_three_view_compose_job(
        user_id=current_user.id,
        job_key=job_key,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Compose job not found")
    return job


@router.post("/portraits/three-view/recompose", response_model=ThreeViewUploadSchema)
async def recompose_three_view_portraits(
    left_image: Optional[UploadFile] = File(default=None),
    front_image: Optional[UploadFile] = File(default=None),
    right_image: Optional[UploadFile] = File(default=None),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    payload = {}
    if left_image is not None:
        payload["left"] = {
            "data": await left_image.read(),
            "filename": left_image.filename or "left.jpg",
            "content_type": left_image.content_type or "application/octet-stream",
        }
    if front_image is not None:
        payload["front"] = {
            "data": await front_image.read(),
            "filename": front_image.filename or "front.jpg",
            "content_type": front_image.content_type or "application/octet-stream",
        }
    if right_image is not None:
        payload["right"] = {
            "data": await right_image.read(),
            "filename": right_image.filename or "right.jpg",
            "content_type": right_image.content_type or "application/octet-stream",
        }

    try:
        logger.info(
            "Three-view recompose request user_id=%s replace_angles=%s",
            current_user.id,
            ",".join(sorted(payload.keys())) or "-",
        )
        return await service.recompose_three_view_set(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            images=payload,
        )
    except ValueError as exc:
        logger.warning("Three-view recompose rejected user_id=%s reason=%s", current_user.id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portraits/videos/presign", response_model=PortraitVideoDirectUploadPlanSchema)
async def prepare_video_direct_upload_plan(
    req: PortraitVideoDirectUploadPlanRequest,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        logger.info("Prepare video direct upload plan user_id=%s filename=%s", current_user.id, req.filename)
        return await service.prepare_video_direct_upload(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            video_type=req.video_type,
            filename=req.filename,
            content_type=req.content_type,
            size=req.size,
        )
    except ValueError as exc:
        logger.warning("Prepare video upload plan rejected user_id=%s reason=%s", current_user.id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portraits/videos/commit", response_model=PortraitVideoSchema)
async def commit_video_direct_upload(
    req: PortraitVideoDirectUploadCommitRequest,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        logger.info("Commit video direct upload user_id=%s", current_user.id)
        return await service.commit_video_direct_upload(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            upload_plan_token=req.upload_plan_token,
        )
    except ValueError as exc:
        logger.warning("Commit video direct upload rejected user_id=%s reason=%s", current_user.id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portraits/videos", response_model=PortraitVideoSchema)
async def upload_portrait_video(
    video_file: UploadFile = File(...),
    video_type: Literal["intro", "showreel"] = Form(...),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        declared_size = None
        if hasattr(video_file, "size"):
            declared_size = getattr(video_file, "size")
        logger.info(
            "Portrait video upload received user_id=%s filename=%s content_type=%s",
            current_user.id,
            video_file.filename,
            video_file.content_type,
        )
        return await service.upload_portrait_video_stream(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            video_type=video_type,
            upload_stream=video_file.file,
            filename=video_file.filename or "portrait_video.mp4",
            content_type=video_file.content_type or "application/octet-stream",
            declared_size=declared_size,
        )
    except ValueError as exc:
        logger.warning("Portrait video upload rejected user_id=%s reason=%s", current_user.id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/portraits/videos", response_model=PortraitVideoListSchema)
async def list_portrait_videos(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_current: bool = Query(default=False),
    video_type: Optional[Literal["intro", "showreel"]] = Query(default=None),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    logger.info(
        "Portrait video list query user_id=%s limit=%s offset=%s include_current=%s",
        current_user.id,
        limit,
        offset,
        include_current,
    )
    items = await service.list_portrait_videos(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        include_current=include_current,
        video_type=video_type,
    )
    return {"items": items}


@router.get("/portraits/videos/current", response_model=Optional[PortraitVideoSchema])
async def get_current_portrait_video(
    video_type: Optional[Literal["intro", "showreel"]] = Query(default=None),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    return await service.get_current_portrait_video(user_id=current_user.id, video_type=video_type)


@router.get("/portraits/videos/state", response_model=PortraitVideoStateSchema)
async def get_portrait_video_state(
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    return await service.get_video_state(user_id=current_user.id)


@router.post("/portraits/videos/publish", response_model=PortraitVideoSchema)
async def publish_portrait_video_draft(
    req: PortraitVideoPublishRequest,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        return await service.publish_current_video(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            video_type=req.video_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portraits/audios", response_model=PortraitAudioSchema)
async def upload_portrait_audio(
    audio_file: UploadFile = File(...),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        declared_size = None
        if hasattr(audio_file, "size"):
            declared_size = getattr(audio_file, "size")
        logger.info(
            "Portrait audio upload received user_id=%s filename=%s content_type=%s",
            current_user.id,
            audio_file.filename,
            audio_file.content_type,
        )
        return await service.upload_portrait_audio_stream(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            upload_stream=audio_file.file,
            filename=audio_file.filename or "portrait_audio.mp3",
            content_type=audio_file.content_type or "application/octet-stream",
            declared_size=declared_size,
        )
    except ValueError as exc:
        logger.warning("Portrait audio upload rejected user_id=%s reason=%s", current_user.id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/portraits/audios", response_model=PortraitAudioListSchema)
async def list_portrait_audios(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    logger.info(
        "Portrait audio list query user_id=%s limit=%s offset=%s",
        current_user.id,
        limit,
        offset,
    )
    items = await service.list_portrait_audios(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return {"items": items}


@router.post("/portraits/audios/state", response_model=PortraitAudioSchema)
async def toggle_portrait_audio_state(
    req: PortraitAudioPublishToggleRequest,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        return await service.toggle_portrait_audio_publish(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            audio_id=req.audio_id,
            published=req.published,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/portraits/audios/{audio_id}")
async def delete_portrait_audio(
    audio_id: int,
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        await service.delete_portrait_audio(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            audio_id=audio_id,
        )
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/portraits/three-view/history", response_model=HistoryCleanupResultSchema)
async def cleanup_three_view_history(
    purge_storage: bool = Query(default=True),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    logger.info(
        "Three-view history cleanup requested user_id=%s purge_storage=%s",
        current_user.id,
        purge_storage,
    )
    return await service.cleanup_three_view_history(
        user_id=current_user.id,
        purge_storage=purge_storage,
    )


@router.delete("/portraits/videos/history", response_model=HistoryCleanupResultSchema)
async def cleanup_portrait_video_history(
    purge_storage: bool = Query(default=True),
    service: PortraitService = Depends(get_portrait_service),
    current_user: UserModel = Depends(require_individual_user),
):
    logger.info(
        "Portrait video history cleanup requested user_id=%s purge_storage=%s",
        current_user.id,
        purge_storage,
    )
    return await service.cleanup_video_history(
        user_id=current_user.id,
        purge_storage=purge_storage,
    )


@router.get("/styles", response_model=List[StyleSchema])
async def list_styles(
    service: StyleService = Depends(get_style_service),
    _current_user=Depends(require_individual_user),
):
    styles = await service.list_styles()
    logger.info("Styles listed count=%s", len(styles))
    return styles

@router.post("/styles/generate", response_model=GeneratedResultSchema)
async def generate_style(
    req: GenerateStyleRequest,
    service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_individual_user),
):
    logger.info("Generate style request user_id=%s style_id=%s", current_user.id, req.style_id)
    try:
        return await service.generate_result(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            style_id=req.style_id,
            custom_prompt=req.custom_prompt,
        )
    except ValueError as exc:
        logger.warning("Generate style rejected user_id=%s style_id=%s reason=%s", current_user.id, req.style_id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Generate style failed user_id=%s style_id=%s reason=%s", current_user.id, req.style_id, str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/styles/upload", response_model=GeneratedResultSchema)
async def upload_custom_style_image(
    style_id: int = Form(...),
    image_file: UploadFile = File(...),
    service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_individual_user),
):
    payload = await image_file.read()
    logger.info(
        "Upload custom style image request user_id=%s style_id=%s filename=%s size=%s",
        current_user.id,
        style_id,
        image_file.filename,
        len(payload),
    )
    try:
        return await service.upload_custom_result(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            style_id=style_id,
            file_data=payload,
            filename=image_file.filename or "custom-upload.jpg",
            content_type=image_file.content_type or "image/jpeg",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/styles/publish", response_model=GeneratedResultSchema)
async def publish_style_draft(
    req: StylePublishRequest,
    service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        return await service.publish_draft_result(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            style_id=req.style_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/styles/result-state", response_model=GeneratedResultSchema)
async def toggle_style_result_state(
    req: StyleResultStateToggleRequest,
    service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        return await service.toggle_result_state(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            result_id=req.result_id,
            published=req.published,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/styles/results/{result_id}")
async def delete_style_result(
    result_id: int,
    service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        await service.delete_result(
            user_id=current_user.id,
            user_display_name=current_user.display_name,
            result_id=result_id,
        )
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/styles/results", response_model=StyleResultGroupListSchema)
async def list_style_results(
    limit_per_style: int = Query(default=20, ge=1, le=100),
    service: StyleService = Depends(get_style_service),
    current_user: UserModel = Depends(require_individual_user),
):
    logger.info("List style results user_id=%s limit_per_style=%s", current_user.id, limit_per_style)
    return await service.list_results_grouped(
        user_id=current_user.id,
        user_display_name=current_user.display_name,
        limit_per_style=limit_per_style,
    )
