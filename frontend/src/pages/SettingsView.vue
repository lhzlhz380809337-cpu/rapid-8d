<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useChatStore } from "../stores/chat";
import { useConfigStore } from "../stores/config";
import { t } from "../i18n";
import type { AppConfig } from "../api/config";

const router = useRouter();
const chatStore = useChatStore();
const store = useConfigStore();
const lang = computed(() => store.interfaceLang);
const interfaceLang = ref("zh");
const reportLang = ref("zh");
const apiBaseUrl = ref("");
const apiModel = ref("");
const glossaryContent = ref("");
const saved = ref(false);

function goBack() {
  router.push(chatStore.projectId ? `/chat/${chatStore.projectId}` : "/");
}

function applyConfig(cfg: AppConfig) {
  interfaceLang.value = cfg.app?.interface_lang || "zh";
  reportLang.value = cfg.app?.report_lang || "zh";
  apiBaseUrl.value = cfg.llm.api.base_url || "";
  apiModel.value = cfg.llm.api.model || "";
  localStorage.setItem("interface_lang", interfaceLang.value);
}

onMounted(async () => {
  await store.load();
  if (store.config) applyConfig(store.config);
  glossaryContent.value = await store.loadGlossary();
});

async function saveSettings() {
  await store.updateLLM({ base_url: apiBaseUrl.value, model: apiModel.value });
  await store.updateApp({ interface_lang: interfaceLang.value, report_lang: reportLang.value });
  await store.saveGlossary(glossaryContent.value);
  saved.value = true;
  setTimeout(() => (saved.value = false), 2000);
}
</script>

<template>
  <div class="settings-view">
    <div class="settings-header">
      <button class="btn-back" @click="goBack">{{ t('backToEdit', lang) }}</button>
      <h2>{{ t('settingsTitle', lang) }}</h2>
    </div>

    <section class="setting-group">
      <h3>云端 AI 服务</h3>
      <p class="help-text">首版只支持云端 API。密钥由服务器环境变量 R8D_API_KEY 管理，不会在网页中显示或保存。</p>
      <div class="form-row">
        <label>API 地址</label>
        <input v-model="apiBaseUrl" class="form-input" placeholder="https://api.deepseek.com/v1" />
      </div>
      <div class="form-row">
        <label>模型名称</label>
        <input v-model="apiModel" class="form-input" placeholder="deepseek-chat" />
      </div>
      <p class="status" :class="{ ready: store.config?.ai_ready }">
        {{ store.config?.ai_ready ? '服务器密钥已配置' : '服务器尚未配置 AI 密钥，手动填写功能仍可使用' }}
      </p>
    </section>

    <section class="setting-group">
      <h3>{{ t('langSettings', lang) }}</h3>
      <div class="form-row">
        <label>{{ t('interfaceLangLabel', lang) }}</label>
        <select v-model="interfaceLang" class="form-input">
          <option value="zh">中文</option>
          <option value="en">English</option>
        </select>
      </div>
      <div class="form-row">
        <label>{{ t('reportLangLabel', lang) }}</label>
        <select v-model="reportLang" class="form-input">
          <option value="zh">中文</option>
          <option value="en">English</option>
          <option value="both">中英双语</option>
        </select>
      </div>
    </section>

    <section class="setting-group">
      <h3>{{ t('glossaryTitle', lang) }}</h3>
      <p class="help-text">{{ t('glossaryHelp', lang) }}</p>
      <textarea
        v-model="glossaryContent"
        class="glossary-textarea"
        :placeholder="lang === 'en' ? '### Term Mapping\n- Containment Action → 遏制措施' : '### 术语表\n- 遏制措施 → Containment Action'"
        spellcheck="false"
        rows="14"
      />
    </section>

    <div class="form-actions">
      <button class="btn-save" @click="saveSettings">{{ t('save', lang) }}</button>
      <span v-if="saved" class="saved-hint">{{ t('saved', lang) }}</span>
    </div>
  </div>
</template>

<style scoped>
.settings-view { max-width: 680px; margin: 0 auto; padding: 24px; height: 100%; overflow-y: auto; }
.settings-header { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; }
.settings-header h2 { font-size: 18px; margin: 0; }
.btn-back { background: #fff; border: 1px solid #d6dde2; padding: 7px 12px; border-radius: 6px; cursor: pointer; }
.setting-group { background: #fff; border: 1px solid #e0e6ea; border-radius: 10px; padding: 18px 20px; margin-bottom: 16px; }
.setting-group h3 { font-size: 15px; margin: 0 0 14px; color: #1a5276; }
.help-text { color: #667985; font-size: 13px; line-height: 1.6; margin: 0 0 14px; }
.form-row { display: grid; grid-template-columns: 110px 1fr; align-items: center; gap: 12px; margin-bottom: 12px; }
.form-row label { font-size: 13px; color: #40535e; }
.form-input, .glossary-textarea { width: 100%; box-sizing: border-box; border: 1px solid #ccd7dd; border-radius: 6px; padding: 9px 10px; font: inherit; }
.glossary-textarea { resize: vertical; min-height: 190px; line-height: 1.55; }
.status { margin: 8px 0 0; color: #a15d00; font-size: 12px; }
.status.ready { color: #167445; }
.form-actions { display: flex; align-items: center; gap: 12px; padding-bottom: 24px; }
.btn-save { border: 0; border-radius: 7px; padding: 10px 22px; color: #fff; background: #1677a8; cursor: pointer; }
.saved-hint { color: #167445; font-size: 13px; }
@media (max-width: 600px) {
  .settings-view { padding: 14px; }
  .setting-group { padding: 15px; }
  .form-row { grid-template-columns: 1fr; gap: 6px; }
}
</style>
