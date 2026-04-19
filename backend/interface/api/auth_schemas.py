from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


UserRole = Literal["individual", "enterprise", "admin"]


class UserSchema(BaseModel):
    id: int
    username: str
    display_name: str
    company_intro: Optional[str] = None
    role: UserRole
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserSchema


class RegisterRequest(BaseModel):
    phone: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=6, max_length=128)
    confirm_password: str = Field(min_length=6, max_length=128)
    agreement_accepted: bool = False


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    agreement_accepted: bool = True


class AdminEnterpriseUserSchema(BaseModel):
    id: int
    username: str
    company_name: str
    company_intro: str
    created_at: datetime


class AdminCreateEnterpriseUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    company_name: str = Field(min_length=1, max_length=64)
    company_intro: str = Field(default="", max_length=4000)


class AdminUpdateEnterpriseUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    company_name: str = Field(min_length=1, max_length=64)
    company_intro: str = Field(default="", max_length=4000)


class EnterpriseBasicInfoSchema(BaseModel):
    user_id: int
    company_name: str
    company_intro: str
    credit_code: str
    registered_address: str
    is_ready_for_agreement: bool
    created_at: datetime


class EnterpriseBasicInfoUpdateRequest(BaseModel):
    company_name: str = Field(default="", max_length=64)
    company_intro: str = Field(default="", max_length=4000)
    credit_code: str = Field(default="", max_length=64)
    registered_address: str = Field(default="", max_length=512)


class PortraitGuidanceSampleSchema(BaseModel):
    view_angle: Literal["left", "front", "right"]
    image_url: str
    preview_url: str
    bucket_name: str
    object_key: str
    source_filename: str
    mime_type: str
    file_size: int
    created_at: datetime
    updated_at: datetime


class PortraitGuidanceSampleStateSchema(BaseModel):
    left: Optional[PortraitGuidanceSampleSchema] = None
    front: Optional[PortraitGuidanceSampleSchema] = None
    right: Optional[PortraitGuidanceSampleSchema] = None
    all_ready: bool = False


class AgreementTemplateSchema(BaseModel):
    version: int
    source_document_name: str
    party_a_company_name: str
    party_a_credit_code: str
    party_a_registered_address: str
    authorization_date_mode: Literal["fixed", "relative_months"] = "fixed"
    authorization_term_months: Optional[int] = None
    authorization_start_date: Optional[date] = None
    authorization_end_date: Optional[date] = None
    party_a_signature_label: str
    party_a_signed_date: Optional[date] = None
    is_ready: bool
    created_at: datetime
    updated_at: datetime


class AgreementStatusSchema(BaseModel):
    is_template_ready: bool
    is_signed: bool
    needs_resign: bool
    blocking_reason: Optional[str] = None
    message: str
    template_version: int
    signed_template_version: Optional[int] = None
    signed_at: Optional[datetime] = None


class EnterpriseAgreementRecordSchema(BaseModel):
    user_id: int
    template_version: int
    status: str
    party_b_company_name: str
    party_b_credit_code: str
    party_b_registered_address: str
    party_b_signature_data_url: str
    party_b_signed_date: Optional[date] = None
    signed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ActorAgreementRecordSchema(BaseModel):
    actor_id: int
    user_id: int
    template_version: int
    status: str
    party_b_name: str
    party_b_gender: str
    party_b_identity_number: str
    party_b_contact_address: str
    party_b_phone: str
    party_b_email: str
    party_b_signature_data_url: str
    party_b_signed_date: Optional[date] = None
    signed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ActorAgreementFormValuesSchema(BaseModel):
    party_b_name: str
    party_b_gender: str
    party_b_identity_number: str
    party_b_contact_address: str
    party_b_phone: str
    party_b_email: str
    party_b_signature_data_url: str
    party_b_signed_date: date


class EnterpriseAgreementFormValuesSchema(BaseModel):
    party_b_company_name: str
    party_b_credit_code: str
    party_b_registered_address: str
    party_b_signature_data_url: str
    party_b_signed_date: date


class ActorAgreementViewSchema(BaseModel):
    template: AgreementTemplateSchema
    status: AgreementStatusSchema
    agreement: Optional[ActorAgreementRecordSchema] = None
    form_values: ActorAgreementFormValuesSchema


class EnterpriseAgreementViewSchema(BaseModel):
    template: AgreementTemplateSchema
    status: AgreementStatusSchema
    agreement: Optional[EnterpriseAgreementRecordSchema] = None
    form_values: EnterpriseAgreementFormValuesSchema


class AdminAgreementTemplateUpdateRequest(BaseModel):
    party_a_company_name: str = Field(default="", max_length=128)
    party_a_credit_code: str = Field(default="", max_length=64)
    party_a_registered_address: str = Field(default="", max_length=512)
    authorization_date_mode: Literal["fixed", "relative_months"] = "fixed"
    authorization_term_months: Optional[int] = Field(default=None, ge=1, le=120)
    authorization_start_date: Optional[date] = None
    authorization_end_date: Optional[date] = None
    party_a_signature_label: str = Field(default="", max_length=128)
    party_a_signed_date: Optional[date] = None


class ActorAgreementSignRequest(BaseModel):
    party_b_name: str = Field(default="", max_length=64)
    party_b_gender: str = Field(default="", max_length=16)
    party_b_identity_number: str = Field(default="", max_length=32)
    party_b_contact_address: str = Field(default="", max_length=256)
    party_b_phone: str = Field(default="", max_length=32)
    party_b_email: str = Field(default="", max_length=128)
    party_b_signature_data_url: str = Field(default="", max_length=2_000_000)
    party_b_signed_date: Optional[date] = None


class EnterpriseAgreementSignRequest(BaseModel):
    party_b_company_name: str = Field(default="", max_length=128)
    party_b_credit_code: str = Field(default="", max_length=64)
    party_b_registered_address: str = Field(default="", max_length=512)
    party_b_signature_data_url: str = Field(default="", max_length=2_000_000)
    party_b_signed_date: Optional[date] = None


class MessageResponse(BaseModel):
    message: str
