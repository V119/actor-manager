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

        <label class="flex items-center gap-2 text-sm text-on-surface-variant cursor-pointer select-none">
          <input
            v-model="form.agreement_accepted"
            type="checkbox"
            class="h-4 w-4 rounded border-sky-300/35 bg-surface/40 text-sky-400 focus:ring-sky-300/60"
          />
          <span>
            我已阅读并同意
            <button
              type="button"
              class="text-sky-300 hover:text-sky-200 underline-offset-2 hover:underline"
              @click.stop="openAgreementModal"
            >
              《AI肖像权独家授权合作协议》
            </button>
          </span>
        </label>
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

    <teleport to="body">
      <div
        v-if="agreementModalVisible"
        class="fixed inset-0 z-[120] bg-black/45 px-4 py-6 md:px-8 md:py-10 flex items-center justify-center"
        @click.self="closeAgreementModal"
      >
        <div class="w-full max-w-5xl max-h-full rounded-2xl bg-white text-[#1f2329] shadow-[0_24px_80px_rgba(15,23,42,0.35)] overflow-hidden">
          <div class="h-14 px-6 border-b border-[#e6e8eb] flex items-center justify-between">
            <p class="text-base font-semibold">{{ agreementTitle }}</p>
            <button
              type="button"
              class="h-8 w-8 rounded-full text-[#7c8592] hover:bg-[#eef1f5] hover:text-[#3f4752] text-xl leading-none"
              @click="closeAgreementModal"
              aria-label="关闭协议弹窗"
            >
              ×
            </button>
          </div>

          <div class="px-6 py-6 md:px-10 md:py-8 max-h-[calc(86vh-56px)] overflow-y-auto space-y-6">
            <h2 class="text-center text-2xl font-bold">{{ agreementTitle }}</h2>
            <p class="text-sm leading-7 text-[#2f3742]">
              发布日期：2026年4月19日
            </p>
            <p class="text-sm leading-7 text-[#2f3742]">
              生效日期：2026年4月19日
            </p>

            <div
              v-for="section in agreementSections"
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
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../lib/auth'

const router = useRouter()

const form = reactive({
  phone: '',
  password: '',
  confirm_password: '',
  agreement_accepted: false
})

const loading = ref(false)
const errorMessage = ref('')
const agreementModalVisible = ref(false)

const agreementTitle = 'AI肖像权独家授权合作协议'
const agreementSections = [
  {
    title: '第一条 合作内容',
    paragraphs: [
      '乙方确认将本人肖像、影像、声音及相关素材授权给甲方用于平台展示、内容制作、模型训练、项目推广及商业合作。',
      '甲方可在合法合规的范围内使用并处理乙方提交的素材，用于平台运营和合作业务拓展。'
    ]
  },
  {
    title: '第二条 授权范围与期限',
    paragraphs: [
      '授权范围包括素材采集、存储、加工、生成、展示、传播及授权合作方按约使用。',
      '授权期限以甲方平台当前公示规则为准，双方可按规则续展、变更或终止。'
    ]
  },
  {
    title: '第三条 收益与结算',
    paragraphs: [
      '乙方收益分配、结算周期及结算方式以双方就具体项目达成的约定为准。',
      '甲方应按约向乙方结算收益，乙方应配合完成结算所需的信息确认。'
    ]
  },
  {
    title: '第四条 双方权利义务',
    paragraphs: [
      '乙方保证提交素材真实、合法、完整，且不存在侵权、冒名、盗用等情形。',
      '甲方应采取合理措施保护乙方数据与素材安全，不得用于法律法规禁止的用途。'
    ]
  },
  {
    title: '第五条 违约与责任',
    paragraphs: [
      '任一方违反本协议约定给对方造成损失的，应依法承担相应违约责任并赔偿损失。',
      '如因乙方素材权属问题引发争议，由乙方承担相应法律责任。'
    ]
  },
  {
    title: '第六条 争议解决',
    paragraphs: [
      '双方因本协议产生争议的，应先友好协商；协商不成的，提交有管辖权的人民法院处理。',
      '本协议未尽事宜，按国家相关法律法规及平台公示规则执行。'
    ]
  },
  {
    title: '第七条 其他',
    paragraphs: [
      '乙方勾选“我已阅读并同意《AI肖像权独家授权合作协议》”并完成注册，即视为已阅读、理解并同意本协议全部条款。',
      '本协议全文展示完毕。'
    ]
  }
]

function openAgreementModal() {
  agreementModalVisible.value = true
}

function closeAgreementModal() {
  agreementModalVisible.value = false
}

async function submit() {
  if (!form.agreement_accepted) {
    errorMessage.value = '请先阅读并同意《AI肖像权独家授权合作协议》。'
    return
  }

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
