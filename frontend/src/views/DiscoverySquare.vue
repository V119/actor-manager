<template>
  <div class="flex-1 overflow-y-auto bg-background p-8 pt-24 min-h-screen">
    <div class="max-w-7xl mx-auto">
      <section class="mb-8 space-y-4">
        <div class="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div class="relative w-full md:w-96 group">
            <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">search</span>
            <input
              v-model.trim="keyword"
              class="w-full bg-surface/40 border border-sky-400/10 rounded-full py-3 pl-12 pr-6 text-on-surface placeholder:text-slate-500 focus:outline-none focus:border-sky-400/40 focus:ring-1 focus:ring-sky-400/40 transition-all backdrop-blur-sm"
              placeholder="搜索已发布演员"
              type="text"
            />
          </div>
          <div class="text-sm text-slate-400">已发布演员：{{ filteredActors.length }}</div>
        </div>
      </section>

      <div v-if="loading" class="text-sm text-on-surface-variant">正在加载已发布演员...</div>
      <div v-else-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</div>
      <div v-else-if="!filteredActors.length" class="text-sm text-on-surface-variant">暂无已发布演员。</div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <button
          v-for="actor in filteredActors"
          :key="actor.actor_id"
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
            <div class="absolute top-3 right-3 bg-slate-950/40 backdrop-blur-md px-3 py-1 rounded-full border border-sky-400/20 flex items-center gap-1.5">
              <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
              <span class="text-[10px] font-bold text-emerald-400 tracking-wider">已发布</span>
            </div>
          </div>
          <div class="p-5 flex flex-col gap-3">
            <div>
              <h3 class="text-lg font-bold text-on-surface tracking-tight">{{ actor.name }}</h3>
              <p class="text-xs text-on-surface-variant">ID: {{ actor.external_id }}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="t in actor.tags"
                :key="t"
                class="px-2.5 py-0.5 text-[10px] font-semibold rounded bg-sky-400/10 text-sky-300 border border-sky-400/20"
              >
                {{ t }}
              </span>
            </div>
            <div class="text-xs text-on-surface-variant">
              已发布风格图 {{ actor.published_style_count }} 张 · 录音 {{ actor.published_audio_count || 0 }} 条
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
import { ensureEnterpriseAgreementSigned, isEnterpriseAgreementBlockingErrorMessage } from '../lib/enterpriseAgreement'

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
      onBlocked: (message) => {
        errorMessage.value = message
      }
    })
    if (!agreementResult.allowed) {
      actors.value = []
      return
    }
    const payload = await apiRequest('/enterprise/discovery/actors', {
      token: authStore.state.token
    })
    actors.value = Array.isArray(payload) ? payload : []
  } catch (error) {
    const nextMessage = error instanceof Error ? error.message : '广场数据加载失败，请稍后重试。'
    errorMessage.value = nextMessage
    if (isEnterpriseAgreementBlockingErrorMessage(nextMessage)) {
      await router.push('/enterprise-agreement')
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadActors()
})
</script>
