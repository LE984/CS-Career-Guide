<template>
  <nav v-if="total > 0" class="page-controls" :aria-label="label">
    <p class="page-count">共 {{ total }} 条<span v-if="allowSize"> · 第 {{ page }} / {{ totalPages }} 页</span></p>
    <div class="page-actions">
      <label v-if="allowSize" class="page-size">每页<select :value="pageSize" :disabled="busy" @change="$emit('size', Number($event.target.value))"><option v-for="size in pageSizes" :key="size" :value="size">{{ size }} 条</option></select></label>
      <button type="button" :disabled="busy || page <= 1" aria-label="上一页" @click="$emit('page', page - 1)"><UiIcon class="previous" name="chevron" /></button>
      <template v-if="allowSize"><template v-for="(number, index) in numbers" :key="index"><span v-if="number === '…'" class="page-gap">…</span><button v-else type="button" class="page-number" :aria-current="number === page ? 'page' : undefined" :aria-label="`第 ${number} 页`" :disabled="busy" @click="number !== page && $emit('page', number)">{{ number }}</button></template></template>
      <span v-else class="page-gap" :aria-label="`第 ${page} 页，共 ${totalPages} 页`">{{ page }} / {{ totalPages }}</span>
      <button type="button" :disabled="busy || page >= totalPages" aria-label="下一页" @click="$emit('page', page + 1)"><UiIcon name="chevron" /></button>
    </div>
  </nav>
</template>
<script setup>
import { computed } from 'vue'
import { pageNumbers, pageSizes } from '@/features/company-reviews/browse.js'
import UiIcon from './UiIcon.vue'
const props = defineProps({ page: { type: Number, default: 1 }, pageSize: { type: Number, default: 10 }, total: { type: Number, default: 0 }, busy: Boolean, allowSize: { type: Boolean, default: true }, label: { type: String, default: '列表分页' } })
defineEmits(['page', 'size'])
const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const numbers = computed(() => pageNumbers(props.page, totalPages.value))
</script>
<style scoped>
.page-controls { display: flex; justify-content: space-between; flex-wrap: wrap; align-items: center; gap: 16px; margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--career-border); font-size: 12px; }
.page-count { color: var(--career-muted); }
.page-actions { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.page-actions button { display: grid; place-items: center; min-width: 36px; min-height: 40px; border: 1px solid var(--career-border); border-radius: 7px; background: white; padding-inline: 7px; }
.page-actions button[aria-current='page'] { color: white; background: #333f32; border-color: #333f32; }
.page-actions button:disabled { opacity: .4; cursor: not-allowed; }
.page-actions button:hover:enabled:not([aria-current]) { background: #eff2e9; }
.page-size { display: flex; align-items: center; gap: 6px; margin-right: 8px; }
.page-size select { min-height: 40px; border: 1px solid var(--career-border); border-radius: 7px; padding: 0 7px; background: white; }
.page-gap { padding-inline: 3px; }
.previous { transform: rotate(180deg); }
@media(max-width:760px) { .page-controls { gap: 10px; } .page-actions { width: 100%; gap: 4px; } .page-size { width: 100%; margin: 0 0 6px; } .page-count span { white-space: nowrap; } }
</style>
