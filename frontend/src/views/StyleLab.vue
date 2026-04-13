<template>
  <div class="min-h-screen bg-background text-on-surface relative overflow-y-auto pt-24 px-8 pb-12 space-y-10">
    <section>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-semibold text-primary uppercase tracking-widest flex items-center gap-2">
          <span class="w-1.5 h-1.5 bg-primary rounded-full"></span>
          已发布基础照
        </h3>
        <button
          class="text-xs text-on-surface-variant hover:text-primary transition-colors flex items-center gap-1"
          @click="goToPortraitUpload"
        >
          <span class="material-symbols-outlined text-base">add_circle</span>
          管理肖像
        </button>
      </div>
      <p class="text-xs text-on-surface-variant mb-4">
        风格生成将使用你当前账号已发布的左侧面、正面、右侧面基础照。
      </p>

      <div v-if="loadingBasePhotos" class="text-sm text-on-surface-variant">正在加载基础照...</div>
      <div
        v-else-if="basePhotoSlots.length"
        class="flex gap-4 overflow-x-auto pb-3 -mx-2 px-2"
      >
        <div
          v-for="item in basePhotoSlots"
          :key="item.view_angle"
          class="flex-shrink-0 w-44 h-56 rounded-xl bg-surface/60 backdrop-blur-xl border border-sky-400/10 p-1.5"
        >
          <div class="w-full h-full rounded-lg overflow-hidden bg-slate-950/30 relative">
            <img :src="item.preview_url" :alt="item.label" class="w-full h-full object-cover" />
            <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/80 to-transparent px-2 py-1.5">
              <p class="text-[11px] text-sky-100 font-medium">{{ item.label }}</p>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="rounded-xl border border-dashed border-sky-300/25 bg-slate-950/20 p-6 text-sm text-on-surface-variant">
        暂无已发布基础照，请先在“肖像上传”中上传并发布左侧面、正面、右侧面三张照片。
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-primary uppercase tracking-widest flex items-center gap-2 mb-4">
        <span class="w-1.5 h-1.5 bg-primary rounded-full"></span>
        选择视觉风格
      </h3>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <button
          v-for="style in styleCards"
          :key="style.name"
          type="button"
          class="group cursor-pointer relative overflow-hidden rounded-2xl bg-surface/60 backdrop-blur-xl border p-2 transition-all duration-300 text-left"
          :class="selectedStyleId === style.id ? 'border-sky-300/80 shadow-[0_0_24px_rgba(125,211,252,0.28)]' : 'border-sky-400/10 hover:border-primary/40'"
          :disabled="!style.id"
          @click="selectStyle(style)"
        >
          <div class="aspect-[3/4] rounded-xl overflow-hidden mb-3 relative">
            <img :src="style.preview_url" :alt="style.name" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
            <div class="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent opacity-60"></div>
          </div>
          <div class="px-2 pb-2">
            <p class="text-sm font-bold text-on-surface">{{ style.name }}</p>
            <p class="text-[10px] text-on-surface-variant">{{ style.en }}</p>
          </div>
          <div v-if="!style.id" class="absolute inset-0 bg-slate-950/55 flex items-center justify-center text-xs text-slate-200">
            暂不可用
          </div>
        </button>
      </div>
    </section>

    <section class="flex flex-col items-center py-2">
      <button
        class="relative group px-12 py-4 bg-primary/20 rounded-full border border-primary/50 text-primary font-bold text-lg flex items-center gap-3 transition-all duration-300 hover:bg-primary/30 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
        :disabled="generating || !selectedStyleId || !hasBasePhotos"
        @click="generateStyle"
      >
        <span class="material-symbols-outlined text-2xl" style="font-variation-settings: 'FILL' 1;">auto_fix_high</span>
        {{ generating ? '生成中...' : '开始生成' }}
      </button>
      <p class="text-xs text-on-surface-variant mt-4">预计耗时 15-30 秒，基于你已发布的基础照生成</p>
      <p v-if="errorMessage" class="text-sm text-rose-300 mt-3">{{ errorMessage }}</p>
      <p v-if="successMessage" class="text-sm text-emerald-300 mt-3">{{ successMessage }}</p>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-primary uppercase tracking-widest flex items-center gap-2 mb-6">
        <span class="w-1.5 h-1.5 bg-primary rounded-full"></span>
        最终生成效果图
      </h3>

      <div class="space-y-8">
        <div
          v-for="group in groupedDisplay"
          :key="group.name"
          class="rounded-2xl border border-sky-400/10 bg-surface/55 backdrop-blur-xl p-4"
        >
          <div class="mb-4 flex items-center justify-between">
            <div>
              <h4 class="text-base font-semibold text-sky-100">{{ group.name }}</h4>
              <p class="text-xs text-on-surface-variant">{{ group.en }}</p>
            </div>
            <button
              class="px-3 py-1.5 rounded-md border border-emerald-300/40 text-xs text-emerald-200 hover:bg-emerald-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
              :disabled="!group.draft_result || publishingStyleId === group.style_id"
              @click="publishStyleDraft(group.style_id)"
            >
              {{ publishingStyleId === group.style_id ? '发布中...' : '发布该风格草稿' }}
            </button>
          </div>

          <div class="grid md:grid-cols-2 gap-4">
            <div class="rounded-xl border border-sky-300/20 bg-slate-950/25 p-3">
              <p class="text-xs text-sky-200 mb-2">草稿（未发布）</p>
              <div v-if="group.draft_result" class="rounded-lg overflow-hidden border border-sky-300/15">
                <img :src="group.draft_result.preview_url || group.draft_result.image_url" :alt="`${group.name} 草稿`" class="w-full h-auto" />
              </div>
              <div v-else class="text-xs text-on-surface-variant py-6 text-center">暂无草稿</div>
            </div>

            <div class="rounded-xl border border-emerald-300/25 bg-slate-950/25 p-3">
              <p class="text-xs text-emerald-200 mb-2">已发布</p>
              <div v-if="group.published_result" class="rounded-lg overflow-hidden border border-emerald-300/20">
                <img :src="group.published_result.preview_url || group.published_result.image_url" :alt="`${group.name} 已发布`" class="w-full h-auto" />
              </div>
              <div v-else class="text-xs text-on-surface-variant py-6 text-center">暂无已发布内容</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const router = useRouter()

