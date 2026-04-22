<template>
  <div class="flex-1 overflow-y-auto bg-background px-8 pt-24 pb-12 min-h-screen text-on-surface">
    <div class="max-w-6xl mx-auto space-y-6">
      <section class="rounded-2xl border border-moss-400/10 bg-surface/60 p-6 backdrop-blur-xl">
        <h1 class="text-3xl font-bold tracking-tight">金额与提现</h1>
        <p class="mt-2 text-sm text-on-surface-variant">
          在这里查看累计结算金额、可提现余额，并提交提现申请。
        </p>
      </section>

      <div v-if="loading" class="text-sm text-on-surface-variant">正在加载钱包数据...</div>
      <div v-else-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        {{ errorMessage }}
      </div>

      <template v-else>
        <section class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
          <article class="rounded-2xl border border-sage-300/20 bg-sage-500/10 p-5">
            <p class="text-xs tracking-[0.16em] uppercase text-sage-100/70">可提现余额</p>
            <p class="mt-3 text-2xl font-bold text-sage-100">{{ formatCurrency(wallet.available_amount) }}</p>
          </article>
          <article class="rounded-2xl border border-moss-300/20 bg-moss-500/10 p-5">
            <p class="text-xs tracking-[0.16em] uppercase text-moss-100/70">累计结算</p>
            <p class="mt-3 text-2xl font-bold text-moss-100">{{ formatCurrency(wallet.total_settled_amount) }}</p>
          </article>
          <article class="rounded-2xl border border-brass-300/20 bg-brass-500/10 p-5">
            <p class="text-xs tracking-[0.16em] uppercase text-brass-100/70">提现处理中</p>
            <p class="mt-3 text-2xl font-bold text-brass-100">{{ formatCurrency(wallet.total_withdrawing_amount) }}</p>
          </article>
          <article class="rounded-2xl border border-violet-300/20 bg-violet-500/10 p-5">
            <p class="text-xs tracking-[0.16em] uppercase text-violet-100/70">累计已提现</p>
            <p class="mt-3 text-2xl font-bold text-violet-100">{{ formatCurrency(wallet.total_withdrawn_amount) }}</p>
          </article>
          <article class="rounded-2xl border border-rose-300/20 bg-rose-500/10 p-5">
            <p class="text-xs tracking-[0.16em] uppercase text-rose-100/70">失败/驳回金额</p>
            <p class="mt-3 text-2xl font-bold text-rose-100">{{ formatCurrency(wallet.total_failed_withdraw_amount) }}</p>
          </article>
        </section>

        <section class="grid grid-cols-1 xl:grid-cols-5 gap-5">
          <article class="xl:col-span-2 rounded-2xl border border-moss-400/10 bg-surface/50 p-5">
            <h2 class="text-lg font-semibold text-on-surface">发起提现</h2>
            <p class="mt-1 text-xs text-on-surface-variant">支持微信或支付宝收款，金额不得超过可提现余额。</p>

            <form class="mt-5 space-y-4" @submit.prevent="submitWithdraw">
              <label class="block">
                <span class="text-xs text-on-surface-variant">提现金额（元）</span>
                <input
                  v-model.number="form.amount"
                  type="number"
                  min="1"
                  step="1"
                  class="mt-2 w-full rounded-xl border border-moss-300/20 bg-ink-950/30 px-3 py-2.5 text-sm text-on-surface outline-none transition focus:border-moss-300/40 focus:ring-1 focus:ring-moss-300/30"
                  placeholder="请输入提现金额"
                  required
                />
              </label>

              <label class="block">
                <span class="text-xs text-on-surface-variant">提现方式</span>
                <select
                  v-model="form.channel"
                  class="mt-2 w-full rounded-xl border border-moss-300/20 bg-ink-950/30 px-3 py-2.5 text-sm text-on-surface outline-none transition focus:border-moss-300/40 focus:ring-1 focus:ring-moss-300/30"
                >
                  <option value="wechat">微信</option>
                  <option value="alipay">支付宝</option>
                </select>
              </label>

              <label class="block">
                <span class="text-xs text-on-surface-variant">收款人</span>
                <input
                  v-model.trim="form.accountName"
                  type="text"
                  maxlength="64"
                  class="mt-2 w-full rounded-xl border border-moss-300/20 bg-ink-950/30 px-3 py-2.5 text-sm text-on-surface outline-none transition focus:border-moss-300/40 focus:ring-1 focus:ring-moss-300/30"
                  placeholder="请输入姓名"
                  required
                />
              </label>

              <label class="block">
                <span class="text-xs text-on-surface-variant">收款账号</span>
                <input
                  v-model.trim="form.accountNo"
                  type="text"
                  maxlength="128"
                  class="mt-2 w-full rounded-xl border border-moss-300/20 bg-ink-950/30 px-3 py-2.5 text-sm text-on-surface outline-none transition focus:border-moss-300/40 focus:ring-1 focus:ring-moss-300/30"
                  placeholder="请输入微信号或支付宝账号"
                  required
                />
              </label>

              <label class="block">
                <span class="text-xs text-on-surface-variant">备注（可选）</span>
                <textarea
                  v-model.trim="form.remark"
                  rows="3"
                  maxlength="256"
                  class="mt-2 w-full rounded-xl border border-moss-300/20 bg-ink-950/30 px-3 py-2.5 text-sm text-on-surface outline-none transition focus:border-moss-300/40 focus:ring-1 focus:ring-moss-300/30"
                  placeholder="填写备注信息"
                />
              </label>

              <p v-if="submitError" class="text-sm text-rose-300">{{ submitError }}</p>
              <p v-if="submitSuccess" class="text-sm text-sage-300">{{ submitSuccess }}</p>

              <button
                type="submit"
                class="w-full rounded-xl bg-moss-400/90 px-4 py-2.5 text-sm font-semibold text-ink-950 transition hover:bg-moss-300 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="submitting"
              >
                {{ submitting ? '提交中...' : '提交提现申请' }}
              </button>
            </form>
          </article>

          <article class="xl:col-span-3 rounded-2xl border border-moss-400/10 bg-surface/50 p-5">
            <div class="flex items-center justify-between gap-3">
              <h2 class="text-lg font-semibold text-on-surface">提现记录</h2>
              <button
                type="button"
                class="rounded-full border border-moss-300/30 px-3 py-1.5 text-xs text-moss-100 transition hover:bg-moss-400/10"
                @click="reload"
              >
                刷新
              </button>
            </div>

            <div v-if="!withdrawals.length" class="mt-4 rounded-xl border border-moss-300/10 bg-ink-950/20 px-4 py-6 text-sm text-on-surface-variant">
              暂无提现记录。
            </div>

            <div v-else class="mt-4 space-y-3">
              <div
                v-for="item in withdrawals"
                :key="item.withdraw_id"
                class="rounded-xl border border-moss-300/10 bg-ink-950/20 px-4 py-4"
              >
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <p class="text-sm font-semibold text-moss-50">{{ formatCurrency(item.amount) }}</p>
                  <span class="rounded-full border px-2.5 py-1 text-[11px] font-semibold" :class="withdrawStatusClass(item.status)">
                    {{ withdrawStatusLabel(item.status) }}
                  </span>
                </div>
                <p class="mt-2 text-xs text-on-surface-variant">
                  单号：{{ item.out_withdraw_no }} · 方式：{{ channelLabel(item.channel) }} · 账号：{{ item.account_no_masked }}
                </p>
                <p class="mt-1 text-xs text-on-surface-variant">
                  申请时间：{{ formatDateTime(item.requested_at) }}
                  <template v-if="item.processed_at">
                    · 处理时间：{{ formatDateTime(item.processed_at) }}
                  </template>
                </p>
                <p v-if="item.failure_reason" class="mt-1 text-xs text-rose-300">
                  失败原因：{{ item.failure_reason }}
                </p>
              </div>
            </div>
          </article>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { authStore } from '../lib/auth'
