<template>
  <div class="min-h-screen bg-background text-on-surface">
    <main class="max-w-7xl mx-auto px-6 md:px-8 pt-24 pb-14 space-y-8">
      <header class="space-y-3">
        <div class="flex items-center gap-3">
          <h1 class="text-3xl font-bold tracking-tight">肖像、视频与录音素材上传</h1>
          <span class="px-3 py-1 rounded-full border border-moss-300/30 bg-moss-400/10 text-moss-200 text-xs font-semibold">
            个人素材中心
          </span>
        </div>
        <p class="text-sm text-on-surface-variant max-w-3xl leading-relaxed">
          你上传的素材会自动归档到当前账号下，系统会将左侧面、正面、右侧面三张图片合成为一张 4:3 上半身三视图图像，同时支持上传视频与录音素材。
        </p>
      </header>

      <section class="bg-surface/65 border border-moss-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-moss-300 text-[20px]">tips_and_updates</span>
          <h2 class="text-lg font-semibold">拍摄说明</h2>
        </div>
        <div class="grid md:grid-cols-2 xl:grid-cols-4 gap-3">
          <article class="rounded-xl border border-moss-400/10 bg-ink-950/20 px-4 py-3">
            <p class="text-sm font-semibold text-moss-100">构图范围</p>
            <p class="mt-1 text-xs text-on-surface-variant">请以示例图为标准，保持上半身取景，范围从腰部以上到头顶。</p>
          </article>
          <article class="rounded-xl border border-moss-400/10 bg-ink-950/20 px-4 py-3">
            <p class="text-sm font-semibold text-moss-100">角度要求</p>
            <p class="mt-1 text-xs text-on-surface-variant">请对照下方左侧面、正面、右侧面示例图，各上传 1 张。</p>
          </article>
          <article class="rounded-xl border border-moss-400/10 bg-ink-950/20 px-4 py-3">
            <p class="text-sm font-semibold text-moss-100">背景环境</p>
            <p class="mt-1 text-xs text-on-surface-variant">参考示例图的干净背景，避免杂乱物体、强阴影和遮挡。</p>
          </article>
          <article class="rounded-xl border border-moss-400/10 bg-ink-950/20 px-4 py-3">
            <p class="text-sm font-semibold text-moss-100">检测说明</p>
            <p class="mt-1 text-xs text-on-surface-variant">上传图片将校验清晰度，左/正/右三张图片长边都需大于 2000 像素。</p>
          </article>
        </div>

        <div class="mt-5 rounded-2xl border border-moss-400/10 bg-ink-950/25 p-3 md:p-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 class="text-base font-semibold text-moss-100">标准示例图</h3>
              <p class="mt-1 text-xs text-on-surface-variant">
                请按示例图的角度、上半身取景范围和干净背景进行拍摄并上传。当前仅做提示，不做自动检测。
              </p>
            </div>
            <span v-if="guidanceLoading" class="text-xs text-on-surface-variant">正在加载示例图...</span>
          </div>

          <div class="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-3xl mx-auto">
            <article
              v-for="slot in guidanceSampleSlots"
              :key="slot.key"
              class="rounded-xl border border-moss-400/10 bg-surface/35 p-2.5"
            >
              <div class="mb-2 flex items-center justify-between">
                <p class="text-xs font-semibold text-moss-200">{{ slot.label }}</p>
                <span class="text-[11px] text-on-surface-variant">示例标准</span>
              </div>
              <div class="mx-auto aspect-[9/16] w-24 sm:w-28 rounded-lg overflow-hidden border border-moss-400/10 bg-ink-950/40">
                <img
                  v-if="slot.previewUrl"
                  :src="slot.previewUrl"
                  :alt="slot.label"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex flex-col items-center justify-center gap-2 text-on-surface-variant">
                  <span class="material-symbols-outlined text-3xl">image_not_supported</span>
                  <p class="text-xs">管理员暂未配置</p>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section class="space-y-6">
        <div class="bg-surface/65 border border-moss-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-semibold">基础素材区（左/正/右 三张）</h2>
            <span class="text-xs text-on-surface-variant">系统将合成为 4:3 三视图</span>
          </div>
          <p class="mb-4 text-xs text-on-surface-variant">
            <span v-if="loadingExisting">正在加载已上传素材...</span>
            <span v-else-if="hasExistingSession">已显示你当前三视图所用的三张原图。替换任意角度后点击“发布最新三视图”即可更新，未替换角度将沿用当前素材。</span>
            <span v-else>首次上传需选择左侧、正面、右侧三张图片。</span>
          </p>

          <div class="grid md:grid-cols-3 gap-4">
            <div
              v-for="slot in imageSlots"
              :key="slot.key"
              class="rounded-xl border border-dashed border-moss-400/25 bg-ink-950/20 p-3"
            >
              <div class="mb-2 flex items-center justify-between">
                <p class="text-sm font-semibold text-moss-200">{{ slot.label }}</p>
                <span class="text-[11px] text-on-surface-variant">上半身</span>
              </div>
              <div class="aspect-[9/16] rounded-lg overflow-hidden bg-surface/50 border border-moss-400/10">
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
              <label class="mt-3 inline-flex cursor-pointer items-center justify-center w-full rounded-lg border border-moss-300/25 bg-moss-400/10 px-3 py-2 text-sm text-moss-100 hover:bg-moss-400/20 transition-colors">
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
              <p v-if="slot.error" class="mt-1 text-[11px] text-rose-300">
                {{ slot.error }}
              </p>
            </div>
          </div>

          <div class="mt-5">
            <button
              class="px-5 py-2.5 rounded-lg bg-moss-400 text-ink-950 font-semibold hover:brightness-110 transition disabled:opacity-60 disabled:cursor-not-allowed"
              :disabled="isImageSubmitting || !canUploadImages || hasImageValidationError"
              @click="publishLatestThreeView"
            >
              {{ isImageSubmitting ? '发布处理中...' : (hasExistingSession ? '发布最新三视图（自动重新合成）' : '上传并发布三视图') }}
            </button>
          </div>

          <p v-if="imageSuccessMessage" class="mt-3 text-sm text-sage-300">{{ imageSuccessMessage }}</p>
          <p v-if="imageErrorMessage" class="mt-3 text-sm text-rose-300">{{ imageErrorMessage }}</p>
        </div>

        <div
          v-if="displayComposite"
          class="bg-surface/65 border border-sage-400/20 rounded-2xl p-5 md:p-6 backdrop-blur-xl"
        >
          <div class="mb-4 flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold">当前三视图</h2>
            <span class="text-xs text-on-surface-variant">点击图片查看无损原图</span>
          </div>
          <div class="rounded-xl overflow-hidden border border-sage-300/25 bg-ink-950/25">
            <div class="aspect-[4/3]">
              <img
                :src="displayComposite.composite_preview_url"
                alt="当前三视图"
                class="w-full h-full object-cover cursor-zoom-in"
                @click="openCompositeViewer"
              />
            </div>
          </div>
        </div>

        <div class="bg-surface/65 border border-moss-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl">
          <div class="flex items-start justify-between gap-4 mb-5">
            <div>
              <h2 class="text-lg font-semibold">动态视频区</h2>
              <p class="text-xs text-on-surface-variant mt-1">
                必须上传并发布 2 个本人视频：1 分钟内真人自我介绍 + 妆造风格/演戏混剪。
              </p>
            </div>
            <span
              class="text-xs px-2.5 py-1 rounded-full border"
              :class="allRequiredVideosPublished ? 'border-sage-300/40 text-sage-200 bg-sage-400/10' : 'border-brass-300/40 text-brass-200 bg-brass-400/10'"
            >
              {{ allRequiredVideosPublished ? '已满足双视频要求' : '待补齐双视频' }}
            </span>
          </div>

          <div class="grid xl:grid-cols-2 gap-5">
            <article
              v-for="slot in videoTypeSlots"
              :key="slot.key"
              class="rounded-xl border border-moss-400/20 bg-ink-950/20 p-4 space-y-4"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-moss-100">{{ slot.title }}</p>
                  <p class="text-xs text-on-surface-variant mt-1">{{ slot.subtitle }}</p>
                </div>
                <span class="text-[11px] text-moss-100 border border-moss-300/35 bg-moss-400/10 rounded-full px-2 py-0.5">必传</span>
              </div>

              <div class="aspect-video rounded-lg overflow-hidden border border-moss-400/15 bg-surface/50">
                <video
                  v-if="slot.currentPreview"
                  :src="slot.currentPreview"
                  controls
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex flex-col items-center justify-center gap-2 text-on-surface-variant">
                  <span class="material-symbols-outlined text-3xl">videocam</span>
                  <p class="text-xs">未选择 {{ slot.title }}</p>
                </div>
              </div>

              <label class="mt-3 inline-flex cursor-pointer items-center justify-center w-full rounded-lg border border-moss-300/25 bg-moss-400/10 px-3 py-2 text-sm text-moss-100 hover:bg-moss-400/20 transition-colors">
                选择视频
                <input
                  type="file"
                  accept="video/*"
                  class="hidden"
                  @change="onVideoSelected(slot.key, $event)"
                />
              </label>
              <p class="mt-2 text-[11px] text-on-surface-variant truncate">
                {{ slot.currentFileName || '尚未上传文件' }}
              </p>

              <div class="space-y-2">
                <p class="text-sm font-semibold text-moss-100">上传要求</p>
                <ul class="space-y-2 text-xs text-on-surface-variant">
                  <li v-for="tip in slot.tips" :key="`${slot.key}-${tip}`">- {{ tip }}</li>
                </ul>
              </div>

              <label class="flex items-center gap-2 text-xs text-on-surface-variant">
                <input
                  v-model="videoOwnershipConfirmed[slot.key]"
                  type="checkbox"
                  class="h-4 w-4 rounded border border-moss-300/40 bg-ink-900/70"
                />
                确认该视频为本人出镜
              </label>

              <div class="flex flex-wrap gap-3">
              <button
                class="px-5 py-2.5 rounded-lg border border-moss-300/35 text-moss-100 hover:bg-moss-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="slot.form.uploading || !slot.form.file"
                @click="submitVideo(slot.key)"
              >
                {{ slot.form.uploading ? '视频上传中...' : '上传视频素材' }}
              </button>
              <button
                class="px-5 py-2.5 rounded-lg border border-sage-300/40 text-sage-200 hover:bg-sage-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="slot.form.publishing || !slot.draft"
                @click="publishVideoDraft(slot.key)"
              >
                {{ slot.form.publishing ? '发布中...' : '发布当前视频草稿' }}
              </button>
              </div>
              <p v-if="slot.form.success" class="text-sm text-sage-300">{{ slot.form.success }}</p>
              <p v-if="slot.form.error" class="text-sm text-rose-300">{{ slot.form.error }}</p>

              <div v-if="slot.draft" class="rounded-xl border border-moss-300/20 bg-ink-950/25 p-3">
                <p class="text-xs font-semibold mb-2">视频草稿（未发布）</p>
                <video :src="slot.draft.preview_url" controls class="w-full rounded-lg border border-moss-300/15" />
                <p class="mt-2 text-xs text-on-surface-variant truncate">{{ slot.draftFileName || '未命名文件' }}</p>
              </div>

              <div v-if="slot.published" class="rounded-xl border border-sage-300/25 bg-ink-950/25 p-3">
                <p class="text-xs font-semibold mb-2">已发布视频</p>
                <video :src="slot.published.preview_url" controls class="w-full rounded-lg border border-sage-300/20" />
                <p class="mt-2 text-xs text-on-surface-variant truncate">{{ slot.publishedFileName || '未命名文件' }}</p>
              </div>
            </article>
          </div>

          <div
            class="mt-5 rounded-xl border px-4 py-3"
            :class="allRequiredVideosPublished ? 'border-sage-300/30 bg-sage-400/5' : 'border-brass-300/30 bg-brass-400/5'"
          >
            <p class="text-sm font-semibold">完整度检查</p>
            <p class="mt-1 text-xs text-on-surface-variant">
              <span v-if="allRequiredVideosPublished">两个必填视频都已发布，演员动态视频区完整。</span>
              <span v-else>请补齐并发布“真人自我介绍”和“妆造风格/演戏混剪”两个视频。</span>
            </p>
          </div>
        </div>

        <div class="bg-surface/65 border border-moss-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl">
          <div class="flex flex-wrap items-start justify-between gap-4 mb-5">
            <div>
              <h2 class="text-lg font-semibold">录音素材区</h2>
              <p class="text-xs text-on-surface-variant mt-1">
                可上传一段或多段声音素材，用于展示声线、台词表现或角色声音状态。每条录音都可单独发布、取消发布或删除。
              </p>
            </div>
            <span
              class="text-xs px-2.5 py-1 rounded-full border"
              :class="publishedAudioCount > 0 ? 'border-sage-300/40 text-sage-200 bg-sage-400/10' : 'border-moss-300/35 text-moss-100 bg-moss-400/10'"
            >
              {{ publishedAudioCount > 0 ? `已发布 ${publishedAudioCount} 条录音` : '暂无已发布录音' }}
            </span>
          </div>

          <div class="rounded-2xl border border-moss-400/15 bg-ink-950/20 p-4 md:p-5">
            <div class="flex flex-col lg:flex-row lg:items-center gap-4">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-moss-100">上传新的录音素材</p>
                <p class="mt-1 text-xs text-on-surface-variant">
                  支持常见音频格式，上传后可先试听，再决定是否发布到企业端广场。
                </p>
                <p class="mt-3 text-xs text-on-surface-variant truncate">
                  {{ selectedAudioFileLabel }}
                </p>
              </div>
              <div class="flex flex-wrap gap-3">
                <label class="inline-flex cursor-pointer items-center justify-center rounded-lg border border-moss-300/25 bg-moss-400/10 px-4 py-2.5 text-sm text-moss-100 hover:bg-moss-400/20 transition-colors">
                  选择录音
                  <input
                    type="file"
                    accept="audio/*"
                    multiple
                    class="hidden"
                    @change="onAudioSelected"
                  />
                </label>
                <button
                  class="rounded-lg border border-sage-300/35 px-4 py-2.5 text-sm font-semibold text-sage-200 hover:bg-sage-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
                  :disabled="audioUpload.uploading || !selectedAudioFileCount"
                  @click="submitAudio"
                >
                  {{ audioUpload.uploading ? '录音上传中...' : `上传录音素材${selectedAudioFileCount ? `（${selectedAudioFileCount}）` : ''}` }}
                </button>
              </div>
            </div>
            <p v-if="audioUpload.error" class="mt-3 text-sm text-rose-300">{{ audioUpload.error }}</p>
            <p v-if="audioUpload.success" class="mt-3 text-sm text-sage-300">{{ audioUpload.success }}</p>
          </div>

          <div class="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <article
              v-for="asset in audioAssets"
              :key="asset.id"
              class="rounded-2xl border border-moss-400/15 bg-ink-950/20 p-4 space-y-4"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-moss-100 truncate">{{ asset.source_filename || '未命名录音' }}</p>
                  <p class="mt-1 text-xs text-on-surface-variant">
                    {{ formatAudioMeta(asset) }}
                  </p>
                </div>
                <span
                  class="shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-medium"
                  :class="asset.is_published ? 'border-sage-300/35 bg-sage-400/10 text-sage-200' : 'border-brass-300/35 bg-brass-400/10 text-brass-200'"
                >
                  {{ asset.is_published ? '已发布' : '未发布' }}
                </span>
              </div>

              <div class="rounded-xl border border-moss-400/12 bg-surface/45 p-3">
                <audio :src="asset.preview_url" controls class="w-full" preload="metadata" />
              </div>

              <div class="flex items-center justify-between gap-3">
                <button
                  class="inline-flex min-w-[88px] items-center justify-center rounded-lg border px-3 py-2 text-sm font-medium transition disabled:opacity-60 disabled:cursor-not-allowed"
                  :class="asset.is_published ? 'border-brass-300/35 text-brass-200 hover:bg-brass-400/10' : 'border-sage-300/35 text-sage-200 hover:bg-sage-400/10'"
                  :disabled="audioActionLoadingId === asset.id"
                  @click="toggleAudioPublish(asset)"
                >
                  {{ audioActionLoadingId === asset.id ? '处理中...' : (asset.is_published ? '取消发布' : '发布') }}
                </button>
                <button
                  class="inline-flex min-w-[88px] items-center justify-center rounded-lg border border-rose-300/35 px-3 py-2 text-sm font-medium text-rose-200 hover:bg-rose-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
                  :disabled="audioActionLoadingId === asset.id"
                  @click="deleteAudio(asset)"
                >
                  删除
                </button>
              </div>
            </article>

            <div
              v-if="!audioAssets.length && !audioLoading"
              class="md:col-span-2 xl:col-span-3 rounded-2xl border border-dashed border-moss-400/20 bg-ink-950/15 px-5 py-10 text-center"
            >
              <span class="material-symbols-outlined text-4xl text-moss-200/80">mic</span>
              <p class="mt-3 text-sm font-semibold text-moss-100">还没有录音素材</p>
              <p class="mt-1 text-xs text-on-surface-variant">上传第一条录音后，就可以在这里统一试听、发布和删除。</p>
            </div>
          </div>

          <p v-if="audioLoading" class="mt-4 text-xs text-on-surface-variant">正在加载录音素材...</p>
          <p v-if="audioListError" class="mt-4 text-sm text-rose-300">{{ audioListError }}</p>
        </div>
      </section>
    </main>

    <div
      v-if="compositeViewer.visible && compositeViewer.url"
      class="fixed inset-0 z-[120] bg-black/85 backdrop-blur-sm p-4 md:p-8 flex flex-col"
      @click.self="closeCompositeViewer"
    >
      <div class="mb-3 flex items-center justify-between">
        <p class="text-xs text-ink-200/80">无损原图预览</p>
        <button
          type="button"
          class="rounded-md border border-ink-300/35 px-3 py-1.5 text-xs text-ink-100 hover:bg-white/10 transition"
          @click="closeCompositeViewer"
        >
          关闭
        </button>
      </div>
      <div class="flex-1 min-h-0 rounded-xl border border-ink-300/20 bg-ink-950/40 overflow-hidden">
        <img
          :src="compositeViewer.url"
          alt="三视图无损原图"
          class="w-full h-full object-contain"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ensureAgreementSignedForPublish } from '../lib/agreement'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const loadingExisting = ref(false)

