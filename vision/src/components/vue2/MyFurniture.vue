<template>
  <div class="furniture-library">
    <!-- Search and filter section -->
    <div class="filter-section">

      <div class="home-arrow" @click="goToHome">
     <span class="arrow">&#171;</span>
     </div>
      <input type="text" v-model="searchQuery" @input="filterModels" placeholder="搜索模型..." class="search-input">
      <select v-model="categoryFilter" @change="filterModels" class="category-select">
        <option value="">所有类别</option>
        <option value="FURNITURE">家具</option>
        <option value="DECOR">装饰品</option>
        <option value="LIGHTING">照明</option>npm
        <option value="MATERIAL">材质</option>
      </select>

    </div>

    

    <!-- Model list -->
    <div class="model-list">
      <div v-for="model in filteredModels" :key="model.id" class="model-card" @click="openModelViewer(model)">
        <div class="model-thumbnail">
          <!-- <div v-if="model.isLoadingThumbnail" class="loading-placeholder">
            <div class="spinner"></div>
          </div> -->
          <img :src="model.thumbnail_url || defaultThumbnail" alt="模型缩略图" class="thumbnail"
            @load="model.isLoadingThumbnail = false" @error="handleImageError(model)" />
        </div>
        <div class="model-info">
          <h3 class="model-name">{{ model.name }}</h3>
          <p class="model-desc">{{ model.description }}</p>
          <div class="model-meta">
            <span class="model-type">{{ getAssetTypeText(model.asset_type) }}</span>
            <span class="model-date">{{ formatDate(model.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="models.length === 0 && !isLoadingModels" class="empty-state">
        <img src="https://picsum.photos/200/150?grayscale" alt="空状态" class="empty-image">
        <p>暂无可用模型，请稍后再试</p>
      </div>

      <!-- Loading state -->
      <div v-if="isLoadingModels" class="loading-state">
        <div class="spinner large"></div>
        <p>正在加载模型...</p>
      </div>
    </div>

    <!-- 3D Model Viewer Modal -->
    <div v-if="isModelViewerOpen" class="model-viewer-modal" @click.self="closeModelViewer">
      <div class="modal-content">
        <div class="model-header">
          <h2>{{ currentModel?.name || '模型查看器' }}</h2>
          <button class="close-btn" @click="closeModelViewer">×</button>
        </div>
        <div class="model-preview-container">
          <canvas ref="modelContainer" class="model-container"></canvas>

          <!-- Status indicators -->
          <div v-if="modelLoadingError" class="status-overlay error">
            <div class="status-content">
              <h3>模型加载失败</h3>
              <p>{{ modelLoadingError }}</p>
              <button @click="retryLoadModel">重试</button>
            </div>
          </div>
          <div v-else-if="isModelLoading" class="status-overlay loading">
            <div class="status-content">
              <div class="spinner large"></div>
              <p>{{ loadProgressText }}</p>
            </div>
          </div>
        </div>
        <div class="model-controls">
          <button @click="resetCamera" :disabled="!modelLoaded">重置视角</button>
          <button @click="toggleAutoRotate" :disabled="!modelLoaded">
            {{ isAutoRotating ? '停止旋转' : '自动旋转' }}
          </button>
          <button @click="downloadModel" :disabled="!currentModel">
            下载模型
          </button>
          <div class="model-format-info" v-if="currentModel">
            格式: {{ currentModel.file_url.split('.').pop().toUpperCase() }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import * as BABYLON from 'babylonjs';
import 'babylonjs-loaders';
import apiClient from '@/api/axios';
export default {
  data() {
    return {
      models: [],
      filteredModels: [],
      searchQuery: '',
      categoryFilter: '',
      isLoadingModels: false,
      defaultThumbnail: 'https://picsum.photos/300/200?grayscale&blur=2',
      assetTypeMap: {
        'FURNITURE': '家具',
        'DECOR': '装饰品',
        'LIGHTING': '照明',
        'MATERIAL': '材质',
        'OTHER': '其他'
      },
      isModelViewerOpen: false,
      currentModel: null,
      engine: null,
      scene: null,
      camera: null,
      modelMesh: null,
      isAutoRotating: false,
      modelLoaded: false,
      isModelLoading: false,
      modelLoadingError: null,
      loadProgress: 0,
      loadProgressText: '准备加载...',
      sceneReady: false,
      autoRotationBehavior: null,
      shadowGenerator: null,
      resizeObserver: null
    };
  },

  mounted() {
    this.fetchModels();
  },

  beforeUnmount() {
    this.disposeViewer();
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  },

  watch: {
    isModelViewerOpen(newValue) {
      if (newValue) {
        this.resetLoadState();
        this.$nextTick(() => {
          this.initViewer();
        });
      } else {
        this.disposeViewer();
      }
    }
  },

  methods: {
    async fetchModels() {
      this.isLoadingModels = true;
      try {
        const response = await apiClient.get('/api/assets/');
        this.models = response.data.map(model => ({
          ...model,
          isLoadingThumbnail: true,
          file_extension: model.file_url.split('.').pop().toLowerCase()
        }));
        this.filteredModels = [...this.models];
      } catch (error) {
        console.error('获取模型列表失败:', error);
        alert('无法加载模型，请稍后重试');
      } finally {
        this.isLoadingModels = false;
      }
    },

    filterModels() {
      this.filteredModels = this.models.filter(model => {
        const matchesSearch = model.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
          (model.description || '').toLowerCase().includes(this.searchQuery.toLowerCase());
        const matchesCategory = !this.categoryFilter || model.asset_type === this.categoryFilter;
        return matchesSearch && matchesCategory;
      });
    },

    handleImageError(model) {
      model.thumbnail_url = this.defaultThumbnail;
      model.isLoadingThumbnail = false;
    },

    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN');
    },

    getAssetTypeText(assetType) {
      return this.assetTypeMap[assetType] || assetType;
    },

    openModelViewer(model) {
      this.currentModel = model;
      this.isModelViewerOpen = true;
    },
    goToHome() {

      this.$router.push({ name: 'PersonRoom' });
    },

    initViewer() {
      const container = this.$refs.modelContainer;
      if (!container) return;

      try {
        // Initialize Babylon.js engine
        this.engine = new BABYLON.Engine(container, true, {
          preserveDrawingBuffer: true,
          stencil: true
        });

        // Create scene
        this.scene = new BABYLON.Scene(this.engine);
        this.scene.clearColor = new BABYLON.Color4(0.95, 0.95, 0.95, 1);

        // Setup camera
        this.setupCamera(container);
        
        // Setup lighting
        this.setupLighting();
        

        
        // Setup environment
        this.setupEnvironment();

        // Start render loop
        this.engine.runRenderLoop(() => {
          this.scene.render();
        });

        // Handle resize
        this.setupResizeHandler();

        this.sceneReady = true;
        this.loadModel();
      } catch (error) {
        console.error('初始化失败:', error);
        this.modelLoadingError = '初始化渲染引擎失败: ' + error.message;
        this.isModelLoading = false;
      }
    },

    setupCamera(container) {
      this.camera = new BABYLON.ArcRotateCamera(
        "camera",
        -Math.PI / 2,
        Math.PI / 2.5,
        5,
        BABYLON.Vector3.Zero(),
        this.scene
      );
      this.camera.attachControl(container, true);
      this.camera.lowerRadiusLimit = 1;
      this.camera.upperRadiusLimit = 20;
      this.camera.wheelDeltaPercentage = 0.01;
      this.camera.panningSensibility = 50;

      // Setup auto rotation behavior
      this.autoRotationBehavior = new BABYLON.AutoRotationBehavior();
      this.autoRotationBehavior.idleRotationSpeed = 0.5;
      this.autoRotationBehavior.idleRotationSpinupTime = 1000;
      this.autoRotationBehavior.idleRotationWaitTime = 2000;
      this.autoRotationBehavior.zoomStopsAnimation = true;
      this.camera.addBehavior(this.autoRotationBehavior);
    },

    setupLighting() {
      // Hemispheric light (ambient)
      const hemisphericLight = new BABYLON.HemisphericLight(
        "hemisphericLight",
        new BABYLON.Vector3(0, 1, 0),
        this.scene
      );
      hemisphericLight.intensity = 0.7;

      // Directional light (key light)
      const directionalLight = new BABYLON.DirectionalLight(
        "directionalLight",
        new BABYLON.Vector3(-1, -2, -1),
        this.scene
      );
      directionalLight.intensity = 0.8;
      directionalLight.position = new BABYLON.Vector3(5, 10, 5);

      // Shadow generator
      this.shadowGenerator = new BABYLON.ShadowGenerator(1024, directionalLight);
      this.shadowGenerator.useBlurExponentialShadowMap = true;
      this.shadowGenerator.blurKernel = 32;
    },


    setupEnvironment() {
      // Add some basic environment effects
      this.scene.ambientColor = new BABYLON.Color3(0.5, 0.5, 0.5);
      
      // Enable scene fog for better depth perception
      this.scene.fogMode = BABYLON.Scene.FOGMODE_EXP;
      this.scene.fogDensity = 0.01;
      this.scene.fogColor = this.scene.clearColor;
    },

    setupResizeHandler() {
      // Use ResizeObserver for better performance than window.resize
      this.resizeObserver = new ResizeObserver(() => {
        if (this.engine) {
          this.engine.resize();
        }
      });
      this.resizeObserver.observe(this.$refs.modelContainer);
    },

    async loadModel() {
      if (!this.sceneReady || !this.currentModel || !this.scene) return;

      try {
        this.isModelLoading = true;
        this.modelLoadingError = null;
        this.loadProgress = 0;
        this.loadProgressText = '准备加载模型...';

        const url = this.currentModel.file_url;
        const fileExtension = this.currentModel.file_extension;

        // Validate file extension
        if (!["obj", "fbx", "gltf", "glb"].includes(fileExtension)) {
          throw new Error(`不支持的模型格式: ${fileExtension}`);
        }

        // Clear previous model if exists
        if (this.modelMesh) {
          this.modelMesh.dispose();
          this.modelMesh = null;
        }

        // Prepare loading options
        const loadingOptions = {
          onProgress: (event) => {
            if (event.lengthComputable) {
              this.loadProgress = Math.round((event.loaded / event.total) * 100);
              this.loadProgressText = `加载中: ${this.loadProgress}%`;
            }
          },
          scene: this.scene
        };

        // Load the model based on its format
        let result;
        if (fileExtension === "obj") {
          result = await BABYLON.SceneLoader.ImportMeshAsync(
            "",
            "",
            url,
            this.scene,
            loadingOptions.onProgress
          );
        } else {
          // For other formats (gltf/glb/fbx)
          result = await BABYLON.SceneLoader.ImportMeshAsync(
            "",
            "",
            url,
            this.scene,
            loadingOptions.onProgress
          );
        }

        if (!result.meshes || result.meshes.length === 0) {
          throw new Error('模型加载成功，但未找到网格数据');
        }

        // Process loaded meshes
        this.modelMesh = result.meshes[0];
        this.setupModel(this.modelMesh);

        this.modelLoaded = true;
        this.loadProgressText = '加载完成';
        
        // Small delay to show completion before hiding loader
        setTimeout(() => {
          this.isModelLoading = false;
        }, 500);
      } catch (error) {
        console.error('加载模型失败:', error);
        this.modelLoadingError = `加载模型失败: ${error.message}`;
        this.isModelLoading = false;
      }
    },

    setupModel(mesh) {
      // Compute bounding box and center the model
      const boundingInfo = mesh.getHierarchyBoundingVectors(true);
      const size = boundingInfo.max.subtract(boundingInfo.min);
      const center = boundingInfo.max.add(boundingInfo.min).scale(0.5);

      // Calculate scale to fit the model in the view
      const maxDim = Math.max(size.x, size.y, size.z);
      const targetSize = 5; // Target size in world units
      const scale = targetSize / maxDim;

      // Apply transformations to all meshes
      mesh.getChildMeshes().forEach(childMesh => {
        childMesh.position = childMesh.position.subtract(center);
        childMesh.scaling = new BABYLON.Vector3(scale, scale, scale);
        
        // Enable shadows
        this.shadowGenerator.addShadowCaster(childMesh);
        
        // Setup basic material if none exists
        if (!childMesh.material) {
          const material = new BABYLON.StandardMaterial("defaultMaterial", this.scene);
          material.diffuseColor = new BABYLON.Color3(0.8, 0.8, 0.8);
          material.specularColor = new BABYLON.Color3(0.2, 0.2, 0.2);
          childMesh.material = material;
        }
      });

      // Position the root mesh
      mesh.position = new BABYLON.Vector3(0, -center.y * scale, 0);
      
      // Set camera target and radius
      this.camera.setTarget(mesh.position);
      this.camera.radius = maxDim * 1.5;
    },

    resetCamera() {
      if (this.camera && this.modelMesh) {
        this.camera.setTarget(this.modelMesh.position);
        this.camera.alpha = -Math.PI / 2;
        this.camera.beta = Math.PI / 2.5;
        this.camera.radius = this.modelMesh.getBoundingInfo().boundingBox.extendSizeWorld.length() * 1.5;
      }
    },

    toggleAutoRotate() {
      this.isAutoRotating = !this.isAutoRotating;
      if (this.autoRotationBehavior) {
        this.autoRotationBehavior.pause = !this.isAutoRotating;
      }
    },

    async downloadModel() {
      if (!this.currentModel?.file_url) {
        alert('无法下载模型：模型URL不存在');
        return;
      }

      try {
        const response = await fetch(this.currentModel.file_url);
        if (!response.ok) throw new Error('下载失败');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = this.currentModel.name || `model.${this.currentModel.file_extension}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('下载模型失败:', error);
        alert('下载模型失败，请稍后重试');
      }
    },

    closeModelViewer() {
      this.isModelViewerOpen = false;
    },

    disposeViewer() {
      // Dispose Babylon.js resources in reverse creation order
      if (this.modelMesh) {
        this.modelMesh.dispose();
        this.modelMesh = null;
      }
      
      if (this.shadowGenerator) {
        this.shadowGenerator.dispose();
        this.shadowGenerator = null;
      }
      
      if (this.scene) {
        this.scene.dispose();
        this.scene = null;
      }
      
      if (this.engine) {
        this.engine.dispose();
        this.engine = null;
      }
      
      this.camera = null;
      this.autoRotationBehavior = null;
      this.modelLoaded = false;
      this.sceneReady = false;
    },

    resetLoadState() {
      this.modelLoaded = false;
      this.isModelLoading = true;
      this.modelLoadingError = null;
      this.loadProgress = 0;
      this.loadProgressText = '准备加载...';
    },

    retryLoadModel() {
      this.resetLoadState();
      this.loadModel();
    }
  }
};
</script>

<style scoped>
.arrow {
  font-size: 24px; /* 调整箭头大小 */
  font-weight: bold; /* 可选：加粗 */
  line-height: 1; /* 确保垂直对齐 */
}
/* Base styles */
.furniture-library {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  font-family: 'Arial', sans-serif;
}

.filter-section {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.search-input:focus {
  border-color: #3498db;
  outline: none;
}

.category-select {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  background-color: white;
  cursor: pointer;
}

/* Model list styles */
.model-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.model-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.model-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.12);
}

.model-thumbnail {
  position: relative;
  height: 200px;
  background-color: #f8f9fa;
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 3px solid #3498db;
  animation: spin 1s linear infinite;
}

.large.spinner {
  width: 50px;
  height: 50px;
  border-width: 4px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.3s;
}

.thumbnail:hover {
  opacity: 0.9;
}

.model-info {
  padding: 16px;
  flex: 1;
}

.model-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.model-desc {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.model-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #888;
}

/* Empty and loading states */
.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
  text-align: center;
  grid-column: 1 / -1;
}

.empty-image {
  width: 100px;
  height: 100px;
  margin-bottom: 20px;
  opacity: 0.6;
}

.empty-state p,
.loading-state p {
  color: #666;
  margin-top: 15px;
}

/* Model viewer modal */
.model-viewer-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  opacity: 0;
  animation: fadeIn 0.3s forwards;
}

@keyframes fadeIn {
  to { opacity: 1; }
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.model-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
  background-color: #f8f9fa;
}

.model-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #888;
  padding: 5px;
  line-height: 1;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #e74c3c;
}

.model-preview-container {
  position: relative;
  width: 100%;
  height: 600px;
  background-color: #f0f0f0;
}

.model-container {
  width: 100%;
  height: 100%;
  display: block;
  outline: none;
}

/* Status overlays */
.status-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.status-content {
  text-align: center;
  padding: 30px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  max-width: 400px;
}

.status-overlay.error .status-content {
  border-top: 4px solid #e74c3c;
}

.status-overlay.loading .status-content {
  border-top: 4px solid #3498db;
}

.status-content h3 {
  margin-top: 0;
  margin-bottom: 10px;
}

.status-content p {
  margin-bottom: 20px;
  color: #555;
}

.status-content button {
  padding: 8px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.status-content button:hover {
  background-color: #2980b9;
}

/* Model controls */
.model-controls {
  padding: 15px 20px;
  display: flex;
  gap: 10px;
  border-top: 1px solid #eee;
  background-color: #f8f9fa;
  align-items: center;
}

.model-controls button {
  padding: 10px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.model-controls button:hover {
  background-color: #2980b9;
  transform: translateY(-1px);
}

.model-controls button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  transform: none;
}

.model-format-info {
  margin-left: auto;
  font-size: 14px;
  color: #7f8c8d;
  background-color: #ecf0f1;
  padding: 6px 12px;
  border-radius: 4px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .filter-section {
    flex-direction: column;
    gap: 10px;
  }
  
  .search-input,
  .category-select {
    width: 100%;
  }
  
  .model-list {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
  
  .modal-content {
    width: 95%;
    height: 95vh;
  }
  
  .model-preview-container {
    height: 60vh;
  }
  
  .model-controls {
    flex-wrap: wrap;
  }
  
  .model-format-info {
    margin-left: 0;
    width: 100%;
    text-align: center;
    margin-top: 10px;
  }
}
</style>