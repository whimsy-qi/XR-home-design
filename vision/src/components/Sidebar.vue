<template>
  <aside class="sidebar">
    <div class="logo-container">
      <span class="logo-icon">V</span>
      <h2 class="logo-text">Vision</h2>
    </div>

    <div class="history-section">
      <h3 class="history-title">最近项目</h3>
      
      <div v-if="isLoading" class="status-info">正在加载...</div>
      <div v-if="error" class="status-info error">{{ error }}</div>

      <ul v-if="tasks.length > 0" class="task-list">
        <li v-for="task in tasks" :key="task.id" class="task-item">
          <span class="task-icon" :class="getTaskIcon(task.task_type_display).class">{{ getTaskIcon(task.task_type_display).icon }}</span>
          <div class="task-info">
            <span class="task-type">{{ task.task_type_display }}</span>
            <span class="task-status" :class="task.status_display.toLowerCase()">{{ task.status_display }}</span>
          </div>
        </li>
      </ul>
      
      <p v-else-if="!isLoading" class="status-info">暂无历史项目</p>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const tasks = ref([]);
const isLoading = ref(true);
const error = ref('');
const authStore = useAuthStore();

// 一个辅助函数，根据任务类型返回不同的图标和样式
const getTaskIcon = (taskType) => {
  if (taskType.includes('方案')) {
    return { icon: '💡', class: 'plan' };
  }
  if (taskType.includes('图片')) {
    return { icon: '🖼️', class: 'image' };
  }
  if (taskType.includes('模型')) {
    return { icon: '🧊', class: 'model' };
  }
  return { icon: '📁', class: 'default' };
};

onMounted(async () => {
  if (!authStore.accessToken) {
    error.value = '用户未登录';
    isLoading.value = false;
    return;
  }
  
  try {
    axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.accessToken}`;
    const response = await axios.get('http://127.0.0.1:8000/api/ai/tasks/');

    // --- 【核心修正】增加一个健壮性检查 ---
    // 检查后端返回的数据是否是我们预期的分页格式
    if (response.data && Array.isArray(response.data.results)) {
      // 如果是，就从 .results 中获取任务数组
      tasks.value = response.data.results.slice(0, 10);
    } 
    // 兼容后端没有返回分页，而是直接返回了一个数组的情况
    else if (Array.isArray(response.data)) {
      tasks.value = response.data.slice(0, 10);
    } 
    else {
      // 如果数据格式未知，抛出一个更清晰的错误
      console.error("后端返回的数据格式不正确: ", response.data);
      throw new Error('后端返回的数据格式不正确');
    }
    // ------------------------------------

  } catch (err) {
    error.value = '无法加载历史项目。';
    // 在控制台打印出原始错误，方便调试
    console.error('获取任务列表失败:', err);
  } finally {
    isLoading.value = false;
  }
});
</script>

<style scoped>
.sidebar {
  width: 280px;
  background-color: #FFFFFF;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  height: 100vh;
  border-right: 1px solid #EEEEEE;
  box-sizing: border-box;
}
.logo-container {
  display: flex;
  align-items: center;
  padding: 0 0.5rem;
  margin-bottom: 2.5rem;
  flex-shrink: 0; /* 防止被压缩 */
}
.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(45deg, #FFA726, #FFD54F);
  color: white;
  display: grid;
  place-items: center;
  font-size: 1.5rem;
  font-weight: bold;
  border-radius: 10px;
  margin-right: 0.8rem;
}
.logo-text {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.history-section {
  flex-grow: 1;
  overflow-y: auto; /* 当列表过长时可以滚动 */
}
.history-title {
  font-size: 0.9rem;
  text-transform: uppercase;
  color: #757575;
  margin-bottom: 1rem;
  padding: 0 0.5rem;
}
.task-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.task-item {
  display: flex;
  align-items: center;
  padding: 0.8rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
}
.task-item:hover {
  background-color: #FFF8E1; /* 浅黄色悬浮背景 */
}
.task-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 1.5rem;
  margin-right: 1rem;
}
.task-icon.plan { background-color: rgba(255, 213, 79, 0.3); }
.task-icon.image { background-color: rgba(255, 167, 38, 0.3); }
.task-icon.model { background-color: rgba(255, 184, 77, 0.3); }

.task-info {
  display: flex;
  flex-direction: column;
}
.task-type {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}
.task-status {
  font-size: 0.8rem;
  color: #757575;
}
.status-info {
  padding: 1rem;
  text-align: center;
  color: #757575;
}
.status-info.error {
  color: #D32F2F;
}
</style>