const imageUploading = ref(false)
const imagePublishing = ref(false)
const imageErrorMessage = ref('')
const imageSuccessMessage = ref('')
const latestComposite = ref(null)
const publishedComposite = ref(null)
const compositeViewer = reactive({
  visible: false,
  url: ''
})

const VIDEO_TYPE_INTRO = 'intro'
const VIDEO_TYPE_SHOWREEL = 'showreel'
const INTRO_MAX_DURATION_SECONDS = 60
const MIN_IMAGE_LONG_EDGE_PX = 2000
const VIDEO_TYPE_CONFIGS = [
  {
    key: VIDEO_TYPE_INTRO,
    title: '真人自我介绍',
    subtitle: '时长要求：1 分钟以内',
    tips: [
      '本人出镜，镜头稳定，声音清晰。',
      '建议介绍姓名、年龄段、擅长角色与作品经历。',
      '如超出 1 分钟将无法上传。'
    ]
  },
  {
    key: VIDEO_TYPE_SHOWREEL,
    title: '妆造风格/演戏混剪',
    subtitle: '展示不同妆造或演戏片段',
    tips: [
      '本人出镜，可包含不同妆造、角色与情绪段落。',
      '建议用多个片段混剪，突出可塑性和镜头表现。',
      '可附带台词、动作或情绪转场片段。'
    ]
  }
]

