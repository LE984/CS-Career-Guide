<template><span class="workspace-avatar-content"><img v-if="src && !failed" :src="src" :alt="alt" @error="failed = true" /><WorkspaceIcon v-else name="user" /></span></template>
<script setup>
import { ref, watch } from 'vue'
import WorkspaceIcon from './WorkspaceIcon.vue'
const props = defineProps({ src: String, alt: { type: String, default: '个人头像' } })
const failed = ref(false)
watch(() => props.src, () => { failed.value = false })
</script>
<style scoped>
.workspace-avatar-content { display: grid; place-items: center; width: 100%; height: 100%; border-radius: inherit; background: #eff3e8; overflow: hidden; }
img { width: 100%; height: 100%; object-fit: cover; }
svg { width: 35%; height: 35%; color: #849475; }
</style>
