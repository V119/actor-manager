<template>
  <div class="min-h-screen bg-background text-on-background relative overflow-y-auto pt-24 px-8 pb-12">
    <!-- Section 1: Top Horizontal Scroll (Reference Photos) -->
    <section class="mb-10">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-semibold text-primary uppercase tracking-widest flex items-center gap-2">
          <span class="w-1.5 h-1.5 bg-primary rounded-full"></span>
          已上传基础照
        </h3>
        <button class="text-xs text-on-surface-variant hover:text-primary transition-colors flex items-center gap-1">
          <span class="material-symbols-outlined text-base">add_circle</span> 管理肖像
        </button>
      </div>
      <div class="flex gap-4 overflow-x-auto pb-4 -mx-2 px-2 scroll-smooth">
        <div v-for="n in 4" :key="n" class="flex-shrink-0 w-44 h-56 rounded-xl bg-surface/60 backdrop-blur-xl border border-sky-400/10 p-1.5 transition-transform hover:scale-105 duration-300 group">
          <img class="w-full h-full object-cover rounded-lg" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBQzwvjxATKWKYWtrGhGQXa0FKlgLHTe6kLD_IGfsBx8WoBLl8M9QuxAr3FP9AvUDi2N8Lx8OLoNKjCNsuHgyjEHm40qlsbRl4yonZFqJ4T4aOSjwvJ5pjjuSj_qLYxO2ezmi0KWuxWbQHLYqyjokq4U6MVHP3FQ7ShYo0UNEuKDj6zggUCzvSf6ceBdo8xPXwafUbQ8faGgj3pM-Mjw1ST2GPQy3V0SNh6cW_CwxNgnkRELaYMfb-Y1oQolI3ixAlfjTZ7Pv3mZ2w2" alt="Portrait">
        </div>
      </div>
    </section>

    <!-- Section 2: Style Selection -->
    <section class="mb-10">
      <h3 class="text-sm font-semibold text-primary uppercase tracking-widest flex items-center gap-2 mb-4">
        <span class="w-1.5 h-1.5 bg-primary rounded-full"></span>
        选择视觉风格
      </h3>
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <div v-for="style in styles" :key="style.name" class="group cursor-pointer relative overflow-hidden rounded-2xl bg-surface/60 backdrop-blur-xl border border-sky-400/10 p-2 hover:border-primary/30 transition-all duration-300">
          <div class="aspect-[3/4] rounded-xl overflow-hidden mb-3 relative">
            <img :src="style.img" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110">
            <div class="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent opacity-60"></div>
          </div>
          <div class="px-2 pb-2">
            <p class="text-sm font-bold text-on-surface">{{ style.name }}</p>
            <p class="text-[10px] text-on-surface-variant">{{ style.en }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 3: Core Interaction Button -->
    <section class="flex flex-col items-center py-8 mb-12">
      <button class="relative group px-12 py-4 bg-primary/20 rounded-full border border-primary/50 text-primary font-bold text-lg flex items-center gap-3 transition-all duration-300 hover:bg-primary/30 active:scale-95 shadow-[0_0_20px_rgba(125,211,252,0.2)] hover:shadow-[0_0_40px_rgba(125,211,252,0.4)]">
        <span class="material-symbols-outlined text-2xl" style="font-variation-settings: 'FILL' 1;">auto_fix_high</span>
        开始生成
      </button>
      <p class="text-xs text-on-surface-variant mt-4">预计耗时 15-30 秒，消耗 2 个积分</p>
    </section>

    <!-- Section 4: Results -->
    <section>
      <h3 class="text-sm font-semibold text-primary uppercase tracking-widest flex items-center gap-2 mb-6">
        <span class="w-1.5 h-1.5 bg-primary rounded-full"></span>
        最近生成结果
      </h3>
      <div class="columns-2 md:columns-3 lg:columns-4 gap-6 space-y-6">
        <div v-for="n in 6" :key="n" class="break-inside-avoid relative group rounded-2xl overflow-hidden bg-surface/60 border border-white/10 hover:border-primary/50 transition-all duration-500">
          <img class="w-full h-auto" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA-RzienHssUZcVfN0mIdVUUi_q7wF3_ZzgLmDeeZBVK0XZ7c719SfZauZ8Igc4y_Cn5fIZUMm01DXXS7aD54xR73ZfsUDHGXsqXyu_olGzY6bgBz1RaysLcG6YAMIAn2meRBXrkI3bv4J45YC67kl9NjyQgI6R5mptBdhxrCz7uhmKiGxXDLRXHGSyffmhbUhEIDfzr64OqUqte_V0j6XlN0qQ1pqSk3OD8_9XWEbIyjTVXWpPjFZpI6eEKeXdcPLRLeFKU9bsYlj_">
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
const styles = [
  { name: '古装魅影', en: 'Historical & Epic', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD00KMgUb0Pckf9vLFC8_RU4BlI3xMCYS05fAaxWQombg-8VnMusIk_SfJCNs51mZ7SxuBB85MYyuA8HkAHVqxgrls1VSCnliNKV_377DH5AI-D8FhjE_E-5n2mjFG_AJibwqJwE2kd6Vf4N_jZleRfUW-1gYLBx-UyetLcO_tx-y0tnfy2KMRYN7gWapcZ2Kje906S1MO9pTNC3eiAxYAyGEmEDSvwdWsyU7Lw4x6L9NFSbPALwLofjPmBk-mPKtGWndQL4XLSDduj' },
  { name: '现代极简', en: 'Modern Minimal', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCCZs5TPGFVy7JxseOoRpt8ezORT4adYH1cLjLsfp5HwenWR0EAzvRjQR22wI00LqEbbaqgGEwUtgeEcKoBAtPUwM_dtJiibusH0TJNBU30sYtrvL40xAqi-Ns0c7JLTOV3h72DXvX6Toa22BbBPgoLiTJinqUdqbV99A7QQCry8kajB7T_Va_xaPcJtSlgEhwhJ545kIY4-tCXPMzNs9VZ5Uwqkchx2O96uByo3QsrVZrypve84zqpWcUXqELIEha4NgOjby9qGD7N' },
  { name: '科幻纪元', en: 'Sci-Fi Future', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC7z6PepGrJ0qBZXFAYCy4QFm1wBJZdCOwQCHYnedhZNDcAvQNL4iGlLWGD-tXGIvRQ4RNyEcHcFte2alc8rvInBo2OHqY-XQqyL5hi55R-cqeBUjQReBS18zlAGWumtnG9no_Ltj4CajfiTZ-q388miAWEewFK3PlYjQrYWkj_gTJBLiTShCSSxv9gbyKHWuHIqy6CcJKQ46FHVfRL8GFzafZ7EKhnIX7fo_0sNsgV7ahhNP5Cq9QrsloDNf9fibTGk5NiIMFOCFzI' },
  { name: '黑色电影', en: 'Classic Noir', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAiMkiCMGfe655OOompjW1VvTAU0RU3YE8YjQmjzszegWx9nORlWnhZ2Z0Tp_Dp4sxZbX9ZSJfSZOUp4CErcsW2P3p8OdO9Lb3znojkfBDi2h28Hp3low-6kaHCwW8KAS9sesuve6UHV1ihr6h8a3pRcwGht0Vy8ZN5VCrNGbX2lzA6DWpSf_wHKRx0iC6O5MRYRuHwVTB6M-bSkJa0EDkI8af9KgR0QtR969HHnFC4ajnKR1joR43QaVgFaUY2GKyThGWLF2dYU_E1' },
  { name: '油画质感', en: 'Oil Painting', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC9ipTxbm-qu6iG2QPAj3nqp4AOHKOW90w-SWgTR1EcK5dwWhFfyX8PJQPzY-B0OfbKxN2sgUtQJqqMKBXbUdMqUoBsQ9VeRE6gkRhc7fkFOz4sxTTopU3Dz1QFbGH05fD8X4y0PqFzcZxDo2LdCx-B4szCAnJHuUosFvTXKctdMun_ymrRWle9pKy63DTN_3mXGJQgmR4JcALzmtYRg8egVqJuPHExwmfjx31EOZvUgNbJvYcNahq54dK1nka59YiPX9SzSsrLJ4RE' }
]
</script>
