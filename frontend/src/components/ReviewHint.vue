<script setup lang="ts">
defineProps<{ content: string }>();
</script>

<template>
  <div class="review-hint">
    <div class="hint-header">质检建议 (基于历史案例库)</div>
    <div class="hint-body">{{ content }}</div>
  </div>
</template>

<style scoped>
.review-hint {
  background: #fef9e7;
  border: 1px solid #f9e79f;
  border-radius: 6px;
  padding: 8px 12px;
  margin-left: 40px;
  margin-bottom: 8px;
  max-width: 80%;
  font-size: 13px;
}

.hint-header {
  font-size: 11px;
  font-weight: 600;
  color: #b7950b;
  margin-bottom: 4px;
}

.hint-body {
  color: #666;
  line-height: 1.6;
}
</style>
