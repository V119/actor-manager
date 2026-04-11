<template>
  <div class="flex h-screen w-full relative bg-background text-on-surface">
    <!-- SideNavBar -->
    <aside class="h-screen w-64 border-r border-sky-400/10 bg-slate-950/75 backdrop-blur-2xl flex flex-col flex-shrink-0 z-40 pt-16 fixed left-0">
      <div class="px-6 mb-8">
        <h1 class="text-lg font-bold text-sky-400 tracking-wider">Glacier AI Actor</h1>
        <p class="text-slate-500 text-xs mt-1">AI 演员模式</p>
      </div>
      <nav class="flex-1 space-y-1">
        <router-link to="/discovery" class="text-slate-400 flex items-center px-6 py-3 hover:bg-white/5 hover:text-sky-200 transition-all" active-class="bg-sky-400/10 text-sky-300 border-r-2 border-sky-300">
          <span class="material-symbols-outlined mr-3">dashboard</span>
          <span class="font-inter text-sm">演员发现广场</span>
        </router-link>
        <router-link to="/edit-portrait" class="text-slate-400 flex items-center px-6 py-3 hover:bg-white/5 hover:text-sky-200 transition-all" active-class="bg-sky-400/10 text-sky-300 border-r-2 border-sky-300">
          <span class="material-symbols-outlined mr-3">cloud_upload</span>
          <span class="font-inter text-sm">肖像上传</span>
        </router-link>
        <router-link to="/protocols" class="text-slate-400 flex items-center px-6 py-3 hover:bg-white/5 hover:text-sky-200 transition-all" active-class="bg-sky-400/10 text-sky-300 border-r-2 border-sky-300">
          <span class="material-symbols-outlined mr-3">description</span>
          <span class="font-inter text-sm">协议管理</span>
        </router-link>
        <router-link to="/style-lab" class="text-slate-400 flex items-center px-6 py-3 hover:bg-white/5 hover:text-sky-200 transition-all" active-class="bg-sky-400/10 text-sky-300 border-r-2 border-sky-300">
          <span class="material-symbols-outlined mr-3">auto_awesome</span>
          <span class="font-inter text-sm">风格实验室</span>
        </router-link>
      </nav>
      <div class="p-6 border-t border-white/5">
        <button class="text-slate-400 flex items-center hover:text-error transition-colors">
          <span class="material-symbols-outlined mr-3">logout</span>
          <span class="font-inter text-sm">退出</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 ml-64 relative overflow-y-auto">
      <!-- Top Navigation Bar -->
      <nav class="fixed top-0 left-64 right-0 bg-[#0a0e1a]/60 backdrop-blur-xl border-b border-sky-400/10 shadow-[0_0_30px_rgba(125,211,252,0.05)] z-50 flex justify-between items-center px-6 h-16">
        <div class="text-2xl font-semibold tracking-tighter text-sky-300">Glacier AI</div>
        <div class="flex items-center gap-4">
          <button class="p-2 rounded-full text-slate-400 hover:bg-sky-400/10 hover:text-sky-200 transition-all duration-300 active:scale-95">
            <span class="material-symbols-outlined">notifications</span>
          </button>
          <button class="p-2 rounded-full text-slate-400 hover:bg-sky-400/10 hover:text-sky-200 transition-all duration-300 active:scale-95">
            <span class="material-symbols-outlined">settings</span>
          </button>
          <div class="w-8 h-8 rounded-full overflow-hidden border border-sky-400/20">
            <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuA5q0kC-bP_9btLt9zOI7x_5IoKS3124FXsYC53PLDm4a8-NbaOl97pjcGCKxskhMLMCOYYikUvJSVhm1QROTNQWbkFavyDKLOFxDOeJm1lpvwStIIBdLDKZHaFRVdLuy3j_xmrOxegUz3df51_kTNUI8gYEqPy3b_VvtbKM6enK4nr4C6dcW_MHmZFTv50idNyuKQ2D6WR3YvOjt2w4sG9C4D0xOGiz2VtRY67c0pIHFJ0OrLXGCmU4PGDt_G-v68ujSWlIE92qQdf" alt="User" class="w-full h-full object-cover">
          </div>
        </div>
      </nav>

      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