function createVideoFormState() {
  return {
    uploading: false,
    publishing: false,
    error: '',
    success: '',
    file: null,
    fileName: '',
    preview: ''
  }
}

const videoForms = reactive({
  [VIDEO_TYPE_INTRO]: createVideoFormState(),
  [VIDEO_TYPE_SHOWREEL]: createVideoFormState()
})
const audioUpload = reactive({
  uploading: false,
  error: '',
  success: '',
  files: []
})
const videoDrafts = ref({
  [VIDEO_TYPE_INTRO]: null,
  [VIDEO_TYPE_SHOWREEL]: null
})
const publishedVideos = ref({
  [VIDEO_TYPE_INTRO]: null,
  [VIDEO_TYPE_SHOWREEL]: null
})
const audioAssets = ref([])
const audioLoading = ref(false)
const audioListError = ref('')
const audioActionLoadingId = ref(null)
const videoOwnershipConfirmed = reactive({
  [VIDEO_TYPE_INTRO]: false,
  [VIDEO_TYPE_SHOWREEL]: false
})
const guidanceLoading = ref(false)
const guidanceSamples = ref({ left: null, front: null, right: null, all_ready: false })

const images = reactive({
  left: { label: '左侧面图', preview: '', file: null, fileName: '', existingPreview: '', existingFileName: '', error: '' },
  front: { label: '正面图', preview: '', file: null, fileName: '', existingPreview: '', existingFileName: '', error: '' },
  right: { label: '右侧面图', preview: '', file: null, fileName: '', existingPreview: '', existingFileName: '', error: '' }
})

