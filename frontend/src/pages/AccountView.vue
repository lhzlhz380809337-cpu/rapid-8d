<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "../api/client";
import { currentUser, loadUser } from "../auth";
const name = ref(""); const password = ref(""); const message = ref("");
const service = ref("尚未配置"); const ready = ref(false); const busy = ref(false);
const deletionPassword = ref("");
const oldPassword = ref(""); const newPassword = ref("");
async function changePassword() {
  busy.value = true; message.value = "";
  try {
    await api.put("/auth/password", { current_password: oldPassword.value, new_password: newPassword.value });
    window.location.hash = "/login"; window.location.reload();
  } catch(e: any) { message.value = e.message; } finally { busy.value = false; }
}
onMounted(async () => { const cfg = await api.get<any>("/config"); service.value = cfg.ai_service_name; ready.value = cfg.ai_ready; });
async function consent() {
  busy.value = true; message.value = "";
  try { await api.put("/auth/consent", { accepted: !currentUser.value?.ai_consent }); await loadUser(); }
  catch (e: any) { message.value = e.message; } finally { busy.value = false; }
}
async function create() {
  busy.value = true; message.value = "";
  try { await api.post("/auth/users", { username: name.value, password: password.value }); message.value = `已创建账号 ${name.value}，请通过你认可的方式交付凭据。`; name.value = ""; password.value = ""; }
  catch(e: any) { message.value = e.message; } finally { busy.value = false; }
}
async function removeAccount() {
  if (!window.confirm("确认永久删除账号及其全部项目、附件和报告？此操作无法撤销。")) return;
  busy.value = true;
  try {
    await api.remove("/auth/account", { username: currentUser.value?.username, password: deletionPassword.value });
    window.location.hash = "/login"; window.location.reload();
  } catch(e: any) { message.value = e.message; } finally { busy.value = false; }
}
</script>
<template>
  <div class="account-page"><h2>账号与数据</h2><p class="muted">{{ currentUser?.username }} · {{ currentUser?.role === 'admin' ? '管理员' : '试用账号' }}</p>
    <section><h3>AI 数据处理授权</h3><p>当前服务：<strong>{{ service }}</strong></p><p>使用 AI 对话、内容检查及报告生成功能时，会把相关项目内容、对话和已提取的附件文字发送给该服务处理。请仅提交你有权使用的资料。输出可能不准确，应由责任人核实后使用。</p><p>撤回授权后将停止新的 AI 请求，不影响手动编辑。撤回不能撤销已经发送的请求。</p><button :disabled="busy || (!ready && !currentUser?.ai_consent)" @click="consent">{{ currentUser?.ai_consent ? '撤回 AI 授权' : '同意并启用 AI 功能' }}</button><p v-if="!ready" class="muted">AI 服务尚未配置，可以先创建和手动编辑项目。</p></section>
    <section><h3>修改密码</h3><form @submit.prevent="changePassword"><label>当前密码<input v-model="oldPassword" type="password" required minlength="8" autocomplete="current-password"></label><label>新密码<input v-model="newPassword" type="password" required minlength="8" maxlength="128" autocomplete="new-password"></label><button :disabled="busy">修改并重新登录</button></form></section>
    <section v-if="currentUser?.role === 'admin'"><h3>创建试用账号</h3><form @submit.prevent="create"><label>账号<input v-model="name" pattern="[A-Za-z0-9_]{3,40}" required placeholder="3–40 位字母、数字或下划线"></label><label>初始密码<input v-model="password" type="password" required minlength="8" maxlength="128" autocomplete="new-password" placeholder="至少 8 位"></label><button :disabled="busy">创建账号</button></form></section>
    <section v-else><h3>删除账号</h3><p>删除账号将移除当前服务上的项目、附件、报告和登录会话。已导出的文件不会被删除；备份副本按运营方的备份保留期限处理。</p><label>输入当前密码<input v-model="deletionPassword" type="password" autocomplete="current-password"></label><button :disabled="busy || deletionPassword.length < 8" @click="removeAccount">删除账号及数据</button></section>
    <p v-if="message" role="status">{{ message }}</p>
  </div>
</template>
<style scoped>
.account-page{height:100%;overflow:auto;padding:28px;max-width:850px;margin:auto}.account-page h2{color:#1a5276}.muted{color:#6d7d88;margin:10px 0}section{background:#fff;border:1px solid #dde5eb;border-radius:10px;padding:24px;margin:24px 0}section p{line-height:1.8;margin:12px 0}label{display:block;margin:14px 0}input{display:block;width:100%;max-width:420px;padding:10px;margin-top:8px;border:1px solid #cad5df;border-radius:5px}button{background:#1a5276;color:white;padding:10px 18px;border:0;border-radius:5px;cursor:pointer}button:disabled{opacity:.5}@media(max-width:600px){.account-page{padding:16px}section{padding:18px}}
</style>
