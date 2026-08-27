import { defineStore } from 'pinia';
import apiClient from '@/api/axios';
import { useRouter } from 'vue-router';

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],             // 存储历史会话列表
    activeSession: null,      // 存储当前正在进行的会话对象（包含消息历史）
    isLoadingList: false,     // 是否正在加载会话列表
    isLoadingMessages: false, // 是否正在加载单个会话的消息
    isSendingMessage: false,  // 是否正在发送消息并等待回复
    error: null,              // 存储错误信息
  }),

  actions: {
    /**
     * 从后端获取所有历史会话的列表。
     */
    async fetchSessionList() {
      this.isLoadingList = true;
      this.error = null;
      try {
        const response = await apiClient.get('/api/ai/chat/sessions/');
        this.sessions = response.data.results; // 假设后端分页，从results获取
      } catch (err) {
        this.error = '无法加载历史对话。';
        console.error("获取会话列表失败:", err);
      } finally {
        this.isLoadingList = false;
      }
    },

    /**
     * 根据会话ID，从后端获取单个会话的详细信息（包含完整的消息历史）。
     * @param {string} sessionId - 要加载的会话ID。
     */
    async loadSession(sessionId) {
      if (!sessionId) {
        this.activeSession = null;
        return;
      }
      this.isLoadingMessages = true;
      this.activeSession = null;
      this.error = null;
      try {
        const response = await apiClient.get(`/api/ai/chat/sessions/${sessionId}/`);
        this.activeSession = response.data;
      } catch (err) {
        this.error = '无法加载对话内容。';
        console.error(`加载会话 ${sessionId} 失败:`, err);
      } finally {
        this.isLoadingMessages = false;
      }
    },

    /**
     * 发送一条新消息给后端。
     * @param {string} message - 用户输入的消息文本。
     */
    async sendMessage(message) {
      if (!message.trim()) return;
      
      this.isSendingMessage = true;

      // 如果当前没有活跃会话，说明是新对话的开始
      if (!this.activeSession) {
        // 创建一个临时的会话对象，用于立即在UI上显示用户消息
        this.activeSession = { id: null, title: '新的对话', history: [] };
      }
      this.activeSession.history.push({ role: 'user', content: message });

      try {
        const response = await apiClient.post('/api/ai/chat/send_message/', {
          message: message,
          session_id: this.activeSession.id, // 如果是新对话，id为null，后端会自动创建
        });

        const { task_id, session_id } = response.data;

        // 如果是新对话，后端会返回新的session_id，我们更新它
        if (!this.activeSession.id) {
          this.activeSession.id = session_id;
        }

        // 开始轮询这个新任务的结果
        this.pollTaskResult(task_id, session_id);

      } catch (err) {
        this.error = '消息发送失败。';
        this.activeSession.history.push({ role: 'assistant', content: `抱歉，发送失败: ${err.message || '未知错误'}`});
        this.isSendingMessage = false;
      }
    },

    /**
     * 轮询一个AI任务的状态，直到它完成或失败。
     * @param {string} taskId - 要轮询的任务ID。
     * @param {string} sessionId - 任务完成后需要刷新的会话ID。
     */
    pollTaskResult(taskId, sessionId) {
      const intervalId = setInterval(async () => {
        try {
          const response = await apiClient.get(`/api/ai/tasks/${taskId}/`);
          const task = response.data;

          if (task.status === 'COMPLETED' || task.status === 'FAILED') {
            clearInterval(intervalId);
            this.isSendingMessage = false;
            
            // 任务完成后，重新加载整个会话，以获取AI的最终回复
            await this.loadSession(sessionId);

            // 检查侧边栏的会话列表是否包含这个新会话，如果不包含则刷新列表
            const isSessionInList = this.sessions.some(s => s.id === sessionId);
            if (!isSessionInList) {
              await this.fetchSessionList();
            }
          }
        } catch (error) {
          clearInterval(intervalId);
          this.isSendingMessage = false;
          console.error('轮询任务状态失败:', error);
          // 可以在这里给用户一个错误提示
          this.error = "获取AI回复失败。";
        }
      }, 3000); // 每3秒轮询一次
    },

    /**
     * 用于在UI上开始一个新聊天。
     */
    startNewChat() {
      this.activeSession = null;
    },
  },
});