import {
  createActorWithdrawal,
  fetchActorWalletSummary,
  listActorWithdrawals
} from '../lib/payment'

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const submitError = ref('')
const submitSuccess = ref('')
const wallet = ref({
  available_amount: 0,
  total_settled_amount: 0,
  total_withdrawing_amount: 0,
  total_withdrawn_amount: 0,
  total_failed_withdraw_amount: 0
})
const withdrawals = ref([])

const form = ref({
  amount: 0,
  channel: 'wechat',
  accountName: '',
  accountNo: '',
  remark: ''
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

function channelLabel(channel) {
  const normalized = String(channel || '').toLowerCase()
  if (normalized === 'wechat') return '微信'
  if (normalized === 'alipay') return '支付宝'
  return normalized || '未知'
}

function withdrawStatusLabel(status) {
  const normalized = String(status || '').toLowerCase()
  if (normalized === 'pending') return '待处理'
  if (normalized === 'processing') return '处理中'
  if (normalized === 'succeeded') return '已打款'
  if (normalized === 'failed') return '失败'
  if (normalized === 'rejected') return '已驳回'
  return status || '未知'
}

function withdrawStatusClass(status) {
  const normalized = String(status || '').toLowerCase()
  if (normalized === 'pending') return 'border-brass-300/30 bg-brass-500/10 text-brass-100'
  if (normalized === 'processing') return 'border-moss-300/30 bg-moss-500/10 text-moss-100'
  if (normalized === 'succeeded') return 'border-sage-300/30 bg-sage-500/10 text-sage-100'
  if (normalized === 'failed' || normalized === 'rejected') return 'border-rose-300/30 bg-rose-500/10 text-rose-100'
  return 'border-ink-300/20 bg-ink-500/10 text-ink-200'
}

async function loadWalletData() {
  if (!authStore.state.token) return
  const summary = await fetchActorWalletSummary({ token: authStore.state.token })
  wallet.value = {
    available_amount: Number(summary?.available_amount || 0),
    total_settled_amount: Number(summary?.total_settled_amount || 0),
    total_withdrawing_amount: Number(summary?.total_withdrawing_amount || 0),
    total_withdrawn_amount: Number(summary?.total_withdrawn_amount || 0),
    total_failed_withdraw_amount: Number(summary?.total_failed_withdraw_amount || 0)
  }
}

async function loadWithdrawals() {
  if (!authStore.state.token) return
  const payload = await listActorWithdrawals({ token: authStore.state.token, limit: 100 })
  withdrawals.value = Array.isArray(payload?.items) ? payload.items : []
}

async function reload() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  try {
    await Promise.all([loadWalletData(), loadWithdrawals()])
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '钱包数据加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function submitWithdraw() {
  if (!authStore.state.token) return
  submitError.value = ''
  submitSuccess.value = ''
  if (!Number.isFinite(Number(form.value.amount)) || Number(form.value.amount) <= 0) {
    submitError.value = '请输入正确的提现金额。'
    return
  }
  submitting.value = true
  try {
    await createActorWithdrawal({
      token: authStore.state.token,
      payload: {
        amount: Number(form.value.amount),
        channel: form.value.channel,
        account_name: form.value.accountName,
        account_no: form.value.accountNo,
        remark: form.value.remark
      }
    })
    submitSuccess.value = '提现申请已提交。'
    form.value.amount = 0
    form.value.remark = ''
    await reload()
  } catch (error) {
    submitError.value = error instanceof Error ? error.message : '提现申请提交失败，请稍后重试。'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await reload()
})
</script>
