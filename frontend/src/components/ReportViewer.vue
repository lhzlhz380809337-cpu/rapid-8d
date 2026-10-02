<script setup lang="ts">
import { computed } from "vue";
import { reportApi } from "../api/report";

const props = defineProps<{ sessionId: string }>();

const url = computed(() => reportApi.previewUrl(props.sessionId));
</script>

<template>
  <iframe sandbox="" :src="url" class="report-frame" />
</template>

<style scoped>
.report-frame {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
