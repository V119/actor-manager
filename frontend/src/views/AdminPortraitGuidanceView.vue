<template>
  <div class="min-h-screen pt-24 px-6 pb-10 lg:px-10">
    <section class="max-w-7xl mx-auto space-y-6">
      <div class="rounded-2xl border border-sage-400/20 bg-ink-950/60 backdrop-blur-xl p-6">
        <p class="text-xs tracking-[0.2em] uppercase text-sage-300">Portrait Standard</p>
        <h1 class="text-2xl font-bold text-sage-100 mt-2">拍摄示例图管理</h1>
        <p class="text-sm text-on-surface-variant mt-2">
          单独维护演员端拍摄说明中的左侧面、正面、右侧面三张标准示例图。演员上传基础照时，会以这里的示例图作为规范参考。
        </p>
      </div>

      <section class="rounded-2xl border border-sage-400/15 bg-surface/60 backdrop-blur-xl p-6">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold text-sage-100">三视图示例配置</h2>
            <p class="text-sm text-on-surface-variant mt-2">
              建议上传 9:16 上半身示例图，取景范围保持腰部以上至头顶，背景简单干净。
            </p>
          </div>
          <button
            class="px-3 py-2 rounded-lg border border-sage-400/20 text-sage-200 text-sm hover:bg-sage-400/10 transition-colors"
            type="button"
            @click="loadGuidanceSamples"
          >
            刷新示例图
          </button>
        </div>

        <p v-if="guidanceErrorMessage" class="text-sm text-rose-300 mt-4">{{ guidanceErrorMessage }}</p>
        <p v-if="guidanceSuccessMessage" class="text-sm text-sage-300 mt-4">{{ guidanceSuccessMessage }}</p>

        <div class="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          <article
            v-for="slot in guidanceSlots"
            :key="slot.key"
            class="rounded-xl border border-sage-400/10 bg-ink-950/35 p-4"
          >
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold text-sage-100">{{ slot.label }}</h3>
              <span class="text-[11px] text-on-surface-variant">9:16 上半身</span>
            </div>
            <div class="aspect-[9/16] rounded-lg overflow-hidden border border-sage-400/15 bg-surface/45">
              <img
                v-if="guidancePreviewFor(slot.key)"
                :src="guidancePreviewFor(slot.key)"
                :alt="slot.label"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex flex-col items-center justify-center gap-2 text-on-surface-variant">
                <span class="material-symbols-outlined text-3xl">image_search</span>
                <p class="text-xs">暂未设置示例图</p>
              </div>
            </div>
            <p class="mt-3 text-xs text-on-surface-variant leading-relaxed">{{ slot.hint }}</p>
            <label class="mt-3 inline-flex cursor-pointer items-center justify-center w-full rounded-lg border border-sage-300/25 bg-sage-400/10 px-3 py-2 text-sm text-sage-100 hover:bg-sage-400/20 transition-colors">
              选择示例图
              <input
                type="file"
                accept="image/*"
                class="hidden"
                @change="onGuidanceFileSelected(slot.key, $event)"
              />
            </label>
            <p class="mt-2 text-[11px] text-on-surface-variant truncate">
              {{ guidanceFileNameFor(slot.key) || '尚未选择文件' }}
            </p>
            <button
              type="button"
              :disabled="guidanceUploading === slot.key || !guidanceFiles[slot.key]"
              class="mt-3 w-full px-4 py-2 rounded-lg bg-sage-300 text-ink-950 text-sm font-semibold hover:brightness-110 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
              @click="uploadGuidanceSample(slot.key)"
            >
              {{ guidanceUploading === slot.key ? '上传中...' : '保存此示例图' }}
            </button>
          </article>
        </div>
      </section>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const guidanceState = ref({ left: null, front: null, right: null, all_ready: false })
const guidanceUploading = ref('')
const guidanceErrorMessage = ref('')
const guidanceSuccessMessage = ref('')

const guidanceFiles = reactive({
  left: null,
  front: null,
  right: null
})

const guidanceLocalPreviews = reactive({
  left: '',
  front: '',
  right: ''
})

const guidanceSlots = [
  { key: 'left', label: '左侧面图', hint: '展示左侧面角度标准，保持腰部以上到头顶的上半身取景。' },
  { key: 'front', label: '正面图', hint: '展示正面角度标准，面部无遮挡，头顶和腰部以上范围完整。' },
  { key: 'right', label: '右侧面图', hint: '展示右侧面角度标准，背景简单干净，避免杂乱干扰。' }
]

function guidancePreviewFor(key) {
  return guidanceLocalPreviews[key] || guidanceState.value?.[key]?.preview_url || ''
}

function guidanceFileNameFor(key) {
  return guidanceFiles[key]?.name || guidanceState.value?.[key]?.source_filename || ''
}

function onGuidanceFileSelected(key, event) {
  const input = event.target
  if (!input?.files?.length) return
  const file = input.files[0]
  guidanceFiles[key] = file
  guidanceLocalPreviews[key] = URL.createObjectURL(file)
}

async function loadGuidanceSamples() {
  if (!authStore.state.token) return
  guidanceErrorMessage.value = ''
  try {
    const payload = await apiRequest('/portrait-guidance/samples', { token: authStore.state.token })
    guidanceState.value = payload || { left: null, front: null, right: null, all_ready: false }
  } catch (error) {
    guidanceErrorMessage.value = error instanceof Error ? error.message : '加载拍摄示例图失败'
  }
}

async function uploadGuidanceSample(key) {
  if (!authStore.state.token || !guidanceFiles[key]) return
  guidanceUploading.value = key
  guidanceErrorMessage.value = ''
  guidanceSuccessMessage.value = ''
  try {
    const formData = new FormData()
    formData.append('file', guidanceFiles[key])
    const payload = await apiRequest(`/admin/portrait-guidance/samples/${key}`, {
      method: 'POST',
      token: authStore.state.token,
      formData
    })
    guidanceState.value = {
      ...guidanceState.value,
      [key]: payload,
      all_ready: Boolean(
        (key === 'left' ? payload : guidanceState.value.left)
        && (key === 'front' ? payload : guidanceState.value.front)
        && (key === 'right' ? payload : guidanceState.value.right)
      )
    }
    guidanceFiles[key] = null
    guidanceLocalPreviews[key] = ''
    guidanceSuccessMessage.value = '拍摄示例图已保存'
  } catch (error) {
    guidanceErrorMessage.value = error instanceof Error ? error.message : '保存拍摄示例图失败'
  } finally {
    guidanceUploading.value = ''
  }
}

onMounted(async () => {
  await loadGuidanceSamples()
})
</script>
