<template>
  <div class="flex-1 overflow-y-auto bg-background p-8 pt-24 min-h-screen text-on-surface">
    <div class="max-w-7xl mx-auto space-y-6">
      <section class="rounded-2xl border border-moss-400/10 bg-surface/60 p-6 backdrop-blur-xl">
        <h1 class="text-3xl font-bold tracking-tight">提现审核</h1>
        <p class="mt-2 text-sm text-on-surface-variant">
          管理员可在此审核演员提现申请，支持通过、驳回和失败处理。
        </p>
      </section>

      <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <article class="rounded-2xl border border-brass-300/20 bg-brass-500/10 p-4">
          <p class="text-xs tracking-[0.16em] uppercase text-brass-100/70">待处理单数</p>
          <p class="mt-2 text-2xl font-bold text-brass-100">{{ pendingCount }}</p>
        </article>
        <article class="rounded-2xl border border-sage-300/20 bg-sage-500/10 p-4">
          <p class="text-xs tracking-[0.16em] uppercase text-sage-100/70">已成功单数</p>
          <p class="mt-2 text-2xl font-bold text-sage-100">{{ succeededCount }}</p>
        </article>
        <article class="rounded-2xl border border-rose-300/20 bg-rose-500/10 p-4">
          <p class="text-xs tracking-[0.16em] uppercase text-rose-100/70">失败/驳回单数</p>
          <p class="mt-2 text-2xl font-bold text-rose-100">{{ failedCount }}</p>
        </article>
      </section>

      <section class="rounded-2xl border border-moss-400/10 bg-surface/50 p-5">
        <div class="flex flex-col md:flex-row gap-3 md:items-center md:justify-between">
          <div class="flex items-center gap-3">
            <label class="text-xs text-on-surface-variant">状态筛选</label>
            <select
              v-model="statusFilter"
              class="rounded-xl border border-moss-300/20 bg-ink-950/30 px-3 py-2 text-sm text-on-surface outline-none transition focus:border-moss-300/40 focus:ring-1 focus:ring-moss-300/30"
            >
              <option value="">全部</option>
              <option value="pending">待处理</option>
              <option value="processing">处理中</option>
              <option value="succeeded">已成功</option>
              <option value="failed">失败</option>
              <option value="rejected">已驳回</option>
            </select>
          </div>
          <button
            type="button"
            class="rounded-full border border-moss-300/30 px-4 py-2 text-xs text-moss-100 transition hover:bg-moss-400/10"
            @click="loadWithdrawals"
          >
            刷新列表
          </button>
        </div>

        <div v-if="loading" class="mt-4 text-sm text-on-surface-variant">正在加载提现列表...</div>
        <div v-else-if="errorMessage" class="mt-4 rounded-xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {{ errorMessage }}
        </div>
        <div v-else-if="!filteredWithdrawals.length" class="mt-4 rounded-xl border border-moss-300/10 bg-ink-950/20 px-4 py-6 text-sm text-on-surface-variant">
          当前没有匹配条件的提现记录。
        </div>

        <div v-else class="mt-4 space-y-3">
          <article
            v-for="item in filteredWithdrawals"
            :key="item.withdraw_id"
            class="rounded-xl border border-moss-300/10 bg-ink-950/20 px-4 py-4"
          >
            <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <p class="text-sm font-semibold text-moss-50">{{ item.actor_name || `演员#${item.actor_id}` }}</p>
                  <span class="rounded-full border px-2.5 py-1 text-[11px] font-semibold" :class="statusClass(item.status)">
                    {{ statusLabel(item.status) }}
                  </span>
                </div>
                <p class="mt-2 text-xs text-on-surface-variant">
                  提现单号：{{ item.out_withdraw_no }} · 金额：{{ formatCurrency(item.amount) }} ·
                  方式：{{ channelLabel(item.channel) }}
                </p>
                <p class="mt-1 text-xs text-on-surface-variant">
                  账号：{{ item.account_name }}（{{ item.account_no_masked }}）
                </p>
                <p class="mt-1 text-xs text-on-surface-variant">
                  申请时间：{{ formatDateTime(item.requested_at) }}
                  <template v-if="item.processed_at">
                    · 处理时间：{{ formatDateTime(item.processed_at) }}
                  </template>
                </p>
                <p v-if="item.remark" class="mt-1 text-xs text-on-surface-variant">备注：{{ item.remark }}</p>
                <p v-if="item.failure_reason" class="mt-1 text-xs text-rose-300">失败原因：{{ item.failure_reason }}</p>
              </div>

              <div v-if="isReviewable(item.status)" class="flex flex-wrap gap-2">
                <button
                  type="button"
                  class="rounded-full border border-sage-300/30 bg-sage-500/10 px-3 py-1.5 text-xs text-sage-100 transition hover:bg-sage-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="reviewingNo === item.out_withdraw_no"
                  @click="reviewWithdraw(item, 'approve')"
                >
                  通过
                </button>
                <button
                  type="button"
                  class="rounded-full border border-brass-300/30 bg-brass-500/10 px-3 py-1.5 text-xs text-brass-100 transition hover:bg-brass-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="reviewingNo === item.out_withdraw_no"
                  @click="reviewWithdraw(item, 'fail')"
                >
                  标记失败
                </button>
                <button
                  type="button"
                  class="rounded-full border border-rose-300/30 bg-rose-500/10 px-3 py-1.5 text-xs text-rose-100 transition hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="reviewingNo === item.out_withdraw_no"
                  @click="reviewWithdraw(item, 'reject')"
                >
                  驳回
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { authStore } from '../lib/auth'
import { listAdminWithdrawals, reviewAdminWithdrawal } from '../lib/payment'

