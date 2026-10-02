<script setup lang="ts">
import { computed } from "vue";
import { useConfigStore } from "../stores/config";
import { t } from "../i18n";

const props = defineProps<{
  currentStep: string;
  outputConfirmed: Record<string, boolean>;
  stepOutputs: Record<string, string>;
}>();

const emit = defineEmits<{
  select: [step: string];
}>();

const configStore = useConfigStore();
const lang = computed(() => configStore.interfaceLang);

const steps = computed(() => [
  { id: "D1", label: lang.value === "en" ? "D1 Build Team" : "D1 组建团队" },
  { id: "D2", label: lang.value === "en" ? "D2 Describe Problem" : "D2 问题描述" },
  { id: "D3", label: lang.value === "en" ? "D3 Short Term Action" : "D3 短期措施" },
  { id: "D4", label: lang.value === "en" ? "D4 Root Cause Analysis" : "D4 根本原因分析" },
  { id: "D5", label: lang.value === "en" ? "D5 Define Long Term Action" : "D5 制定长期措施" },
  { id: "D6", label: lang.value === "en" ? "D6 Implement Long Term Action" : "D6 实施长期措施" },
  { id: "D7", label: lang.value === "en" ? "D7 Proof of Effectiveness" : "D7 措施有效性验证" },
  { id: "D8", label: lang.value === "en" ? "D8 Prevention" : "D8 标准化与预防" },
]);

function isActive(stepId: string) {
  return stepId === props.currentStep;
}

function dotState(stepId: string): "green" | "yellow" | "gray" {
  if (props.outputConfirmed[stepId]) return "green";
  if (props.stepOutputs[stepId]) return "yellow";
  return "gray";
}

function isConfirmed(stepId: string) {
  return !!props.outputConfirmed[stepId];
}
</script>

<template>
  <div class="step-progress">
    <h3 class="step-title">{{ lang === 'en' ? '8D Progress' : '8D 进度' }}</h3>
    <div class="step-list">
      <div
        v-for="step in steps"
        :key="step.id"
        :class="['step-item', { active: isActive(step.id) }]"
        @click="emit('select', step.id)"
      >
        <div :class="['step-dot', `dot-${dotState(step.id)}`, { active: isActive(step.id) }]">
          <span v-if="isConfirmed(step.id)" class="step-check">&#10003;</span>
        </div>
        <span class="step-label">{{ step.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.step-progress {
  padding: 0;
}

.step-title {
  font-size: 13px;
  color: #888;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  user-select: none;
  color: #555;
}

.step-item:hover {
  background: #f5f5f5;
}

.step-item.active {
  background: #eaf2f8;
  font-weight: 600;
  color: #1a5276;
}

.step-item.active:hover {
  background: #d4e6f1;
}

.step-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s, box-shadow 0.3s;
}

/* Green: confirmed, complete */
.step-dot.dot-green {
  background: #27ae60;
}

/* Yellow: has output, not confirmed */
.step-dot.dot-yellow {
  background: #f0c040;
}

/* Gray: no output yet */
.step-dot.dot-gray {
  background: #ddd;
}

/* Active ring */
.step-dot.active {
  box-shadow: 0 0 0 3px rgba(41, 128, 185, 0.3);
}

.step-check {
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}
</style>
