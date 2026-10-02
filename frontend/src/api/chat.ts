import { api, API_ORIGIN } from "./client";

export interface ChatResponse {
  reply: string;
  current_step: string;
  step_status: string;
  project_id: string;
}

export interface GenerateOutputResponse {
  output: string;
  suggestions: string[];
}

export interface ReviewContextResponse {
  findings: Array<{
    type: string;
    title: string;
    description: string;
    source: string;
    suggestion: string;
  }>;
}

export interface FocusResponse {
  step: string;
  focus: string;
}

export const chatApi = {
  send: (projectId: string, message: string, step?: string) =>
    api.post<ChatResponse>("/chat", { project_id: projectId, message, step }),

  switchStep: (projectId: string, step: string) =>
    api.put<{ status: string }>("/chat/switch-step", { project_id: projectId, step }),

  saveContextNotes: (projectId: string, step: string, notes: string) =>
    api.put<{ status: string }>(`/project/${projectId}/context/${step}`, {
      project_id: projectId,
      step,
      notes,
    }),

  getContextNotes: (projectId: string, step: string) =>
    api.get<{ notes: string }>(`/project/${projectId}/context/${step}`),

  generateOutput: (projectId: string, step: string) =>
    api.post<GenerateOutputResponse>(`/project/${projectId}/generate-output/${step}`, {
      project_id: projectId,
      step,
    }),

  confirmOutput: (projectId: string, step: string, output: string) =>
    api.put<{ status: string }>(`/project/${projectId}/confirm-output/${step}`, {
      project_id: projectId,
      step,
      output,
    }),

  getFocus: (projectId: string, step: string) =>
    api.get<FocusResponse>(`/project/${projectId}/focus/${step}`),

  reviewContext: (projectId: string, step: string) =>
    api.post<ReviewContextResponse>(`/project/${projectId}/review-context/${step}`, {
      project_id: projectId,
      step,
    }),
};

export const uploadApi = {
  upload: async (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const base = API_ORIGIN;
    const resp = await fetch(`${base}/api/upload/${projectId}`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Upload failed");
    }
    return resp.json() as Promise<{ url: string; filename: string }>;
  },
};

