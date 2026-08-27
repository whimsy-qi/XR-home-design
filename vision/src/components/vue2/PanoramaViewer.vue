<template>
  <div id="container" ref="container" style="width: 100vw; height: 100vh;"></div>
</template>

<script>
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { markRaw } from 'vue'

export default {
  name: 'PanoramaViewer',
  data() {
    return {
      scene: null,
      camera: null,
      renderer: null,
      controls: null,
      poiObjects: [],
      hotPoints: [
        { 
          position: { x: 0, y: 0, z: -0.2 }, 
          detail: { title: '信息点1', gotoRoom: 'room2' }  // 点击跳转 room2
        },
        { 
          position: { x: -0.2, y: -0.05, z: 0.2 }, 
          detail: { title: '信息点2' }  // 不跳转
        }
      ],
      roomsCubemaps: {
        room1: [
          'scene_left.jpeg',
          'scene_right.jpeg',
          'scene_top.jpeg',
          'scene_bottom.jpeg',
          'scene_front.jpeg',
          'scene_back.jpeg'
        ],
        room2: [
          'scene1_left.jpg',
          'scene1_right.jpg',
          'scene1_top.jpg',
          'scene1_bottom.jpg',
          'scene1_front.jpg',
          'scene1_back.jpg'
        ],
        room3: [
          'scene_left.jpeg',
          'scene_right.jpeg',
          'scene_top.jpeg',
          'scene_bottom.jpeg',
          'scene_front.jpeg',
          'scene_back.jpeg'
        ]
      }
    }
  },
  mounted() {
    this.initThree()
    this.reloadRoom(this.$route.query.roomId || 'room1')
  },
  watch: {
    '$route.query.roomId'(newRoomId) {
      this.reloadRoom(newRoomId || 'room1')
    }
  },
  methods: {
    initThree() {
      const container = this.$refs.container

      // 使用 markRaw 防止 Three.js 对象被 Vue 响应式系统包装
      this.scene = markRaw(new THREE.Scene())

      this.camera = markRaw(new THREE.PerspectiveCamera(
        90,
        container.clientWidth / container.clientHeight,
        0.1,
        100
      ))
      this.camera.position.set(0, 0, 0.01)

      this.renderer = markRaw(new THREE.WebGLRenderer())
      this.renderer.setSize(container.clientWidth, container.clientHeight)
      container.appendChild(this.renderer.domElement)

      this.controls = markRaw(new OrbitControls(this.camera, this.renderer.domElement))
      this.controls.zoomSpeed = 5.0

      this.animate()

      container.addEventListener('click', this.onClick, false)
    },
    reloadRoom(roomId) {
      this.clearScene()
      const cubemapFiles = this.roomsCubemaps[roomId]
      if (!cubemapFiles) {
        console.error(`没有找到房间 ${roomId} 的贴图资源，默认使用 room1`)
        this.loadCubemapMaterials(this.roomsCubemaps['room1'])
      } else {
        this.loadCubemapMaterials(cubemapFiles)
      }
      this.initPoints()
    },
    clearScene() {
      while (this.scene.children.length > 0) {
        this.scene.remove(this.scene.children[0])
      }
      this.poiObjects = []
    },
    loadCubemapMaterials(fileNames) {
      const loader = new THREE.TextureLoader()
      const materials = []

      fileNames.forEach(file => {
        // 改用public文件夹的方式，避免动态路径问题
        const texture = loader.load(`/images/${file}`)
        materials.push(new THREE.MeshBasicMaterial({ map: texture }))
      })

      const box = markRaw(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), materials))
      box.geometry.scale(1, 1, -1)
      this.scene.add(box)
    },
    initPoints() {
      const loader = new THREE.TextureLoader()
      const pointTexture = loader.load('/images/hot.png')
      const material = new THREE.SpriteMaterial({ map: pointTexture })

      this.poiObjects = []

      this.hotPoints.forEach(hot => {
        const sprite = markRaw(new THREE.Sprite(material.clone()))
        sprite.scale.set(0.1, 0.1, 0.1)
        sprite.position.set(hot.position.x, hot.position.y, hot.position.z)
        sprite.detail = hot.detail
        this.scene.add(sprite)
        this.poiObjects.push(sprite)
      })
    },
    animate() {
      requestAnimationFrame(() => this.animate())
      this.renderer.render(this.scene, this.camera)
    },
    onClick(event) {
      event.preventDefault()
      const rect = this.$refs.container.getBoundingClientRect()
      const mouse = new THREE.Vector2()
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

      const raycaster = new THREE.Raycaster()
      raycaster.setFromCamera(mouse, this.camera)
      const intersects = raycaster.intersectObjects(this.poiObjects)

      if (intersects.length > 0) {
        const clicked = intersects[0].object.detail
        alert('点击了热点：' + clicked.title)
        if (clicked.gotoRoom) {
          this.$router.push({ name: 'PanoramaViewer', query: { roomId: clicked.gotoRoom } })
        }
      }
    }
  },
  beforeDestroy() {
    if (this.renderer) this.renderer.dispose()
    if (this.controls) this.controls.dispose()
  }
}
</script>

<style scoped>
html, body, #app, #container {
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>
