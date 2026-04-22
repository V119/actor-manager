import peewee
import peewee_async
from datetime import datetime
from playhouse.postgres_ext import BinaryJSONField

database = peewee_async.PooledPostgresqlDatabase(None)

class BaseModel(peewee_async.AioModel):
    class Meta:
        database = database

class ActorModel(BaseModel):
    name = peewee.CharField()
    external_id = peewee.CharField(unique=True)
    age = peewee.IntegerField()
    location = peewee.CharField()
    hometown = peewee.CharField(default="")
    height = peewee.IntegerField()
    weight_kg = peewee.IntegerField(default=0)
    bust_cm = peewee.IntegerField(default=0)
    waist_cm = peewee.IntegerField(default=0)
    hip_cm = peewee.IntegerField(default=0)
    shoe_size = peewee.CharField(default="")
    bio = peewee.TextField()
    acting_requirements = peewee.TextField(default="")
    rejected_requirements = peewee.TextField(default="")
    availability_note = peewee.TextField(default="")
    pricing_unit = peewee.CharField(default="project")
    pricing_amount = peewee.IntegerField(default=0)
    tags = BinaryJSONField(default=[])
    is_published = peewee.BooleanField(default=False)
    created_at = peewee.DateTimeField(default=datetime.now)

class PortraitModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='portraits')
    image_url = peewee.CharField()
    portrait_type = peewee.CharField()
    created_at = peewee.DateTimeField(default=datetime.now)

class StyleModel(BaseModel):
    name = peewee.CharField()
    description = peewee.TextField()
    preview_url = peewee.CharField()
    category = peewee.CharField()

class UserModel(BaseModel):
    username = peewee.CharField(unique=True)
    password_hash = peewee.CharField()
    role = peewee.CharField()  # "individual" | "enterprise" | "admin"
    display_name = peewee.CharField()
    company_intro = peewee.TextField(default="")
    company_credit_code = peewee.CharField(default="")
    company_registered_address = peewee.TextField(default="")
    created_at = peewee.DateTimeField(default=datetime.now)


class PortraitGuidanceSampleModel(BaseModel):
    view_angle = peewee.CharField(unique=True, index=True)  # left | front | right
    bucket_name = peewee.CharField()
    object_key = peewee.CharField()
    image_url = peewee.CharField()
    source_filename = peewee.CharField()
    mime_type = peewee.CharField()
    file_size = peewee.BigIntegerField(default=0)
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)


class GeneratedResultModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel)
    user = peewee.ForeignKeyField(UserModel, backref='generated_results', on_delete='CASCADE', null=True)
    style = peewee.ForeignKeyField(StyleModel)
    image_url = peewee.CharField()
    custom_prompt = peewee.TextField(default="")
    lifecycle_state = peewee.CharField(default='draft', index=True)  # draft | published | superseded
    superseded_at = peewee.DateTimeField(null=True, index=True)
    published_at = peewee.DateTimeField(null=True, index=True)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('actor', 'user', 'style', 'lifecycle_state', 'created_at'), False),
        )

class SessionModel(BaseModel):
    user = peewee.ForeignKeyField(UserModel, backref='sessions', on_delete='CASCADE')
    token = peewee.CharField(unique=True, index=True)
    expires_at = peewee.DateTimeField()
    created_at = peewee.DateTimeField(default=datetime.now)

class ProtocolModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, null=True)
    enterprise_user = peewee.ForeignKeyField(UserModel, backref='created_protocols', null=True)
    target_user = peewee.ForeignKeyField(UserModel, backref='assigned_protocols', null=True)
    company_name = peewee.CharField()
    title = peewee.CharField()
    content = peewee.TextField()
    status = peewee.CharField(default='pending')
    created_at = peewee.DateTimeField(default=datetime.now)
    signed_at = peewee.DateTimeField(null=True)


class AgreementTemplateConfigModel(BaseModel):
    version = peewee.IntegerField(default=1)
    source_document_name = peewee.CharField(default="")
    party_a_company_name = peewee.CharField(default="")
    party_a_credit_code = peewee.CharField(default="")
    party_a_registered_address = peewee.TextField(default="")
    authorization_date_mode = peewee.CharField(default="fixed")
    authorization_term_months = peewee.IntegerField(null=True)
    authorization_start_date = peewee.DateField(null=True)
    authorization_end_date = peewee.DateField(null=True)
    party_a_signature_label = peewee.CharField(default="")
    party_a_signed_date = peewee.DateField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)


