<template>
  <div class="min-h-screen bg-background text-on-surface">
    <main class="max-w-7xl mx-auto px-6 md:px-8 pt-24 pb-14 space-y-8">
      <header class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold tracking-tight">购物车与结算</h1>
          <p class="mt-2 text-sm text-on-surface-variant">
            在这里统一完成演员购物车管理、订单创建、支付与验收。
          </p>
        </div>
        <div class="flex flex-wrap gap-3">
          <button
            type="button"
            class="rounded-lg border border-moss-300/25 bg-ink-950/30 px-4 py-2 text-sm text-moss-100 transition hover:bg-moss-400/10"
            :disabled="pageLoading"
            @click="refreshAll"
          >
            {{ pageLoading ? '刷新中...' : '刷新数据' }}
          </button>
        </div>
      </header>

      <section v-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        {{ errorMessage }}
      </section>
      <section v-if="successMessage" class="rounded-2xl border border-sage-400/20 bg-sage-500/10 px-4 py-3 text-sm text-sage-200">
        {{ successMessage }}
      </section>

      <section class="grid lg:grid-cols-[1.4fr_1fr] gap-6">
        <div class="rounded-2xl border border-moss-400/10 bg-surface/65 p-5 md:p-6 backdrop-blur-xl space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <h2 class="text-lg font-semibold">演员购物车</h2>
            <div class="flex flex-wrap items-center gap-2 text-xs text-on-surface-variant">
              <button
                type="button"
                class="rounded-md border border-moss-300/25 px-3 py-1.5 text-moss-100 transition hover:bg-moss-400/10"
                @click="toggleSelectAll(true)"
              >
                全选
              </button>
              <button
                type="button"
                class="rounded-md border border-moss-300/25 px-3 py-1.5 text-moss-100 transition hover:bg-moss-400/10"
                @click="toggleSelectAll(false)"
              >
                清空
              </button>
              <span>已选 {{ selectedActorIds.length }} / {{ cartItems.length }}</span>
            </div>
          </div>

          <div v-if="cartLoading" class="text-sm text-on-surface-variant">正在加载购物车...</div>
          <div v-else-if="!cartItems.length" class="rounded-xl border border-moss-300/15 bg-ink-950/25 px-4 py-6 text-sm text-on-surface-variant">
            购物车为空。可在演员详情页先签约，再加入购物车。
          </div>
          <div v-else class="space-y-3">
            <article
              v-for="item in cartItems"
              :key="item.cart_item_id"
              class="rounded-xl border border-moss-300/15 bg-ink-950/25 px-4 py-4"
            >
              <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <label class="flex items-start gap-3">
                  <input
                    v-model="selectedActorIds"
                    :value="item.actor_id"
                    type="checkbox"
                    class="mt-1 h-4 w-4 rounded border-moss-300/30 bg-ink-900 text-moss-300 focus:ring-moss-300/60"
                    @change="refreshPreview"
                  />
                  <div>
                    <p class="text-sm font-semibold text-moss-100">{{ item.actor_name }}</p>
                    <p class="mt-1 text-xs text-on-surface-variant">ID: {{ item.actor_external_id }}</p>
                    <p class="mt-1 text-xs text-on-surface-variant">计费单位：{{ item.pricing_unit === 'day' ? '天' : '项目' }}</p>
                  </div>
                </label>
                <div class="flex flex-wrap items-center gap-3">
                  <p class="text-sm font-semibold text-sage-200">{{ formatCurrency(item.actor_quote_amount) }}</p>
                  <button
                    type="button"
                    class="rounded-md border border-rose-300/25 bg-rose-500/10 px-3 py-1.5 text-xs text-rose-100 transition hover:bg-rose-500/20"
                    :disabled="removingActorId === item.actor_id"
                    @click="removeCartItem(item.actor_id)"
                  >
                    {{ removingActorId === item.actor_id ? '移除中...' : '移出购物车' }}
                  </button>
                </div>
              </div>
            </article>
          </div>
        </div>

        <div class="rounded-2xl border border-sage-400/15 bg-surface/65 p-5 md:p-6 backdrop-blur-xl space-y-4">
          <h2 class="text-lg font-semibold">订单预览</h2>
          <div v-if="previewLoading" class="text-sm text-on-surface-variant">正在计算订单金额...</div>
          <template v-else-if="orderPreview">
            <div class="space-y-3 text-sm">
              <div class="flex items-center justify-between">
                <span class="text-on-surface-variant">演员报价合计</span>
                <span>{{ formatCurrency(orderPreview.actor_total_amount) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-on-surface-variant">平台手续费</span>
                <span>{{ formatCurrency(orderPreview.platform_fee_amount) }}</span>
              </div>
              <div class="flex items-center justify-between text-xs text-on-surface-variant">
                <span>手续费率</span>
                <span>{{ formatRate(orderPreview.fee_rate_bps) }}</span>
              </div>
              <div class="border-t border-sage-300/20 pt-3 flex items-center justify-between text-base font-semibold">
                <span>应付总额</span>
                <span class="text-sage-200">{{ formatCurrency(orderPreview.payable_total_amount) }}</span>
              </div>
            </div>

            <button
              type="button"
              class="w-full rounded-lg bg-moss-400 px-4 py-2.5 text-sm font-semibold text-ink-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="creatingOrder || !selectedActorIds.length"
              @click="createOrder"
            >
              {{ creatingOrder ? '创建订单中...' : `创建订单（${selectedActorIds.length} 位演员）` }}
            </button>
          </template>
          <div v-else class="text-sm text-on-surface-variant">请先在购物车中选择演员后预览。</div>
        </div>
      </section>

      <section class="grid xl:grid-cols-[1fr_1.2fr] gap-6">
        <div class="rounded-2xl border border-moss-400/10 bg-surface/65 p-5 md:p-6 backdrop-blur-xl space-y-4">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold">订单列表</h2>
            <button
              type="button"
              class="rounded-md border border-moss-300/25 px-3 py-1.5 text-xs text-moss-100 transition hover:bg-moss-400/10"
              :disabled="ordersLoading"
              @click="loadOrders"
            >
              {{ ordersLoading ? '刷新中...' : '刷新订单' }}
            </button>
          </div>
          <div v-if="ordersLoading" class="text-sm text-on-surface-variant">正在加载订单...</div>
          <div v-else-if="!orders.length" class="text-sm text-on-surface-variant">暂无订单记录。</div>
          <div v-else class="space-y-3">
            <article
              v-for="order in orders"
              :key="order.order_no"
              class="rounded-xl border px-4 py-4 transition"
              :class="activeOrderNo === order.order_no ? 'border-moss-300/40 bg-moss-500/10' : 'border-moss-300/15 bg-ink-950/25'"
            >
              <div class="flex flex-col gap-3">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="text-sm font-semibold text-moss-100">{{ order.order_no }}</p>
                    <p class="mt-1 text-xs text-on-surface-variant">创建时间：{{ formatDateTime(order.created_at) }}</p>
                  </div>
                  <span class="rounded-full border px-2.5 py-1 text-xs" :class="statusClass(order.status)">
                    {{ statusLabel(order.status) }}
                  </span>
                </div>
                <div class="flex items-center justify-between text-sm">
                  <span class="text-on-surface-variant">应付总额</span>
                  <span class="font-semibold text-sage-200">{{ formatCurrency(order.payable_total_amount) }}</span>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="rounded-md border border-moss-300/25 px-3 py-1.5 text-xs text-moss-100 transition hover:bg-moss-400/10"
                    @click="loadOrderDetail(order.order_no)"
                  >
                    查看详情
                  </button>
                  <button
                    v-if="canPay(order)"
                    type="button"
                    class="rounded-md border border-sage-300/25 bg-sage-500/10 px-3 py-1.5 text-xs text-sage-100 transition hover:bg-sage-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="payingOrderNo === order.order_no"
                    @click="payOrder(order.order_no, 'wechat')"
                  >
                    {{ payingOrderNo === order.order_no ? '支付中...' : '微信支付' }}
                  </button>
                  <button
                    v-if="canPay(order)"
                    type="button"
                    class="rounded-md border border-brass-300/25 bg-brass-500/10 px-3 py-1.5 text-xs text-brass-100 transition hover:bg-brass-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="payingOrderNo === order.order_no"
                    @click="payOrder(order.order_no, 'alipay')"
                  >
                    {{ payingOrderNo === order.order_no ? '支付中...' : '支付宝支付' }}
                  </button>
                  <button
                    v-if="canAccept(order)"
                    type="button"
                    class="rounded-md border border-moss-300/25 bg-moss-500/10 px-3 py-1.5 text-xs text-moss-100 transition hover:bg-moss-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="acceptingOrderNo === order.order_no"
                    @click="acceptOrder(order.order_no)"
                  >
                    {{ acceptingOrderNo === order.order_no ? '验收中...' : '手动验收' }}
                  </button>
                </div>
              </div>
            </article>
          </div>
        </div>

        <div class="rounded-2xl border border-sage-400/15 bg-surface/65 p-5 md:p-6 backdrop-blur-xl space-y-4">
          <h2 class="text-lg font-semibold">订单详情</h2>
          <div v-if="orderDetailLoading" class="text-sm text-on-surface-variant">正在加载订单详情...</div>
          <div v-else-if="!activeOrder" class="text-sm text-on-surface-variant">请选择左侧订单查看详情。</div>
          <template v-else>
            <div class="rounded-xl border border-sage-300/20 bg-ink-950/25 px-4 py-4 space-y-2">
              <div class="flex items-center justify-between text-sm">
                <span class="text-on-surface-variant">订单号</span>
                <span class="font-semibold text-moss-100">{{ activeOrder.order_no }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="text-on-surface-variant">订单状态</span>
                <span :class="statusTextClass(activeOrder.status)">{{ statusLabel(activeOrder.status) }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="text-on-surface-variant">应付总额</span>
                <span>{{ formatCurrency(activeOrder.payable_total_amount) }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="text-on-surface-variant">已退款</span>
                <span>{{ formatCurrency(activeOrder.refunded_total_amount) }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="text-on-surface-variant">可退款余额</span>
                <span>{{ formatCurrency(activeOrder.refundable_remaining_amount) }}</span>
              </div>
            </div>

            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-moss-100">演员条目</h3>
              <div v-if="!activeOrder.items?.length" class="text-xs text-on-surface-variant">暂无条目。</div>
              <div v-else class="space-y-2">
                <article
                  v-for="item in activeOrder.items"
                  :key="item.order_item_id"
                  class="rounded-lg border border-moss-300/15 bg-ink-950/25 px-3 py-3 text-xs space-y-1"
                >
                  <p class="font-semibold text-moss-100">{{ item.actor_name }}（{{ item.actor_external_id }}）</p>
                  <p class="text-on-surface-variant">
                    报价 {{ formatCurrency(item.actor_quote_amount) }} / 手续费 {{ formatCurrency(item.platform_fee_amount) }} / 小计 {{ formatCurrency(item.line_total_amount) }}
                  </p>
                  <p class="text-on-surface-variant">
                    已结算 {{ formatCurrency(item.settled_amount) }} / 已退款 {{ formatCurrency(item.refunded_amount) }} / 状态 {{ item.item_status }}
                  </p>
                </article>
              </div>
            </div>

            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-moss-100">支付记录</h3>
              <div v-if="!activeOrder.payments?.length" class="text-xs text-on-surface-variant">暂无支付记录。</div>
              <div v-else class="space-y-2">
                <article
                  v-for="payment in activeOrder.payments"
                  :key="payment.payment_id"
                  class="rounded-lg border border-sage-300/15 bg-ink-950/25 px-3 py-3 text-xs"
                >
                  <p class="text-sage-100">{{ payment.channel }} · {{ payment.status }}</p>
                  <p class="mt-1 text-on-surface-variant">{{ payment.out_trade_no }} · {{ formatCurrency(payment.amount) }}</p>
                </article>
              </div>
            </div>
          </template>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { authStore } from '../lib/auth'
import { ensureEnterpriseAgreementSigned } from '../lib/enterpriseAgreement'
import {
  createEnterpriseOrder,
  fetchEnterpriseCart,
  getEnterpriseOrder,
  listEnterpriseOrders,
  payEnterpriseOrder,
  previewEnterpriseOrder,
  removeEnterpriseCartItem,
  acceptEnterpriseOrder
} from '../lib/payment'

const pageLoading = ref(false)
const cartLoading = ref(false)
const previewLoading = ref(false)
const creatingOrder = ref(false)
const ordersLoading = ref(false)
const orderDetailLoading = ref(false)
const payingOrderNo = ref('')
const acceptingOrderNo = ref('')
const removingActorId = ref(0)

const errorMessage = ref('')
const successMessage = ref('')
const cartItems = ref([])
const selectedActorIds = ref([])
const orderPreview = ref(null)
const orders = ref([])
const activeOrderNo = ref('')
const activeOrder = ref(null)

function resetMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function formatCurrency(value) {
  const amount = Number(value || 0)
  if (!Number.isFinite(amount)) return '￥0'
  return `￥${amount.toLocaleString('zh-CN')}`
}

function formatRate(bps) {
  const value = Number(bps || 0)
  return `${(value / 100).toFixed(2)}%`
}

function formatDateTime(value) {
  if (!value) return '未记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '未记录'
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function statusLabel(status) {
  const map = {
    pending_payment: '待支付',
    payment_failed: '支付失败',
    paid: '已支付待结算',
    settled: '已结算',
    partially_refunded: '部分退款',
    refunded: '已退款'
  }
  return map[status] || status
}

function statusClass(status) {
  if (status === 'settled') return 'border-sage-300/30 bg-sage-500/10 text-sage-100'
  if (status === 'paid') return 'border-moss-300/30 bg-moss-500/10 text-moss-100'
  if (status === 'pending_payment') return 'border-brass-300/30 bg-brass-500/10 text-brass-100'
  if (status === 'refunded' || status === 'partially_refunded') return 'border-violet-300/30 bg-violet-500/10 text-violet-100'
  return 'border-ink-300/20 bg-ink-500/10 text-ink-200'
}

function statusTextClass(status) {
  if (status === 'settled') return 'text-sage-200'
  if (status === 'paid') return 'text-moss-200'
  if (status === 'pending_payment') return 'text-brass-100'
  if (status === 'refunded' || status === 'partially_refunded') return 'text-violet-200'
  return 'text-ink-200'
}

function canPay(order) {
  return ['pending_payment', 'payment_failed'].includes(order?.status)
}

function canAccept(order) {
  if (!order) return false
  return ['paid', 'partially_refunded', 'settled'].includes(order.status) && !order.accepted_at
}

function syncSelectionFromCart() {
  const validIds = new Set(cartItems.value.map((item) => item.actor_id))
  const next = selectedActorIds.value.filter((id) => validIds.has(id))
  if (!next.length && cartItems.value.length) {
    selectedActorIds.value = cartItems.value.map((item) => item.actor_id)
    return
  }
  selectedActorIds.value = next
}

function toggleSelectAll(checked) {
  selectedActorIds.value = checked ? cartItems.value.map((item) => item.actor_id) : []
  refreshPreview()
}

async function loadCart() {
  if (!authStore.state.token) return
  cartLoading.value = true
  try {
    const payload = await fetchEnterpriseCart({ token: authStore.state.token })
    cartItems.value = Array.isArray(payload?.items) ? payload.items : []
    syncSelectionFromCart()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '购物车加载失败'
  } finally {
    cartLoading.value = false
  }
}

async function refreshPreview() {
  if (!authStore.state.token) return
  if (!selectedActorIds.value.length) {
    orderPreview.value = null
    return
  }
  previewLoading.value = true
  try {
    orderPreview.value = await previewEnterpriseOrder({
      token: authStore.state.token,
      actorIds: selectedActorIds.value
    })
  } catch (error) {
    orderPreview.value = null
    errorMessage.value = error instanceof Error ? error.message : '订单预览失败'
  } finally {
    previewLoading.value = false
  }
}

async function loadOrders() {
  if (!authStore.state.token) return
  ordersLoading.value = true
  try {
    const payload = await listEnterpriseOrders({ token: authStore.state.token, limit: 50 })
    orders.value = Array.isArray(payload?.items) ? payload.items : []
    if (!orders.value.length) {
      activeOrderNo.value = ''
      activeOrder.value = null
      return
    }
    if (!activeOrderNo.value || !orders.value.find((order) => order.order_no === activeOrderNo.value)) {
      activeOrderNo.value = orders.value[0].order_no
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '订单列表加载失败'
  } finally {
    ordersLoading.value = false
  }
}

async function loadOrderDetail(orderNo) {
  if (!authStore.state.token) return
  orderDetailLoading.value = true
  activeOrderNo.value = orderNo
  try {
    activeOrder.value = await getEnterpriseOrder({ token: authStore.state.token, orderNo })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '订单详情加载失败'
  } finally {
    orderDetailLoading.value = false
  }
}

async function createOrder() {
  if (!authStore.state.token || !selectedActorIds.value.length) return
  creatingOrder.value = true
  resetMessages()
  try {
    const order = await createEnterpriseOrder({
      token: authStore.state.token,
      actorIds: selectedActorIds.value
    })
    successMessage.value = `订单 ${order.order_no} 创建成功。`
    await loadCart()
    await refreshPreview()
    await loadOrders()
    await loadOrderDetail(order.order_no)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建订单失败'
  } finally {
    creatingOrder.value = false
  }
}

async function payOrder(orderNo, channel) {
  if (!authStore.state.token) return
  payingOrderNo.value = orderNo
  resetMessages()
  try {
    const payment = await payEnterpriseOrder({
      token: authStore.state.token,
      orderNo,
      channel
    })
    if (payment.status === 'paid') {
      successMessage.value = `${channel === 'wechat' ? '微信' : '支付宝'}支付成功。`
    } else {
      successMessage.value = '已创建支付单，请按通道指引继续支付。'
    }
    await loadOrders()
    await loadOrderDetail(orderNo)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '发起支付失败'
  } finally {
    payingOrderNo.value = ''
  }
}

async function acceptOrder(orderNo) {
  if (!authStore.state.token) return
  acceptingOrderNo.value = orderNo
  resetMessages()
  try {
    const order = await acceptEnterpriseOrder({ token: authStore.state.token, orderNo })
    successMessage.value = '已手动验收订单，系统将按放款规则结算。'
    activeOrder.value = order
    await loadOrders()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '手动验收失败'
  } finally {
    acceptingOrderNo.value = ''
  }
}

async function removeCartItem(actorId) {
  if (!authStore.state.token) return
  removingActorId.value = actorId
  resetMessages()
  try {
    await removeEnterpriseCartItem({ token: authStore.state.token, actorId })
    successMessage.value = '已移出购物车。'
    await loadCart()
    await refreshPreview()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '移出购物车失败'
  } finally {
    removingActorId.value = 0
  }
}

async function refreshAll() {
  if (!authStore.state.token) return
  pageLoading.value = true
  resetMessages()
  try {
    const agreementResult = await ensureEnterpriseAgreementSigned({ token: authStore.state.token })
    if (!agreementResult.allowed) return
    await loadCart()
    await refreshPreview()
    await loadOrders()
    if (activeOrderNo.value) {
      await loadOrderDetail(activeOrderNo.value)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '刷新失败'
  } finally {
    pageLoading.value = false
  }
}

onMounted(async () => {
  await refreshAll()
})
</script>
