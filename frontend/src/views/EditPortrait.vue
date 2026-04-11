<template>
  <div class="min-h-screen bg-background text-on-surface font-body selection:bg-primary/30 selection:text-primary">
    <main class="max-w-7xl mx-auto px-8 pt-24 pb-12">
      <header class="flex justify-between items-end mb-10">
        <div class="space-y-2">
          <div class="flex items-center gap-3">
            <h1 class="text-3xl font-bold tracking-tight text-on-surface font-headline">肖像编辑</h1>
            <span class="px-3 py-1 bg-surface-container-highest text-primary text-xs font-semibold rounded-full border border-primary/20 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              草稿
            </span>
          </div>
          <p class="text-on-surface-variant max-w-xl">完善您的基础素材与特征标签，让 AI 系统更好地理解并生成您的多维数字形象。</p>
        </div>
        <div class="hidden lg:flex items-center gap-4">
          <button class="px-6 py-2.5 rounded-lg border border-outline-variant text-on-surface hover:bg-white/5 transition-all active:scale-95">
            存草稿
          </button>
          <button class="px-6 py-2.5 rounded-lg bg-primary/20 border border-primary/50 text-primary hover:bg-primary/30 transition-all active:scale-95 shadow-[0_0_20px_rgba(125,211,252,0.15)]">
            确认发布
          </button>
        </div>
      </header>

      <div class="grid grid-cols-1 xl:grid-cols-12 gap-8">
        <!-- Left Column: Media Assets -->
        <div class="xl:col-span-8 space-y-8">
          <section class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 rounded-xl p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-lg font-semibold flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">image</span>
                基础素材区
              </h2>
              <span class="text-xs text-on-surface-variant">请上传高清、无遮挡的照片</span>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div v-for="slot in imageSlots" :key="slot.label" class="aspect-[3/4] relative group rounded-lg overflow-hidden bg-surface/60 border-dashed border-2 border-primary/10 hover:border-primary/40 transition-all cursor-pointer">
                <img v-if="slot.url" :src="slot.url" :alt="slot.label" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110">
                <div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-2">
                  <span class="material-symbols-outlined text-on-surface-variant text-3xl">add</span>
                  <span class="text-[10px] text-on-surface-variant uppercase tracking-widest">Upload Image</span>
                </div>
                <div class="absolute bottom-3 left-3 px-2 py-1 bg-slate-950/60 backdrop-blur-md rounded-md border border-white/10">
                  <span class="text-xs font-medium" :class="slot.url ? 'text-primary' : 'text-on-surface-variant'">{{ slot.label }}</span>
                </div>
              </div>
            </div>
          </section>

          <section class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 rounded-xl p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-lg font-semibold flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">movie</span>
                动态视频区
              </h2>
              <span class="text-xs text-on-surface-variant">提供 5-10 秒的面部多角度视频</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="relative aspect-video rounded-lg overflow-hidden bg-surface/60 group cursor-pointer border border-primary/10">
                <div class="absolute inset-0 bg-slate-950/40 flex items-center justify-center">
                  <div class="w-16 h-16 rounded-full bg-primary/20 backdrop-blur-xl border border-primary/50 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <span class="material-symbols-outlined text-primary text-4xl" style="font-variation-settings: 'FILL' 1;">play_arrow</span>
                  </div>
                </div>
              </div>
              <div class="relative aspect-video rounded-lg overflow-hidden bg-surface/60 border-dashed border-2 border-primary/10 hover:border-primary/40 transition-all flex flex-col items-center justify-center gap-3 group cursor-pointer">
                <div class="w-12 h-12 rounded-full bg-surface-container-highest flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                  <span class="material-symbols-outlined text-on-surface-variant group-hover:text-primary transition-colors">videocam</span>
                </div>
                <p class="text-sm font-medium text-on-surface-variant">上传侧面动态展示</p>
              </div>
            </div>
          </section>

          <!-- Tips / Info Panel -->
          <div class="p-5 rounded-xl border border-sky-400/5 bg-sky-400/5 space-y-3">
            <div class="flex items-center gap-2 text-sky-300">
              <span class="material-symbols-outlined text-[20px]">info</span>
              <span class="text-sm font-semibold">发布指南</span>
            </div>
            <ul class="text-xs text-on-surface-variant space-y-2 leading-relaxed">
              <li class="flex items-start gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-sky-400 mt-1 flex-shrink-0"></span>
                素材越多，AI 生成的肖像一致性越强。
              </li>
              <li class="flex items-start gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-sky-400 mt-1 flex-shrink-0"></span>
                请确保背景尽量简洁，以便系统进行自动扣像。
              </li>
              <li class="flex items-start gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-sky-400 mt-1 flex-shrink-0"></span>
                标签将直接影响您在剧组端的搜索权重。
              </li>
            </ul>
          </div>
        </div>

        <!-- Right Column: Tag Management -->
        <div class="xl:col-span-4 space-y-8">
          <section class="bg-surface/75 backdrop-blur-2xl border border-sky-400/15 rounded-xl p-6 h-fit sticky top-24">
            <div class="flex items-center gap-2 mb-6">
              <span class="material-symbols-outlined text-tertiary">sell</span>
              <h2 class="text-lg font-semibold">标签管理</h2>
            </div>
            <div class="space-y-6">
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-medium ml-1">添加新标签</label>
                <div class="relative">
                  <input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-3 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/20 outline-none transition-all placeholder:text-outline" placeholder="输入标签按回车..." type="text"/>
                  <button class="absolute right-3 top-1/2 -translate-y-1/2 text-primary hover:text-primary-fixed-dim transition-colors">
                    <span class="material-symbols-outlined">add_circle</span>
                  </button>
                </div>
              </div>
              <div class="space-y-3">
                <h3 class="text-xs text-on-surface-variant font-medium ml-1">当前已选</h3>
                <div class="flex flex-wrap gap-2">
                  <div v-for="tag in selectedTags" :key="tag" class="px-4 py-1.5 bg-primary/10 text-primary text-xs font-semibold rounded-full border border-primary/30 flex items-center gap-2 group transition-all hover:bg-primary/20">
                    {{ tag }}
                    <button class="hover:text-white transition-colors"><span class="material-symbols-outlined text-[14px]">close</span></button>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selectedTags = ref(['硬汉', '古装', '都市精英'])
const imageSlots = ref([
  { label: '正脸', url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCRID0babGi56R0vdZTNmZi8D504GU-zSQ_x9sMmonnBewZQCPeiq34wgOhwyWy_dvijQZkw8SeF8JVg1eb7sjZn9X71nwRzhu3svfu4Jo6pXaXfd5_s2aw5Ezyr5vO6pIhGzlyWPfgFybZpe2qgp73-aWLlU9RoOrevqLSB25-ZrLNsqIvo9uHJPYshlgjdKYXWXIaqLviVtmWdxzxQ7KLNgQMTtUdZy7hEjEMBqxEyjVS8szeWgN5hqEMMA1lzRVik9pgzk8xJI9i' },
  { label: '左侧', url: '' },
  { label: '右侧', url: '' },
  { label: '全身', url: '' }
])
</script>