class EnterpriseAgreementTemplateConfigModel(BaseModel):
    version = peewee.IntegerField(default=1)
    source_document_name = peewee.CharField(default="")
    party_a_company_name = peewee.CharField(default="")
    party_a_credit_code = peewee.CharField(default="")
    party_a_registered_address = peewee.TextField(default="")
    authorization_date_mode = peewee.CharField(default="fixed")
    authorization_term_months = peewee.IntegerField(null=True)
    authorization_start_date = peewee.DateField(null=True)
    authorization_end_date = peewee.DateField(null=True)
    party_a_signature_label = peewee.CharField(default="")
    party_a_signed_date = peewee.DateField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)


class ActorAgreementModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='agreement_record', unique=True)
    user = peewee.ForeignKeyField(UserModel, backref='agreement_record', on_delete='CASCADE', unique=True)
    template_version = peewee.IntegerField(default=1, index=True)
    status = peewee.CharField(default='pending', index=True)
    party_b_name = peewee.CharField()
    party_b_gender = peewee.CharField()
    party_b_identity_number = peewee.CharField()
    party_b_contact_address = peewee.TextField()
    party_b_phone = peewee.CharField()
    party_b_email = peewee.CharField()
    party_b_signature_data_url = peewee.TextField()
    party_b_signed_date = peewee.DateField(null=True)
    signed_at = peewee.DateTimeField(null=True, index=True)
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)


class EnterpriseAgreementModel(BaseModel):
    user = peewee.ForeignKeyField(UserModel, backref='enterprise_agreement_record', on_delete='CASCADE', unique=True)
    template_version = peewee.IntegerField(default=1, index=True)
    status = peewee.CharField(default='pending', index=True)
    party_b_company_name = peewee.CharField()
    party_b_credit_code = peewee.CharField()
    party_b_registered_address = peewee.TextField()
    party_b_signature_data_url = peewee.TextField()
    party_b_signed_date = peewee.DateField(null=True)
    signed_at = peewee.DateTimeField(null=True, index=True)
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)


class EnterpriseActorSigningModel(BaseModel):
    enterprise_user = peewee.ForeignKeyField(UserModel, backref='actor_signings', on_delete='CASCADE')
    actor = peewee.ForeignKeyField(ActorModel, backref='enterprise_signings', on_delete='CASCADE')
    signed_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('enterprise_user', 'actor'), True),
            (('enterprise_user', 'signed_at'), False),
            (('actor', 'signed_at'), False),
        )


class PortraitUploadSessionModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_upload_sessions')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_upload_sessions', on_delete='CASCADE')
    session_key = peewee.CharField(unique=True, index=True)
    is_current = peewee.BooleanField(default=True, index=True)
    superseded_at = peewee.DateTimeField(null=True, index=True)
    composite_bucket = peewee.CharField()
    composite_object_key = peewee.CharField()
    composite_image_url = peewee.CharField()
    composite_preview_bucket = peewee.CharField(default="")
    composite_preview_object_key = peewee.CharField(default="")
    composite_preview_image_url = peewee.CharField(default="")
    composite_file_size = peewee.BigIntegerField(default=0)
    composite_preview_file_size = peewee.BigIntegerField(default=0)
    composite_variant_map = BinaryJSONField(default=dict)
    composite_width = peewee.IntegerField()
    composite_height = peewee.IntegerField()
    avatar_bucket_name = peewee.CharField(default="")
    avatar_object_key = peewee.CharField(default="")
    avatar_image_url = peewee.CharField(default="")
    avatar_mime_type = peewee.CharField(default="")
    avatar_width = peewee.IntegerField(default=0)
    avatar_height = peewee.IntegerField(default=0)
    avatar_file_size = peewee.BigIntegerField(default=0)
    avatar_variant_map = BinaryJSONField(default=dict)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('actor', 'user', 'created_at'), False),
        )


