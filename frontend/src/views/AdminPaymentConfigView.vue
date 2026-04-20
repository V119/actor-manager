<template>
  <div class="flex-1 overflow-y-auto bg-background p-8 pt-24 min-h-screen text-on-surface">
    <div class="max-w-6xl mx-auto space-y-6">
      <section class="rounded-2xl border border-sky-400/10 bg-surface/60 p-6 backdrop-blur-xl">
        <h1 class="text-3xl font-bold tracking-tight">支付配置</h1>
        <p class="mt-2 text-sm text-on-surface-variant">
          在管理端设置平台手续费率与支付参数。手续费率会作用于后续新创建订单。
        </p>
      </section>

      <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <article class="rounded-2xl border border-emerald-300/20 bg-emerald-500/10 p-5">
          <p class="text-xs tracking-[0.16em] uppercase text-emerald-100/70">当前手续费率</p>
          <p class="mt-3 text-2xl font-bold text-emerald-100">{{ feeRatePercent }}</p>
          <p class="mt-1 text-xs text-emerald-100/70">{{ form.feeRateBps }} bps</p>
        </article>
        <article class="rounded-2xl border border-sky-300/20 bg-sky-500/10 p-5">
          <p class="text-xs tracking-[0.16em] uppercase text-sky-100/70">示例报价</p>
          <p class="mt-3 text-2xl font-bold text-sky-100">{{ formatCurrency(sampleActorQuoteAmount) }}</p>
          <p class="mt-1 text-xs text-sky-100/70">演员报价</p>
        </article>
        <article class="rounded-2xl border border-violet-300/20 bg-violet-500/10 p-5">
          <p class="text-xs tracking-[0.16em] uppercase text-violet-100/70">示例手续费</p>
          <p class="mt-3 text-2xl font-bold text-violet-100">{{ formatCurrency(samplePlatformFeeAmount) }}</p>
          <p class="mt-1 text-xs text-violet-100/70">按当前手续费率测算</p>
        </article>
      </section>

      <section class="rounded-2xl border border-sky-400/10 bg-surface/50 p-6">
        <div class="flex items-center justify-between gap-3">
          <h2 class="text-lg font-semibold">参数设置</h2>
          <button
            type="button"
            class="rounded-full border border-sky-300/30 px-4 py-2 text-xs text-sky-100 transition hover:bg-sky-400/10"
            :disabled="loading"
            @click="loadConfig"
          >
            刷新配置
          </button>
        </div>

        <div v-if="loading" class="mt-4 text-sm text-on-surface-variant">正在加载配置...</div>
        <div v-else class="mt-5 space-y-5">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label class="block">
              <span class="text-xs text-on-surface-variant">平台手续费率（bps，0-4000）</span>
              <input
                v-model.number="form.feeRateBps"
                type="number"
                min="0"
                max="4000"
                step="1"
                class="mt-2 w-full rounded-xl border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm outline-none transition focus:border-sky-300/40 focus:ring-1 focus:ring-sky-300/30"
              />
              <p class="mt-1 text-xs text-on-surface-variant">100 bps = 1%。例如 600 bps = 6%。</p>
            </label>

            <div class="rounded-xl border border-sky-300/10 bg-slate-950/20 px-4 py-3">
              <p class="text-xs text-on-surface-variant">支付通道开关</p>
              <div class="mt-3 flex items-center gap-6">
                <label class="inline-flex items-center gap-2 text-sm text-on-surface">
                  <input v-model="form.allowWechat" type="checkbox" class="accent-sky-400" />
                  微信支付
                </label>
                <label class="inline-flex items-center gap-2 text-sm text-on-surface">
                  <input v-model="form.allowAlipay" type="checkbox" class="accent-sky-400" />
                  支付宝支付
                </label>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <label class="block">
              <span class="text-xs text-on-surface-variant">自动验收时长（小时）</span>
              <input
                v-model.number="form.autoAcceptHours"
                type="number"
                min="1"
                max="2160"
                step="1"
                class="mt-2 w-full rounded-xl border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm outline-none transition focus:border-sky-300/40 focus:ring-1 focus:ring-sky-300/30"
              />
            </label>
            <label class="block">
              <span class="text-xs text-on-surface-variant">纠纷保护期（小时）</span>
              <input
                v-model.number="form.disputeProtectHours"
                type="number"
                min="0"
                max="2160"
                step="1"
                class="mt-2 w-full rounded-xl border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm outline-none transition focus:border-sky-300/40 focus:ring-1 focus:ring-sky-300/30"
              />
            </label>
            <label class="block">
              <span class="text-xs text-on-surface-variant">最大冻结时长（小时）</span>
              <input
                v-model.number="form.maxHoldHours"
                type="number"
                min="24"
                max="8760"
                step="1"
                class="mt-2 w-full rounded-xl border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm outline-none transition focus:border-sky-300/40 focus:ring-1 focus:ring-sky-300/30"
              />
            </label>
            <label class="block">
              <span class="text-xs text-on-surface-variant">结算安全缓冲（小时）</span>
              <input
                v-model.number="form.settlementSafetyBufferHours"
                type="number"
                min="0"
                max="168"
                step="1"
                class="mt-2 w-full rounded-xl border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm outline-none transition focus:border-sky-300/40 focus:ring-1 focus:ring-sky-300/30"
              />
            </label>
          </div>

          <p v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</p>
          <p v-if="successMessage" class="text-sm text-emerald-300">{{ successMessage }}</p>

          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="rounded-xl bg-sky-400/90 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="saving || loading"
              @click="saveConfig"
            >
              {{ saving ? '保存中...' : '保存配置' }}
            </button>
            <span class="text-xs text-on-surface-variant">上次更新时间：{{ formatDateTime(configUpdatedAt) }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { authStore } from '../lib/auth'
import { fetchAdminPaymentConfig, updateAdminPaymentConfig } from '../lib/payment'

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const configUpdatedAt = ref('')

const form = ref({
  feeRateBps: 600,
  autoAcceptHours: 72,
  disputeProtectHours: 168,
  maxHoldHours: 4320,
  settlementSafetyBufferHours: 24,
  allowWechat: true,
  allowAlipay: true
})

const sampleActorQuoteAmount = 10000

const feeRatePercent = computed(() => {
  const bps = Number(form.value.feeRateBps || 0)
  return `${(bps / 100).toFixed(2)}%`
})

const samplePlatformFeeAmount = computed(() => {
  const bps = Math.max(0, Number(form.value.feeRateBps || 0))
  return Math.floor((sampleActorQuoteAmount * bps) / 10000)
})

function formatCurrency(value) {
  const amount = Number(value || 0)
  if (!Number.isFinite(amount)) return '￥0'
  return `￥${amount.toLocaleString('zh-CN')}`
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

function assignFormFromConfig(payload) {
  form.value = {
    feeRateBps: Number(payload?.fee_rate_bps ?? 600),
    autoAcceptHours: Number(payload?.auto_accept_hours ?? 72),
    disputeProtectHours: Number(payload?.dispute_protect_hours ?? 168),
    maxHoldHours: Number(payload?.max_hold_hours ?? 4320),
    settlementSafetyBufferHours: Number(payload?.settlement_safety_buffer_hours ?? 24),
    allowWechat: Boolean(payload?.allow_wechat ?? true),
    allowAlipay: Boolean(payload?.allow_alipay ?? true)
  }
  configUpdatedAt.value = payload?.updated_at || ''
}

function buildPayload() {
  return {
    fee_rate_bps: Math.trunc(Number(form.value.feeRateBps || 0)),
    auto_accept_hours: Math.trunc(Number(form.value.autoAcceptHours || 0)),
    dispute_protect_hours: Math.trunc(Number(form.value.disputeProtectHours || 0)),
    max_hold_hours: Math.trunc(Number(form.value.maxHoldHours || 0)),
    settlement_safety_buffer_hours: Math.trunc(Number(form.value.settlementSafetyBufferHours || 0)),
    allow_wechat: Boolean(form.value.allowWechat),
    allow_alipay: Boolean(form.value.allowAlipay)
  }
}

async function loadConfig() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const payload = await fetchAdminPaymentConfig({ token: authStore.state.token })
    assignFormFromConfig(payload)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载支付配置失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  if (!authStore.state.token) return
  const payload = buildPayload()
  if (payload.fee_rate_bps < 0 || payload.fee_rate_bps > 4000) {
    errorMessage.value = '手续费率范围必须在 0 到 4000 bps 之间。'
    return
  }
  if (payload.settlement_safety_buffer_hours >= payload.max_hold_hours) {
    errorMessage.value = '结算安全缓冲时间必须小于最大冻结时间。'
    return
  }

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const updated = await updateAdminPaymentConfig({
      token: authStore.state.token,
      payload
    })
    assignFormFromConfig(updated)
    successMessage.value = '支付配置已保存。'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存失败，请稍后重试。'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadConfig()
})
</script>
