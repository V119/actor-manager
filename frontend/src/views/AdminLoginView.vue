<template>
  <div class="min-h-screen bg-background text-on-surface flex items-center justify-center px-6">
    <div class="w-full max-w-md bg-surface/65 border border-amber-400/20 rounded-2xl p-8 backdrop-blur-2xl shadow-[0_0_40px_rgba(251,191,36,0.12)]">
      <div class="mb-8">
        <p class="text-xs tracking-[0.2em] uppercase text-amber-300">Glacier AI Admin</p>
        <h1 class="text-3xl font-bold mt-2">后台管理登录</h1>
        <p class="text-on-surface-variant text-sm mt-2">登录后可管理企业用户账号、企业名称与企业简介。</p>
      </div>

      <form class="space-y-5" @submit.prevent="submit">
        <label class="block">
          <span class="text-xs text-on-surface-variant">管理员用户名</span>
          <input
            v-model="form.username"
            type="text"
            class="mt-2 w-full bg-surface/40 border border-amber-400/20 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60 focus:border-amber-300/40"
            placeholder="请输入管理员用户名"
            required
          />
        </label>

        <label class="block">
          <span class="text-xs text-on-surface-variant">管理员密码</span>
          <input
            v-model="form.password"
            type="password"
            class="mt-2 w-full bg-surface/40 border border-amber-400/20 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60 focus:border-amber-300/40"
            placeholder="请输入管理员密码"
            required
          />
        </label>

        <p v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 rounded-xl bg-amber-300 text-slate-900 font-semibold hover:brightness-110 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {{ loading ? '登录中...' : '登录管理端' }}
        </button>
      </form>

      <p class="text-xs text-on-surface-variant mt-6">默认管理员账号可在后端配置中修改。</p>
      <p class="text-xs text-on-surface-variant mt-2">
        业务登录入口：
        <RouterLink to="/login/individual" class="text-sky-300 hover:text-sky-200">演员登录</RouterLink>
        /
        <RouterLink to="/login/enterprise" class="text-sky-300 hover:text-sky-200">企业登录</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authStore } from '../lib/auth'

const router = useRouter()
const route = useRoute()

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  loading.value = true
  errorMessage.value = ''
  try {
    const loginFn = typeof authStore.adminLogin === 'function'
      ? authStore.adminLogin.bind(authStore)
      : authStore.login.bind(authStore)
    const user = await loginFn(form.username, form.password)
    if (user.role !== 'admin') {
      await authStore.logout()
      errorMessage.value = '该账号不是管理员账号。'
      return
    }
    const redirect = typeof route.query.redirect === 'string'
      ? route.query.redirect
      : authStore.defaultRouteForRole(user.role)
    await router.replace(redirect)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>