class PortraitUploadAssetModel(BaseModel):
    session = peewee.ForeignKeyField(PortraitUploadSessionModel, backref='raw_assets', on_delete='CASCADE')
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_upload_assets')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_upload_assets', on_delete='CASCADE')
    view_angle = peewee.CharField()
    bucket_name = peewee.CharField()
    object_key = peewee.CharField()
    image_url = peewee.CharField()
    source_filename = peewee.CharField()
    mime_type = peewee.CharField()
    file_size = peewee.BigIntegerField(default=0)
    width = peewee.IntegerField()
    height = peewee.IntegerField()
    preview_bucket_name = peewee.CharField(default="")
    preview_object_key = peewee.CharField(default="")
    preview_image_url = peewee.CharField(default="")
    preview_mime_type = peewee.CharField(default="")
    preview_width = peewee.IntegerField(default=0)
    preview_height = peewee.IntegerField(default=0)
    preview_file_size = peewee.BigIntegerField(default=0)
    variant_map = BinaryJSONField(default=dict)
    expected_ratio = peewee.CharField(default='9:16')
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('session', 'view_angle'), True),
            (('actor', 'user', 'created_at'), False),
        )


class PortraitVideoAssetModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_video_assets')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_video_assets', on_delete='CASCADE')
    video_type = peewee.CharField(default='intro', index=True)
    is_current = peewee.BooleanField(default=True, index=True)
    superseded_at = peewee.DateTimeField(null=True, index=True)
    bucket_name = peewee.CharField()
    object_key = peewee.CharField()
    video_url = peewee.CharField()
    source_filename = peewee.CharField()
    mime_type = peewee.CharField()
    file_size = peewee.BigIntegerField(default=0)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('actor', 'user', 'video_type', 'created_at'), False),
        )


class PortraitAudioAssetModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_audio_assets')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_audio_assets', on_delete='CASCADE')
    is_published = peewee.BooleanField(default=False, index=True)
    superseded_at = peewee.DateTimeField(null=True, index=True)
    bucket_name = peewee.CharField()
    object_key = peewee.CharField()
    audio_url = peewee.CharField()
    source_filename = peewee.CharField()
    mime_type = peewee.CharField()
    file_size = peewee.BigIntegerField(default=0)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('actor', 'user', 'is_published', 'created_at'), False),
        )


class PortraitComposeJobModel(BaseModel):
    job_key = peewee.CharField(unique=True, index=True)
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_compose_jobs')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_compose_jobs', on_delete='CASCADE')
    status = peewee.CharField(default='pending', index=True)  # pending | processing | completed | failed
    request_payload = BinaryJSONField(default=dict)
    result_session = peewee.ForeignKeyField(PortraitUploadSessionModel, null=True, backref='compose_jobs')
    error_message = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('user', 'status', 'created_at'), False),
            (('status', 'created_at'), False),
        )


class PaymentOpsConfigModel(BaseModel):
    fee_rate_bps = peewee.IntegerField(default=600)
    auto_accept_hours = peewee.IntegerField(default=72)
    dispute_protect_hours = peewee.IntegerField(default=168)
    max_hold_hours = peewee.IntegerField(default=4320)
    settlement_safety_buffer_hours = peewee.IntegerField(default=24)
    allow_wechat = peewee.BooleanField(default=True)
    allow_alipay = peewee.BooleanField(default=True)
    updated_by = peewee.ForeignKeyField(UserModel, null=True, backref='payment_configs_updated')
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)


class EnterpriseCartItemModel(BaseModel):
    enterprise_user = peewee.ForeignKeyField(UserModel, backref='cart_items', on_delete='CASCADE')
    actor = peewee.ForeignKeyField(ActorModel, backref='cart_items', on_delete='CASCADE')
    signing = peewee.ForeignKeyField(EnterpriseActorSigningModel, null=True, backref='cart_items', on_delete='SET NULL')
    actor_quote_amount = peewee.IntegerField(default=0)
    quote_snapshot = BinaryJSONField(default=dict)
    status = peewee.CharField(default='active', index=True)  # active | removed | converted
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('enterprise_user', 'actor'), True),
            (('enterprise_user', 'status', 'created_at'), False),
        )


