<template>
  <div class="min-h-screen bg-background text-on-surface">
    <main class="max-w-7xl mx-auto px-6 md:px-8 pt-24 pb-14 space-y-8">
      <header class="space-y-3">
        <div class="flex items-center gap-3">
          <h1 class="text-3xl font-bold tracking-tight">肖像与视频素材上传</h1>
          <span class="px-3 py-1 rounded-full border border-sky-300/30 bg-sky-400/10 text-sky-200 text-xs font-semibold">
            个人素材中心
          </span>
        </div>
        <p class="text-sm text-on-surface-variant max-w-3xl leading-relaxed">
          你上传的素材会自动归档到当前账号下，系统会将左侧面、正面、右侧面三张图片合成为一张 4:3 上半身三视图图像，同时支持上传视频素材。
        </p>
      </header>

      <section class="bg-surface/65 border border-sky-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-sky-300 text-[20px]">tips_and_updates</span>
          <h2 class="text-lg font-semibold">拍摄说明</h2>
        </div>
        <div class="grid md:grid-cols-2 xl:grid-cols-4 gap-3">
          <article class="rounded-xl border border-sky-400/10 bg-slate-950/20 px-4 py-3">
            <p class="text-sm font-semibold text-sky-100">构图范围</p>
            <p class="mt-1 text-xs text-on-surface-variant">上半身，取景从腰部以上到头顶。</p>
          </article>
          <article class="rounded-xl border border-sky-400/10 bg-slate-950/20 px-4 py-3">
            <p class="text-sm font-semibold text-sky-100">角度要求</p>
            <p class="mt-1 text-xs text-on-surface-variant">请分别拍摄正面、左侧面、右侧面各 1 张。</p>
          </article>
          <article class="rounded-xl border border-sky-400/10 bg-slate-950/20 px-4 py-3">
            <p class="text-sm font-semibold text-sky-100">背景环境</p>
            <p class="mt-1 text-xs text-on-surface-variant">背景尽量简单干净，避免杂乱物体干扰。</p>
          </article>
          <article class="rounded-xl border border-sky-400/10 bg-slate-950/20 px-4 py-3">
            <p class="text-sm font-semibold text-sky-100">检测说明</p>
            <p class="mt-1 text-xs text-on-surface-variant">当前仅提供拍摄提示，后续版本可能加入自动检测。</p>
          </article>
        </div>
      </section>

      <section class="space-y-6">
        <div class="bg-surface/65 border border-sky-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-semibold">基础素材区（左/正/右 三张）</h2>
            <span class="text-xs text-on-surface-variant">系统将合成为 4:3 三视图</span>
          </div>
          <p class="mb-4 text-xs text-on-surface-variant">
            <span v-if="loadingExisting">正在加载已上传素材...</span>
            <span v-else-if="hasExistingSession">已显示你最近一次上传的三张原图。可替换任意角度并重新生成，未替换角度将沿用当前素材。</span>
            <span v-else>首次上传需选择左侧、正面、右侧三张图片。</span>
          </p>

          <div class="grid md:grid-cols-3 gap-4">
            <div
              v-for="slot in imageSlots"
              :key="slot.key"
              class="rounded-xl border border-dashed border-sky-400/25 bg-slate-950/20 p-3"
            >
              <div class="mb-2 flex items-center justify-between">
                <p class="text-sm font-semibold text-sky-200">{{ slot.label }}</p>
                <span class="text-[11px] text-on-surface-variant">上半身</span>
              </div>
              <div class="aspect-[9/16] rounded-lg overflow-hidden bg-surface/50 border border-sky-400/10">
                <img
                  v-if="slot.currentPreview"
                  :src="slot.currentPreview"
                  :alt="slot.label"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex flex-col items-center justify-center gap-2 text-on-surface-variant">
                  <span class="material-symbols-outlined text-3xl">add_photo_alternate</span>
                  <p class="text-xs">未选择图片</p>
                </div>
              </div>
              <label class="mt-3 inline-flex cursor-pointer items-center justify-center w-full rounded-lg border border-sky-300/25 bg-sky-400/10 px-3 py-2 text-sm text-sky-100 hover:bg-sky-400/20 transition-colors">
                选择图片
                <input
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="onImageSelected(slot.key, $event)"
                />
              </label>
              <p class="mt-2 text-[11px] text-on-surface-variant truncate">
                {{ slot.displayFileName || '尚未上传文件' }}
              </p>
            </div>
          </div>

          <div class="mt-5">
            <button
              class="px-5 py-2.5 rounded-lg bg-sky-400 text-slate-950 font-semibold hover:brightness-110 transition disabled:opacity-60 disabled:cursor-not-allowed"
              :disabled="imageUploading || !canUploadImages"
              @click="submitThreeView"
            >
              {{ imageUploading ? '提交处理中...' : (hasExistingSession ? '提交修改并重新生成 4:3 三视图' : '上传并生成 4:3 三视图') }}
            </button>
            <button
              class="ml-3 px-5 py-2.5 rounded-lg border border-emerald-300/40 text-emerald-200 hover:bg-emerald-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
              :disabled="imagePublishing || !latestComposite"
              @click="publishThreeViewDraft"
            >
              {{ imagePublishing ? '发布中...' : '发布当前三视图草稿' }}
            </button>
          </div>

          <p v-if="imageSuccessMessage" class="mt-3 text-sm text-emerald-300">{{ imageSuccessMessage }}</p>
          <p v-if="imageErrorMessage" class="mt-3 text-sm text-rose-300">{{ imageErrorMessage }}</p>
        </div>

        <div
          v-if="latestComposite"
          class="bg-surface/65 border border-sky-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl"
        >
          <h2 class="text-lg font-semibold mb-4">三视图草稿（未发布）</h2>
          <div class="rounded-xl overflow-hidden border border-sky-300/20 bg-slate-950/25">
            <div class="aspect-[4/3]">
              <img
                :src="latestComposite.composite_preview_url"
                alt="三视图草稿"
                class="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>

        <div
          v-if="publishedComposite"
          class="bg-surface/65 border border-emerald-400/20 rounded-2xl p-5 md:p-6 backdrop-blur-xl"
        >
          <h2 class="text-lg font-semibold mb-4">已发布三视图</h2>
          <div class="rounded-xl overflow-hidden border border-emerald-300/25 bg-slate-950/25">
            <div class="aspect-[4/3]">
              <img
                :src="publishedComposite.composite_preview_url"
                alt="已发布三视图"
                class="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>

        <div class="bg-surface/65 border border-sky-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-semibold">动态视频区</h2>
            <span class="text-xs text-on-surface-variant">建议 5-10 秒，包含多角度缓慢转头</span>
          </div>

          <div class="grid md:grid-cols-2 gap-5">
            <div class="rounded-xl border border-dashed border-sky-400/25 bg-slate-950/20 p-4">
              <div class="aspect-video rounded-lg overflow-hidden border border-sky-400/15 bg-surface/50">
                <video
                  v-if="currentVideoPreview"
                  :src="currentVideoPreview"
                  controls
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex flex-col items-center justify-center gap-2 text-on-surface-variant">
                  <span class="material-symbols-outlined text-3xl">videocam</span>
                  <p class="text-xs">未选择视频</p>
                </div>
              </div>

              <label class="mt-3 inline-flex cursor-pointer items-center justify-center w-full rounded-lg border border-sky-300/25 bg-sky-400/10 px-3 py-2 text-sm text-sky-100 hover:bg-sky-400/20 transition-colors">
                选择视频
                <input
                  type="file"
                  accept="video/*"
                  class="hidden"
                  @change="onVideoSelected"
                />
              </label>
              <p class="mt-2 text-[11px] text-on-surface-variant truncate">
                {{ currentVideoFileName || '尚未上传文件' }}
              </p>
            </div>

            <div class="rounded-xl border border-sky-400/10 bg-slate-950/20 p-4 space-y-4">
              <div class="space-y-2">
                <p class="text-sm font-semibold text-sky-100">视频建议内容</p>
                <ul class="space-y-2 text-xs text-on-surface-variant">
                  <li>1. 面部无遮挡，光线均匀，避免强背光。</li>
                  <li>2. 缓慢转头覆盖正面、左侧面、右侧面。</li>
                  <li>3. 背景保持干净，尽量减少移动干扰。</li>
                </ul>
              </div>
              <button
                class="px-5 py-2.5 rounded-lg border border-sky-300/35 text-sky-100 hover:bg-sky-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="videoUploading || !videoFile"
                @click="submitVideo"
              >
                {{ videoUploading ? '视频上传中...' : '上传视频素材' }}
              </button>
              <button
                class="px-5 py-2.5 rounded-lg border border-emerald-300/40 text-emerald-200 hover:bg-emerald-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="videoPublishing || !latestVideo"
                @click="publishVideoDraft"
              >
                {{ videoPublishing ? '发布中...' : '发布当前视频草稿' }}
              </button>
              <p v-if="videoSuccessMessage" class="text-sm text-emerald-300">{{ videoSuccessMessage }}</p>
              <p v-if="videoErrorMessage" class="text-sm text-rose-300">{{ videoErrorMessage }}</p>
            </div>
          </div>

          <div v-if="latestVideo" class="mt-5 rounded-xl border border-sky-300/20 bg-slate-950/25 p-4">
            <p class="text-sm font-semibold mb-2">视频草稿（未发布）</p>
            <video :src="latestVideo.preview_url" controls class="w-full rounded-lg border border-sky-300/15" />
            <p class="mt-2 text-xs text-on-surface-variant truncate">{{ latestVideoFileName || '未命名文件' }}</p>
          </div>

          <div v-if="publishedVideo" class="mt-5 rounded-xl border border-emerald-300/25 bg-slate-950/25 p-4">
            <p class="text-sm font-semibold mb-2">已发布视频</p>
            <video :src="publishedVideo.preview_url" controls class="w-full rounded-lg border border-emerald-300/20" />
            <p class="mt-2 text-xs text-on-surface-variant truncate">{{ publishedVideoFileName || '未命名文件' }}</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const loadingExisting = ref(false)