const loading = ref(false)
const errorMessage = ref('')
const withdrawals = ref([])
const statusFilter = ref('')
const reviewingNo = ref('')

const filteredWithdrawals = computed(() => {
  const status = String(statusFilter.value || '').toLowerCase()
  if (!status) return withdrawals.value
  return withdrawals.value.filter((item) => String(item.status || '').toLowerCase() === status)
})

const pendingCount = computed(() => withdrawals.value.filter((item) => isReviewable(item.status)).length)
const succeededCount = computed(() => withdrawals.value.filter((item) => String(item.status || '').toLowerCase() === 'succeeded').length)
const failedCount = computed(() => withdrawals.value.filter((item) => ['failed', 'rejected'].includes(String(item.status || '').toLowerCase())).length)

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

function channelLabel(channel) {
  const normalized = String(channel || '').toLowerCase()
  if (normalized === 'wechat') return '微信'
  if (normalized === 'alipay') return '支付宝'
  return normalized || '未知'
}

function statusLabel(status) {
  const normalized = String(status || '').toLowerCase()
  if (normalized === 'pending') return '待处理'
  if (normalized === 'processing') return '处理中'
  if (normalized === 'succeeded') return '已成功'
  if (normalized === 'failed') return '失败'
  if (normalized === 'rejected') return '已驳回'
  return status || '未知'
}

function statusClass(status) {
  const normalized = String(status || '').toLowerCase()
  if (normalized === 'pending') return 'border-brass-300/30 bg-brass-500/10 text-brass-100'
  if (normalized === 'processing') return 'border-moss-300/30 bg-moss-500/10 text-moss-100'
  if (normalized === 'succeeded') return 'border-sage-300/30 bg-sage-500/10 text-sage-100'
  if (normalized === 'failed' || normalized === 'rejected') return 'border-rose-300/30 bg-rose-500/10 text-rose-100'
  return 'border-ink-300/20 bg-ink-500/10 text-ink-200'
}

function isReviewable(status) {
  const normalized = String(status || '').toLowerCase()
  return normalized === 'pending' || normalized === 'processing'
}

async function loadWithdrawals() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  try {
    const payload = await listAdminWithdrawals({ token: authStore.state.token, limit: 200 })
    withdrawals.value = Array.isArray(payload?.items) ? payload.items : []
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '提现记录加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function reviewWithdraw(item, action) {
  if (!authStore.state.token || !item?.out_withdraw_no) return
  let failureReason = ''
  if (action === 'approve') {
    const confirmed = window.confirm(`确认通过提现申请：${item.out_withdraw_no}？`)
    if (!confirmed) return
  } else {
    const tip = action === 'reject' ? '请输入驳回原因：' : '请输入失败原因：'
    const value = window.prompt(tip, '')
    if (value === null) return
    failureReason = String(value || '').trim()
    if (!failureReason) {
      window.alert('原因不能为空。')
      return
    }
  }

  reviewingNo.value = item.out_withdraw_no
  try {
    await reviewAdminWithdrawal({
      token: authStore.state.token,
      payload: {
        out_withdraw_no: item.out_withdraw_no,
        action,
        failure_reason: failureReason
      }
    })
    await loadWithdrawals()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '审核失败，请稍后重试。'
  } finally {
    reviewingNo.value = ''
  }
}

onMounted(async () => {
  await loadWithdrawals()
})
</script>
