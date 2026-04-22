<template>
  <div class="min-h-screen bg-background text-on-surface">
    <main class="max-w-5xl mx-auto px-6 md:px-8 pt-24 pb-14 space-y-8">
      <header class="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold tracking-tight">企业基本信息</h1>
          <p class="mt-2 text-sm text-on-surface-variant">
            单独维护企业资料。企业登录协议弹窗会展示协议全文，广场与签约模块使用这里的企业资料。
          </p>
        </div>
        <div class="text-xs text-on-surface-variant">
          资料完整度：<span class="font-semibold text-moss-300">{{ completionPercentage }}%</span>
        </div>
      </header>

      <section class="rounded-2xl border border-moss-400/10 bg-surface/65 p-5 md:p-6 backdrop-blur-xl">
        <div class="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div class="flex items-center gap-4">
            <div class="flex h-16 w-16 items-center justify-center rounded-2xl border border-moss-300/20 bg-moss-400/10 text-xl font-semibold text-moss-200">
              {{ companyInitial }}
            </div>
            <div>
              <p class="text-sm font-semibold text-moss-100">{{ form.company_name || '未填写企业名称' }}</p>
              <p class="mt-1 text-xs leading-6 text-on-surface-variant">
                {{
                  isReadyForAgreement
                    ? '企业资料已准备完成。'
                    : '请先补全企业名称、统一社会信用代码和注册地址。'
                }}
              </p>
            </div>
          </div>

          <div
            class="rounded-2xl border px-4 py-3 text-sm"
            :class="isReadyForAgreement ? 'border-sage-400/20 bg-sage-500/10 text-sage-200' : 'border-brass-400/20 bg-brass-500/10 text-brass-100'"
          >
            {{ isReadyForAgreement ? '已满足企业资料要求' : '还有必填信息待完善' }}
          </div>
        </div>
      </section>

      <section v-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        {{ errorMessage }}
      </section>
      <section v-if="successMessage" class="rounded-2xl border border-sage-400/20 bg-sage-500/10 px-4 py-3 text-sm text-sage-200">
        {{ successMessage }}
      </section>

      <section v-if="loading" class="rounded-2xl border border-moss-400/10 bg-surface/50 p-8 text-sm text-on-surface-variant">
        正在加载企业基本信息...
      </section>

      <form v-else class="space-y-6" @submit.prevent="saveBasicInfo">
        <section class="rounded-2xl border border-moss-400/10 bg-surface/65 p-5 md:p-6 backdrop-blur-xl space-y-4">
          <h2 class="text-lg font-semibold">企业资料</h2>
          <div class="grid md:grid-cols-2 gap-4">
            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">企业名称</span>
              <input
                v-model="form.company_name"
                type="text"
                maxlength="64"
                class="w-full rounded-lg border bg-ink-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-moss-300/50"
                :class="fieldErrors.company_name ? 'border-rose-300/50' : 'border-moss-300/20'"
                placeholder="请输入企业全称"
              />
              <p v-if="fieldErrors.company_name" class="text-xs text-rose-300">{{ fieldErrors.company_name }}</p>
            </label>

            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">统一社会信用代码</span>
              <input
                v-model="form.credit_code"
                type="text"
                maxlength="64"
                class="w-full rounded-lg border bg-ink-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-moss-300/50"
                :class="fieldErrors.credit_code ? 'border-rose-300/50' : 'border-moss-300/20'"
                placeholder="请输入统一社会信用代码"
              />
              <p v-if="fieldErrors.credit_code" class="text-xs text-rose-300">{{ fieldErrors.credit_code }}</p>
            </label>

            <label class="space-y-1 md:col-span-2">
              <span class="text-xs text-on-surface-variant">企业简介</span>
              <textarea
                v-model="form.company_intro"
                rows="4"
                maxlength="4000"
                class="w-full rounded-lg border border-moss-300/20 bg-ink-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-moss-300/50"
                placeholder="介绍企业业务方向、合作偏好或品牌背景"
              ></textarea>
            </label>

            <label class="space-y-1 md:col-span-2">
              <span class="text-xs text-on-surface-variant">注册地址</span>
              <textarea
                v-model="form.registered_address"
                rows="4"
                maxlength="512"
                class="w-full rounded-lg border bg-ink-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-moss-300/50"
                :class="fieldErrors.registered_address ? 'border-rose-300/50' : 'border-moss-300/20'"
                placeholder="请输入企业注册地址"
              ></textarea>
              <p v-if="fieldErrors.registered_address" class="text-xs text-rose-300">{{ fieldErrors.registered_address }}</p>
            </label>
          </div>
        </section>

        <section class="rounded-2xl border border-moss-400/10 bg-surface/65 p-5 md:p-6 backdrop-blur-xl">
          <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 class="text-lg font-semibold">保存资料</h2>
              <p class="mt-1 text-sm leading-6 text-on-surface-variant">
                保存后，企业登录后可直接访问演员发布广场与签约演员。
              </p>
            </div>

            <div class="flex flex-wrap gap-3">
              <button
                type="submit"
                :disabled="saving"
                class="rounded-lg bg-moss-400 px-5 py-2.5 text-sm font-semibold text-ink-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {{ saving ? '保存中...' : '保存基本信息' }}
              </button>
            </div>
          </div>
        </section>
      </form>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const form = reactive({
  company_name: '',
  company_intro: '',
  credit_code: '',
  registered_address: ''
})