const imageUploading = ref(false)
const imagePublishing = ref(false)
const imageErrorMessage = ref('')
const imageSuccessMessage = ref('')
const latestComposite = ref(null)
const publishedComposite = ref(null)

const videoUploading = ref(false)
const videoPublishing = ref(false)
const videoErrorMessage = ref('')
const videoSuccessMessage = ref('')
const videoFile = ref(null)
const videoFileName = ref('')
const videoPreview = ref('')
const latestVideo = ref(null)
const publishedVideo = ref(null)

const images = reactive({
  left: { label: '左侧面图', preview: '', file: null, fileName: '', existingPreview: '', existingFileName: '' },
  front: { label: '正面图', preview: '', file: null, fileName: '', existingPreview: '', existingFileName: '' },
  right: { label: '右侧面图', preview: '', file: null, fileName: '', existingPreview: '', existingFileName: '' }
})

const hasExistingSession = computed(() => Boolean(latestComposite.value?.session_id))
const hasAnyImageReplacement = computed(() => Boolean(images.left.file || images.front.file || images.right.file))

const imageSlots = computed(() => [
  {
    key: 'left',
    label: images.left.label,
    currentPreview: images.left.preview || images.left.existingPreview,
    displayFileName: images.left.fileName || images.left.existingFileName
  },
  {
    key: 'front',
    label: images.front.label,
    currentPreview: images.front.preview || images.front.existingPreview,
    displayFileName: images.front.fileName || images.front.existingFileName
  },
  {
    key: 'right',
    label: images.right.label,
    currentPreview: images.right.preview || images.right.existingPreview,
    displayFileName: images.right.fileName || images.right.existingFileName
  }
])

