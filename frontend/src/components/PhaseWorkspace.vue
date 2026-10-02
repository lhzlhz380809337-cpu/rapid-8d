<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from "vue";
import { useChatStore } from "../stores/chat";
import { useConfigStore } from "../stores/config";
import { uploadApi } from "../api/chat";
import MermaidRenderer from "./MermaidRenderer.vue";
import { t } from "../i18n";

const store = useChatStore();
const configStore = useConfigStore();

const outputEditText = ref("");
const outputEditing = ref(false);

const lang = computed(() => configStore.interfaceLang);
const currentContext = computed(() => store.stepContextNotes[store.currentStep] || "");
const currentDraft = computed(() => store.stepContextDraft[store.currentStep] || "");
const currentOutput = computed(() => store.stepOutputs[store.currentStep] || "");
const isConfirmed = computed(() => store.stepOutputConfirmed[store.currentStep] || false);

// ─── Expand + Font Size ────────────────────────────────────────────

const expandedSection = ref<string | null>(null);
const fontSizes = reactive<Record<string, number>>({ context: 13, output: 13 });

function initFontSizes() {
  try {
    const saved = localStorage.getItem('pw_font_sizes');
    if (saved) Object.assign(fontSizes, JSON.parse(saved));
  } catch {}
}
initFontSizes();

function changeFontSize(section: string, delta: number) {
  const v = (fontSizes[section] || 13) + delta;
  fontSizes[section] = Math.max(10, Math.min(24, v));
  localStorage.setItem('pw_font_sizes', JSON.stringify({...fontSizes}));
}

function toggleExpand(section: string) {
  expandedSection.value = expandedSection.value === section ? null : section;
}

function onEsc(e: KeyboardEvent) {
  if (e.key === 'Escape') expandedSection.value = null;
}

onMounted(() => document.addEventListener('keydown', onEsc));
onUnmounted(() => document.removeEventListener('keydown', onEsc));

// ─── Step watch ────────────────────────────────────────────────────

watch(() => store.currentStep, () => {
  if (!store.stepContextDraft[store.currentStep]) {
    store.stepContextDraft[store.currentStep] = currentContext.value;
  }
  outputEditText.value = currentOutput.value;
  outputEditing.value = false;
}, { immediate: true });

if (!store.stepContextDraft[store.currentStep]) {
  store.stepContextDraft[store.currentStep] = currentContext.value;
}
outputEditText.value = currentOutput.value;

// ─── Context ────────────────────────────────────────────────────────

let saveTimer: ReturnType<typeof setTimeout> | null = null;
let pendingSave: (() => void) | null = null;
const saveStatus = ref("");
function flushSave() {
  if (saveTimer) clearTimeout(saveTimer);
  const pending = pendingSave;
  pendingSave = null;
  pending?.();
}
onUnmounted(flushSave);
watch(() => [store.currentStep, store.projectId], flushSave, { flush: "sync" });

function onContextInput(e: Event) {
  const val = (e.target as HTMLTextAreaElement).value;
  store.stepContextDraft[store.currentStep] = val;
  const step = store.currentStep;
  const project = store.projectId;
  saveStatus.value = "待保存…";
  if (saveTimer) clearTimeout(saveTimer);
  pendingSave = () => {
    saveStatus.value = "正在保存…";
    store.saveContextNotes(val, step, project)
      .then(() => { saveStatus.value = "已保存"; })
      .catch((e) => { saveStatus.value = `保存失败：${e.message}。请保留当前页面并重试。`; });
  };
  saveTimer = setTimeout(flushSave, 800);
}

// ─── Image upload ───────────────────────────────────────────────────

const uploading = ref(false);

async function uploadImage(file: File) {
  if (!store.projectId || uploading.value) return;
  uploading.value = true;
  try {
    const result = await uploadApi.upload(store.projectId, file);
    const md = `![${result.filename}](${result.url})`;
    const draft = store.stepContextDraft[store.currentStep] || "";
    store.stepContextDraft[store.currentStep] = draft ? draft + "\n" + md : md;
    store.saveContextNotes(store.stepContextDraft[store.currentStep]);
  } catch (e: any) {
    alert("Image upload failed: " + (e.message || "Unknown error"));
  } finally {
    uploading.value = false;
  }
}

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files?.length) uploadImage(input.files[0]);
}

function onPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      e.preventDefault();
      const file = item.getAsFile();
      if (file) uploadImage(file);
      return;
    }
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  if (e.dataTransfer?.files.length) {
    uploadImage(e.dataTransfer.files[0]);
  }
}

// ─── Output ─────────────────────────────────────────────────────────

function enterOutputEdit() {
  outputEditText.value = currentOutput.value;
  outputEditing.value = true;
}

