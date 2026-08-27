<template>
  <div class="plan-display">
    <header class="plan-header">
      <h2>{{ plan.title }}</h2>
      <div class="actions">
        <button @click="copyText" class="action-btn" title="复制文本内容">
          <svg xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          <span>复制文本</span>
        </button>
        <a :href="plan.final_pdf_url" target="_blank" download class="action-btn" title="下载PDF报告">
          <svg xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
          <span>下载PDF</span>
        </a>
      </div>
    </header>

    <section v-for="(section, index) in parsedTextContent" :key="index" class="plan-section">
      <h3>{{ section.headline }}</h3>
      <p>{{ section.content }}</p>
    </section>

    <section class="plan-section">
      <h3>效果图预览</h3>
      <div class="image-gallery">
        <img v-for="(url, i) in plan.generated_image_urls" :key="i" :src="url" alt="AI生成的效果图">
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  plan: {
    type: Object,
    required: true,
  }
});

// 【核心修改】新增一个计算属性，用于智能解析后端返回的文本内容
const parsedTextContent = computed(() => {
  const content = props.plan.generated_text_content;
  if (!content) return [];
  
  // 情况一：后端已成功解析，直接返回
  if (Array.isArray(content) && content.length > 0 && typeof content[0] === 'object') {
    return content;
  }
  
  // 情况二：后端返回的是一个包含JSON的字符串
  if (typeof content === 'string') {
    try {
      // 尝试清理字符串中可能存在的`json`标记和首尾的 `\n` 或空格
      const cleanedString = content.replace(/```json\n?|```/g, '').trim();
      const parsed = JSON.parse(cleanedString);
      // 确保解析后是期望的数组格式
      if (Array.isArray(parsed)) {
        return parsed;
      }
    } catch (e) {
      console.error("二次解析JSON失败:", e);
      // 如果二次解析也失败，则返回一个降级显示的内容
      return [{ headline: "AI设计方案", content: content }];
    }
  }

  // 其他未知情况，同样做降级处理
  return [{ headline: "AI设计方案", content: "无法解析的方案内容格式。" }];
});

const plainTextContent = computed(() => {
    let text = `${props.plan.title}\n\n`;
    // 使用解析后的内容来生成纯文本
    parsedTextContent.value.forEach(section => {
        text += `${section.headline}\n${section.content}\n\n`;
    });
    return text;
});

const copyText = async () => {
  try {
    await navigator.clipboard.writeText(plainTextContent.value);
    alert('方案文本已复制到剪贴板！');
  } catch (err) {
    console.error('复制失败:', err);
    alert('复制失败，请手动复制。');
  }
};
</script>

<style scoped>
/* 样式部分无需修改 */
.plan-display { background: #fff; padding: 2rem 3rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
.plan-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 1.5rem; margin-bottom: 2rem; }
.plan-header h2 { margin: 0; font-size: 1.5rem; color: #333; }
.actions { display: flex; gap: 0.8rem; }
.action-btn { display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem; padding: 0.5rem 1rem; border: 1px solid #E0E0E0; background-color: #fff; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 500; color: #555; transition: all 0.2s ease-in-out; text-decoration: none; }
.action-btn:hover { background-color: #FFF8E1; border-color: #FFA726; color: #FB8C00; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
.action-btn svg { stroke: currentColor; }
.plan-section { margin-bottom: 2rem; }
.plan-section h3 { margin-bottom: 1rem; color: #333; font-size: 1.2rem; padding-bottom: 0.5rem; border-bottom: 1px solid #f0f0f0; }
.plan-section p { line-height: 1.8; color: #555; white-space: pre-wrap; }
.image-gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
.image-gallery img { width: 100%; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
</style>