const canUploadImages = computed(() => {
  if (hasExistingSession.value) {
    return hasAnyImageReplacement.value
  }
  return Boolean(images.left.file && images.front.file && images.right.file)
})

const currentVideoPreview = computed(() => videoPreview.value || latestVideo.value?.preview_url || '')
const currentVideoFileName = computed(() => videoFileName.value || latestVideo.value?.source_filename || '')
const latestVideoFileName = computed(() => latestVideo.value?.source_filename || extractFileName(latestVideo.value?.object_key || ''))
const publishedVideoFileName = computed(() => publishedVideo.value?.source_filename || extractFileName(publishedVideo.value?.object_key || ''))
const COMPOSE_JOB_POLL_INTERVAL_MS = 1200
const COMPOSE_JOB_POLL_MAX_ATTEMPTS = 200

function extractFileName(path) {
  if (!path) return ''
  const parts = String(path).split('/')
  return parts[parts.length - 1] || ''
}

function applySessionToImageSlots(session) {
  const rawImages = Array.isArray(session?.raw_images) ? session.raw_images : []
  const byAngle = {}
  rawImages.forEach((item) => {
    byAngle[item.view_angle] = item
  })

  for (const key of ['left', 'front', 'right']) {
    images[key].existingPreview = byAngle[key]?.preview_url || ''
    images[key].existingFileName = byAngle[key]?.source_filename || ''
    images[key].preview = ''
    images[key].file = null
    images[key].fileName = ''
  }
}

