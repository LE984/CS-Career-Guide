<template><span class="streaming-text"><span>{{ head }}</span><span :class="{ 'reveal-tail': pending }">{{ tail }}</span><span v-if="active || pending" class="stream-cursor" aria-hidden="true"></span></span></template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { createTextReveal } from './text-reveal.js'
const props = defineProps({ text: { type: String, default: '' }, active: Boolean })
const emit = defineEmits(['reveal'])
const visible = ref(''), pending = ref(false)
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)')
const reveal = createTextReveal((text, busy) => {
  visible.value = text; pending.value = busy; emit('reveal')
}, { immediate: () => reducedMotion.matches || document.hidden })
const segmenter = new Intl.Segmenter('zh', { granularity: 'grapheme' })
const characters = computed(() => Array.from(segmenter.segment(visible.value), part => part.segment))
const head = computed(() => pending.value ? characters.value.slice(0, -6).join('') : visible.value)
const tail = computed(() => pending.value ? characters.value.slice(-6).join('') : '')
watch(() => props.text, text => reveal.set(text), { immediate: true })
const flushWhenHidden = () => { if (document.hidden || reducedMotion.matches) reveal.flush() }
document.addEventListener('visibilitychange', flushWhenHidden)
reducedMotion.addEventListener('change', flushWhenHidden)
onUnmounted(() => {
  reveal.dispose()
  document.removeEventListener('visibilitychange', flushWhenHidden)
  reducedMotion.removeEventListener('change', flushWhenHidden)
})
</script>

<style scoped>
.reveal-tail { opacity: .72; }
.stream-cursor { display: inline-block; width: 5px; height: 1em; margin-left: 4px; background: #7d9abb; vertical-align: -.1em; border-radius: 2px; animation: breathe 1.1s ease-in-out infinite; }
@keyframes breathe { 50% { opacity: .3; } }
@media (prefers-reduced-motion: reduce) { .stream-cursor { animation: none; } }
</style>
