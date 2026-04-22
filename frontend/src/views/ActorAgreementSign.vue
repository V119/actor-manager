<template>
  <div class="min-h-screen bg-background text-on-surface">
    <main class="max-w-5xl mx-auto px-6 md:px-8 pt-24 pb-14 space-y-8">
      <header class="rounded-3xl border border-moss-400/15 bg-ink-950/55 backdrop-blur-xl p-6 md:p-8">
        <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div>
            <p class="text-xs tracking-[0.2em] uppercase text-moss-300">Agreement Sign</p>
            <h1 class="mt-2 text-3xl font-bold tracking-tight">协议签署</h1>
          </div>
          <div class="min-w-[220px] rounded-2xl border border-moss-300/20 bg-ink-900/45 p-4">
            <p class="text-xs text-on-surface-variant">当前状态</p>
            <p
              class="mt-2 text-sm font-semibold"
              :class="agreementStatus.is_signed ? 'text-sage-300' : 'text-brass-300'"
            >
              {{ agreementStatus.is_signed ? '已签署' : '未签署' }}
            </p>
          </div>
        </div>
      </header>

      <section v-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        {{ errorMessage }}
      </section>
      <section v-if="successMessage" class="rounded-2xl border border-sage-400/20 bg-sage-500/10 px-4 py-3 text-sm text-sage-200">
        {{ successMessage }}
      </section>

      <section v-if="loading" class="rounded-2xl border border-moss-400/10 bg-surface/50 p-8 text-sm text-on-surface-variant">
        正在加载协议内容...
      </section>

      <section v-else class="rounded-[28px] border border-moss-400/12 bg-[#f9f4ea] text-[#1f1a14] shadow-[0_24px_80px_rgba(15,23,42,0.28)] overflow-hidden">
        <div class="border-b border-[#d9cfbc] bg-[linear-gradient(135deg,rgba(255,249,240,0.95),rgba(245,236,220,0.92))] px-6 py-5 md:px-10">
          <p class="text-xs tracking-[0.18em] uppercase text-[#7a6544]">DOCX Rendered Template</p>
          <p class="mt-2 text-sm text-[#66563d]">
            甲方信息由管理端配置，乙方信息与签字由演员本人填写。
          </p>
        </div>

        <div class="px-6 py-8 md:px-10 md:py-10">
          <article class="mx-auto max-w-3xl space-y-4 text-[15px] leading-8">
            <h2 class="text-center text-[30px] font-bold tracking-[0.08em] text-[#1f1a14]">AI肖像权独家授权合作协议</h2>

            <div class="space-y-2 pt-4">
              <p><strong>甲方：</strong></p>
              <p>公司名称：<span class="inline-flex min-w-[220px] border-b border-[#54452f] px-2">{{ displayOrPlaceholder(agreement.template?.party_a_company_name) }}</span></p>
              <p>统一社会信用代码：<span class="inline-flex min-w-[220px] border-b border-[#54452f] px-2">{{ displayOrPlaceholder(agreement.template?.party_a_credit_code) }}</span></p>
              <p>注册地址：<span class="inline-flex min-w-[320px] border-b border-[#54452f] px-2">{{ displayOrPlaceholder(agreement.template?.party_a_registered_address) }}</span></p>
            </div>

            <div class="space-y-2 pt-2">
              <p><strong>乙方：</strong></p>
              <div class="agreement-field-block">
                <p class="agreement-inline-row">
                  <span class="agreement-inline-label">姓名：</span>
                  <span class="agreement-inline-field agreement-inline-field-sm" :class="{ 'agreement-inline-field-error': fieldErrors.party_b_name }">
                    <input v-model="form.party_b_name" :disabled="isAgreementLocked" type="text" maxlength="64" class="agreement-inline-input" :class="{ 'agreement-inline-input-locked': isAgreementLocked }" />
                  </span>
                </p>
                <p v-if="fieldErrors.party_b_name" class="agreement-field-error-text">{{ fieldErrors.party_b_name }}</p>
              </div>
              <div class="agreement-field-block">
                <p class="agreement-inline-row">
                  <span class="agreement-inline-label">性别：</span>
                  <span class="agreement-inline-field agreement-inline-field-xs" :class="{ 'agreement-inline-field-error': fieldErrors.party_b_gender }">
                    <input v-model="form.party_b_gender" :disabled="isAgreementLocked" type="text" maxlength="16" class="agreement-inline-input" :class="{ 'agreement-inline-input-locked': isAgreementLocked }" />
                  </span>
                </p>
                <p v-if="fieldErrors.party_b_gender" class="agreement-field-error-text">{{ fieldErrors.party_b_gender }}</p>
              </div>
              <div class="agreement-field-block">
                <p class="agreement-inline-row">
                  <span class="agreement-inline-label">公民身份号码：</span>
                  <span class="agreement-inline-field agreement-inline-field-lg" :class="{ 'agreement-inline-field-error': fieldErrors.party_b_identity_number }">
                    <input v-model="form.party_b_identity_number" :disabled="isAgreementLocked" type="text" maxlength="32" class="agreement-inline-input" :class="{ 'agreement-inline-input-locked': isAgreementLocked }" />
                  </span>
                </p>
                <p v-if="fieldErrors.party_b_identity_number" class="agreement-field-error-text">{{ fieldErrors.party_b_identity_number }}</p>
              </div>
              <div class="agreement-field-block">
                <p class="agreement-inline-row">
                  <span class="agreement-inline-label">联系地址：</span>
                  <span class="agreement-inline-field agreement-inline-field-lg" :class="{ 'agreement-inline-field-error': fieldErrors.party_b_contact_address }">
                    <input v-model="form.party_b_contact_address" :disabled="isAgreementLocked" type="text" maxlength="256" class="agreement-inline-input" :class="{ 'agreement-inline-input-locked': isAgreementLocked }" />
                  </span>
                </p>
                <p v-if="fieldErrors.party_b_contact_address" class="agreement-field-error-text">{{ fieldErrors.party_b_contact_address }}</p>
              </div>
              <div class="agreement-field-block">
                <p class="agreement-inline-row">
                  <span class="agreement-inline-label">联系电话：</span>
                  <span class="agreement-inline-field agreement-inline-field-md" :class="{ 'agreement-inline-field-error': fieldErrors.party_b_phone }">
                    <input v-model="form.party_b_phone" :disabled="isAgreementLocked" type="text" maxlength="32" class="agreement-inline-input" :class="{ 'agreement-inline-input-locked': isAgreementLocked }" />
                  </span>
                </p>
                <p v-if="fieldErrors.party_b_phone" class="agreement-field-error-text">{{ fieldErrors.party_b_phone }}</p>
              </div>
              <div class="agreement-field-block">
                <p class="agreement-inline-row">
                  <span class="agreement-inline-label">电子邮箱：</span>
                  <span class="agreement-inline-field agreement-inline-field-md" :class="{ 'agreement-inline-field-error': fieldErrors.party_b_email }">
                    <input v-model="form.party_b_email" :disabled="isAgreementLocked" type="email" maxlength="128" class="agreement-inline-input" :class="{ 'agreement-inline-input-locked': isAgreementLocked }" />
                  </span>
                </p>
                <p v-if="fieldErrors.party_b_email" class="agreement-field-error-text">{{ fieldErrors.party_b_email }}</p>
              </div>
            </div>

            <div class="space-y-2 pt-3 agreement-copy">
              <p><strong>第一条 合作宗旨与合作内容</strong></p>
              <p>1.1 乙方自愿将自身合法拥有的肖像权（包括面部肖像、全身肖像、照片、视频肖像素材、声音样本等）独家授权给甲方，由甲方在全球范围内通过自身平台进行乙方个人信息、肖像素材的上传、推广、宣发，对接各类剧方、广告方、直播合作方需求，促成乙方肖像权商业使用合作。</p>
              <p><strong>1.2 甲方获得乙方独家授权后，有权将乙方肖像权合法转授权给合作剧方、广告公司、直播运营方，用于本协议明确列举的AI短剧、AI长剧、商业广告、线上直播、短视频宣发等合规商业制作，</strong>乙方不得干预甲方在已获授权范围内的正常转授权及推广运营工作。</p>
              <p>1.3 乙方需配合甲方完成肖像素材提交、信息备案等基础工作，确保提供的所有素材、信息真实合法，无任何肖像权、隐私权权属争议。</p>

              <p class="pt-2"><strong>第二条 授权范围、期限及相关约定</strong></p>
              <p><strong>2.1 本协议为独家授权协议。</strong>协议有效期内，乙方不得将自身肖像权以任何形式、任何渠道授权给除甲方以外的任何第三方用于AI短剧、长剧、广告、直播等同类商业用途；乙方在线下进行的商业站台、现场演出、传统媒体采访，以及乙方参演的、未对乙方肖像进行任何形式的AI换脸、面部替换或数字分身生成的传统影视剧、综艺节目，不受本协议限制，无需甲方同意。</p>
              <p>2.2 乙方授权甲方使用乙方的肖像数据进行AI模型的训练、开发、优化及商业应用。授权内容包括但不限于：</p>
              <p>（1）采集、存储、处理乙方的肖像数据；</p>
              <p>（2）利用肖像数据训练、构建、优化AI模型；</p>
              <p>（3）利用AI模型制作、生产各类AI作品；</p>
              <p>（4）对AI作品进行发行、传播、展示、表演、放映、广播及信息网络传播；</p>
              <p>（5）对AI作品及AI模型进行商业推广、授权使用及其他商业化运营；</p>
              <p>（6）基于乙方肖像数据及AI模型开发的数字人形象用于直播、互动、代言等商业活动；</p>
              <p>（7）基于AI技术发展而产生的其他合理使用方式。</p>
              <p>（8）甲方及甲方转授权的第三方有权利用AI技术让乙方的数字分身做出乙方本人未曾做出的表情、动作、台词，将乙方的肖像替换到任何角色或场景中（法律法规禁止的除外）。</p>
              <p>
                2.3 本协议的授权期限自
                <span class="inline-flex min-w-[140px] border-b border-[#54452f] px-2">{{ formatDateText(displayAuthorizationWindow.start) }}</span>
                起至
                <span class="inline-flex min-w-[140px] border-b border-[#54452f] px-2">{{ formatDateText(displayAuthorizationWindow.end) }}</span>
                止，协议到期自动终止。
              </p>
              <p><strong>2.4 甲方有权将本合同项下的部分或全部权利转授权给第三方行使，包括但不限于授权第三方使用AI模型、AI作品进行播出、发行、代言推广等商业活动。</strong></p>
              <p><strong>2.5 甲方基于乙方肖像权开展的平台推广、转授权对接、AI模型优化、合作项目运营等产生的全部知识产权，包括但不限于平台运营权益、转授权合同权益、AI数字人形象知识产权、项目衍生作品著作权等，全部归甲方所有。</strong></p>

              <p class="pt-2"><strong>第三条 报酬标准与支付方式</strong></p>
              <p>3.1 双方确认，本协议项下每一具体商业项目的分成比例、成本扣除范围及结算方式，由双方在合作前另行签署《项目确认函》中约定。未签署《项目确认函》的项目，甲方不得使用乙方肖像。</p>
              <p>3.2 结算周期由双方在《项目确认函》中约定，可采用按项目打包结算、按天结算或其他双方认可的方式。</p>
              <p>3.3 若本协议因期满或解除而终止时，已进入正式制作周期的项目，乙方仍按该项目《项目确认函》约定的分成比例继续享有收益，直至该项目全部收入结算完毕。甲方不得以协议终止为由降低或终止乙方分成。</p>

              <p class="pt-2"><strong>第四条 双方权利与义务</strong></p>
              <p>4.1 甲方权利义务</p>
              <p>4.1.1 有权对乙方信息、肖像素材进行合规整理、推广、宣发，筛选优质合作方，合法开展转授权工作；</p>
              <p>4.1.2 严格按照协议约定按时足额支付乙方报酬，不得无故拖欠、克扣；</p>
              <p>4.1.3 不得利用AI技术制作并传播虚假新闻信息，不得利用演员肖像制作淫秽色情、赌博诈骗、暴力血腥、涉及政治敏感、严重损害乙方人格尊严及名誉权等内容；</p>
              <p>4.1.4 监督转授权第三方合规使用乙方肖像，禁止出现歪曲、丑化、玷污乙方肖像的行为，发现违规使用及时制止并追责；</p>
              <p>4.1.5 为乙方提供必要的合作对接服务，定期告知乙方肖像授权合作进展及收益情况。</p>
              <p>4.2 乙方权利义务</p>
              <p>4.2.1 按照协议约定足额获取报酬，有权查询自身肖像授权合作明细；</p>
              <p>4.2.2 严格遵守独家授权约定，协议期内不得擅自将肖像权授权给第三方同类平台或合作方；</p>
              <p>4.2.3 保证肖像素材无权属争议，若因乙方肖像权问题引发法律纠纷，全部责任由乙方承担，赔偿甲方全部损失；</p>
              <p>4.2.4 配合甲方及转授权第三方完成必要的素材补充、信息核实工作，不得无故拒绝、拖延。</p>

              <p class="pt-2"><strong>第五条 协议终止与终止后的处理</strong></p>
              <p>本协议因任何原因终止后，甲方及甲方转授权的第三方应立即停止基于乙方肖像及本协议生成的AI模型、数字人形象等成果，进行任何形式的新的商业开发、授权、销售或商业化运营，甲方及甲方转授权的第三方仅可为宣传、展示其在本协议有效期内已经完成并公开发布的AI作品之目的，在非商业性质的渠道中，以非突出的方式使用存量作品的片段或截图，且不得以该等使用行为进行任何形式的直接或间接收费，亦不得将乙方的肖像作为宣传的核心卖点。</p>

              <p class="pt-2"><strong>第六条 违约责任</strong></p>
              <p>6.1 若甲方无故拖欠乙方报酬超过 <u>10</u> 个工作日，每逾期一日，按应付未付金额的 <u>千分之五</u> 向乙方支付违约金；逾期超过 <u>30</u> 日，乙方有权单方解除协议并追索全部报酬及违约金。</p>
              <p><strong>6.2 若乙方违反独家授权约定，擅自将肖像权授权给第三方，视为根本性违约，需向甲方支付违约金人民币 <u>300000</u> 元，同时退还已收取的全部报酬，甲方有权单方解除协议，乙方需赔偿甲方全部经济损失及维权成本。</strong></p>
              <p>6.3 任何一方违反协议其他约定，需在收到对方整改通知后 <u>10</u> 个工作日内改正，逾期未改正的，需承担相应违约责任，赔偿对方全部损失，同时还应承担对方因维权而产生的合理费用，包括但不限于律师费、保全费、保全担保费、差旅费等。</p>

              <p class="pt-2"><strong>第七条 争议解决</strong></p>
              <p>7.1 协议到期未续约、双方协商一致解除、一方根本性违约导致解除的，协议终止；协议终止后，未完成的制作项目，乙方仍按约定获取到期后报酬。</p>
              <p>7.2 因本协议产生的争议，双方优先友好协商解决；协商不成的，<strong>提交甲方所在地人民法院诉讼解决。</strong></p>
              <p>7.3 本协议一式两份，甲乙双方各执一份，签字盖章后生效，具有同等法律效力。</p>
              <p>（以下无正文）</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-10 pt-6">
              <div class="space-y-4">
                <p class="agreement-inline-row agreement-signoff-row">
                  <span class="agreement-inline-label">甲方（盖章）：</span>
                  <span class="agreement-inline-field agreement-inline-field-md">
                    {{ displayOrPlaceholder(agreement.template?.party_a_signature_label || agreement.template?.party_a_company_name) }}
                  </span>
                </p>
                <p class="agreement-inline-row agreement-signoff-row">
                  <span class="agreement-inline-label">日期：</span>
                  <span class="agreement-inline-field agreement-inline-field-sm">
                    {{ formatDateText(agreement.template?.party_a_signed_date) }}
                  </span>
                </p>
              </div>

              <div class="space-y-4">
                <div>
                  <p class="agreement-inline-row agreement-signoff-row mb-2">
                    <span class="agreement-inline-label">乙方（签字）：</span>
                    <span class="agreement-inline-field agreement-inline-field-signature">
                      <span class="sr-only">乙方签字区域</span>
                    </span>
                  </p>
                  <div
                    ref="signatureCard"
                    class="agreement-signature-card rounded-md border bg-white p-2"
                    :class="[
                      signatureHint.visible ? 'agreement-signature-card-active' : 'border-[#8a7553]',
                      fieldErrors.party_b_signature_data_url ? 'agreement-signature-card-error' : '',
                      isAgreementLocked ? 'agreement-signature-card-locked' : ''
                    ]"
                  >
                    <canvas
                      ref="signatureCanvas"
                      class="agreement-signature-canvas"
                    />
                  </div>
                  <p v-if="fieldErrors.party_b_signature_data_url" class="agreement-field-error-text mt-2">
                    {{ fieldErrors.party_b_signature_data_url }}
                  </p>
                  <transition name="agreement-hint">
                    <div
                      v-if="signatureHint.visible"
                      class="mt-3 rounded-2xl border border-brass-300/60 bg-brass-100/90 px-4 py-3 text-sm text-brass-900 shadow-[0_10px_30px_rgba(120,53,15,0.12)]"
                      role="alert"
                    >
                      <p class="font-semibold">{{ signatureHint.title }}</p>
                      <p class="mt-1 leading-6">{{ signatureHint.message }}</p>
                    </div>
                  </transition>
                  <div class="mt-3 flex flex-wrap gap-3">
                    <button v-if="!isAgreementLocked" type="button" class="secondary-button" @click="clearSignature">清空签名</button>
                    <span class="text-xs text-[#7a6544]">
                      {{ isAgreementLocked ? '协议已签署，签字内容已锁定。' : '请使用手写签名完成乙方签字。' }}
                    </span>
                  </div>
                </div>
                <div class="agreement-field-block">
                  <p class="agreement-inline-row agreement-signoff-row">
                    <span class="agreement-inline-label">日期：</span>
                    <span class="agreement-inline-field agreement-inline-field-sm" :class="{ 'agreement-inline-field-error': fieldErrors.party_b_signed_date }">
                      <input v-model="form.party_b_signed_date" :disabled="isAgreementLocked" type="date" class="agreement-inline-input agreement-inline-date-input" :class="{ 'agreement-inline-input-locked': isAgreementLocked }" />
                    </span>
                  </p>
                  <p v-if="fieldErrors.party_b_signed_date" class="agreement-field-error-text">{{ fieldErrors.party_b_signed_date }}</p>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section v-if="!isAgreementLocked" class="flex justify-end">
        <button
          type="button"
          :disabled="submitting || !agreement.template?.is_ready"
          class="rounded-full bg-moss-400 px-6 py-3 text-sm font-semibold text-ink-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          @click="submitAgreement"
        >
          {{ submitting ? '签署提交中...' : '确认签署协议' }}
        </button>
      </section>
    </main>
  </div>
