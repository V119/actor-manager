from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

VideoTypeLiteral = Literal["intro", "showreel"]


class PortraitSchema(BaseModel):
    id: Optional[int]
    actor_id: int
    image_url: str
    portrait_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ActorSchema(BaseModel):
    id: Optional[int]
    name: str
    external_id: str
    age: int
    location: str
    height: int
    bio: str
    tags: List[str]
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ActorBasicInfoSchema(BaseModel):
    actor_id: int
    external_id: str
    name: str
    age: int
    height: int
    weight_kg: int
    location: str
    hometown: str
    bust_cm: int
    waist_cm: int
    hip_cm: int
    shoe_size: str
    bio: str
    tags: List[str]
    acting_requirements: str
    rejected_requirements: str
    availability_note: str
    pricing_unit: Literal["day", "project"]
    pricing_amount: int
    avatar_url: Optional[str]
    avatar_original_url: Optional[str] = None
    avatar_variant_urls: dict[str, str] = Field(default_factory=dict)
    avatar_source: Literal["three_view", "none"]
    created_at: datetime


class ActorBasicInfoUpdateRequest(BaseModel):
    name: str
    age: int = 0
    height: int = 0
    weight_kg: int = 0
    location: str = ""
    hometown: str = ""
    bust_cm: int = 0
    waist_cm: int = 0
    hip_cm: int = 0
    shoe_size: str = ""
    bio: str = ""
    tags: List[str] = Field(default_factory=list)
    acting_requirements: str = ""
    rejected_requirements: str = ""
    availability_note: str = ""
    pricing_unit: Literal["day", "project"] = "project"
    pricing_amount: int = 0

class StyleSchema(BaseModel):
    id: int
    name: str
    description: str
    preview_url: str
    category: str

    class Config:
        from_attributes = True

class GeneratedResultSchema(BaseModel):
    id: int
    actor_id: int
    style_id: int
    style_name: str
    style_category: str
    image_url: str
    preview_url: str
    custom_prompt: str
    lifecycle_state: str
    published_at: Optional[datetime]
    created_at: datetime

class GenerateStyleRequest(BaseModel):
    style_id: int
    custom_prompt: str = ""
    actor_id: Optional[int] = None


class StylePublishRequest(BaseModel):
    style_id: int


class StyleResultGroupSchema(BaseModel):
    style_id: int
    style_name: str
    style_category: str
    results: List[GeneratedResultSchema]


class StyleResultGroupListSchema(BaseModel):
    groups: List[StyleResultGroupSchema]


class StyleResultStateToggleRequest(BaseModel):
    result_id: int
    published: bool


class ThreeViewRawImageSchema(BaseModel):
    id: int
    view_angle: Literal["front", "left", "right"]
    image_url: str
    original_url: str
    preview_url: str
    bucket_name: str
    object_key: str
    preview_bucket_name: str
    preview_object_key: str
    preview_image_url: str
    preview_mime_type: str
    preview_width: int
    preview_height: int
    preview_file_size: int
    variant_urls: dict[str, str] = Field(default_factory=dict)
    source_filename: str
    mime_type: str
    file_size: int
    width: int
    height: int
    expected_ratio: str
    created_at: datetime


class ThreeViewUploadSchema(BaseModel):
    session_id: int
    session_key: str
    actor_id: int
    is_current: bool
    superseded_at: Optional[datetime]
    composite_image_url: str
    composite_original_url: str
    composite_preview_url: str
    composite_variant_urls: dict[str, str] = Field(default_factory=dict)
    composite_bucket: str
    composite_object_key: str
    composite_preview_bucket: str
    composite_preview_object_key: str
    composite_preview_image_url: str
    composite_file_size: int
    composite_preview_file_size: int
    composite_width: int
    composite_height: int
    avatar_url: Optional[str] = None
    avatar_original_url: Optional[str] = None
    avatar_variant_urls: dict[str, str] = Field(default_factory=dict)
    expected_composite_ratio: str
    expected_single_ratio: str
    detection_note: str
    raw_images: List[ThreeViewRawImageSchema]
    created_at: datetime