function onImageSelected(slotKey, event) {
  const input = event.target
  if (!input?.files?.length) return
  const file = input.files[0]
  images[slotKey].file = file
  images[slotKey].fileName = file.name
  images[slotKey].preview = URL.createObjectURL(file)
}

function onVideoSelected(event) {
  const input = event.target
  if (!input?.files?.length) return
  const file = input.files[0]
  videoFile.value = file
  videoFileName.value = file.name
  videoPreview.value = URL.createObjectURL(file)
}

async function loadExistingAssets() {
  if (!authStore.state.token) return

  loadingExisting.value = true
  imageErrorMessage.value = ''
  videoErrorMessage.value = ''
  try {
    const threeViewState = await apiRequest('/portraits/three-view/state', {
      token: authStore.state.token
    })
    latestComposite.value = threeViewState?.draft || null
    publishedComposite.value = threeViewState?.published || null

    if (latestComposite.value?.session_id) {
      applySessionToImageSlots(latestComposite.value)
      imageSuccessMessage.value = '已加载三视图草稿，可继续修改或发布。'
    } else if (publishedComposite.value?.session_id) {
      applySessionToImageSlots(publishedComposite.value)
      imageSuccessMessage.value = '已加载当前已发布三视图。'
    }

    const videoState = await apiRequest('/portraits/videos/state', {
      token: authStore.state.token
    })
    latestVideo.value = videoState?.draft || null
    publishedVideo.value = videoState?.published || null
  } catch (error) {
    const message = error instanceof Error ? error.message : '历史素材加载失败，请稍后重试。'
    imageErrorMessage.value = message
  } finally {
    loadingExisting.value = false
  }
}

