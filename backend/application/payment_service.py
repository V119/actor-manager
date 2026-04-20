from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
from typing import Any, Literal
import uuid
import peewee

from backend.infrastructure.config import settings
from backend.infrastructure.orm_models import (
    ActorModel,
    ActorWithdrawRecordModel,
    EnterpriseActorSigningModel,
    EnterpriseCartItemModel,
    EnterpriseOrderActorItemModel,
    EnterpriseOrderModel,
    PaymentAuditLogModel,
    PaymentOpsConfigModel,
    PaymentTransactionModel,
    RefundRecordModel,
    SettlementRecordModel,
    UserModel,
    database,
)


logger = logging.getLogger(__name__)

PaymentChannel = Literal["wechat", "alipay"]
PAYMENT_CHANNELS: tuple[str, str] = ("wechat", "alipay")

ORDER_STATUS_PENDING_PAYMENT = "pending_payment"
ORDER_STATUS_PAID = "paid"
ORDER_STATUS_SETTLED = "settled"
ORDER_STATUS_PARTIALLY_REFUNDED = "partially_refunded"
ORDER_STATUS_REFUNDED = "refunded"
ORDER_STATUS_PAYMENT_FAILED = "payment_failed"

SETTLEMENT_STATUS_PENDING = "pending"
SETTLEMENT_STATUS_PARTIAL = "partial"
SETTLEMENT_STATUS_SETTLED = "settled"

ORDER_ITEM_STATUS_PENDING = "pending"
ORDER_ITEM_STATUS_PAID = "paid"
ORDER_ITEM_STATUS_SETTLED = "settled"
ORDER_ITEM_STATUS_PARTIALLY_REFUNDED = "partially_refunded"
ORDER_ITEM_STATUS_REFUNDED = "refunded"

PAYMENT_STATUS_INITIATED = "initiated"
PAYMENT_STATUS_PAID = "paid"
PAYMENT_STATUS_FAILED = "failed"

REFUND_STATUS_PENDING = "pending"
REFUND_STATUS_SUCCEEDED = "succeeded"
REFUND_STATUS_FAILED = "failed"

SETTLE_STATUS_PENDING = "pending"
SETTLE_STATUS_SETTLED = "settled"
SETTLE_STATUS_FAILED = "failed"

WITHDRAW_STATUS_PENDING = "pending"
WITHDRAW_STATUS_PROCESSING = "processing"
WITHDRAW_STATUS_SUCCEEDED = "succeeded"
WITHDRAW_STATUS_FAILED = "failed"
WITHDRAW_STATUS_REJECTED = "rejected"
WITHDRAW_STATUSES: tuple[str, ...] = (
    WITHDRAW_STATUS_PENDING,
    WITHDRAW_STATUS_PROCESSING,
    WITHDRAW_STATUS_SUCCEEDED,
    WITHDRAW_STATUS_FAILED,
    WITHDRAW_STATUS_REJECTED,
)
WITHDRAW_REVIEW_ACTIONS: tuple[str, ...] = ("approve", "reject", "fail")


def _utcnow() -> datetime:
    return datetime.now()


def _gen_no(prefix: str) -> str:
    return f"{prefix}{_utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}".upper()


def _clip_int(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, int(value)))


@dataclass
class MockChannelGateway:
    auto_success: bool = True

    def initiate_payment(
        self,
        *,
        channel: PaymentChannel,
        out_trade_no: str,
        amount: int,
        order_no: str,
    ) -> dict[str, Any]:
        if self.auto_success:
            return {
                "status": PAYMENT_STATUS_PAID,
                "channel_trade_no": f"{channel.upper()}_TRADE_{uuid.uuid4().hex[:16]}",
                "pay_payload": {
                    "pay_token": f"{channel}_pay_token_{uuid.uuid4().hex[:20]}",
                    "order_no": order_no,
                    "amount": amount,
                },
            }
        return {
            "status": PAYMENT_STATUS_INITIATED,
            "channel_trade_no": None,
            "pay_payload": {
                "pay_url": f"https://pay.mock/{channel}/{out_trade_no}",
                "order_no": order_no,
                "amount": amount,
            },
        }

    def refund(
        self,
        *,
        channel: PaymentChannel,
        out_trade_no: str,
        out_refund_no: str,
        amount: int,
        reason: str,
    ) -> dict[str, Any]:
        if self.auto_success:
            return {
                "status": REFUND_STATUS_SUCCEEDED,
                "channel_refund_no": f"{channel.upper()}_REFUND_{uuid.uuid4().hex[:16]}",
                "raw": {
                    "out_trade_no": out_trade_no,
                    "out_refund_no": out_refund_no,
                    "amount": amount,
                    "reason": reason,
                },
            }
        return {
            "status": REFUND_STATUS_FAILED,
            "channel_refund_no": None,
            "raw": {
                "error": "mock gateway set to manual mode",
            },
        }

    def settle(
        self,
        *,
        channel: PaymentChannel,
        out_settle_no: str,
        actor_id: int,
        amount: int,
        order_no: str,
    ) -> dict[str, Any]:
        if self.auto_success:
            return {
                "status": SETTLE_STATUS_SETTLED,
                "channel_settle_no": f"{channel.upper()}_SETTLE_{uuid.uuid4().hex[:16]}",
                "raw": {
                    "out_settle_no": out_settle_no,
                    "actor_id": actor_id,
                    "amount": amount,
                    "order_no": order_no,
                },
            }
        return {
            "status": SETTLE_STATUS_FAILED,
            "channel_settle_no": None,
            "raw": {
                "error": "mock gateway set to manual mode",
            },
        }


class DisabledGateway:
    def initiate_payment(
        self,
        *,
        channel: PaymentChannel,
        out_trade_no: str,
        amount: int,
        order_no: str,
    ) -> dict[str, Any]:
        raise ValueError(
            f"未启用 Mock 支付且未接入真实{channel}网关，无法发起支付（order_no={order_no}, out_trade_no={out_trade_no}）。"
        )

    def refund(
        self,
        *,
        channel: PaymentChannel,
        out_trade_no: str,
        out_refund_no: str,
        amount: int,
        reason: str,
    ) -> dict[str, Any]:
        raise ValueError(
            f"未启用 Mock 支付且未接入真实{channel}网关，无法发起退款（out_refund_no={out_refund_no}, out_trade_no={out_trade_no}）。"
        )

    def settle(
        self,
        *,
        channel: PaymentChannel,
        out_settle_no: str,
        actor_id: int,
        amount: int,
        order_no: str,
    ) -> dict[str, Any]:
        raise ValueError(
            f"未启用 Mock 支付且未接入真实{channel}网关，无法发起结算（out_settle_no={out_settle_no}, order_no={order_no}）。"
        )


def build_payment_gateway() -> MockChannelGateway | DisabledGateway:
    if bool(settings.PAYMENT_USE_MOCK):
        return MockChannelGateway(auto_success=bool(settings.PAYMENT_MOCK_CHANNEL_AUTO_SUCCESS))
    return DisabledGateway()