class EnterpriseOrderModel(BaseModel):
    enterprise_user = peewee.ForeignKeyField(UserModel, backref='enterprise_orders', on_delete='CASCADE')
    order_no = peewee.CharField(unique=True, index=True)
    status = peewee.CharField(default='pending_payment', index=True)
    currency = peewee.CharField(default='CNY')
    actor_total_amount = peewee.IntegerField(default=0)
    platform_fee_rate_bps = peewee.IntegerField(default=0)
    platform_fee_amount = peewee.IntegerField(default=0)
    payable_total_amount = peewee.IntegerField(default=0)
    paid_total_amount = peewee.IntegerField(default=0)
    refunded_total_amount = peewee.IntegerField(default=0)
    settlement_status = peewee.CharField(default='pending', index=True)
    settled_total_amount = peewee.IntegerField(default=0)
    auto_accept_at = peewee.DateTimeField(null=True, index=True)
    release_at = peewee.DateTimeField(null=True, index=True)
    accepted_at = peewee.DateTimeField(null=True)
    payment_succeeded_at = peewee.DateTimeField(null=True, index=True)
    settled_at = peewee.DateTimeField(null=True, index=True)
    closed_at = peewee.DateTimeField(null=True, index=True)
    order_snapshot = BinaryJSONField(default=dict)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('enterprise_user', 'status', 'created_at'), False),
            (('enterprise_user', 'settlement_status', 'created_at'), False),
        )


class EnterpriseOrderActorItemModel(BaseModel):
    order = peewee.ForeignKeyField(EnterpriseOrderModel, backref='actor_items', on_delete='CASCADE')
    enterprise_user = peewee.ForeignKeyField(UserModel, backref='ordered_actor_items', on_delete='CASCADE')
    actor = peewee.ForeignKeyField(ActorModel, backref='order_items')
    cart_item = peewee.ForeignKeyField(EnterpriseCartItemModel, null=True, backref='order_items', on_delete='SET NULL')
    actor_quote_amount = peewee.IntegerField(default=0)
    platform_fee_amount = peewee.IntegerField(default=0)
    line_total_amount = peewee.IntegerField(default=0)
    settled_amount = peewee.IntegerField(default=0)
    refunded_amount = peewee.IntegerField(default=0)
    item_status = peewee.CharField(default='pending', index=True)  # pending | paid | settled | partially_refunded | refunded
    actor_receivable_amount = peewee.IntegerField(default=0)
    actor_release_at = peewee.DateTimeField(null=True, index=True)
    quote_snapshot = BinaryJSONField(default=dict)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('order', 'actor'), True),
            (('actor', 'item_status', 'created_at'), False),
        )


class PaymentTransactionModel(BaseModel):
    enterprise_user = peewee.ForeignKeyField(UserModel, backref='payment_transactions', on_delete='CASCADE')
    order = peewee.ForeignKeyField(EnterpriseOrderModel, backref='payments', on_delete='CASCADE')
    channel = peewee.CharField(index=True)  # wechat | alipay
    out_trade_no = peewee.CharField(unique=True, index=True)
    channel_trade_no = peewee.CharField(null=True, index=True)
    amount = peewee.IntegerField(default=0)
    status = peewee.CharField(default='initiated', index=True)  # initiated | paid | failed | closed
    paid_at = peewee.DateTimeField(null=True, index=True)
    expires_at = peewee.DateTimeField(null=True)
    request_payload = BinaryJSONField(default=dict)
    response_payload = BinaryJSONField(default=dict)
    notify_payload = BinaryJSONField(default=dict)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('order', 'status', 'created_at'), False),
            (('enterprise_user', 'channel', 'created_at'), False),
        )


class SettlementRecordModel(BaseModel):
    order = peewee.ForeignKeyField(EnterpriseOrderModel, backref='settlements', on_delete='CASCADE')
    actor_item = peewee.ForeignKeyField(EnterpriseOrderActorItemModel, null=True, backref='settlements', on_delete='CASCADE')
    actor = peewee.ForeignKeyField(ActorModel, null=True, backref='settlements')
    channel = peewee.CharField(default='internal', index=True)  # wechat | alipay | internal
    out_settle_no = peewee.CharField(unique=True, index=True)
    channel_settle_no = peewee.CharField(null=True, index=True)
    settle_amount = peewee.IntegerField(default=0)
    platform_fee_amount = peewee.IntegerField(default=0)
    status = peewee.CharField(default='pending', index=True)  # pending | settled | failed | reversed
    requested_at = peewee.DateTimeField(default=datetime.now, index=True)
    settled_at = peewee.DateTimeField(null=True, index=True)
    request_payload = BinaryJSONField(default=dict)
    response_payload = BinaryJSONField(default=dict)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('order', 'status', 'created_at'), False),
            (('actor', 'status', 'created_at'), False),
        )


class ActorWithdrawRecordModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='withdraw_records', on_delete='CASCADE')
    actor_user = peewee.ForeignKeyField(UserModel, backref='actor_withdraw_records', on_delete='CASCADE')
    channel = peewee.CharField(index=True)  # wechat | alipay
    out_withdraw_no = peewee.CharField(unique=True, index=True)
    channel_withdraw_no = peewee.CharField(null=True, index=True)
    amount = peewee.IntegerField(default=0)
    status = peewee.CharField(default='pending', index=True)  # pending | processing | succeeded | failed | rejected
    account_name = peewee.CharField(default="")
    account_no = peewee.CharField(default="")
    account_snapshot = BinaryJSONField(default=dict)
    remark = peewee.CharField(default="")
    requested_at = peewee.DateTimeField(default=datetime.now, index=True)
    processed_at = peewee.DateTimeField(null=True, index=True)
    failure_reason = peewee.CharField(default="")
    request_payload = BinaryJSONField(default=dict)
    response_payload = BinaryJSONField(default=dict)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('actor', 'status', 'created_at'), False),
            (('actor_user', 'created_at'), False),
        )


class RefundRecordModel(BaseModel):
    enterprise_user = peewee.ForeignKeyField(UserModel, backref='refunds', on_delete='CASCADE')
    order = peewee.ForeignKeyField(EnterpriseOrderModel, backref='refunds', on_delete='CASCADE')
    actor_item = peewee.ForeignKeyField(EnterpriseOrderActorItemModel, null=True, backref='refunds', on_delete='SET NULL')
    payment = peewee.ForeignKeyField(PaymentTransactionModel, null=True, backref='refunds', on_delete='SET NULL')
    channel = peewee.CharField(index=True)  # wechat | alipay | internal
    out_refund_no = peewee.CharField(unique=True, index=True)
    channel_refund_no = peewee.CharField(null=True, index=True)
    refund_amount = peewee.IntegerField(default=0)
    status = peewee.CharField(default='pending', index=True)  # pending | succeeded | failed | canceled
    reason = peewee.CharField(default="")
    operator_user = peewee.ForeignKeyField(UserModel, null=True, backref='operated_refunds', on_delete='SET NULL')
    reviewed_by = peewee.ForeignKeyField(UserModel, null=True, backref='reviewed_refunds', on_delete='SET NULL')
    reviewed_at = peewee.DateTimeField(null=True, index=True)
    request_payload = BinaryJSONField(default=dict)
    response_payload = BinaryJSONField(default=dict)
    notify_payload = BinaryJSONField(default=dict)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('order', 'status', 'created_at'), False),
            (('enterprise_user', 'status', 'created_at'), False),
            (('operator_user', 'created_at'), False),
        )


class PaymentAuditLogModel(BaseModel):
    enterprise_user = peewee.ForeignKeyField(UserModel, null=True, backref='payment_audit_logs', on_delete='SET NULL')
    order = peewee.ForeignKeyField(EnterpriseOrderModel, null=True, backref='audit_logs', on_delete='SET NULL')
    actor_item = peewee.ForeignKeyField(EnterpriseOrderActorItemModel, null=True, backref='audit_logs', on_delete='SET NULL')
    payment = peewee.ForeignKeyField(PaymentTransactionModel, null=True, backref='audit_logs', on_delete='SET NULL')
    refund = peewee.ForeignKeyField(RefundRecordModel, null=True, backref='audit_logs', on_delete='SET NULL')
    settlement = peewee.ForeignKeyField(SettlementRecordModel, null=True, backref='audit_logs', on_delete='SET NULL')
    action = peewee.CharField(index=True)
    operator_user = peewee.ForeignKeyField(UserModel, null=True, backref='operated_payment_audit_logs', on_delete='SET NULL')
    detail = BinaryJSONField(default=dict)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('order', 'created_at'), False),
            (('action', 'created_at'), False),
            (('operator_user', 'created_at'), False),
        )
