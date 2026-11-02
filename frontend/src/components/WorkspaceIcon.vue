<template>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path v-for="(path, index) in paths[name] || paths.file" :key="index" :d="path" /></svg>
</template>
<script setup>
defineProps({ name: { type: String, default: 'file' } })
const paths = {
  file: ['M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8Z', 'M14 3v5h5M9 12h6M9 16h6'],
  save: ['M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h12l4 4v12a2 2 0 0 1-2 2Z', 'M7 3v6h10V3M7 21v-7h10v7'],
  download: ['M12 3v12M7 10l5 5 5-5M4 16v4h16v-4'],
  arrow: ['M4 12h16M14 6l6 6-6 6'],
  edit: ['M12 20h9M16 4l4 4M4 20l4-1L20 7a2.1 2.1 0 0 0-3-3L5 16Z'],
  message: ['M21 11a8 8 0 0 1-8 8H7l-4 3V6a3 3 0 0 1 3-3h7a8 8 0 0 1 8 8Z', 'M7 8h9M7 12h6'],
  user: ['M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0ZM4 21v-2a8 8 0 0 1 16 0v2'],
  plus: ['M12 5v14M5 12h14'],
  close: ['m6 6 12 12M6 18 18 6'],
  check: ['m5 12 4 4L19 6'],
  clock: ['M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM12 7v5l3 2'],
  school: ['m2 9 10-5 10 5-10 5Z', 'M6 11v6c4 3 8 3 12 0v-6M22 9v7'],
  briefcase: ['M8 6V4h8v2M3 7h18v14H3ZM3 12c6 4 12 4 18 0M10 13h4v3h-4Z'],
  compass: ['M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM16 8l-3 5-5 3 3-5Z'],
  code: ['m8 7-5 5 5 5M16 7l5 5-5 5M14 4l-4 16'],
  eye: ['M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z', 'M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z'],
  expand: ['M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5'],
  alert: ['M12 3 2 21h20ZM12 9v5M12 17h.01'],
  refresh: ['M20 7V3l-3 3A8 8 0 1 0 20 15M20 7h-5'],
}
</script>
<style scoped>
svg { width: 19px; height: 19px; flex-shrink: 0; }
</style>