class PaymentService:
    def __init__(self, gateway: MockChannelGateway | DisabledGateway | None = None):
        self.gateway = gateway or build_payment_gateway()

    # -------------------------
    # Config
    # -------------------------
    def get_ops_config(self) -> dict[str, Any]:
        with database.allow_sync():
            config = self._get_or_create_ops_config_sync()
            return self._serialize_ops_config(config)

    def update_ops_config(self, *, operator_user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        with database.allow_sync():
            config = self._get_or_create_ops_config_sync()
            config.fee_rate_bps = _clip_int(payload.get("fee_rate_bps", config.fee_rate_bps), 0, 4000)
            config.auto_accept_hours = _clip_int(payload.get("auto_accept_hours", config.auto_accept_hours), 1, 24 * 90)
            config.dispute_protect_hours = _clip_int(payload.get("dispute_protect_hours", config.dispute_protect_hours), 0, 24 * 90)
            config.max_hold_hours = _clip_int(payload.get("max_hold_hours", config.max_hold_hours), 24, 24 * 365)
            config.settlement_safety_buffer_hours = _clip_int(
                payload.get("settlement_safety_buffer_hours", config.settlement_safety_buffer_hours),
                0,
                24 * 7,
            )
            config.allow_wechat = bool(payload.get("allow_wechat", config.allow_wechat))
            config.allow_alipay = bool(payload.get("allow_alipay", config.allow_alipay))
            if config.settlement_safety_buffer_hours >= config.max_hold_hours:
                raise ValueError("结算安全缓冲时间必须小于最大冻结时间。")
            config.updated_by_id = operator_user_id
            config.updated_at = _utcnow()
            config.save()
            self._audit(
                action="payment_config_updated",
                operator_user_id=operator_user_id,
                detail=self._serialize_ops_config(config),
            )
            return self._serialize_ops_config(config)

    # -------------------------
    # Cart
    # -------------------------
    def ensure_cart_item_for_signing(
        self,
        *,
        enterprise_user_id: int,
        actor_id: int,
        signing_id: int | None,
    ) -> dict[str, Any]:
        with database.allow_sync():
            actor = ActorModel.get_or_none(
                (ActorModel.id == actor_id)
                & (ActorModel.is_published == True)  # noqa: E712
            )
            if not actor:
                raise ValueError("演员不存在或未发布，无法加入购物车。")

            snapshot = self._build_quote_snapshot(actor=actor)
            now = _utcnow()
            item, created = EnterpriseCartItemModel.get_or_create(
                enterprise_user_id=enterprise_user_id,
                actor_id=actor_id,
                defaults={
                    "signing_id": signing_id,
                    "actor_quote_amount": int(actor.pricing_amount or 0),
                    "quote_snapshot": snapshot,
                    "status": "active",
                    "created_at": now,
                    "updated_at": now,
                },
            )
            if not created:
                item.signing_id = signing_id
                item.actor_quote_amount = int(actor.pricing_amount or 0)
                item.quote_snapshot = snapshot
                item.status = "active"
                item.updated_at = now
                item.save()
            return self._serialize_cart_item(item)

    def add_actor_to_cart(self, *, enterprise_user_id: int, actor_id: int) -> dict[str, Any]:
        with database.allow_sync():
            signing = EnterpriseActorSigningModel.get_or_none(
                (EnterpriseActorSigningModel.enterprise_user_id == enterprise_user_id)
                & (EnterpriseActorSigningModel.actor_id == actor_id)
            )
            if not signing:
                raise ValueError("请先签约该演员后再加入购物车。")
            existing_item = EnterpriseCartItemModel.get_or_none(
                (EnterpriseCartItemModel.enterprise_user_id == enterprise_user_id)
                & (EnterpriseCartItemModel.actor_id == actor_id)
            )
            if existing_item and existing_item.status == "active":
                raise ValueError("该演员已在购物车中，请勿重复加入。")
        return self.ensure_cart_item_for_signing(
            enterprise_user_id=enterprise_user_id,
            actor_id=actor_id,
            signing_id=signing.id,
        )

    def remove_actor_from_cart(self, *, enterprise_user_id: int, actor_id: int) -> None:
        with database.allow_sync():
            item = EnterpriseCartItemModel.get_or_none(
                (EnterpriseCartItemModel.enterprise_user_id == enterprise_user_id)
                & (EnterpriseCartItemModel.actor_id == actor_id)
                & (EnterpriseCartItemModel.status == "active")
            )
            if not item:
                raise ValueError("购物车中未找到该演员。")
            item.status = "removed"
            item.updated_at = _utcnow()
            item.save()

    def list_cart_items(self, *, enterprise_user_id: int) -> list[dict[str, Any]]:
        with database.allow_sync():
            items = list(
                EnterpriseCartItemModel.select(EnterpriseCartItemModel, ActorModel)
                .join(ActorModel)
                .where(
                    (EnterpriseCartItemModel.enterprise_user_id == enterprise_user_id)
                    & (EnterpriseCartItemModel.status == "active")
                )
                .order_by(EnterpriseCartItemModel.created_at.desc())
            )
            return [self._serialize_cart_item(item) for item in items]

    # -------------------------
    # Orders
    # -------------------------
    def preview_order(
        self,
        *,
        enterprise_user_id: int,
        actor_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        with database.allow_sync():
            items = self._load_active_cart_items_sync(enterprise_user_id=enterprise_user_id, actor_ids=actor_ids)
            config = self._get_or_create_ops_config_sync()
            breakdown = self._build_order_breakdown(items=items, fee_rate_bps=int(config.fee_rate_bps))
            return {
                "currency": "CNY",
                "fee_rate_bps": int(config.fee_rate_bps),
                "actor_total_amount": breakdown["actor_total_amount"],
                "platform_fee_amount": breakdown["platform_fee_amount"],
                "payable_total_amount": breakdown["payable_total_amount"],
                "items": breakdown["items"],
            }

    def create_order(
        self,
        *,
        enterprise_user_id: int,
        actor_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        with database.allow_sync():
            with database.atomic():
                items = self._load_active_cart_items_sync(enterprise_user_id=enterprise_user_id, actor_ids=actor_ids)
                config = self._get_or_create_ops_config_sync()
                breakdown = self._build_order_breakdown(items=items, fee_rate_bps=int(config.fee_rate_bps))
                now = _utcnow()
                order_no = _gen_no("AO")
                order = EnterpriseOrderModel.create(
                    enterprise_user_id=enterprise_user_id,
                    order_no=order_no,
                    status=ORDER_STATUS_PENDING_PAYMENT,
                    currency="CNY",
                    actor_total_amount=breakdown["actor_total_amount"],
                    platform_fee_rate_bps=int(config.fee_rate_bps),
                    platform_fee_amount=breakdown["platform_fee_amount"],
                    payable_total_amount=breakdown["payable_total_amount"],
                    paid_total_amount=0,
                    refunded_total_amount=0,
                    settlement_status=SETTLEMENT_STATUS_PENDING,
                    settled_total_amount=0,
                    order_snapshot=self._json_safe(
                        {
                            "source": "enterprise_cart",
                            "rule_snapshot": self._serialize_ops_config(config),
                            "items": breakdown["items"],
                        }
                    ),
                    created_at=now,
                    updated_at=now,
                )

                line_map = {int(line["cart_item_id"]): line for line in breakdown["items"]}
                for cart_item in items:
                    line = line_map[int(cart_item.id)]
                    EnterpriseOrderActorItemModel.create(
                        order_id=order.id,
                        enterprise_user_id=enterprise_user_id,
                        actor_id=cart_item.actor_id,
                        cart_item_id=cart_item.id,
                        actor_quote_amount=int(line["actor_quote_amount"]),
                        platform_fee_amount=int(line["platform_fee_amount"]),
                        line_total_amount=int(line["line_total_amount"]),
                        settled_amount=0,
                        refunded_amount=0,
                        item_status=ORDER_ITEM_STATUS_PENDING,
                        actor_receivable_amount=int(line["actor_quote_amount"]),
                        actor_release_at=None,
                        quote_snapshot=self._json_safe(
                            {
                                **(cart_item.quote_snapshot or {}),
                                "actor_refunded_amount": 0,
                                "line_total_amount": int(line["line_total_amount"]),
                                "platform_fee_amount": int(line["platform_fee_amount"]),
                            }
                        ),
                        created_at=now,
                        updated_at=now,
                    )
                    cart_item.status = "converted"
                    cart_item.updated_at = now
                    cart_item.save()

                self._audit(
                    action="order_created",
                    enterprise_user_id=enterprise_user_id,
                    order_id=order.id,
                    operator_user_id=enterprise_user_id,
                    detail={
                        "order_no": order_no,
                        "payable_total_amount": int(order.payable_total_amount),
                        "item_count": len(items),
                    },
                )
                return self._serialize_order(order, include_children=True)

    def list_enterprise_orders(
        self,
        *,
        enterprise_user_id: int,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with database.allow_sync():
            orders = list(
                EnterpriseOrderModel.select()
                .where(EnterpriseOrderModel.enterprise_user_id == enterprise_user_id)
                .order_by(EnterpriseOrderModel.created_at.desc())
                .limit(max(1, min(int(limit), 200)))
            )
            return [self._serialize_order(order, include_children=False) for order in orders]

    def list_admin_orders(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with database.allow_sync():
            orders = list(
                EnterpriseOrderModel.select(EnterpriseOrderModel, UserModel)
                .join(UserModel, on=(EnterpriseOrderModel.enterprise_user == UserModel.id))
                .order_by(EnterpriseOrderModel.created_at.desc())
                .limit(max(1, min(int(limit), 500)))
            )
            return [self._serialize_order(order, include_children=False, include_enterprise=True) for order in orders]

    def get_order_for_enterprise(self, *, enterprise_user_id: int, order_no: str) -> dict[str, Any]:
        with database.allow_sync():
            order = EnterpriseOrderModel.get_or_none(
                (EnterpriseOrderModel.order_no == order_no)
                & (EnterpriseOrderModel.enterprise_user_id == enterprise_user_id)
            )
            if not order:
                raise ValueError("订单不存在。")
            return self._serialize_order(order, include_children=True)

    def get_order_for_admin(self, *, order_no: str) -> dict[str, Any]:
        with database.allow_sync():
            order = EnterpriseOrderModel.get_or_none(EnterpriseOrderModel.order_no == order_no)
            if not order:
                raise ValueError("订单不存在。")
            return self._serialize_order(order, include_children=True, include_enterprise=True)

    def create_payment(
        self,
        *,
        enterprise_user_id: int,
        order_no: str,
        channel: PaymentChannel,
    ) -> dict[str, Any]:
        normalized_channel = self._normalize_channel(channel)
        with database.allow_sync():
            with database.atomic():
                order = EnterpriseOrderModel.get_or_none(
                    (EnterpriseOrderModel.order_no == order_no)
                    & (EnterpriseOrderModel.enterprise_user_id == enterprise_user_id)
                )
                if not order:
                    raise ValueError("订单不存在。")
                if order.status not in {ORDER_STATUS_PENDING_PAYMENT, ORDER_STATUS_PAYMENT_FAILED}:
                    raise ValueError("当前订单状态不允许发起支付。")
                if int(order.payable_total_amount or 0) <= 0:
                    raise ValueError("订单金额异常。")

                config = self._get_or_create_ops_config_sync()
                if normalized_channel == "wechat" and not config.allow_wechat:
                    raise ValueError("当前未开启微信支付。")
                if normalized_channel == "alipay" and not config.allow_alipay:
                    raise ValueError("当前未开启支付宝支付。")

                out_trade_no = _gen_no("PT")
                payment = PaymentTransactionModel.create(
                    enterprise_user_id=enterprise_user_id,
                    order_id=order.id,
                    channel=normalized_channel,
                    out_trade_no=out_trade_no,
                    amount=int(order.payable_total_amount),
                    status=PAYMENT_STATUS_INITIATED,
                    request_payload=self._json_safe(
                        {
                            "order_no": order.order_no,
                            "amount": int(order.payable_total_amount),
                            "channel": normalized_channel,
                        }
                    ),
                    response_payload=self._json_safe({}),
                    notify_payload=self._json_safe({}),
                    created_at=_utcnow(),
                    updated_at=_utcnow(),
                )

                gateway_result = self.gateway.initiate_payment(
                    channel=normalized_channel,
                    out_trade_no=out_trade_no,
                    amount=int(order.payable_total_amount),
                    order_no=order.order_no,
                )
                payment.response_payload = self._json_safe(dict(gateway_result or {}))
                payment.channel_trade_no = gateway_result.get("channel_trade_no")
                payment.updated_at = _utcnow()

                if gateway_result.get("status") == PAYMENT_STATUS_PAID:
                    paid_at = _utcnow()
                    payment.status = PAYMENT_STATUS_PAID
                    payment.paid_at = paid_at
                    self._mark_order_paid_sync(
                        order=order,
                        config=config,
                        paid_at=paid_at,
                    )
                elif gateway_result.get("status") == PAYMENT_STATUS_FAILED:
                    payment.status = PAYMENT_STATUS_FAILED
                    order.status = ORDER_STATUS_PAYMENT_FAILED
                    order.updated_at = _utcnow()
                    order.save()
                else:
                    payment.status = PAYMENT_STATUS_INITIATED

                payment.save()
                self._audit(
                    action="payment_created",
                    enterprise_user_id=enterprise_user_id,
                    order_id=order.id,
                    payment_id=payment.id,
                    operator_user_id=enterprise_user_id,
                    detail={
                        "channel": normalized_channel,
                        "out_trade_no": out_trade_no,
                        "status": payment.status,
                    },
                )
                return self._serialize_payment(payment)

    def list_order_payments_for_enterprise(self, *, enterprise_user_id: int, order_no: str) -> list[dict[str, Any]]:
        with database.allow_sync():
            order = EnterpriseOrderModel.get_or_none(
                (EnterpriseOrderModel.order_no == order_no)
                & (EnterpriseOrderModel.enterprise_user_id == enterprise_user_id)
            )
            if not order:
                raise ValueError("订单不存在。")
            payments = list(
                PaymentTransactionModel.select()
                .where(PaymentTransactionModel.order_id == order.id)
                .order_by(PaymentTransactionModel.created_at.desc())
            )
            return [self._serialize_payment(payment) for payment in payments]

    def accept_order(
        self,
        *,
        enterprise_user_id: int,
        order_no: str,
    ) -> dict[str, Any]:
        with database.allow_sync():
            with database.atomic():
                order = EnterpriseOrderModel.get_or_none(
                    (EnterpriseOrderModel.order_no == order_no)
                    & (EnterpriseOrderModel.enterprise_user_id == enterprise_user_id)
                )
                if not order:
                    raise ValueError("订单不存在。")
                if order.status not in {
                    ORDER_STATUS_PAID,
                    ORDER_STATUS_PARTIALLY_REFUNDED,
                    ORDER_STATUS_SETTLED,
                }:
                    raise ValueError("当前订单状态不支持验收。")
                if not order.payment_succeeded_at:
                    raise ValueError("订单尚未支付成功。")

                config = self._get_or_create_ops_config_sync()
                now = _utcnow()
                max_deadline = self._calc_forced_settlement_deadline(order.payment_succeeded_at, config)
                release_at = min(
                    now + timedelta(hours=int(config.dispute_protect_hours)),
                    max_deadline,
                )
                order.accepted_at = now
                order.release_at = release_at
                order.updated_at = now
                order.save()

                (
                    EnterpriseOrderActorItemModel.update(
                        actor_release_at=release_at,
                        updated_at=now,
                    )
                    .where(
                        (EnterpriseOrderActorItemModel.order_id == order.id)
                        & (EnterpriseOrderActorItemModel.item_status.in_([ORDER_ITEM_STATUS_PAID, ORDER_ITEM_STATUS_PARTIALLY_REFUNDED]))
                    )
                    .execute()
                )
                self._audit(
                    action="order_accepted",
                    enterprise_user_id=enterprise_user_id,
                    order_id=order.id,
                    operator_user_id=enterprise_user_id,
                    detail={"release_at": release_at.isoformat()},
                )
                return self._serialize_order(order, include_children=True)

    # -------------------------
    # Refunds
    # -------------------------
    def list_refunds(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with database.allow_sync():
            refunds = list(
                RefundRecordModel.select()
                .order_by(RefundRecordModel.created_at.desc())
                .limit(max(1, min(int(limit), 500)))
            )
            return [self._serialize_refund(refund) for refund in refunds]

    def get_refund(self, *, out_refund_no: str) -> dict[str, Any]:
        with database.allow_sync():
            refund = RefundRecordModel.get_or_none(RefundRecordModel.out_refund_no == out_refund_no)
            if not refund:
                raise ValueError("退款单不存在。")
            return self._serialize_refund(refund)

    def create_refund_request(
        self,
        *,
        operator_user_id: int,
        order_no: str,
        refund_amount: int,
        reason: str,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        amount = int(refund_amount or 0)
        if amount <= 0:
            raise ValueError("退款金额必须大于 0。")
        reason_text = (reason or "").strip() or "运营发起退款"

        with database.allow_sync():
            with database.atomic():
                order = EnterpriseOrderModel.get_or_none(EnterpriseOrderModel.order_no == order_no)
                if not order:
                    raise ValueError("订单不存在。")
                if order.status not in {
                    ORDER_STATUS_PAID,
                    ORDER_STATUS_PARTIALLY_REFUNDED,
                    ORDER_STATUS_SETTLED,
                }:
                    raise ValueError("当前订单状态不允许退款。")

                paid_total = int(order.paid_total_amount or 0)
                refunded_total = int(order.refunded_total_amount or 0)
                order_remaining = max(0, paid_total - refunded_total)
                if order_remaining <= 0:
                    raise ValueError("订单已无可退金额。")

                actor_item: EnterpriseOrderActorItemModel | None = None
                if actor_id is not None:
                    actor_item = EnterpriseOrderActorItemModel.get_or_none(
                        (EnterpriseOrderActorItemModel.order_id == order.id)
                        & (EnterpriseOrderActorItemModel.actor_id == actor_id)
                    )
                    if not actor_item:
                        raise ValueError("订单中不存在该演员条目。")
                    item_remaining = self._item_refundable_remaining(actor_item)
                    if item_remaining <= 0:
                        raise ValueError("该演员条目已无可退金额。")
                    order_remaining = min(order_remaining, item_remaining)

                if amount > order_remaining:
                    raise ValueError(f"退款金额超过可退额度，当前最多可退 {order_remaining}。")

                payment = (
                    PaymentTransactionModel.select()
                    .where(
                        (PaymentTransactionModel.order_id == order.id)
                        & (PaymentTransactionModel.status == PAYMENT_STATUS_PAID)
                    )
                    .order_by(PaymentTransactionModel.created_at.desc())
                    .first()
                )
                if not payment:
                    raise ValueError("未找到成功支付记录，无法发起退款。")

                out_refund_no = _gen_no("RF")
                refund = RefundRecordModel.create(
                    enterprise_user_id=order.enterprise_user_id,
                    order_id=order.id,
                    actor_item_id=actor_item.id if actor_item else None,
                    payment_id=payment.id,
                    channel=payment.channel,
                    out_refund_no=out_refund_no,
                    refund_amount=amount,
                    status=REFUND_STATUS_PENDING,
                    reason=reason_text,
                    operator_user_id=operator_user_id,
                    request_payload=self._json_safe(
                        {
                            "order_no": order.order_no,
                            "actor_id": actor_id,
                            "refund_amount": amount,
                            "reason": reason_text,
                        }
                    ),
                    response_payload=self._json_safe({}),
                    notify_payload=self._json_safe({}),
                    created_at=_utcnow(),
                    updated_at=_utcnow(),
                )
                self._audit(
                    action="refund_requested",
                    enterprise_user_id=order.enterprise_user_id,
                    order_id=order.id,
                    payment_id=payment.id,
                    refund_id=refund.id,
                    operator_user_id=operator_user_id,
                    detail={"out_refund_no": out_refund_no, "refund_amount": amount, "actor_id": actor_id},
                )
                return self._serialize_refund(refund)

    def approve_refund(
        self,
        *,
        reviewed_by_user_id: int,
        out_refund_no: str,
    ) -> dict[str, Any]:
        with database.allow_sync():
            with database.atomic():
                refund = RefundRecordModel.get_or_none(RefundRecordModel.out_refund_no == out_refund_no)
                if not refund:
                    raise ValueError("退款单不存在。")
                if refund.status != REFUND_STATUS_PENDING:
                    raise ValueError("当前退款单状态不可审核。")

                order = EnterpriseOrderModel.get_by_id(refund.order_id)
                payment = PaymentTransactionModel.get_by_id(refund.payment_id)
                actor_item = (
                    EnterpriseOrderActorItemModel.get_or_none(EnterpriseOrderActorItemModel.id == refund.actor_item_id)
                    if refund.actor_item_id
                    else None
                )
                if actor_item is not None and actor_item.order_id != order.id:
                    raise ValueError("退款单数据异常。")

                gateway_result = self.gateway.refund(
                    channel=self._normalize_channel(refund.channel),
                    out_trade_no=payment.out_trade_no,
                    out_refund_no=refund.out_refund_no,
                    amount=int(refund.refund_amount),
                    reason=refund.reason,
                )
                refund.response_payload = self._json_safe(dict(gateway_result or {}))
                refund.reviewed_by_id = reviewed_by_user_id
                refund.reviewed_at = _utcnow()
                refund.updated_at = _utcnow()
                refund.channel_refund_no = gateway_result.get("channel_refund_no")

                if gateway_result.get("status") == REFUND_STATUS_SUCCEEDED:
                    refund.status = REFUND_STATUS_SUCCEEDED
                    self._apply_refund_to_order_sync(
                        order=order,
                        actor_item=actor_item,
                        refund_amount=int(refund.refund_amount),
                    )
                else:
                    refund.status = REFUND_STATUS_FAILED

                refund.save()
                self._audit(
                    action="refund_reviewed",
                    enterprise_user_id=order.enterprise_user_id,
                    order_id=order.id,
                    payment_id=payment.id,
                    refund_id=refund.id,
                    operator_user_id=reviewed_by_user_id,
                    detail={
                        "out_refund_no": refund.out_refund_no,
                        "status": refund.status,
                        "refund_amount": int(refund.refund_amount),
                    },
                )
                return self._serialize_refund(refund)

    # -------------------------
    # Settlement
    # -------------------------
    def run_due_settlements(
        self,
        *,
        operator_user_id: int,
        limit: int = 200,
    ) -> dict[str, Any]:
        with database.allow_sync():
            with database.atomic():
                now = _utcnow()
                due_items = list(
                    EnterpriseOrderActorItemModel.select(EnterpriseOrderActorItemModel, EnterpriseOrderModel)
                    .join(EnterpriseOrderModel)
                    .where(
                        (EnterpriseOrderActorItemModel.actor_release_at.is_null(False))
                        & (EnterpriseOrderActorItemModel.actor_release_at <= now)
                        & (
                            EnterpriseOrderActorItemModel.item_status.in_(
                                [
                                    ORDER_ITEM_STATUS_PAID,
                                    ORDER_ITEM_STATUS_PARTIALLY_REFUNDED,
                                ]
                            )
                        )
                        & (
                            EnterpriseOrderModel.status.in_(
                                [
                                    ORDER_STATUS_PAID,
                                    ORDER_STATUS_PARTIALLY_REFUNDED,
                                    ORDER_STATUS_SETTLED,
                                ]
                            )
                        )
                    )
                    .order_by(EnterpriseOrderActorItemModel.actor_release_at.asc(), EnterpriseOrderActorItemModel.id.asc())
                    .limit(max(1, min(int(limit), 1000)))
                )

                if not due_items:
                    return {
                        "processed_count": 0,
                        "settled_count": 0,
                        "failed_count": 0,
                        "items": [],
                    }

                processed = 0
                settled_count = 0
                failed_count = 0
                result_items: list[dict[str, Any]] = []
                touched_order_ids: set[int] = set()

                for item in due_items:
                    processed += 1
                    order = item.order
                    touched_order_ids.add(order.id)
                    actor_due = self._item_actor_settle_remaining(item)
                    if actor_due <= 0:
                        self._refresh_item_status(item)
                        item.updated_at = _utcnow()
                        item.save()
                        result_items.append(
                            {
                                "order_no": order.order_no,
                                "actor_id": item.actor_id,
                                "settled_amount": 0,
                                "status": "skipped",
                                "reason": "actor due amount is zero",
                            }
                        )
                        continue

                    latest_payment = (
                        PaymentTransactionModel.select()
                        .where(
                            (PaymentTransactionModel.order_id == order.id)
                            & (PaymentTransactionModel.status == PAYMENT_STATUS_PAID)
                        )
                        .order_by(PaymentTransactionModel.created_at.desc())
                        .first()
                    )
                    channel = latest_payment.channel if latest_payment else "wechat"
                    out_settle_no = _gen_no("ST")

                    settlement = SettlementRecordModel.create(
                        order_id=order.id,
                        actor_item_id=item.id,
                        actor_id=item.actor_id,
                        channel=channel,
                        out_settle_no=out_settle_no,
                        settle_amount=actor_due,
                        platform_fee_amount=int(item.platform_fee_amount or 0),
                        status=SETTLE_STATUS_PENDING,
                        requested_at=_utcnow(),
                        request_payload=self._json_safe(
                            {
                                "order_no": order.order_no,
                                "actor_id": item.actor_id,
                                "settle_amount": actor_due,
                            }
                        ),
                        response_payload=self._json_safe({}),
                        created_at=_utcnow(),
                        updated_at=_utcnow(),
                    )

                    gateway_result = self.gateway.settle(
                        channel=self._normalize_channel(channel),
                        out_settle_no=out_settle_no,
                        actor_id=item.actor_id,
                        amount=actor_due,
                        order_no=order.order_no,
                    )
                    settlement.response_payload = self._json_safe(dict(gateway_result or {}))
                    settlement.channel_settle_no = gateway_result.get("channel_settle_no")
                    settlement.updated_at = _utcnow()

                    if gateway_result.get("status") == SETTLE_STATUS_SETTLED:
                        settlement.status = SETTLE_STATUS_SETTLED
                        settlement.settled_at = _utcnow()
                        item.settled_amount = int(item.settled_amount or 0) + actor_due
                        self._refresh_item_status(item)
                        item.updated_at = _utcnow()
                        item.save()
                        order.settled_total_amount = int(order.settled_total_amount or 0) + actor_due
                        settled_count += 1
                        result_items.append(
                            {
                                "order_no": order.order_no,
                                "actor_id": item.actor_id,
                                "settled_amount": actor_due,
                                "status": "settled",
                            }
                        )
                    else:
                        settlement.status = SETTLE_STATUS_FAILED
                        failed_count += 1
                        result_items.append(
                            {
                                "order_no": order.order_no,
                                "actor_id": item.actor_id,
                                "settled_amount": 0,
                                "status": "failed",
                            }
                        )
                    settlement.save()
                    self._audit(
                        action="settlement_processed",
                        enterprise_user_id=order.enterprise_user_id,
                        order_id=order.id,
                        actor_item_id=item.id,
                        settlement_id=settlement.id,
                        operator_user_id=operator_user_id,
                        detail={
                            "out_settle_no": out_settle_no,
                            "status": settlement.status,
                            "settle_amount": actor_due,
                        },
                    )

                for order_id in touched_order_ids:
                    order = EnterpriseOrderModel.get_by_id(order_id)
                    self._recompute_order_settlement_sync(order)
                    self._recompute_order_status_sync(order)
                    order.updated_at = _utcnow()
                    order.save()

                return {
                    "processed_count": processed,
                    "settled_count": settled_count,
                    "failed_count": failed_count,
                    "items": result_items,
                }

    # -------------------------
    # Actor wallet & withdraw
    # -------------------------
    def get_actor_wallet_summary(self, *, actor_id: int) -> dict[str, Any]:
        with database.allow_sync():
            return self._build_actor_wallet_summary_sync(actor_id=actor_id)

    def list_actor_withdrawals(self, *, actor_id: int, limit: int = 50) -> list[dict[str, Any]]:
        with database.allow_sync():
            rows = list(
                ActorWithdrawRecordModel.select()
                .where(ActorWithdrawRecordModel.actor_id == actor_id)
                .order_by(ActorWithdrawRecordModel.created_at.desc())
                .limit(max(1, min(int(limit), 200)))
            )
            return [self._serialize_actor_withdraw(row) for row in rows]

    def list_admin_withdrawals(self, *, limit: int = 100, status: str | None = None) -> list[dict[str, Any]]:
        status_text = str(status or "").strip().lower()
        if status_text and status_text not in WITHDRAW_STATUSES:
            raise ValueError("提现状态非法。")
        with database.allow_sync():
            query = (
                ActorWithdrawRecordModel.select(ActorWithdrawRecordModel, ActorModel, UserModel)
                .join(ActorModel, on=(ActorWithdrawRecordModel.actor == ActorModel.id))
                .switch(ActorWithdrawRecordModel)
                .join(UserModel, on=(ActorWithdrawRecordModel.actor_user == UserModel.id))
            )
            if status_text:
                query = query.where(ActorWithdrawRecordModel.status == status_text)
            rows = list(
                query.order_by(ActorWithdrawRecordModel.created_at.desc()).limit(
                    max(1, min(int(limit), 500))
                )
            )
            return [self._serialize_actor_withdraw(row, include_actor_context=True) for row in rows]

    def get_admin_withdrawal(self, *, out_withdraw_no: str) -> dict[str, Any]:
        with database.allow_sync():
            row = (
                ActorWithdrawRecordModel.select(ActorWithdrawRecordModel, ActorModel, UserModel)
                .join(ActorModel, on=(ActorWithdrawRecordModel.actor == ActorModel.id))
                .switch(ActorWithdrawRecordModel)
                .join(UserModel, on=(ActorWithdrawRecordModel.actor_user == UserModel.id))
                .where(ActorWithdrawRecordModel.out_withdraw_no == out_withdraw_no)
                .first()
            )
            if not row:
                raise ValueError("提现单不存在。")
            return self._serialize_actor_withdraw(row, include_actor_context=True)

    def review_actor_withdraw(
        self,
        *,
        reviewed_by_user_id: int,
        out_withdraw_no: str,
        action: str,
        failure_reason: str = "",
    ) -> dict[str, Any]:
        action_text = str(action or "").strip().lower()
        if action_text not in WITHDRAW_REVIEW_ACTIONS:
            raise ValueError("审核动作非法，仅支持 approve、reject、fail。")
        reason_text = str(failure_reason or "").strip()

        with database.allow_sync():
            with database.atomic():
                row = ActorWithdrawRecordModel.get_or_none(
                    ActorWithdrawRecordModel.out_withdraw_no == out_withdraw_no
                )
                if not row:
                    raise ValueError("提现单不存在。")
                if row.status not in {WITHDRAW_STATUS_PENDING, WITHDRAW_STATUS_PROCESSING}:
                    raise ValueError("当前提现单状态不可审核。")

                now = _utcnow()
                if action_text == "approve":
                    self._lock_actor_row_for_update_sync(actor_id=int(row.actor_id))
                    available_excluding_self = self._calc_actor_available_amount_sync(
                        actor_id=int(row.actor_id),
                        exclude_withdraw_id=int(row.id),
                    )
                    if int(row.amount or 0) > available_excluding_self:
                        raise ValueError(
                            f"当前可核准金额不足，最多可核准 {available_excluding_self}。"
                        )
                    row.status = WITHDRAW_STATUS_SUCCEEDED
                    row.failure_reason = ""
                    row.processed_at = now
                    if not row.channel_withdraw_no:
                        row.channel_withdraw_no = f"{str(row.channel).upper()}_WITHDRAW_{uuid.uuid4().hex[:16]}"
                elif action_text == "reject":
                    row.status = WITHDRAW_STATUS_REJECTED
                    row.failure_reason = reason_text or "运营驳回提现申请。"
                    row.processed_at = now
                else:
                    row.status = WITHDRAW_STATUS_FAILED
                    row.failure_reason = reason_text or "运营处理失败，请重试。"
                    row.processed_at = now

                response_payload = dict(row.response_payload or {})
                response_payload["review"] = self._json_safe(
                    {
                        "action": action_text,
                        "reviewed_by": reviewed_by_user_id,
                        "reviewed_at": now,
                        "failure_reason": row.failure_reason,
                        "status": row.status,
                    }
                )
                row.response_payload = self._json_safe(response_payload)
                row.updated_at = now
                row.save()

                self._audit(
                    action=f"actor_withdraw_{action_text}",
                    operator_user_id=reviewed_by_user_id,
                    detail={
                        "actor_id": int(row.actor_id),
                        "out_withdraw_no": row.out_withdraw_no,
                        "status": row.status,
                        "amount": int(row.amount or 0),
                        "failure_reason": row.failure_reason,
                    },
                )

                row = (
                    ActorWithdrawRecordModel.select(ActorWithdrawRecordModel, ActorModel, UserModel)
                    .join(ActorModel, on=(ActorWithdrawRecordModel.actor == ActorModel.id))
                    .switch(ActorWithdrawRecordModel)
                    .join(UserModel, on=(ActorWithdrawRecordModel.actor_user == UserModel.id))
                    .where(ActorWithdrawRecordModel.id == row.id)
                    .first()
                )
                return self._serialize_actor_withdraw(row, include_actor_context=True)

    def create_actor_withdraw_request(
        self,
        *,
        actor_id: int,
        actor_user_id: int,
        amount: int,
        channel: PaymentChannel,
        account_name: str,
        account_no: str,
        remark: str = "",
    ) -> dict[str, Any]:
        normalized_channel = self._normalize_channel(channel)
        withdraw_amount = int(amount or 0)
        if withdraw_amount <= 0:
            raise ValueError("提现金额必须大于 0。")

        account_name_text = str(account_name or "").strip()
        account_no_text = str(account_no or "").strip()
        remark_text = str(remark or "").strip()
        if not account_name_text:
            raise ValueError("收款账户姓名不能为空。")
        if not account_no_text:
            raise ValueError("收款账号不能为空。")

        with database.allow_sync():
            with database.atomic():
                self._lock_actor_row_for_update_sync(actor_id=actor_id)
                summary = self._build_actor_wallet_summary_sync(actor_id=actor_id)
                available_amount = int(summary["available_amount"])
                if withdraw_amount > available_amount:
                    raise ValueError(f"可提现余额不足，当前最多可提现 {available_amount}。")

                now = _utcnow()
                out_withdraw_no = _gen_no("WD")
                status = WITHDRAW_STATUS_PENDING
                processed_at: datetime | None = None
                channel_withdraw_no: str | None = None
                failure_reason = ""
                response_payload: dict[str, Any] = {}

                if bool(settings.PAYMENT_USE_MOCK) and bool(settings.PAYMENT_MOCK_CHANNEL_AUTO_SUCCESS):
                    status = WITHDRAW_STATUS_SUCCEEDED
                    processed_at = now
                    channel_withdraw_no = f"{normalized_channel.upper()}_WITHDRAW_{uuid.uuid4().hex[:16]}"
                    response_payload = {
                        "status": status,
                        "channel_withdraw_no": channel_withdraw_no,
                        "mock": True,
                    }
                elif bool(settings.PAYMENT_USE_MOCK):
                    response_payload = {
                        "status": status,
                        "mock": True,
                        "message": "Mock 手动模式：提现申请已创建，等待处理。",
                    }
                else:
                    response_payload = {
                        "status": status,
                        "message": "提现申请已提交，等待运营处理。",
                    }

                record = ActorWithdrawRecordModel.create(
                    actor_id=actor_id,
                    actor_user_id=actor_user_id,
                    channel=normalized_channel,
                    out_withdraw_no=out_withdraw_no,
                    channel_withdraw_no=channel_withdraw_no,
                    amount=withdraw_amount,
                    status=status,
                    account_name=account_name_text,
                    account_no=account_no_text,
                    account_snapshot=self._json_safe(
                        {
                            "account_name": account_name_text,
                            "account_no_masked": self._mask_account_no(account_no_text),
                            "channel": normalized_channel,
                        }
                    ),
                    remark=remark_text,
                    requested_at=now,
                    processed_at=processed_at,
                    failure_reason=failure_reason,
                    request_payload=self._json_safe(
                        {
                            "amount": withdraw_amount,
                            "channel": normalized_channel,
                            "account_name": account_name_text,
                            "account_no": account_no_text,
                            "remark": remark_text,
                        }
                    ),
                    response_payload=self._json_safe(response_payload),
                    created_at=now,
                    updated_at=now,
                )
                self._audit(
                    action="actor_withdraw_requested",
                    actor_item_id=None,
                    operator_user_id=actor_user_id,
                    detail={
                        "actor_id": actor_id,
                        "out_withdraw_no": out_withdraw_no,
                        "amount": withdraw_amount,
                        "status": status,
                        "channel": normalized_channel,
                    },
                )
                if status == WITHDRAW_STATUS_SUCCEEDED:
                    self._audit(
                        action="actor_withdraw_succeeded",
                        actor_item_id=None,
                        operator_user_id=actor_user_id,
                        detail={
                            "actor_id": actor_id,
                            "out_withdraw_no": out_withdraw_no,
                            "amount": withdraw_amount,
                            "channel_withdraw_no": channel_withdraw_no,
                            "channel": normalized_channel,
                        },
                    )
                return self._serialize_actor_withdraw(record)

    # -------------------------
    # Internal helpers
    # -------------------------
    def _normalize_channel(self, channel: str) -> PaymentChannel:
        normalized = str(channel or "").strip().lower()
        if normalized not in PAYMENT_CHANNELS:
            raise ValueError("支付通道非法，仅支持 wechat 和 alipay。")
        return normalized  # type: ignore[return-value]

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(item) for item in value]
        return value

    def _get_or_create_ops_config_sync(self) -> PaymentOpsConfigModel:
        config = (
            PaymentOpsConfigModel.select()
            .order_by(PaymentOpsConfigModel.id.asc())
            .first()
        )
        if config:
            return config
        now = _utcnow()
        return PaymentOpsConfigModel.create(
            fee_rate_bps=int(settings.PAYMENT_FEE_RATE_BPS),
            auto_accept_hours=int(settings.PAYMENT_AUTO_ACCEPT_HOURS),
            dispute_protect_hours=int(settings.PAYMENT_DISPUTE_PROTECT_HOURS),
            max_hold_hours=int(settings.PAYMENT_MAX_HOLD_HOURS),
            settlement_safety_buffer_hours=int(settings.PAYMENT_SETTLEMENT_SAFETY_BUFFER_HOURS),
            allow_wechat=("wechat" in settings.PAYMENT_ALLOWED_CHANNELS),
            allow_alipay=("alipay" in settings.PAYMENT_ALLOWED_CHANNELS),
            created_at=now,
            updated_at=now,
        )

    def _serialize_ops_config(self, config: PaymentOpsConfigModel) -> dict[str, Any]:
        return {
            "use_mock": bool(settings.PAYMENT_USE_MOCK),
            "mock_channel_auto_success": bool(settings.PAYMENT_MOCK_CHANNEL_AUTO_SUCCESS),
            "fee_rate_bps": int(config.fee_rate_bps),
            "auto_accept_hours": int(config.auto_accept_hours),
            "dispute_protect_hours": int(config.dispute_protect_hours),
            "max_hold_hours": int(config.max_hold_hours),
            "settlement_safety_buffer_hours": int(config.settlement_safety_buffer_hours),
            "allow_wechat": bool(config.allow_wechat),
            "allow_alipay": bool(config.allow_alipay),
            "updated_by": int(config.updated_by_id) if config.updated_by_id else None,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

    def _sum_withdraw_amount_sync(
        self,
        *,
        actor_id: int,
        statuses: set[str],
        exclude_withdraw_id: int | None = None,
    ) -> int:
        if not statuses:
            return 0
        query = ActorWithdrawRecordModel.select(
            peewee.fn.COALESCE(peewee.fn.SUM(ActorWithdrawRecordModel.amount), 0)
        ).where(
            (ActorWithdrawRecordModel.actor_id == actor_id)
            & (ActorWithdrawRecordModel.status.in_(tuple(statuses)))
        )
        if exclude_withdraw_id is not None:
            query = query.where(ActorWithdrawRecordModel.id != int(exclude_withdraw_id))
        value = query.scalar()
        return int(value or 0)

    def _calc_actor_net_settled_amount_sync(self, *, actor_id: int) -> int:
        # Net settled amount is derived from order item facts (settled minus post-settlement refund impacts),
        # which keeps withdrawable balance consistent with enterprise payment/refund lifecycle.
        items = list(
            EnterpriseOrderActorItemModel.select()
            .where(EnterpriseOrderActorItemModel.actor_id == actor_id)
        )
        total = 0
        for item in items:
            actor_refunded_amount = int((item.quote_snapshot or {}).get("actor_refunded_amount", 0) or 0)
            actor_due_after_refund = max(0, int(item.actor_quote_amount or 0) - actor_refunded_amount)
            item_settled_amount = max(0, int(item.settled_amount or 0))
            total += min(actor_due_after_refund, item_settled_amount)
        return int(total)

    def _calc_actor_available_amount_sync(
        self,
        *,
        actor_id: int,
        exclude_withdraw_id: int | None = None,
    ) -> int:
        total_settled_amount = self._calc_actor_net_settled_amount_sync(actor_id=actor_id)
        total_withdrawing_amount = self._sum_withdraw_amount_sync(
            actor_id=actor_id,
            statuses={WITHDRAW_STATUS_PENDING, WITHDRAW_STATUS_PROCESSING},
            exclude_withdraw_id=exclude_withdraw_id,
        )
        total_withdrawn_amount = self._sum_withdraw_amount_sync(
            actor_id=actor_id,
            statuses={WITHDRAW_STATUS_SUCCEEDED},
            exclude_withdraw_id=exclude_withdraw_id,
        )
        return max(0, total_settled_amount - total_withdrawing_amount - total_withdrawn_amount)

    def _build_actor_wallet_summary_sync(self, *, actor_id: int) -> dict[str, Any]:
        total_settled_amount = self._calc_actor_net_settled_amount_sync(actor_id=actor_id)
        total_withdrawing_amount = self._sum_withdraw_amount_sync(
            actor_id=actor_id,
            statuses={WITHDRAW_STATUS_PENDING, WITHDRAW_STATUS_PROCESSING},
        )
        total_withdrawn_amount = self._sum_withdraw_amount_sync(
            actor_id=actor_id,
            statuses={WITHDRAW_STATUS_SUCCEEDED},
        )
        total_failed_withdraw_amount = self._sum_withdraw_amount_sync(
            actor_id=actor_id,
            statuses={WITHDRAW_STATUS_FAILED, WITHDRAW_STATUS_REJECTED},
        )
        available_amount = self._calc_actor_available_amount_sync(actor_id=actor_id)
        return {
            "actor_id": actor_id,
            "currency": "CNY",
            "available_amount": available_amount,
            "total_settled_amount": total_settled_amount,
            "total_withdrawing_amount": total_withdrawing_amount,
            "total_withdrawn_amount": total_withdrawn_amount,
            "total_failed_withdraw_amount": total_failed_withdraw_amount,
            "updated_at": _utcnow(),
        }

    def _lock_actor_row_for_update_sync(self, *, actor_id: int) -> None:
        actor = (
            ActorModel.select()
            .where(ActorModel.id == actor_id)
            .for_update()
            .first()
        )
        if not actor:
            raise ValueError("演员不存在。")

    def _serialize_actor_withdraw(
        self,
        row: ActorWithdrawRecordModel,
        *,
        include_actor_context: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "withdraw_id": int(row.id),
            "actor_id": int(row.actor_id),
            "actor_user_id": int(row.actor_user_id),
            "channel": row.channel,
            "out_withdraw_no": row.out_withdraw_no,
            "channel_withdraw_no": row.channel_withdraw_no,
            "amount": int(row.amount or 0),
            "status": row.status,
            "account_name": row.account_name,
            "account_no_masked": self._mask_account_no(row.account_no),
            "remark": row.remark or "",
            "requested_at": row.requested_at,
            "processed_at": row.processed_at,
            "failure_reason": row.failure_reason or "",
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        if include_actor_context:
            actor = row.actor
            actor_user = row.actor_user
            payload["actor_name"] = actor.name if actor else ""
            payload["actor_external_id"] = actor.external_id if actor else ""
            payload["actor_user_display_name"] = actor_user.display_name if actor_user else ""
        return payload

    def _mask_account_no(self, account_no: str) -> str:
        value = str(account_no or "").strip()
        if not value:
            return ""
        if len(value) <= 4:
            return "*" * len(value)
        return f"{'*' * (len(value) - 4)}{value[-4:]}"

    def _build_quote_snapshot(self, *, actor: ActorModel) -> dict[str, Any]:
        return {
            "actor_id": int(actor.id),
            "actor_name": actor.name,
            "external_id": actor.external_id,
            "pricing_unit": str(actor.pricing_unit or "project"),
            "pricing_amount": int(actor.pricing_amount or 0),
            "snapshot_at": _utcnow().isoformat(),
        }

    def _serialize_cart_item(self, item: EnterpriseCartItemModel) -> dict[str, Any]:
        actor = item.actor
        return {
            "cart_item_id": int(item.id),
            "actor_id": int(item.actor_id),
            "actor_name": actor.name if actor else "",
            "actor_external_id": actor.external_id if actor else "",
            "actor_quote_amount": int(item.actor_quote_amount or 0),
            "pricing_unit": str((item.quote_snapshot or {}).get("pricing_unit") or "project"),
            "status": item.status,
            "signed_at": item.signing.signed_at if item.signing else None,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

    def _load_active_cart_items_sync(
        self,
        *,
        enterprise_user_id: int,
        actor_ids: list[int] | None = None,
    ) -> list[EnterpriseCartItemModel]:
        query = (
            EnterpriseCartItemModel.select(EnterpriseCartItemModel, ActorModel)
            .join(ActorModel)
            .where(
                (EnterpriseCartItemModel.enterprise_user_id == enterprise_user_id)
                & (EnterpriseCartItemModel.status == "active")
            )
            .order_by(EnterpriseCartItemModel.created_at.asc())
        )
        if actor_ids:
            ids = [int(v) for v in actor_ids if int(v) > 0]
            if ids:
                query = query.where(EnterpriseCartItemModel.actor_id.in_(ids))
            else:
                raise ValueError("下单演员列表为空。")
        items = list(query)
        if not items:
            raise ValueError("购物车为空，请先选择演员。")
        return items

    def _build_order_breakdown(
        self,
        *,
        items: list[EnterpriseCartItemModel],
        fee_rate_bps: int,
    ) -> dict[str, Any]:
        actor_total = sum(max(0, int(item.actor_quote_amount or 0)) for item in items)
        platform_fee_total = (actor_total * max(0, int(fee_rate_bps))) // 10000
        fees = self._distribute_fee(
            bases=[max(0, int(item.actor_quote_amount or 0)) for item in items],
            fee_total=platform_fee_total,
        )
        lines: list[dict[str, Any]] = []
        for item, fee in zip(items, fees):
            actor_amount = max(0, int(item.actor_quote_amount or 0))
            lines.append(
                {
                    "cart_item_id": int(item.id),
                    "actor_id": int(item.actor_id),
                    "actor_name": item.actor.name if item.actor else "",
                    "actor_external_id": item.actor.external_id if item.actor else "",
                    "actor_quote_amount": actor_amount,
                    "platform_fee_amount": int(fee),
                    "line_total_amount": actor_amount + int(fee),
                }
            )
        return {
            "actor_total_amount": actor_total,
            "platform_fee_amount": platform_fee_total,
            "payable_total_amount": actor_total + platform_fee_total,
            "items": lines,
        }

    def _distribute_fee(self, *, bases: list[int], fee_total: int) -> list[int]:
        if not bases:
            return []
        if fee_total <= 0:
            return [0 for _ in bases]
        total_base = sum(max(0, int(v)) for v in bases)
        if total_base <= 0:
            result = [0 for _ in bases]
            result[-1] = int(fee_total)
            return result

        allocated: list[int] = []
        consumed = 0
        for index, base in enumerate(bases):
            if index == len(bases) - 1:
                fee = int(fee_total - consumed)
            else:
                fee = (max(0, int(base)) * int(fee_total)) // int(total_base)
                consumed += fee
            allocated.append(fee)
        return allocated

    def _mark_order_paid_sync(
        self,
        *,
        order: EnterpriseOrderModel,
        config: PaymentOpsConfigModel,
        paid_at: datetime,
    ) -> None:
        auto_accept_at = paid_at + timedelta(hours=int(config.auto_accept_hours))
        max_deadline = self._calc_forced_settlement_deadline(paid_at, config)
        release_by_accept = auto_accept_at + timedelta(hours=int(config.dispute_protect_hours))
        release_at = min(release_by_accept, max_deadline)

        order.status = ORDER_STATUS_PAID
        order.paid_total_amount = int(order.payable_total_amount or 0)
        order.payment_succeeded_at = paid_at
        order.auto_accept_at = auto_accept_at
        order.release_at = release_at
        order.settlement_status = SETTLEMENT_STATUS_PENDING
        order.updated_at = _utcnow()
        order.save()

        now = _utcnow()
        (
            EnterpriseOrderActorItemModel.update(
                item_status=ORDER_ITEM_STATUS_PAID,
                actor_release_at=release_at,
                updated_at=now,
            )
            .where(EnterpriseOrderActorItemModel.order_id == order.id)
            .execute()
        )

    def _calc_forced_settlement_deadline(
        self,
        paid_at: datetime,
        config: PaymentOpsConfigModel,
    ) -> datetime:
        max_hold_hours = int(config.max_hold_hours or 0)
        buffer_hours = int(config.settlement_safety_buffer_hours or 0)
        safe_hours = max(1, max_hold_hours - buffer_hours)
        return paid_at + timedelta(hours=safe_hours)

    def _serialize_order_item(self, item: EnterpriseOrderActorItemModel) -> dict[str, Any]:
        quote_snapshot = item.quote_snapshot or {}
        actor_refunded_amount = int(quote_snapshot.get("actor_refunded_amount", 0) or 0)
        return {
            "order_item_id": int(item.id),
            "actor_id": int(item.actor_id),
            "actor_name": item.actor.name if item.actor else "",
            "actor_external_id": item.actor.external_id if item.actor else "",
            "actor_quote_amount": int(item.actor_quote_amount or 0),
            "platform_fee_amount": int(item.platform_fee_amount or 0),
            "line_total_amount": int(item.line_total_amount or 0),
            "refunded_amount": int(item.refunded_amount or 0),
            "settled_amount": int(item.settled_amount or 0),
            "actor_refunded_amount": actor_refunded_amount,
            "actor_settle_remaining_amount": self._item_actor_settle_remaining(item),
            "item_refundable_remaining_amount": self._item_refundable_remaining(item),
            "item_status": item.item_status,
            "actor_release_at": item.actor_release_at,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

    def _serialize_order(
        self,
        order: EnterpriseOrderModel,
        *,
        include_children: bool,
        include_enterprise: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "order_no": order.order_no,
            "status": order.status,
            "currency": order.currency,
            "actor_total_amount": int(order.actor_total_amount or 0),
            "platform_fee_rate_bps": int(order.platform_fee_rate_bps or 0),
            "platform_fee_amount": int(order.platform_fee_amount or 0),
            "payable_total_amount": int(order.payable_total_amount or 0),
            "paid_total_amount": int(order.paid_total_amount or 0),
            "refunded_total_amount": int(order.refunded_total_amount or 0),
            "refundable_remaining_amount": max(
                0,
                int(order.paid_total_amount or 0) - int(order.refunded_total_amount or 0),
            ),
            "settlement_status": order.settlement_status,
            "settled_total_amount": int(order.settled_total_amount or 0),
            "auto_accept_at": order.auto_accept_at,
            "release_at": order.release_at,
            "accepted_at": order.accepted_at,
            "payment_succeeded_at": order.payment_succeeded_at,
            "settled_at": order.settled_at,
            "closed_at": order.closed_at,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }
        if include_enterprise:
            enterprise = UserModel.get_or_none(UserModel.id == order.enterprise_user_id)
            payload["enterprise"] = {
                "enterprise_user_id": int(order.enterprise_user_id),
                "company_name": enterprise.display_name if enterprise else "",
                "username": enterprise.username if enterprise else "",
            }
        if include_children:
            items = list(
                EnterpriseOrderActorItemModel.select(EnterpriseOrderActorItemModel, ActorModel)
                .join(ActorModel)
                .where(EnterpriseOrderActorItemModel.order_id == order.id)
                .order_by(EnterpriseOrderActorItemModel.id.asc())
            )
            payments = list(
                PaymentTransactionModel.select()
                .where(PaymentTransactionModel.order_id == order.id)
                .order_by(PaymentTransactionModel.created_at.desc())
            )
            refunds = list(
                RefundRecordModel.select()
                .where(RefundRecordModel.order_id == order.id)
                .order_by(RefundRecordModel.created_at.desc())
            )
            settlements = list(
                SettlementRecordModel.select()
                .where(SettlementRecordModel.order_id == order.id)
                .order_by(SettlementRecordModel.created_at.desc())
            )
            payload["items"] = [self._serialize_order_item(item) for item in items]
            payload["payments"] = [self._serialize_payment(payment) for payment in payments]
            payload["refunds"] = [self._serialize_refund(refund) for refund in refunds]
            payload["settlements"] = [self._serialize_settlement(settlement) for settlement in settlements]
        return payload

    def _serialize_payment(self, payment: PaymentTransactionModel) -> dict[str, Any]:
        return {
            "payment_id": int(payment.id),
            "order_id": int(payment.order_id),
            "out_trade_no": payment.out_trade_no,
            "channel_trade_no": payment.channel_trade_no,
            "channel": payment.channel,
            "amount": int(payment.amount or 0),
            "status": payment.status,
            "paid_at": payment.paid_at,
            "expires_at": payment.expires_at,
            "pay_payload": (payment.response_payload or {}).get("pay_payload"),
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
        }

    def _serialize_refund(self, refund: RefundRecordModel) -> dict[str, Any]:
        return {
            "refund_id": int(refund.id),
            "order_id": int(refund.order_id),
            "actor_item_id": int(refund.actor_item_id) if refund.actor_item_id else None,
            "payment_id": int(refund.payment_id) if refund.payment_id else None,
            "out_refund_no": refund.out_refund_no,
            "channel_refund_no": refund.channel_refund_no,
            "channel": refund.channel,
            "refund_amount": int(refund.refund_amount or 0),
            "status": refund.status,
            "reason": refund.reason,
            "operator_user_id": int(refund.operator_user_id) if refund.operator_user_id else None,
            "reviewed_by": int(refund.reviewed_by_id) if refund.reviewed_by_id else None,
            "reviewed_at": refund.reviewed_at,
            "created_at": refund.created_at,
            "updated_at": refund.updated_at,
        }

    def _serialize_settlement(self, settlement: SettlementRecordModel) -> dict[str, Any]:
        return {
            "settlement_id": int(settlement.id),
            "order_id": int(settlement.order_id),
            "actor_item_id": int(settlement.actor_item_id) if settlement.actor_item_id else None,
            "actor_id": int(settlement.actor_id) if settlement.actor_id else None,
            "out_settle_no": settlement.out_settle_no,
            "channel_settle_no": settlement.channel_settle_no,
            "channel": settlement.channel,
            "settle_amount": int(settlement.settle_amount or 0),
            "platform_fee_amount": int(settlement.platform_fee_amount or 0),
            "status": settlement.status,
            "requested_at": settlement.requested_at,
            "settled_at": settlement.settled_at,
            "created_at": settlement.created_at,
            "updated_at": settlement.updated_at,
        }

    def _item_refundable_remaining(self, item: EnterpriseOrderActorItemModel) -> int:
        return max(0, int(item.line_total_amount or 0) - int(item.refunded_amount or 0))

    def _item_actor_settle_remaining(self, item: EnterpriseOrderActorItemModel) -> int:
        actor_refunded = int((item.quote_snapshot or {}).get("actor_refunded_amount", 0) or 0)
        actor_due = max(0, int(item.actor_quote_amount or 0) - actor_refunded)
        return max(0, actor_due - int(item.settled_amount or 0))

    def _refresh_item_status(self, item: EnterpriseOrderActorItemModel) -> None:
        refunded_amount = int(item.refunded_amount or 0)
        line_total = int(item.line_total_amount or 0)
        if refunded_amount >= line_total and line_total > 0:
            item.item_status = ORDER_ITEM_STATUS_REFUNDED
            return

        actor_settle_remaining = self._item_actor_settle_remaining(item)
        if actor_settle_remaining <= 0 and int(item.actor_quote_amount or 0) > 0:
            if refunded_amount > 0:
                item.item_status = ORDER_ITEM_STATUS_PARTIALLY_REFUNDED
            else:
                item.item_status = ORDER_ITEM_STATUS_SETTLED
            return

        if refunded_amount > 0:
            item.item_status = ORDER_ITEM_STATUS_PARTIALLY_REFUNDED
            return

        if int(item.settled_amount or 0) > 0:
            item.item_status = ORDER_ITEM_STATUS_SETTLED
            return

        item.item_status = ORDER_ITEM_STATUS_PAID

    def _apply_refund_to_order_sync(
        self,
        *,
        order: EnterpriseOrderModel,
        actor_item: EnterpriseOrderActorItemModel | None,
        refund_amount: int,
    ) -> None:
        remaining = int(refund_amount)
        if remaining <= 0:
            return

        if actor_item is not None:
            used = self._apply_refund_to_item_sync(item=actor_item, amount=remaining)
            remaining -= used
            actor_item.save()
        else:
            items = list(
                EnterpriseOrderActorItemModel.select()
                .where(EnterpriseOrderActorItemModel.order_id == order.id)
                .order_by(EnterpriseOrderActorItemModel.id.asc())
            )
            for item in items:
                if remaining <= 0:
                    break
                alloc = min(remaining, self._item_refundable_remaining(item))
                if alloc <= 0:
                    continue
                used = self._apply_refund_to_item_sync(item=item, amount=alloc)
                remaining -= used
                item.save()

        if remaining != 0:
            raise ValueError("退款金额分摊失败，请检查订单条目。")

        order.refunded_total_amount = int(order.refunded_total_amount or 0) + int(refund_amount)
        self._recompute_order_settlement_sync(order)
        self._recompute_order_status_sync(order)
        order.updated_at = _utcnow()
        order.save()

    def _apply_refund_to_item_sync(self, *, item: EnterpriseOrderActorItemModel, amount: int) -> int:
        refundable = self._item_refundable_remaining(item)
        if amount <= 0 or amount > refundable:
            raise ValueError("条目退款金额非法。")

        quote_snapshot = dict(item.quote_snapshot or {})
        actor_refunded_before = int(quote_snapshot.get("actor_refunded_amount", 0) or 0)
        actor_quote_amount = int(item.actor_quote_amount or 0)
        line_total_amount = max(1, int(item.line_total_amount or 0))
        actor_refundable_remaining = max(0, actor_quote_amount - actor_refunded_before)

        if amount == refundable:
            actor_refund_part = actor_refundable_remaining
        else:
            actor_refund_part = (int(amount) * actor_quote_amount) // line_total_amount
            actor_refund_part = min(actor_refund_part, actor_refundable_remaining)

        quote_snapshot["actor_refunded_amount"] = actor_refunded_before + actor_refund_part
        item.quote_snapshot = quote_snapshot
        item.refunded_amount = int(item.refunded_amount or 0) + int(amount)
        self._refresh_item_status(item)
        item.updated_at = _utcnow()
        return int(amount)

    def _recompute_order_settlement_sync(self, order: EnterpriseOrderModel) -> None:
        items = list(
            EnterpriseOrderActorItemModel.select()
            .where(EnterpriseOrderActorItemModel.order_id == order.id)
        )
        if not items:
            order.settlement_status = SETTLEMENT_STATUS_PENDING
            return

        total_actor_due = 0
        total_actor_settled = 0
        for item in items:
            actor_refunded = int((item.quote_snapshot or {}).get("actor_refunded_amount", 0) or 0)
            actor_due = max(0, int(item.actor_quote_amount or 0) - actor_refunded)
            total_actor_due += actor_due
            total_actor_settled += min(actor_due, int(item.settled_amount or 0))

        if total_actor_due <= 0:
            order.settlement_status = SETTLEMENT_STATUS_SETTLED
            order.settled_at = order.settled_at or _utcnow()
            return

        if total_actor_settled <= 0:
            order.settlement_status = SETTLEMENT_STATUS_PENDING
            return

        if total_actor_settled >= total_actor_due:
            order.settlement_status = SETTLEMENT_STATUS_SETTLED
            order.settled_at = order.settled_at or _utcnow()
            return

        order.settlement_status = SETTLEMENT_STATUS_PARTIAL

    def _recompute_order_status_sync(self, order: EnterpriseOrderModel) -> None:
        paid_total = int(order.paid_total_amount or 0)
        refunded_total = int(order.refunded_total_amount or 0)

        if paid_total <= 0:
            order.status = ORDER_STATUS_PENDING_PAYMENT
            return
        if refunded_total >= paid_total:
            order.status = ORDER_STATUS_REFUNDED
            order.closed_at = order.closed_at or _utcnow()
            return
        if refunded_total > 0:
            order.status = ORDER_STATUS_PARTIALLY_REFUNDED
            return
        if order.settlement_status == SETTLEMENT_STATUS_SETTLED:
            order.status = ORDER_STATUS_SETTLED
            return
        order.status = ORDER_STATUS_PAID

    def _audit(
        self,
        *,
        action: str,
        detail: dict[str, Any],
        enterprise_user_id: int | None = None,
        order_id: int | None = None,
        actor_item_id: int | None = None,
        payment_id: int | None = None,
        refund_id: int | None = None,
        settlement_id: int | None = None,
        operator_user_id: int | None = None,
    ) -> None:
        try:
            PaymentAuditLogModel.create(
                enterprise_user_id=enterprise_user_id,
                order_id=order_id,
                actor_item_id=actor_item_id,
                payment_id=payment_id,
                refund_id=refund_id,
                settlement_id=settlement_id,
                action=action,
                operator_user_id=operator_user_id,
                detail=self._json_safe(detail),
                created_at=_utcnow(),
            )
        except Exception:
            logger.exception("Failed to write payment audit log action=%s", action)
