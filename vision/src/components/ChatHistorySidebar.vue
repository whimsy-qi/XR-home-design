<template>
  <aside class="chat-history-sidebar">
    <div class="header">
      <router-link to="/" class="logo-link" title="返回主仪表盘">
        <span class="logo-icon">V</span>
        <h2 class="logo-text">Vision</h2>
      </router-link>
      <button @click="startNewChat" class="new-chat-btn" title="开始新对话">+</button>
    </div>

    <div class="history-section">
      <h3 class="history-title">对话历史</h3>
      <div v-if="chatStore.isLoadingList" class="status-info">正在加载...</div>
      <ul v-else class="session-list">
        <li
          v-for="session in chatStore.sessions" 
          :key="session.id"
          class="session-item"
          :class="{ 'active': route.params.sessionId === session.id }"
          @click="loadChat(session.id)"
        >
          <p class="session-name">{{ session.title || '未命名对话' }}</p>
          <span class="session-time">{{ formatTime(session.created_at) }}</span>
        </li>
      </ul>
    </div>
  </aside>
</template>

<script setup>
import { onMounted } from 'vue';
import { useChatStore } from '@/stores/chat';
import { useRouter, useRoute } from 'vue-router';

const chatStore = useChatStore();
const router = useRouter();
const route = useRoute();

onMounted(() => {
  chatStore.fetchSessionList();
});

const startNewChat = () => {
  chatStore.startNewChat();
  router.push('/chat');
};

const loadChat = (sessionId) => {
  router.push(`/chat/${sessionId}`);
};

const formatTime = (timeStr) => {
  if (!timeStr) return '';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};
</script>

<style scoped>
.chat-history-sidebar { display: flex; flex-direction: column; height: 100%; background-color: #fdfdfd; border-right: 1px solid #e0e0e0; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; border-bottom: 1px solid #eee; flex-shrink: 0; }
.logo-link { text-decoration: none; display: flex; align-items: center; }
.logo-icon { width: 40px; height: 40px; background: linear-gradient(45deg, #FFA726, #FFD54F); color: white; display: grid; place-items: center; font-size: 1.5rem; font-weight: bold; border-radius: 10px; margin-right: 0.8rem; }
.logo-text { font-size: 1.5rem; font-weight: 600; margin: 0; color: #333; }
.new-chat-btn { background: #FFA726; color: white; border: none; width: 32px; height: 32px; border-radius: 50%; font-size: 1.8rem; line-height: 32px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.history-section { flex-grow: 1; overflow-y: auto; }
.history-title { font-size: 0.8rem; text-transform: uppercase; color: #999; margin: 1.5rem 1rem 0.5rem; }
.session-list { list-style: none; padding: 0 0.5rem; margin: 0; }
.session-item { display: block; padding: 0.8rem 1rem; text-decoration: none; color: #333; border-radius: 8px; cursor: pointer; }
.session-item:hover { background-color: #f0f0f0; }
.session-item.active { background-color: #FFF8E1; font-weight: 600; }
.session-name { margin: 0 0 0.25rem 0; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.session-time { font-size: 0.75rem; color: #999; }
.status-info { text-align: center; padding: 1rem; color: #999; }
</style>