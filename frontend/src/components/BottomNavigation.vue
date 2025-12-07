<template>
  <nav class="bottom-nav">
    <div
      class="nav-item"
      :class="{ active: activeTab === 'calendar' }"
      @click="$emit('navigate', 'calendar')"
    >
      <div class="nav-icon">📋</div>
      <span>课表</span>
    </div>
    <div
      class="nav-item"
      :class="{ active: activeTab === 'students' }"
      @click="$emit('navigate', 'students')"
    >
      <div class="nav-icon">👤</div>
      <span>学员</span>
    </div>
  </nav>
</template>

<script setup>
defineProps({
  activeTab: {
    type: String,
    default: 'calendar'
  }
})

defineEmits(['navigate'])
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 1200px;
  height: 70px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 100;
  padding: 0 20px;
  box-sizing: border-box;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.3s;
  padding: 5px;
}

.nav-item.active {
  color: #1989fa;
}

.nav-icon {
  font-size: 24px;
  margin-bottom: 4px;
}
</style>