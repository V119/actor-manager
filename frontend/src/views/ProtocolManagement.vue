<template>
  <div class="max-w-6xl mx-auto px-8 py-24 space-y-8 min-h-screen bg-background text-on-surface">
    <section class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">协议管理</h1>
        <p class="text-sm text-on-surface-variant mt-2">
          <span v-if="isEnterprise">企业用户可创建协议并指定签署对象。</span>
          <span v-else>普通用户可查看并签署企业发来的协议。</span>
        </p>
      </div>
      <div class="text-xs text-on-surface-variant">
        当前角色：<span class="text-sky-300 font-semibold">{{ roleLabel }}</span>
      </div>
    </section>

    <section v-if="isEnterprise" class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 rounded-xl p-6">
      <h2 class="text-lg font-semibold mb-4">发起新协议</h2>
      <form class="space-y-4" @submit.prevent="createProtocol">
        <label class="block">
          <span class="text-xs text-on-surface-variant">签署用户</span>
          <select
            v-model="createForm.target_user_id"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
            required
          >
            <option disabled value="">请选择普通用户</option>
            <option v-for="user in individualUsers" :key="user.id" :value="user.id">
              {{ user.display_name }}（{{ user.username }}）
            </option>
          </select>
        </label>

        <label class="block">
          <span class="text-xs text-on-surface-variant">协议标题</span>
          <input
            v-model="createForm.title"
            type="text"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
            placeholder="例如：3年肖像授权协议（全球范围）"
            required
          />
        </label>

        <label class="block">
          <span class="text-xs text-on-surface-variant">协议内容</span>
          <textarea
            v-model="createForm.content"
            rows="6"
            class="mt-2 w-full bg-surface/40 border border-sky-400/15 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-sky-300/50"
            placeholder="请输入完整协议内容..."
            required
          />
        </label>

        <button
          type="submit"
          :disabled="loading"
          class="px-6 py-3 rounded-lg bg-sky-400 text-slate-950 text-sm font-semibold hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {{ loading ? '提交中...' : '创建并发送协议' }}
        </button>
      </form>
    </section>

    <section v-else class="flex p-1.5 bg-surface/60 backdrop-blur-xl border border-sky-400/10 rounded-xl w-fit">
      <button
        class="px-6 py-2 rounded-lg text-sm font-semibold transition-all"
        :class="activeFilter === 'pending' ? 'bg-sky-400/10 text-sky-300 border border-sky-400/20' : 'text-on-surface-variant hover:text-on-surface'"
        @click="activeFilter = 'pending'"
      >
        待签署
      </button>
      <button
        class="px-6 py-2 rounded-lg text-sm font-semibold transition-all"
        :class="activeFilter === 'signed' ? 'bg-sky-400/10 text-sky-300 border border-sky-400/20' : 'text-on-surface-variant hover:text-on-surface'"
        @click="activeFilter = 'signed'"
      >
        已签署
      </button>
      <button
        class="px-6 py-2 rounded-lg text-sm font-semibold transition-all"
        :class="activeFilter === 'all' ? 'bg-sky-400/10 text-sky-300 border border-sky-400/20' : 'text-on-surface-variant hover:text-on-surface'"
        @click="activeFilter = 'all'"
      >
        全部
      </button>
    </section>

    <p v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</p>
    <p v-if="successMessage" class="text-sm text-emerald-300">{{ successMessage }}</p>

    <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <article
        v-for="protocol in visibleProtocols"
        :key="protocol.id"
        class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 p-6 rounded-xl group hover:border-sky-400/30 transition-all duration-300"
      >
        <div class="flex items-start justify-between mb-5">
          <div>
            <h3 class="font-semibold text-on-surface">{{ protocol.title }}</h3>
            <p class="text-xs text-on-surface-variant mt-1">
              发起方：{{ protocol.company_name }}
            </p>
            <p v-if="isEnterprise" class="text-xs text-on-surface-variant mt-1">
              签署人：{{ protocol.target_user_display_name || '-' }}（{{ protocol.target_username || '-' }}）
            </p>
          </div>
          <span
            class="px-3 py-1 rounded-full text-[10px] font-bold tracking-wider border"
            :class="protocol.status === 'signed'
              ? 'bg-emerald-400/10 text-emerald-300 border-emerald-300/30'
              : 'bg-amber-400/10 text-amber-300 border-amber-300/30'"
          >
            {{ protocol.status === 'signed' ? '已签署' : '待签署' }}
          </span>
        </div>

        <p class="text-sm text-on-surface/80 leading-relaxed line-clamp-3">{{ protocol.content }}</p>
        <p class="text-xs text-on-surface-variant mt-4">创建时间：{{ formatDate(protocol.created_at) }}</p>

        <div class="mt-5 flex gap-3">
          <button
            class="px-4 py-2 rounded-lg text-sm font-medium border border-sky-400/20 text-sky-300 hover:bg-sky-400/10 transition-all"
            @click="selectedProtocol = protocol"
          >
            查看详情
          </button>
          <button
            v-if="!isEnterprise && protocol.status !== 'signed'"
            class="px-4 py-2 rounded-lg text-sm font-semibold bg-sky-400 text-slate-950 hover:brightness-110 transition-all"
            :disabled="loading"
            @click="signProtocol(protocol.id)"
          >
            签署
          </button>
        </div>
      </article>
    </section>

    <section v-if="!visibleProtocols.length" class="rounded-xl border border-sky-400/10 bg-surface/40 p-10 text-center text-on-surface-variant">
      暂无协议记录
    </section>

    <div v-if="selectedProtocol" class="fixed inset-0 z-50 flex justify-end">
      <div class="absolute inset-0 bg-background/60 backdrop-blur-sm" @click="selectedProtocol = null" />
      <div class="relative w-full md:w-[640px] bg-surface/75 backdrop-blur-2xl border-l border-sky-400/20 shadow-2xl flex flex-col">
        <button
          class="absolute top-5 left-[-50px] w-10 h-10 rounded-full bg-surface/60 border border-sky-400/10 flex items-center justify-center text-on-surface hover:text-primary transition-colors"
          @click="selectedProtocol = null"
        >
          <span class="material-symbols-outlined">close</span>
        </button>
        <div class="p-8 border-b border-white/5 space-y-2">
          <h2 class="text-xl font-bold">{{ selectedProtocol.title }}</h2>
          <p class="text-xs text-on-surface-variant">发起方：{{ selectedProtocol.company_name }}</p>
        </div>
        <div class="p-8 overflow-y-auto text-sm leading-relaxed text-on-surface/85 whitespace-pre-wrap">
          {{ selectedProtocol.content }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const selectedProtocol = ref(null)
const protocols = ref([])
const individualUsers = ref([])
const activeFilter = ref('pending')

const createForm = reactive({
  target_user_id: '',
  title: '',
  content: ''
})

const user = computed(() => authStore.state.user)
const isEnterprise = computed(() => user.value?.role === 'enterprise')
const roleLabel = computed(() => (isEnterprise.value ? '企业用户' : '普通用户'))

const visibleProtocols = computed(() => {
  if (isEnterprise.value) {
    return protocols.value
  }
  if (activeFilter.value === 'all') {
    return protocols.value
  }
  return protocols.value.filter((item) => item.status === activeFilter.value)
})

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

async function loadProtocols() {
  if (!authStore.state.token) return
  const endpoint = isEnterprise.value ? '/enterprise/protocols' : '/user/protocols'
  protocols.value = await apiRequest(endpoint, { token: authStore.state.token })
}

async function loadIndividualUsers() {
  if (!isEnterprise.value || !authStore.state.token) return
  individualUsers.value = await apiRequest('/enterprise/users', { token: authStore.state.token })
}

async function createProtocol() {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await apiRequest('/enterprise/protocols', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        target_user_id: Number(createForm.target_user_id),
        title: createForm.title,
        content: createForm.content
      }
    })
    successMessage.value = '协议已成功创建并发送。'
    createForm.target_user_id = ''
    createForm.title = ''
    createForm.content = ''
    await loadProtocols()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建协议失败'
  } finally {
    loading.value = false
  }
}

async function signProtocol(protocolId) {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await apiRequest(`/user/protocols/${protocolId}/sign`, {
      method: 'POST',
      token: authStore.state.token
    })
    successMessage.value = '协议签署成功。'
    await loadProtocols()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '签署失败'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    await loadProtocols()
    await loadIndividualUsers()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '协议数据加载失败'
  } finally {
    loading.value = false
  }
})
</script>