class ThreeViewHistorySchema(BaseModel):
    items: List[ThreeViewUploadSchema]


class ThreeViewStateSchema(BaseModel):
    draft: Optional[ThreeViewUploadSchema]
    published: Optional[ThreeViewUploadSchema]


class ThreeViewDirectUploadFileSchema(BaseModel):
    view_angle: Literal["front", "left", "right"]
    filename: str
    content_type: str
    size: int = 0


class DirectUploadTargetSchema(BaseModel):
    view_angle: str
    bucket_name: str
    object_key: str
    source_filename: str
    mime_type: str
    file_size: int
    image_url: str
    upload_url: str
    upload_method: str


class ThreeViewDirectUploadPlanRequest(BaseModel):
    files: List[ThreeViewDirectUploadFileSchema]


class ThreeViewDirectUploadPlanSchema(BaseModel):
    upload_plan_token: str
    upload_batch_key: str
    expires_in_seconds: int
    uploads: List[DirectUploadTargetSchema]


class ThreeViewComposeJobCreateRequest(BaseModel):
    upload_plan_token: str
    reuse_latest_missing: bool = False


class ThreeViewComposeJobSchema(BaseModel):
    job_key: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    result: Optional[ThreeViewUploadSchema] = None


class PortraitVideoSchema(BaseModel):
    id: int
    actor_id: int
    user_id: int
    video_type: VideoTypeLiteral
    is_current: bool
    superseded_at: Optional[datetime]
    bucket_name: str
    object_key: str
    video_url: str
    preview_url: str
    source_filename: str
    mime_type: str
    file_size: int
    created_at: datetime


class PortraitVideoListSchema(BaseModel):
    items: List[PortraitVideoSchema]


class PortraitVideoTypeStateSchema(BaseModel):
    draft: Optional[PortraitVideoSchema]
    published: Optional[PortraitVideoSchema]


class PortraitVideoStateSchema(BaseModel):
    intro: PortraitVideoTypeStateSchema
    showreel: PortraitVideoTypeStateSchema
    both_published_ready: bool


class PortraitVideoDirectUploadPlanRequest(BaseModel):
    video_type: VideoTypeLiteral
    filename: str
    content_type: str
    size: int = 0


class PortraitVideoDirectUploadPlanSchema(BaseModel):
    upload_plan_token: str
    upload_batch_key: str
    expires_in_seconds: int
    upload: DirectUploadTargetSchema


class PortraitVideoDirectUploadCommitRequest(BaseModel):
    upload_plan_token: str


class PortraitVideoPublishRequest(BaseModel):
    video_type: VideoTypeLiteral


class PortraitAudioSchema(BaseModel):
    id: int
    actor_id: int
    user_id: int
    is_published: bool
    superseded_at: Optional[datetime]
    bucket_name: str
    object_key: str
    audio_url: str
    preview_url: str
    source_filename: str
    mime_type: str
    file_size: int
    created_at: datetime


class PortraitAudioListSchema(BaseModel):
    items: List[PortraitAudioSchema]


class PortraitAudioPublishToggleRequest(BaseModel):
    audio_id: int
    published: bool


class HistoryCleanupResultSchema(BaseModel):
    deleted_records: int
    deleted_objects: int
    skipped_objects: int


class PublishedActorCardSchema(BaseModel):
    actor_id: int
    name: str
    external_id: str
    tags: List[str]
    cover_image_url: Optional[str]
    published_three_view_url: Optional[str]
    published_video_url: Optional[str]
    published_style_count: int
    published_audio_count: int
    updated_at: datetime


class EnterpriseSignedActorCardSchema(PublishedActorCardSchema):
    signed_at: datetime
    payment_status: str = "not_ordered"
    payment_status_label: str = "未下单"
    latest_order_no: Optional[str] = None
    latest_order_status: Optional[str] = None
    latest_order_at: Optional[datetime] = None
    latest_line_total_amount: int = 0