const STYLE_DEFINITIONS = [
  {
    name: '古装魅影',
    en: 'Historical & Epic',
    category: 'cinematic',
    preview_url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD00KMgUb0Pckf9vLFC8_RU4BlI3xMCYS05fAaxWQombg-8VnMusIk_SfJCNs51mZ7SxuBB85MYyuA8HkAHVqxgrls1VSCnliNKV_377DH5AI-D8FhjE_E-5n2mjFG_AJibwqJwE2kd6Vf4N_jZleRfUW-1gYLBx-UyetLcO_tx-y0tnfy2KMRYN7gWapcZ2Kje906S1MO9pTNC3eiAxYAyGEmEDSvwdWsyU7Lw4x6L9NFSbPALwLofjPmBk-mPKtGWndQL4XLSDduj'
  },
  {
    name: '现代极简',
    en: 'Modern Minimal',
    category: 'commercial',
    preview_url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCCZs5TPGFVy7JxseOoRpt8ezORT4adYH1cLjLsfp5HwenWR0EAzvRjQR22wI00LqEbbaqgGEwUtgeEcKoBAtPUwM_dtJiibusH0TJNBU30sYtrvL40xAqi-Ns0c7JLTOV3h72DXvX6Toa22BbBPgoLiTJinqUdqbV99A7QQCry8kajB7T_Va_xaPcJtSlgEhwhJ545kIY4-tCXPMzNs9VZ5Uwqkchx2O96uByo3QsrVZrypve84zqpWcUXqELIEha4NgOjby9qGD7N'
  },
  {
    name: '科幻纪元',
    en: 'Sci-Fi Future',
    category: 'sci-fi',
    preview_url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC7z6PepGrJ0qBZXFAYCy4QFm1wBJZdCOwQCHYnedhZNDcAvQNL4iGlLWGD-tXGIvRQ4RNyEcHcFte2alc8rvInBo2OHqY-XQqyL5hi55R-cqeBUjQReBS18zlAGWumtnG9no_Ltj4CajfiTZ-q388miAWEewFK3PlYjQrYWkj_gTJBLiTShCSSxv9gbyKHWuHIqy6CcJKQ46FHVfRL8GFzafZ7EKhnIX7fo_0sNsgV7ahhNP5Cq9QrsloDNf9fibTGk5NiIMFOCFzI'
  },
  {
    name: '黑色电影',
    en: 'Classic Noir',
    category: 'noir',
    preview_url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAiMkiCMGfe655OOompjW1VvTAU0RU3YE8YjQmjzszegWx9nORlWnhZ2Z0Tp_Dp4sxZbX9ZSJfSZOUp4CErcsW2P3p8OdO9Lb3znojkfBDi2h28Hp3low-6kaHCwW8KAS9sesuve6UHV1ihr6h8a3pRcwGht0Vy8ZN5VCrNGbX2lzA6DWpSf_wHKRx0iC6O5MRYRuHwVTB6M-bSkJa0EDkI8af9KgR0QtR969HHnFC4ajnKR1joR43QaVgFaUY2GKyThGWLF2dYU_E1'
  },
  {
    name: '油画质感',
    en: 'Oil Painting',
    category: 'oil-painting',
    preview_url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC9ipTxbm-qu6iG2QPAj3nqp4AOHKOW90w-SWgTR1EcK5dwWhFfyX8PJQPzY-B0OfbKxN2sgUtQJqqMKBXbUdMqUoBsQ9VeRE6gkRhc7fkFOz4sxTTopU3Dz1QFbGH05fD8X4y0PqFzcZxDo2LdCx-B4szCAnJHuUosFvTXKctdMun_ymrRWle9pKy63DTN_3mXGJQgmR4JcALzmtYRg8egVqJuPHExwmfjx31EOZvUgNbJvYcNahq54dK1nka59YiPX9SzSsrLJ4RE'
  }
]