const activeComposite = computed(() => latestComposite.value || publishedComposite.value || null)
const displayComposite = computed(() => latestComposite.value || publishedComposite.value || null)
const hasExistingSession = computed(() => Boolean(activeComposite.value?.session_id))
const hasAnyImageReplacement = computed(() => Boolean(images.left.file || images.front.file || images.right.file))
const hasImageValidationError = computed(() => Boolean(images.left.error || images.front.error || images.right.error))
const isImageSubmitting = computed(() => imageUploading.value || imagePublishing.value)

const imageSlots = computed(() => [
  {
    key: 'left',
    label: images.left.label,
    currentPreview: images.left.preview || images.left.existingPreview,
    displayFileName: images.left.fileName || images.left.existingFileName,
    error: images.left.error
  },
  {
    key: 'front',
    label: images.front.label,
    currentPreview: images.front.preview || images.front.existingPreview,
    displayFileName: images.front.fileName || images.front.existingFileName,
    error: images.front.error
  },
  {
    key: 'right',
    label: images.right.label,
    currentPreview: images.right.preview || images.right.existingPreview,
    displayFileName: images.right.fileName || images.right.existingFileName,
    error: images.right.error
  }
])

const guidanceSampleSlots = computed(() => [
  {
    key: 'left',
    label: '左侧面图',
    previewUrl: guidanceSamples.value?.left?.preview_url || ''
  },
  {
    key: 'front',
    label: '正面图',
    previewUrl: guidanceSamples.value?.front?.preview_url || ''
  },
  {
    key: 'right',
    label: '右侧面图',
    previewUrl: guidanceSamples.value?.right?.preview_url || ''
  }
])

