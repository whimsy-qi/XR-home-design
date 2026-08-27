<template>
  <div class="local-model-section">
    <h3 class="upload-title">上传新的家具模型</h3>
    <form @submit.prevent="handleUpload">
      <div class="form-group">
        <label for="modelName">模型名称:</label>
        <input type="text" id="modelName" v-model="modelName" placeholder="请输入模型名称" required>
      </div>

      <div class="form-group">
        <label for="modelDescription">模型描述:</label>
        <textarea id="modelDescription" v-model="modelDescription" placeholder="请输入模型描述"></textarea>
      </div>

      <div class="form-group">
        <label for="modelFile">选择文件 (FBX/GLB/OBJ):</label>
        <input type="file" ref="fileInput" id="modelFile" accept=".fbx,.glb,.obj" @change="handleFileSelected">
        <span v-if="selectedFileName" class="file-info">
          {{ selectedFileName }} ({{ fileType || '未知类型' }})
        </span>
      </div>

      <button type="submit" class="upload-btn" :disabled="!modelName || !selectedFile">
        开始上传
      </button>

      <!-- 上传进度显示 -->
      <div v-if="uploadProgress > 0 && uploadProgress < 100" class="progress-bar">
        上传中：{{ uploadProgress }}%
      </div>
      <div v-if="uploadProgress === 100" class="progress-bar done">
        上传完成！
      </div>
    </form>

    <div v-if="uploadError" class="error-message">
      上传失败: {{ uploadError }}
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      modelName: '',
      modelDescription: '',
      selectedFile: null,
      selectedFileName: '',
      uploadError: '',
      fileType: '',
      uploadProgress: 0,
      presignUrl: '',
      ossPath: ''
    };
  },
  methods: {
    handleFileSelected(event) {
      this.selectedFile = event.target.files[0];
      if (!this.selectedFile) return;

      this.selectedFileName = this.selectedFile.name;
      this.fileType = this.selectedFile.type || this.getMimeTypeByExtension(this.selectedFileName);
      console.log('选择的文件类型:', this.fileType);
    },

    getMimeTypeByExtension(fileName) {
      const extension = fileName.split('.').pop().toLowerCase();
      const mimeTypeMap = {
        'obj': 'model/obj',
        'fbx': 'model/fbx',
        'glb': 'model/gltf-binary',
        'gltf': 'model/gltf+json',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'txt': 'text/plain'
      };
      return mimeTypeMap[extension] || 'application/octet-stream';
    },

    async handleUpload() {
      if (!this.modelName || !this.selectedFile) {
        this.uploadError = '请填写模型名称并选择文件';
        return;
      }

      try {
        this.uploadProgress = 0;
        this.uploadError = '';
        const formData = new FormData();

        formData.append('file_name', this.selectedFile.name);
        formData.append('file_type', this.fileType);
        formData.append('file', this.selectedFile);
        formData.append('name', this.modelName);
        formData.append('description', this.modelDescription || '');
        formData.append('asset_type', 'FURNITURE');

        // 1. 请求后端生成预签名URL
        const backendUrl = 'http://localhost:8000/api/THIS-IS-A-UNIQUE-TEST-URL-FOR-UPLOAD/';
        const presignResponse = await axios.post(backendUrl, formData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.lengthComputable) {
              const backendProgress = Math.round((progressEvent.loaded / progressEvent.total) * 30);
              this.uploadProgress = backendProgress;
            }
          }
        });

        const { presigned_url, file_url, oss_path, error } = presignResponse.data;
        if (error) throw new Error(error);
        if (!presigned_url) throw new Error('后端未返回预签名URL');

        console.log('预签名URL生成成功:', presigned_url);
        console.log('OSS存储路径:', oss_path);

        // 2. 使用预签名URL直传OSS
        const file = formData.get('file');
        await axios.put(presigned_url, file, {
          headers: {
            'Content-Type': this.fileType,
            'Content-Disposition': `attachment; filename=${encodeURIComponent(this.selectedFile.name)}`
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.lengthComputable) {
              const ossProgress = Math.round((progressEvent.loaded / progressEvent.total) * 70) + 30;
              this.uploadProgress = Math.min(ossProgress, 100);
              console.log(`OSS直传进度: ${this.uploadProgress}%`);
            }
          }
        });

        console.log('文件直传OSS成功');

        // 3. 通知后端完成上传，创建资产记录
        const confirmUrl = 'http://localhost:8000/api/assets/finalize-asset-upload-operation/';
        console.log('发送确认请求的数据:', {
          oss_path,
          file_url,
          name: this.modelName,
          description: this.modelDescription,
          asset_type: 'FURNITURE'
        });
        const confirmResponse = await axios.post(confirmUrl, {
          oss_path,
          file_url,
          name: this.modelName,
          description: this.modelDescription,
          asset_type: 'FURNITURE'
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`

          }
        });
        console.log("confirmResponse---"+JSON.stringify(confirmResponse));
        if (confirmResponse.status === 201) {
          console.log('后端确认上传完成');
          this.resetForm();
        } else {
          throw new Error('后端确认失败');
        }
      } catch (error) {
        console.error('上传全流程失败:', error);
        this.uploadError = error.message || '上传失败，请检查网络或重试';
        this.uploadProgress = 0;
        this.presignUrl = '';
      }
    },

    resetForm() {
      this.modelName = '';
      this.modelDescription = '';
      this.selectedFile = null;
      this.selectedFileName = '';
      this.fileType = '';
      this.uploadProgress = 0;
      this.presignUrl = '';
      this.ossPath = '';
    }
  }
};
</script>

<style scoped>
.local-model-section {
  background-color: #fff;
  padding: 50px;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  width: 800px;
  max-width: none;
}

.upload-title {
  text-align: center;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 30px;
}

.form-group label {
  display: block;
  margin-bottom: 10px;
  font-weight: 500;
  color: #333;
  font-size: 18px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 15px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 18px;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #fff9e5;
}

.file-selector {
  display: flex;
  align-items: center;
  gap: 15px;
}

.file-selector input[type="file"] {
  width: 100%;
  cursor: pointer;
  appearance: none;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 15px;
  background-color: #f9fafc;
  color: #333;
  font-size: 18px;
  height: 50px;

}

.file-selector input[type="file"]::-webkit-file-upload-button {
  display: none;
}

.file-info {
  color: #333;
  font-size: 18px;

}

.upload-btn {
  padding: 15px 20px;
  background-color: #FFA726;
  color: #111111;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  width: 100%;
  margin-top: 20px;
}

.upload-btn:hover {
  background-color: #FB8C00;
}

.error-message {
  color: #f56c6c;
  margin-top: 10px;
  font-size: 14px;
  text-align: center;
}

.back-btn {
  padding: 15px 20px;
  background-color: #ccc;
  color: #333;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  margin-top: 10px;
  width: 100%;
}

.progress-bar {
  height: 20px;
  background-color: #f0f0f0;
  border-radius: 4px;
  margin-top: 10px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background-color: #f3e227;
  transition: width 0.3s;
}

.success-message {
  color: #67c23a;
  margin-top: 10px;
  text-align: center;
}
</style>