async function saveOutputEdit() {
  try {
    await store.confirmOutput(outputEditText.value);
    outputEditing.value = false;
  } catch (e: any) { saveStatus.value = `输出保存失败：${e.message}`; }
}

function cancelOutputEdit() {
  outputEditText.value = currentOutput.value;
  outputEditing.value = false;
}

function onOutputUpdate(content: string) {
  outputEditText.value = content;
}
</script>

<template>
  <div class="phase-workspace">
    <!-- Section 1: Context Editor -->
    <div :class="['section', 'context-section', { 'section-expanded': expandedSection === 'context' }]">
      <div class="section-header">
        <span class="header-title">{{ t('context', lang) }}</span>
        <span class="header-spacer"></span>
        <button class="hdr-btn" :title="t('fontSizeDown', lang)" @click="changeFontSize('context', -1)">A⁻</button>
        <button class="hdr-btn" :title="t('fontSizeUp', lang)" @click="changeFontSize('context', 1)">A⁺</button>
        <button class="hdr-btn" :title="expandedSection === 'context' ? t('collapsePanel', lang) : t('expandPanel', lang)" @click="toggleExpand('context')">{{ expandedSection === 'context' ? '✕' : '⛶' }}</button>
      </div>
      <div v-if="expandedSection !== 'context'" class="context-toolbar">
        <label class="tool-btn" :title="t('upload', lang)">
          📎
          <input type="file" accept="image/*" hidden @change="onFileSelect" />
        </label>
        <span class="tool-hint">{{ lang === 'en' ? 'Supports text and image upload' : '支持文字和图片上传' }}</span>
      </div>
      <textarea
        :value="currentDraft"
        class="context-textarea"
        :style="{ fontSize: fontSizes.context + 'px' }"
        :placeholder="t('contextPlaceholder', lang)"
        @input="onContextInput"
        @paste="onPaste"
        @dragover.prevent
        @drop="onDrop"
      ></textarea>
      <p v-if="saveStatus" role="status" style="padding: 4px 12px; font-size: 12px; color: #526777">{{ saveStatus }}</p>
      <div v-if="expandedSection !== 'context'" class="context-hint">
        {{ t('contextHint', lang) }}
      </div>
      <div v-if="uploading" class="upload-hint">{{ t('uploading', lang) }}</div>
    </div>

    <!-- Section 2: AI Output -->
    <div :class="['section', 'output-section', { 'section-expanded': expandedSection === 'output' }]" :style="{ fontSize: fontSizes.output + 'px' }">
      <div class="section-header output-header">
        <span class="header-title">{{ t('aiOutput', lang) }}</span>
        <div class="output-actions output-actions-inline">
          <button
            v-if="!currentOutput && !outputEditing"
            class="btn-generate"
            :disabled="store.generatingOutput"
            @click="store.generateOutput()"
          >
            {{ t('generate', lang) }}
          </button>
          <button v-if="!currentOutput && !outputEditing" class="btn-edit-out" @click="enterOutputEdit">手动填写</button>
          <template v-else-if="!outputEditing && !isConfirmed">
            <button class="btn-generate" :disabled="store.generatingOutput" @click="store.generateOutput()">
              {{ t('regenerate', lang) }}
            </button>
            <button class="btn-edit-out" @click="enterOutputEdit">{{ t('editOutput', lang) }}</button>
            <button class="btn-confirm" @click="store.confirmOutput(currentOutput)">{{ t('confirmOutput', lang) }}</button>
          </template>
          <template v-else-if="outputEditing">
            <button class="btn-confirm" @click="saveOutputEdit">{{ t('confirmEdit', lang) }}</button>
            <button class="btn-edit-out" @click="cancelOutputEdit">{{ t('cancel', lang) }}</button>
          </template>
          <template v-else>
            <button class="btn-edit-out" @click="enterOutputEdit">{{ t('unlockEdit', lang) }}</button>
            <button class="btn-generate" :disabled="store.generatingOutput" @click="store.generateOutput()">{{ t('regenerateAI', lang) }}</button>
          </template>
        </div>
        <span class="header-spacer"></span>
        <span v-if="isConfirmed" class="badge-confirmed">{{ t('confirmed', lang) }}</span>
        <button class="hdr-btn" :title="t('fontSizeDown', lang)" @click="changeFontSize('output', -1)">A⁻</button>
        <button class="hdr-btn" :title="t('fontSizeUp', lang)" @click="changeFontSize('output', 1)">A⁺</button>
        <button class="hdr-btn" :title="expandedSection === 'output' ? t('collapsePanel', lang) : t('expandPanel', lang)" @click="toggleExpand('output')">{{ expandedSection === 'output' ? '✕' : '⛶' }}</button>
      </div>

      <div v-if="!currentOutput && !outputEditing && !store.generatingOutput" class="output-empty">
        {{ t('outputEmpty', lang) }}
      </div>

      <div v-if="store.generatingOutput" class="output-generating">
        {{ t('outputGenerating', lang) }}
      </div>

      <div v-if="outputEditing" class="output-content">
        <textarea v-model="outputEditText" class="context-textarea" style="min-height: 180px; width: 100%" placeholder="输入本阶段报告内容，确认后保存"></textarea>
      </div>
      <div v-else-if="currentOutput && !store.generatingOutput" class="output-content">
        <MermaidRenderer
          :content="outputEditing ? outputEditText : currentOutput"
          :editable="!isConfirmed || outputEditing"
          :font-size="fontSizes.output"
          @update="onOutputUpdate"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.phase-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  padding: 16px;
  gap: 10px;
}

