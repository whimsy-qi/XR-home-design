import { defineStore } from 'pinia';
import apiClient from '@/api/axios';

export const usePlanStore = defineStore('plan', {
  state: () => ({
    taskId: null,
    taskStatus: 'idle', // idle, loading, success, error
    planResult: null,
    error: null,
    progress: 0,
  }),

  actions: {
    async generatePlan(formData) {
      this.taskStatus = 'loading';
      this.error = null;
      this.planResult = null;
      this.progress = 0;

      try {
        // 【核心修正】在请求路径前加上 /api 前缀
        const response = await apiClient.post('/api/ai/plan/generate/', formData);
        
        this.taskId = response.data.task_id;
        this.pollPlanStatus(); // 开始轮询
      } catch (err) {
        this.taskStatus = 'error';
        this.error = err.response?.data?.error || '启动方案生成任务失败。';
        console.error(err);
      }
    },

    pollPlanStatus() {
      const intervalId = setInterval(async () => {
        if (!this.taskId) {
          clearInterval(intervalId);
          return;
        }
        try {
          // 【核心修正】轮询的路径也需要加上 /api 前缀
          const response = await apiClient.get(`/api/ai/tasks/${this.taskId}/`);
          const task = response.data;
          
          // 假设后端任务会更新自己的progress字段
          this.progress = task.progress || this.progress; 

          if (task.status === 'COMPLETED') {
            clearInterval(intervalId);
            // 任务完成后，从任务记录中获取关联的方案ID
            const planId = task.generated_decor_plan;
            if (planId) {
                // 【核心修正】获取方案详情的路径也需要加上 /api 前缀
                const planResponse = await apiClient.get(`/api/ai/plan/${planId}/`);
                this.planResult = planResponse.data;
                this.taskStatus = 'success';
            } else {
                throw new Error("任务完成，但未找到生成的方案ID。");
            }
          } else if (task.status === 'FAILED') {
            clearInterval(intervalId);
            this.taskStatus = 'error';
            this.error = task.error_message || '方案生成失败。';
          }
        } catch (err) {
          clearInterval(intervalId);
          this.taskStatus = 'error';
          this.error = err.message || '轮询任务状态时发生错误。';
          console.error(err);
        }
      }, 3000); // 每3秒轮询一次
    },
    
    reset() {
        this.taskId = null;
        this.taskStatus = 'idle';
        this.planResult = null;
        this.error = null;
        this.progress = 0;
    }
  },
});