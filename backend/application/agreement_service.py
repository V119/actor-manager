from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
import re
from typing import Any

from backend.infrastructure.orm_models import (
    ActorAgreementModel,
    ActorModel,
    AgreementTemplateConfigModel,
    EnterpriseAgreementModel,
    EnterpriseAgreementTemplateConfigModel,
    UserModel,
    database,
)


DEFAULT_ACTOR_AGREEMENT_SOURCE_DOCUMENT = "AI肖像权独家授权合作协议.docx"
DEFAULT_ENTERPRISE_AGREEMENT_SOURCE_DOCUMENT = "AI肖像权转授权与内容制作合作协议.docx"
AUTHORIZATION_DATE_MODES = {"fixed", "relative_months"}
PHONE_PATTERN = re.compile(r"^[0-9+\-\s]{6,32}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
IDENTITY_PATTERN = re.compile(r"^[0-9Xx]{15,18}$")


class AgreementFieldValidationError(ValueError):
    def __init__(self, field_errors: dict[str, str], message: str = "请完善协议中的必填信息后再提交。") -> None:
        super().__init__(message)
        self.field_errors = field_errors
        self.message = message


class AgreementService:
    def get_admin_template(self) -> dict[str, Any]:
        with database.allow_sync():
            config = _ensure_actor_template_config_sync()
            return _serialize_template_config(config, DEFAULT_ACTOR_AGREEMENT_SOURCE_DOCUMENT)

    def update_admin_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        with database.allow_sync():
            config = _ensure_actor_template_config_sync()
            _update_template_config(config, payload, DEFAULT_ACTOR_AGREEMENT_SOURCE_DOCUMENT)
            return _serialize_template_config(config, DEFAULT_ACTOR_AGREEMENT_SOURCE_DOCUMENT)

    def get_admin_enterprise_template(self) -> dict[str, Any]:
        with database.allow_sync():
            config = _ensure_enterprise_template_config_sync()
            return _serialize_template_config(config, DEFAULT_ENTERPRISE_AGREEMENT_SOURCE_DOCUMENT)

    def update_admin_enterprise_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        with database.allow_sync():
            config = _ensure_enterprise_template_config_sync()
            _update_template_config(config, payload, DEFAULT_ENTERPRISE_AGREEMENT_SOURCE_DOCUMENT)
            return _serialize_template_config(config, DEFAULT_ENTERPRISE_AGREEMENT_SOURCE_DOCUMENT)

    def get_actor_agreement_view(self, user: UserModel) -> dict[str, Any]:
        actor = resolve_actor_for_user(user_id=user.id, user_display_name=user.display_name)
        with database.allow_sync():
            config = _ensure_actor_template_config_sync()
            agreement = (
                ActorAgreementModel.select()
                .where(ActorAgreementModel.user_id == user.id)
                .first()
            )
            return {
                "template": _serialize_template_config(config, DEFAULT_ACTOR_AGREEMENT_SOURCE_DOCUMENT),
                "status": _serialize_status(
                    config,
                    agreement,
                    signed_message="协议已签署，可正常发布内容。",
                    unsigned_message="请先完成协议签署后再发布内容。",
                ),
                "agreement": _serialize_actor_agreement_record(agreement),
                "form_values": _serialize_actor_form_values(user=user, actor=actor, agreement=agreement),
            }

    def get_actor_agreement_status(self, user: UserModel) -> dict[str, Any]:
        actor = resolve_actor_for_user(user_id=user.id, user_display_name=user.display_name)
        _ = actor
        with database.allow_sync():
            config = _ensure_actor_template_config_sync()
            agreement = (
                ActorAgreementModel.select()
                .where(ActorAgreementModel.user_id == user.id)
                .first()
            )
            return _serialize_status(
                config,
                agreement,
                signed_message="协议已签署，可正常发布内容。",
                unsigned_message="请先完成协议签署后再发布内容。",
            )

    def sign_actor_agreement(self, user: UserModel, payload: dict[str, Any]) -> dict[str, Any]:
        actor = resolve_actor_for_user(user_id=user.id, user_display_name=user.display_name)
        validated = _validate_actor_sign_payload(payload)
        with database.allow_sync():
            config = _ensure_actor_template_config_sync()
            if not _is_template_ready(config):
                raise ValueError("协议模板尚未配置完成，请联系管理员后再签署。")

            agreement = (
                ActorAgreementModel.select()
                .where(ActorAgreementModel.user_id == user.id)
                .first()
            )
            now = datetime.now()
            if agreement is None:
                agreement = ActorAgreementModel.create(
                    user_id=user.id,
                    actor_id=actor.id,
                    template_version=config.version,
                    status="signed",
                    party_b_name=validated["party_b_name"],
                    party_b_gender=validated["party_b_gender"],
                    party_b_identity_number=validated["party_b_identity_number"],
                    party_b_contact_address=validated["party_b_contact_address"],
                    party_b_phone=validated["party_b_phone"],
                    party_b_email=validated["party_b_email"],
                    party_b_signature_data_url=validated["party_b_signature_data_url"],
                    party_b_signed_date=validated["party_b_signed_date"],
                    signed_at=now,
                    created_at=now,
                    updated_at=now,
                )
            else:
                agreement.actor_id = actor.id
                agreement.template_version = config.version
                agreement.status = "signed"
                agreement.party_b_name = validated["party_b_name"]
                agreement.party_b_gender = validated["party_b_gender"]
                agreement.party_b_identity_number = validated["party_b_identity_number"]
                agreement.party_b_contact_address = validated["party_b_contact_address"]
                agreement.party_b_phone = validated["party_b_phone"]
                agreement.party_b_email = validated["party_b_email"]
                agreement.party_b_signature_data_url = validated["party_b_signature_data_url"]
                agreement.party_b_signed_date = validated["party_b_signed_date"]
                agreement.signed_at = now
                agreement.updated_at = now
                agreement.save()

            return {
                "template": _serialize_template_config(config, DEFAULT_ACTOR_AGREEMENT_SOURCE_DOCUMENT),
                "status": _serialize_status(
                    config,
                    agreement,
                    signed_message="协议已签署，可正常发布内容。",
                    unsigned_message="请先完成协议签署后再发布内容。",
                ),
                "agreement": _serialize_actor_agreement_record(agreement),
                "form_values": _serialize_actor_form_values(user=user, actor=actor, agreement=agreement),
            }

    def get_enterprise_agreement_view(self, user: UserModel) -> dict[str, Any]:
        with database.allow_sync():
            config = _ensure_enterprise_template_config_sync()
            agreement = (
                EnterpriseAgreementModel.select()
                .where(EnterpriseAgreementModel.user_id == user.id)
                .first()
            )
            return {
                "template": _serialize_template_config(config, DEFAULT_ENTERPRISE_AGREEMENT_SOURCE_DOCUMENT),
                "status": _serialize_status(
                    config,
                    agreement,
                    signed_message="企业协议已签署，可正常访问演员广场。",
                    unsigned_message="请先完成企业协议签署后再访问演员广场。",
                ),
                "agreement": _serialize_enterprise_agreement_record(agreement),
                "form_values": _serialize_enterprise_form_values(
                    user=user,
                    agreement=agreement,
                    current_template_version=config.version,
                ),
            }

    def get_enterprise_agreement_status(self, user: UserModel) -> dict[str, Any]:
        with database.allow_sync():
            config = _ensure_enterprise_template_config_sync()
            agreement = (
                EnterpriseAgreementModel.select()
                .where(EnterpriseAgreementModel.user_id == user.id)
                .first()
            )
            return _serialize_status(
                config,
                agreement,
                signed_message="企业协议已签署，可正常访问演员广场。",
                unsigned_message="请先完成企业协议签署后再访问演员广场。",
            )

    def sign_enterprise_agreement(self, user: UserModel, payload: dict[str, Any]) -> dict[str, Any]:
        validated = _validate_enterprise_sign_payload(payload)
        with database.allow_sync():
            config = _ensure_enterprise_template_config_sync()
            if not _is_template_ready(config):
                raise ValueError("企业协议模板尚未配置完成，请联系管理员后再签署。")

            agreement = (
                EnterpriseAgreementModel.select()
                .where(EnterpriseAgreementModel.user_id == user.id)
                .first()
            )
            now = datetime.now()
            if agreement is None:
                agreement = EnterpriseAgreementModel.create(
                    user_id=user.id,
                    template_version=config.version,
                    status="signed",
                    party_b_company_name=validated["party_b_company_name"],
                    party_b_credit_code=validated["party_b_credit_code"],
                    party_b_registered_address=validated["party_b_registered_address"],
                    party_b_signature_data_url=validated["party_b_signature_data_url"],
                    party_b_signed_date=validated["party_b_signed_date"],
                    signed_at=now,
                    created_at=now,
                    updated_at=now,
                )
            else:
                agreement.template_version = config.version
                agreement.status = "signed"
                agreement.party_b_company_name = validated["party_b_company_name"]
                agreement.party_b_credit_code = validated["party_b_credit_code"]
                agreement.party_b_registered_address = validated["party_b_registered_address"]
                agreement.party_b_signature_data_url = validated["party_b_signature_data_url"]
                agreement.party_b_signed_date = validated["party_b_signed_date"]
                agreement.signed_at = now
                agreement.updated_at = now
                agreement.save()

            return {
                "template": _serialize_template_config(config, DEFAULT_ENTERPRISE_AGREEMENT_SOURCE_DOCUMENT),
                "status": _serialize_status(
                    config,
                    agreement,
                    signed_message="企业协议已签署，可正常访问演员广场。",
                    unsigned_message="请先完成企业协议签署后再访问演员广场。",
                ),
                "agreement": _serialize_enterprise_agreement_record(agreement),
                "form_values": _serialize_enterprise_form_values(
                    user=user,
                    agreement=agreement,
                    current_template_version=config.version,
                ),
            }


def resolve_actor_for_user(user_id: int, user_display_name: str) -> ActorModel:
    actor_external_id = f"USER-{user_id}"
    with database.allow_sync():
        actor, _created = ActorModel.get_or_create(
            external_id=actor_external_id,
            defaults={
                "name": user_display_name or f"user_{user_id}",
                "age": 0,
                "location": "",
                "hometown": "",
                "height": 0,
                "weight_kg": 0,
                "bust_cm": 0,
                "waist_cm": 0,
                "hip_cm": 0,
                "shoe_size": "",
                "bio": "",
                "acting_requirements": "",
                "rejected_requirements": "",
                "availability_note": "",
                "pricing_unit": "project",
                "pricing_amount": 0,
                "tags": ["self-upload"],
                "is_published": False,
            },
        )
        return actor


def get_actor_agreement_status_by_actor(actor_id: int) -> dict[str, Any]:
    with database.allow_sync():
        config = _ensure_actor_template_config_sync()
        agreement = (
            ActorAgreementModel.select()
            .where(ActorAgreementModel.actor_id == actor_id)
            .first()
        )
        return _serialize_status(
            config,
            agreement,
            signed_message="协议已签署，可正常发布内容。",
            unsigned_message="请先完成协议签署后再发布内容。",
        )


def is_actor_agreement_currently_signed(actor_id: int) -> bool:
    status = get_actor_agreement_status_by_actor(actor_id)
    return bool(status.get("is_signed"))


def ensure_actor_agreement_signed(actor_id: int) -> None:
    status = get_actor_agreement_status_by_actor(actor_id)
    if not status.get("is_signed"):
        raise ValueError(str(status.get("message") or "请先完成协议签署后再发布内容。"))


def get_enterprise_agreement_status_by_user(user_id: int) -> dict[str, Any]:
    with database.allow_sync():
        config = _ensure_enterprise_template_config_sync()
        agreement = (
            EnterpriseAgreementModel.select()
            .where(EnterpriseAgreementModel.user_id == user_id)
            .first()
        )
        return _serialize_status(
            config,
            agreement,
            signed_message="企业协议已签署，可正常访问演员广场。",
            unsigned_message="请先完成企业协议签署后再访问演员广场。",
        )


def is_enterprise_agreement_currently_signed(user_id: int) -> bool:
    status = get_enterprise_agreement_status_by_user(user_id)
    return bool(status.get("is_signed"))


def ensure_enterprise_agreement_signed(user_id: int) -> None:
    status = get_enterprise_agreement_status_by_user(user_id)
    if not status.get("is_signed"):
        raise ValueError(str(status.get("message") or "请先完成企业协议签署后再访问演员广场。"))


def _ensure_actor_template_config_sync() -> AgreementTemplateConfigModel:
    now = datetime.now()
    config, _created = AgreementTemplateConfigModel.get_or_create(
        id=1,
        defaults={
            "version": 1,
            "source_document_name": DEFAULT_ACTOR_AGREEMENT_SOURCE_DOCUMENT,
            "party_a_company_name": "",
            "party_a_credit_code": "",
            "party_a_registered_address": "",
            "authorization_date_mode": "fixed",
            "authorization_term_months": None,
            "authorization_start_date": None,
            "authorization_end_date": None,
            "party_a_signature_label": "",
            "party_a_signed_date": None,
            "created_at": now,
            "updated_at": now,
        },
    )
    return config


def _ensure_enterprise_template_config_sync() -> EnterpriseAgreementTemplateConfigModel:
    now = datetime.now()
    config, _created = EnterpriseAgreementTemplateConfigModel.get_or_create(
        id=1,
        defaults={
            "version": 1,
            "source_document_name": DEFAULT_ENTERPRISE_AGREEMENT_SOURCE_DOCUMENT,
            "party_a_company_name": "",
            "party_a_credit_code": "",
            "party_a_registered_address": "",
            "authorization_date_mode": "fixed",
            "authorization_term_months": None,
            "authorization_start_date": None,
            "authorization_end_date": None,
            "party_a_signature_label": "",
            "party_a_signed_date": None,
            "created_at": now,
            "updated_at": now,
        },
    )
    return config


def _update_template_config(config: Any, payload: dict[str, Any], source_document_name: str) -> None:
    next_company_name = _clean_text(payload.get("party_a_company_name"), 128)
    next_credit_code = _clean_text(payload.get("party_a_credit_code"), 64)
    next_registered_address = _clean_text(payload.get("party_a_registered_address"), 512)
    next_signature_label = _clean_text(payload.get("party_a_signature_label"), 128) or next_company_name
    next_date_mode = _normalize_authorization_date_mode(payload.get("authorization_date_mode"))
    next_term_months = _normalize_authorization_term_months(payload.get("authorization_term_months"), next_date_mode)
    next_start_date, next_end_date = _resolve_authorization_dates(
        next_date_mode,
        payload.get("authorization_start_date"),
        payload.get("authorization_end_date"),
        next_term_months,
    )
    next_signed_date = payload.get("party_a_signed_date")

    current_fingerprint = _template_fingerprint(config)
    next_fingerprint = (
        next_company_name,
        next_credit_code,
        next_registered_address,
        next_signature_label,
        next_date_mode,
        next_term_months,
        next_start_date,
        next_end_date,
        next_signed_date,
    )

    config.party_a_company_name = next_company_name
    config.party_a_credit_code = next_credit_code
    config.party_a_registered_address = next_registered_address
    config.party_a_signature_label = next_signature_label
    config.authorization_date_mode = next_date_mode
    config.authorization_term_months = next_term_months
    config.authorization_start_date = next_start_date
    config.authorization_end_date = next_end_date
    config.party_a_signed_date = next_signed_date
    config.source_document_name = source_document_name
    config.updated_at = datetime.now()
    if current_fingerprint != next_fingerprint:
        config.version = int(config.version or 1) + 1
    config.save()


def _template_fingerprint(config: Any) -> tuple[Any, ...]:
    authorization_date_mode = getattr(config, "authorization_date_mode", "fixed") or "fixed"
    authorization_start_date, authorization_end_date = _fingerprint_authorization_dates(
        authorization_date_mode,
        getattr(config, "authorization_start_date", None),
        getattr(config, "authorization_end_date", None),
    )
    return (
        config.party_a_company_name,
        config.party_a_credit_code,
        config.party_a_registered_address,
        config.party_a_signature_label,
        authorization_date_mode,
        getattr(config, "authorization_term_months", None),
        authorization_start_date,
        authorization_end_date,
        config.party_a_signed_date,
    )


def _is_template_ready(config: Any) -> bool:
    authorization_date_mode = getattr(config, "authorization_date_mode", "fixed") or "fixed"
    has_authorization_window = False
    if authorization_date_mode == "relative_months":
        has_authorization_window = getattr(config, "authorization_term_months", None) is not None
    else:
        has_authorization_window = (
            getattr(config, "authorization_start_date", None) is not None
            and getattr(config, "authorization_end_date", None) is not None
        )

    return all(
        [
            _has_text(config.party_a_company_name),
            _has_text(config.party_a_credit_code),
            _has_text(config.party_a_registered_address),
            has_authorization_window,
            config.party_a_signed_date is not None,
        ]
    )


def _serialize_template_config(config: Any, source_document_name: str) -> dict[str, Any]:
    authorization_date_mode = getattr(config, "authorization_date_mode", "fixed") or "fixed"
    authorization_start_date, authorization_end_date = _display_authorization_dates(
        authorization_date_mode,
        config.authorization_start_date,
        config.authorization_end_date,
    )
    return {
        "version": int(config.version or 1),
        "source_document_name": config.source_document_name or source_document_name,
        "party_a_company_name": config.party_a_company_name or "",
        "party_a_credit_code": config.party_a_credit_code or "",
        "party_a_registered_address": config.party_a_registered_address or "",
        "authorization_date_mode": authorization_date_mode,
        "authorization_term_months": getattr(config, "authorization_term_months", None),
        "authorization_start_date": authorization_start_date,
        "authorization_end_date": authorization_end_date,
        "party_a_signature_label": config.party_a_signature_label or config.party_a_company_name or "",
        "party_a_signed_date": config.party_a_signed_date,
        "is_ready": _is_template_ready(config),
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


def _serialize_status(
    config: Any,
    agreement: Any | None,
    *,
    signed_message: str,
    unsigned_message: str,
) -> dict[str, Any]:
    is_template_ready = _is_template_ready(config)
    signed_version = int(agreement.template_version) if agreement and agreement.template_version is not None else None
    is_signed = bool(
        is_template_ready
        and agreement is not None
        and agreement.status == "signed"
        and signed_version == int(config.version or 1)
    )
    needs_resign = bool(
        agreement is not None
        and agreement.status == "signed"
        and signed_version is not None
        and signed_version != int(config.version or 1)
    )

    blocking_reason = None
    if not is_template_ready:
        blocking_reason = "template_not_ready"
    elif needs_resign:
        blocking_reason = "outdated"
    elif not is_signed:
        blocking_reason = "unsigned"

    if is_signed:
        message = signed_message
    elif blocking_reason == "template_not_ready":
        message = "协议模板尚未配置完成，请联系管理员后再签署。"
    elif blocking_reason == "outdated":
        message = "协议内容已更新，请重新签署后再继续使用。"
    else:
        message = unsigned_message

    return {
        "is_template_ready": is_template_ready,
        "is_signed": is_signed,
        "needs_resign": needs_resign,
        "blocking_reason": blocking_reason,
        "message": message,
        "template_version": int(config.version or 1),
        "signed_template_version": signed_version,
        "signed_at": agreement.signed_at if agreement else None,
    }


def _serialize_actor_agreement_record(agreement: ActorAgreementModel | None) -> dict[str, Any] | None:
    if agreement is None:
        return None
    return {
        "actor_id": int(agreement.actor_id),
        "user_id": int(agreement.user_id),
        "template_version": int(agreement.template_version or 1),
        "status": agreement.status,
        "party_b_name": agreement.party_b_name or "",
        "party_b_gender": agreement.party_b_gender or "",
        "party_b_identity_number": agreement.party_b_identity_number or "",
        "party_b_contact_address": agreement.party_b_contact_address or "",
        "party_b_phone": agreement.party_b_phone or "",
        "party_b_email": agreement.party_b_email or "",
        "party_b_signature_data_url": agreement.party_b_signature_data_url or "",
        "party_b_signed_date": agreement.party_b_signed_date,
        "signed_at": agreement.signed_at,
        "created_at": agreement.created_at,
        "updated_at": agreement.updated_at,
    }


def _serialize_enterprise_agreement_record(agreement: EnterpriseAgreementModel | None) -> dict[str, Any] | None:
    if agreement is None:
        return None
    return {
        "user_id": int(agreement.user_id),
        "template_version": int(agreement.template_version or 1),
        "status": agreement.status,
        "party_b_company_name": agreement.party_b_company_name or "",
        "party_b_credit_code": agreement.party_b_credit_code or "",
        "party_b_registered_address": agreement.party_b_registered_address or "",
        "party_b_signature_data_url": agreement.party_b_signature_data_url or "",
        "party_b_signed_date": agreement.party_b_signed_date,
        "signed_at": agreement.signed_at,
        "created_at": agreement.created_at,
        "updated_at": agreement.updated_at,
    }


def _serialize_actor_form_values(
    user: UserModel,
    actor: ActorModel,
    agreement: ActorAgreementModel | None,
) -> dict[str, Any]:
    default_name = agreement.party_b_name if agreement else ""
    if not default_name:
        actor_name = (actor.name or "").strip()
        default_name = actor_name if actor_name and not actor_name.startswith("user_") else ""

    default_phone = agreement.party_b_phone if agreement else ""
    if not default_phone and PHONE_PATTERN.fullmatch(str(user.username or "")):
        default_phone = str(user.username)

    default_address = agreement.party_b_contact_address if agreement else ""
    if not default_address:
        default_address = (actor.location or "").strip()

    return {
        "party_b_name": default_name,
        "party_b_gender": agreement.party_b_gender if agreement else "",
        "party_b_identity_number": agreement.party_b_identity_number if agreement else "",
        "party_b_contact_address": default_address,
        "party_b_phone": default_phone,
        "party_b_email": agreement.party_b_email if agreement else "",
        "party_b_signature_data_url": agreement.party_b_signature_data_url if agreement else "",
        "party_b_signed_date": agreement.party_b_signed_date if agreement and agreement.party_b_signed_date else date.today(),
    }


def _serialize_enterprise_form_values(
    user: UserModel,
    agreement: EnterpriseAgreementModel | None,
    current_template_version: int,
) -> dict[str, Any]:
    is_current_signed_agreement = bool(
        agreement
        and agreement.status == "signed"
        and int(agreement.template_version or 0) == int(current_template_version or 0)
    )

    default_company_name = (user.display_name or user.username or "").strip()
    default_credit_code = (getattr(user, "company_credit_code", "") or "").strip()
    default_registered_address = (getattr(user, "company_registered_address", "") or "").strip()

    if is_current_signed_agreement:
        default_company_name = agreement.party_b_company_name or default_company_name
        default_credit_code = agreement.party_b_credit_code or default_credit_code
        default_registered_address = agreement.party_b_registered_address or default_registered_address

    return {
        "party_b_company_name": default_company_name,
        "party_b_credit_code": default_credit_code,
        "party_b_registered_address": default_registered_address,
        "party_b_signature_data_url": agreement.party_b_signature_data_url if is_current_signed_agreement and agreement else "",
        "party_b_signed_date": agreement.party_b_signed_date if is_current_signed_agreement and agreement and agreement.party_b_signed_date else date.today(),
    }


def _validate_actor_sign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    field_errors: dict[str, str] = {}

    party_b_name = _clean_text(payload.get("party_b_name"), 64)
    if not party_b_name:
        field_errors["party_b_name"] = "请填写乙方姓名。"

    party_b_gender = _clean_text(payload.get("party_b_gender"), 16)
    if not party_b_gender:
        field_errors["party_b_gender"] = "请填写乙方性别。"

    party_b_identity_number = _clean_text(payload.get("party_b_identity_number"), 32)
    if not party_b_identity_number:
        field_errors["party_b_identity_number"] = "请填写乙方公民身份号码。"
    elif not IDENTITY_PATTERN.fullmatch(party_b_identity_number):
        field_errors["party_b_identity_number"] = "请输入合法的公民身份号码。"

    party_b_contact_address = _clean_text(payload.get("party_b_contact_address"), 256)
    if not party_b_contact_address:
        field_errors["party_b_contact_address"] = "请填写乙方联系地址。"

    party_b_phone = _clean_text(payload.get("party_b_phone"), 32)
    if not party_b_phone:
        field_errors["party_b_phone"] = "请填写乙方联系电话。"
    elif not PHONE_PATTERN.fullmatch(party_b_phone):
        field_errors["party_b_phone"] = "请输入合法的联系电话。"

    party_b_email = _clean_text(payload.get("party_b_email"), 128)
    if not party_b_email:
        field_errors["party_b_email"] = "请填写乙方电子邮箱。"
    elif not EMAIL_PATTERN.fullmatch(party_b_email):
        field_errors["party_b_email"] = "请输入合法的电子邮箱地址。"

    signature_data_url = _clean_text(payload.get("party_b_signature_data_url"), 2_000_000)
    if not signature_data_url:
        field_errors["party_b_signature_data_url"] = "请完成乙方签字。"
    elif not signature_data_url.startswith("data:image/"):
        field_errors["party_b_signature_data_url"] = "签字图片格式不正确，请重新签署。"

    signed_date = payload.get("party_b_signed_date")
    if not isinstance(signed_date, date):
        field_errors["party_b_signed_date"] = "请选择乙方签署日期。"

    if field_errors:
        raise AgreementFieldValidationError(field_errors)

    return {
        "party_b_name": party_b_name,
        "party_b_gender": party_b_gender,
        "party_b_identity_number": party_b_identity_number.upper(),
        "party_b_contact_address": party_b_contact_address,
        "party_b_phone": party_b_phone,
        "party_b_email": party_b_email,
        "party_b_signature_data_url": signature_data_url,
        "party_b_signed_date": signed_date,
    }


def _validate_enterprise_sign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    field_errors: dict[str, str] = {}

    party_b_company_name = _clean_text(payload.get("party_b_company_name"), 128)
    if not party_b_company_name:
        field_errors["party_b_company_name"] = "请填写乙方公司名称。"

    party_b_credit_code = _clean_text(payload.get("party_b_credit_code"), 64)
    if not party_b_credit_code:
        field_errors["party_b_credit_code"] = "请填写乙方统一社会信用代码。"

    party_b_registered_address = _clean_text(payload.get("party_b_registered_address"), 512)
    if not party_b_registered_address:
        field_errors["party_b_registered_address"] = "请填写乙方住所地。"

    signature_data_url = _clean_text(payload.get("party_b_signature_data_url"), 2_000_000)
    if not signature_data_url:
        field_errors["party_b_signature_data_url"] = "请完成乙方盖章/签字。"
    elif not signature_data_url.startswith("data:image/"):
        field_errors["party_b_signature_data_url"] = "签字图片格式不正确，请重新签署。"

    signed_date = payload.get("party_b_signed_date")
    if not isinstance(signed_date, date):
        field_errors["party_b_signed_date"] = "请选择乙方签署日期。"

    if field_errors:
        raise AgreementFieldValidationError(field_errors)

    return {
        "party_b_company_name": party_b_company_name,
        "party_b_credit_code": party_b_credit_code.upper(),
        "party_b_registered_address": party_b_registered_address,
        "party_b_signature_data_url": signature_data_url,
        "party_b_signed_date": signed_date,
    }


def _clean_text(value: Any, max_len: int) -> str:
    return str(value or "").strip()[:max_len]


def _has_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def _normalize_authorization_date_mode(value: Any) -> str:
    mode = str(value or "fixed").strip() or "fixed"
    if mode not in AUTHORIZATION_DATE_MODES:
        raise ValueError("授权期限模式不正确。")
    return mode


def _normalize_authorization_term_months(value: Any, date_mode: str) -> int | None:
    if date_mode != "relative_months":
        return None
    if value in (None, ""):
        raise ValueError("请选择授权期限月数。")
    try:
        months = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("授权期限月数必须是整数。") from exc
    if months < 1 or months > 120:
        raise ValueError("授权期限月数需在1到120个月之间。")
    return months


def _resolve_authorization_dates(
    date_mode: str,
    start_date: date | None,
    end_date: date | None,
    term_months: int | None,
) -> tuple[date | None, date | None]:
    if date_mode == "fixed":
        if start_date and end_date and start_date > end_date:
            raise ValueError("授权截止日期不能早于开始日期。")
        return start_date, end_date

    if term_months is None:
        raise ValueError("请选择授权期限月数。")
    return None, None


def _add_months(base_date: date, months: int) -> date:
    total_month = (base_date.month - 1) + months
    year = base_date.year + total_month // 12
    month = total_month % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _fingerprint_authorization_dates(
    authorization_date_mode: str,
    authorization_start_date: date | None,
    authorization_end_date: date | None,
) -> tuple[date | None, date | None]:
    if authorization_date_mode == "relative_months":
        return None, None
    return authorization_start_date, authorization_end_date


def _display_authorization_dates(
    authorization_date_mode: str,
    authorization_start_date: date | None,
    authorization_end_date: date | None,
) -> tuple[date | None, date | None]:
    if authorization_date_mode == "relative_months":
        return None, None
    return authorization_start_date, authorization_end_date
