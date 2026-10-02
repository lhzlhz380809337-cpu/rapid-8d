<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from "vue";
import { useChatStore } from "../stores/chat";
import { useConfigStore } from "../stores/config";
import { uploadApi } from "../api/chat";
import { t, getFocus } from "../i18n";

const store = useChatStore();
const configStore = useConfigStore();
const lang = computed(() => configStore.interfaceLang);
const input = ref("");
const chatEl = ref<HTMLElement | null>(null);
const uploading = ref(false);
const uploadError = ref("");

const showFocus = ref(false);
const currentFocus = computed(() => getFocus(store.currentStep));

function toggleFocus() {
  showFocus.value = !showFocus.value;
}
function closeFocus() {
  showFocus.value = false;
}

// ─── Expand + Font Size ────────────────────────────────────────────

const expanded = ref(false);
const chatFontSize = ref(13);

function initFontSize() {
  try {
    const saved = localStorage.getItem('chat_font_size');
    if (saved) chatFontSize.value = parseInt(saved) || 13;
  } catch {}
}
initFontSize();

function changeChatFontSize(delta: number) {
  chatFontSize.value = Math.max(10, Math.min(24, chatFontSize.value + delta));
  localStorage.setItem('chat_font_size', String(chatFontSize.value));
}

function toggleExpand() {
  expanded.value = !expanded.value;
}

function onEsc(e: KeyboardEvent) {
  if (e.key === 'Escape') expanded.value = false;
}

onMounted(() => document.addEventListener('keydown', onEsc));
onUnmounted(() => document.removeEventListener('keydown', onEsc));

// ─── Chat ──────────────────────────────────────────────────────────

const filteredMessages = computed(() => {
  return store.messages.filter(m => m.step === store.currentStep);
});

function scrollToBottom() {
  nextTick(() => {
    if (chatEl.value) {
      chatEl.value.scrollTop = chatEl.value.scrollHeight;
    }
  });
}

watch(() => store.messages.length, scrollToBottom);
watch(() => store.currentStep, scrollToBottom);

function send() {
  const text = input.value.trim();
  if (!text || store.sending) return;
  store.sendMessage(text);
  input.value = "";
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

async function uploadFile(file: File) {
  if (!store.projectId || uploading.value) return;
  uploading.value = true;
  try {
    const result: any = await uploadApi.upload(store.projectId, file);
    if (result.is_image) {
      input.value = input.value + ` ![${result.original_name || result.filename}](${result.url})`;
    } else {
      const label = t('docParsed', lang.value);
      if (result.parse_status === 'ok' && result.text) {
        input.value = input.value + `\n[${label} ${result.original_name || result.filename}]\n${result.text}\n`;
      } else {
        input.value = input.value + `\n[${t('docEmpty', lang.value)}: ${result.original_name || result.filename}]\n`;
      }
    }
  } catch (e: any) {
    uploadError.value = e.message || t('docUnsupported', lang.value);
    setTimeout(() => { uploadError.value = ''; }, 4000);
  } finally {
    uploading.value = false;
  }
}

function onFileSelect(e: Event) {
  const inp = e.target as HTMLInputElement;
  if (inp.files?.length) uploadFile(inp.files[0]);
}

function onPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      e.preventDefault();
      const file = item.getAsFile();
      if (file) uploadFile(file);
      return;
    }
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  if (e.dataTransfer?.files.length) {
    uploadFile(e.dataTransfer.files[0]);
  }
}

function addToContext(content: string) {
  const step = store.currentStep;
  const existing = store.stepContextDraft[step] || "";
  const merged = existing ? existing + "\n\n" + content : content;
  store.stepContextDraft[step] = merged;
  store.saveContextNotes(merged);
}
</script>

