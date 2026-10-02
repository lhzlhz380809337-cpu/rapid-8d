<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { reportApi } from "../api/report";
import { useConfigStore } from "../stores/config";
import { t } from "../i18n";

const route = useRoute();
const router = useRouter();
const configStore = useConfigStore();
const lang = computed(() => configStore.interfaceLang);
const projectId = route.params.id as string;

const defaultRequirements = ref("");
const customRequirements = ref("");
const generating = ref(false);
const confirming = ref(false);
const previewHtml = ref("");
const reportContent = ref("");
const errorMsg = ref("");
const showFinalPrompt = ref(false);

const builtPrompt = computed(() => {
  const def = defaultRequirements.value;
  const cust = customRequirements.value.trim();
  return cust ? def + "\n" + cust : def;
});

onMounted(async () => {
  try {
    const resp = await reportApi.getRequirements(projectId);
    defaultRequirements.value = resp.default_requirements;
    customRequirements.value = resp.custom_requirements;
  } catch (e: any) {
    errorMsg.value = "加载报告要求失败：" + (e.message || "未知错误");
  }
});

async function saveRequirements() {
  try {
    await reportApi.saveRequirements(projectId, customRequirements.value);
  } catch {
    // silently fail on auto-save
  }
}

async function preview() {
  if (generating.value) return;
  generating.value = true;
  errorMsg.value = "";
  previewHtml.value = "";

  try {
    await saveRequirements();
    const resp = await reportApi.generateWithLLM(projectId, customRequirements.value);
    previewHtml.value = resp.html;
    reportContent.value = resp.report_content;
  } catch (e: any) {
    errorMsg.value = "生成失败：" + (e.message || "网络错误");
  } finally {
    generating.value = false;
  }
}

async function confirm() {
  if (confirming.value || !previewHtml.value) return;
  confirming.value = true;
  errorMsg.value = "";

  try {
    await saveRequirements();
    const resp = await reportApi.saveReport(projectId, previewHtml.value);

    const blob = new Blob([previewHtml.value], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `8D_${resp.title}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e: any) {
    errorMsg.value = "确认失败：" + (e.message || "网络错误");
  } finally {
    confirming.value = false;
  }
}

function goBack() {
  router.push(`/chat/${projectId}`);
}
</script>

<template>
  <div class="report-generator">
    <!-- Header -->
    <div class="toolbar">
      <button class="btn-back" @click="goBack">{{ t('backToEdit', lang) }}</button>
      <h2>{{ t('reportFullTitle', lang) }}</h2>
      <span class="toolbar-hint">{{ t('aiGenerateMode', lang) }}</span>
    </div>

    <div class="generator-body">
      <!-- Left: Prompt editor -->
      <div class="prompt-panel">
        <div class="panel-title">{{ t('reportPromptSection', lang) }}</div>

        <!-- Default requirements (read-only) -->
        <div class="requirements-section">
          <div class="section-label">{{ t('systemDefaults', lang) }}</div>
          <pre class="requirements-readonly">{{ defaultRequirements || t('loading', lang) }}</pre>
        </div>

        <!-- Custom requirements (editable) -->
        <div class="requirements-section">
          <div class="section-label">{{ t('customReqs', lang) }}</div>
          <textarea
            v-model="customRequirements"
            class="requirements-editor"
            :placeholder="t('customReqsPlaceholder', lang)"
            rows="8"
          ></textarea>
        </div>

        <!-- Collapsible final prompt preview -->
        <div class="prompt-preview-toggle" @click="showFinalPrompt = !showFinalPrompt">
          {{ showFinalPrompt ? '▾' : '▸' }} {{ t('finalPromptPreview', lang) }}
        </div>
        <pre v-if="showFinalPrompt" class="final-prompt">{{ builtPrompt }}</pre>

        <!-- Actions -->
        <div class="prompt-actions">
          <button
            class="btn-preview"
            :disabled="generating"
            @click="preview"
          >
            {{ generating ? "生成中..." : "生成报告并预览" }}
          </button>
          <button
            class="btn-confirm"
            :disabled="confirming || !previewHtml"
            @click="confirm"
          >
            {{ confirming ? "保存中..." : "确认并保存" }}
          </button>
          <button class="btn-cancel" @click="goBack">返回</button>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>

      <!-- Right: Preview area -->
      <div class="preview-panel">
        <div class="panel-title">{{ lang === 'en' ? 'Report Preview' : '报告预览' }}</div>
        <div v-if="!previewHtml && !generating" class="preview-empty">
          {{ t('previewEmpty', lang) }}
        </div>
        <div v-if="generating" class="preview-loading">
          {{ t('aiGenerating', lang) }}
        </div>
        <iframe
          v-if="previewHtml"
          :srcdoc="previewHtml"
          class="preview-iframe"
          sandbox=""
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-generator {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.toolbar h2 {
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}

.toolbar-hint {
  font-size: 11px;
  color: #f0ad4e;
  background: #fef9e7;
  padding: 2px 10px;
  border-radius: 10px;
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

.generator-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

/* Left: Prompt editor */
.prompt-panel {
  width: 420px;
  flex-shrink: 0;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 12px;
  overflow-y: auto;
  background: #fafafa;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.requirements-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
}

.requirements-readonly {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 12.5px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: #555;
  margin: 0;
}

.requirements-editor {
  border: 1px solid #ddd;
  border-left: 3px solid #2980b9;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 12.5px;
  line-height: 1.7;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
}

.requirements-editor:focus {
  border-color: #2980b9;
}

.prompt-preview-toggle {
  font-size: 12px;
  color: #2980b9;
  cursor: pointer;
  user-select: none;
}

.prompt-preview-toggle:hover {
  text-decoration: underline;
}

.final-prompt {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 11px;
  line-height: 1.5;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
  color: #666;
  margin: 0;
}

/* Actions */
.prompt-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-preview,
.btn-confirm,
.btn-cancel {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-preview {
  background: #2980b9;
  color: #fff;
  flex: 1;
}

.btn-preview:hover:not(:disabled) {
  background: #1a5276;
}

.btn-preview:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-confirm {
  background: #27ae60;
  color: #fff;
}

.btn-confirm:hover:not(:disabled) {
  background: #1e8449;
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-cancel {
  background: #fff;
  color: #555;
  border: 1px solid #ddd;
}

.btn-cancel:hover {
  background: #f0f0f0;
}

.error-msg {
  font-size: 12px;
  color: #e74c3c;
  padding: 8px;
  background: #fdf0ef;
  border-radius: 4px;
}

/* Right: Preview */
.preview-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  min-width: 0;
}

.preview-empty,
.preview-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 14px;
}

.preview-iframe {
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  width: 100%;
}
</style>
<style scoped>
@media(max-width:768px){.generator-body{flex-direction:column;overflow:auto}.prompt-panel{width:100%;max-height:none;flex-shrink:0}.preview-panel{min-height:500px}.toolbar{flex-wrap:wrap;padding:12px}.toolbar-hint{display:none}}
</style>
