<template>
  <div class="segmentation-tool">
    <div 
      class="interactive-image-wrapper" 
      ref="wrapperRef"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseLeave"
      @click="handleWrapperClick"
    >
      <img 
        :src="imageUrl" 
        alt="AI生成的可交互效果图" 
        @load="onImageLoad" 
        class="base-image"
        ref="imageRef"
        draggable="false"
      >
      
      <div 
        v-for="(point, index) in points" 
        :key="`p-${index}`"
        class="marker"
        :class="point.label === 1 ? 'foreground' : 'background'"
        :style="{ left: point.x + 'px', top: point.y + 'px' }"
        :title="point.label === 1 ? '前景点 (点击移除)' : '背景点 (点击移除)'"
        @click.stop="removePoint(index)"
        @mousedown.stop 
      ></div>

       <div 
        v-for="(box, index) in boxes"
        :key="`b-${index}`"
        class="drawn-box"
        :style="{ left: box.x + 'px', top: box.y + 'px', width: box.width + 'px', height: box.height + 'px' }"
        title="框选区域 (点击移除)"
        @click.stop="removeBox(index)"
        @mousedown.stop
      ></div>

      <div
        v-if="isDrawing && currentBox"
        class="drawing-box"
        :style="{ left: currentBox.x + 'px', top: currentBox.y + 'px', width: currentBox.width + 'px', height: currentBox.height + 'px' }"
      ></div>
    </div>

    <div class="controls-wrapper">
        <div class="mode-group">
            <span class="mode-title">模式:</span>
            <button class="mode-btn" :class="{active: drawingMode === 'point'}" @click.stop="setDrawingMode('point')">点选</button>
            <button class="mode-btn" :class="{active: drawingMode === 'box'}" @click.stop="setDrawingMode('box')">框选</button>
        </div>
        <div class="mode-group" v-if="drawingMode === 'point'">
            <span class="mode-title">类型:</span>
            <button class="mode-btn point-fg" :class="{active: currentPointType === 1}" @click.stop="currentPointType = 1">前景</button>
            <button class="mode-btn point-bg" :class="{active: currentPointType === 0}" @click.stop="currentPointType = 0">背景</button>
        </div>
        <div class="action-buttons">
            <button @click.stop="triggerSegmentation" class="action-btn segment" :disabled="points.length === 0 && boxes.length === 0">执行分割</button>
            <button @click.stop="clearAll" class="action-btn clear" v-if="points.length > 0 || boxes.length > 0">全部清除</button>
        </div>
    </div>
  </div>
</template>

<script setup>
// Script部分无需修改
import { ref } from 'vue';

const props = defineProps({ imageUrl: { type: String, required: true }});
const emit = defineEmits(['start-segment']);

const imageRef = ref(null);
const points = ref([]);
const boxes = ref([]);
const naturalImageSize = ref({ width: 0, height: 0 });

const drawingMode = ref('point');
const currentPointType = ref(1);

const isDrawing = ref(false);
const startCoords = ref({x: 0, y: 0});
const currentBox = ref(null);
const hasDragged = ref(false);

const onImageLoad = (event) => {
  naturalImageSize.value.width = event.target.naturalWidth;
  naturalImageSize.value.height = event.target.naturalHeight;
};

const setDrawingMode = (mode) => {
  drawingMode.value = mode;
};

