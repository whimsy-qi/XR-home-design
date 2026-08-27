        { image: (new URL('@/assets/5.png', import.meta.url).href), name: 'VISKAFORS威思卡弗 三人沙发', currentPrice: 8999, originalPrice: 12999, isNew: false, isHot: true, isMemberPrice: false, category: '客厅', description: '全真皮材质' },
<template>
  <div class="all-furniture-container">
    <!-- 左侧导航栏 -->
    <div class="left-nav">
      <!-- 标题行 - 使用flex布局 -->
      <div class="header-row">
        <div class="home-arrow" @click="goToHome">
          <span class="arrow">&#171;</span> <!-- ⬅（向左） -->
        </div>
        <h2>所有家具</h2>
      </div>
      
      <!-- 分类列表 - 恢复原来的样式 -->
      <ul>
        <li v-for="(category, index) in categories" :key="index" @click="filterFurniture(category)">
          {{ category }}
        </li>
      </ul>
    </div>
    
    <!-- 右侧家具展示区 -->
    <div class="right-content">
      <input type="text" placeholder="搜索" v-model="searchText" class="search-input">
      <div class="furniture-grid" ref="furnitureList">
        <div class="furniture-item" v-for="(furniture, index) in filteredFurniture" :key="index">
          <div class="furniture-image">
            <img :src="furniture.image" alt="家具图片">
          </div>
          <div class="furniture-info">

            <div class="name">{{ furniture.name }}</div>
            <div class="description" v-if="furniture.description">
              {{ furniture.description }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      categories: ['客厅', '卧室', '厨房', '书房', '洗浴', '装饰', '绿植'],
      furnitureData: [
        // 客厅家具 (5个)
        { image: (new URL('@/assets/5.png', import.meta.url).href), name: '三人沙发', currentPrice: 8999, originalPrice: 12999, isNew: false, isHot: true, isMemberPrice: false, category: '客厅', description: '全真皮材质' },
        { image: (new URL('@/assets/6.png', import.meta.url).href), name: '双人沙发', currentPrice: 3999, originalPrice: 5999, isNew: true, isHot: false, isMemberPrice: true, category: '客厅', description: '舒适布艺' },
        { image: (new URL('@/assets/7.png', import.meta.url).href), name: '三人沙发', currentPrice: 1299, originalPrice: 1699, isNew: false, isHot: true, isMemberPrice: false, category: '客厅', description: '舒适布衣' },
        { image: (new URL('@/assets/12.png', import.meta.url).href), name: '单人椅', currentPrice: 1999, originalPrice: 2499, isNew: false, isHot: false, isMemberPrice: true, category: '客厅', description: '舒适布衣' },
        { image: (new URL('@/assets/13.png', import.meta.url).href), name: '布椅', currentPrice: 899, originalPrice: 1199, isNew: true, isHot: false, isMemberPrice: false, category: '客厅', description: '真皮材质' },
        
        // 卧室家具 (5个)
        { image: (new URL('@/assets/14.png', import.meta.url).href), name: '书桌', currentPrice: 3499, originalPrice: 4299, isNew: false, isHot: true, isMemberPrice: false, category: '客厅', description: '真皮沙发' },
        { image: (new URL('@/assets/18.png', import.meta.url).href), name: '沙发椅', currentPrice: 2999, originalPrice: 3599, isNew: false, isHot: false, isMemberPrice: true, category: '客厅', description: '布艺' },
        { image: (new URL('@/assets/16.png', import.meta.url).href), name: '休闲椅', currentPrice: 399, originalPrice: 499, isNew: true, isHot: false, isMemberPrice: false, category: '客厅', description: '简约现代' },
        { image: (new URL('@/assets/17.png', import.meta.url).href), name: '休闲椅', currentPrice: 1799, originalPrice: 2199, isNew: false, isHot: true, isMemberPrice: true, category: '客厅', description: '布艺' },
        { image: (new URL('@/assets/20.png', import.meta.url).href), name: '推拉门椅子', currentPrice: 249, originalPrice: 329, isNew: true, isHot: false, isMemberPrice: false, category: '客厅', description: '藤条/松木' },
        
        // 厨房家具 (5个)
        { image: (new URL('@/assets/24.png', import.meta.url).href), name: '单人沙发/扶手椅', currentPrice: 799, originalPrice: 999, isNew: false, isHot: true, isMemberPrice: false, category: '客厅', description: '模块化设计' },
        { image: (new URL('@/assets/25.png', import.meta.url).href), name: '椅子', currentPrice: 1999, originalPrice: 2499, isNew: true, isHot: false, isMemberPrice: true, category: '客厅', description: '可伸缩设计' },
        { image: (new URL('@/assets/22.png', import.meta.url).href), name: '木柜', currentPrice: 599, originalPrice: 749, isNew: false, isHot: false, isMemberPrice: false, category: '客厅', description: '木质' },
        { image: (new URL('@/assets/23.png', import.meta.url).href), name: '储物柜', currentPrice: 4999, originalPrice: 5999, isNew: false, isHot: true, isMemberPrice: true, category: '客厅', description: '藤条' },
        { image: (new URL('@/assets/19.png', import.meta.url).href), name: '竹椅', currentPrice: 2299, originalPrice: 2899, isNew: true, isHot: false, isMemberPrice: false, category: '客厅', description: '藤条' },
        
        // 书房家具 (5个)
        { image: (new URL('@/assets/31.png', import.meta.url).href), name: '卧室三件套', currentPrice: 899, originalPrice: 1199, isNew: false, isHot: true, isMemberPrice: false, category: '卧室', description: '淡米色' },
        { image: (new URL('@/assets/32.png', import.meta.url).href), name: '卧室五件套', currentPrice: 1499, originalPrice: 1899, isNew: true, isHot: false, isMemberPrice: true, category: '卧室', description: '木质' },
        { image: (new URL('@/assets/33.png', import.meta.url).href), name: '卧室三件套', currentPrice: 2499, originalPrice: 2999, isNew: false, isHot: true, isMemberPrice: true, category: '卧室', description: '木质' },
        { image: (new URL('@/assets/34.png', import.meta.url).href), name: '卧室三件套', currentPrice: 299, originalPrice: 399, isNew: true, isHot: false, isMemberPrice: false, category: '卧室', description: '淡米色' },
        { image: (new URL('@/assets/35.png', import.meta.url).href), name: '卧室三件套', currentPrice: 4299, originalPrice: 4999, isNew: false, isHot: false, isMemberPrice: true, category: '卧室', description: '木质' },

                // 书房家具 (5个)
        { image: (new URL('@/assets/51.png', import.meta.url).href), name: '绿植', currentPrice: 899, originalPrice: 1199, isNew: false, isHot: true, isMemberPrice: false, category: '绿植', description: '室内/户外' },
        { image: (new URL('@/assets/52.png', import.meta.url).href), name: '人造盆栽', currentPrice: 1499, originalPrice: 1899, isNew: true, isHot: false, isMemberPrice: true, category: '绿植', description: '室内/户外' },
        { image: (new URL('@/assets/53.png', import.meta.url).href), name: '绿植', currentPrice: 2499, originalPrice: 2999, isNew: false, isHot: true, isMemberPrice: true, category: '绿植', description: '室内/户外' },
        { image: (new URL('@/assets/54.png', import.meta.url).href), name: '摆件植物', currentPrice: 299, originalPrice: 399, isNew: true, isHot: false, isMemberPrice: false, category: '绿植', description: '室内/户外/毛茛' },
        { image: (new URL('@/assets/55.png', import.meta.url).href), name: '人造植物', currentPrice: 4299, originalPrice: 4999, isNew: false, isHot: false, isMemberPrice: true, category: '绿植', description: '室内/户外/毛茛' },
        { image: (new URL('@/assets/56.png', import.meta.url).href), name: '绿植', currentPrice: 899, originalPrice: 1199, isNew: false, isHot: true, isMemberPrice: false, category: '绿植', description: '室内/户外' },
        { image: (new URL('@/assets/57.png', import.meta.url).href), name: '人造盆栽', currentPrice: 1499, originalPrice: 1899, isNew: true, isHot: false, isMemberPrice: true, category: '绿植', description: '室内/户外' },
        { image: (new URL('@/assets/58.png', import.meta.url).href), name: '绿植', currentPrice: 2499, originalPrice: 2999, isNew: false, isHot: true, isMemberPrice: true, category: '绿植', description: '室内/户外' },
      ],
      searchText: '',
      selectedCategory: ''
    };
  },
  computed: {
    filteredFurniture() {
      return this.furnitureData.filter(furniture => {
        return (
          (this.searchText === '' || furniture.name.toLowerCase().includes(this.searchText.toLowerCase())) &&
          (this.selectedCategory === '' || furniture.category === this.selectedCategory)
        );
      });
    }
  },
  methods: {
    filterFurniture(category) {
      this.selectedCategory = category;
    },
     // 添加返回首页方法
    goToHome() {

      this.$router.push({ name: 'PersonRoom' });
    }
    
  }
};
</script>

