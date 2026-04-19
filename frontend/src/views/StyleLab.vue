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

    <section class="rounded-2xl border border-sky-400/10 bg-surface/55 backdrop-blur-xl p-5 space-y-6">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <h3 class="text-sm font-semibold text-primary uppercase tracking-widest flex items-center gap-2">
          <span class="w-1.5 h-1.5 bg-primary rounded-full"></span>
          风格创作与结果管理
        </h3>
        <p class="text-xs text-on-surface-variant">点击风格卡片切换标签，管理当前风格下的全部图片。</p>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
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

      <div class="rounded-xl border border-sky-300/20 bg-slate-950/25 p-4 space-y-3">
        <div class="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h4 class="text-base font-semibold text-sky-100">{{ activeStyleCard?.name || '请选择风格' }}</h4>
            <p class="text-xs text-on-surface-variant">{{ activeStyleCard?.en || '选择风格后可生成并管理图片' }}</p>
          </div>
          <div class="text-xs text-on-surface-variant">
            当前风格共 {{ activeStyleResults.length }} 张
          </div>
        </div>

        <div v-if="!isCustomStyle">
          <label for="custom-style-prompt" class="block text-xs text-on-surface-variant mb-2">自定义描述</label>
          <div class="flex items-center gap-3 flex-wrap">
            <input
              id="custom-style-prompt"
              v-model="customPromptInput"
              type="text"
              maxlength="1000"
              placeholder="例如：夜晚街头，微雨，电影级侧光，情绪感强烈"
              class="flex-1 min-w-[240px] rounded-lg border border-sky-300/25 bg-slate-950/40 px-3 py-2 text-sm text-on-surface placeholder:text-on-surface-variant/70 focus:outline-none focus:ring-2 focus:ring-primary/35 focus:border-primary/45"
            />
            <button
              class="relative group px-5 py-2.5 bg-primary/20 rounded-full border border-primary/50 text-primary font-semibold text-sm flex items-center gap-2 transition-all duration-300 hover:bg-primary/30 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
              :disabled="isCurrentStyleGenerating || !selectedStyleId || !hasBasePhotos"
              @click="generateStyle"
            >
              <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">auto_fix_high</span>
              {{ isCurrentStyleGenerating ? '生成中...' : '生成当前风格图片' }}
            </button>
          </div>
          <p class="text-[11px] text-on-surface-variant mt-2">预计耗时 15-30 秒</p>
        </div>
        <div v-else>
          <label class="block text-xs text-on-surface-variant mb-2">上传自定义图片</label>
          <div class="flex items-center gap-3 flex-wrap">
            <label
              for="custom-style-upload"
              class="flex-1 min-w-[240px] rounded-lg border border-dashed border-sky-300/25 bg-slate-950/40 px-3 py-2.5 text-sm text-on-surface-variant cursor-pointer hover:border-primary/45 hover:text-on-surface transition-colors"
            >
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-base">upload_file</span>
                <span>{{ customUploadFileName || '选择一张图片上传到自定义风格' }}</span>
              </div>
            </label>
            <input
              id="custom-style-upload"
              ref="customUploadInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleCustomFileChange"
            />
            <button
              class="relative group px-5 py-2.5 bg-primary/20 rounded-full border border-primary/50 text-primary font-semibold text-sm flex items-center gap-2 transition-all duration-300 hover:bg-primary/30 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
              :disabled="isCurrentStyleUploading || !selectedStyleId || !customUploadFile"
              @click="uploadCustomStyleImage"
            >
              <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">cloud_upload</span>
              {{ isCurrentStyleUploading ? '上传中...' : '上传当前图片' }}
            </button>
          </div>
          <p class="text-[11px] text-on-surface-variant mt-2">选择图片上传。</p>
        </div>
      </div>

      <div>
        <div v-if="!activeStyleResults.length" class="rounded-xl border border-dashed border-sky-300/25 bg-slate-950/20 p-8 text-sm text-on-surface-variant text-center">
          {{ isCustomStyle ? '当前风格暂无图片，选择图片后点击“上传当前图片”开始添加。' : '当前风格暂无图片，输入描述后点击“生成当前风格图片”开始创作。' }}
        </div>
        <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <article
            v-for="item in activeStyleResults"
            :key="item.id"
            class="group rounded-xl border border-sky-300/20 bg-slate-950/30 overflow-hidden"
          >
            <div class="relative">
              <img
                :src="item.preview_url || item.image_url"
                :alt="`${activeStyleCard?.name || '风格图'}-${item.id}`"
                class="w-full aspect-[3/4] object-cover"
              />
              <div class="absolute top-2 right-2">
                <span
                  class="px-2 py-1 rounded-full text-[11px] font-medium border"
                  :class="item.lifecycle_state === 'published' ? 'bg-emerald-500/25 border-emerald-300/60 text-emerald-50' : 'bg-amber-500/20 border-amber-300/60 text-amber-50'"
                >
                  {{ item.lifecycle_state === 'published' ? '已发布' : '未发布' }}
                </span>
              </div>
              <div class="absolute inset-x-0 bottom-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                <div class="rounded-lg border border-white/15 bg-slate-950/78 backdrop-blur-sm shadow-[0_10px_24px_rgba(2,6,23,0.45)] px-3 py-2">
                  <p class="text-[11px] text-slate-100 leading-relaxed line-clamp-3 drop-shadow-[0_1px_1px_rgba(0,0,0,0.45)]">
                  {{ item.custom_prompt || '无自定义描述' }}
                  </p>
                </div>
              </div>
            </div>
            <div class="p-3 flex items-center justify-between gap-2">
              <div class="flex items-center gap-3">
                <div class="flex flex-col">
                </div>
                <button
                  type="button"
                  class="inline-flex items-center justify-center rounded-md border px-3 py-1.5 text-xs font-medium transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
                  :class="item.lifecycle_state === 'published'
                    ? 'border-amber-300/45 bg-amber-500/15 text-amber-50 hover:bg-amber-500/22 hover:border-amber-300/60'
                    : 'border-emerald-300/45 bg-emerald-500/18 text-emerald-50 hover:bg-emerald-500/25 hover:border-emerald-300/60'"
                  :disabled="updatingResultId === item.id"
                  @click="toggleResultState(item)"
                >
                  <span class="material-symbols-outlined text-sm mr-1">
                    {{ updatingResultId === item.id ? 'hourglass_top' : item.lifecycle_state === 'published' ? 'visibility_off' : 'visibility' }}
                  </span>
                  {{
                    updatingResultId === item.id
                      ? '处理中...'
                      : item.lifecycle_state === 'published'
                        ? '取消发布'
                        : '发布'
                  }}
                </button>
              </div>
              <button
                class="px-3 py-1.5 rounded-md border border-rose-300/40 text-xs text-rose-200 hover:bg-rose-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="deletingResultId === item.id"
                @click="confirmDeleteResult(item)"
              >
                {{ deletingResultId === item.id ? '删除中...' : '删除' }}
              </button>
            </div>
          </article>
        </div>
      </div>
    </section>

    <p v-if="errorMessage" class="text-sm text-rose-300 mt-3">{{ errorMessage }}</p>
    <p v-if="successMessage" class="text-sm text-emerald-300 mt-3">{{ successMessage }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ensureAgreementSignedForPublish } from '../lib/agreement'
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
  },
  {
    name: '自定义',
    en: 'Custom Upload',
    category: 'custom',
    preview_url: '/style-custom-preview.svg'
  }
]