async function submitThreeView() {
  if (!authStore.state.token) {
    imageErrorMessage.value = '登录状态失效，请重新登录。'
    return
  }
  if (!canUploadImages.value) {
    imageErrorMessage.value = hasExistingSession.value
      ? '请至少选择一张要替换的图片。'
      : '请先上传左侧、正面、右侧三张图片。'
    return
  }

  imageUploading.value = true
  imageErrorMessage.value = ''
  imageSuccessMessage.value = ''
  try {
    const hadExisting = hasExistingSession.value
    const selectedFiles = {}
    if (images.left.file) selectedFiles.left = images.left.file
    if (images.front.file) selectedFiles.front = images.front.file
    if (images.right.file) selectedFiles.right = images.right.file
    let result = null
    let usedFallback = false
    try {
      result = await submitThreeViewDirectFlow(selectedFiles, hadExisting)
    } catch (directError) {
      console.warn('three-view direct upload fallback triggered', directError)
      result = await submitThreeViewLegacyFlow(selectedFiles, hadExisting)
      usedFallback = true
    }

    latestComposite.value = result
    applySessionToImageSlots(result)
    if (usedFallback) {
      imageSuccessMessage.value = '直传链路不可用，已自动切换为后端上传并完成 4:3 三视图生成。'
    } else {
      imageSuccessMessage.value = hadExisting
        ? '修改已提交，系统已重新生成 4:3 上半身三视图。'
        : '上传成功，已生成 4:3 上半身三视图拼接图。'
    }
  } catch (error) {
    imageErrorMessage.value = error instanceof Error ? error.message : '上传失败，请稍后重试。'
  } finally {
    imageUploading.value = false
  }
}

async function submitVideo() {
  if (!authStore.state.token) {
    videoErrorMessage.value = '登录状态失效，请重新登录。'
    return
  }
  if (!videoFile.value) {
    videoErrorMessage.value = '请先选择视频文件。'
    return
  }

  videoUploading.value = true
  videoErrorMessage.value = ''
  videoSuccessMessage.value = ''
  try {
    const file = videoFile.value
    let result = null
    let usedFallback = false
    try {
      result = await submitVideoDirectFlow(file)
    } catch (directError) {
      console.warn('video direct upload fallback triggered', directError)
      result = await submitVideoLegacyFlow(file)
      usedFallback = true
    }
    latestVideo.value = result
    if (publishedVideo.value && publishedVideo.value.id === result.id) {
      publishedVideo.value = null
    }
    videoFile.value = null
    videoFileName.value = ''
    videoPreview.value = ''
    videoSuccessMessage.value = usedFallback
      ? '直传链路不可用，已自动切换为后端上传并完成保存。'
      : '视频上传成功，已保存为新的素材版本。'
  } catch (error) {
    videoErrorMessage.value = error instanceof Error ? error.message : '视频上传失败，请稍后重试。'
  } finally {
    videoUploading.value = false
  }
}

async function publishThreeViewDraft() {
  if (!authStore.state.token) {
    imageErrorMessage.value = '登录状态失效，请重新登录。'
    return
  }
  if (!latestComposite.value?.session_id) {
    imageErrorMessage.value = '暂无可发布的三视图草稿。'
    return
  }

  imagePublishing.value = true
  imageErrorMessage.value = ''
  imageSuccessMessage.value = ''
  try {
    const published = await apiRequest('/portraits/three-view/publish', {
      method: 'POST',
      token: authStore.state.token
    })
    publishedComposite.value = published
    latestComposite.value = null
    applySessionToImageSlots(published)
    imageSuccessMessage.value = '三视图草稿已发布，企业用户可在广场查看。'
  } catch (error) {
    imageErrorMessage.value = error instanceof Error ? error.message : '三视图发布失败，请稍后重试。'
  } finally {
    imagePublishing.value = false
  }
}

async function publishVideoDraft() {
  if (!authStore.state.token) {
    videoErrorMessage.value = '登录状态失效，请重新登录。'
    return
  }
  if (!latestVideo.value?.id) {
    videoErrorMessage.value = '暂无可发布的视频草稿。'
    return
  }

  videoPublishing.value = true
  videoErrorMessage.value = ''
  videoSuccessMessage.value = ''
  try {
    const published = await apiRequest('/portraits/videos/publish', {
      method: 'POST',
      token: authStore.state.token
    })
    publishedVideo.value = published
    latestVideo.value = null
    videoSuccessMessage.value = '视频草稿已发布，企业用户可在广场查看。'
  } catch (error) {
    videoErrorMessage.value = error instanceof Error ? error.message : '视频发布失败，请稍后重试。'
  } finally {
    videoPublishing.value = false
  }
}

