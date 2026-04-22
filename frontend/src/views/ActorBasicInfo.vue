<template>
  <div class="min-h-screen bg-background text-on-surface">
    <main class="max-w-6xl mx-auto px-6 md:px-8 pt-24 pb-14 space-y-8">
      <header class="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold tracking-tight">演员基本信息</h1>
          <p class="mt-2 text-sm text-on-surface-variant">
            管理个人资料、身材参数、接戏要求。头像默认使用三视图合成图自动生成。
          </p>
        </div>
        <div class="text-xs text-on-surface-variant">
          资料完整度：<span class="text-sky-300 font-semibold">{{ profileCompletion }}%</span>
        </div>
      </header>

      <section class="bg-surface/65 border border-sky-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl">
        <div class="flex flex-col md:flex-row md:items-center gap-5">
          <div class="w-24 h-24 rounded-full overflow-hidden border border-sky-300/30 bg-slate-950/30 flex-shrink-0">
            <img
              v-if="basicInfo?.avatar_url"
              :src="basicInfo.avatar_url"
              alt="演员头像"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-sky-200">
              <span class="material-symbols-outlined text-3xl">person</span>
            </div>
          </div>

          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-sky-100">头像设置</p>
            <p class="mt-1 text-xs text-on-surface-variant">
              {{
                basicInfo?.avatar_source === 'three_view'
                  ? '已使用正面照上半部分自动裁剪头像。'
                  : '暂无三视图合成图，请先上传并发布三视图后自动生成头像。'
              }}
            </p>
            <div class="mt-3 flex flex-wrap gap-3">
              <button
                class="px-4 py-2 rounded-lg border border-sky-300/35 text-sm text-sky-100 hover:bg-sky-400/10 transition"
                @click="goToPortraitUpload"
              >
                前往肖像上传
              </button>
            </div>
          </div>
        </div>
      </section>

      <form class="space-y-6" @submit.prevent="saveBasicInfo">
        <section class="bg-surface/65 border border-sky-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl space-y-4">
          <h2 class="text-lg font-semibold">基础资料</h2>
          <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">姓名</span>
              <input
                v-model="form.name"
                type="text"
                maxlength="64"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
                placeholder="请输入姓名"
              />
            </label>

            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">年龄</span>
              <input
                v-model.number="form.age"
                type="number"
                min="0"
                max="100"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
              />
            </label>

            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">身高（cm）</span>
              <input
                v-model.number="form.height"
                type="number"
                min="0"
                max="250"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
              />
            </label>

            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">体重（kg）</span>
              <input
                v-model.number="form.weight_kg"
                type="number"
                min="0"
                max="300"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
              />
            </label>

            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">常驻地</span>
              <input
                v-model="form.location"
                type="text"
                maxlength="64"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
                placeholder="如：上海"
              />
            </label>

            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">籍贯</span>
              <input
                v-model="form.hometown"
                type="text"
                maxlength="64"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
                placeholder="如：四川成都"
              />
            </label>
          </div>
        </section>

        <section class="bg-surface/65 border border-sky-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl space-y-4">
          <h2 class="text-lg font-semibold">身材参数</h2>
          <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">胸围（cm）</span>
              <input
                v-model.number="form.bust_cm"
                type="number"
                min="0"
                max="200"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
              />
            </label>
            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">腰围（cm）</span>
              <input
                v-model.number="form.waist_cm"
                type="number"
                min="0"
                max="200"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
              />
            </label>
            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">臀围（cm）</span>
              <input
                v-model.number="form.hip_cm"
                type="number"
                min="0"
                max="220"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
              />
            </label>
            <label class="space-y-1">
              <span class="text-xs text-on-surface-variant">鞋码</span>
              <input
                v-model="form.shoe_size"
                type="text"
                maxlength="16"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
                placeholder="如：38 / 39"
              />
            </label>
          </div>
        </section>

        <section class="bg-surface/65 border border-sky-400/10 rounded-2xl p-5 md:p-6 backdrop-blur-xl space-y-4">
          <h2 class="text-lg font-semibold">职业信息与接戏偏好</h2>

          <div class="rounded-2xl border border-sky-400/15 bg-slate-950/20 p-4 md:p-5 space-y-4">
            <div>
              <p class="text-sm font-semibold text-sky-100">自我定价</p>
              <p class="mt-1 text-xs text-on-surface-variant">
                设置你的基础合作报价，企业端沟通时可更快了解合作预期。
              </p>
            </div>

            <div class="grid lg:grid-cols-[1.2fr_1fr] gap-4">
              <div class="space-y-2">
                <span class="text-xs text-on-surface-variant">计费方式</span>
                <div class="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    class="rounded-xl border px-4 py-3 text-left transition"
                    :class="form.pricing_unit === 'day'
                      ? 'border-sky-300/40 bg-sky-400/12 text-sky-50 shadow-[0_0_0_1px_rgba(125,211,252,0.18)]'
                      : 'border-sky-300/15 bg-slate-950/25 text-on-surface-variant hover:border-sky-300/30 hover:text-sky-100'"
                    @click="form.pricing_unit = 'day'"
                  >
                    <p class="text-sm font-semibold">按天计费</p>
                    <p class="mt-1 text-xs opacity-80">适合通告、拍摄天数明确的项目</p>
                  </button>
                  <button
                    type="button"
                    class="rounded-xl border px-4 py-3 text-left transition"
                    :class="form.pricing_unit === 'project'
                      ? 'border-sky-300/40 bg-sky-400/12 text-sky-50 shadow-[0_0_0_1px_rgba(125,211,252,0.18)]'
                      : 'border-sky-300/15 bg-slate-950/25 text-on-surface-variant hover:border-sky-300/30 hover:text-sky-100'"
                    @click="form.pricing_unit = 'project'"
                  >
                    <p class="text-sm font-semibold">按项目计费</p>
                    <p class="mt-1 text-xs opacity-80">适合整包合作、角色打包报价</p>
                  </button>
                </div>
              </div>

              <label class="space-y-2">
                <span class="text-xs text-on-surface-variant">
                  价格（元/{{ form.pricing_unit === 'day' ? '天' : '项目' }}）
                </span>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-sky-200/80">￥</span>
                  <input
                    v-model.number="form.pricing_amount"
                    type="number"
                    min="0"
                    max="100000000"
                    step="1"
                    class="w-full rounded-xl border border-sky-300/20 bg-slate-950/30 pl-8 pr-3 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
                    :placeholder="form.pricing_unit === 'day' ? '例如：3000' : '例如：20000'"
                  />
                </div>
                <p class="text-[11px] text-on-surface-variant">
                  当前展示为基础参考报价，实际合作价格可根据角色、档期和项目内容再沟通。
                </p>
              </label>
            </div>
          </div>

          <label class="space-y-1 block">
            <span class="text-xs text-on-surface-variant">擅长标签</span>
            <div class="rounded-lg border border-sky-300/20 bg-slate-950/30 p-2.5">
              <div class="flex flex-wrap gap-2 min-h-[30px]">
                <span
                  v-for="(tag, index) in form.tags"
                  :key="`${tag}-${index}`"
                  class="inline-flex items-center gap-1 rounded-full border border-sky-300/30 bg-sky-400/10 px-2.5 py-1 text-xs text-sky-100"
                >
                  {{ tag }}
                  <button
                    type="button"
                    class="text-sky-200/80 hover:text-rose-200"
                    @click="removeTag(index)"
                  >
                    <span class="material-symbols-outlined text-sm leading-none">close</span>
                  </button>
                </span>
              </div>
              <div class="mt-2 flex gap-2">
                <input
                  v-model="tagDraft"
                  type="text"
                  maxlength="24"
                  placeholder="输入标签后回车，例如：古装、都市、武打"
                  class="flex-1 rounded-lg border border-sky-300/20 bg-slate-900/50 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
                  @keydown="onTagKeydown"
                />
                <button
                  type="button"
                  class="px-3 py-2 rounded-lg border border-sky-300/30 text-xs text-sky-100 hover:bg-sky-400/10"
                  @click="appendTag()"
                >
                  添加
                </button>
              </div>
              <div class="mt-2 flex flex-wrap gap-2">
                <button
                  v-for="quickTag in quickTagSuggestions"
                  :key="quickTag"
                  type="button"
                  class="px-2.5 py-1 rounded-full border border-white/10 text-[11px] text-on-surface-variant hover:text-sky-100 hover:border-sky-300/30 transition"
                  @click="appendTag(quickTag)"
                >
                  {{ quickTag }}
                </button>
              </div>
            </div>
          </label>

          <label class="space-y-1 block">
            <span class="text-xs text-on-surface-variant">个人简介</span>
            <textarea
              v-model="form.bio"
              rows="4"
              maxlength="2000"
              class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
              placeholder="可填写代表作品、擅长角色、训练背景等"
            />
          </label>

          <div class="grid md:grid-cols-2 gap-4">
            <label class="space-y-1 block">
              <span class="text-xs text-on-surface-variant">接戏要求</span>
              <textarea
                v-model="form.acting_requirements"
                rows="5"
                maxlength="2000"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
                placeholder="如：希望有完整剧本、角色成长线清晰、提供基础排练周期等"
              />
            </label>

            <label class="space-y-1 block">
              <span class="text-xs text-on-surface-variant">不接受的戏/条件</span>
              <textarea
                v-model="form.rejected_requirements"
                rows="5"
                maxlength="2000"
                class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
                placeholder="如：不接裸露戏、危险动作需专业替身、拒绝过度改词等"
              />
            </label>
          </div>

          <label class="space-y-1 block">
            <span class="text-xs text-on-surface-variant">档期备注</span>
            <textarea
              v-model="form.availability_note"
              rows="3"
              maxlength="1000"
              class="w-full rounded-lg border border-sky-300/20 bg-slate-950/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
              placeholder="如：可接受异地拍摄，提前 7 天确认档期"
            />
          </label>
        </section>

        <p v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</p>
        <p v-if="successMessage" class="text-sm text-emerald-300">{{ successMessage }}</p>

        <div class="flex items-center gap-3">
          <button
            type="submit"
            :disabled="saving || loading"
            class="px-6 py-2.5 rounded-lg bg-sky-400 text-slate-950 font-semibold hover:brightness-110 transition disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {{ saving ? '保存中...' : '保存基本信息' }}
          </button>
          <button
            type="button"
            :disabled="saving || loading"
            class="px-6 py-2.5 rounded-lg border border-sky-300/30 text-sky-100 hover:bg-sky-400/10 transition disabled:opacity-60 disabled:cursor-not-allowed"
            @click="loadBasicInfo"
          >
            重新加载
          </button>
        </div>
      </form>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const basicInfo = ref(null)