const canUploadImages = computed(() => {
  if (hasExistingSession.value) {
    return hasAnyImageReplacement.value
  }
  return Boolean(images.left.file && images.front.file && images.right.file)
})

const videoTypeSlots = computed(() => VIDEO_TYPE_CONFIGS.map((config) => {
  const draft = videoDrafts.value[config.key] || null
  const published = publishedVideos.value[config.key] || null
  const form = videoForms[config.key]
  return {
    ...config,
    draft,
    published,
    form,
    currentPreview: form.preview || draft?.preview_url || '',
    currentFileName: form.fileName || draft?.source_filename || '',
    draftFileName: draft?.source_filename || extractFileName(draft?.object_key || ''),
    publishedFileName: published?.source_filename || extractFileName(published?.object_key || '')
  }
}))
const allRequiredVideosPublished = computed(() => VIDEO_TYPE_CONFIGS.every((item) => Boolean(publishedVideos.value[item.key]?.id)))
const publishedAudioCount = computed(() => audioAssets.value.filter((item) => item?.is_published).length)
const selectedAudioFileCount = computed(() => audioUpload.files.length)
const selectedAudioFileLabel = computed(() => {
  if (!audioUpload.files.length) return '尚未选择录音文件'
  if (audioUpload.files.length === 1) return audioUpload.files[0]?.name || '已选择 1 个录音文件'
  return `已选择 ${audioUpload.files.length} 个录音文件`
})
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
    images[key].existingPreview = byAngle[key]?.variant_urls?.grid || byAngle[key]?.preview_url || ''
    images[key].existingFileName = byAngle[key]?.source_filename || ''
    images[key].preview = ''
    images[key].file = null
    images[key].fileName = ''
    images[key].error = ''
  }
}

