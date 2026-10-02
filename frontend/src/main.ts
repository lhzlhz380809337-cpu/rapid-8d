import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import ChatView from "./pages/ChatView.vue";
import ReportPreview from "./pages/ReportPreview.vue";
import ReportGenerator from "./pages/ReportGenerator.vue";
import HistoryView from "./pages/HistoryView.vue";
import SettingsView from "./pages/SettingsView.vue";
import LoginView from "./pages/LoginView.vue";
import AccountView from "./pages/AccountView.vue";
import { currentUser, loadUser } from "./auth";

const routes = [
  { path: "/login", component: LoginView },
  { path: "/account", component: AccountView },
  { path: "/", name: "home", component: ChatView },
  { path: "/chat/:id", name: "chat", component: ChatView },
  { path: "/report/:id", name: "report", component: ReportPreview },
  { path: "/report-generator/:id", name: "report-generator", component: ReportGenerator },
  { path: "/history", name: "history", component: HistoryView },
  { path: "/settings", name: "settings", component: SettingsView },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

const app = createApp(App);
router.beforeEach(async (to) => {
  if (to.path === "/login") return true;
  if (!currentUser.value) await loadUser();
  if (!currentUser.value) return "/login";
  if (to.path === "/settings" && currentUser.value.role !== "admin") return "/account";
  return true;
});
app.use(createPinia());
app.use(router);
app.mount("#app");
