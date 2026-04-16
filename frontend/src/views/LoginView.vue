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
const expectedRole = computed(() => route.meta.loginRole === 'enterprise' ? 'enterprise' : 'individual')
const pageTitle = computed(() => expectedRole.value === 'enterprise' ? '企业用户登录' : '普通演员登录')
const pageSubtitle = computed(() => (
  expectedRole.value === 'enterprise'
    ? '登录后进入企业协议签署与演员发布广场。企业账号由后台管理员创建。'
    : '登录后进入基本信息、协议签署、素材管理和风格实验室。'
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

async function submit() {
  loading.value = true
  errorMessage.value = ''
  try {
    const user = await authStore.login(form.account, form.password)
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
