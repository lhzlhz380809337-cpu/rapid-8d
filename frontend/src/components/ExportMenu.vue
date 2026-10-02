<script setup lang="ts">
import { reportApi } from "../api/report";

const props = defineProps<{ sessionId: string }>();

function exportDocx() {
  window.open(reportApi.exportDocxUrl(props.sessionId), "_blank");
}

function exportPdf() {
  window.open(reportApi.exportPdfUrl(props.sessionId), "_blank");
}
</script>

<template>
  <div class="export-menu">
    <button class="export-btn docx" @click="exportDocx">导出 Word</button>
    <button class="export-btn pdf" @click="exportPdf">
      导出 PDF
    </button>
  </div>
</template>

<style scoped>
.export-menu {
  display: flex;
  gap: 8px;
}

.export-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  color: #fff;
}

.export-btn.docx {
  background: #27ae60;
}

.export-btn.docx:hover {
  background: #1e8449;
}

.export-btn.pdf {
  background: #e74c3c;
}

.export-btn.pdf:hover {
  background: #c0392b;
}
</style>
