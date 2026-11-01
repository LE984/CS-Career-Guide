<template>
  <div class="min-h-screen bg-base-200">
    <Navbar />
    <main class="w-full py-6">
      <router-view />
    </main>
    <Footer />
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue' // 根组件
import Footer from './components/Footer.vue'
</script>
