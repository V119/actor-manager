<template>
  <div class="flex-1 overflow-y-auto bg-background p-8 pt-24 min-h-screen">
    <div class="max-w-6xl mx-auto">
      <section class="mb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold tracking-tight text-on-surface">签约企业</h1>
          <p class="mt-2 text-sm text-on-surface-variant">
            这里展示已经与当前演员签约的企业，点击企业卡片可查看完整企业信息。
          </p>
        </div>
        <div class="relative w-full md:w-96">
          <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">search</span>
          <input
            v-model.trim="keyword"
            class="w-full bg-surface/40 border border-sky-400/10 rounded-full py-3 pl-12 pr-6 text-on-surface placeholder:text-slate-500 focus:outline-none focus:border-sky-400/40 focus:ring-1 focus:ring-sky-400/40 transition-all backdrop-blur-sm"
            placeholder="搜索签约企业"
            type="text"
          />
        </div>
      </section>

      <div v-if="loading" class="text-sm text-on-surface-variant">正在加载签约企业...</div>
      <div v-else-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</div>
      <div v-else-if="!filteredEnterprises.length" class="rounded-2xl border border-sky-400/10 bg-surface/40 px-5 py-8 text-sm text-on-surface-variant">
        当前还没有企业与您完成签约。
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <button
          v-for="enterprise in filteredEnterprises"
          :key="`${enterprise.enterprise_user_id}-${enterprise.signed_at}`"
          type="button"
          class="rounded-2xl border border-sky-400/10 bg-surface/50 p-5 text-left transition hover:border-sky-300/30 hover:-translate-y-1"
          @click="openEnterprise(enterprise.enterprise_user_id)"
        >
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-xl font-semibold text-on-surface">{{ enterprise.company_name }}</h2>
              <p class="mt-2 text-sm leading-6 text-on-surface-variant line-clamp-3">
                {{ enterprise.company_intro || '企业暂未填写企业简介。' }}
              </p>
            </div>
            <span class="rounded-full border border-emerald-300/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200">
              已签约
            </span>
          </div>

          <div class="mt-5 grid md:grid-cols-2 gap-3 text-sm">
            <div class="rounded-xl border border-sky-300/10 bg-slate-950/20 px-4 py-3">
              <p class="text-[11px] tracking-[0.16em] uppercase text-slate-400">统一社会信用代码</p>
              <p class="mt-2 break-all text-sky-50">{{ enterprise.credit_code || '未填写' }}</p>
            </div>
            <div class="rounded-xl border border-sky-300/10 bg-slate-950/20 px-4 py-3">
              <p class="text-[11px] tracking-[0.16em] uppercase text-slate-400">签约时间</p>
              <p class="mt-2 text-sky-50">{{ formatDateTime(enterprise.signed_at) }}</p>
            </div>
            <div class="rounded-xl border border-sky-300/10 bg-slate-950/20 px-4 py-3 md:col-span-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <p class="text-[11px] tracking-[0.16em] uppercase text-slate-400">付款情况</p>
                <span
                  class="rounded-full border px-2.5 py-1 text-[11px] font-semibold"
                  :class="paymentStatusClass(enterprise.payment_status)"
                >
                  {{ enterprise.payment_status_label || '未下单' }}
                </span>
              </div>
              <p class="mt-2 text-sky-50">
                <template v-if="enterprise.latest_order_no">
                  最近订单：{{ enterprise.latest_order_no }} · {{ formatCurrency(enterprise.latest_line_total_amount) }}
                </template>
                <template v-else>
                  暂无付款记录
                </template>
              </p>
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const keyword = ref('')
const enterprises = ref([])

const filteredEnterprises = computed(() => {
  const query = keyword.value.toLowerCase()
  if (!query) return enterprises.value
  return enterprises.value.filter((item) => {
    const companyName = String(item.company_name || '').toLowerCase()
    const companyIntro = String(item.company_intro || '').toLowerCase()
    const creditCode = String(item.credit_code || '').toLowerCase()
    return companyName.includes(query) || companyIntro.includes(query) || creditCode.includes(query)
  })
})

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

function formatCurrency(value) {
  const amount = Number(value || 0)
  if (!Number.isFinite(amount)) return '￥0'
  return `￥${amount.toLocaleString('zh-CN')}`
}

function paymentStatusClass(status) {
  const normalized = String(status || '').toLowerCase()
  if (normalized === 'settled') return 'border-emerald-300/30 bg-emerald-500/10 text-emerald-100'
  if (normalized === 'paid') return 'border-sky-300/30 bg-sky-500/10 text-sky-100'
  if (normalized === 'pending_payment') return 'border-amber-300/30 bg-amber-500/10 text-amber-100'
  if (normalized === 'payment_failed') return 'border-rose-300/30 bg-rose-500/10 text-rose-100'
  if (normalized === 'partially_refunded') return 'border-violet-300/30 bg-violet-500/10 text-violet-100'
  if (normalized === 'refunded') return 'border-slate-300/30 bg-slate-500/10 text-slate-100'
  return 'border-slate-300/20 bg-slate-500/10 text-slate-200'
}

function openEnterprise(enterpriseUserId) {
  router.push(`/actor-signed-enterprises/${enterpriseUserId}`)
}

async function loadEnterprises() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  try {
    const payload = await apiRequest('/actors/me/signed-enterprises', {
      token: authStore.state.token
    })
    enterprises.value = Array.isArray(payload) ? payload : []
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '签约企业加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadEnterprises()
})
</script>
