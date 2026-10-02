<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useChatStore } from "./stores/chat";
import { useConfigStore } from "./stores/config";
import { t } from "./i18n";
const router = useRouter();
const store = useChatStore();
const configStore = useConfigStore();
import { currentUser } from "./auth";
import { api } from "./api/client";
async function logout() {
  await api.post("/auth/logout", {});
  window.location.hash = "/login";
  window.location.reload();
}

watch(currentUser, async (user) => {
  if (!user) return;
  await configStore.load();
  if (configStore.config?.app?.interface_lang) {
    localStorage.setItem("interface_lang", configStore.config.app.interface_lang);
  }
}, { immediate: true });

const lang = computed(() => configStore.interfaceLang);

const showNewDialog = ref(false);
const newReportName = ref("");

function openNewDialog() {
  newReportName.value = "Untitled 8D Report";
  showNewDialog.value = true;
}

async function createNewReport() {
  showNewDialog.value = false;
  const p = await store.newProject(newReportName.value.trim() || "Untitled 8D Report");
  router.push(`/chat/${p.project_id}`);
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <h1 class="app-logo" @click="router.push('/')">8D Agent</h1>
      <nav v-if="currentUser" class="app-nav">
        <a class="nav-link" @click="openNewDialog">{{ t('navNew', lang) }}</a>
        <router-link to="/history" class="nav-link">{{ t('navHistory', lang) }}</router-link>
        <router-link v-if="currentUser.role === 'admin'" to="/settings" class="nav-link">{{ t('navSettings', lang) }}</router-link>
        <router-link to="/account" class="nav-link">账号</router-link>
        <a class="nav-link" @click="logout">退出</a>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>

    <!-- New Report Dialog -->
    <div v-if="showNewDialog" class="dialog-overlay" @click.self="showNewDialog = false">
      <div class="dialog-box">
        <h3>{{ t('dialogNewTitle', lang) }}</h3>
        <input
          v-model="newReportName"
          class="dialog-input"
          :placeholder="t('dialogInputPlaceholder', lang)"
          @keydown.enter="createNewReport"
          autofocus
        />
        <div class="dialog-actions">
          <button class="dialog-btn btn-cancel" @click="showNewDialog = false">{{ t('dialogCancel', lang) }}</button>
          <button class="dialog-btn btn-ok" @click="createNewReport">{{ t('dialogOk', lang) }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
  font-size: 14px;
  color: #333;
  background: #f5f6f8;
}

.app-shell {
  display: flex;
  flex-direction: column;
  height: 100dvh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 52px;
  background: #1a5276;
  color: #fff;
  flex-shrink: 0;
}

.app-logo {
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 1px;
}

.app-nav {
  display: flex;
  gap: 8px;
}

.nav-link {
  color: rgba(255, 255, 255, 0.85);
  text-decoration: none;
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.nav-link:hover,
.nav-link.router-link-active {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.app-main {
  flex: 1;
  overflow: auto;
}

/* Dialog */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-box {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  width: min(380px, calc(100vw - 32px));
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.dialog-box h3 {
  font-size: 16px;
  margin-bottom: 16px;
  color: #333;
}

.dialog-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  font-family: inherit;
}

.dialog-input:focus {
  border-color: #2980b9;
}

.dialog-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 18px;
}

.dialog-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-cancel {
  background: #f0f0f0;
  color: #555;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-ok {
  background: #2980b9;
  color: #fff;
}

.btn-ok:hover {
  background: #1a5276;
}
</style>
<style>
@media(max-width:600px){.app-header{padding:0 10px;height:auto;min-height:52px;flex-wrap:wrap;gap:6px}.app-logo{font-size:16px}.app-nav{gap:0;flex-wrap:wrap}.nav-link{padding:8px;font-size:12px}input,textarea,select{font-size:16px}}
</style>
