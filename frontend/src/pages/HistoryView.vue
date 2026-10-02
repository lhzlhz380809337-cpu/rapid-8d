<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useChatStore } from "../stores/chat";
import { useConfigStore } from "../stores/config";
import { projectApi, type ProjectSummary } from "../api/session";
import { t } from "../i18n";

const router = useRouter();
const store = useChatStore();
const configStore = useConfigStore();
const lang = computed(() => configStore.interfaceLang);

function goBack() {
  if (store.projectId) {
    router.push(`/chat/${store.projectId}`);
  } else {
    router.push("/");
  }
}
const projects = ref<ProjectSummary[]>([]);
const loading = ref(true);
const errorMsg = ref("");

onMounted(async () => {
  try {
    projects.value = await projectApi.list();
  } catch (e: any) {
    errorMsg.value = e.message || t('errorLoadProjects', lang.value);
  } finally {
    loading.value = false;
  }
});

function openProject(id: string) {
  router.push(`/chat/${id}`);
}

async function deleteProject(id: string) {
  if (!confirm(t('deleteConfirm', lang.value))) return;
  await projectApi.delete(id);
  projects.value = projects.value.filter((p) => p.project_id !== id);
}
</script>

<template>
  <div class="history-view">
    <div class="history-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">{{ t('historyBack', lang) }}</button>
        <h2>{{ t('historyProjects', lang) }}</h2>
      </div>
      <button class="btn-new" @click="router.push('/')">+ {{ t('newProject', lang) }}</button>
    </div>

    <div v-if="loading" class="empty">{{ t('loading', lang) }}</div>

    <div v-else-if="errorMsg" class="empty error">
      <p>{{ errorMsg }}</p>
      <p><button class="btn-retry" @click="router.go(0)">{{ lang === 'en' ? 'Retry' : '重试' }}</button></p>
    </div>

    <div v-else-if="projects.length === 0" class="empty">
      <p>{{ t('noHistory', lang) }}</p>
      <p><router-link to="/">{{ t('noHistoryHint', lang) }}</router-link></p>
    </div>

    <div v-else class="project-list">
      <div
        v-for="p in projects"
        :key="p.project_id"
        class="project-card"
        @click="openProject(p.project_id)"
      >
        <div class="project-info">
          <h3>{{ p.title }}</h3>
          <div class="project-meta">
            <span>{{ p.current_step }}</span>
            <span>{{ t('stepsCompleted', lang).replace('{done}', String(p.steps_completed)).replace('{total}', String(p.total_steps)) }}</span>
            <span>{{ t('latest', lang) }} {{ p.date }}</span>
            <span>{{ t('snapshotsCount', lang).replace('{n}', String(p.context_versions)) }}</span>
            <span v-if="p.report_versions > 0">{{ t('reportsCount', lang).replace('{n}', String(p.report_versions)) }}</span>
          </div>
        </div>
        <button class="btn-delete" @click.stop="deleteProject(p.project_id)">
          {{ t('deleteProject', lang) }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.history-header h2 {
  font-size: 18px;
  margin: 0;
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

.btn-new {
  padding: 8px 16px;
  background: #2980b9;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.project-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.project-info h3 {
  font-size: 15px;
  margin-bottom: 4px;
}

.project-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #888;
  flex-wrap: wrap;
}

.btn-delete {
  padding: 6px 12px;
  background: none;
  border: 1px solid #e74c3c;
  color: #e74c3c;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  flex-shrink: 0;
}

.btn-delete:hover {
  background: #e74c3c;
  color: #fff;
}

.empty {
  text-align: center;
  color: #999;
  padding: 60px 0;
  line-height: 2;
}

.empty.error {
  color: #e74c3c;
}

.btn-retry {
  padding: 6px 16px;
  background: #2980b9;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  margin-top: 8px;
}
</style>