const stylesFromApi = ref([])
const styleGroups = ref([])
const publishedThreeView = ref(null)

const selectedStyleId = ref(null)
const generating = ref(false)
const publishingStyleId = ref(null)
const loadingBasePhotos = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const basePhotoSession = computed(() => publishedThreeView.value || null)
const hasBasePhotos = computed(() => {
  const rawImages = Array.isArray(basePhotoSession.value?.raw_images) ? basePhotoSession.value.raw_images : []
  const angleSet = new Set(rawImages.map((item) => item.view_angle))
  return angleSet.has('left') && angleSet.has('front') && angleSet.has('right')
})

const basePhotoSlots = computed(() => {
  const rawImages = Array.isArray(basePhotoSession.value?.raw_images) ? basePhotoSession.value.raw_images : []
  const byAngle = {}
  rawImages.forEach((item) => {
    byAngle[item.view_angle] = item
  })
  return [
    { view_angle: 'left', label: '左侧面图', preview_url: byAngle.left?.preview_url || '' },
    { view_angle: 'front', label: '正面图', preview_url: byAngle.front?.preview_url || '' },
    { view_angle: 'right', label: '右侧面图', preview_url: byAngle.right?.preview_url || '' }
  ].filter((item) => Boolean(item.preview_url))
})

const styleCards = computed(() => {
  const backendStyles = Array.isArray(stylesFromApi.value) ? stylesFromApi.value : []
  return STYLE_DEFINITIONS.map((fallback) => {
    const matched = backendStyles.find((item) => item.name === fallback.name)
      || backendStyles.find((item) => item.category === fallback.category)

    return {
      ...fallback,
      id: matched?.id || null,
      description: matched?.description || ''
    }
  })
})

const groupedDisplay = computed(() => {
  const groupMap = new Map()
  const groups = Array.isArray(styleGroups.value) ? styleGroups.value : []
  groups.forEach((group) => {
    groupMap.set(group.style_name, group)
  })

  const cardMap = new Map(styleCards.value.map((item) => [item.name, item]))
  return STYLE_DEFINITIONS.map((style) => {
    const group = groupMap.get(style.name) || {}
    return {
      style_id: group.style_id || cardMap.get(style.name)?.id || null,
      name: style.name,
      en: style.en,
      draft_result: group.draft_result || null,
      published_result: group.published_result || null
    }
  })
})

function selectStyle(style) {
  if (!style?.id) return
  selectedStyleId.value = style.id
  errorMessage.value = ''
}

function goToPortraitUpload() {
  router.push('/edit-portrait')
}

async function loadStyles() {
  const payload = await apiRequest('/styles', { token: authStore.state.token })
  stylesFromApi.value = Array.isArray(payload) ? payload : []

  if (!selectedStyleId.value) {
    const first = styleCards.value.find((item) => Boolean(item.id))
    if (first) {
      selectedStyleId.value = first.id
    }
  }
}

async function loadCurrentThreeView() {
  loadingBasePhotos.value = true
  try {
    const payload = await apiRequest('/portraits/three-view/state', { token: authStore.state.token })
    publishedThreeView.value = payload?.published || null
  } finally {
    loadingBasePhotos.value = false
  }
}

async function loadStyleResults() {
  const payload = await apiRequest('/styles/results?limit_per_style=20', { token: authStore.state.token })
  styleGroups.value = Array.isArray(payload?.groups) ? payload.groups : []
}

async function generateStyle() {
  if (!selectedStyleId.value) {
    errorMessage.value = '请先选择一个风格。'
    return
  }
  if (!hasBasePhotos.value) {
    errorMessage.value = '请先在肖像上传中发布左侧面、正面、右侧面基础照后再生成。'
    return
  }

  generating.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    await apiRequest('/styles/generate', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        style_id: selectedStyleId.value
      }
    })
    successMessage.value = '风格图片已生成，结果已更新到下方对应风格分组。'
    await loadStyleResults()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '生成失败，请稍后重试。'
  } finally {
    generating.value = false
  }
}

async function publishStyleDraft(styleId) {
  if (!styleId) {
    errorMessage.value = '请选择可用风格后再发布。'
    return
  }
  publishingStyleId.value = styleId
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await apiRequest('/styles/publish', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        style_id: styleId
      }
    })
    successMessage.value = '草稿风格图已发布，企业用户可在广场查看。'
    await loadStyleResults()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '发布失败，请稍后重试。'
  } finally {
    publishingStyleId.value = null
  }
}

onMounted(async () => {
  if (!authStore.state.token) {
    errorMessage.value = '登录状态失效，请重新登录。'
    return
  }

  try {
    await Promise.all([
      loadStyles(),
      loadCurrentThreeView(),
      loadStyleResults()
    ])
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '风格实验室初始化失败，请稍后刷新重试。'
  }
})
</script>