.section {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Expanded fullscreen */
.section.section-expanded {
  position: fixed;
  inset: 16px;
  z-index: 999;
  background: #fff;
  box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}

.section-header {
  background: #f8f8f8;
  padding: 7px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.header-title {
  flex-shrink: 0;
}

.header-spacer {
  flex: 1;
}

.hdr-btn {
  background: none;
  border: 1px solid transparent;
  color: #999;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  cursor: pointer;
  flex-shrink: 0;
  font-family: inherit;
  line-height: 1.4;
  transition: all 0.15s;
}

.hdr-btn:hover {
  background: #e8e8e8;
  color: #333;
  border-color: #ccc;
}

.section-body {
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.6;
}

/* Context + Output: equal height */
.context-section,
.output-section {
  flex: 1;
  min-height: 0;
}

.context-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.tool-btn {
  cursor: pointer;
  font-size: 15px;
  padding: 2px 6px;
  border-radius: 3px;
  transition: background 0.2s;
  background: none;
  border: none;
}

.tool-btn:hover {
  background: #e8e8e8;
}

.tool-hint {
  font-size: 11px;
  color: #bbb;
}

.context-textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.6;
  font-family: inherit;
  min-height: 0;
}

.upload-hint {
  font-size: 11px;
  color: #2980b9;
  padding: 4px 12px;
}

/* Output */
.output-empty, .output-generating {
  padding: 20px 12px;
  text-align: center;
  color: #999;
  font-size: 13px;
  flex: 1;
}

.output-content {
  padding: 10px 12px;
  flex: 1;
  overflow-y: auto;
}

.warnings-box {
  margin: 0 12px 8px;
  padding: 8px 12px;
  background: #fef9e7;
  border: 1px solid #f9e79f;
  border-radius: 4px;
  font-size: 12px;
}

.warnings-title {
  font-weight: 600;
  color: #b7950b;
  margin-bottom: 4px;
}

.warnings-box ul {
  margin: 0;
  padding-left: 18px;
  color: #7d6608;
}

.warnings-box li {
  margin: 2px 0;
}

/* Context hint */
.context-hint {
  padding: 6px 12px;
  font-size: 11px;
  color: #999;
  flex-shrink: 0;
  border-top: 1px solid #eee;
}

/* Buttons */
.output-actions {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid #eee;
  flex-shrink: 0;
}

.btn-generate, .btn-confirm, .btn-edit-out {
  padding: 6px 14px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-generate {
  background: #2980b9;
  color: #fff;
}

.btn-generate:hover:not(:disabled) {
  background: #1a5276;
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-confirm {
  background: #27ae60;
  color: #fff;
}

.btn-confirm:hover {
  background: #1e8449;
}

.btn-edit-out {
  background: #fff;
  color: #555;
  border: 1px solid #ddd;
}

.btn-edit-out:hover {
  background: #f0f0f0;
}

.badge-confirmed {
  background: #27ae60;
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.output-header {
  justify-content: flex-start;
  gap: 12px;
}

.output-actions-inline {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
  overflow-x: auto;
  padding: 0;
  border-top: 0;
  flex: 0 1 auto;
  scrollbar-width: none;
}

.output-actions-inline::-webkit-scrollbar {
  display: none;
}

.output-actions-inline .btn-generate,
.output-actions-inline .btn-confirm,
.output-actions-inline .btn-edit-out {
  padding: 4px 9px;
  font-size: 12px;
  line-height: 1.3;
  white-space: nowrap;
  flex-shrink: 0;
}

.output-header .badge-confirmed {
  margin-left: 8px;
  flex-shrink: 0;
}
@media(max-width:600px){
  .output-header{flex-wrap:wrap;gap:8px}
  .output-actions-inline{order:2;flex:1 0 100%;flex-wrap:wrap;overflow:visible}
  .output-actions-inline button{min-height:32px}
}
</style>
