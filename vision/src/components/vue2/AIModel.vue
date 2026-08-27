<template>
  <div>

    <!-- 水平排列的两个主要模块 -->
    <div class="horizontal-container">
      <!-- 图生3D模型模块 -->
      <div class="container image-to-3d">
        <h2>1. 单图像生成3D模型</h2>
        <label for="sourceImageFile">选择源图片:</label>
        <input type="file" id="sourceImageFile" accept="image/png, image/jpeg, image/webp" @change="handleImageFileChange">

        <label for="img23d_assetName">资产名称 (可选):</label>
        <input type="text" id="img23d_assetName" placeholder="例如: AI Sofa from Image" v-model="img23d.assetName">

        <label for="img23d_assetDescription">资产描述 (可选):</label>
        <input type="text" id="img23d_assetDescription" placeholder="例如: AI generated sofa based on an uploaded image." v-model="img23d.assetDescription">

        <label for="img23d_aiModel">Meshy AI 模型 (可选):</label>
        <select id="img23d_aiModel" v-model="img23d.aiModel">
          <option value="meshy-4" selected>meshy-4</option>
          <option value="meshy-5">meshy-5</option>
        </select>

        
        <button @click="generateImageTo3D">提交图像生成3D任务</button>
        <div id="img23d_output" class="output" :class="{ error: img23dOutput.isError, success: !img23dOutput.isError }">
        </div>
      </div>

      <!-- 文本生成3D模型模块 -->
      <div class="container text-to-3d">
        <h2>2. 文本生成3D模型</h2>
        <label for="textPrompt">文本提示:</label>
        <textarea id="textPrompt" rows="2" placeholder="例如: A comfortable wooden armchair with soft cushions" v-model="txt23d.prompt"></textarea>

        <label for="txt23d_assetName">资产名称 (可选):</label>
        <input type="text" id="txt23d_assetName" placeholder="例如: AI Armchair from Text" v-model="txt23d.assetName">

        <label for="txt23d_artStyle">艺术风格 (可选):</label>
        <select id="txt23d_artStyle" v-model="txt23d.artStyle">
          <option value="realistic" selected>Realistic (写实)</option>
          <option value="sculpture">Sculpture (雕塑)</option>
        </select>

        <label for="txt23d_targetPolycount">目标面数 (可选):</label>
        <input type="number" id="txt23d_targetPolycount" v-model="txt23d.targetPolycount">
    
        <button @click="generateTextTo3D">提交文本生成3D任务</button>
        <div id="txt23d_output" class="output" :class="{ error: txt23dOutput.isError, success: !txt23dOutput.isError }">
        </div>
      </div>
    </div>
    
    <!-- AI任务追踪模块放在最下面 -->
    <div class="container task-tracker">
      <h3>AI任务追踪</h3>
      <div id="tasksStatus">
        <template v-if="Object.keys(activeTasks).length === 0">
          无任务进行中...
        </template>
        <template v-else>
          <ul>
            <li v-for="(task, taskId) in activeTasks" :key="taskId" class="task-item">
              <strong>类型:</strong> {{ task.type }}<br>
              <strong>进度:</strong> {{ task.progress || 0 }}%
            </li>
          </ul>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AIModelGenerator',
  data() {
    return {
      API_BASE_URL: "http://127.0.0.1:8000/api",
      accessToken: localStorage.getItem('access_token') || '', // 直接从localStorage获取token
      sourceImageFile: null,
      activeTasks: {},
      
      // 图像生成3D相关数据
      img23d: {
        assetName: '',
        assetDescription: '',
        aiModel: 'meshy-4',
        enablePbr: true,
        shouldRemesh: true,
        shouldTexture: true
      },
      img23dOutput: {
        message: '',
        isError: false
      },
      
      // 文本生成3D相关数据
      txt23d: {
        prompt: '',
        assetName: '',
        assetDescription: '',
        artStyle: 'realistic',
        aiModel: 'meshy-4',
        negativePrompt: 'low quality, low poly, ugly, deformed, broken',
        targetPolycount: 50000,
        enablePbr: true,
        texturePrompt: ''
      },
      txt23dOutput: {
        message: '',
        isError: false
      }
    }
  },
  methods: {
    handleImageFileChange(event) {
      this.sourceImageFile = event.target.files[0];
    },
    
    displayOutput(element, data, isError = false) {
      if (element === 'img23d') {
        this.img23dOutput.message = JSON.stringify(data, null, 2);
        this.img23dOutput.isError = isError;
      } else if (element === 'txt23d') {
        this.txt23dOutput.message = JSON.stringify(data, null, 2);
        this.txt23dOutput.isError = isError;
      }
    },
    
    async generateImageTo3D() {
      if (!this.accessToken) {
        alert("未找到Access Token，请确保用户已登录!");
        return;
      }
      
      this.displayOutput('img23d', { message: "正在提交任务..." });
      
      if (!this.sourceImageFile) {
        this.displayOutput('img23d', { error: "请选择源图片!" }, true);
        return;
      }
      
      const formData = new FormData();
      formData.append('source_image', this.sourceImageFile);
      formData.append('name', this.img23d.assetName || `AI Image3D - ${this.sourceImageFile.name}`);
      formData.append('description', this.img23d.assetDescription || `AI generated 3D model from ${this.sourceImageFile.name}.`);
      formData.append('ai_model', this.img23d.aiModel);
      formData.append('enable_pbr', this.img23d.enablePbr.toString());
      formData.append('should_remesh', this.img23d.shouldRemesh.toString());
      formData.append('should_texture', this.img23d.shouldTexture.toString());
      
      try {
        const response = await fetch(`${this.API_BASE_URL}/ai/image-to-3d/`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${this.accessToken}` },
          body: formData
        });
        const data = await response.json();
        if (!response.ok) {
          throw data;
        }
        this.displayOutput('img23d', data, false);
        if (data.celery_task_id) {
          this.trackTask(data.celery_task_id, data.ai_task_tracker_id, "Image-to-3D");
        }
      } catch (error) {
        console.error("Image-to-3D error:", error);
        this.displayOutput('img23d', error, true);
      }
    },
    
    async generateTextTo3D() {
      if (!this.accessToken) {
        alert("未找到Access Token，请确保用户已登录!");
        return;
      }
      
      this.displayOutput('txt23d', { message: "正在提交任务..." });
      
      if (!this.txt23d.prompt) {
        this.displayOutput('txt23d', { error: "请输入文本提示!" }, true);
        return;
      }
      
      const payload = {
        prompt: this.txt23d.prompt,
        name: this.txt23d.assetName || `AI Text3D - ${this.txt23d.prompt.substring(0,20)}`,
        description: this.txt23d.assetDescription || `AI generated 3D model from text: ${this.txt23d.prompt}.`,
        art_style: this.txt23d.artStyle,
        negative_prompt: this.txt23d.negativePrompt,
        should_remesh: this.img23d.shouldRemesh,
        ai_model: this.txt23d.aiModel,
        target_polycount: parseInt(this.txt23d.targetPolycount) || 50000,
        enable_pbr: this.txt23d.enablePbr,
        texture_prompt: this.txt23d.texturePrompt || this.txt23d.prompt
      };
      
      try {
        const response = await fetch(`${this.API_BASE_URL}/ai/text-to-3d/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.accessToken}`
          },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
          throw data;
        }
        this.displayOutput('txt23d', data, false);
        if (data.celery_task_id) {
          this.trackTask(data.celery_task_id, data.ai_task_tracker_id, "Text-to-3D");
        }
      } catch (error) {
        console.error("Text-to-3D error:", error);
        this.displayOutput('txt23d', error, true);
      }
    },
    
    trackTask(celeryTaskId, backendTaskId, taskType) {
      this.$set(this.activeTasks, celeryTaskId, { 
        backendTaskId: backendTaskId, 
        status: 'SUBMITTED', 
        progress: 0, 
        type: taskType 
      });
      
      const intervalId = setInterval(async () => {
        try {
          if (this.activeTasks[celeryTaskId] && 
              this.activeTasks[celeryTaskId].status !== 'COMPLETED' && 
              this.activeTasks[celeryTaskId].status !== 'FAILED') {
            
            this.activeTasks[celeryTaskId].progress = Math.min(100, (this.activeTasks[celeryTaskId].progress || 0) + 5);
            
            if(this.activeTasks[celeryTaskId].progress < 20) {
              this.activeTasks[celeryTaskId].status = "CELERY_RECEIVED";
            } else if(this.activeTasks[celeryTaskId].progress < 80) {
              this.activeTasks[celeryTaskId].status = "AI_API_PENDING";
            } else if(this.activeTasks[celeryTaskId].progress < 95) {
              this.activeTasks[celeryTaskId].status = "UPLOADING_TO_OSS";
            } else if(this.activeTasks[celeryTaskId].progress < 100) {
              this.activeTasks[celeryTaskId].status = "TRIGGERING_THUMBNAIL";
            }

            if (this.activeTasks[celeryTaskId].progress >= 100) {
              this.activeTasks[celeryTaskId].status = 'COMPLETED (Mock)';
              clearInterval(intervalId);
            }
          } else {
            clearInterval(intervalId);
          }
        } catch (error) {
          console.error(`Error polling task ${celeryTaskId}:`, error);
          this.activeTasks[celeryTaskId].status = 'POLLING_ERROR';
          clearInterval(intervalId);
        }
      }, 5000);
    }
  },
  mounted() {
    // 初始化数据
    this.txt23d.negativePrompt = 'low quality, low poly, ugly, deformed, broken';
    this.txt23d.targetPolycount = 50000;
    
    // 检查是否有token
    if (!this.accessToken) {
      console.warn("未找到access_token，请确保用户已登录");
    }
  }
}
</script>

<style scoped>
body { 
  font-family: sans-serif; 
  margin: 20px; 
  background-color: #f4f4f4; 
  color: #333; 
}

/* 新增的水平排列容器样式 */
.horizontal-container {
  display: flex;
  gap: 20px;
  min-width: 1000px;
  margin-bottom: 20px;
}

/* 调整容器宽度以适应水平排列 */
.horizontal-container > .container {
  flex: 1;
  min-width: 0; /* 防止内容溢出 */
}

.container { 
  background-color: #fff; 
  padding: 20px; 
  border-radius: 8px; 
  box-shadow: 0 0 10px rgba(0,0,0,0.1); 
  margin-bottom: 20px; 
}

/* 任务追踪容器单独样式 */
.container.task-tracker {
  width: 100%;
}

h2, h3 { 
  color: #555; 
}
label { 
  display: block; 
  margin-top: 10px; 
  font-weight: bold; 
}
input[type="text"], 
input[type="password"], 
textarea, 
input[type="file"], 
input[type="number"], 
select {
  width: calc(100% - 22px); 
  padding: 10px; 
  margin-top: 5px; 
  margin-bottom: 15px;
  border: 1px solid #ddd; 
  border-radius: 4px; 
  box-sizing: border-box;
}
button {
  background-color: #FFA726; 
  color: white; 
  padding: 10px 15px;
  border: none; 
  border-radius: 4px; 
  cursor: pointer; 
  font-size: 16px; 
  margin-right: 10px;
}
button:hover { 
  background-color: #FB8C00; 
}

.task-item { 
  border-bottom: 1px solid #eee; 
  padding-bottom: 10px; 
  margin-bottom: 10px; 
}
.task-item:last-child { 
  border-bottom: none; 
}
.hidden { 
  display: none; 
}

/* 响应式设计 - 在小屏幕上恢复垂直排列 */
@media (max-width: 768px) {
  .horizontal-container {
    flex-direction: column;
  }
}
</style>