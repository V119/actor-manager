<template>
  <div class="flex-1 overflow-y-auto bg-background p-8 pt-24 min-h-screen">
    <div class="max-w-7xl mx-auto">
      <section class="mb-10 space-y-6">
        <div class="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div class="relative w-full md:w-96 group">
            <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-sky-300 transition-colors">search</span>
            <input class="w-full bg-surface/40 border border-sky-400/10 rounded-full py-3 pl-12 pr-6 text-on-surface placeholder:text-slate-500 focus:outline-none focus:border-sky-400/40 focus:ring-1 focus:ring-sky-400/40 transition-all backdrop-blur-sm" placeholder="搜索全球顶尖 AI 演员..." type="text"/>
          </div>
          <div class="flex items-center gap-2 text-sm text-slate-400">
            <span class="material-symbols-outlined text-lg">sort</span>
            <span>排序方式:</span>
            <button class="text-sky-300 font-medium">推荐</button>
          </div>
        </div>
        <div class="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-hide">
          <button v-for="tag in tags" :key="tag" class="px-6 py-2 rounded-full border border-white/10 text-on-surface-variant text-sm font-medium whitespace-nowrap hover:bg-white/5 hover:border-sky-300/30 transition-all" :class="tag === '全部演员' ? 'bg-sky-300 text-on-primary font-semibold shadow-lg shadow-sky-400/10' : 'bg-surface/60'">
            {{ tag }}
          </button>
        </div>
      </section>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div v-for="actor in actors" :key="actor.id" class="bg-surface/40 backdrop-blur-md border border-sky-400/10 rounded-xl overflow-hidden flex flex-col group hover:border-sky-400/30 hover:translate-y-[-4px] transition-all duration-300">
          <div class="relative aspect-[3/4] overflow-hidden">
            <img :src="actor.img" :alt="actor.name" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
            <div class="absolute top-3 right-3 bg-slate-950/40 backdrop-blur-md px-3 py-1 rounded-full border border-sky-400/20 flex items-center gap-1.5">
              <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
              <span class="text-[10px] font-bold text-emerald-400 tracking-wider">已发布</span>
            </div>
          </div>
          <div class="p-5 flex flex-col gap-3">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-lg font-bold text-on-surface tracking-tight">{{ actor.name }}</h3>
                <p class="text-xs text-on-surface-variant">ID: {{ actor.external_id }}</p>
              </div>
              <button class="text-sky-300 hover:text-sky-200 transition-colors">
                <span class="material-symbols-outlined">favorite</span>
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span v-for="t in actor.tags" :key="t" class="px-2.5 py-0.5 text-[10px] font-semibold rounded bg-sky-400/10 text-sky-300 border border-sky-400/20">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const tags = ['全部演员', '甜美', '硬汉', '动作', '学院', '古典', '科技感']
const actors = [
  { id: 1, name: '苏长生', external_id: 'GL-928374', tags: ['硬汉', '武打', '冷峻'], img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAVVe-CtMV2MaDhQFqCqhT0Kq3vK0DdMpbbcopsBD74Aa_yD1LLlqUuXM_O3I8k1QqbmJ6h1VubQKb-nE6lBOZZg051RojR5PCKCOtusVOVgT1bULA-OWObZR7xb52BIG0ljeQRCPEZpLRAmtsu69tw651Alu5vevpRgXESgInA4xVdb40JSLWw7FhrSd1CKBSZVEkkUTP-UopBxt6QBOw5kMK0Kf9Y-nDKVSpDVvOaN2bttCdc9GIZBzLK_ijlNrqBqe4pYn9qmnNT' },
  { id: 2, name: '林清漪', external_id: 'GL-928375', tags: ['甜美', '学院', '气质'], img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDmxKTX8W2oD-ImUo2aVSlLkTJcKhNtpGPxEzU_wOHy-pdF2ujWoTonNtHk3ce6nZHMXn-B_KrPuHRQIs9UZbgqK5Z1TiIrPf-G__X3PwhJaviz0pxmvdarD4NmGibWEnsZtA0YjZFWmdn-Izvg_blaZ83hm8iVai8W2HaaEmOpYn9AmmyQTGZQ5kiwoK2dMnEcbykVhGMlbnhooN0SEc9LcC_KsuV9_Vc9qqzN8vzwcA-Xvlhch5Kr6sf-jdKYHdauua-K_6f6YiPC' }
]
</script>