const fieldErrors = reactive({
  company_name: '',
  credit_code: '',
  registered_address: ''
})

const completionPercentage = computed(() => {
  const values = [
    form.company_name,
    form.company_intro,
    form.credit_code,
    form.registered_address
  ]
  const completed = values.filter((item) => String(item || '').trim()).length
  return Math.round((completed / values.length) * 100)
})

const isReadyForAgreement = computed(() => (
  Boolean(form.company_name.trim())
  && Boolean(form.credit_code.trim())
  && Boolean(form.registered_address.trim())
))

const companyInitial = computed(() => {
  const value = form.company_name.trim() || authStore.state.user?.display_name || '企'
  return value.slice(0, 1).toUpperCase()
})

function resetMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function resetFieldErrors() {
  fieldErrors.company_name = ''
  fieldErrors.credit_code = ''
  fieldErrors.registered_address = ''
}

function syncForm(payload) {
  form.company_name = payload?.company_name || authStore.state.user?.display_name || ''
  form.company_intro = payload?.company_intro || authStore.state.user?.company_intro || ''
  form.credit_code = payload?.credit_code || ''
  form.registered_address = payload?.registered_address || ''
}

function applyFieldErrors(errors = {}) {
  resetFieldErrors()
  fieldErrors.company_name = errors.company_name || ''
  fieldErrors.credit_code = errors.credit_code || ''
  fieldErrors.registered_address = errors.registered_address || ''
}

function validateForm() {
  resetFieldErrors()
  let valid = true
  if (!form.company_name.trim()) {
    fieldErrors.company_name = '请填写企业名称。'
    valid = false
  }
  if (!form.credit_code.trim()) {
    fieldErrors.credit_code = '请填写统一社会信用代码。'
    valid = false
  }
  if (!form.registered_address.trim()) {
    fieldErrors.registered_address = '请填写注册地址。'
    valid = false
  }
  return valid
}

async function loadBasicInfo() {
  if (!authStore.state.token) return
  loading.value = true
  resetMessages()
  resetFieldErrors()
  try {
    const payload = await apiRequest('/enterprise/basic-info', { token: authStore.state.token })
    syncForm(payload)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '企业基本信息加载失败'
  } finally {
    loading.value = false
  }
}

async function saveBasicInfo() {
  if (!authStore.state.token) return
  resetMessages()
  if (!validateForm()) {
    errorMessage.value = '请先补全企业基本信息中的必填项。'
    return
  }

  saving.value = true
  try {
    const payload = await apiRequest('/enterprise/basic-info', {
      method: 'PUT',
      token: authStore.state.token,
      body: {
        company_name: form.company_name.trim(),
        company_intro: form.company_intro.trim(),
        credit_code: form.credit_code.trim(),
        registered_address: form.registered_address.trim()
      }
    })
    syncForm(payload)
    if (authStore.state.user) {
      authStore.state.user.display_name = payload.company_name || authStore.state.user.display_name
      authStore.state.user.company_intro = payload.company_intro || ''
    }
    successMessage.value = '企业基本信息已保存。'
  } catch (error) {
    const detail = error && typeof error === 'object' ? error.detail : null
    const nextFieldErrors = detail && typeof detail === 'object' ? detail.field_errors : null
    if (nextFieldErrors) {
      applyFieldErrors(nextFieldErrors)
    }
    errorMessage.value = error instanceof Error ? error.message : '企业基本信息保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadBasicInfo()
})
</script>
