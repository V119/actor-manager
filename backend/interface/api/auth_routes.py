from datetime import datetime, timedelta
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.config import get_config
from backend.infrastructure.orm_models import ProtocolModel, SessionModel, UserModel, database
from backend.infrastructure.security import generate_session_token, hash_password, verify_password
from backend.interface.api.auth_schemas import (
    AuthResponse,
    CreateProtocolRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    RoleProtocolSchema,
    UserSchema,
)


router = APIRouter()
SESSION_TTL_DAYS = int(get_config("auth.session_ttl_days", 7))
logger = logging.getLogger(__name__)


def _to_user_schema(user: UserModel) -> UserSchema:
    return UserSchema(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        created_at=user.created_at,
    )


def _create_session(user: UserModel) -> str:
    token = generate_session_token()
    expires_at = datetime.now() + timedelta(days=SESSION_TTL_DAYS)
    SessionModel.create(user=user, token=token, expires_at=expires_at)
    return token


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        logger.warning("Authorization header missing")
        raise HTTPException(status_code=401, detail="Missing authorization header")
    if not authorization.startswith("Bearer "):
        logger.warning("Authorization header format invalid")
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        logger.warning("Bearer token missing")
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return token


def get_current_user(authorization: Optional[str] = Header(default=None)) -> UserModel:
    token = _extract_bearer_token(authorization)
    with database.allow_sync():
        session = (
            SessionModel.select(SessionModel, UserModel)
            .join(UserModel)
            .where((SessionModel.token == token) & (SessionModel.expires_at > datetime.now()))
            .first()
        )
    if not session:
        logger.warning("Session invalid or expired")
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return session.user


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


def _to_protocol_schema(protocol: ProtocolModel, target_user: Optional[UserModel] = None) -> RoleProtocolSchema:
    return RoleProtocolSchema(
        id=protocol.id,
        company_name=protocol.company_name,
        title=protocol.title,
        content=protocol.content,
        status=protocol.status,
        created_at=protocol.created_at,
        signed_at=protocol.signed_at,
        enterprise_user_id=protocol.enterprise_user_id,
        target_user_id=protocol.target_user_id,
        target_user_display_name=target_user.display_name if target_user else None,
        target_username=target_user.username if target_user else None,
    )


@router.post("/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    with database.allow_sync():
        existing = UserModel.get_or_none(UserModel.username == req.username)
        if existing:
            logger.warning("Register failed: username already exists username=%s", req.username)
            raise HTTPException(status_code=409, detail="Username already exists")

        user = UserModel.create(
            username=req.username,
            password_hash=hash_password(req.password),
            role=req.role,
            display_name=req.display_name or req.username,
        )
        token = _create_session(user)

    logger.info("User registered user_id=%s username=%s role=%s", user.id, user.username, user.role)
    return AuthResponse(token=token, user=_to_user_schema(user))


@router.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    with database.allow_sync():
        user = UserModel.get_or_none(UserModel.username == req.username)
        if not user or not verify_password(req.password, user.password_hash):
            logger.warning("Login failed username=%s", req.username)
            raise HTTPException(status_code=401, detail="Invalid username or password")
        token = _create_session(user)
    logger.info("User login success user_id=%s username=%s role=%s", user.id, user.username, user.role)
    return AuthResponse(token=token, user=_to_user_schema(user))


@router.post("/auth/logout", response_model=MessageResponse)
async def logout(
    authorization: Optional[str] = Header(default=None),
    current_user: UserModel = Depends(get_current_user),
):
    token = _extract_bearer_token(authorization)
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


@router.get("/enterprise/users", response_model=List[UserSchema])
async def list_individual_users(current_user: UserModel = Depends(require_enterprise_user)):
    with database.allow_sync():
        users = list(
            UserModel.select()
            .where(UserModel.role == "individual")
            .order_by(UserModel.created_at.desc())
        )
    # current_user only for permission check, intentionally unused in response mapping.
    _ = current_user
    logger.info("Enterprise listed individual users enterprise_user_id=%s count=%s", current_user.id, len(users))
    return [_to_user_schema(user) for user in users]


@router.post("/enterprise/protocols", response_model=RoleProtocolSchema)
async def create_enterprise_protocol(
    req: CreateProtocolRequest,
    current_user: UserModel = Depends(require_enterprise_user),
):
    with database.allow_sync():
        target_user = UserModel.get_or_none(
            (UserModel.id == req.target_user_id) & (UserModel.role == "individual")
        )
        if not target_user:
            logger.warning(
                "Create protocol failed: target user not found enterprise_user_id=%s target_user_id=%s",
                current_user.id,
                req.target_user_id,
            )
            raise HTTPException(status_code=404, detail="Target individual user not found")

        protocol = ProtocolModel.create(
            actor=None,
            enterprise_user=current_user,
            target_user=target_user,
            company_name=current_user.display_name,
            title=req.title,
            content=req.content,
            status="pending",
        )
    logger.info(
        "Protocol created protocol_id=%s enterprise_user_id=%s target_user_id=%s",
        protocol.id,
        current_user.id,
        target_user.id,
    )
    return _to_protocol_schema(protocol, target_user=target_user)


@router.get("/enterprise/protocols", response_model=List[RoleProtocolSchema])
async def list_enterprise_protocols(current_user: UserModel = Depends(require_enterprise_user)):
    with database.allow_sync():
        protocols = list(
            ProtocolModel.select()
            .where(ProtocolModel.enterprise_user == current_user)
            .order_by(ProtocolModel.created_at.desc())
        )
        target_ids = [p.target_user_id for p in protocols if p.target_user_id]
        target_map = {}
        if target_ids:
            target_map = {
                user.id: user
                for user in UserModel.select().where(UserModel.id.in_(target_ids))
            }
    logger.info(
        "Enterprise listed protocols enterprise_user_id=%s count=%s",
        current_user.id,
        len(protocols),
    )
    return [_to_protocol_schema(p, target_map.get(p.target_user_id)) for p in protocols]


@router.get("/user/protocols", response_model=List[RoleProtocolSchema])
async def list_user_protocols(current_user: UserModel = Depends(require_individual_user)):
    with database.allow_sync():
        protocols = list(
            ProtocolModel.select()
            .where(ProtocolModel.target_user == current_user)
            .order_by(ProtocolModel.created_at.desc())
        )
    logger.info("Individual listed protocols user_id=%s count=%s", current_user.id, len(protocols))
    return [_to_protocol_schema(p, current_user) for p in protocols]


@router.post("/user/protocols/{protocol_id}/sign", response_model=RoleProtocolSchema)
async def sign_user_protocol(
    protocol_id: int,
    current_user: UserModel = Depends(require_individual_user),
):
    with database.allow_sync():
        protocol = ProtocolModel.get_or_none(
            (ProtocolModel.id == protocol_id) & (ProtocolModel.target_user == current_user)
        )
        if not protocol:
            logger.warning(
                "Sign protocol failed: protocol not found protocol_id=%s user_id=%s",
                protocol_id,
                current_user.id,
            )
            raise HTTPException(status_code=404, detail="Protocol not found")

        if protocol.status != "signed":
            protocol.status = "signed"
            protocol.signed_at = datetime.now()
            protocol.save()

    logger.info("Protocol signed protocol_id=%s user_id=%s", protocol.id, current_user.id)
    return _to_protocol_schema(protocol, current_user)
