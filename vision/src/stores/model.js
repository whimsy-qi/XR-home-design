import { defineStore } from 'pinia';
import apiClient from '@/api/axios';

export const useModelStore = defineStore('model', {
  state: () => ({
    taskId: null,
    taskStatus: 'idle', // idle, loading, success, error
    error: null,
    progress: 0,
  }),

  actions: {
    // 动作1: 从文本生成3D模型
    async generateFromText(formData) {
      this.reset();
      this.taskStatus = 'loading';
      try {
        const response = await apiClient.post('/api/ai/3d/text-to-3d/', formData);
        this.taskId = response.data.ai_task_tracker_id; // 后端返回的是 ai_task_tracker_id
        this.pollModelTask();
      } catch (err) {
        this.taskStatus = 'error';
        this.error = err.response?.data?.error || '启动文生3D任务失败。';
      }
    },

    // 动作2: 从图像生成3D模型
    async generateFromImage(formDataObject) {
      this.reset();
      this.taskStatus = 'loading';
      try {
        const response = await apiClient.post('/api/ai/3d/image-to-3d/', formDataObject, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        this.taskId = response.data.ai_task_tracker_id;
        this.pollModelTask();
      } catch (err) {
        this.taskStatus = 'error';
        this.error = err.response?.data?.error || '启动图生3D任务失败。';
      }
    },

    // 动作3: 统一轮询任务状态
    pollModelTask() {
      const intervalId = setInterval(async () => {
        if (!this.taskId) {
          clearInterval(intervalId);
          return;
        }
        try {
          const response = await apiClient.get(`/api/ai/tasks/${this.taskId}/`);
          const task = response.data;
          this.progress = task.progress;

          if (task.status === 'COMPLETED') {
            clearInterval(intervalId);
            this.taskStatus = 'success';
          } else if (task.status === 'FAILED') {
            clearInterval(intervalId);
            this.taskStatus = 'error';
            this.error = task.error_message || '3D模型生成失败。';
          }
        } catch (err) {
          clearInterval(intervalId);
          this.taskStatus = 'error';
          this.error = '轮询任务状态时发生错误。';
        }
      }, 3000); 
    },
    
    reset() {
      this.taskId = null;
      this.taskStatus = 'idle';
      this.error = null;
      this.progress = 0;
    }
  },
});