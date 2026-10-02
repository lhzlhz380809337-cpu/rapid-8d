import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { configApi, type AppConfig } from "../api/config";

export const useConfigStore = defineStore("config", () => {
  const config = ref<AppConfig | null>(null);
  const loading = ref(false);

  const interfaceLang = computed(() => config.value?.app?.interface_lang || "zh");

  async function load() {
    loading.value = true;
    try {
      config.value = await configApi.get();
      if (config.value?.app?.interface_lang) {
        localStorage.setItem("interface_lang", config.value.app.interface_lang);
      }
    } finally {
      loading.value = false;
    }
  }

  async function updateLLM(settings: Record<string, string>) {
    await configApi.updateLLM(settings);
    await load();
  }

  async function updateApp(settings: Record<string, string>) {
    await configApi.updateApp(settings);
    if (config.value) {
      if (!config.value.app) config.value.app = { interface_lang: "zh", report_lang: "zh" };
      Object.assign(config.value.app, settings);
    }
    // Save to localStorage for frontend i18n
    if (settings.interface_lang) {
      localStorage.setItem("interface_lang", settings.interface_lang);
    }
  }

  async function loadGlossary(): Promise<string> {
    try {
      const res = await configApi.getGlossary();
      return res.content || "";
    } catch {
      return "";
    }
  }

  async function saveGlossary(content: string): Promise<void> {
    await configApi.updateGlossary(content);
  }

  return { config, loading, interfaceLang, load, updateLLM, updateApp, loadGlossary, saveGlossary };
});
