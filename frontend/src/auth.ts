import { ref } from "vue";
import { api } from "./api/client";

export interface User { id: string; username: string; role: string; ai_consent: number }
export const currentUser = ref<User | null>(null);
export async function loadUser() {
  try { currentUser.value = await api.get<User>("/auth/me"); }
  catch { currentUser.value = null; }
  return currentUser.value;
}
