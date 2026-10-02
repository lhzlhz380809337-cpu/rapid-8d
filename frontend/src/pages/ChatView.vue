<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useChatStore } from "../stores/chat";
import { useConfigStore } from "../stores/config";
import { reportApi } from "../api/report";
import { t } from "../i18n";
import StepProgress from "../components/StepProgress.vue";
import VersionHistory from "../components/VersionHistory.vue";
import PhaseWorkspace from "../components/PhaseWorkspace.vue";
import PhaseChatPanel from "../components/PhaseChatPanel.vue";

const route = useRoute();
const router = useRouter();
const store = useChatStore();
const configStore = useConfigStore();
const lang = computed(() => configStore.interfaceLang);

const sessionTitle = ref("Untitled 8D Report");
const generating = ref(false);
const editingTitle = ref(false);
const titleInput = ref<HTMLInputElement | null>(null);
const sidebarOpen = ref(false);
const mobileTab = ref<'workspace' | 'chat'>('workspace');

watch(() => route.params.id, async () => {
  const id = route.params.id as string | undefined;
  if (id) {
    const detail = await store.loadProject(id);
    sessionTitle.value = detail.title;
  }
}, { immediate: true });

function startEditTitle() {
  editingTitle.value = true;
  setTimeout(() => titleInput.value?.focus(), 50);
}

async function saveTitle() {
  editingTitle.value = false;
  const newTitle = sessionTitle.value.trim() || "未命名 8D 报告";
  sessionTitle.value = newTitle;
  if (store.projectId) {
    await store.updateTitle(newTitle);
  }
}

function onTitleKeydown(e: KeyboardEvent) {
  if (e.key === "Enter") saveTitle();
  if (e.key === "Escape") { editingTitle.value = false; sessionTitle.value = store.projectId ? sessionTitle.value : "未命名 8D 报告"; }
}

async function onStepSelect(step: string) {
  await store.switchStep(step);
}

async function loadHistoryVersion(date: string) {
  if (!store.projectId) return;
  const ctx = await store.loadProject(store.projectId, date);
  sessionTitle.value = ctx.title;
}

async function generateReport() {
  if (!store.projectId || generating.value) return;
  generating.value = true;
  try {
    const resp = await reportApi.generate(store.projectId);

    if (resp.warnings && resp.warnings.length > 0) {
      const warningText = resp.warnings
        .map((w) => `  - [${w.step}] ${w.type}: ${w.match}`)
        .join("\n");
      const proceed = confirm(
        `报告已生成，但发现以下内容需要核实：\n\n${warningText}\n\n是否继续？`
      );
      if (!proceed) return;
    }

    window.open(reportApi.exportDocxUrl(store.projectId), "_blank");
    router.push(`/report/${store.projectId}`);
  } finally {
    generating.value = false;
  }
}

function openReportGenerator() {
  if (store.projectId) {
    router.push(`/report-generator/${store.projectId}`);
  }
}

function viewReport() {
  if (store.projectId) {
    router.push(`/report/${store.projectId}`);
  }
}
</script>

<template>
  <div class="chat-view">
    <!-- Mobile overlay -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false" />

    <!-- Left Sidebar -->
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <StepProgress
        :current-step="store.currentStep"
        :output-confirmed="store.stepOutputConfirmed"
        :step-outputs="store.stepOutputs"
        @select="onStepSelect"
      />
      <button
        v-if="store.projectId"
        class="btn-preview"
        @click="viewReport"
      >
        {{ t('generateAndPreview', lang) }}
      </button>
      <button
        v-if="store.projectId"
        class="btn-ai-report"
        @click="openReportGenerator"
      >
        {{ t('reportFullTitle', lang) }}
      </button>
      <VersionHistory
        v-if="store.projectId"
        :project-id="store.projectId"
        :current-date="store.contextDate"
        @select="loadHistoryVersion"
      />
      <div class="sidebar-copyright">
        <p><strong>8D Agent</strong> V0.3 试用版</p>
        <p>© 2026 Liu Hongzhi</p>
        <p class="copyright-warn">{{ t('aboutTestVersion', lang) }}</p>
        <p><a href="mailto:lhzcj1992@126.com">lhzcj1992@126.com</a></p>
      </div>
    </aside>

    <!-- Mobile top bar -->
    <div class="mobile-topbar">
      <button class="menu-toggle" @click="sidebarOpen = !sidebarOpen" aria-label="菜单">
        <span /><span /><span />
      </button>
      <div class="mobile-title-area">
        <input
          v-if="editingTitle"
          ref="titleInput"
          v-model="sessionTitle"
          class="mobile-title-input"
          @blur="saveTitle"
          @keydown="onTitleKeydown"
        />
        <template v-else>
          <span class="mobile-title-text" @click="startEditTitle">{{ sessionTitle || 'Untitled 8D Report' }}</span>
          <button class="mobile-title-edit" @click="startEditTitle">✏️</button>
        </template>
      </div>
      <div class="mobile-tab-bar">
        <button :class="['mobile-tab', { active: mobileTab === 'workspace' }]" @click="mobileTab = 'workspace'">工作区</button>
        <button :class="['mobile-tab', { active: mobileTab === 'chat' }]" @click="mobileTab = 'chat'">AI对话</button>
      </div>
    </div>

    <!-- Center: Phase Workspace -->
    <section class="phase-workspace-panel" :class="{ 'mobile-active': mobileTab === 'workspace' }">
      <div v-if="!store.projectId" class="welcome-state">
        <p>{{ t('welcomeTitle', lang) }}</p>
        <p class="welcome-hint">{{ t('welcomeHint', lang) }}</p>
      </div>
      <template v-else>
        <div class="panel-header">
          <div class="title-row">
            <input
              v-if="editingTitle"
              ref="titleInput"
              v-model="sessionTitle"
              class="title-input"
              @blur="saveTitle"
              @keydown="onTitleKeydown"
            />
            <h2 v-else>{{ sessionTitle }}</h2>
            <button class="btn-edit-title" title="修改名称" @click="startEditTitle">✏️</button>
          </div>
          <span class="step-badge">{{ store.currentStep }}</span>
        </div>
        <PhaseWorkspace />
      </template>
    </section>

    <!-- Right: Chat Panel -->
    <section class="phase-chat-panel-wrapper" :class="{ 'mobile-active': mobileTab === 'chat' }">
      <PhaseChatPanel />
    </section>

  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  height: 100%;
}

