import { api } from "./client";

export interface AppConfig {
  is_admin: boolean;
  ai_ready: boolean;
  ai_service_name: string;
  app?: { interface_lang: string; report_lang: string };
  llm: {
    api: { base_url: string; model: string; has_api_key: boolean };
  };
  report: { company_name: string };
}

export const configApi = {
  get: () => api.get<AppConfig>("/config"),

  updateLLM: (settings: Record<string, string>) =>
    api.put<void>("/config/llm", { provider: "api", api: settings }),

  updateApp: (settings: Record<string, string>) =>
    api.put<void>("/config/app", settings),

  getGlossary: () => api.get<{ content: string }>("/config/glossary"),

  updateGlossary: (content: string) =>
    api.put<void>("/config/glossary", { content }),
};
