import { api } from "./client";

export interface ProjectSummary {
  project_id: string;
  title: string;
  current_step: string;
  date: string;
  steps_completed: number;
  total_steps: number;
  message_count: number;
  context_versions: number;
  report_versions: number;
}

export interface ProjectDetail extends ProjectSummary {
  contexts: ContextVersion[];
  reports: ReportVersion[];
}

export interface ContextVersion {
  date: string;
  path: string;
  size: number;
}

export interface ReportVersion {
  date: string;
  html_path: string;
  docx_path: string;
}

export interface ContextData {
  project_id: string;
  date: string;
  title: string;
  current_step: string;
  step_states: Record<string, {
    status: string;
    summary: string;
    context_notes?: string;
    ai_output?: string;
    output_confirmed?: boolean;
    images?: string[];
  }>;
  messages: Array<{ role: string; content: string; step: string; timestamp: string }>;
}

export const projectApi = {
  create: (title?: string) =>
    api.post<{ project_id: string; title: string }>(
      `/projects?title=${encodeURIComponent(title || "未命名 8D 报告")}`
    ),

  list: () => api.get<ProjectSummary[]>("/projects"),

  get: (id: string) => api.get<ProjectDetail>(`/projects/${id}`),

  delete: (id: string) => api.delete<void>(`/projects/${id}`),

  rename: (id: string, title: string) =>
    api.put<{ status: string }>(`/projects/${id}?title=${encodeURIComponent(title)}`),

  listContexts: (id: string) => api.get<ContextVersion[]>(`/projects/${id}/contexts`),

  loadContext: (id: string, date?: string) =>
    api.get<ContextData>(date ? `/projects/${id}/contexts/${date}` : `/projects/${id}/contexts/latest`),
};
