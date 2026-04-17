<template>
  <div class="flex-1 overflow-y-auto bg-background px-8 pt-24 pb-12 min-h-screen text-on-surface">
    <div class="max-w-5xl mx-auto space-y-6">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-full border border-sky-300/20 bg-surface/40 px-4 py-2 text-sm text-sky-100 transition hover:bg-sky-400/10"
        @click="goBack"
      >
        <span class="material-symbols-outlined text-base">arrow_back</span>
        返回签约企业
      </button>

      <div v-if="loading" class="text-sm text-on-surface-variant">正在加载企业详情...</div>
      <div v-else-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        {{ errorMessage }}
      </div>

      <template v-else-if="enterprise">
        <section class="rounded-2xl border border-sky-400/10 bg-surface/60 p-6 backdrop-blur-xl">
          <div class="flex flex-col md:flex-row gap-5 md:items-start md:justify-between">
            <div>
              <p class="text-xs tracking-[0.18em] uppercase text-slate-400">签约企业</p>
              <h1 class="mt-3 text-3xl font-bold tracking-tight">{{ enterprise.company_name }}</h1>
              <p class="mt-3 max-w-3xl text-sm leading-7 text-on-surface-variant whitespace-pre-wrap">
                {{ enterprise.company_intro || '该企业暂未填写企业简介。' }}
              </p>
            </div>
            <div class="rounded-2xl border border-emerald-300/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
              签约时间：{{ formatDateTime(enterprise.signed_at) }}
            </div>
          </div>
        </section>

        <section class="grid md:grid-cols-2 gap-4">
          <div
            v-for="item in infoItems"
            :key="item.label"
            class="rounded-2xl border border-sky-400/10 bg-surface/50 px-5 py-4"
          >
            <p class="text-[11px] tracking-[0.16em] uppercase text-slate-400">{{ item.label }}</p>
            <p class="mt-2 text-sm leading-7 break-words text-sky-50 whitespace-pre-wrap">{{ item.value }}</p>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const enterprise = ref(null)

const infoItems = computed(() => {
  if (!enterprise.value) return []
  return [
    { label: '统一社会信用代码', value: enterprise.value.credit_code || '未填写' },
    { label: '注册地址', value: enterprise.value.registered_address || '未填写' },
    { label: '企业创建时间', value: formatDateTime(enterprise.value.created_at) },
    { label: '签约时间', value: formatDateTime(enterprise.value.signed_at) }
  ]
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

async function goBack() {
  await router.push('/actor-signed-enterprises')
}

async function loadEnterpriseDetail() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  try {
    const enterpriseUserId = Number(route.params.enterpriseUserId)
    const payload = await apiRequest(`/actors/me/signed-enterprises/${enterpriseUserId}`, {
      token: authStore.state.token
    })
    enterprise.value = payload
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '企业详情加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadEnterpriseDetail()
})
</script>