const tagDraft = ref('')

const quickTagSuggestions = [
  '古装',
  '都市',
  '喜剧',
  '正剧',
  '动作戏',
  '舞蹈',
  '武术',
  '配音'
]

const form = reactive({
  name: '',
  age: 0,
  height: 0,
  weight_kg: 0,
  location: '',
  hometown: '',
  bust_cm: 0,
  waist_cm: 0,
  hip_cm: 0,
  shoe_size: '',
  bio: '',
  tags: [],
  acting_requirements: '',
  rejected_requirements: '',
  availability_note: '',
  pricing_unit: 'project',
  pricing_amount: 0
})

const profileCompletion = computed(() => {
  const checks = [
    Boolean(form.name.trim()),
    form.age > 0,
    form.height > 0,
    Boolean(form.location.trim()),
    Boolean(form.hometown.trim()),
    Boolean(form.bio.trim()),
    form.tags.length > 0,
    Boolean(form.acting_requirements.trim()),
    form.pricing_amount > 0
  ]
  const done = checks.filter(Boolean).length
  return Math.round((done / checks.length) * 100)
})

function applyBasicInfo(payload) {
  basicInfo.value = payload || null
  form.name = payload?.name || ''
  form.age = Number(payload?.age || 0)
  form.height = Number(payload?.height || 0)
  form.weight_kg = Number(payload?.weight_kg || 0)
  form.location = payload?.location || ''
  form.hometown = payload?.hometown || ''
  form.bust_cm = Number(payload?.bust_cm || 0)
  form.waist_cm = Number(payload?.waist_cm || 0)
  form.hip_cm = Number(payload?.hip_cm || 0)
  form.shoe_size = payload?.shoe_size || ''
  form.bio = payload?.bio || ''
  form.tags = Array.isArray(payload?.tags) ? [...payload.tags] : []
  form.acting_requirements = payload?.acting_requirements || ''
  form.rejected_requirements = payload?.rejected_requirements || ''
  form.availability_note = payload?.availability_note || ''
  form.pricing_unit = payload?.pricing_unit === 'day' ? 'day' : 'project'
  form.pricing_amount = Number(payload?.pricing_amount || 0)
}