<style scoped>
.arrow {
  font-size: 40px;
  font-weight: bold;
  color: #333;
  margin-right: 10px;
  
  /* 关键调整：仅箭头本身下移 */
  display: inline-block;
  vertical-align: middle;

  transform: translateY(63px); /* 精确控制箭头下移2px */
}

.all-furniture-container {
  display: flex;
  height: 100vh;
}
.left-nav {
  width: 200px;
  padding: 20px;
  background-color: #f8f9fa;
}
.left-nav h2 {
  text-align: center;
  font-size: 24px;
  margin-bottom: 20px;
}
.left-nav li {
  padding: 12px 0;
  cursor: pointer;
  font-size: 18px;
  border-bottom: 1px solid #eee;
  padding-left: 10px;
}
.left-nav li:hover {
  background-color: #f0f0f0;
}
.right-content {
  flex: 1;
  padding: 20px;
}
.search-input {
  width: 200px;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
  margin-bottom: 25px;
  font-size: 16px;
}
.furniture-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(180px, 1fr)); /* 减小列宽 */
  gap: 30px; /* 调整间距 */
}
.furniture-item {
  height: 300px; /* 调整为竖长方形（高度 > 宽度） */
  width: 100%;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
}
.furniture-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
.furniture-image {
  height: 200px; /* 正方形图片区域 */
  width: 85%; /* 宽度与卡片一致 */
  overflow: hidden;
}
.furniture-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.furniture-image img:hover {
  transform: scale(1.05);
}
.furniture-info {
  padding: 10px 12px; /* 减少内边距 */
  flex: 1;
  display: flex;
  flex-direction: column;
}
.price {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  flex-wrap: wrap;
}
.tag {
  background-color: #e53935;
  color: white;
  font-size: 12px;
  padding: 2px 4px;
  border-radius: 2px;
  margin-right: 5px;
  margin-bottom: 3px;
}
.original-price {
  text-decoration: line-through;
  color: #999;
  font-size: 13px;
  margin-left: 5px;
}
.current-price {
  color: #e53935;
  font-weight: bold;
  font-size: 16px;
}
.name {
  font-size: 14px;
  margin-bottom: 5px;
  font-weight: 500;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.description {
  font-size: 12px;
  color: #666;
  flex: 1;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

</style>