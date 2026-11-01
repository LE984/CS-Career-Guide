<template>
  <footer class="w-full py-20 bg-slate-50 border-t border-slate-200/50">
    <div class="max-w-7xl mx-auto px-8 grid grid-cols-1 md:grid-cols-4 gap-16">
      <div class="md:col-span-1">
        <span class="text-2xl font-black text-indigo-600 mb-8 block">CS Career Guide</span>
        <p class="text-slate-500 font-medium text-sm leading-7 mb-6">© {{ new Date().getFullYear() }} CS Career Guide. <br/>专为计算机学子打造的职业成长平台，   赋能每一位开发者的职场梦想。</p>
      </div>
      <div class="flex flex-col gap-6">
        <h5 class="font-black text-slate-900 text-sm uppercase tracking-widest">快速链接</h5>
        <div class="flex flex-col gap-4">
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">关于我们</a>
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">职业路径</a>
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">AI 助手</a>
        </div>
      </div>
      <div class="flex flex-col gap-6">
        <h5 class="font-black text-slate-900 text-sm uppercase tracking-widest">法律合规</h5>
        <div class="flex flex-col gap-4">
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">隐私政策</a>
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">服务条款</a>
        </div>
      </div>
      <div class="flex flex-col gap-6">
        <h5 class="font-black text-slate-900 text-sm uppercase tracking-widest">联系支持</h5>
        <div class="flex flex-col gap-4">
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">联系我们</a>
        </div>
      </div>
    </div>
  </footer>
</template>