<template>
  <div :class="['phase-chat-panel', { 'chat-expanded': expanded }]">
    <div class="chat-header">
      <span>{{ t('aiChat', lang) }}</span>
      <span class="chat-step-badge">{{ store.currentStep }}</span>
      <button
        class="hdr-btn focus-btn"
        :title="t('focus', lang)"
        @click="toggleFocus"
      >ℹ</button>
      <span class="header-spacer"></span>
      <button class="hdr-btn" :title="t('fontSizeDown', lang)" @click="changeChatFontSize(-1)">A⁻</button>
      <button class="hdr-btn" :title="t('fontSizeUp', lang)" @click="changeChatFontSize(1)">A⁺</button>
      <button class="hdr-btn" :title="expanded ? t('collapsePanel', lang) : t('expandPanel', lang)" @click="toggleExpand">{{ expanded ? '✕' : '⛶' }}</button>
    </div>

    <!-- Focus popover -->
    <div v-if="showFocus" class="focus-popover">
      <div class="focus-popover-header">
        <span>{{ t('focus', lang) }} — {{ store.currentStep }}</span>
        <button class="hdr-btn" @click="closeFocus">✕</button>
      </div>
      <div class="focus-popover-body">{{ currentFocus }}</div>
    </div>

    <!-- Cross-check warnings -->
    <div v-if="store.crossCheckWarnings.length > 0" class="chat-warnings">
      <div class="chat-warnings-title">{{ t('crossCheckWarning', lang) }}</div>
      <ul>
        <li v-for="(w, i) in store.crossCheckWarnings" :key="i">{{ w }}</li>
      </ul>
    </div>

    <!-- Messages -->
    <div ref="chatEl" class="chat-messages" :style="{ fontSize: chatFontSize + 'px' }">
      <div v-if="filteredMessages.length === 0" class="chat-empty">
        {{ t('chatEmptyHint', lang).replace('{step}', store.currentStep) }}
      </div>

      <div v-for="(msg, i) in filteredMessages" :key="i" class="chat-msg-wrapper">
        <div
          :class="[
            'chat-msg-bubble',
            msg.role === 'user' ? 'msg-user' : msg.role === 'system' ? 'msg-system' : 'msg-assistant',
          ]"
        >
          <div
            :class="['msg-content', { 'findings-content': msg.role === 'system' && msg.content.includes('上下文检查结果') }]"
            style="white-space: pre-wrap"
            v-text="msg.content"
          ></div>
          <button
            v-if="msg.role === 'assistant'"
            class="btn-add-context"
            :title="t('addToContext', lang)"
            @click="addToContext(msg.content)"
          >
            {{ t('addToContext', lang) }}
          </button>
        </div>
      </div>

      <div v-if="store.sending" class="chat-msg-bubble msg-assistant typing">{{ t('typing', lang) }}</div>
    </div>

    <!-- Input -->
    <div v-if="!expanded" class="chat-input-area">
      <div class="input-row">
        <label class="upload-btn" :title="t('upload', lang)">
          📎
          <input type="file" accept="image/*,.txt,.md,.log,.csv,.xml,.json,.pdf,.docx,.doc,.xlsx,.xls" hidden @change="onFileSelect" />
        </label>
        <textarea
          v-model="input"
          class="chat-input"
          :placeholder="t('chatPlaceholder', lang)"
          :disabled="store.sending"
          @keydown="onKeydown"
          @paste="onPaste"
          @dragover.prevent
          @drop="onDrop"
          rows="2"
        ></textarea>
        <button
          class="btn-send"
          :disabled="store.sending || !input.trim()"
          @click="send"
        >
          {{ t('send', lang) }}
        </button>
      </div>
      <div v-if="uploadError" class="chat-upload-error">{{ uploadError }}</div>
    </div>
  </div>
</template>

<style scoped>
.phase-chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-left: 1px solid #e0e0e0;
  background: #fafafa;
  position: relative;
}

/* Expanded */
.phase-chat-panel.chat-expanded {
  position: fixed;
  inset: 16px;
  z-index: 999;
  background: #fafafa;
  box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  font-size: 14px;
  font-weight: 600;
}

.chat-step-badge {
  background: #2980b9;
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
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

.chat-warnings {
  margin: 8px 12px;
  padding: 8px 12px;
  background: #fef9e7;
  border: 1px solid #f9e79f;
  border-radius: 4px;
  font-size: 12px;
}

.chat-warnings-title {
  font-weight: 600;
  color: #b7950b;
  margin-bottom: 4px;
}

.chat-warnings ul {
  margin: 0;
  padding-left: 18px;
  color: #7d6608;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.chat-empty {
  text-align: center;
  color: #bbb;
  margin-top: 60px;
  font-size: 13px;
  line-height: 1.6;
}

.chat-msg-wrapper {
  margin-bottom: 8px;
}

.chat-msg-bubble {
  max-width: 90%;
  padding: 8px 12px;
  border-radius: 8px;
  line-height: 1.6;
  position: relative;
}

.msg-user {
  margin-left: auto;
  background: #2980b9;
  color: #fff;
}

.msg-assistant {
  background: #fff;
  border: 1px solid #e0e0e0;
}

.msg-system {
  margin-left: auto;
  margin-right: auto;
  background: #fef9e7;
  border: 1px solid #f9e79f;
}

.msg-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.findings-content {
  background: #fffbeb;
  border-left: 3px solid #f0ad4e;
  padding: 8px 12px;
  border-radius: 4px;
  margin: -4px -8px;
  font-size: 12.5px;
  line-height: 1.8;
}

.findings-content strong {
  color: #333;
}

.btn-add-context {
  display: block;
  margin-top: 6px;
  padding: 2px 8px;
  border: 1px solid #ddd;
  border-radius: 3px;
  background: #fff;
  font-size: 11px;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-context:hover {
  color: #2980b9;
  border-color: #2980b9;
}

.typing {
  color: #999;
  font-style: italic;
}

/* Input */
.chat-input-area {
  padding: 10px 12px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
}

.input-row {
  display: flex;
  gap: 6px;
  align-items: flex-end;
}

.upload-btn {
  cursor: pointer;
  font-size: 18px;
  padding: 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

.upload-btn:hover {
  background: #f0f0f0;
}

.chat-upload-error {
  font-size: 11px;
  color: #e74c3c;
  text-align: center;
  margin-top: 4px;
  padding: 4px 8px;
  background: #fdf0ef;
  border-radius: 4px;
}

.chat-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  resize: none;
  font-family: inherit;
  line-height: 1.4;
}

.chat-input:focus {
  border-color: #2980b9;
}

.btn-send {
  padding: 8px 16px;
  background: #2980b9;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Focus popover */
.focus-popover {
  position: absolute;
  top: 44px;
  left: 16px;
  right: 16px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  z-index: 100;
  max-height: 60vh;
  display: flex;
  flex-direction: column;
}

.focus-popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #eee;
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.focus-popover-body {
  padding: 14px;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-y: auto;
}

.focus-btn {
  font-weight: 700;
  font-size: 13px;
  color: #2980b9;
}
</style>