</template>

<script setup>
import SignaturePad from 'signature_pad'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const agreement = ref({
  template: null,
  status: {
    is_signed: false,
    message: ''
  },
  agreement: null,
  form_values: null
})
const agreementStatus = ref({
  is_signed: false,
  template_version: 1,
  message: ''
})

const form = reactive({
  party_b_name: '',
  party_b_gender: '',
  party_b_identity_number: '',
  party_b_contact_address: '',
  party_b_phone: '',
  party_b_email: '',
  party_b_signed_date: '',
  party_b_signature_data_url: ''
})
const fieldErrors = reactive({
  party_b_name: '',
  party_b_gender: '',
  party_b_identity_number: '',
  party_b_contact_address: '',
  party_b_phone: '',
  party_b_email: '',
  party_b_signature_data_url: '',
  party_b_signed_date: ''
})

const signatureCanvas = ref(null)
const signatureCard = ref(null)
let signaturePad = null
const signatureHint = reactive({
  visible: false,
  title: '',
  message: ''
})
const isAgreementLocked = computed(() => Boolean(agreementStatus.value?.is_signed))
const displayAuthorizationWindow = computed(() => resolveAuthorizationWindow(
  agreement.value?.template,
  form.party_b_signed_date,
))

function resetMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function resetFieldErrors() {
  fieldErrors.party_b_name = ''
  fieldErrors.party_b_gender = ''
  fieldErrors.party_b_identity_number = ''
  fieldErrors.party_b_contact_address = ''
  fieldErrors.party_b_phone = ''
  fieldErrors.party_b_email = ''
  fieldErrors.party_b_signature_data_url = ''
  fieldErrors.party_b_signed_date = ''
}

