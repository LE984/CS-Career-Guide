<template><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path :d="paths[name] || paths.arrow" /></svg></template>
<script setup>
defineProps({ name: { type: String, default: 'arrow' } })
const paths = {
  arrow: 'M5 12h14m-6-6 6 6-6 6', external: 'M14 4h6v6m0-6L10 14M10 4H4v16h16v-6',
  search: 'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
  close: 'm6 6 12 12M6 18 18 6', chevron: 'm8 5 7 7-7 7', down: 'm6 9 6 6 6-6',
  briefcase: 'M8 6V3h8v3M3 7h18v14H3zM3 12c5 3 13 3 18 0M10 13h4',
  school: 'm2 8 10-5 10 5-10 5zM6 10v7l6 4 6-4v-7M22 8v9',
  location: 'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0ZM15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
  shield: 'M12 3 3 7v5c0 5 9 9 9 9s9-4 9-9V7zM8 12l3 3 5-6',
  alert: 'm12 3 10 18H2zM12 9v5m0 3v.1', star: 'm12 3 2.8 5.8 6.4.9-4.6 4.5 1.1 6.3-5.7-3-5.7 3 1.1-6.3L2.8 9.7l6.4-.9z',
  message: 'M3 4h18v13H9l-6 4zM7 8h10M7 12h6', refresh: 'M20 7a9 9 0 1 0 1 9M20 2v6h-6',
  calendar: 'M5 5h14v16H5zM8 2v6m8-6v6M5 11h14', check: 'm5 12 4 4L19 6',
}
</script>
<style scoped>svg { width: 20px; height: 20px; flex-shrink: 0; }</style>
