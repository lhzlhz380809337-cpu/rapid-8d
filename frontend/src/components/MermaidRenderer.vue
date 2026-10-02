<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import mermaid from "mermaid";
import DOMPurify from "dompurify";

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "strict",
  fontFamily: "inherit",
});

const props = defineProps<{
  content: string;
  editable?: boolean;
  fontSize?: number;
}>();

const emit = defineEmits<{
  update: [content: string];
}>();

const editMode = ref(false);
const editContent = ref("");
const renderedHtml = ref("");
const error = ref("");

function sanitizeMermaid(code: string): string {
  // Replace characters inside node labels [...] that confuse Mermaid 11.x parser
  return code.replace(/\[([^\]]*)\]/g, (_full, label: string) => {
    const safe = label
      .replace(/\(/g, "（")
      .replace(/\)/g, "）")
      .replace(/"/g, "＂");
    return `[${safe}]`;
  });
}

const MERMAID_ERROR_MARKERS = ["Syntax error", "mermaid version"];

function isErrorSvg(svg: string): boolean {
  return MERMAID_ERROR_MARKERS.some((m) => svg.includes(m));
}

async function render() {
  error.value = "";
  const source = editMode.value ? editContent.value : props.content;

  if (!source) {
    renderedHtml.value = "";
    return;
  }

  // Parse markdown: extract mermaid blocks and render them separately
  const mermaidBlocks: { placeholder: string; code: string }[] = [];
  let processed = source;

  // Find mermaid code blocks
  const mermaidRegex = /```mermaid\s*([\s\S]*?)\s*```/g;
  let match;
  let idx = 0;

  while ((match = mermaidRegex.exec(source)) !== null) {
    const placeholder = `__MERMAID_${idx}__`;
    const rawCode = match[1].trim();
    mermaidBlocks.push({ placeholder, code: sanitizeMermaid(rawCode) });
    processed = processed.replace(match[0], placeholder);
    idx++;
  }

  // Render mermaid blocks to SVG
  const svgMap: Record<string, string> = {};
  for (const block of mermaidBlocks) {
    try {
      const id = `mermaid-${Math.random().toString(36).slice(2, 8)}`;
      const { svg } = await mermaid.render(id, block.code);
      if (isErrorSvg(svg)) {
        svgMap[block.placeholder] = `<pre class="mermaid-error">图表渲染失败</pre>`;
      } else {
        svgMap[block.placeholder] = svg;
      }
    } catch (e: any) {
      svgMap[block.placeholder] = `<pre class="mermaid-error">图表渲染失败: ${e.message}</pre>`;
    }
  }

  // Replace placeholders with SVGs
  for (const block of mermaidBlocks) {
    processed = processed.replace(block.placeholder, svgMap[block.placeholder] || "");
  }

  // Convert remaining markdown to HTML
  processed = renderMarkdown(processed);
  renderedHtml.value = DOMPurify.sanitize(processed, { USE_PROFILES: { html: true, svg: true, svgFilters: true } });
}

function renderMarkdown(md: string): string {
  let html = md;

  // Mermaid SVGs (already rendered) wrapped in div
  html = html.replace(/<svg/g, '<div class="mermaid-chart"><svg');
  html = html.replace(/<\/svg>/g, "</svg></div>");

  // Markdown tables
  html = html.replace(/\n(\|.+\|)[\s\S]*?\n\n/g, (match) => {
    const rows = match.trim().split("\n");
    const thead = rows[0] ? `<thead><tr>${rows[0].split("|").filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join("")}</tr></thead>` : "";
    const tbody = rows.slice(2).map(row =>
      `<tr>${row.split("|").filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join("")}</tr>`
    ).join("");
    return `\n<table>${thead}<tbody>${tbody}</tbody></table>\n`;
  });

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // Italic
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Headers
  html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");

  // Lists
  html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");

  // Line breaks
  html = html.replace(/\n\n/g, "</p><p>");
  html = html.replace(/\n/g, "<br>");
  html = `<p>${html}</p>`;

  // Images
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />');

  return html;
}

function enterEdit() {
  editContent.value = props.content;
  editMode.value = true;
}

function saveEdit() {
  editMode.value = false;
  emit("update", editContent.value);
}

function cancelEdit() {
  editMode.value = false;
  editContent.value = props.content;
}

watch(() => props.content, () => {
  nextTick(render);
}, { immediate: true });
</script>

<template>
  <div class="mermaid-renderer">
    <div v-if="editable && !editMode" class="toolbar">
      <button class="btn-edit" @click="enterEdit">编辑</button>
    </div>
    <div v-if="editable && editMode" class="toolbar">
      <button class="btn-save" @click="saveEdit">保存</button>
      <button class="btn-cancel" @click="cancelEdit">取消</button>
    </div>

    <div v-if="editMode" class="edit-area">
      <textarea v-model="editContent" class="edit-textarea" rows="15"></textarea>
      <div class="edit-preview">
        <div class="preview-label">预览</div>
        <div class="rendered" v-html="renderedHtml" ref="previewEl" :style="fontSize ? { fontSize: fontSize + 'px' } : {}"></div>
      </div>
    </div>

    <div v-else class="rendered" v-html="renderedHtml" :style="fontSize ? { fontSize: fontSize + 'px' } : {}"></div>

    <div v-if="error" class="render-error">{{ error }}</div>
  </div>
</template>

<style scoped>
.mermaid-renderer {
  position: relative;
}

.toolbar {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.btn-edit, .btn-save, .btn-cancel {
  padding: 3px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  background: #fff;
}

.btn-save {
  background: #27ae60;
  color: #fff;
  border-color: #27ae60;
}

.btn-cancel {
  background: #e74c3c;
  color: #fff;
  border-color: #e74c3c;
}

.edit-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.edit-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  resize: vertical;
}

.edit-preview {
  border: 1px dashed #ccc;
  padding: 10px;
  border-radius: 4px;
}

.preview-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 6px;
}

.rendered {
  line-height: 1.7;
  font-size: 14px;
}

.rendered :deep(h2) { font-size: 16px; margin: 12px 0 6px; }
.rendered :deep(h3) { font-size: 14px; margin: 10px 0 4px; }
.rendered :deep(h4) { font-size: 13px; margin: 8px 0 4px; }
.rendered :deep(ul) { padding-left: 20px; margin: 6px 0; }
.rendered :deep(li) { margin: 2px 0; }
.rendered :deep(code) { background: #f0f0f0; padding: 1px 4px; border-radius: 2px; font-size: 13px; }
.rendered :deep(table) { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 13px; }
.rendered :deep(th), .rendered :deep(td) { border: 1px solid #ddd; padding: 6px 10px; text-align: left; }
.rendered :deep(th) { background: #f5f5f5; font-weight: 600; }
.rendered :deep(.mermaid-chart) { margin: 12px 0; padding: 10px; background: #fafafa; border-radius: 4px; overflow-x: auto; }
.rendered :deep(.mermaid-chart svg) { max-width: 100%; }
.rendered :deep(img) { max-width: 100%; border-radius: 4px; margin: 8px 0; }
.rendered :deep(.mermaid-error) { color: #e74c3c; font-size: 12px; padding: 8px; background: #fdf0ef; border-radius: 4px; }

.render-error {
  color: #e74c3c;
  font-size: 12px;
  margin-top: 6px;
  padding: 6px 10px;
  background: #fdf0ef;
  border-radius: 4px;
}
</style>