const stylesFromApi = ref([])
const styleGroups = ref([])
const publishedThreeView = ref(null)

const selectedStyleId = ref(null)
const generatingStyleIds = ref([])
const uploadingStyleIds = ref([])
const updatingResultId = ref(null)
const deletingResultId = ref(null)
const loadingBasePhotos = ref(false)
const customPromptInput = ref('')
const customUploadFile = ref(null)
const customUploadInput = ref(null)
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

const activeStyleCard = computed(() => {
  return styleCards.value.find((item) => item.id === selectedStyleId.value) || null
})
const isCustomStyle = computed(() => String(activeStyleCard.value?.category || '').toLowerCase() === 'custom')
const customUploadFileName = computed(() => customUploadFile.value?.name || '')

const styleResultMap = computed(() => {
  const map = new Map()
  const groups = Array.isArray(styleGroups.value) ? styleGroups.value : []
  groups.forEach((group) => {
    if (group?.style_id) {
      map.set(group.style_id, Array.isArray(group.results) ? group.results : [])
    }
  })
  return map
})

const activeStyleResults = computed(() => {
  if (!selectedStyleId.value) return []
  const rows = styleResultMap.value.get(selectedStyleId.value) || []
  return [...rows].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})
const isCurrentStyleGenerating = computed(() => {
  if (!selectedStyleId.value) return false
  return generatingStyleIds.value.includes(selectedStyleId.value)
})
const isCurrentStyleUploading = computed(() => {
  if (!selectedStyleId.value) return false
  return uploadingStyleIds.value.includes(selectedStyleId.value)
})

