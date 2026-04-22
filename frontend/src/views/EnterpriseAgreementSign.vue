<template>
  <div class="min-h-screen bg-background text-on-surface">
    <main class="max-w-5xl mx-auto px-6 md:px-8 pt-24 pb-14 space-y-8">
      <header class="rounded-3xl border border-moss-400/15 bg-ink-950/55 backdrop-blur-xl p-6 md:p-8">
        <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div>
            <p class="text-xs tracking-[0.2em] uppercase text-moss-300">Enterprise Agreement</p>
            <h1 class="mt-2 text-3xl font-bold tracking-tight">企业协议签署</h1>
          </div>
          <div class="min-w-[220px] rounded-2xl border border-moss-300/20 bg-ink-900/45 p-4">
            <p class="text-xs text-on-surface-variant">当前状态</p>
            <p
              class="mt-2 text-sm font-semibold"
              :class="agreementStatus.is_signed ? 'text-sage-300' : 'text-brass-300'"
            >
              {{ agreementStatus.is_signed ? '已签署' : '未签署' }}
            </p>
            <p class="mt-2 text-xs text-on-surface-variant leading-relaxed">{{ agreementStatus.message || '请完成企业协议签署。' }}</p>
          </div>
        </div>
      </header>

      <section v-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        {{ errorMessage }}
      </section>
      <section v-if="entryNoticeMessage" class="rounded-2xl border border-brass-400/30 bg-brass-500/10 px-4 py-3 text-sm text-brass-100">
        {{ entryNoticeMessage }}
      </section>
      <section v-if="successMessage" class="rounded-2xl border border-sage-400/20 bg-sage-500/10 px-4 py-3 text-sm text-sage-200">
        {{ successMessage }}
      </section>

      <section v-if="loading" class="rounded-2xl border border-moss-400/10 bg-surface/50 p-8 text-sm text-on-surface-variant">
        正在加载协议内容...
      </section>

      <template v-else>
        <section
          v-if="!isAgreementLocked && !isEnterpriseBasicInfoReady"
          class="rounded-2xl border border-brass-400/30 bg-brass-500/10 px-5 py-4"
        >
          <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <p class="text-sm leading-6 text-brass-100">
              请先前往“企业基本信息”页面补全企业名称、统一社会信用代码和注册地址，再继续完成协议签署。
            </p>
            <button type="button" class="secondary-button secondary-button-dark" @click="goToEnterpriseBasicInfo">
              前往企业基本信息
            </button>
          </div>
        </section>

        <section class="rounded-[28px] border border-moss-400/12 bg-[#f9f4ea] text-[#1f1a14] shadow-[0_24px_80px_rgba(15,23,42,0.28)] overflow-hidden">
          <div class="border-b border-[#d9cfbc] bg-[linear-gradient(135deg,rgba(255,249,240,0.95),rgba(245,236,220,0.92))] px-6 py-5 md:px-10">
            <p class="text-xs tracking-[0.18em] uppercase text-[#7a6544]">DOCX Rendered Template</p>
            <p class="mt-2 text-sm text-[#66563d]">
              甲方信息由平台管理端配置，乙方企业信息与签字由企业用户填写。
            </p>
          </div>

          <div class="px-6 py-8 md:px-10 md:py-10">
            <article class="mx-auto max-w-3xl space-y-4 text-[15px] leading-8">
              <h2 class="text-center text-[28px] font-bold tracking-[0.08em] text-[#1f1a14]">AI肖像权转授权与内容制作合作协议</h2>

              <div class="space-y-2 pt-4">
                <p><strong>甲方：</strong></p>
                <p>公司名称：<span class="inline-flex min-w-[220px] border-b border-[#54452f] px-2">{{ displayOrPlaceholder(agreement.template?.party_a_company_name) }}</span></p>
                <p>统一社会信用代码：<span class="inline-flex min-w-[220px] border-b border-[#54452f] px-2">{{ displayOrPlaceholder(agreement.template?.party_a_credit_code) }}</span></p>
                <p>住所地：<span class="inline-flex min-w-[320px] border-b border-[#54452f] px-2">{{ displayOrPlaceholder(agreement.template?.party_a_registered_address) }}</span></p>
              </div>

              <div class="space-y-2 pt-2">
                <p><strong>乙方：</strong></p>
                <div class="agreement-field-block">
                  <p class="agreement-inline-row">
                    <span class="agreement-inline-label">公司名称：</span>
                    <span
                      class="agreement-inline-field agreement-inline-field-lg agreement-inline-display"
                      :class="{
                        'agreement-inline-field-error': fieldErrors.party_b_company_name,
                        'agreement-inline-placeholder': !hasFilledText(form.party_b_company_name)
                      }"
                    >
                      {{ displayAgreementField(form.party_b_company_name, '请前往企业基本信息页填写企业名称') }}
                    </span>
                  </p>
                  <p v-if="fieldErrors.party_b_company_name" class="agreement-field-error-text">{{ fieldErrors.party_b_company_name }}</p>
                </div>
                <div class="agreement-field-block">
                  <p class="agreement-inline-row">
                    <span class="agreement-inline-label">统一社会信用代码：</span>
                    <span
                      class="agreement-inline-field agreement-inline-field-lg agreement-inline-display"
                      :class="{
                        'agreement-inline-field-error': fieldErrors.party_b_credit_code,
                        'agreement-inline-placeholder': !hasFilledText(form.party_b_credit_code)
                      }"
                    >
                      {{ displayAgreementField(form.party_b_credit_code, '请前往企业基本信息页填写统一社会信用代码') }}
                    </span>
                  </p>
                  <p v-if="fieldErrors.party_b_credit_code" class="agreement-field-error-text">{{ fieldErrors.party_b_credit_code }}</p>
                </div>
                <div class="agreement-field-block">
                  <p class="agreement-inline-row">
                    <span class="agreement-inline-label">住所地：</span>
                    <span
                      class="agreement-inline-field agreement-inline-field-lg agreement-inline-display agreement-inline-display-multiline"
                      :class="{
                        'agreement-inline-field-error': fieldErrors.party_b_registered_address,
                        'agreement-inline-placeholder': !hasFilledText(form.party_b_registered_address)
                      }"
                    >
                      {{ displayAgreementField(form.party_b_registered_address, '请前往企业基本信息页填写企业注册地址') }}
                    </span>
                  </p>
                  <p v-if="fieldErrors.party_b_registered_address" class="agreement-field-error-text">{{ fieldErrors.party_b_registered_address }}</p>
                </div>
              </div>

              <div class="space-y-2 pt-3 agreement-copy">
              <p><strong>第一条 合作背景与转授权依据</strong></p>
              <p>1.1 甲方已与对应演员（肖像权人）签订合法有效的《AI肖像权独家授权合作协议》，依法获得演员肖像权独家授权及转授权权利，有权将演员肖像权转授权给乙方用于合规商业制作。</p>
              <p>1.2 乙方因自身业务需要，需使用演员肖像权制作AI短剧、AI长剧、商业广告、直播相关内容，自愿通过甲方平台下单选定演员，接受甲方转授权，严格按照协议约定使用肖像并支付费用。</p>
              <p>1.3 乙方确认，已充分知晓甲方与演员之间的授权约定，承诺遵守本协议及原授权协议相关规定，不得超出约定范围使用肖像。</p>
              <p>1.4 本协议为甲方平台的框架性使用协议。具体项目的费用标准、结算方式等，以双方具体签订的《项目订单》执行。</p>

              <p class="pt-2"><strong>第二条 授权范围、期限及相关约定</strong></p>
              <p>2.1甲方依据其与演员签订的《AI肖像权独家授权合作协议》，将以下权利转授权给乙方：</p>
              <p>（1）利用AI模型制作、生产各类AI作品；</p>
              <p>（2）对AI作品进行发行、传播、展示、表演、放映、广播及信息网络传播；</p>
              <p>（3）对AI作品进行商业推广、授权使用及其他商业化运营；</p>
              <p>（4）基于授权演员肖像数据及AI模型开发的数字人形象用于直播、互动、代言等商业活动；</p>
              <p>（5）基于AI技术发展而产生的其他合理使用方式。</p>
              <p>2.2 未经甲方书面同意，乙方不得将本协议项下的权利再转授权给任何第三方。</p>
              <p>2.3 乙方可根据项目需求，选择以下授权模式之一：</p>
              <p>□非独家授权：甲方可同时向其他第三方授予相同演员、相同类型项目的权利，收费标准为：                     。</p>
              <p>□独家授权：在本项目范围内，甲方不得再向其他第三方授予该演员的相同权利，收费标准为：                 。</p>
              <p>
                2.4 本协议授权期限自
                <span class="inline-flex min-w-[140px] border-b border-[#54452f] px-2">{{ formatDateText(displayAuthorizationWindow.start) }}</span>
                起至
                <span class="inline-flex min-w-[140px] border-b border-[#54452f] px-2">{{ formatDateText(displayAuthorizationWindow.end) }}</span>
                止。授权期限届满，本协议自动终止。若项目制作周期延长，转授权期限自动顺延至项目制作完成之日，顺延期间费用按双方签订的《项目订单》继续执行。
              </p>
              <p>2.5 授权地域：全球。</p>
              <p>2.6 乙方仅获得本协议约定的肖像使用权，演员肖像权原始权属仍归演员所有，甲方与演员之间的知识产权归属按原协议执行，乙方不得主张任何肖像权及相关知识产权权益。</p>

              <p class="pt-2"><strong>第三条 合作费用与支付方式</strong></p>
              <p>3.1 双方确认，本协议为框架性合作协议。具体项目的费用标准、分成比例、支付方式、结算周期等，由双方在签署具体项目的《项目订单》时另行约定。</p>
              <p>3.2 甲方收到首付款后，向乙方出具授权使用证明，乙方方可启动项目制作。</p>

              <p class="pt-2"><strong>第四条 双方权利与义务</strong></p>
              <p>4.1 甲方权利义务</p>
              <p>4.1.1 保证转授权合法有效，向乙方提供必要的授权证明文件，确保乙方正常使用演员肖像；</p>
              <p>4.1.2 有权监督乙方肖像使用情况，发现乙方超范围、违规使用肖像，有权立即制止、收回授权并追责；</p>
              <p>4.1.3 配合乙方完成必要的授权沟通、素材协调工作。</p>
              <p>4.2 乙方在使用AI技术处理授权演员肖像时，应当遵守以下规范：</p>
              <p>4.2.1乙方不得将授权演员的肖像数据用于训练乙方自有AI模型或任何第三方AI模型，亦不得以任何形式向任何第三方提供、披露、出售或允许其访问前述数据。如乙方违反本条，除承担第6.2条约定的根本性违约责任外，还应立即：</p>
              <p>（1）在甲方监督下，彻底删除或销毁其控制的全部前述数据及该AI模型；</p>
              <p>（2）向甲方支付惩罚性违约金人民币 300000 元。</p>
              <p>4.2.2 不得利用AI技术制作并传播虚假新闻信息；</p>
              <p>4.2.3 不得利用授权演员肖像制作淫秽色情、赌博诈骗、暴力血腥等内容；生成内容应当健康、积极，不得含有色情、暴力、恐怖、赌博、毒品等违法内容；</p>
              <p>4.2.4 不得对授权演员肖像进行丑化、污损、歪曲；</p>
              <p>4.2.5 不得利用AI技术生成授权演员未曾发生的虚假言行或政治立场，损害演员名誉；</p>
              <p>4.2.6 依据《互联网信息服务深度合成管理规定》，乙方应在生成的AI短剧、广告等内容的显著位置添加AI生成标识，告知公众该内容涉及深度合成技术。因乙方未标识导致公众误解产生的法律责任，由乙方承担；</p>
              <p>4.2.7 项目制作完成后，如需超出约定期限使用肖像，需提前与甲方协商，另行签订补充协议并支付费用；</p>
              <p>4.2.8 协议终止或解除后，乙方应立即停止使用演员肖像，已制作完成的作品可按约定正常播出，不得再次剪辑、修改使用。</p>
              <p>4.2.9 乙方如因使用授权演员肖像（包括但不限于使用方式、使用范围、生成内容等）给甲方造成任何损失的，包括但不限于经济损失、名誉损失、商誉损害、对演员的违约赔偿、诉讼费、律师费、公证费等，乙方应当全额赔偿并承担全部责任。甲方拥有对本条款的最终解释权，乙方对此予以认可。</p>

              <p class="pt-2"><strong>第五条 协议终止与终止后的处理</strong></p>
              <p>5.1 本协议终止后，乙方应立即停止使用基于授权演员肖像训练的AI模型及相关数据，不得再用于生成任何新的AI作品或商业内容。乙方应在终止后10日内 删除或销毁相关数据。</p>
              <p>5.2 若本协议终止前已有项目正式启动制作（以已投入制作成本为准）但尚未完成，乙方有权继续完成该项目，但须按双方签订的《项目订单》继续向甲方支付分成。该项目完成后，乙方不得再使用该AI模型开展任何新项目。</p>

              <p class="pt-2"><strong>第六条 违约责任与协议终止</strong></p>
              <p>6.1 乙方逾期支付分成的，每逾期一日，按应付未付金额的 千分之五 支付违约金；逾期超过30日，甲方有权单方解除本合同。</p>
              <p>6.2 乙方超范围使用肖像、擅自转授权、违规损害演员形象的，视为根本性违约，需向甲方支付违约金人民币 300000 元，并立即停止违约行为、删除相关内容。违约金不足以弥补甲方损失的，乙方还应赔偿甲方的全部实际损失（包括甲方对演员的违约赔偿、甲方商誉损失等）。</p>
              <p>6.3 乙方在合同终止后继续使用AI模型生成新作品的，视为严重违约，甲方有权要求乙方支付违约金人民币 300000 元，并赔偿甲方全部损失。</p>

              <p class="pt-2"><strong>第七条 争议解决与其他</strong></p>
              <p>7.1 因本协议产生的争议，双方友好协商解决；协商不成的，提交甲方所在地人民法院诉讼解决。</p>
              <p>7.2 本协议一式两份，甲乙双方各执一份，盖章后生效，具有同等法律效力；未尽事宜，双方可签订补充协议，补充协议与本协议具有同等法律效力。</p>
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
                      <span class="agreement-inline-label">乙方（盖章）：</span>
                      <span class="agreement-inline-field agreement-inline-field-signature">
                        <span class="sr-only">乙方盖章区域</span>
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
                        {{ isAgreementLocked ? '协议已签署，盖章/签字内容已锁定。' : '请使用手写签名或盖章样式完成乙方签署。' }}
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
      </template>

      <section v-if="!loading && !isAgreementLocked" class="flex justify-end">
        <button
          type="button"
          :disabled="submitting || !agreement.template?.is_ready || !isEnterpriseBasicInfoReady"
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
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiRequest } from '../lib/api'
import { authStore } from '../lib/auth'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const entryNoticeMessage = ref('')
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
  party_b_company_name: '',
  party_b_credit_code: '',
  party_b_registered_address: '',
  party_b_signed_date: '',
  party_b_signature_data_url: ''
})
const fieldErrors = reactive({
  party_b_company_name: '',
  party_b_credit_code: '',
  party_b_registered_address: '',
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
const isEnterpriseBasicInfoReady = computed(() => (
  hasFilledText(form.party_b_company_name)
  && hasFilledText(form.party_b_credit_code)
  && hasFilledText(form.party_b_registered_address)
))

function resetMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function syncEntryNotice() {
  entryNoticeMessage.value = typeof route.query.notice === 'string'
    ? route.query.notice
    : ''
}

function resetFieldErrors() {
  fieldErrors.party_b_company_name = ''
  fieldErrors.party_b_credit_code = ''
  fieldErrors.party_b_registered_address = ''
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
  fieldErrors.party_b_company_name = errors.party_b_company_name || ''
  fieldErrors.party_b_credit_code = errors.party_b_credit_code || ''
  fieldErrors.party_b_registered_address = errors.party_b_registered_address || ''
  fieldErrors.party_b_signature_data_url = errors.party_b_signature_data_url || ''
  fieldErrors.party_b_signed_date = errors.party_b_signed_date || ''
}

function showSignatureHint({
  title = '还差一步就可以完成签署',
  message = '请在签字区域手写签名或绘制企业盖章后，再提交协议。'
} = {}) {
  signatureHint.visible = true
  signatureHint.title = title
  signatureHint.message = message
  nextTick(() => {
    signatureCard.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

function scrollToSignatureSection() {
  nextTick(() => {
    signatureCard.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

function scrollToPageTop() {
  nextTick(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  })
}

async function goToEnterpriseBasicInfo() {
  await router.push('/enterprise-basic-info')
}

function hasBasicInfoFieldErrors(errors = fieldErrors) {
  return Boolean(
    errors.party_b_company_name
    || errors.party_b_credit_code
    || errors.party_b_registered_address
  )
}

function hasFilledText(value) {
  return Boolean(String(value || '').trim())
}

function displayOrPlaceholder(value) {
  const normalized = String(value || '').trim()
  return normalized || '待管理员配置'
}

function displayAgreementField(value, placeholder) {
  const normalized = String(value || '').trim()
  return normalized || placeholder
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
  form.party_b_company_name = defaults.party_b_company_name || authStore.state.user?.display_name || ''
  form.party_b_credit_code = defaults.party_b_credit_code || ''
  form.party_b_registered_address = defaults.party_b_registered_address || ''
  form.party_b_signed_date = defaults.party_b_signed_date || ''
  form.party_b_signature_data_url = defaults.party_b_signature_data_url || ''
}

function validateBeforeSubmit() {
  resetFieldErrors()
  hideSignatureHint()
  let isValid = true

  if (!form.party_b_company_name.trim()) {
    fieldErrors.party_b_company_name = '请先在企业基本信息中填写企业名称。'
    isValid = false
  }
  if (!form.party_b_credit_code.trim()) {
    fieldErrors.party_b_credit_code = '请先在企业基本信息中填写统一社会信用代码。'
    isValid = false
  }
  if (!form.party_b_registered_address.trim()) {
    fieldErrors.party_b_registered_address = '请先在企业基本信息中填写注册地址。'
    isValid = false
  }
  if (!form.party_b_signed_date) {
    fieldErrors.party_b_signed_date = '请选择签署日期。'
    isValid = false
  }

  const isSignatureEmpty = !signaturePad || signaturePad.isEmpty()
  if (isSignatureEmpty) {
    fieldErrors.party_b_signature_data_url = '请完成乙方盖章/签字。'
    isValid = false
  }

  if (hasBasicInfoFieldErrors(fieldErrors)) {
    errorMessage.value = '请先前往企业基本信息页完善企业资料，再继续签署协议。'
    scrollToPageTop()
  } else if (fieldErrors.party_b_signed_date || fieldErrors.party_b_signature_data_url) {
    scrollToSignatureSection()
  }

  if (fieldErrors.party_b_signature_data_url && !hasBasicInfoFieldErrors(fieldErrors)) {
    showSignatureHint()
  }

  return isValid
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
    const payload = await apiRequest('/enterprise/agreement', { token: authStore.state.token })
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
  resetMessages()
  if (!agreement.value?.template?.is_ready) {
    errorMessage.value = '企业协议模板尚未配置完成，请联系管理员后再签署。'
    return
  }
  if (!validateBeforeSubmit()) {
    return
  }
  submitting.value = true
  try {
    const signatureDataUrl = signaturePad && !signaturePad.isEmpty()
      ? signaturePad.toDataURL('image/png')
      : form.party_b_signature_data_url

    const payload = await apiRequest('/enterprise/agreement/sign', {
      method: 'POST',
      token: authStore.state.token,
      body: {
        party_b_company_name: form.party_b_company_name.trim(),
        party_b_credit_code: form.party_b_credit_code.trim(),
        party_b_registered_address: form.party_b_registered_address.trim(),
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
    entryNoticeMessage.value = ''
    successMessage.value = '企业协议已签署成功，现在可以访问演员广场与演员详情了。'
  } catch (error) {
    const detail = error && typeof error === 'object' ? error.detail : null
    const nextFieldErrors = detail && typeof detail === 'object' && detail.field_errors ? detail.field_errors : null
    if (nextFieldErrors) {
      applyFieldErrors(nextFieldErrors)
      errorMessage.value = detail.message || '请检查标记出的企业信息或签署内容。'
    } else {
      const nextMessage = error instanceof Error ? error.message : '企业协议签署失败'
      if (nextMessage.includes('签字') || nextMessage.includes('盖章')) {
        fieldErrors.party_b_signature_data_url = nextMessage
        errorMessage.value = ''
      } else {
        errorMessage.value = nextMessage
      }
    }
    if (hasBasicInfoFieldErrors(fieldErrors)) {
      scrollToPageTop()
    } else if (fieldErrors.party_b_signed_date || fieldErrors.party_b_signature_data_url) {
      scrollToSignatureSection()
    }
    if (fieldErrors.party_b_signature_data_url && !hasBasicInfoFieldErrors(fieldErrors)) {
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
  syncEntryNotice()
  await loadAgreement()
  window.addEventListener('resize', handleResize)
})

watch(
  () => route.query.notice,
  () => {
    syncEntryNotice()
  }
)

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

.agreement-inline-display {
  line-height: 1.5;
  font-size: 0.95rem;
  white-space: pre-wrap;
}

.agreement-inline-display-multiline {
  align-items: flex-start;
}

.agreement-inline-placeholder {
  color: #8d7b60;
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

.secondary-button-dark {
  border-color: rgba(125, 211, 252, 0.22);
  background: rgba(63, 107, 86, 0.2);
  color: #e6f0ea;
}

.secondary-button-dark:hover {
  background: rgba(63, 107, 86, 0.28);
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
