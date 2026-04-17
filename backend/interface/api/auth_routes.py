from datetime import datetime, timedelta
import logging
from pathlib import Path
import re
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.application.agreement_service import AgreementFieldValidationError, AgreementService
from backend.config import get_config
from backend.infrastructure.config import settings
from backend.infrastructure.orm_models import (
    PortraitGuidanceSampleModel,
    SessionModel,
    UserModel,
    database,
)
from backend.infrastructure.security import generate_session_token, hash_password, verify_password
from backend.infrastructure.storage import StorageClient
from backend.interface.api.auth_schemas import (
    AdminCreateEnterpriseUserRequest,
    AdminAgreementTemplateUpdateRequest,
    AdminEnterpriseUserSchema,
    AdminUpdateEnterpriseUserRequest,
    ActorAgreementSignRequest,
    ActorAgreementViewSchema,
    EnterpriseBasicInfoSchema,
    EnterpriseBasicInfoUpdateRequest,
    EnterpriseAgreementSignRequest,
    EnterpriseAgreementViewSchema,
    AgreementStatusSchema,
    AgreementTemplateSchema,
    AuthResponse,
    LoginRequest,
    MessageResponse,
    PortraitGuidanceSampleSchema,
    PortraitGuidanceSampleStateSchema,
    RegisterRequest,
    UserSchema,
)


router = APIRouter()
SESSION_TTL_HOURS = int(get_config("auth.session_ttl_hours", int(get_config("auth.session_ttl_days", 1)) * 24))
DEFAULT_ADMIN_USERNAME = str(get_config("auth.admin.username", "admin"))
DEFAULT_ADMIN_PASSWORD = str(get_config("auth.admin.password", "Admin@123456"))
DEFAULT_ADMIN_DISPLAY_NAME = str(get_config("auth.admin.display_name", "系统管理员"))
logger = logging.getLogger(__name__)
PHONE_PATTERN = re.compile(r"^1\d{10}$")


