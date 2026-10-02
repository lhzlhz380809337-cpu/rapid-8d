<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useConfigStore } from "../stores/config";
import { projectApi, type ContextVersion } from "../api/session";
import { t } from "../i18n";

const props = defineProps<{ projectId: string; currentDate: string }>();
const emit = defineEmits<{ select: [date: string] }>();

const configStore = useConfigStore();
const lang = computed(() => configStore.interfaceLang);

const versions = ref<ContextVersion[]>([]);
const loading = ref(false);

onMounted(async () => {
  if (!props.projectId) return;
  loading.value = true;
  try {
    versions.value = await projectApi.listContexts(props.projectId);
  } finally {
    loading.value = false;
  }
});

function selectVersion(date: string) {
  emit("select", date);
}
</script>

<template>
  <div class="version-history">
    <h3 class="vh-title">{{ t('snapshotHistory', lang) }}</h3>
    <div v-if="loading" class="vh-empty">{{ t('loading', lang) }}</div>
    <div v-else-if="versions.length === 0" class="vh-empty">{{ t('noSnapshotHistory', lang) }}</div>
    <div v-else class="vh-list">
      <div
        v-for="v in versions"
        :key="v.date"
        :class="['vh-item', { active: v.date === currentDate }]"
        @click="selectVersion(v.date)"
      >
        <span class="vh-date">{{ v.date }}</span>
        <span class="vh-size">{{ (v.size / 1024).toFixed(0) }} KB</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.version-history {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.vh-title {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}

.vh-empty {
  font-size: 12px;
  color: #bbb;
}

.vh-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.vh-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.vh-item:hover {
  background: #f0f6fb;
}

.vh-item.active {
  background: #eaf2f8;
  font-weight: 600;
}

.vh-date {
  color: #555;
}

.vh-size {
  color: #aaa;
}
</style>
