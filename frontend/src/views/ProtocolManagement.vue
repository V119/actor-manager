<template>
  <div class="max-w-5xl mx-auto px-8 py-24 space-y-8 min-h-screen bg-background text-on-surface">
    <div class="flex p-1.5 bg-surface/60 backdrop-blur-xl border border-sky-400/10 rounded-xl w-fit">
      <button class="px-8 py-2.5 rounded-lg text-sm font-semibold transition-all bg-sky-400/10 text-sky-300 shadow-[0_0_20px_rgba(125,211,252,0.1)] border border-sky-400/20">
        待处理
      </button>
      <button class="px-8 py-2.5 rounded-lg text-sm font-semibold transition-all text-on-surface-variant hover:text-on-surface">
        已签署
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="protocol in protocols" :key="protocol.id" class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 p-6 rounded-xl group hover:border-sky-400/30 transition-all duration-300 relative overflow-hidden">
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-lg bg-surface-bright border border-white/10 flex items-center justify-center overflow-hidden">
              <span class="material-symbols-outlined text-primary text-2xl">business</span>
            </div>
            <div>
              <h3 class="font-semibold text-on-surface">{{ protocol.company }}</h3>
              <p class="text-xs text-on-surface-variant">发起于 {{ protocol.date }}</p>
            </div>
          </div>
          <span class="px-3 py-1 rounded-full bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider border border-primary/20">待处理</span>
        </div>
        <div class="space-y-2 mb-6">
          <div class="flex items-center gap-2 text-sm text-on-surface-variant">
            <span class="material-symbols-outlined text-sm">description</span>
            <span>{{ protocol.title }}</span>
          </div>
          <p class="text-sm text-on-surface/70 leading-relaxed">{{ protocol.summary }}</p>
        </div>
        <button @click="selectedProtocol = protocol" class="w-full py-3 bg-surface/40 hover:bg-sky-400/10 text-sky-300 font-semibold text-sm rounded-lg transition-all border border-sky-400/20 flex items-center justify-center gap-2">
          查看协议详情
          <span class="material-symbols-outlined text-lg">arrow_forward</span>
        </button>
      </div>
    </div>

    <!-- Detail Overlay (Half-screen Flyout) -->
    <div v-if="selectedProtocol" class="fixed inset-0 z-50 flex justify-end">
      <!-- Backdrop -->
      <div @click="selectedProtocol = null" class="absolute inset-0 bg-background/60 backdrop-blur-sm"></div>
      <!-- Content Panel -->
      <div class="relative w-full md:w-[600px] bg-surface/75 backdrop-blur-2xl border-l border-sky-400/20 shadow-2xl flex flex-col">
        <!-- Close Button -->
        <button @click="selectedProtocol = null" class="absolute top-6 left-[-50px] w-10 h-10 rounded-full bg-surface/60 backdrop-blur-md border border-sky-400/10 flex items-center justify-center text-on-surface hover:text-primary transition-colors">
          <span class="material-symbols-outlined">close</span>
        </button>
        <div class="p-8 border-b border-white/5">
          <div class="flex items-center gap-4 mb-4">
            <h2 class="text-xl font-bold text-on-surface">{{ selectedProtocol.company }} - {{ selectedProtocol.title }}</h2>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto p-8 space-y-6 text-sm text-on-surface/80 leading-relaxed font-inter">
          <section>
            <h4 class="text-on-surface font-semibold mb-2">一、授权范围</h4>
            <p>乙方（演员）特此不可撤销地授予甲方在全球范围内、在任何媒体形式中，为了推广项目之目的，使用乙方的姓名、肖像、声音及表演。</p>
          </section>
          <div class="p-4 bg-sky-400/5 rounded-lg border border-sky-400/10 italic text-sky-200/60">
            * 这仅是协议内容的摘要预览，完整版协议法律效力以最终签署的版本为准。
          </div>
        </div>
        <!-- Action Footer -->
        <div class="p-8 border-t border-white/5 bg-surface-container flex justify-end items-center gap-4">
          <button @click="selectedProtocol = null" class="px-8 py-3 rounded-xl border border-white/10 hover:bg-white/5 transition-all text-on-surface font-medium">拒绝</button>
          <button @click="selectedProtocol = null" class="px-8 py-3 rounded-xl bg-sky-400 text-slate-950 font-bold shadow-[0_0_20px_rgba(125,211,252,0.3)] hover:brightness-110 active:scale-95 transition-all flex items-center gap-2">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">edit_note</span>
            去签署
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const selectedProtocol = ref(null)
const protocols = [
  { id: 1, company: '星界影业有限公司', date: '2024.05.20', title: '3年肖像授权协议 (全球范围)', summary: '包含电影宣发、社交媒体推广及线下商业活动使用权。预计签署后 3 个工作日完成首笔款项拨付。' },
  { id: 2, company: '极光传媒实验室', date: '2024.05.18', title: 'AI 视频合成长期演职协议', summary: '涉及 12 个短视频系列制作，需授权数字分身在特定剧本框架下的表达权限。保密协议等级：高。' }
]
</script>
