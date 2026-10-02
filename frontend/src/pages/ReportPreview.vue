<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useChatStore } from "../stores/chat";
import { reportApi, type GenerateReportResponse } from "../api/report";

const route = useRoute();
const router = useRouter();
const store = useChatStore();
const projectId = route.params.id as string;
const previewUrl = ref("");

onMounted(() => {
  previewUrl.value = reportApi.previewUrl(projectId);
});

function goBack() {
  if (store.projectId) {
    router.push(`/chat/${store.projectId}`);
  } else {
    router.push("/");
  }
}

function exportDocx() {
  window.open(reportApi.exportDocxUrl(projectId), "_blank");
}

function exportPdf() {
  window.open(reportApi.exportPdfUrl(projectId), "_blank");
}
</script>

<template>
  <div class="report-view">
    <div class="toolbar">
      <button class="btn-back" @click="goBack">← 返回编辑</button>
      <h2>8D 报告预览</h2>
      <div class="toolbar-actions">
        <button class="btn-export" @click="exportDocx">导出 Word</button>
        <button class="btn-export btn-pdf" @click="exportPdf">导出 PDF</button>
      </div>
    </div>
    <iframe sandbox="" v-if="previewUrl" :src="previewUrl" class="report-iframe" />
    <div v-else class="empty">加载中...</div>
  </div>
</template>

<style scoped>
.report-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.toolbar h2 {
  font-size: 16px;
}

.btn-back {
  background: none;
  border: 1px solid #ddd;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  color: #555;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #f0f0f0;
  color: #2980b9;
  border-color: #2980b9;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.btn-export {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  background: #27ae60;
  color: #fff;
}

.btn-export:hover {
  background: #1e8449;
}

.btn-pdf {
  background: #e74c3c;
}

.btn-pdf:hover {
  background: #c0392b;
}

.report-iframe {
  flex: 1;
  border: none;
  width: 100%;
}

.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}
</style>