def _normalize_phone(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def _validate_phone(value: str) -> str:
    phone = _normalize_phone(value)
    if not PHONE_PATTERN.fullmatch(phone):
        raise HTTPException(status_code=422, detail="手机号格式不正确")
    return phone


def _to_user_schema(user: UserModel) -> UserSchema:
    return UserSchema(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        company_intro=user.company_intro,
        role=user.role,
        created_at=user.created_at,
    )


def _to_admin_enterprise_user_schema(user: UserModel) -> AdminEnterpriseUserSchema:
    return AdminEnterpriseUserSchema(
        id=user.id,
        username=user.username,
        company_name=user.display_name,
        company_intro=user.company_intro or "",
        created_at=user.created_at,
    )


def _enterprise_basic_info_field_errors(payload: dict) -> dict[str, str]:
    company_name = str(payload.get("company_name") or "").strip()
    credit_code = str(payload.get("credit_code") or "").strip()
    registered_address = str(payload.get("registered_address") or "").strip()

    errors: dict[str, str] = {}
    if not company_name:
        errors["company_name"] = "请填写企业名称。"
    if not credit_code:
        errors["credit_code"] = "请填写统一社会信用代码。"
    if not registered_address:
        errors["registered_address"] = "请填写注册地址。"
    return errors


def _to_enterprise_basic_info_schema(user: UserModel) -> EnterpriseBasicInfoSchema:
    company_name = str(user.display_name or "").strip()
    credit_code = str(getattr(user, "company_credit_code", "") or "").strip()
    registered_address = str(getattr(user, "company_registered_address", "") or "").strip()
    return EnterpriseBasicInfoSchema(
        user_id=user.id,
        company_name=company_name,
        company_intro=user.company_intro or "",
        credit_code=credit_code,
        registered_address=registered_address,
        is_ready_for_agreement=bool(company_name and credit_code and registered_address),
        created_at=user.created_at,
    )


def _create_session(user: UserModel) -> str:
    token = generate_session_token()
    expires_at = datetime.now() + timedelta(hours=SESSION_TTL_HOURS)
    SessionModel.create(user=user, token=token, expires_at=expires_at)
    return token


def _resolve_current_user(request: Request) -> UserModel:
    current_user = getattr(request.state, "current_user", None)
    if current_user:
        return current_user

    auth_error = getattr(request.state, "auth_error", None)
    if auth_error == "Invalid authorization header":
        logger.warning("Authorization header format invalid")
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    logger.warning("Session invalid or expired")
    raise HTTPException(status_code=401, detail="Session expired or invalid")


def get_current_user(request: Request) -> UserModel:
    return _resolve_current_user(request)


def require_enterprise_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.role != "enterprise":
        logger.warning(
            "Access denied: enterprise role required user_id=%s actual_role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(status_code=403, detail="Enterprise role required")
    return current_user


def require_individual_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.role != "individual":
        logger.warning(
            "Access denied: individual role required user_id=%s actual_role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(status_code=403, detail="Individual role required")
    return current_user


def require_admin_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.role != "admin":
        logger.warning(
            "Access denied: admin role required user_id=%s actual_role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user


def _ensure_default_admin_user() -> UserModel:
    with database.allow_sync():
        admin_user = UserModel.get_or_none(UserModel.username == DEFAULT_ADMIN_USERNAME)
        if admin_user and admin_user.role != "admin":
            logger.error(
                "Default admin username occupied by non-admin account username=%s role=%s",
                DEFAULT_ADMIN_USERNAME,
                admin_user.role,
            )
            raise HTTPException(
                status_code=409,
                detail="Default admin username occupied by non-admin account",
            )

        if admin_user is None:
            admin_user = UserModel.create(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                role="admin",
                display_name=DEFAULT_ADMIN_DISPLAY_NAME,
                company_intro="",
            )
            logger.warning("Default admin user auto-created username=%s", DEFAULT_ADMIN_USERNAME)

    return admin_user


def _get_storage_client() -> StorageClient:
    return StorageClient(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY,
        settings.MINIO_BUCKET,
        secure=settings.MINIO_SECURE,
        public_base_url=settings.MINIO_PUBLIC_BASE_URL,
    )


def _to_guidance_sample_schema(
    sample: PortraitGuidanceSampleModel,
    storage_client: StorageClient,
) -> PortraitGuidanceSampleSchema:
    return PortraitGuidanceSampleSchema(
        view_angle=sample.view_angle,
        image_url=sample.image_url,
        preview_url=storage_client.get_url(sample.object_key, bucket=sample.bucket_name),
        bucket_name=sample.bucket_name,
        object_key=sample.object_key,
        source_filename=sample.source_filename,
        mime_type=sample.mime_type,
        file_size=sample.file_size,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )


def _load_guidance_sample_state() -> PortraitGuidanceSampleStateSchema:
    storage_client = _get_storage_client()
    with database.allow_sync():
        samples = list(PortraitGuidanceSampleModel.select())

    payload = {"left": None, "front": None, "right": None}
    for sample in samples:
        if sample.view_angle in payload:
            payload[sample.view_angle] = _to_guidance_sample_schema(sample, storage_client)

    return PortraitGuidanceSampleStateSchema(
        left=payload["left"],
        front=payload["front"],
        right=payload["right"],
        all_ready=all(payload.values()),
    )


def _guidance_extension(filename: str, content_type: str) -> str:
    extension = Path(filename or "").suffix.lower().lstrip(".")
    if extension in {"jpg", "jpeg", "png", "webp"}:
        return extension
    if content_type == "image/png":
        return "png"
    if content_type == "image/webp":
        return "webp"
    return "jpg"


@router.post("/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    phone = _validate_phone(req.phone)
    if req.password != req.confirm_password:
        raise HTTPException(status_code=422, detail="两次输入的密码不一致")

    with database.allow_sync():
        existing = UserModel.get_or_none(UserModel.username == phone)
        if existing:
            logger.warning("Register failed: phone already exists phone=%s", phone)
            raise HTTPException(status_code=409, detail="手机号已被注册")

        user = UserModel.create(
            username=phone,
            password_hash=hash_password(req.password),
            role="individual",
            display_name=phone,
            company_intro="",
        )
        token = _create_session(user)

    logger.info("User registered user_id=%s username=%s role=%s", user.id, user.username, user.role)
    return AuthResponse(token=token, user=_to_user_schema(user))


@router.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    username = req.username.strip()
    with database.allow_sync():
        user = UserModel.get_or_none(UserModel.username == username)
        if not user or not verify_password(req.password, user.password_hash):
            logger.warning("Login failed username=%s", username)
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        token = _create_session(user)
    logger.info("User login success user_id=%s username=%s role=%s", user.id, user.username, user.role)
    return AuthResponse(token=token, user=_to_user_schema(user))


@router.post("/admin/auth/login", response_model=AuthResponse)
async def admin_login(req: LoginRequest):
    _ensure_default_admin_user()
    with database.allow_sync():
        user = UserModel.get_or_none(UserModel.username == req.username)
        if not user or not verify_password(req.password, user.password_hash):
            logger.warning("Admin login failed username=%s", req.username)
            raise HTTPException(status_code=401, detail="Invalid username or password")
        if user.role != "admin":
            logger.warning("Admin login denied username=%s role=%s", req.username, user.role)
            raise HTTPException(status_code=403, detail="Admin role required")
        token = _create_session(user)
    logger.info("Admin login success user_id=%s username=%s", user.id, user.username)
    return AuthResponse(token=token, user=_to_user_schema(user))


@router.post("/auth/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: UserModel = Depends(get_current_user),
):
    token = getattr(request.state, "session_token", None)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    with database.allow_sync():
        SessionModel.delete().where(
            (SessionModel.token == token) & (SessionModel.user == current_user)
        ).execute()
    logger.info("User logged out user_id=%s username=%s", current_user.id, current_user.username)
    return MessageResponse(message="Logged out")


@router.get("/auth/me", response_model=UserSchema)
async def me(current_user: UserModel = Depends(get_current_user)):
    logger.debug("Session check for user_id=%s", current_user.id)
    return _to_user_schema(current_user)


@router.get("/enterprise/basic-info", response_model=EnterpriseBasicInfoSchema)
async def get_enterprise_basic_info(current_user: UserModel = Depends(require_enterprise_user)):
    with database.allow_sync():
        user = UserModel.get_by_id(current_user.id)
    return _to_enterprise_basic_info_schema(user)


@router.put("/enterprise/basic-info", response_model=EnterpriseBasicInfoSchema)
async def update_enterprise_basic_info(
    req: EnterpriseBasicInfoUpdateRequest,
    current_user: UserModel = Depends(require_enterprise_user),
):
    payload = req.model_dump()
    field_errors = _enterprise_basic_info_field_errors(payload)
    if field_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "请完善企业基本信息中的必填项后再保存。",
                "field_errors": field_errors,
            },
        )

    with database.allow_sync():
        user = UserModel.get_by_id(current_user.id)
        user.display_name = str(payload.get("company_name") or "").strip()
        user.company_intro = str(payload.get("company_intro") or "").strip()
        user.company_credit_code = str(payload.get("credit_code") or "").strip()
        user.company_registered_address = str(payload.get("registered_address") or "").strip()
        user.save()

    logger.info("Enterprise basic info updated user_id=%s", current_user.id)
    return _to_enterprise_basic_info_schema(user)


@router.get("/portrait-guidance/samples", response_model=PortraitGuidanceSampleStateSchema)
async def get_portrait_guidance_samples(_current_user: UserModel = Depends(get_current_user)):
    return _load_guidance_sample_state()


@router.get("/admin/enterprise-users", response_model=List[AdminEnterpriseUserSchema])
async def list_enterprise_users(_current_user: UserModel = Depends(require_admin_user)):
    with database.allow_sync():
        users = list(
            UserModel.select()
            .where(UserModel.role == "enterprise")
            .order_by(UserModel.created_at.desc())
        )
    return [_to_admin_enterprise_user_schema(user) for user in users]


@router.post("/admin/enterprise-users", response_model=AdminEnterpriseUserSchema)
async def create_enterprise_user(
    req: AdminCreateEnterpriseUserRequest,
    _current_user: UserModel = Depends(require_admin_user),
):
    with database.allow_sync():
        existing = UserModel.get_or_none(UserModel.username == req.username)
        if existing:
            logger.warning("Create enterprise user failed: username exists username=%s", req.username)
            raise HTTPException(status_code=409, detail="Username already exists")

        user = UserModel.create(
            username=req.username,
            password_hash=hash_password(req.password),
            role="enterprise",
            display_name=req.company_name.strip(),
            company_intro=req.company_intro.strip(),
        )

    logger.info("Enterprise user created user_id=%s username=%s", user.id, user.username)
    return _to_admin_enterprise_user_schema(user)


@router.put("/admin/enterprise-users/{enterprise_user_id}", response_model=AdminEnterpriseUserSchema)
async def update_enterprise_user(
    enterprise_user_id: int,
    req: AdminUpdateEnterpriseUserRequest,
    _current_user: UserModel = Depends(require_admin_user),
):
    with database.allow_sync():
        user = UserModel.get_or_none(
            (UserModel.id == enterprise_user_id) & (UserModel.role == "enterprise")
        )
        if not user:
            raise HTTPException(status_code=404, detail="Enterprise user not found")

        name_conflict = UserModel.get_or_none(
            (UserModel.username == req.username) & (UserModel.id != enterprise_user_id)
        )
        if name_conflict:
            logger.warning("Update enterprise user failed: username exists username=%s", req.username)
            raise HTTPException(status_code=409, detail="Username already exists")

        user.username = req.username
        user.display_name = req.company_name.strip()
        user.company_intro = req.company_intro.strip()
        if req.password:
            user.password_hash = hash_password(req.password)
        user.save()

    logger.info("Enterprise user updated user_id=%s username=%s", user.id, user.username)
    return _to_admin_enterprise_user_schema(user)


@router.post(
    "/admin/portrait-guidance/samples/{view_angle}",
    response_model=PortraitGuidanceSampleSchema,
)
async def upload_portrait_guidance_sample(
    view_angle: str,
    file: UploadFile = File(...),
    _current_user: UserModel = Depends(require_admin_user),
):
    normalized_angle = view_angle.strip().lower()
    if normalized_angle not in {"left", "front", "right"}:
        raise HTTPException(status_code=400, detail="Invalid guidance sample angle")

    content_type = file.content_type or "application/octet-stream"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Guidance sample must be an image")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Guidance sample image cannot be empty")

    storage_client = _get_storage_client()
    extension = _guidance_extension(file.filename or "", content_type)
    now = datetime.now()
    object_key = f"portrait-guidance/samples/{normalized_angle}/{uuid.uuid4().hex}.{extension}"
    image_url = await storage_client.upload_file(
        object_key,
        data,
        content_type,
        bucket=settings.MINIO_PORTRAIT_GUIDANCE_BUCKET,
    )

    with database.allow_sync():
        sample = PortraitGuidanceSampleModel.get_or_none(
            PortraitGuidanceSampleModel.view_angle == normalized_angle
        )
        if sample is None:
            sample = PortraitGuidanceSampleModel.create(
                view_angle=normalized_angle,
                bucket_name=settings.MINIO_PORTRAIT_GUIDANCE_BUCKET,
                object_key=object_key,
                image_url=image_url,
                source_filename=file.filename or f"{normalized_angle}.{extension}",
                mime_type=content_type,
                file_size=len(data),
                created_at=now,
                updated_at=now,
            )
        else:
            sample.bucket_name = settings.MINIO_PORTRAIT_GUIDANCE_BUCKET
            sample.object_key = object_key
            sample.image_url = image_url
            sample.source_filename = file.filename or f"{normalized_angle}.{extension}"
            sample.mime_type = content_type
            sample.file_size = len(data)
            sample.updated_at = now
            sample.save()

    logger.info(
        "Portrait guidance sample uploaded angle=%s bucket=%s object_key=%s bytes=%s",
        normalized_angle,
        settings.MINIO_PORTRAIT_GUIDANCE_BUCKET,
        object_key,
        len(data),
    )
    return _to_guidance_sample_schema(sample, storage_client)


@router.get("/enterprise/users", response_model=List[UserSchema])
async def list_individual_users(current_user: UserModel = Depends(require_enterprise_user)):
    with database.allow_sync():
        users = list(
            UserModel.select()
            .where(UserModel.role == "individual")
            .order_by(UserModel.created_at.desc())
        )
    _ = current_user
    logger.info("Enterprise listed individual users enterprise_user_id=%s count=%s", current_user.id, len(users))
    return [_to_user_schema(user) for user in users]


def get_agreement_service() -> AgreementService:
    return AgreementService()


@router.get("/admin/agreement/template", response_model=AgreementTemplateSchema)
async def get_admin_agreement_template(
    service: AgreementService = Depends(get_agreement_service),
    _current_user: UserModel = Depends(require_admin_user),
):
    return service.get_admin_template()


@router.put("/admin/agreement/template", response_model=AgreementTemplateSchema)
async def update_admin_agreement_template(
    req: AdminAgreementTemplateUpdateRequest,
    service: AgreementService = Depends(get_agreement_service),
    _current_user: UserModel = Depends(require_admin_user),
):
    try:
        return service.update_admin_template(req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/admin/enterprise-agreement/template", response_model=AgreementTemplateSchema)
async def get_admin_enterprise_agreement_template(
    service: AgreementService = Depends(get_agreement_service),
    _current_user: UserModel = Depends(require_admin_user),
):
    return service.get_admin_enterprise_template()


@router.put("/admin/enterprise-agreement/template", response_model=AgreementTemplateSchema)
async def update_admin_enterprise_agreement_template(
    req: AdminAgreementTemplateUpdateRequest,
    service: AgreementService = Depends(get_agreement_service),
    _current_user: UserModel = Depends(require_admin_user),
):
    try:
        return service.update_admin_enterprise_template(req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/actor/agreement", response_model=ActorAgreementViewSchema)
async def get_actor_agreement(
    service: AgreementService = Depends(get_agreement_service),
    current_user: UserModel = Depends(require_individual_user),
):
    return service.get_actor_agreement_view(current_user)


@router.get("/actor/agreement/status", response_model=AgreementStatusSchema)
async def get_actor_agreement_status(
    service: AgreementService = Depends(get_agreement_service),
    current_user: UserModel = Depends(require_individual_user),
):
    return service.get_actor_agreement_status(current_user)


@router.post("/actor/agreement/sign", response_model=ActorAgreementViewSchema)
async def sign_actor_agreement(
    req: ActorAgreementSignRequest,
    service: AgreementService = Depends(get_agreement_service),
    current_user: UserModel = Depends(require_individual_user),
):
    try:
        return service.sign_actor_agreement(current_user, req.model_dump())
    except AgreementFieldValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": exc.message,
                "field_errors": exc.field_errors,
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/enterprise/agreement", response_model=EnterpriseAgreementViewSchema)
async def get_enterprise_agreement(
    service: AgreementService = Depends(get_agreement_service),
    current_user: UserModel = Depends(require_enterprise_user),
):
    return service.get_enterprise_agreement_view(current_user)


@router.get("/enterprise/agreement/status", response_model=AgreementStatusSchema)
async def get_enterprise_agreement_status(
    service: AgreementService = Depends(get_agreement_service),
    current_user: UserModel = Depends(require_enterprise_user),
):
    return service.get_enterprise_agreement_status(current_user)


@router.post("/enterprise/agreement/sign", response_model=EnterpriseAgreementViewSchema)
async def sign_enterprise_agreement(
    req: EnterpriseAgreementSignRequest,
    service: AgreementService = Depends(get_agreement_service),
    current_user: UserModel = Depends(require_enterprise_user),
):
    try:
        return service.sign_enterprise_agreement(current_user, req.model_dump())
    except AgreementFieldValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": exc.message,
                "field_errors": exc.field_errors,
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
