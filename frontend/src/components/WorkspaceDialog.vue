<template>
  <dialog ref="dialogRef" class="workspace-dialog" :aria-labelledby="titleId" @cancel.prevent="requestClose" @click="onBackdrop" @keydown="keepFocus">
    <header><div><p v-if="caption">{{ caption }}</p><h2 :id="titleId">{{ title }}</h2></div><button type="button" :disabled="busy" :aria-label="`关闭${title}`" @click="requestClose"><WorkspaceIcon name="close" /></button></header>
    <div class="workspace-dialog-body"><slot /></div>
    <footer v-if="$slots.footer"><slot name="footer" /></footer>
  </dialog>
</template>
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import WorkspaceIcon from './WorkspaceIcon.vue'
const props = defineProps({ open: Boolean, title: { type: String, required: true }, titleId: { type: String, required: true }, caption: String, busy: Boolean })
const emit = defineEmits(['close'])
const dialogRef = ref(null)
function syncOpen() { const dialog = dialogRef.value; if (!dialog) return; if (props.open && !dialog.open) dialog.showModal(); else if (!props.open && dialog.open) dialog.close() }
function requestClose() { if (!props.busy) emit('close') }
function onBackdrop(event) { if (event.target !== dialogRef.value) return; const box = dialogRef.value.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) requestClose() }
function keepFocus(event) {
  if (event.key !== 'Tab') return
  const nodes = [...dialogRef.value.querySelectorAll('button, a[href], input, select, textarea, [tabindex]')].filter(node => node.tabIndex >= 0 && !node.matches(':disabled') && node.getClientRects().length)
  const first = nodes[0], last = nodes.at(-1)
  if (!first) { event.preventDefault(); return }
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
}
watch(() => props.open, syncOpen, { flush: 'post' })
onMounted(syncOpen)
onBeforeUnmount(() => dialogRef.value?.close())
</script>
<style>
html:has(dialog.workspace-dialog[open]) { overflow: hidden; }
.workspace-dialog { width: min(720px, calc(100% - 40px)); max-height: calc(100dvh - 48px); padding: 0; border: 1px solid #dce1d4; border-radius: 20px; color: #242723; background: #fff; box-shadow: 0 24px 100px #24272320; }
.workspace-dialog[open] { display: flex; flex-direction: column; }
.workspace-dialog::backdrop { background: #20282065; backdrop-filter: blur(3px); }
.workspace-dialog > header { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 24px 28px; border-bottom: 1px solid #e1e2db; flex-shrink: 0; }
.workspace-dialog > header p { font-size: 11px; color: #6e716a; margin-bottom: 5px; }
.workspace-dialog > header h2 { font-size: 22px; font-weight: 600; line-height: 1.5; }
.workspace-dialog > header button { display: grid; place-items: center; width: 44px; height: 44px; border: 1px solid #e1e2db; border-radius: 10px; background: white; flex-shrink: 0; }
.workspace-dialog-body { padding: 28px; overflow-y: auto; min-height: 0; overscroll-behavior: contain; }
.workspace-dialog > footer { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 10px; padding: 18px 28px; border-top: 1px solid #e1e2db; flex-shrink: 0; }
@media(max-width:760px) { .workspace-dialog { width: calc(100% - 24px); max-height: calc(100dvh - 24px); border-radius: 16px; } .workspace-dialog > header, .workspace-dialog-body { padding: 20px; } .workspace-dialog > footer { padding: 16px 20px; } .workspace-dialog > header h2 { font-size: 20px; } }
</style>