/* Sidebar */
.sidebar {
  width: 240px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
  overflow-y: auto;
}

.sidebar-copyright {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #e8e8e8;
  font-size: 11px;
  color: #aaa;
  line-height: 1.6;
  text-align: center;
}

.sidebar-copyright a {
  color: #2980b9;
  text-decoration: none;
}

.sidebar-copyright .copyright-warn {
  color: #e67e22;
}

.btn-report,
.btn-ai-report,
.btn-preview {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  color: #fff;
}

.btn-report {
  background: #27ae60;
}

.btn-report:hover:not(:disabled) {
  background: #1e8449;
}

.btn-report:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ai-report {
  background: #f0ad4e;
}

.btn-ai-report:hover {
  background: #ec971f;
}

.btn-preview {
  background: #2980b9;
}

.btn-preview:hover {
  background: #1a5276;
}

/* Phase Workspace Panel */
.phase-workspace-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fff;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-badge {
  background: #2980b9;
  color: #fff;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.title-input {
  font-size: 16px;
  font-weight: 600;
  border: 1px solid #2980b9;
  border-radius: 4px;
  padding: 4px 8px;
  outline: none;
  font-family: inherit;
  width: 100%;
  max-width: 300px;
}

.btn-edit-title {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 4px;
  border-radius: 3px;
  flex-shrink: 0;
  opacity: 0.4;
  transition: opacity 0.2s;
}

.btn-edit-title:hover {
  opacity: 1;
  background: #f0f0f0;
}

.welcome-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 16px;
}

.welcome-hint {
  font-size: 13px;
  color: #bbb;
  margin-top: 10px;
}

/* Chat Panel */
.phase-chat-panel-wrapper {
  flex: 1;
  min-width: 0;
}

/* ─── Mobile: top bar & tab bar ─── */
.mobile-topbar { display: none; }
.mobile-tab-bar { display: none; }
.sidebar-overlay { display: none; }

@media (max-width: 768px) {
  .chat-view { flex-direction: column; }
  .sidebar-overlay { display: block; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 90; }
  .sidebar {
    position: fixed; top: 0; left: 0; height: 100vh; z-index: 100;
    transform: translateX(-100%); transition: transform 0.25s ease;
    box-shadow: 4px 0 20px rgba(0,0,0,0.15);
  }
  .sidebar.open { transform: translateX(0); }

  .mobile-topbar {
    display: flex; align-items: center; gap: 0;
    height: 44px; padding: 0 8px; background: #1a5276; color: #fff;
    flex-shrink: 0;
  }
  .mobile-topbar .menu-toggle {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    width: 32px; height: 32px; border: none; background: none; cursor: pointer;
    padding: 5px; border-radius: 4px; flex-shrink: 0;
  }
  .mobile-topbar .menu-toggle:hover { background: rgba(255,255,255,0.15); }
  .mobile-topbar .menu-toggle span {
    display: block; width: 100%; height: 2px; background: #fff; margin: 2px 0; border-radius: 2px;
  }
  .mobile-title-area { display: flex; align-items: center; flex: 1; min-width: 0; gap: 4px; }
  .mobile-title-text { font-size: 13px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
  .mobile-title-input { font-size: 13px; font-weight: 600; border: 1px solid rgba(255,255,255,0.4); border-radius: 4px; padding: 2px 6px; background: rgba(255,255,255,0.15); color: #fff; outline: none; width: 100%; min-width: 0; font-family: inherit; }
  .mobile-title-edit { background: none; border: none; color: rgba(255,255,255,0.6); cursor: pointer; font-size: 12px; padding: 2px; flex-shrink: 0; }
  .mobile-tab-bar { display: flex; flex: 1; justify-content: center; }
  .mobile-tab {
    padding: 6px 12px; border: none; background: rgba(255,255,255,0.1);
    font-size: 12px; font-weight: 500; cursor: pointer; font-family: inherit;
    color: rgba(255,255,255,0.7); border-radius: 6px; transition: all 0.15s;
    white-space: nowrap;
  }
  .mobile-tab.active { background: rgba(255,255,255,0.25); color: #fff; font-weight: 600; }
  .mobile-tab + .mobile-tab { margin-left: 4px; }

  .phase-workspace-panel,
  .phase-chat-panel-wrapper {
    display: none;
  }
  .phase-workspace-panel.mobile-active,
  .phase-chat-panel-wrapper.mobile-active {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .panel-header { display: none; }
}
</style>

