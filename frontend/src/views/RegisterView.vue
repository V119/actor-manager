<template>
  <div class="min-h-screen bg-background text-on-surface flex items-center justify-center px-6">
    <div class="w-full max-w-lg bg-surface/65 border border-sky-400/15 rounded-2xl p-8 backdrop-blur-2xl shadow-[0_0_40px_rgba(125,211,252,0.08)]">
      <div class="mb-8">
        <p class="text-xs tracking-[0.2em] uppercase text-sky-300">Glacier AI Actor</p>
        <h1 class="text-3xl font-bold mt-2">注册账户</h1>
        <p class="text-on-surface-variant text-sm mt-2">选择普通用户或企业用户角色后进入对应工作台。</p>
      </div>

      <form class="space-y-5" @submit.prevent="submit">
        <label class="block">
          <span class="text-xs text-on-surface-variant">用户名</span>
          <input
            v-model="form.username"
            type="text"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
            placeholder="请输入用户名"
            required
          />
        </label>

        <label class="block">
          <span class="text-xs text-on-surface-variant">显示名称</span>
          <input
            v-model="form.display_name"
            type="text"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
            placeholder="例如：星界影业 / 苏长生"
          />
        </label>

        <label class="block">
          <span class="text-xs text-on-surface-variant">角色</span>
          <div class="mt-2 grid grid-cols-2 gap-3">
            <button
              type="button"
              class="rounded-xl border px-4 py-3 text-sm font-semibold transition-all"
              :class="form.role === 'individual' ? 'border-sky-300 bg-sky-400/15 text-sky-200' : 'border-sky-400/15 bg-surface/40 text-on-surface-variant'"
              @click="form.role = 'individual'"
            >
              普通用户
            </button>
            <button
              type="button"
              class="rounded-xl border px-4 py-3 text-sm font-semibold transition-all"
              :class="form.role === 'enterprise' ? 'border-sky-300 bg-sky-400/15 text-sky-200' : 'border-sky-400/15 bg-surface/40 text-on-surface-variant'"
              @click="form.role = 'enterprise'"
            >
              企业用户
            </button>
          </div>
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
        <RouterLink to="/login" class="text-sky-300 hover:text-sky-200">去登录</RouterLink>
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
  username: '',
  display_name: '',
  password: '',
  role: 'individual'
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
