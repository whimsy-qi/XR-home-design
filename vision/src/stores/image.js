import { defineStore } from 'pinia';
import apiClient from '@/api/axios';

export const useImageStore = defineStore('image', {
  state: () => ({
    // --- 文生图阶段的状态 ---
    taskId: null,
    taskStatus: 'idle', // idle, loading, success, error
    generatedImages: [],
    error: null,
    progress: 0,

    // --- 图像分割阶段的状态 ---
    segmentTaskId: null,
    segmentTaskStatus: 'idle', // idle, loading, success, error
    segmentationResultUrl: null,
    segmentationError: null,

    // --- 【新增】分割图生3D阶段的状态 ---
    model3dTaskId: null,
    model3dTaskStatus: 'idle', // idle, loading, success, error
    model3dError: null,
    model3dResult: null,
  }),

  actions: {
    // 动作1: 启动文生图任务
    async generateImages(formData) {
      this.reset(); // 开始一次新的生成时，重置所有状态
      this.taskStatus = 'loading';

      try {
        const response = await apiClient.post('/api/ai/image/text-to-image/', formData);
        this.taskId = response.data.task_id;
        this.pollImageTask();
      } catch (err) {
        this.taskStatus = 'error';
        this.error = err.response?.data?.error || '启动图片生成任务失败。';
        console.error(err);
      }
    },

    // 动作2: 轮询文生图任务状态
    pollImageTask() {
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
            this.generatedImages = task.meshy_result_data.image_urls || [];
            this.taskStatus = 'success';
          } else if (task.status === 'FAILED') {
            clearInterval(intervalId);
            this.taskStatus = 'error';
            this.error = task.error_message || '图片生成失败。';
          }
        } catch (err) {
          clearInterval(intervalId);
          this.taskStatus = 'error';
          this.error = '轮询文生图任务时发生错误。';
          console.error(err);
        }
      }, 3000); 
    },

    // 动作3: 启动图像分割任务
      async startSegmentation(imageUrl, payload) {
      this.segmentTaskStatus = 'loading';
      this.segmentationError = null;
      this.segmentationResultUrl = null;

      try {
        const response = await apiClient.post('/api/ai/segmentation/start/', {
          source_image_url: imageUrl,
          prompts: payload.points,      // 传入点
          box_prompts: payload.boxes,   // 传入框
        });
        this.segmentTaskId = response.data.task_id;
        this.pollSegmentationTask();
      } catch (err) {
        this.segmentTaskStatus = 'error';
        this.segmentationError = err.response?.data?.error || '启动分割任务失败。';
      }
    },

    // 动作4: 轮询分割任务状态
    pollSegmentationTask() {
      const intervalId = setInterval(async () => {
        if (!this.segmentTaskId) {
          clearInterval(intervalId);
          return;
        }
        try {
          const response = await apiClient.get(`/api/ai/tasks/${this.segmentTaskId}/`);
          const task = response.data;

          // 根据后端的任务状态，判断是否成功
          if (task.status === 'AWAITING_MASK_SELECTION' || task.status === 'COMPLETED') { 
            clearInterval(intervalId);
            this.segmentationResultUrl = task.meshy_result_data.segmented_url;
            this.segmentTaskStatus = 'success';
          } else if (task.status === 'FAILED') {
            clearInterval(intervalId);
            this.segmentTaskStatus = 'error';
            this.segmentationError = task.error_message || '分割失败。';
          }
        } catch (err) {
          clearInterval(intervalId);
          this.segmentTaskStatus = 'error';
          this.segmentationError = '轮询分割任务时发生错误。';
          console.error(err);
        }
      }, 3000);
    },
       async generate3dFromCutout(sourceSegmentationTaskId) {
        this.model3dTaskStatus = 'loading';
        this.model3dError = null;
        this.model3dResult = null;

        try {
            const response = await apiClient.post('/api/ai/3d/generate-from-cutout/', {
                source_task_id: sourceSegmentationTaskId
            });
            this.model3dTaskId = response.data.task_id;
            this.pollModel3dTask();
        } catch (err) {
            this.model3dTaskStatus = 'error';
            this.model3dError = err.response?.data?.error || '启动3D生成任务失败。';
        }
    },

    // --- 【新增】动作：轮询3D模型任务状态 ---
    pollModel3dTask() {
        const intervalId = setInterval(async () => {
            if (!this.model3dTaskId) {
              clearInterval(intervalId);
              return;
            }
            try {
              const response = await apiClient.get(`/api/ai/tasks/${this.model3dTaskId}/`);
              const task = response.data;

              if (task.status === 'COMPLETED') { 
                clearInterval(intervalId);
                this.model3dResult = task; // 保存整个任务结果
                this.model3dTaskStatus = 'success';
              } else if (task.status === 'FAILED') {
                clearInterval(intervalId);
                this.model3dTaskStatus = 'error';
                this.model3dError = task.error_message || '3D模型生成失败。';
              }
            } catch (err) {
              clearInterval(intervalId);
              this.model3dTaskStatus = 'error';
              this.model3dError = '轮询3D任务时发生错误。';
            }
        }, 3000);
    },
    
    // 动作5: 重置整个store，用于开始一次全新的创作
    reset() {
        this.taskId = null;
        this.taskStatus = 'idle';
        this.generatedImages = [];
        this.error = null;
        this.progress = 0;
        
        this.segmentTaskId = null;
        this.segmentTaskStatus = 'idle';
        this.segmentationResultUrl = null;
        this.segmentationError = null;
        
           // 【新增】重置3D模型状态
        this.model3dTaskId = null;
        this.model3dTaskStatus = 'idle';
        this.model3dError = null;
        this.model3dResult = null;
        
    }
  },
});