const handleMouseDown = (event) => {
  hasDragged.value = false;
  if (drawingMode.value === 'box') {
    isDrawing.value = true;
    const rect = event.currentTarget.getBoundingClientRect();
    startCoords.value = { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }
};

const handleMouseMove = (event) => {
  if (!isDrawing.value || drawingMode.value !== 'box') return;
  hasDragged.value = true;
  const rect = event.currentTarget.getBoundingClientRect();
  const currentX = event.clientX - rect.left;
  const currentY = event.clientY - rect.top;
  const x = Math.min(startCoords.value.x, currentX);
  const y = Math.min(startCoords.value.y, currentY);
  const width = Math.abs(startCoords.value.x - currentX);
  const height = Math.abs(startCoords.value.y - currentY);
  currentBox.value = { x, y, width, height };
};

const handleMouseUp = (event) => {
  if (drawingMode.value === 'box' && isDrawing.value) {
    if (currentBox.value && currentBox.value.width > 5 && currentBox.value.height > 5) {
      boxes.value.push(currentBox.value);
    }
  } else if (drawingMode.value === 'point' && !hasDragged.value) {
      handlePointClick(event);
  }
  isDrawing.value = false;
  currentBox.value = null;
};

const handleMouseLeave = () => {
    if(isDrawing.value) {
        isDrawing.value = false;
        currentBox.value = null;
    }
}

const handlePointClick = (event) => {
  if (!imageRef.value) return;
  const rect = imageRef.value.getBoundingClientRect();
  const displayX = event.clientX - rect.left;
  const displayY = event.clientY - rect.top;
  points.value.push({ x: displayX, y: displayY, label: currentPointType.value });
};

const removePoint = (index) => { points.value.splice(index, 1); };
const removeBox = (index) => { boxes.value.splice(index, 1); };
const clearAll = () => {
  points.value = [];
  boxes.value = [];
};

const triggerSegmentation = () => {
  if (points.value.length === 0 && boxes.value.length === 0) return;
  const rect = imageRef.value.getBoundingClientRect();
  const scaleX = naturalImageSize.value.width / rect.width;
  const scaleY = naturalImageSize.value.height / rect.height;
  const backendPoints = points.value.map(p => ({ x: Math.round(p.x * scaleX), y: Math.round(p.y * scaleY), label: p.label }));
  const backendBoxes = boxes.value.map(b => ({
      x_min: Math.round(b.x * scaleX),
      y_min: Math.round(b.y * scaleY),
      x_max: Math.round((b.x + b.width) * scaleX),
      y_max: Math.round((b.y + b.height) * scaleY),
  }));
  emit('start-segment', { points: backendPoints, boxes: backendBoxes });
  clearAll();
};
</script>

<style scoped>
/* 样式有较多更新 */
.segmentation-tool {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}
.interactive-image-wrapper { 
  position: relative; 
  cursor: crosshair; 
  display: inline-block; 
  line-height: 0; 
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.base-image { max-width: 100%; display: block; user-select: none; -webkit-user-drag: none; }
.marker { position: absolute; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5); transform: translate(-50%, -50%); pointer-events: all; cursor: pointer; }
.marker.foreground { background-color: rgba(76, 175, 80, 0.8); }
.marker.background { background-color: rgba(244, 67, 54, 0.8); }
.drawn-box { position: absolute; border: 2px dashed #4CAF50; background-color: rgba(76, 175, 80, 0.2); pointer-events: all; cursor: pointer; }
.drawing-box { position: absolute; border: 2px dashed #2196F3; background-color: rgba(33, 150, 243, 0.2); pointer-events: none; }

.controls-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap; /* 【核心修改】允许换行 */
  gap: 1.5rem; /* 【核心修改】增大组之间的间距 */
  width: 100%;
  padding: 1rem;
  margin-top: 1rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.mode-group { display: flex; align-items: center; gap: 0.5rem; }
.mode-title { font-size: 0.9rem; color: #555; font-weight: 500; white-space: nowrap; /* 防止标题换行 */ }
.mode-btn { background: #f0f0f0; color: #333; border: 1px solid #ddd; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; transition: all 0.2s; font-size: 0.9rem; white-space: nowrap; /* 防止按钮内文字换行 */ }
.mode-btn.active { color: white; border-color: #FB8C00; background: #FFA726; font-weight: bold; }
.mode-btn.point-fg.active { background: #4CAF50; border-color: #66BB6A; }
.mode-btn.point-bg.active { background: #f44336; border-color: #ef5350; }

.action-buttons { display: flex; gap: 0.5rem; }
.action-btn { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.6rem 1.2rem; border: none; border-radius: 6px; cursor: pointer; color: white; font-weight: 500; font-size: 0.9rem; transition: background-color 0.2s; white-space: nowrap; }
.action-btn.clear { background-color: #9E9E9E; }
.action-btn.clear:hover { background-color: #757575; }
.action-btn.segment { background-color: #FFA726; }
.action-btn.segment:hover:not(:disabled) { background-color: #FB8C00; }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.action-btn svg { stroke: white; }
</style>