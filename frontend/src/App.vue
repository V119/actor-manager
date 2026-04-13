<template>
  <router-view v-if="isAuthPage" />

  <div v-else class="flex h-screen w-full relative bg-background text-on-surface">
    <aside class="h-screen w-64 border-r border-sky-400/10 bg-slate-950/75 backdrop-blur-2xl flex flex-col flex-shrink-0 z-40 pt-16 fixed left-0">
      <div class="px-6 mb-8">
        <h1 class="text-lg font-bold text-sky-400 tracking-wider">Glacier AI Actor</h1>
        <p class="text-slate-500 text-xs mt-1">{{ roleSubtitle }}</p>
      </div>
      <nav class="flex-1 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="text-slate-400 flex items-center px-6 py-3 hover:bg-white/5 hover:text-sky-200 transition-all"
          active-class="bg-sky-400/10 text-sky-300 border-r-2 border-sky-300"
        >
          <span class="material-symbols-outlined mr-3">{{ item.icon }}</span>
          <span class="font-inter text-sm">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="p-6 border-t border-white/5">
        <button class="text-slate-400 flex items-center hover:text-rose-300 transition-colors" @click="handleLogout">
          <span class="material-symbols-outlined mr-3">logout</span>
          <span class="font-inter text-sm">退出</span>
        </button>
      </div>
    </aside>

    <main class="flex-1 ml-64 relative overflow-y-auto">
      <nav class="fixed top-0 left-64 right-0 bg-[#0a0e1a]/60 backdrop-blur-xl border-b border-sky-400/10 shadow-[0_0_30px_rgba(125,211,252,0.05)] z-50 flex justify-between items-center px-6 h-16">
        <div class="text-2xl font-semibold tracking-tighter text-sky-300">Glacier AI</div>
        <div class="flex items-center gap-4">
          <div class="text-right">
            <p class="text-sm font-semibold text-sky-200">{{ currentUser?.display_name || '未登录' }}</p>
            <p class="text-xs text-slate-400">{{ profileSubtitle }}</p>
          </div>
          <div class="w-9 h-9 rounded-full border border-sky-400/30 bg-sky-400/10 text-sky-200 flex items-center justify-center text-xs font-bold">
            {{ avatarText }}
          </div>
        </div>
      </nav>

      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authStore } from './lib/auth'

const route = useRoute()
const router = useRouter()

const currentUser = computed(() => authStore.state.user)
const isAuthPage = computed(() => (
  route.path.startsWith('/login')
  || route.path === '/register'
  || route.path.startsWith('/admin/login')
))
const roleLabel = computed(() => {
  if (currentUser.value?.role === 'admin') {
    return '系统管理员'
  }
  return currentUser.value?.role === 'enterprise' ? '企业用户' : '普通用户'
})
const roleSubtitle = computed(() => {
  if (currentUser.value?.role === 'admin') {
    return '系统管理控制台'
  }
  return currentUser.value?.role === 'enterprise' ? '企业协议工作台' : '演员用户工作台'
})
const profileSubtitle = computed(() => {
  if (currentUser.value?.role === 'enterprise') {
    return currentUser.value?.company_intro || '企业用户'
  }
  return roleLabel.value
})
const avatarText = computed(() => {
  const name = currentUser.value?.display_name || currentUser.value?.username || 'U'
  return name.slice(0, 1).toUpperCase()
})

const navItems = computed(() => {
  if (currentUser.value?.role === 'admin') {
    return [
      { to: '/admin/enterprise-users', label: '企业用户管理', icon: 'admin_panel_settings' }
    ]
  }
  if (currentUser.value?.role === 'enterprise') {
    return [
      { to: '/discovery', label: '演员发布广场', icon: 'dashboard' },
      { to: '/protocols', label: '协议管理', icon: 'description' }
    ]
  }
  return [
    { to: '/edit-portrait', label: '肖像上传', icon: 'cloud_upload' },
    { to: '/protocols', label: '协议管理', icon: 'description' },
    { to: '/style-lab', label: '风格实验室', icon: 'auto_awesome' }
  ]
})

async function handleLogout() {
  const role = currentUser.value?.role
  await authStore.logout()
  if (role === 'admin') {
    await router.replace('/admin/login')
    return
  }
  await router.replace(role === 'enterprise' ? '/login/enterprise' : '/login/individual')
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