function normalizeInt(value, minValue, maxValue) {
  const parsed = Number.parseInt(String(value || 0), 10)
  if (!Number.isFinite(parsed)) return minValue
  if (parsed < minValue) return minValue
  if (parsed > maxValue) return maxValue
  return parsed
}

function buildSubmitPayload() {
  return {
    name: form.name.trim(),
    age: normalizeInt(form.age, 0, 100),
    height: normalizeInt(form.height, 0, 250),
    weight_kg: normalizeInt(form.weight_kg, 0, 300),
    location: form.location.trim(),
    hometown: form.hometown.trim(),
    bust_cm: normalizeInt(form.bust_cm, 0, 200),
    waist_cm: normalizeInt(form.waist_cm, 0, 200),
    hip_cm: normalizeInt(form.hip_cm, 0, 220),
    shoe_size: form.shoe_size.trim(),
    bio: form.bio.trim(),
    tags: form.tags,
    acting_requirements: form.acting_requirements.trim(),
    rejected_requirements: form.rejected_requirements.trim(),
    availability_note: form.availability_note.trim(),
    pricing_unit: form.pricing_unit === 'day' ? 'day' : 'project',
    pricing_amount: normalizeInt(form.pricing_amount, 0, 100000000)
  }
}

function appendTag(preset = '') {
  const raw = (preset || tagDraft.value || '').trim()
  if (!raw) return
  if (form.tags.includes(raw)) {
    tagDraft.value = ''
    return
  }
  if (form.tags.length >= 20) return
  form.tags.push(raw.slice(0, 24))
  tagDraft.value = ''
}

function removeTag(index) {
  form.tags.splice(index, 1)
}

function onTagKeydown(event) {
  if (event.key === 'Enter' || event.key === ',' || event.key === '，') {
    event.preventDefault()
    appendTag()
  }
}

async function loadBasicInfo() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const payload = await apiRequest('/actors/me/basic-info', {
      token: authStore.state.token
    })
    applyBasicInfo(payload)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '资料加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function saveBasicInfo() {
  if (!authStore.state.token) return
  if (!form.name.trim()) {
    errorMessage.value = '姓名不能为空。'
    return
  }

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const payload = await apiRequest('/actors/me/basic-info', {
      method: 'PUT',
      token: authStore.state.token,
      body: buildSubmitPayload()
    })
    applyBasicInfo(payload)
    successMessage.value = '基本信息已保存。'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存失败，请稍后重试。'
  } finally {
    saving.value = false
  }
}

function goToPortraitUpload() {
  router.push('/edit-portrait')
}

onMounted(async () => {
  await loadBasicInfo()
})
</script>