function selectStyle(style) {
  if (!style?.id) return
  selectedStyleId.value = style.id
  errorMessage.value = ''
}

function goToPortraitUpload() {
  router.push('/edit-portrait')
}

function handleCustomFileChange(event) {
  const files = event?.target?.files
  customUploadFile.value = files && files[0] ? files[0] : null
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
  const payload = await apiRequest('/styles/results?limit_per_style=100', { token: authStore.state.token })
  styleGroups.value = Array.isArray(payload?.groups) ? payload.groups : []
}

async function generateStyle() {
  const styleId = selectedStyleId.value
  if (!styleId) {
    errorMessage.value = '请先选择一个风格。'
    return
  }
  if (isCustomStyle.value) {
    errorMessage.value = '自定义风格请使用图片上传。'
    return
  }
  if (!hasBasePhotos.value) {
    errorMessage.value = '请先在肖像上传中发布左侧面、正面、右侧面基础照后再生成。'
    return
  }

  generatingStyleIds.value = [...new Set([...generatingStyleIds.value, styleId])]
  errorMessage.value = ''
  successMessage.value = ''

  try {
    await apiRequest('/styles/generate', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        style_id: styleId,
        custom_prompt: customPromptInput.value.trim()
      }
    })
    successMessage.value = '风格图片已生成，已更新当前风格列表。'
    await loadStyleResults()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '生成失败，请稍后重试。'
  } finally {
    generatingStyleIds.value = generatingStyleIds.value.filter((id) => id !== styleId)
  }
}

async function uploadCustomStyleImage() {
  const styleId = selectedStyleId.value
  if (!styleId) {
    errorMessage.value = '请先选择自定义风格。'
    return
  }
  if (!customUploadFile.value) {
    errorMessage.value = '请先选择一张图片后再上传。'
    return
  }

  uploadingStyleIds.value = [...new Set([...uploadingStyleIds.value, styleId])]
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const formData = new FormData()
    formData.append('style_id', String(styleId))
    formData.append('image_file', customUploadFile.value)
    await apiRequest('/styles/upload', {
      method: 'POST',
      token: authStore.state.token,
      formData
    })
    customUploadFile.value = null
    if (customUploadInput.value) {
      customUploadInput.value.value = ''
    }
    await loadStyleResults()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '上传失败，请稍后重试。'
  } finally {
    uploadingStyleIds.value = uploadingStyleIds.value.filter((id) => id !== styleId)
  }
}

async function toggleResultState(item) {
  if (!item?.id) return
  updatingResultId.value = item.id
  errorMessage.value = ''
  try {
    const targetPublished = item.lifecycle_state !== 'published'
    if (targetPublished) {
      const gate = await ensureAgreementSignedForPublish({
        token: authStore.state.token
      })
      if (!gate.allowed) {
        return
      }
    }

    await apiRequest('/styles/result-state', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        result_id: item.id,
        published: targetPublished
      }
    })
    await loadStyleResults()
  } catch (error) {
    const message = error instanceof Error ? error.message : '状态切换失败，请稍后重试。'
    errorMessage.value = message
  } finally {
    updatingResultId.value = null
  }
}

async function confirmDeleteResult(item) {
  if (!item?.id) return
  const confirmed = window.confirm('确定删除该图片吗？删除后将永久移除且不可恢复。')
  if (!confirmed) return

  deletingResultId.value = item.id
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await apiRequest(`/styles/results/${item.id}`, {
      method: 'DELETE',
      token: authStore.state.token
    })
    await loadStyleResults()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '删除失败，请稍后重试。'
  } finally {
    deletingResultId.value = null
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