async function onImageSelected(slotKey, event) {
  const slot = images[slotKey]
  const input = event.target
  if (!input?.files?.length) return
  const file = input.files[0]
  slot.error = ''
  imageErrorMessage.value = ''

  try {
    const { width, height } = await getImageDimensions(file)
    const longEdge = Math.max(width, height)
    if (longEdge <= MIN_IMAGE_LONG_EDGE_PX) {
      throw new Error(`${slot.label}清晰度不足：长边需大于 2000 像素，当前为 ${width}x${height}。`)
    }
    if (slot.preview) {
      URL.revokeObjectURL(slot.preview)
    }
    slot.file = file
    slot.fileName = file.name
    slot.preview = URL.createObjectURL(file)
  } catch (error) {
    slot.file = null
    slot.fileName = ''
    if (slot.preview) {
      URL.revokeObjectURL(slot.preview)
      slot.preview = ''
    }
    const message = error instanceof Error ? error.message : '图片校验失败，请更换图片后重试。'
    slot.error = message
    imageErrorMessage.value = message
  } finally {
    input.value = ''
  }
}

async function onVideoSelected(videoType, event) {
  const form = videoForms[videoType]
  const input = event.target
  if (!input?.files?.length) return
  const file = input.files[0]
  form.error = ''
  form.success = ''

  try {
    if (videoType === VIDEO_TYPE_INTRO) {
      const durationSeconds = await getVideoDuration(file)
      if (durationSeconds > INTRO_MAX_DURATION_SECONDS) {
        throw new Error(`自我介绍视频需控制在 1 分钟内，当前约 ${Math.ceil(durationSeconds)} 秒。`)
      }
    }
    if (form.preview) {
      URL.revokeObjectURL(form.preview)
    }
    form.file = file
    form.fileName = file.name
    form.preview = URL.createObjectURL(file)
  } catch (error) {
    form.file = null
    form.fileName = ''
    if (form.preview) {
      URL.revokeObjectURL(form.preview)
      form.preview = ''
    }
    form.error = error instanceof Error ? error.message : '视频读取失败，请重试。'
  } finally {
    input.value = ''
  }
}

async function onAudioSelected(event) {
  const input = event.target
  if (!input?.files?.length) return
  const files = Array.from(input.files)
  audioUpload.error = ''
  audioUpload.success = ''

  try {
    const invalidFile = files.find((file) => !(file.type || '').startsWith('audio/'))
    if (invalidFile) {
      throw new Error(`“${invalidFile.name}”不是音频文件，请重新选择。`)
    }
    audioUpload.files = files
  } catch (error) {
    clearAudioSelection()
    audioUpload.error = error instanceof Error ? error.message : '录音文件读取失败，请重试。'
  } finally {
    input.value = ''
  }
}

function clearVideoSelection(videoType) {
  const form = videoForms[videoType]
  form.file = null
  form.fileName = ''
  if (form.preview) {
    URL.revokeObjectURL(form.preview)
  }
  form.preview = ''
}

function clearAudioSelection() {
  audioUpload.files = []
}

function normalizeVideoTypeState(payload, videoType) {
  if (payload?.[videoType]) {
    return payload[videoType]
  }
  if (videoType === VIDEO_TYPE_INTRO) {
    return {
      draft: payload?.draft || null,
      published: payload?.published || null
    }
  }
  return {
    draft: null,
    published: null
  }
}

function applyVideoState(payload) {
  VIDEO_TYPE_CONFIGS.forEach((item) => {
    const state = normalizeVideoTypeState(payload, item.key)
    videoDrafts.value[item.key] = state?.draft || null
    publishedVideos.value[item.key] = state?.published || null
  })
}

