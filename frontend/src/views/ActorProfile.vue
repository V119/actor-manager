<template>
  <div class="flex-1 pt-24 px-8 pb-12 overflow-y-auto bg-background text-on-surface">
    <div class="max-w-7xl mx-auto space-y-8">
      <div v-if="loading" class="text-sm text-on-surface-variant">正在加载演员已发布信息...</div>
      <div v-else-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</div>

      <template v-else-if="detail">
        <section class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 p-6 rounded-xl">
          <div class="flex flex-col md:flex-row gap-6 items-start">
            <div class="w-40 h-52 rounded-xl overflow-hidden border border-sky-300/20 bg-slate-950/30">
              <img :src="coverImage" :alt="detail.actor.name" class="w-full h-full object-cover" />
            </div>
            <div class="space-y-3">
              <h1 class="text-3xl font-bold text-on-surface">{{ detail.actor.name }}</h1>
              <p class="text-xs text-on-surface-variant">ID: {{ detail.actor.external_id }}</p>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="tag in detail.actor.tags"
                  :key="tag"
                  class="px-2.5 py-0.5 text-[10px] font-semibold rounded bg-sky-400/10 text-sky-300 border border-sky-400/20"
                >
                  {{ tag }}
                </span>
              </div>
              <p class="text-sm text-on-surface-variant max-w-3xl">{{ detail.actor.bio }}</p>
            </div>
          </div>
        </section>

        <section class="grid lg:grid-cols-2 gap-6">
          <div class="bg-surface/60 border border-emerald-300/20 rounded-xl p-4">
            <h2 class="text-lg font-semibold mb-3">已发布三视图</h2>
            <div v-if="detail.published_three_view" class="space-y-4">
              <div class="aspect-[4/3] rounded-lg overflow-hidden border border-emerald-300/20">
                <img
                  :src="detail.published_three_view.composite_preview_url"
                  alt="已发布三视图"
                  class="w-full h-full object-cover"
                />
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div
                  v-for="img in detail.published_three_view.raw_images"
                  :key="img.id"
                  class="aspect-[9/16] rounded-lg overflow-hidden border border-sky-300/20"
                >
                  <img :src="img.preview_url" :alt="img.view_angle" class="w-full h-full object-cover" />
                </div>
              </div>
            </div>
            <div v-else class="text-xs text-on-surface-variant">暂无已发布三视图。</div>
          </div>

          <div class="bg-surface/60 border border-emerald-300/20 rounded-xl p-4">
            <h2 class="text-lg font-semibold mb-3">已发布视频</h2>
            <div v-if="publishedVideos.length" class="space-y-4">
              <div
                v-for="video in publishedVideos"
                :key="video.id"
                class="rounded-lg border border-emerald-300/20 bg-slate-950/20 p-3 space-y-2"
              >
                <p class="text-xs font-semibold text-emerald-200">
                  {{ videoLabelMap[video.video_type] || '已发布视频' }}
                </p>
                <video :src="video.preview_url" controls class="w-full rounded-lg border border-emerald-300/20" />
              </div>
            </div>
            <div v-else class="text-xs text-on-surface-variant">暂无已发布视频。</div>
          </div>
        </section>

        <section class="bg-surface/60 border border-emerald-300/20 rounded-xl p-4">
          <h2 class="text-lg font-semibold mb-3">已发布风格图</h2>
          <div v-if="detail.published_styles?.length" class="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
            <div
              v-for="item in detail.published_styles"
              :key="item.id"
              class="break-inside-avoid rounded-lg overflow-hidden border border-emerald-300/20"
            >
              <img :src="item.preview_url || item.image_url" :alt="item.style_name" class="w-full h-auto" />
            </div>
          </div>
          <div v-else class="text-xs text-on-surface-variant">暂无已发布风格图。</div>
        </section>

        <section class="bg-surface/60 border border-emerald-300/20 rounded-xl p-4">
          <h2 class="text-lg font-semibold mb-3">已发布录音</h2>
          <div v-if="publishedAudios.length" class="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div
              v-for="audio in publishedAudios"
              :key="audio.id"
              class="rounded-lg border border-emerald-300/20 bg-slate-950/20 p-3 space-y-2"
            >
              <p class="text-xs font-semibold text-emerald-200 truncate">
                {{ audio.source_filename || '已发布录音' }}
              </p>
              <audio :src="audio.preview_url" controls class="w-full" preload="metadata" />
            </div>
          </div>
          <div v-else class="text-xs text-on-surface-variant">暂无已发布录音。</div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const route = useRoute()
const loading = ref(false)
const errorMessage = ref('')
const detail = ref(null)
const videoLabelMap = {
  intro: '真人自我介绍',
  showreel: '妆造风格/演戏混剪'
}

const fallbackCover = 'https://lh3.googleusercontent.com/aida-public/AB6AXuD9xOeWWM-jWAGILA81XqH26NeDYHoqtGJWE9brsTAGIiWw7kgjEJmhS9d25ZDEFQybXpSuk9M_jCEvPBHtXPid3MZ5GZKW2JezdodqzKL0BgEEX6Hj4IlvV5mgXkbks3cx4bd8E19xJxVGT1tENU9rYe3gtZ2xAs7dkwy2hkTeuysJ7qzuM90wWoIhgFKDYdLY5ylh0wX45zCP4PKhlDQBAr0mu0zk4x0jVLSNsJZAacfBelDO38vlM_4rieH1BZ0uq7nQpgs-BsoA'

const publishedVideos = computed(() => {
  const list = Array.isArray(detail.value?.published_videos)
    ? detail.value.published_videos
    : (detail.value?.published_video ? [detail.value.published_video] : [])
  const order = { intro: 0, showreel: 1 }
  return [...list].sort((a, b) => (order[a.video_type] ?? 99) - (order[b.video_type] ?? 99))
})

const publishedAudios = computed(() => {
  const list = Array.isArray(detail.value?.published_audios)
    ? detail.value.published_audios
    : []
  return [...list].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
})

const coverImage = computed(() => {
  if (detail.value?.published_styles?.length) {
    return detail.value.published_styles[0].preview_url || detail.value.published_styles[0].image_url
  }
  if (detail.value?.published_three_view?.composite_preview_url) {
    return detail.value.published_three_view.composite_preview_url
  }
  if (publishedVideos.value.length) {
    return publishedVideos.value[0].preview_url || fallbackCover
  }
  return fallbackCover
})

async function loadDetail() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  try {
    const actorId = Number(route.params.id)
    const payload = await apiRequest(`/enterprise/discovery/actors/${actorId}`, {
      token: authStore.state.token
    })
    detail.value = payload
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '演员详情加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDetail()
})
</script>
