<template>
  <div class="flex-1 pt-24 px-8 pb-12 overflow-y-auto bg-background text-on-surface">
    <div class="max-w-7xl mx-auto grid grid-cols-12 gap-8">
      <!-- 1. Actor Profile Hero Section -->
      <section class="col-span-12 lg:col-span-8">
        <div class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 p-8 rounded-xl flex flex-col md:flex-row gap-8 items-start relative overflow-hidden">
          <div class="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 blur-[100px] rounded-full"></div>
          <div class="w-48 h-64 rounded-xl overflow-hidden border-2 border-primary/20 shrink-0 relative group">
            <img alt="Actor Avatar" class="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuD9xOeWWM-jWAGILA81XqH26NeDYHoqtGJWE9brsTAGIiWw7kgjEJmhS9d25ZDEFQybXpSuk9M_jCEvPBHtXPid3MZ5GZKW2JezdodqzKL0BgEEX6Hj4IlvV5mgXkbks3cx4bd8E19xJxVGT1tENU9rYe3gtZ2xAs7dkwy2hkTeuysJ7qzuM90wWoIhgFKDYdLY5ylh0wX45zCP4PKhlDQBAr0mu0zk4x0jVLSNsJZAacfBelDO38vlM_4rieH1BZ0uq7nQpgs-BsoA"/>
            <div class="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent flex items-end p-4">
              <span class="text-xs text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">VERIFIED</span>
            </div>
          </div>
          <div class="flex-1 space-y-4">
            <div>
              <h1 class="text-4xl font-extrabold text-on-surface tracking-tight mb-2">苏哲远 <span class="text-primary font-light">Su Zheyuan</span></h1>
              <div class="flex items-center gap-4 text-on-surface-variant text-sm">
                <span class="flex items-center gap-1"><span class="material-symbols-outlined text-sm">cake</span> 24岁</span>
                <span class="flex items-center gap-1"><span class="material-symbols-outlined text-sm">location_on</span> 上海 / 中国</span>
                <span class="flex items-center gap-1"><span class="material-symbols-outlined text-sm">height</span> 182cm</span>
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              <span v-for="tag in ['冷峻硬朗', '赛博朋克风', '商业广告']" :key="tag" class="px-3 py-1 bg-surface-variant border border-outline-variant text-primary rounded-full text-xs">{{ tag }}</span>
            </div>
            <p class="text-on-surface-variant text-sm leading-relaxed max-w-xl">
              拥有极高辨识度的亚洲面孔，五官立体，适合塑造未来主义或高端时尚风格。AI 肖像库已完成 8k 精度训练，覆盖运动、职场、科幻等多种商业场景。
            </p>
          </div>
        </div>
      </section>

      <!-- 3. Sidebar/CTA Section -->
      <section class="col-span-12 lg:col-span-4 space-y-6">
        <div class="bg-surface/75 backdrop-blur-2xl border border-sky-400/15 p-6 rounded-xl border-primary/30 shadow-[0_0_30px_rgba(125,211,252,0.1)] relative">
          <div class="flex justify-between items-center mb-6">
            <span class="text-on-surface-variant text-xs uppercase tracking-widest font-semibold">合作状态</span>
            <span class="flex items-center gap-1 text-emerald-400 text-xs"><span class="w-2 h-2 bg-emerald-400 rounded-full"></span> 可签约</span>
          </div>
          <button class="w-full py-4 bg-primary text-on-primary font-bold rounded-lg hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2 mb-4">
            <span class="material-symbols-outlined" style='font-variation-settings: "FILL" 1;'>handshake</span>
            发起签约
          </button>
          <div class="space-y-4 p-4 bg-surface-container-low rounded-lg border border-outline-variant/30">
            <h4 class="text-xs font-bold text-sky-300 flex items-center gap-2">
              <span class="material-symbols-outlined text-sm">gavel</span> 版权说明
            </h4>
            <p class="text-[11px] text-on-surface-variant leading-tight">
              该演员的所有“原始肖像”及生成的“AI 形象”均已在 Glacier 链上进行版权存证。签约后可获得在合同范围内的肖像使用权及衍生品开发权。严禁任何未经授权的训练与传播。
            </p>
          </div>
        </div>

        <div class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 p-6 rounded-xl space-y-4">
          <h4 class="text-sm font-semibold">快速统计</h4>
          <div class="grid grid-cols-2 gap-4">
            <div class="p-3 bg-surface-container-high rounded-lg">
              <p class="text-xs text-on-surface-variant">生成次数</p>
              <p class="text-xl font-bold text-primary">1.2k+</p>
            </div>
            <div class="p-3 bg-surface-container-high rounded-lg">
              <p class="text-xs text-on-surface-variant">品牌合作</p>
              <p class="text-xl font-bold text-tertiary">14</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 2. Media Matrix -->
      <section class="col-span-12 space-y-8 mt-4">
        <div>
          <div class="flex items-center justify-between mb-4 px-2">
            <h2 class="text-xl font-semibold flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">camera_front</span>
              原始肖像 <span class="text-xs text-on-surface-variant font-normal">(Raw Portraits)</span>
            </h2>
            <button class="text-primary text-sm hover:underline">查看全部</button>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <div v-for="n in 5" :key="n" class="group relative aspect-[3/4] rounded-lg overflow-hidden border border-white/10">
              <img class="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBSDkWuJTcTMYqm9N3kU78N0GWxb8DDJt4TG01i5TSDmWoQie7lHzj8S6k7O6zev5LoC8mZR_BkVV-cpc4eMRPkSaUAGfTRo87uioI0hwbGdVLsJSj72xqj9Qjj7FKrBDHjy5upx3uyiBFoSmjq816cvukBibRnitD44XiouTeL-eEXvZ-q3pIO1h3C8xvVJ2pZ8wF-fa00lsHWkrFBzIWjprn1joW3-439xP6daeMoLDuoF8p3a_jmnP5KL6Mh_itIpT2NjW1LS3kq">
            </div>
          </div>
        </div>

        <!-- AI Image Vault -->
        <div>
          <div class="flex items-center justify-between mb-4 px-2">
            <h2 class="text-xl font-semibold flex items-center gap-2">
              <span class="material-symbols-outlined text-tertiary">auto_fix_high</span>
              AI 形象库 <span class="text-xs text-on-surface-variant font-normal">(AI-Generated Persona)</span>
            </h2>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
            <div class="lg:col-span-2 bg-surface/60 backdrop-blur-xl border border-sky-400/10 rounded-xl overflow-hidden group">
              <div class="relative aspect-video">
                <img class="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuC7VKtU0D4-wogPM_OqB-Rmz0IFSLhC1-FBNyGSkqfEywOw2H9s84az2cxlc5KC032-te0jyFYRpB6lJ24pEXPsYmkohSqsgylI3uGz2_igec3suF22tEpifmTE5L9wTOOvBgoVfbuy77VuhRbc0UESm_gA0iHIbXrt75pN1CvxOk4VmPPXEJtkHb9_y6IDz7J4XsPrj5ZzSDpPGbCW-dWVkGTSvaj62ASkF_bgInr7_ycwS9DRhSsqzc0GOZa4cAnGwlyMBqsL-3Qq"/>
              </div>
              <div class="p-4 border-t border-white/5 bg-surface/50">
                <p class="text-sm font-medium">未来纪元：驾驶舱指令</p>
                <p class="text-xs text-on-surface-variant">生成于 2024.05.12</p>
              </div>
            </div>
            <div v-for="n in 2" :key="n" class="bg-surface/60 backdrop-blur-xl border border-sky-400/10 rounded-xl overflow-hidden group">
              <div class="relative aspect-square">
                <img class="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBXNFG83CqC-zqn0SRtKskY3ak85DMuWD22qp3Z-KwrmTptIC_XhsilkJd865q9FPgDhveNcM5xc1vCfrjwXMUhAruSeImHLjaQHmYxNZBV4Jry8jD9GV0rJVdgv-n9i9Jt2lM2SU4EvaJD569rTqmPn8OuSUOpuA2lSKIa8LA-NkSBEZYiVTN7Sw_Lev-hGOw5WwCFXYcNegnZNc9Y0ATRoUA2NqdjqzYFO11E_26t1K4HvninLA-h0gcnqI5TwK3aJ4H6DCxfj1Iw"/>
              </div>
              <div class="p-4 border-t border-white/5 bg-surface/50">
                <p class="text-sm font-medium">都市精英系列</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
</script>