function formatFileSize(size) {
  const value = Number(size || 0)
  if (!Number.isFinite(value) || value <= 0) return '未知大小'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

function formatDateTime(value) {
  if (!value) return '未知时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '未知时间'
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatAudioMeta(asset) {
  return `${formatFileSize(asset?.file_size)} · ${formatDateTime(asset?.created_at)}`
}

function getVideoDuration(file) {
  return new Promise((resolve, reject) => {
    const tempUrl = URL.createObjectURL(file)
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.onloadedmetadata = () => {
      const duration = Number(video.duration || 0)
      URL.revokeObjectURL(tempUrl)
      if (!Number.isFinite(duration) || duration <= 0) {
        reject(new Error('无法读取视频时长，请更换文件后重试。'))
        return
      }
      resolve(duration)
    }
    video.onerror = () => {
      URL.revokeObjectURL(tempUrl)
      reject(new Error('无法解析视频时长，请确认视频文件格式。'))
    }
    video.src = tempUrl
  })
}

function getImageDimensions(file) {
  return new Promise((resolve, reject) => {
    const tempUrl = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => {
      const width = Number(image.naturalWidth || 0)
      const height = Number(image.naturalHeight || 0)
      URL.revokeObjectURL(tempUrl)
      if (!width || !height) {
        reject(new Error('无法读取图片尺寸，请更换文件后重试。'))
        return
      }
      resolve({ width, height })
    }
    image.onerror = () => {
      URL.revokeObjectURL(tempUrl)
      reject(new Error('图片读取失败，请上传有效图片文件。'))
    }
    image.src = tempUrl
  })
}

function openCompositeViewer() {
  const url = displayComposite.value?.composite_original_url || displayComposite.value?.composite_image_url || ''
  if (!url) return
  compositeViewer.url = url
  compositeViewer.visible = true
}

function closeCompositeViewer() {
  compositeViewer.visible = false
  compositeViewer.url = ''
}

async function loadExistingAssets() {
  if (!authStore.state.token) return

  loadingExisting.value = true
  imageErrorMessage.value = ''
  VIDEO_TYPE_CONFIGS.forEach((item) => {
    videoForms[item.key].error = ''
    videoForms[item.key].success = ''
  })
  try {
    const threeViewState = await apiRequest('/portraits/three-view/state', {
      token: authStore.state.token
    })
    latestComposite.value = threeViewState?.draft || null
    publishedComposite.value = threeViewState?.published || null

    const baseComposite = latestComposite.value || publishedComposite.value
    if (baseComposite?.session_id) {
      applySessionToImageSlots(baseComposite)
      imageSuccessMessage.value = '已加载当前三视图素材，替换任意角度后可直接发布更新。'
    }

    const videoState = await apiRequest('/portraits/videos/state', {
      token: authStore.state.token
    })
    applyVideoState(videoState || {})
  } catch (error) {
    const message = error instanceof Error ? error.message : '历史素材加载失败，请稍后重试。'
    imageErrorMessage.value = message
  } finally {
    loadingExisting.value = false
  }
}

async function loadAudioAssets() {
  if (!authStore.state.token) return

  audioLoading.value = true
  audioListError.value = ''
  try {
    const payload = await apiRequest('/portraits/audios', {
      token: authStore.state.token
    })
    audioAssets.value = Array.isArray(payload?.items) ? payload.items : []
  } catch (error) {
    audioListError.value = error instanceof Error ? error.message : '录音素材加载失败，请稍后重试。'
  } finally {
    audioLoading.value = false
  }
}

async function loadGuidanceSamples() {
  if (!authStore.state.token) return
  guidanceLoading.value = true
  try {
    const payload = await apiRequest('/portrait-guidance/samples', {
      token: authStore.state.token
    })
    guidanceSamples.value = payload || { left: null, front: null, right: null, all_ready: false }
  } catch (error) {
    console.warn('portrait guidance samples load failed', error)
  } finally {
    guidanceLoading.value = false
  }
}

async function publishLatestThreeView() {
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
  if (hasImageValidationError.value) {
    imageErrorMessage.value = '图片清晰度校验未通过，请修正后再提交。'
    return
  }

  imageUploading.value = true
  imageErrorMessage.value = ''
  imageSuccessMessage.value = ''
  try {
    const gate = await ensureAgreementSignedForPublish({
      token: authStore.state.token
    })
    if (!gate.allowed) {
      return
    }

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

    imagePublishing.value = true
    try {
      const published = await apiRequest('/portraits/three-view/publish', {
        method: 'POST',
        token: authStore.state.token
      })
      publishedComposite.value = published
      latestComposite.value = null
      applySessionToImageSlots(published)
      if (usedFallback) {
        imageSuccessMessage.value = '已自动切换为后端上传链路并完成“重新合成 + 发布”流程。'
      } else {
        imageSuccessMessage.value = hadExisting
          ? '已发布最新三视图，企业端看到的将是最新版本。'
          : '三视图已生成并发布成功。'
      }
    } finally {
      imagePublishing.value = false
    }
  } catch (error) {
    imageErrorMessage.value = error instanceof Error ? error.message : '发布失败，请稍后重试。'
  } finally {
    imageUploading.value = false
  }
}

async function submitVideo(videoType) {
  const form = videoForms[videoType]
  if (!authStore.state.token) {
    form.error = '登录状态失效，请重新登录。'
    return
  }
  if (!form.file) {
    form.error = '请先选择视频文件。'
    return
  }
  if (!videoOwnershipConfirmed[videoType]) {
    form.error = '请先勾选“确认该视频为本人出镜”。'
    return
  }

  form.uploading = true
  form.error = ''
  form.success = ''
  try {
    const file = form.file
    let result = null
    let usedFallback = false
    try {
      result = await submitVideoDirectFlow(file, videoType)
    } catch (directError) {
      console.warn('video direct upload fallback triggered', directError)
      result = await submitVideoLegacyFlow(file, videoType)
      usedFallback = true
    }
    videoDrafts.value[videoType] = result
    if (publishedVideos.value[videoType] && publishedVideos.value[videoType].id === result.id) {
      publishedVideos.value[videoType] = null
    }
    clearVideoSelection(videoType)
    form.success = usedFallback
      ? '直传链路不可用，已自动切换为后端上传并完成保存。'
      : '视频上传成功，已保存为新的素材版本。'
  } catch (error) {
    form.error = error instanceof Error ? error.message : '视频上传失败，请稍后重试。'
  } finally {
    form.uploading = false
  }
}

async function publishVideoDraft(videoType) {
  const form = videoForms[videoType]
  if (!authStore.state.token) {
    form.error = '登录状态失效，请重新登录。'
    return
  }
  if (!videoDrafts.value[videoType]?.id) {
    form.error = '暂无可发布的视频草稿。'
    return
  }
  if (!videoOwnershipConfirmed[videoType]) {
    form.error = '请先勾选“确认该视频为本人出镜”。'
    return
  }

  form.publishing = true
  form.error = ''
  form.success = ''
  try {
    const gate = await ensureAgreementSignedForPublish({
      token: authStore.state.token
    })
    if (!gate.allowed) {
      return
    }

    const published = await apiRequest('/portraits/videos/publish', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        video_type: videoType
      }
    })
    publishedVideos.value[videoType] = published
    videoDrafts.value[videoType] = null
    form.success = '视频草稿已发布，企业用户可在广场查看。'
  } catch (error) {
    const message = error instanceof Error ? error.message : '视频发布失败，请稍后重试。'
    form.error = message
  } finally {
    form.publishing = false
  }
}

