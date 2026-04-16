<template>
  <div class="min-h-screen pt-24 px-6 pb-10 lg:px-10">
    <section class="max-w-6xl mx-auto space-y-6">
      <div class="rounded-2xl border border-amber-400/20 bg-slate-950/60 backdrop-blur-xl p-6">
        <p class="text-xs tracking-[0.2em] uppercase text-amber-300">Agreement Template</p>
        <h1 class="text-2xl font-bold text-amber-100 mt-2">企业协议模板配置</h1>
        <p class="text-sm text-on-surface-variant mt-2">
          管理企业签署协议中的甲方信息与授权日期。企业端展示内容固定采用《AI肖像权转授权与内容制作合作协议.docx》版本。
        </p>
      </div>

      <section class="rounded-2xl border border-amber-400/15 bg-surface/60 backdrop-blur-xl p-6 space-y-5">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold text-amber-100">甲方信息</h2>
            <p class="text-sm text-on-surface-variant mt-2">
              每次修改会生成新的协议模板版本。企业若已签署旧版本，系统会提示重新签署后才能继续访问演员广场。
            </p>
          </div>
          <div class="text-right text-xs text-on-surface-variant">
            <p>当前版本：<span class="text-amber-200 font-semibold">V{{ template.version || 1 }}</span></p>
            <p class="mt-1">模板状态：<span :class="template.is_ready ? 'text-emerald-300' : 'text-amber-300'">{{ template.is_ready ? '可签署' : '待完善' }}</span></p>
          </div>
        </div>

        <p v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</p>
        <p v-if="successMessage" class="text-sm text-emerald-300">{{ successMessage }}</p>

        <form class="grid grid-cols-1 lg:grid-cols-2 gap-4" @submit.prevent="saveTemplate">
          <label class="space-y-1 lg:col-span-2">
            <span class="text-xs text-on-surface-variant">协议来源文件</span>
            <input
              :value="template.source_document_name || 'AI肖像权转授权与内容制作合作协议.docx'"
              type="text"
              disabled
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/40 px-4 py-3 text-sm text-slate-400"
            />
          </label>

          <label class="space-y-1">
            <span class="text-xs text-on-surface-variant">甲方公司名称</span>
            <input
              v-model="form.party_a_company_name"
              type="text"
              maxlength="128"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
              placeholder="请输入甲方公司名称"
            />
          </label>

          <label class="space-y-1">
            <span class="text-xs text-on-surface-variant">统一社会信用代码</span>
            <input
              v-model="form.party_a_credit_code"
              type="text"
              maxlength="64"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
              placeholder="请输入统一社会信用代码"
            />
          </label>

          <label class="space-y-1 lg:col-span-2">
            <span class="text-xs text-on-surface-variant">注册地址</span>
            <textarea
              v-model="form.party_a_registered_address"
              rows="3"
              maxlength="512"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
              placeholder="请输入甲方注册地址"
            />
          </label>

          <label class="space-y-1">
            <span class="text-xs text-on-surface-variant">授权期限模式</span>
            <select
              v-model="form.authorization_date_mode"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
            >
              <option value="fixed">指定开始时间和结束时间</option>
              <option value="relative_months">当前时间 + N个月</option>
            </select>
          </label>

          <label v-if="form.authorization_date_mode === 'relative_months'" class="space-y-1">
            <span class="text-xs text-on-surface-variant">授权期限（月）</span>
            <input
              v-model.number="form.authorization_term_months"
              type="number"
              min="1"
              max="120"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
              placeholder="例如 6"
            />
          </label>

          <label v-if="form.authorization_date_mode === 'fixed'" class="space-y-1">
            <span class="text-xs text-on-surface-variant">授权开始日期</span>
            <input
              v-model="form.authorization_start_date"
              type="date"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
            />
          </label>

          <label v-if="form.authorization_date_mode === 'fixed'" class="space-y-1">
            <span class="text-xs text-on-surface-variant">授权截止日期</span>
            <input
              v-model="form.authorization_end_date"
              type="date"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
            />
          </label>

          <div
            v-else
            class="space-y-2 rounded-xl border border-amber-300/15 bg-slate-950/20 px-4 py-3 text-sm text-on-surface-variant"
          >
            <p>保存时将自动按当前日期生成授权起止时间。</p>
            <p>预计开始日期：<span class="text-amber-200">{{ relativeDatePreview.start }}</span></p>
            <p>预计结束日期：<span class="text-amber-200">{{ relativeDatePreview.end }}</span></p>
          </div>

          <label class="space-y-1">
            <span class="text-xs text-on-surface-variant">甲方签章显示文本</span>
            <input
              v-model="form.party_a_signature_label"
              type="text"
              maxlength="128"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
              placeholder="默认为甲方公司名称"
            />
          </label>

          <label class="space-y-1">
            <span class="text-xs text-on-surface-variant">甲方签章日期</span>
            <input
              v-model="form.party_a_signed_date"
              type="date"
              class="w-full rounded-xl border border-amber-300/20 bg-slate-950/30 px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60"
            />
          </label>

          <div class="lg:col-span-2 flex justify-end">
            <button
              type="submit"
              :disabled="saving"
              class="px-5 py-3 rounded-xl bg-amber-300 text-slate-900 text-sm font-semibold hover:brightness-110 transition-all disabled:opacity-60"
            >
              {{ saving ? '保存中...' : '保存协议模板' }}
            </button>
          </div>
        </form>
      </section>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const template = ref({
  version: 1,
  source_document_name: 'AI肖像权转授权与内容制作合作协议.docx',
  is_ready: false
})