function hideSignatureHint() {
  signatureHint.visible = false
  signatureHint.title = ''
  signatureHint.message = ''
}

function destroySignaturePad() {
  if (!signaturePad) return
  signaturePad.off()
  signaturePad = null
}

function applyFieldErrors(errors = {}) {
  resetFieldErrors()
  fieldErrors.party_b_name = errors.party_b_name || ''
  fieldErrors.party_b_gender = errors.party_b_gender || ''
  fieldErrors.party_b_identity_number = errors.party_b_identity_number || ''
  fieldErrors.party_b_contact_address = errors.party_b_contact_address || ''
  fieldErrors.party_b_phone = errors.party_b_phone || ''
  fieldErrors.party_b_email = errors.party_b_email || ''
  fieldErrors.party_b_signature_data_url = errors.party_b_signature_data_url || ''
  fieldErrors.party_b_signed_date = errors.party_b_signed_date || ''
}

function showSignatureHint({
  title = '还差一步就可以完成签署',
  message = '请在签字区域手写签上您的姓名，系统会在您确认后完成协议签署。'
} = {}) {
  signatureHint.visible = true
  signatureHint.title = title
  signatureHint.message = message
  nextTick(() => {
    signatureCard.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

function displayOrPlaceholder(value) {
  const normalized = String(value || '').trim()
  return normalized || '待管理员配置'
}

function formatDateText(value) {
  if (!value) return '待填写'
  const [year, month, day] = String(value).split('-')
  if (!year || !month || !day) return String(value)
  return `${year}年${month}月${day}日`
}

function resolveAuthorizationWindow(template, signedDateValue) {
  const dateMode = template?.authorization_date_mode || 'fixed'
  if (dateMode !== 'relative_months') {
    return {
      start: template?.authorization_start_date || '',
      end: template?.authorization_end_date || ''
    }
  }

  const normalizedSignedDate = normalizeDateString(signedDateValue) || formatDate(new Date())
  const termMonths = Number(template?.authorization_term_months) || 0
  if (termMonths < 1) {
    return {
      start: normalizedSignedDate,
      end: ''
    }
  }

  const startDate = parseDateString(normalizedSignedDate)
  if (!startDate) {
    return {
      start: normalizedSignedDate,
      end: ''
    }
  }

  return {
    start: normalizedSignedDate,
    end: formatDate(addMonths(startDate, termMonths))
  }
}

function normalizeDateString(value) {
  if (!value) return ''
  const normalized = String(value).trim()
  return /^\d{4}-\d{2}-\d{2}$/.test(normalized) ? normalized : ''
}

function parseDateString(value) {
  const normalized = normalizeDateString(value)
  if (!normalized) return null
  const [year, month, day] = normalized.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function addMonths(baseDate, months) {
  const year = baseDate.getFullYear()
  const monthIndex = baseDate.getMonth()
  const day = baseDate.getDate()
  const totalMonthIndex = monthIndex + months
  const targetYear = year + Math.floor(totalMonthIndex / 12)
  const targetMonthIndex = totalMonthIndex % 12
  const lastDay = new Date(targetYear, targetMonthIndex + 1, 0).getDate()
  return new Date(targetYear, targetMonthIndex, Math.min(day, lastDay))
}

function formatDate(value) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function syncForm(payload) {
  const defaults = payload?.form_values || {}
  form.party_b_name = defaults.party_b_name || ''
  form.party_b_gender = defaults.party_b_gender || ''
  form.party_b_identity_number = defaults.party_b_identity_number || ''
  form.party_b_contact_address = defaults.party_b_contact_address || ''
  form.party_b_phone = defaults.party_b_phone || ''
  form.party_b_email = defaults.party_b_email || ''
  form.party_b_signed_date = defaults.party_b_signed_date || ''
  form.party_b_signature_data_url = defaults.party_b_signature_data_url || ''
}

function resizeSignatureCanvas() {
  const canvas = signatureCanvas.value
  if (!canvas || !signaturePad) return
  const ratio = Math.max(window.devicePixelRatio || 1, 1)
  const width = canvas.offsetWidth || 600
  const height = canvas.offsetHeight || 140
  canvas.width = width * ratio
  canvas.height = height * ratio
  const context = canvas.getContext('2d')
  if (context) {
    context.scale(ratio, ratio)
  }
  signaturePad.clear()
  if (form.party_b_signature_data_url) {
    signaturePad.fromDataURL(form.party_b_signature_data_url)
  }
}

function initSignaturePad() {
  const canvas = signatureCanvas.value
  if (!canvas) return
  destroySignaturePad()
  signaturePad = new SignaturePad(canvas, {
    minWidth: 0.8,
    maxWidth: 2.2,
    penColor: '#2d2217',
    backgroundColor: 'rgba(255,255,255,1)'
  })
  signaturePad.addEventListener('beginStroke', () => {
    if (isAgreementLocked.value) {
      return
    }
    hideSignatureHint()
    fieldErrors.party_b_signature_data_url = ''
  })
  resizeSignatureCanvas()
  if (isAgreementLocked.value) {
    signaturePad.off()
  }
}

function clearSignature() {
  if (isAgreementLocked.value) return
  if (signaturePad) {
    signaturePad.clear()
  }
  form.party_b_signature_data_url = ''
  fieldErrors.party_b_signature_data_url = ''
  hideSignatureHint()
}

async function loadAgreement() {
  if (!authStore.state.token) return
  destroySignaturePad()
  loading.value = true
  resetMessages()
  resetFieldErrors()
  try {
    const payload = await apiRequest('/actor/agreement', { token: authStore.state.token })
    agreement.value = payload || {
      template: null,
      status: { is_signed: false, message: '' },
      agreement: null,
      form_values: null
    }
    agreementStatus.value = payload?.status || {
      is_signed: false,
      template_version: 1,
      message: ''
    }
    syncForm(payload)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '协议内容加载失败'
  } finally {
    loading.value = false
    await nextTick()
    initSignaturePad()
  }
}

async function submitAgreement() {
  if (!authStore.state.token) return
  if (isAgreementLocked.value) return
  if (!agreement.value?.template?.is_ready) {
    errorMessage.value = '协议模板尚未配置完成，请联系管理员后再签署。'
    return
  }
  if (!signaturePad || signaturePad.isEmpty()) {
    resetMessages()
    resetFieldErrors()
    fieldErrors.party_b_signature_data_url = '请完成乙方签字。'
    showSignatureHint()
    return
  }
  submitting.value = true
  resetMessages()
  resetFieldErrors()
  hideSignatureHint()
  try {
    const signatureDataUrl = signaturePad && !signaturePad.isEmpty()
      ? signaturePad.toDataURL('image/png')
      : form.party_b_signature_data_url

    const payload = await apiRequest('/actor/agreement/sign', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        party_b_name: form.party_b_name.trim(),
        party_b_gender: form.party_b_gender.trim(),
        party_b_identity_number: form.party_b_identity_number.trim(),
        party_b_contact_address: form.party_b_contact_address.trim(),
        party_b_phone: form.party_b_phone.trim(),
        party_b_email: form.party_b_email.trim(),
        party_b_signature_data_url: signatureDataUrl || '',
        party_b_signed_date: form.party_b_signed_date || null
      }
    })
    agreement.value = payload
    agreementStatus.value = payload?.status || agreementStatus.value
    syncForm(payload)
    if (signaturePad) {
      form.party_b_signature_data_url = signaturePad.toDataURL('image/png')
      signaturePad.off()
    }
    successMessage.value = '协议已签署成功，现在可以发布演员资料和素材内容了。'
  } catch (error) {
    const detail = error && typeof error === 'object' ? error.detail : null
    const nextFieldErrors = detail && typeof detail === 'object' && detail.field_errors ? detail.field_errors : null
    if (nextFieldErrors) {
      applyFieldErrors(nextFieldErrors)
      errorMessage.value = detail.message || '请检查协议中的填写内容。'
    } else {
      const nextMessage = error instanceof Error ? error.message : '协议签署失败'
      if (nextMessage.includes('签字')) {
        fieldErrors.party_b_signature_data_url = nextMessage
        showSignatureHint({
          title: '签字还没有完成',
          message: '请先在下方签字区域手写签名，再点击“确认签署协议”。'
        })
        errorMessage.value = ''
      } else {
        errorMessage.value = nextMessage
      }
    }
    if (fieldErrors.party_b_signature_data_url) {
      showSignatureHint({
        title: '签字还没有完成',
        message: fieldErrors.party_b_signature_data_url
      })
    }
  } finally {
    submitting.value = false
  }
}

function handleResize() {
  resizeSignatureCanvas()
}

onMounted(async () => {
  await loadAgreement()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  destroySignaturePad()
  hideSignatureHint()
})
</script>

<style scoped>
.agreement-copy p {
  margin: 0;
}

.agreement-inline-row {
  margin: 0;
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 0;
}

.agreement-field-block {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.agreement-inline-label {
  flex: 0 0 auto;
  color: #1f1a14;
}

.agreement-inline-field {
  display: inline-flex;
  align-items: flex-end;
  min-height: 1.8rem;
  border-bottom: 1px solid #54452f;
  padding: 0 0.2rem 0.05rem;
  vertical-align: bottom;
}

.agreement-inline-field-xs {
  min-width: 5.5rem;
}

.agreement-inline-field-sm {
  min-width: 8rem;
}

.agreement-inline-field-md {
  min-width: 12rem;
}

.agreement-inline-field-lg {
  min-width: min(100%, 21rem);
  flex: 1 1 18rem;
}

.agreement-inline-field-signature {
  min-width: 8rem;
}

.agreement-inline-field-error {
  border-bottom-color: #b42318;
}

.agreement-inline-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: 0;
  line-height: 1.35;
  font-size: 0.95rem;
  color: #1f1a14;
  outline: none;
}

.agreement-inline-input:focus {
  outline: none;
}

.agreement-inline-date-input {
  min-height: 1.5rem;
}

.agreement-inline-input-locked {
  cursor: default;
  color: #2f4a3d;
}

.agreement-signoff-row {
  min-height: 2rem;
}

.agreement-signature-card {
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.agreement-signature-card-active {
  border-color: rgba(217, 119, 6, 0.9);
  box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.18);
}

.agreement-signature-card-error {
  border-color: #b42318;
  box-shadow: 0 0 0 3px rgba(180, 35, 24, 0.12);
}

.agreement-signature-card-locked {
  background: #f7f1e6;
}

.agreement-signature-canvas {
  display: block;
  width: 100%;
  height: 140px;
  background: #ffffff;
  cursor: crosshair;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
}

.agreement-field-error-text {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.4;
  color: #b42318;
}

.secondary-button {
  border-radius: 9999px;
  border: 1px solid rgba(72, 99, 83, 0.35);
  background: rgba(72, 99, 83, 0.12);
  padding: 0.55rem 1rem;
  font-size: 0.85rem;
  color: #2f4a3d;
  transition: background 0.2s ease;
}

.secondary-button:hover {
  background: rgba(72, 99, 83, 0.18);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.agreement-hint-enter-active,
.agreement-hint-leave-active {
  transition: all 0.2s ease;
}

.agreement-hint-enter-from,
.agreement-hint-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