async function submitThreeViewDirectFlow(selectedFiles, hadExisting) {
  const selectedAngles = Object.keys(selectedFiles)
  const selectedCount = selectedAngles.length

  const plan = await apiRequest('/portraits/three-view/presign', {
    method: 'POST',
    token: authStore.state.token,
    body: {
      files: selectedAngles.map((angle) => {
        const file = selectedFiles[angle]
        return {
          view_angle: angle,
          filename: file.name,
          content_type: file.type || 'application/octet-stream',
          size: file.size || 0
        }
      })
    }
  })

  await Promise.all((plan.uploads || []).map(async (target) => {
    const file = selectedFiles[target.view_angle]
    if (!file) throw new Error(`缺少角度 ${target.view_angle} 的本地文件`)
    await uploadToPresignedUrl(target.upload_url, target.upload_method || 'PUT', target.mime_type || file.type, file)
  }))

  const createJobResult = await apiRequest('/portraits/three-view/jobs', {
    method: 'POST',
    token: authStore.state.token,
    body: {
      upload_plan_token: plan.upload_plan_token,
      reuse_latest_missing: hadExisting && selectedCount < 3
    }
  })

  const finalJob = await waitForComposeJob(createJobResult.job_key)
  if (finalJob.status !== 'completed' || !finalJob.result) {
    throw new Error(finalJob.error_message || '合成任务未完成，请稍后重试')
  }
  return finalJob.result
}

async function submitThreeViewLegacyFlow(selectedFiles, hadExisting) {
  const selectedCount = Object.keys(selectedFiles).length
  const endpoint = hadExisting && selectedCount < 3
    ? '/portraits/three-view/recompose'
    : '/portraits/three-view'
  const formData = new FormData()
  if (selectedFiles.left) formData.append('left_image', selectedFiles.left)
  if (selectedFiles.front) formData.append('front_image', selectedFiles.front)
  if (selectedFiles.right) formData.append('right_image', selectedFiles.right)
  return apiRequest(endpoint, {
    method: 'POST',
    token: authStore.state.token,
    formData
  })
}

async function submitVideoDirectFlow(file) {
  const plan = await apiRequest('/portraits/videos/presign', {
    method: 'POST',
    token: authStore.state.token,
    body: {
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      size: file.size || 0
    }
  })
  await uploadToPresignedUrl(
    plan.upload.upload_url,
    plan.upload.upload_method || 'PUT',
    plan.upload.mime_type || file.type,
    file
  )
  return apiRequest('/portraits/videos/commit', {
    method: 'POST',
    token: authStore.state.token,
    body: {
      upload_plan_token: plan.upload_plan_token
    }
  })
}

async function submitVideoLegacyFlow(file) {
  const formData = new FormData()
  formData.append('video_file', file)
  return apiRequest('/portraits/videos', {
    method: 'POST',
    token: authStore.state.token,
    formData
  })
}

async function uploadToPresignedUrl(uploadUrl, uploadMethod, mimeType, file) {
  const response = await fetch(uploadUrl, {
    method: uploadMethod || 'PUT',
    headers: {
      'Content-Type': mimeType || file.type || 'application/octet-stream'
    },
    body: file
  })
  if (!response.ok) {
    throw new Error(`文件直传失败（${response.status}）`)
  }
}

async function waitForComposeJob(jobKey) {
  let lastPayload = null
  for (let attempt = 0; attempt < COMPOSE_JOB_POLL_MAX_ATTEMPTS; attempt += 1) {
    const payload = await apiRequest(`/portraits/three-view/jobs/${jobKey}`, {
      token: authStore.state.token
    })
    lastPayload = payload
    if (payload.status === 'completed' || payload.status === 'failed') {
      return payload
    }
    await new Promise((resolve) => setTimeout(resolve, COMPOSE_JOB_POLL_INTERVAL_MS))
  }
  throw new Error(lastPayload?.error_message || '合成任务处理超时，请稍后在页面刷新查看结果。')
}

onMounted(async () => {
  await loadExistingAssets()
})
</script>