const form = reactive({
  party_a_company_name: '',
  party_a_credit_code: '',
  party_a_registered_address: '',
  authorization_date_mode: 'fixed',
  authorization_term_months: 6,
  authorization_start_date: '',
  authorization_end_date: '',
  party_a_signature_label: '',
  party_a_signed_date: ''
})

const relativeDatePreview = computed(() => buildRelativeDatePreview(form.authorization_term_months))

function resetMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function applyTemplate(payload) {
  template.value = payload || {
    version: 1,
    source_document_name: 'AI肖像权转授权与内容制作合作协议.docx',
    is_ready: false
  }
  form.party_a_company_name = payload?.party_a_company_name || ''
  form.party_a_credit_code = payload?.party_a_credit_code || ''
  form.party_a_registered_address = payload?.party_a_registered_address || ''
  form.authorization_date_mode = payload?.authorization_date_mode || 'fixed'
  form.authorization_term_months = payload?.authorization_term_months || 6
  form.authorization_start_date = payload?.authorization_start_date || ''
  form.authorization_end_date = payload?.authorization_end_date || ''
  form.party_a_signature_label = payload?.party_a_signature_label || ''
  form.party_a_signed_date = payload?.party_a_signed_date || ''
}

async function loadTemplate() {
  if (!authStore.state.token) return
  resetMessages()
  try {
    const payload = await apiRequest('/admin/enterprise-agreement/template', { token: authStore.state.token })
    applyTemplate(payload)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '企业协议模板加载失败'
  }
}

async function saveTemplate() {
  if (!authStore.state.token) return
  saving.value = true
  resetMessages()
  try {
    const payload = await apiRequest('/admin/enterprise-agreement/template', {
      method: 'PUT',
      token: authStore.state.token,
      body: {
        party_a_company_name: form.party_a_company_name.trim(),
        party_a_credit_code: form.party_a_credit_code.trim(),
        party_a_registered_address: form.party_a_registered_address.trim(),
        authorization_date_mode: form.authorization_date_mode,
        authorization_term_months: form.authorization_date_mode === 'relative_months'
          ? Number(form.authorization_term_months) || null
          : null,
        authorization_start_date: form.authorization_date_mode === 'fixed'
          ? (form.authorization_start_date || null)
          : null,
        authorization_end_date: form.authorization_date_mode === 'fixed'
          ? (form.authorization_end_date || null)
          : null,
        party_a_signature_label: form.party_a_signature_label.trim(),
        party_a_signed_date: form.party_a_signed_date || null
      }
    })
    applyTemplate(payload)
    successMessage.value = '企业协议模板已保存'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '企业协议模板保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadTemplate()
})

function buildRelativeDatePreview(months) {
  const safeMonths = Math.min(Math.max(Number(months) || 0, 1), 120)
  const start = new Date()
  const end = addMonths(start, safeMonths)
  return {
    start: formatDate(start),
    end: formatDate(end)
  }
}

function addMonths(baseDate, months) {
  const year = baseDate.getFullYear()
  const monthIndex = baseDate.getMonth()
  const day = baseDate.getDate()
  const totalMonthIndex = monthIndex + months
  const targetYear = year + Math.floor(totalMonthIndex / 12)
  const targetMonthIndex = totalMonthIndex % 12
  const lastDay = new Date(targetYear, targetMonthIndex + 1, 0).getDate()
  return new Date(targetYear, targetMonthIndex, Math.min(day, lastDay))
}

function formatDate(value) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
</script>
