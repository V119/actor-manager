<template>
  <div class="min-h-screen bg-background text-on-surface flex items-center justify-center px-6">
    <div class="w-full max-w-md bg-surface/65 border border-sky-400/15 rounded-2xl p-8 backdrop-blur-2xl shadow-[0_0_40px_rgba(125,211,252,0.08)]">
      <div class="mb-8">
        <p class="text-xs tracking-[0.2em] uppercase text-sky-300">Glacier AI Actor</p>
        <h1 class="text-3xl font-bold mt-2">{{ pageTitle }}</h1>
        <p class="text-on-surface-variant text-sm mt-2">{{ pageSubtitle }}</p>
      </div>

      <form class="space-y-5" @submit.prevent="submit">
        <label class="block">
          <span class="text-xs text-on-surface-variant">{{ accountLabel }}</span>
          <input
            v-model="form.account"
            :type="accountInputType"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
            :placeholder="accountPlaceholder"
            required
          />
        </label>

        <label class="block">
          <span class="text-xs text-on-surface-variant">密码</span>
          <input
            v-model="form.password"
            type="password"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
            placeholder="请输入密码"
            required
          />
        </label>

        <p v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 rounded-xl bg-sky-400 text-slate-950 font-semibold hover:brightness-110 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <label
          v-if="expectedRole === 'enterprise'"
          class="flex items-center gap-2 text-sm text-on-surface-variant cursor-pointer select-none"
        >
          <input
            v-model="enterpriseAgreementAccepted"
            type="checkbox"
            class="h-4 w-4 rounded border-sky-300/35 bg-surface/40 text-sky-400 focus:ring-sky-300/60"
          />
          <span>
            我已阅读并同意
            <button
              type="button"
              class="text-sky-300 hover:text-sky-200 underline-offset-2 hover:underline"
              @click.stop="openEnterpriseAgreementModal"
            >
              《AI肖像权转授权与内容制作合作协议》
            </button>
          </span>
        </label>
      </form>

      <p v-if="expectedRole === 'individual'" class="text-sm text-on-surface-variant mt-6">
        还没有账号？
        <RouterLink to="/register" class="text-sky-300 hover:text-sky-200">立即注册</RouterLink>
      </p>
      <p v-else class="text-sm text-on-surface-variant mt-6">
        企业账号由后台管理员创建。
      </p>
      <p class="text-xs text-on-surface-variant mt-3">
        {{ switchHint }}
        <RouterLink :to="switchLoginPath" class="text-sky-300 hover:text-sky-200">{{ switchLabel }}</RouterLink>
      </p>
    </div>

    <teleport to="body">
      <div
        v-if="enterpriseAgreementModalVisible"
        class="fixed inset-0 z-[120] bg-black/45 px-4 py-6 md:px-8 md:py-10 flex items-center justify-center"
        @click.self="closeEnterpriseAgreementModal"
      >
        <div class="w-full max-w-5xl max-h-full rounded-2xl bg-white text-[#1f2329] shadow-[0_24px_80px_rgba(15,23,42,0.35)] overflow-hidden">
          <div class="h-14 px-6 border-b border-[#e6e8eb] flex items-center justify-between">
            <p class="text-base font-semibold">{{ enterpriseAgreementTitle }}</p>
            <button
              type="button"
              class="h-8 w-8 rounded-full text-[#7c8592] hover:bg-[#eef1f5] hover:text-[#3f4752] text-xl leading-none"
              @click="closeEnterpriseAgreementModal"
              aria-label="关闭协议弹窗"
            >
              ×
            </button>
          </div>

          <div class="px-6 py-6 md:px-10 md:py-8 max-h-[calc(86vh-56px)] overflow-y-auto space-y-6">
            <h2 class="text-center text-2xl font-bold">{{ enterpriseAgreementTitle }}</h2>
            <p class="text-sm leading-7 text-[#2f3742]">
              发布日期：2026年4月19日
            </p>
            <p class="text-sm leading-7 text-[#2f3742]">
              生效日期：2026年4月19日
            </p>

            <div
              v-for="section in enterpriseAgreementSections"
              :key="section.title"
              class="space-y-2"
            >
              <h3 class="text-base font-semibold">{{ section.title }}</h3>
              <p
                v-for="paragraph in section.paragraphs"
                :key="paragraph"
                class="text-sm leading-7 text-[#2f3742]"
              >
                {{ paragraph }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authStore } from '../lib/auth'

