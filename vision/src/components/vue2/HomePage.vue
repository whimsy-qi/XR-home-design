<template>
  <div class="home-page">
    <h1>样板房浏览</h1>
    <div class="room-list">
      <div
        class="room-card"
        v-for="room in rooms"
        :key="room.id"
        @click="goToRoom(room.id)"
      >
        <img :src="room.thumbnail" alt="Room Thumbnail" />
        <div class="room-name">{{ room.name }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import room1_thumb from "@/assets/images0/room1_thumb.jpeg";
import room2_thumb from "@/assets/images0/room2_thumb.jpg";
import room3_thumb from "@/assets/images0/room3_thumb.jpg";
export default {
  name: 'HomePage',
  data () {
    return {
      room1_thumb:room1_thumb,
      room2_thumb:room2_thumb,
      room3_thumb:room3_thumb,
      rooms: [
        {
          id: 'room1',
          name: '客厅样板间',
          thumbnail: room1_thumb
        },
        {
          id: 'room2',
          name: '厨房样板间',
          thumbnail: room2_thumb
        },
        {
          id: 'room3',
          name: '卧室样板间',
          thumbnail: room3_thumb
        }
      ]
    }
  },
  methods: {
    goToRoom(roomId) {
      this.$router.push({ name: 'PanoramaViewer', query: { roomId } })
    }
  }
}
</script>

<style scoped>
.home-page h1 {
  font-size: 1.5rem; /* 默认浏览器大约是2rem，你可以调小，比如1.5rem */
  margin-bottom: 1rem;
  font-weight: bold;
  text-align: left;
}

.home-page {
  margin-top: -30px;  /* 上移20像素，根据需要调节 */
  padding: 2rem;
  text-align: center;
}
.room-list {
  display: flex;
  flex-wrap: wrap;
  gap: 3.4rem; /* 增加间距 */
  justify-content: center;
}
.room-card {
  width: 400px; /* 放大宽度 */
  height: 300px;
  border: 1px solid #ccc;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 8px rgb(0 0 0 / 0.1);
}
.room-card:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 16px rgb(0 0 0 / 0.2);
}
.room-card img {
  width: 100%;
  height: 250px; /* 增加图片高度 */
  object-fit: cover;
}
.room-name {
  padding: 0.5rem 0 0.3rem 0; /* 上下 padding 缩小 */
  font-weight: bold;
  font-size: 1.25rem; /* 字体加大 */
  color: #333;
}
</style>