async function submitAudio() {
  if (!authStore.state.token) {
    audioUpload.error = '登录状态失效，请重新登录。'
    return
  }
  if (!audioUpload.files.length) {
    audioUpload.error = '请先选择录音文件。'
    return
  }

  audioUpload.uploading = true
  audioUpload.error = ''
  audioUpload.success = ''
  try {
    const uploaded = []
    for (const file of audioUpload.files) {
      const formData = new FormData()
      formData.append('audio_file', file)
      const result = await apiRequest('/portraits/audios', {
        method: 'POST',
        token: authStore.state.token,
        formData
      })
      uploaded.push(result)
    }
    audioAssets.value = [...uploaded.reverse(), ...audioAssets.value]
    clearAudioSelection()
    audioUpload.success = uploaded.length > 1
      ? `已上传 ${uploaded.length} 条录音素材，可根据需要选择发布到企业端。`
      : '录音素材上传成功，可根据需要选择发布到企业端。'
  } catch (error) {
    audioUpload.error = error instanceof Error ? error.message : '录音上传失败，请稍后重试。'
  } finally {
    audioUpload.uploading = false
  }
}

async function toggleAudioPublish(asset) {
  if (!authStore.state.token) {
    audioListError.value = '登录状态失效，请重新登录。'
    return
  }
  if (!asset?.id) return

  audioActionLoadingId.value = asset.id
  audioListError.value = ''
  try {
    if (!asset.is_published) {
      const gate = await ensureAgreementSignedForPublish({
        token: authStore.state.token
      })
      if (!gate.allowed) {
        return
      }
    }

    const updated = await apiRequest('/portraits/audios/state', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        audio_id: asset.id,
        published: !asset.is_published
      }
    })
    const existing = audioAssets.value.find((item) => item.id === updated.id)
    if (existing) {
      existing.is_published = updated.is_published
      existing.superseded_at = updated.superseded_at
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '录音发布状态切换失败，请稍后重试。'
    audioListError.value = message
  } finally {
    audioActionLoadingId.value = null
  }
}

async function deleteAudio(asset) {
  if (!authStore.state.token) {
    audioListError.value = '登录状态失效，请重新登录。'
    return
  }
  if (!asset?.id) return

  const confirmed = window.confirm(`确认永久删除录音素材“${asset.source_filename || '未命名录音'}”吗？删除后无法恢复。`)
  if (!confirmed) return

  audioActionLoadingId.value = asset.id
  audioListError.value = ''
  try {
    await apiRequest(`/portraits/audios/${asset.id}`, {
      method: 'DELETE',
      token: authStore.state.token
    })
    audioAssets.value = audioAssets.value.filter((item) => item.id !== asset.id)
  } catch (error) {
    audioListError.value = error instanceof Error ? error.message : '录音删除失败，请稍后重试。'
  } finally {
    audioActionLoadingId.value = null
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

async function submitVideoDirectFlow(file, videoType) {
  const plan = await apiRequest('/portraits/videos/presign', {
    method: 'POST',
    token: authStore.state.token,
    body: {
      video_type: videoType,
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

async function submitVideoLegacyFlow(file, videoType) {
  const formData = new FormData()
  formData.append('video_file', file)
  formData.append('video_type', videoType)
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
  await Promise.all([
    loadGuidanceSamples(),
    loadExistingAssets(),
    loadAudioAssets()
  ])
})
</script>
