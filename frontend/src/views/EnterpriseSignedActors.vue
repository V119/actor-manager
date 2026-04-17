<template>
  <div class="flex-1 overflow-y-auto bg-background p-8 pt-24 min-h-screen">
    <div class="max-w-7xl mx-auto">
      <section class="mb-8 space-y-4">
        <div class="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold tracking-tight text-on-surface">签约演员</h1>
            <p class="mt-2 text-sm text-on-surface-variant">
              这里展示当前企业已签约的全部演员，可点击继续查看演员详情。
            </p>
          </div>
          <div class="relative w-full md:w-96 group">
            <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">search</span>
            <input
              v-model.trim="keyword"
              class="w-full bg-surface/40 border border-sky-400/10 rounded-full py-3 pl-12 pr-6 text-on-surface placeholder:text-slate-500 focus:outline-none focus:border-sky-400/40 focus:ring-1 focus:ring-sky-400/40 transition-all backdrop-blur-sm"
              placeholder="搜索签约演员"
              type="text"
            />
          </div>
        </div>
      </section>

      <div v-if="loading" class="text-sm text-on-surface-variant">正在加载签约演员...</div>
      <div v-else-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</div>
      <div v-else-if="!filteredActors.length" class="rounded-2xl border border-sky-400/10 bg-surface/40 px-5 py-8 text-sm text-on-surface-variant">
        当前还没有签约演员，去演员发布广场挑选合适的演员后即可在这里查看。
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <button
          v-for="actor in filteredActors"
          :key="`${actor.actor_id}-${actor.signed_at}`"
          type="button"
          class="bg-surface/40 backdrop-blur-md border border-sky-400/10 rounded-xl overflow-hidden flex flex-col group hover:border-sky-400/30 hover:translate-y-[-4px] transition-all duration-300 text-left"
          @click="openActor(actor.actor_id)"
        >
          <div class="relative aspect-[3/4] overflow-hidden">
            <img
              :src="actor.cover_image_url || fallbackCover"
              :alt="actor.name"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            >
            <div class="absolute top-3 right-3 bg-slate-950/50 backdrop-blur-md px-3 py-1 rounded-full border border-emerald-300/20">
              <span class="text-[10px] font-bold text-emerald-300 tracking-wider">已签约</span>
            </div>
          </div>
          <div class="p-5 flex flex-col gap-3">
            <div>
              <h3 class="text-lg font-bold text-on-surface tracking-tight">{{ actor.name }}</h3>
              <p class="text-xs text-on-surface-variant">ID: {{ actor.external_id }}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in actor.tags"
                :key="tag"
                class="px-2.5 py-0.5 text-[10px] font-semibold rounded bg-sky-400/10 text-sky-300 border border-sky-400/20"
              >
                {{ tag }}
              </span>
            </div>
            <div class="space-y-1 text-xs text-on-surface-variant">
              <p>签约时间：{{ formatDateTime(actor.signed_at) }}</p>
              <p>风格图 {{ actor.published_style_count }} 张 · 录音 {{ actor.published_audio_count || 0 }} 条</p>
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
import {
  ENTERPRISE_DISCOVERY_BLOCKED_NOTICE,
  buildEnterpriseAgreementRoute,
  ensureEnterpriseAgreementSigned,
  isEnterpriseAgreementBlockingErrorMessage
} from '../lib/enterpriseAgreement'

const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const keyword = ref('')
const actors = ref([])

const fallbackCover = 'https://lh3.googleusercontent.com/aida-public/AB6AXuAVVe-CtMV2MaDhQFqCqhT0Kq3vK0DdMpbbcopsBD74Aa_yD1LLlqUuXM_O3I8k1QqbmJ6h1VubQKb-nE6lBOZZg051RojR5PCKCOtusVOVgT1bULA-OWObZR7xb52BIG0ljeQRCPEZpLRAmtsu69tw651Alu5vevpRgXESgInA4xVdb40JSLWw7FhrSd1CKBSZVEkkUTP-UopBxt6QBOw5kMK0Kf9Y-nDKVSpDVvOaN2bttCdc9GIZBzLK_ijlNrqBqe4pYn9qmnNT'

const filteredActors = computed(() => {
  const query = keyword.value.toLowerCase()
  if (!query) return actors.value
  return actors.value.filter((item) => {
    const name = String(item.name || '').toLowerCase()
    const external = String(item.external_id || '').toLowerCase()
    const tags = Array.isArray(item.tags) ? item.tags.join(',').toLowerCase() : ''
    return name.includes(query) || external.includes(query) || tags.includes(query)
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

function openActor(actorId) {
  router.push(`/actor/${actorId}`)
}

async function loadActors() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  try {
    const agreementResult = await ensureEnterpriseAgreementSigned({
      token: authStore.state.token,
      router,
      blockedNotice: ENTERPRISE_DISCOVERY_BLOCKED_NOTICE,
      onBlocked: (message) => {
        errorMessage.value = message
      }
    })
    if (!agreementResult.allowed) {
      actors.value = []
      return
    }
    const payload = await apiRequest('/enterprise/signed-actors', {
      token: authStore.state.token
    })
    actors.value = Array.isArray(payload) ? payload : []
  } catch (error) {
    const nextMessage = error instanceof Error ? error.message : '签约演员加载失败，请稍后重试。'
    errorMessage.value = nextMessage
    if (isEnterpriseAgreementBlockingErrorMessage(nextMessage)) {
      await router.push(buildEnterpriseAgreementRoute(ENTERPRISE_DISCOVERY_BLOCKED_NOTICE))
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadActors()
})
</script>
