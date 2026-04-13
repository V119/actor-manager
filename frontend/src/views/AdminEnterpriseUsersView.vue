<template>
  <div class="min-h-screen pt-24 px-6 pb-10 lg:px-10">
    <section class="max-w-7xl mx-auto space-y-6">
      <div class="rounded-2xl border border-amber-400/20 bg-slate-950/60 backdrop-blur-xl p-6">
        <p class="text-xs tracking-[0.2em] uppercase text-amber-300">Admin Console</p>
        <h1 class="text-2xl font-bold text-amber-100 mt-2">企业用户管理</h1>
        <p class="text-sm text-slate-300 mt-2">维护企业用户登录账号、企业名称和企业简介。企业用户登录后看到的企业信息与这里保持一致。</p>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-[minmax(300px,360px)_1fr] gap-6">
        <section class="rounded-2xl border border-amber-400/15 bg-surface/60 backdrop-blur-xl p-6">
          <h2 class="text-lg font-semibold text-amber-100">新增企业用户</h2>
          <form class="space-y-4 mt-4" @submit.prevent="createEnterpriseUser">
            <label class="block">
              <span class="text-xs text-on-surface-variant">登录名</span>
              <input
                v-model="createForm.username"
                type="text"
                required
                class="mt-2 w-full bg-surface/40 border border-amber-400/20 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60 focus:border-amber-300/40"
                placeholder="例如：acme_enterprise"
              />
            </label>

            <label class="block">
              <span class="text-xs text-on-surface-variant">登录密码</span>
              <input
                v-model="createForm.password"
                type="password"
                required
                minlength="6"
                class="mt-2 w-full bg-surface/40 border border-amber-400/20 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60 focus:border-amber-300/40"
                placeholder="至少 6 位"
              />
            </label>

            <label class="block">
              <span class="text-xs text-on-surface-variant">企业名称</span>
              <input
                v-model="createForm.company_name"
                type="text"
                required
                class="mt-2 w-full bg-surface/40 border border-amber-400/20 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60 focus:border-amber-300/40"
                placeholder="例如：星界影业"
              />
            </label>

            <label class="block">
              <span class="text-xs text-on-surface-variant">企业简介</span>
              <textarea
                v-model="createForm.company_intro"
                rows="4"
                class="mt-2 w-full bg-surface/40 border border-amber-400/20 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-amber-300/60 focus:border-amber-300/40"
                placeholder="用于企业端登录后的信息展示"
              />
            </label>

            <button
              type="submit"
              :disabled="creating"
              class="w-full py-3 rounded-xl bg-amber-300 text-slate-900 font-semibold hover:brightness-110 transition-all disabled:opacity-60"
            >
              {{ creating ? '创建中...' : '创建企业用户' }}
            </button>
          </form>
        </section>

        <section class="rounded-2xl border border-sky-400/15 bg-surface/60 backdrop-blur-xl p-6">
          <div class="flex items-center justify-between gap-4">
            <h2 class="text-lg font-semibold text-sky-100">企业用户列表</h2>
            <button
              class="px-3 py-2 rounded-lg border border-sky-400/20 text-sky-200 text-sm hover:bg-sky-400/10 transition-colors"
              type="button"
              @click="loadEnterpriseUsers"
            >
              刷新列表
            </button>
          </div>

          <p v-if="errorMessage" class="text-sm text-rose-300 mt-4">{{ errorMessage }}</p>
          <p v-if="successMessage" class="text-sm text-emerald-300 mt-4">{{ successMessage }}</p>

          <div v-if="loading" class="text-sm text-on-surface-variant mt-5">加载中...</div>
          <div v-else-if="enterpriseUsers.length === 0" class="text-sm text-on-surface-variant mt-5">暂无企业用户，请先创建。</div>

          <div v-else class="mt-5 space-y-4">
            <article
              v-for="user in enterpriseUsers"
              :key="user.id"
              class="rounded-xl border border-sky-400/10 bg-slate-950/45 p-4"
            >
              <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
                <h3 class="text-sm font-semibold text-sky-100">企业用户 #{{ user.id }}</h3>
                <p class="text-xs text-slate-400">创建于 {{ formatDate(user.created_at) }}</p>
              </div>

              <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
                <label class="block">
                  <span class="text-xs text-on-surface-variant">登录名</span>
                  <input
                    v-model="editForms[user.id].username"
                    type="text"
                    required
                    class="mt-1.5 w-full bg-surface/40 border border-sky-400/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
                  />
                </label>

                <label class="block">
                  <span class="text-xs text-on-surface-variant">重置密码（可选）</span>
                  <input
                    v-model="editForms[user.id].password"
                    type="password"
                    minlength="6"
                    class="mt-1.5 w-full bg-surface/40 border border-sky-400/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
                    placeholder="留空则不修改"
                  />
                </label>

                <label class="block lg:col-span-2">
                  <span class="text-xs text-on-surface-variant">企业名称</span>
                  <input
                    v-model="editForms[user.id].company_name"
                    type="text"
                    required
                    class="mt-1.5 w-full bg-surface/40 border border-sky-400/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
                  />
                </label>

                <label class="block lg:col-span-2">
                  <span class="text-xs text-on-surface-variant">企业简介</span>
                  <textarea
                    v-model="editForms[user.id].company_intro"
                    rows="3"
                    class="mt-1.5 w-full bg-surface/40 border border-sky-400/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/60 focus:border-sky-300/40"
                  />
                </label>
              </div>

              <div class="mt-3 flex justify-end">
                <button
                  type="button"
                  :disabled="savingId === user.id"
                  class="px-4 py-2 rounded-lg bg-sky-400 text-slate-900 text-sm font-semibold hover:brightness-110 transition-all disabled:opacity-60"
                  @click="updateEnterpriseUser(user.id)"
                >
                  {{ savingId === user.id ? '保存中...' : '保存修改' }}
                </button>
              </div>
            </article>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const loading = ref(false)
