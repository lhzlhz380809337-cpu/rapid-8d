import { defineStore } from "pinia";
import { ref, reactive } from "vue";
import { chatApi } from "../api/chat";
import { projectApi, type ContextData } from "../api/session";

export const useChatStore = defineStore("chat", () => {
  const projectId = ref<string | null>(null);
  const currentStep = ref("D1");
  const messages = ref<Array<{ role: string; content: string; step: string; timestamp: string }>>([]);
  const sending = ref(false);
  const contextDate = ref("");

  // Per-step data
  const stepContextNotes = reactive<Record<string, string>>({});
  const stepContextDraft = reactive<Record<string, string>>({});
  const stepOutputs = reactive<Record<string, string>>({});
  const stepOutputConfirmed = reactive<Record<string, boolean>>({});
  const stepFocusQuestions = reactive<Record<string, string>>({});
  const stepSuggestions = reactive<Record<string, string[]>>({});
  const crossCheckWarnings = ref<string[]>([]);

  // Output generation state
  const generatingOutput = ref(false);

  async function newProject(title?: string) {
    const p = await projectApi.create(title);
    projectId.value = p.project_id;
    currentStep.value = "D1";
    messages.value = [];
    resetStepData();
    return p;
  }

  async function loadProject(id: string, date?: string) {
    const ctx = await projectApi.loadContext(id, date);
    resetStepData();
    projectId.value = ctx.project_id;
    currentStep.value = ctx.current_step;
    contextDate.value = ctx.date;
    messages.value = ctx.messages || [];
    // Load per-step data from context
    if ((ctx as any).step_states) {
      const states = (ctx as any).step_states;
      for (const [step, state] of Object.entries(states)) {
        const s = state as any;
        stepContextNotes[step] = s.context_notes || "";
        stepContextDraft[step] = s.context_notes || "";
        stepOutputs[step] = s.ai_output || "";
        stepOutputConfirmed[step] = Boolean(s.output_confirmed);
        stepSuggestions[step] = Array.isArray(s.suggestions) ? s.suggestions : [];
      }
    }
    return ctx;
  }

  function resetStepData() {
    for (const k of Object.keys(stepContextNotes)) delete stepContextNotes[k];
    for (const k of Object.keys(stepContextDraft)) delete stepContextDraft[k];
    for (const k of Object.keys(stepOutputs)) delete stepOutputs[k];
    for (const k of Object.keys(stepOutputConfirmed)) delete stepOutputConfirmed[k];
    for (const k of Object.keys(stepFocusQuestions)) delete stepFocusQuestions[k];
    for (const k of Object.keys(stepSuggestions)) delete stepSuggestions[k];
    crossCheckWarnings.value = [];
  }

  async function sendMessage(text: string) {
    if (!projectId.value || sending.value) return;
    sending.value = true;

    messages.value.push({
      role: "user",
      content: text,
      step: currentStep.value,
      timestamp: new Date().toISOString(),
    });

    try {
      const resp = await chatApi.send(projectId.value, text, currentStep.value);
      messages.value.push({
        role: "assistant",
        content: resp.reply,
        step: currentStep.value,
        timestamp: new Date().toISOString(),
      });
      // No auto-advance — stay on current step
    } catch (e: any) {
      messages.value.push({
        role: "system",
        content: `Request failed: ${e.message || "Network error"}`,
        step: currentStep.value,
        timestamp: new Date().toISOString(),
      });
    } finally {
      sending.value = false;
    }
  }

  async function switchStep(step: string) {
    if (!projectId.value || step === currentStep.value) return;
    // Optimistic update — switch UI immediately
    currentStep.value = step;
    try {
      await chatApi.switchStep(projectId.value, step);
    } catch (e: any) {
      console.error("Switch step failed:", e.message);
      // UI already updated, backend will sync on next action
    }
  }

  async function loadFocusQuestions(step: string) {
    if (!projectId.value) return;
    const resp = await chatApi.getFocus(projectId.value, step);
    stepFocusQuestions[step] = resp.focus;
  }

  async function saveContextNotes(notes: string, step = currentStep.value, id = projectId.value) {
    if (!id) return;
    await chatApi.saveContextNotes(id, step, notes);
    if (id === projectId.value) {
      stepContextNotes[step] = notes;
    }
  }

  async function reviewContext() {
    if (!projectId.value) return;
    const step = currentStep.value;
    try {
      const resp = await chatApi.reviewContext(projectId.value, step);
      // Reload messages to get the system message with findings
      if (projectId.value) {
        const ctx = await projectApi.loadContext(projectId.value);
        messages.value = ctx.messages || [];
      }
      return resp;
    } catch (e: any) {
      messages.value.push({
        role: "system",
        content: `Context review failed: ${e.message || "Network error"}`,
        step: currentStep.value,
        timestamp: new Date().toISOString(),
      });
    }
  }

  async function generateOutput() {
    if (!projectId.value || generatingOutput.value) return;
    generatingOutput.value = true;

    try {
      const step = currentStep.value;
      const resp = await chatApi.generateOutput(projectId.value, step);
      stepOutputs[step] = resp.output;
      stepSuggestions[step] = resp.suggestions || [];

      // Push suggestions as assistant message in chat
      if (resp.suggestions && resp.suggestions.length > 0) {
        const suggestionItems = resp.suggestions.map((s: string) => `- ${s}`).join('\n');
        messages.value.push({
          role: "assistant",
          content: `📋 AI 输出已生成，以下信息建议补充：\n\n${suggestionItems}\n\n💬 你可以与我讨论这些问题来完善报告。`,
          step: step,
          timestamp: new Date().toISOString(),
        });
      }

      return resp;
    } catch (e: any) {
      messages.value.push({
        role: "system",
        content: `Output generation failed: ${e.message || "Network error"}`,
        step: currentStep.value,
        timestamp: new Date().toISOString(),
      });
    } finally {
      generatingOutput.value = false;
    }
  }

  async function updateTitle(title: string) {
    if (!projectId.value) return;
    await projectApi.rename(projectId.value, title);
  }

  async function confirmOutput(output: string) {
    if (!projectId.value) return;
    const step = currentStep.value;
    await chatApi.confirmOutput(projectId.value, step, output);
    stepOutputs[step] = output;
    stepOutputConfirmed[step] = true;
  }

  return {
    projectId,
    currentStep,
    contextDate,
    messages,
    sending,
    generatingOutput,
    stepContextNotes,
    stepContextDraft,
    stepOutputs,
    stepOutputConfirmed,
    stepFocusQuestions,
    stepSuggestions,
    crossCheckWarnings,
    newProject,
    loadProject,
    sendMessage,
    switchStep,
    loadFocusQuestions,
    saveContextNotes,
    reviewContext,
    generateOutput,
    confirmOutput,
    updateTitle,
  };
});
