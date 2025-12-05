<template>
  <nav class="bottom-nav">
    <div class="nav-item" :class="{ active: currentRoute === 'home' }" @click="navigateTo('home')">
      <div class="nav-icon">🏠</div>
      <span>预约管理</span>
    </div>
    <div class="nav-item" :class="{ active: currentRoute === 'calendar' }" @click="navigateTo('calendar')">
      <div class="nav-icon">📅</div>
      <span>课程日历</span>
    </div>
    <div class="nav-item" :class="{ active: currentRoute === 'students' }" @click="navigateTo('students')">
      <div class="nav-icon">👥</div>
      <span>学员管理</span>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const currentRoute = computed(() => {
  const path = route.path
  if (path === '/') return 'home'
  if (path === '/calendar') return 'calendar'
  if (path === '/students') return 'students'
  return 'home'
})

const navigateTo = (page) => {
  switch(page) {
    case 'home':
      router.push('/')
      break
    case 'calendar':
      router.push('/calendar')
      break
    case 'students':
      router.push('/students')
      break
  }
}
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 430px;
  height: 70px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 100;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
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
  flex: 1;
}

.nav-item.active {
  color: #1989fa;
}

.nav-icon {
  font-size: 24px;
  margin-bottom: 4px;
}
</style>