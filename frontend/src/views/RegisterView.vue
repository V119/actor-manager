<template>
  <div class="min-h-screen bg-background text-on-surface flex items-center justify-center px-6">
    <div class="w-full max-w-lg bg-surface/65 border border-sky-400/15 rounded-2xl p-8 backdrop-blur-2xl shadow-[0_0_40px_rgba(125,211,252,0.08)]">
      <div class="mb-8">
        <p class="text-xs tracking-[0.2em] uppercase text-sky-300">Glacier AI Actor</p>
        <h1 class="text-3xl font-bold mt-2">注册账户</h1>
        <p class="text-on-surface-variant text-sm mt-2">当前仅开放普通演员用户注册，企业用户由后台管理员创建。</p>
      </div>

      <form class="space-y-5" @submit.prevent="submit">
        <label class="block">
          <span class="text-xs text-on-surface-variant">手机号</span>
          <input
            v-model="form.phone"
            type="tel"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
            placeholder="请输入手机号"
            required
          />
        </label>

        <label class="block">
          <span class="text-xs text-on-surface-variant">密码</span>
          <input
            v-model="form.password"
            type="password"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
            placeholder="至少 6 位"
            required
          />
        </label>

        <label class="block">
          <span class="text-xs text-on-surface-variant">确认密码</span>
          <input
            v-model="form.confirm_password"
            type="password"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
            placeholder="请再次输入密码"
            required
          />
        </label>

        <p v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 rounded-xl bg-sky-400 text-slate-950 font-semibold hover:brightness-110 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {{ loading ? '注册中...' : '注册并进入工作台' }}
        </button>
      </form>

      <p class="text-sm text-on-surface-variant mt-6">
        已有账号？
        <RouterLink to="/login/individual" class="text-sky-300 hover:text-sky-200">去登录</RouterLink>
      </p>
      <p class="text-xs text-on-surface-variant mt-3">
        企业用户请使用
        <RouterLink to="/login/enterprise" class="text-sky-300 hover:text-sky-200">企业登录入口</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../lib/auth'

const router = useRouter()

const form = reactive({
  phone: '',
  password: '',
  confirm_password: ''
})

const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  loading.value = true
  errorMessage.value = ''
  try {
    const user = await authStore.register(form)
    await router.replace(authStore.defaultRouteForRole(user.role))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>
