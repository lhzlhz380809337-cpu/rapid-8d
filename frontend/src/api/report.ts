import { api, API_ORIGIN } from "./client";

export interface GenerateReportResponse {
  html_content: string;
  backup_html_path: string;
  docx_path: string;
  project_id: string;
  title: string;
  warnings: Array<{
    type: string;
    match: string;
    label?: string;
    context: string;
    step: string;
  }>;
}

export interface GenerateWithLLMResponse {
  report_content: string;
  html: string;
  project_id: string;
  title: string;
}

export interface ReportRequirementsResponse {
  default_requirements: string;
  custom_requirements: string;
}

export const reportApi = {
  generate: (projectId: string) =>
    api.post<GenerateReportResponse>(`/reports/${projectId}/generate`),

  previewUrl: (projectId: string) => `${API_ORIGIN}/api/reports/${projectId}/preview`,

  exportDocxUrl: (projectId: string) => `${API_ORIGIN}/api/reports/${projectId}/export/docx`,

  exportPdfUrl: (projectId: string) => `${API_ORIGIN}/api/reports/${projectId}/export/pdf`,

  getRequirements: (projectId: string) =>
    api.get<ReportRequirementsResponse>(`/reports/${projectId}/requirements`),

  saveRequirements: (projectId: string, requirements: string) =>
    api.put(`/reports/${projectId}/requirements`, { requirements }),

  generateWithLLM: (projectId: string, requirements: string) =>
    api.post<GenerateWithLLMResponse>(`/reports/${projectId}/generate-with-llm`, { requirements }),

  saveReport: (projectId: string, html: string) =>
    api.post<{ status: string; backup_path: string; title: string }>(
      `/reports/${projectId}/save-report`,
      { html }
    ),
};
