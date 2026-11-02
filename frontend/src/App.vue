<template>
  <div class="app-shell min-h-screen">
    <Navbar />
    <main class="app-content w-full">
      <router-view />
    </main>
    <Footer />
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue' // 根组件
import Footer from './components/Footer.vue'
</script>
