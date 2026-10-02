<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api/client";
import { loadUser } from "../auth";
const username = ref("");
const password = ref("");
const busy = ref(false);
const error = ref("");
const router = useRouter();
async function login() {
  busy.value = true; error.value = "";
  try {
    await api.post("/auth/login", { username: username.value, password: password.value });
    await loadUser();
    await router.replace("/");
  } catch (e: any) { error.value = e.message || "登录失败，请重试"; }
  finally { busy.value = false; }
}
</script>
<template>
  <div class="login-page">
    <div class="login-intro"><span class="eyebrow">RAPID 8D · 试用版</span><h1>把问题，<br>一步步解决。</h1><p>从问题描述到措施验证，让每一次改进都有据可循。</p><div class="steps-line">D1 团队 → D2 问题 → D3–D7 分析与验证 → D8 标准化</div></div>
    <form class="login-card" @submit.prevent="login">
      <h2>登录工作空间</h2><p>当前采用邀请试用，请使用管理员提供的账号。</p>
      <label>账号<input v-model="username" autocomplete="username" required minlength="3" maxlength="40" placeholder="请输入账号"></label>
      <label>密码<input v-model="password" type="password" autocomplete="current-password" required minlength="8" maxlength="128" placeholder="请输入密码"></label>
      <p v-if="error" role="alert" class="error-text">{{ error }}</p>
      <button :disabled="busy" type="submit">{{ busy ? '正在登录…' : '进入工作空间' }}</button>
      <small>AI 输出需人工审核。请勿上传未经授权的业务资料。</small>
    </form>
  </div>
</template>
<style scoped>
.login-page{min-height:100%;display:flex;align-items:center;justify-content:center;gap:80px;padding:40px;background:linear-gradient(135deg,#eef4f8,#fff)}.login-intro{max-width:470px}.eyebrow{font-size:12px;letter-spacing:3px;color:#267797}.login-intro h1{font-size:54px;line-height:1.25;color:#163b50;margin:24px 0}.login-intro p{line-height:1.8;color:#5e7280}.steps-line{font-size:12px;margin-top:32px;color:#637d8d}.login-card{width:380px;background:white;padding:32px;border:1px solid #dee7ed;border-radius:16px;box-shadow:0 12px 45px #163b5010}.login-card h2{color:#163b50}.login-card p{color:#697e8b;line-height:1.7;margin:12px 0 22px}.login-card label{display:block;margin:18px 0;color:#344f60}.login-card input{display:block;width:100%;padding:12px;border:1px solid #cbd8e1;border-radius:6px;margin-top:8px;font:inherit}.login-card button{width:100%;padding:12px;background:#1a5276;color:white;border:0;border-radius:6px;font:inherit;cursor:pointer}.login-card small{display:block;color:#697e8b;margin-top:20px;line-height:1.7}.login-card .error-text{color:#b33b3b}button:disabled{opacity:.6}@media(max-width:760px){.login-page{padding:24px;gap:28px;flex-direction:column;align-items:stretch}.login-intro h1{font-size:32px;margin:12px 0}.steps-line{display:none}.login-card{width:100%;padding:24px}}
</style>