class EnterpriseActorSigningActionSchema(BaseModel):
    actor_id: int
    enterprise_user_id: int
    signed_at: datetime
    already_signed: bool
    message: str


class SignedEnterpriseSchema(BaseModel):
    enterprise_user_id: int
    company_name: str
    company_intro: str
    credit_code: str
    registered_address: str
    signed_at: datetime
    created_at: datetime
    payment_status: str = "not_ordered"
    payment_status_label: str = "未下单"
    latest_order_no: Optional[str] = None
    latest_order_status: Optional[str] = None
    latest_order_at: Optional[datetime] = None
    latest_line_total_amount: int = 0


class PublishedActorDetailSchema(BaseModel):
    actor: ActorBasicInfoSchema
    published_three_view: Optional[ThreeViewUploadSchema]
    published_video: Optional[PortraitVideoSchema]
    published_videos: List[PortraitVideoSchema]
    published_audios: List[PortraitAudioSchema]
    published_styles: List[GeneratedResultSchema]
    is_signed_by_current_enterprise: bool = False


PaymentChannelLiteral = Literal["wechat", "alipay"]


class PaymentOpsConfigSchema(BaseModel):
    use_mock: bool
    mock_channel_auto_success: bool
    fee_rate_bps: int
    auto_accept_hours: int
    dispute_protect_hours: int
    max_hold_hours: int
    settlement_safety_buffer_hours: int
    allow_wechat: bool
    allow_alipay: bool
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class PaymentOpsConfigUpdateRequest(BaseModel):
    fee_rate_bps: int = Field(ge=0, le=4000)
    auto_accept_hours: int = Field(ge=1, le=2160)
    dispute_protect_hours: int = Field(ge=0, le=2160)
    max_hold_hours: int = Field(ge=24, le=8760)
    settlement_safety_buffer_hours: int = Field(ge=0, le=168)
    allow_wechat: bool = True
    allow_alipay: bool = True


class CartItemSchema(BaseModel):
    cart_item_id: int
    actor_id: int
    actor_name: str
    actor_external_id: str
    actor_quote_amount: int
    pricing_unit: str
    status: str
    signed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CartItemCreateRequest(BaseModel):
    actor_id: int


class CartItemDeleteRequest(BaseModel):
    actor_id: int


class CartListSchema(BaseModel):
    items: List[CartItemSchema]


class OrderPreviewRequest(BaseModel):
    actor_ids: Optional[List[int]] = None


class OrderPreviewLineSchema(BaseModel):
    cart_item_id: int
    actor_id: int
    actor_name: str
    actor_external_id: str
    actor_quote_amount: int
    platform_fee_amount: int
    line_total_amount: int


class OrderPreviewSchema(BaseModel):
    currency: str
    fee_rate_bps: int
    actor_total_amount: int
    platform_fee_amount: int
    payable_total_amount: int
    items: List[OrderPreviewLineSchema]


class OrderCreateRequest(BaseModel):
    actor_ids: Optional[List[int]] = None


class PaymentCreateRequest(BaseModel):
    channel: PaymentChannelLiteral


class PaymentSchema(BaseModel):
    payment_id: int
    order_id: int
    out_trade_no: str
    channel_trade_no: Optional[str]
    channel: PaymentChannelLiteral
    amount: int
    status: str
    paid_at: Optional[datetime]
    expires_at: Optional[datetime]
    pay_payload: Optional[dict]
    created_at: datetime
    updated_at: datetime


class RefundSchema(BaseModel):
    refund_id: int
    order_id: int
    actor_item_id: Optional[int]
    payment_id: Optional[int]
    out_refund_no: str
    channel_refund_no: Optional[str]
    channel: PaymentChannelLiteral
    refund_amount: int
    status: str
    reason: str
    operator_user_id: Optional[int]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SettlementSchema(BaseModel):
    settlement_id: int
    order_id: int
    actor_item_id: Optional[int]
    actor_id: Optional[int]
    out_settle_no: str
    channel_settle_no: Optional[str]
    channel: PaymentChannelLiteral
    settle_amount: int
    platform_fee_amount: int
    status: str
    requested_at: datetime
    settled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class OrderItemSchema(BaseModel):
    order_item_id: int
    actor_id: int
    actor_name: str
    actor_external_id: str
    actor_quote_amount: int
    platform_fee_amount: int
    line_total_amount: int
    refunded_amount: int
    settled_amount: int
    actor_refunded_amount: int
    actor_settle_remaining_amount: int
    item_refundable_remaining_amount: int
    item_status: str
    actor_release_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class EnterpriseSummarySchema(BaseModel):
    enterprise_user_id: int
    company_name: str
    username: str