const creating = ref(false)
const savingId = ref(0)
const errorMessage = ref('')
const successMessage = ref('')
const enterpriseUsers = ref([])

const createForm = reactive({
  username: '',
  password: '',
  company_name: '',
  company_intro: ''
})

const editForms = reactive({})

function resetMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function syncEditForms() {
  enterpriseUsers.value.forEach((item) => {
    editForms[item.id] = {
      username: item.username,
      password: '',
      company_name: item.company_name,
      company_intro: item.company_intro || ''
    }
  })
}

async function loadEnterpriseUsers() {
  if (!authStore.state.token) return
  loading.value = true
  resetMessages()
  try {
    const payload = await apiRequest('/admin/enterprise-users', { token: authStore.state.token })
    enterpriseUsers.value = Array.isArray(payload) ? payload : []
    syncEditForms()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载企业用户失败'
  } finally {
    loading.value = false
  }
}

async function createEnterpriseUser() {
  if (!authStore.state.token) return
  creating.value = true
  resetMessages()
  try {
    await apiRequest('/admin/enterprise-users', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        username: createForm.username.trim(),
        password: createForm.password,
        company_name: createForm.company_name.trim(),
        company_intro: createForm.company_intro.trim()
      }
    })
    createForm.username = ''
    createForm.password = ''
    createForm.company_name = ''
    createForm.company_intro = ''
    successMessage.value = '企业用户创建成功'
    await loadEnterpriseUsers()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建企业用户失败'
  } finally {
    creating.value = false
  }
}

async function updateEnterpriseUser(userId) {
  if (!authStore.state.token) return
  const form = editForms[userId]
  if (!form) return

  savingId.value = userId
  resetMessages()
  try {
    await apiRequest(`/admin/enterprise-users/${userId}`, {
      method: 'PUT',
      token: authStore.state.token,
      body: {
        username: form.username.trim(),
        password: form.password ? form.password : null,
        company_name: form.company_name.trim(),
        company_intro: form.company_intro.trim()
      }
    })
    form.password = ''
    successMessage.value = '企业用户信息已更新'
    await loadEnterpriseUsers()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新企业用户失败'
  } finally {
    savingId.value = 0
  }
}

onMounted(async () => {
  await loadEnterpriseUsers()
})
</script>
