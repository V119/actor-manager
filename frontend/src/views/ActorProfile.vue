<template>
  <div class="flex-1 pt-24 px-8 pb-12 overflow-y-auto bg-background text-on-surface">
    <div class="max-w-7xl mx-auto space-y-8">
      <div v-if="loading" class="text-sm text-on-surface-variant">正在加载演员已发布信息...</div>
      <div v-else-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</div>

      <template v-else-if="detail">
        <section class="bg-surface/60 backdrop-blur-xl border border-moss-400/10 p-6 rounded-xl">
          <div class="flex flex-col xl:flex-row gap-6 items-start xl:justify-between">
            <div class="flex flex-col md:flex-row gap-6 items-start flex-1">
              <div class="w-40 h-52 rounded-xl overflow-hidden border border-moss-300/20 bg-ink-950/30">
                <img :src="coverImage" :alt="detail.actor.name" class="w-full h-full object-cover" />
              </div>
              <div class="space-y-3">
                <h1 class="text-3xl font-bold text-on-surface">{{ detail.actor.name }}</h1>
                <p class="text-xs text-on-surface-variant">ID: {{ detail.actor.external_id }}</p>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="tag in detail.actor.tags"
                    :key="tag"
                    class="px-2.5 py-0.5 text-[10px] font-semibold rounded bg-moss-400/10 text-moss-300 border border-moss-400/20"
                  >
                    {{ tag }}
                  </span>
                </div>
                <p class="text-sm text-on-surface-variant max-w-3xl">{{ detail.actor.bio }}</p>
              </div>
            </div>

            <div class="w-full xl:w-80 rounded-2xl border border-sage-300/20 bg-sage-500/5 p-4 space-y-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-[11px] tracking-[0.18em] uppercase text-sage-200/80">签约状态</p>
                  <p class="mt-2 text-sm text-on-surface-variant">
                    {{ detail.is_signed_by_current_enterprise ? '该演员已加入当前企业的签约列表。' : '确认签约后，可在左侧“签约演员”中随时查看。' }}
                  </p>
                </div>
                <span
                  class="rounded-full border px-3 py-1 text-xs font-semibold"
                  :class="detail.is_signed_by_current_enterprise ? 'border-sage-300/25 bg-sage-500/15 text-sage-200' : 'border-brass-300/25 bg-brass-500/10 text-brass-100'"
                >
                  {{ detail.is_signed_by_current_enterprise ? '已签约' : '待签约' }}
                </span>
              </div>

              <button
                type="button"
                class="w-full rounded-xl px-4 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60"
                :class="detail.is_signed_by_current_enterprise ? 'bg-sage-500/15 text-sage-200 border border-sage-300/25' : 'bg-moss-400 text-ink-950 hover:brightness-110'"
                :disabled="detail.is_signed_by_current_enterprise || signing"
                @click="handleSignActor"
              >
                {{ detail.is_signed_by_current_enterprise ? '已签约' : signing ? '签约中...' : '签约' }}
              </button>

              <button
                type="button"
                class="w-full rounded-xl border border-moss-300/25 bg-moss-500/10 px-4 py-3 text-sm font-semibold text-moss-100 transition hover:bg-moss-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="!detail.is_signed_by_current_enterprise || addingToCart || actorInCart"
                @click="handleAddToCart"
              >
                {{
                  !detail.is_signed_by_current_enterprise
                    ? '签约后可加入购物车'
                    : actorInCart
                      ? '已在购物车'
                      : addingToCart
                        ? '加入中...'
                        : '加入购物车'
                }}
              </button>

              <button
                type="button"
                class="w-full rounded-xl border border-moss-300/25 px-4 py-2.5 text-xs text-moss-100 transition hover:bg-moss-500/10"
                @click="goToCartCheckout"
              >
                前往购物车与结算
              </button>

              <p v-if="signActionMessage" class="text-sm text-sage-200 leading-6">{{ signActionMessage }}</p>
              <p v-if="signActionError" class="rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-200 leading-6">
                {{ signActionError }}
              </p>
            </div>
          </div>
        </section>

        <section class="grid xl:grid-cols-[1.2fr_1fr] gap-6">
          <div class="bg-surface/60 border border-moss-400/15 rounded-xl p-5">
            <h2 class="text-lg font-semibold">演员基本信息</h2>
            <div class="mt-4 grid md:grid-cols-2 xl:grid-cols-3 gap-3">
              <div
                v-for="item in basicInfoItems"
                :key="item.label"
                class="rounded-xl border border-moss-300/15 bg-ink-950/20 px-4 py-3"
              >
                <p class="text-[11px] tracking-[0.16em] uppercase text-ink-400">{{ item.label }}</p>
                <p class="mt-2 text-sm font-medium text-moss-50 break-words">{{ item.value }}</p>
              </div>
            </div>

            <div class="mt-5 rounded-xl border border-moss-300/15 bg-ink-950/20 px-4 py-4">
              <p class="text-[11px] tracking-[0.16em] uppercase text-ink-400">擅长标签</p>
              <div v-if="detail.actor.tags?.length" class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="tag in detail.actor.tags"
                  :key="tag"
                  class="px-2.5 py-1 text-xs font-semibold rounded-full bg-moss-400/10 text-moss-300 border border-moss-400/20"
                >
                  {{ tag }}
                </span>
              </div>
              <p v-else class="mt-3 text-sm text-on-surface-variant">未填写擅长标签</p>
            </div>
          </div>

          <div class="bg-surface/60 border border-moss-400/15 rounded-xl p-5">
            <h2 class="text-lg font-semibold">合作偏好与说明</h2>
            <div class="mt-4 space-y-4">
              <div
                v-for="item in profileTextBlocks"
                :key="item.label"
                class="rounded-xl border border-moss-300/15 bg-ink-950/20 px-4 py-4"
              >
                <p class="text-[11px] tracking-[0.16em] uppercase text-ink-400">{{ item.label }}</p>
                <p class="mt-2 text-sm leading-7 text-on-surface-variant whitespace-pre-wrap">{{ item.value }}</p>
              </div>
            </div>
          </div>
        </section>

        <section class="grid lg:grid-cols-2 gap-6">
          <div class="bg-surface/60 border border-sage-300/20 rounded-xl p-4">
            <h2 class="text-lg font-semibold mb-3">三视图</h2>
            <div v-if="detail.published_three_view" class="space-y-4">
              <div class="aspect-[4/3] rounded-lg overflow-hidden border border-sage-300/20">
                <img
                  :src="detail.published_three_view.composite_variant_urls?.detail || detail.published_three_view.composite_preview_url"
                  alt="已发布三视图"
                  class="w-full h-full object-cover"
                />
              </div>
              <p class="text-xs leading-6 text-on-surface-variant">
                展示当前已发布的三视图合成图。
              </p>
            </div>
            <div v-else class="text-xs text-on-surface-variant">暂无已发布三视图。</div>
          </div>

          <div class="bg-surface/60 border border-sage-300/20 rounded-xl p-4">
            <h2 class="text-lg font-semibold mb-3">视频</h2>
            <div v-if="publishedVideos.length" class="space-y-4">
              <div
                v-for="video in publishedVideos"
                :key="video.id"
                class="rounded-lg border border-sage-300/20 bg-ink-950/20 p-3 space-y-2"
              >
                <p class="text-xs font-semibold text-sage-200">
                  {{ videoLabelMap[video.video_type] || '已发布视频' }}
                </p>
                <video :src="video.preview_url" controls class="w-full rounded-lg border border-sage-300/20" />
              </div>
            </div>
            <div v-else class="text-xs text-on-surface-variant">暂无已发布视频。</div>
          </div>
        </section>

        <section class="bg-surface/60 border border-sage-300/20 rounded-xl p-4">
          <h2 class="text-lg font-semibold mb-3">已发布风格图</h2>
          <div v-if="detail.published_styles?.length" class="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
            <div
              v-for="item in detail.published_styles"
              :key="item.id"
              class="break-inside-avoid rounded-lg overflow-hidden border border-sage-300/20 bg-ink-950/20"
            >
              <div class="relative">
                <img :src="item.preview_url || item.image_url" :alt="item.style_name" class="w-full h-auto" />
                <div class="absolute left-3 top-3 flex flex-wrap gap-2">
                  <span class="rounded-full border border-moss-300/35 bg-ink-950/75 px-2.5 py-1 text-[11px] font-semibold text-moss-100 backdrop-blur">
                    {{ item.style_name }}
                  </span>
                  <span class="rounded-full border border-sage-300/30 bg-ink-950/75 px-2.5 py-1 text-[11px] font-semibold text-sage-100 backdrop-blur">
                    {{ styleCategoryLabelMap[item.style_category] || item.style_category || '未分类' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-xs text-on-surface-variant">暂无已发布风格图。</div>
        </section>

        <section class="bg-surface/60 border border-sage-300/20 rounded-xl p-4">
          <h2 class="text-lg font-semibold mb-3">录音</h2>
          <div v-if="publishedAudios.length" class="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div
              v-for="audio in publishedAudios"
              :key="audio.id"
              class="rounded-lg border border-sage-300/20 bg-ink-950/20 p-3 space-y-2"
            >
              <p class="text-xs font-semibold text-sage-200 truncate">
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
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'
import {
  ensureEnterpriseAgreementSigned
} from '../lib/enterpriseAgreement'
import { addEnterpriseCartItem, fetchEnterpriseCart } from '../lib/payment'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const detail = ref(null)
const signing = ref(false)
const addingToCart = ref(false)
const actorInCart = ref(false)
const signActionMessage = ref('')
const signActionError = ref('')
const videoLabelMap = {
  intro: '真人自我介绍',
  showreel: '妆造风格/演戏混剪'
}
const styleCategoryLabelMap = {
  cinematic: '电影感',
  commercial: '商业感',
  'sci-fi': '科幻感',
  noir: '黑色电影',
  'oil-painting': '油画感',
  custom: '自定义'
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
  if (detail.value?.published_three_view?.avatar_variant_urls?.thumb) {
    return detail.value.published_three_view.avatar_variant_urls.thumb
  }
  if (detail.value?.published_three_view?.avatar_url) {
    return detail.value.published_three_view.avatar_url
  }
  if (detail.value?.published_three_view?.composite_preview_url) {
    return detail.value.published_three_view.composite_preview_url
  }
  if (publishedVideos.value.length) {
    return publishedVideos.value[0].preview_url || fallbackCover
  }
  return fallbackCover
})

const basicInfoItems = computed(() => {
  const actor = detail.value?.actor
  if (!actor) return []
  return [
    { label: '年龄', value: formatNumberField(actor.age, '岁') },
    { label: '身高', value: formatNumberField(actor.height, 'cm') },
    { label: '体重', value: formatNumberField(actor.weight_kg, 'kg') },
    { label: '常驻地', value: formatTextField(actor.location) },
    { label: '籍贯', value: formatTextField(actor.hometown) },
    { label: '鞋码', value: formatTextField(actor.shoe_size) },
    { label: '胸围', value: formatNumberField(actor.bust_cm, 'cm') },
    { label: '腰围', value: formatNumberField(actor.waist_cm, 'cm') },
    { label: '臀围', value: formatNumberField(actor.hip_cm, 'cm') },
    { label: '基础报价', value: formatPricing(actor.pricing_amount, actor.pricing_unit) }
  ]
})

const profileTextBlocks = computed(() => {
  const actor = detail.value?.actor
  if (!actor) return []
  return [
    { label: '个人简介', value: formatTextField(actor.bio, '未填写个人简介') },
    { label: '接戏要求', value: formatTextField(actor.acting_requirements, '未填写接戏要求') },
    { label: '不接内容', value: formatTextField(actor.rejected_requirements, '未填写不接内容') },
    { label: '档期说明', value: formatTextField(actor.availability_note, '未填写档期说明') }
  ]
})

function formatTextField(value, emptyText = '未填写') {
  const normalized = String(value || '').trim()
  return normalized || emptyText
}

function formatNumberField(value, suffix) {
  const number = Number(value || 0)
  if (!Number.isFinite(number) || number <= 0) {
    return '未填写'
  }
  return `${number}${suffix}`
}

function formatPricing(amount, unit) {
  const number = Number(amount || 0)
  if (!Number.isFinite(number) || number <= 0) {
    return '未填写'
  }
  return `￥${number}/${unit === 'day' ? '天' : '项目'}`
}

async function handleSignActor() {
  if (!authStore.state.token || !detail.value?.actor?.actor_id || signing.value) return
  signing.value = true
  signActionMessage.value = ''
  signActionError.value = ''
  try {
    const payload = await apiRequest(`/enterprise/signed-actors/${detail.value.actor.actor_id}`, {
      method: 'POST',
      token: authStore.state.token
    })
    detail.value = {
      ...detail.value,
      is_signed_by_current_enterprise: true
    }
    actorInCart.value = true
    signActionMessage.value = `${payload?.message || '已签约该演员。'}已自动加入购物车。`
  } catch (error) {
    signActionError.value = error instanceof Error ? error.message : '签约失败，请稍后重试。'
  } finally {
    signing.value = false
  }
}

async function handleAddToCart() {
  if (!authStore.state.token || !detail.value?.actor?.actor_id || addingToCart.value || actorInCart.value) return
  addingToCart.value = true
  signActionMessage.value = ''
  signActionError.value = ''
  try {
    await addEnterpriseCartItem({
      token: authStore.state.token,
      actorId: detail.value.actor.actor_id
    })
    actorInCart.value = true
    signActionMessage.value = '已加入购物车，可前往“购物车与结算”完成支付。'
  } catch (error) {
    signActionError.value = error instanceof Error ? error.message : '加入购物车失败，请稍后重试。'
  } finally {
    addingToCart.value = false
  }
}

function goToCartCheckout() {
  router.push('/enterprise-cart-checkout')
}

async function syncActorCartState(actorId) {
  if (!authStore.state.token || !actorId) {
    actorInCart.value = false
    return
  }
  try {
    const payload = await fetchEnterpriseCart({ token: authStore.state.token })
    const items = Array.isArray(payload?.items) ? payload.items : []
    actorInCart.value = items.some((item) => Number(item.actor_id) === Number(actorId))
  } catch (_error) {
    actorInCart.value = false
  }
}

async function loadDetail() {
  if (!authStore.state.token) return
  loading.value = true
  errorMessage.value = ''
  signActionMessage.value = ''
  signActionError.value = ''
  actorInCart.value = false
  try {
    const agreementResult = await ensureEnterpriseAgreementSigned({
      token: authStore.state.token
    })
    if (!agreementResult.allowed) {
      detail.value = null
      return
    }
    const actorId = Number(route.params.id)
    const payload = await apiRequest(`/enterprise/discovery/actors/${actorId}`, {
      token: authStore.state.token
    })
    detail.value = payload
    await syncActorCartState(actorId)
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