class OrderSchema(BaseModel):
    order_no: str
    status: str
    currency: str
    actor_total_amount: int
    platform_fee_rate_bps: int
    platform_fee_amount: int
    payable_total_amount: int
    paid_total_amount: int
    refunded_total_amount: int
    refundable_remaining_amount: int
    settlement_status: str
    settled_total_amount: int
    auto_accept_at: Optional[datetime]
    release_at: Optional[datetime]
    accepted_at: Optional[datetime]
    payment_succeeded_at: Optional[datetime]
    settled_at: Optional[datetime]
    closed_at: Optional[datetime]
    enterprise: Optional[EnterpriseSummarySchema] = None
    items: List[OrderItemSchema] = Field(default_factory=list)
    payments: List[PaymentSchema] = Field(default_factory=list)
    refunds: List[RefundSchema] = Field(default_factory=list)
    settlements: List[SettlementSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class OrderListSchema(BaseModel):
    items: List[OrderSchema]


class RefundCreateRequest(BaseModel):
    order_no: str
    refund_amount: int = Field(gt=0)
    reason: str = Field(default="", max_length=256)
    actor_id: Optional[int] = None


class RefundApproveRequest(BaseModel):
    out_refund_no: str


class RefundListSchema(BaseModel):
    items: List[RefundSchema]


class SettlementRunRequest(BaseModel):
    limit: int = Field(default=200, ge=1, le=1000)


class SettlementRunResultItemSchema(BaseModel):
    order_no: str
    actor_id: int
    settled_amount: int
    status: str
    reason: Optional[str] = None


class SettlementRunResultSchema(BaseModel):
    processed_count: int
    settled_count: int
    failed_count: int
    items: List[SettlementRunResultItemSchema]


class ActorWalletSummarySchema(BaseModel):
    actor_id: int
    currency: str = "CNY"
    available_amount: int
    total_settled_amount: int
    total_withdrawing_amount: int
    total_withdrawn_amount: int
    total_failed_withdraw_amount: int
    updated_at: datetime


class ActorWithdrawCreateRequest(BaseModel):
    amount: int = Field(gt=0)
    channel: PaymentChannelLiteral
    account_name: str = Field(min_length=1, max_length=64)
    account_no: str = Field(min_length=1, max_length=128)
    remark: str = Field(default="", max_length=256)


class ActorWithdrawRecordSchema(BaseModel):
    withdraw_id: int
    actor_id: int
    actor_user_id: int
    channel: PaymentChannelLiteral
    out_withdraw_no: str
    channel_withdraw_no: Optional[str]
    amount: int
    status: str
    account_name: str
    account_no_masked: str
    remark: str
    requested_at: datetime
    processed_at: Optional[datetime]
    failure_reason: str
    created_at: datetime
    updated_at: datetime


class ActorWithdrawListSchema(BaseModel):
    items: List[ActorWithdrawRecordSchema]


ActorWithdrawReviewActionLiteral = Literal["approve", "reject", "fail"]


class AdminActorWithdrawRecordSchema(ActorWithdrawRecordSchema):
    actor_name: str = ""
    actor_external_id: str = ""
    actor_user_display_name: str = ""


class AdminActorWithdrawListSchema(BaseModel):
    items: List[AdminActorWithdrawRecordSchema]


class AdminActorWithdrawReviewRequest(BaseModel):
    out_withdraw_no: str
    action: ActorWithdrawReviewActionLiteral
    failure_reason: str = Field(default="", max_length=256)