const router = useRouter()
const route = useRoute()

const form = reactive({
  account: '',
  password: ''
})

const loading = ref(false)
const errorMessage = ref('')
const enterpriseAgreementAccepted = ref(true)
const enterpriseAgreementModalVisible = ref(false)

const enterpriseAgreementTitle = 'AI肖像权转授权与内容制作合作协议'
const enterpriseAgreementSections = [
  {
    title: '第一条 合作背景',
    paragraphs: [
      '甲方基于已取得的合法授权，将演员肖像在约定范围内转授权给乙方用于内容制作与商业推广。',
      '乙方同意在合法、合规、可追溯的前提下使用相关素材和生成内容。'
    ]
  },
  {
    title: '第二条 授权范围',
    paragraphs: [
      '授权范围包括素材使用、内容制作、传播展示、推广发布及约定的商业运营场景。',
      '未经甲方同意，乙方不得将本协议项下权利再授权给第三方。'
    ]
  },
  {
    title: '第三条 合作费用',
    paragraphs: [
      '具体项目费用、结算周期与支付方式以双方实际项目约定为准。',
      '乙方应按照项目约定按时支付相关费用。'
    ]
  },
  {
    title: '第四条 合规义务',
    paragraphs: [
      '乙方不得将授权素材用于违法违规场景，不得损害演员人格权益或社会公共利益。',
      '乙方应遵守深度合成等监管要求，对AI生成内容进行必要标识。'
    ]
  },
  {
    title: '第五条 违约责任',
    paragraphs: [
      '任一方违约造成损失的，应承担相应违约责任并赔偿对方损失。',
      '乙方超范围使用素材或违规传播内容的，甲方有权终止授权并追究责任。'
    ]
  },
  {
    title: '第六条 争议解决',
    paragraphs: [
      '双方因本协议发生争议，应先协商解决；协商不成的，提交有管辖权法院处理。',
      '本协议未尽事宜，按法律法规与平台规则执行。'
    ]
  },
  {
    title: '第七条 其他',
    paragraphs: [
      '乙方在企业登录页勾选“我已阅读并同意《AI肖像权转授权与内容制作合作协议》”并登录，即视为同意本协议全部条款。',
      '本协议全文展示完毕。'
    ]
  }
]

const expectedRole = computed(() => route.meta.loginRole === 'enterprise' ? 'enterprise' : 'individual')
const pageTitle = computed(() => expectedRole.value === 'enterprise' ? '企业用户登录' : '普通演员登录')
const pageSubtitle = computed(() => (
  expectedRole.value === 'enterprise'
    ? '登录后进入企业资料与演员发布广场。企业账号由后台管理员创建。'
    : '登录后进入基本信息、素材管理和风格实验室。'
))
const switchLoginPath = computed(() => (
  expectedRole.value === 'enterprise' ? '/login/individual' : '/login/enterprise'
))
const switchHint = computed(() => (
  expectedRole.value === 'enterprise' ? '普通演员请使用：' : '企业用户请使用：'
))
const switchLabel = computed(() => (
  expectedRole.value === 'enterprise' ? '演员登录入口' : '企业登录入口'
))
const accountLabel = computed(() => (
  expectedRole.value === 'enterprise' ? '用户名' : '手机号'
))
const accountPlaceholder = computed(() => (
  expectedRole.value === 'enterprise' ? '请输入用户名' : '请输入手机号'
))
const accountInputType = computed(() => (
  expectedRole.value === 'enterprise' ? 'text' : 'tel'
))

function openEnterpriseAgreementModal() {
  enterpriseAgreementModalVisible.value = true
}

function closeEnterpriseAgreementModal() {
  enterpriseAgreementModalVisible.value = false
}

async function submit() {
  if (expectedRole.value === 'enterprise' && !enterpriseAgreementAccepted.value) {
    errorMessage.value = '请先阅读并同意《AI肖像权转授权与内容制作合作协议》。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const user = await authStore.login(form.account, form.password, enterpriseAgreementAccepted.value)
    if (user.role !== expectedRole.value) {
      await authStore.logout()
      errorMessage.value = '用户名或密码错误'
      return
    }
    const redirect = typeof route.query.redirect === 'string'
      ? route.query.redirect
      : authStore.defaultRouteForRole(user.role)
    await router.replace(redirect)
  } catch (error) {
    errorMessage.value = '用户名或密码错误'
  } finally {
    loading.value = false
  }
}
</script>
