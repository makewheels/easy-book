<template>
  <div class="home-page">
    <!-- 头部统计信息组件 -->
    <HomePageHeader
      :today-appointments="todayAppointments"
      :tomorrow-appointments="tomorrowAppointments"
    />

    <div class="content">
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <div class="loading-text">加载中...</div>
      </div>

      <!-- 预约列表组件 -->
      <AppointmentList v-else-if="dailyData && dailyData.length > 0" :daily-data="dailyData" />

      <div v-else class="empty-state">
        <div class="empty-icon">📋</div>
        <div class="empty-title">暂无预约</div>
      </div>
    </div>

    <!-- 底部导航组件 -->
    <BottomNavigation />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAppointmentStore } from '@/stores/appointment'
import { getToday, getTomorrow } from '@/utils/date'

// 导入组件
import HomePageHeader from '@/components/home/HomePageHeader.vue'
import AppointmentList from '@/components/home/AppointmentList.vue'
import BottomNavigation from '@/components/home/BottomNavigation.vue'

const appointmentStore = useAppointmentStore()

const loading = computed(() => appointmentStore.loading)
const dailyData = computed(() => {
  const appointmentsByDate = appointmentStore.appointmentsByDate
  console.log('Home.vue - appointmentsByDate:', appointmentsByDate)
  console.log('Home.vue - appointmentsByDate length:', appointmentsByDate?.length)
  const result = appointmentsByDate && appointmentsByDate.length > 0 ? appointmentsByDate : null
  console.log('Home.vue - dailyData result:', result)
  return result
})

// 计算今日预约数量
const todayAppointments = computed(() => {
  if (!dailyData.value || dailyData.value.length === 0) return 0

  const today = getToday()
  // 转换为 MM-DD 格式以匹配后端数据格式
  const todayFormatted = today.substring(5) // 去掉前缀 "YYYY-"
  const todayData = dailyData.value.find(day => day.date === todayFormatted)
  if (!todayData || !todayData.slots) return 0

  return todayData.slots.reduce((total, slot) => total + (slot.students ? slot.students.length : 0), 0)
})

// 计算明日预约数量
const tomorrowAppointments = computed(() => {
  if (!dailyData.value || dailyData.value.length === 0) return 0

  const tomorrow = getTomorrow()
  // 转换为 MM-DD 格式以匹配后端数据格式
  const tomorrowFormatted = tomorrow.substring(5) // 去掉前缀 "YYYY-"
  const tomorrowData = dailyData.value.find(day => day.date === tomorrowFormatted)
  if (!tomorrowData || !tomorrowData.slots) return 0

  return tomorrowData.slots.reduce((total, slot) => total + (slot.students ? slot.students.length : 0), 0)
})

onMounted(async () => {
  console.log('Home.vue - onMounted: 开始加载预约数据')
  try {
    await appointmentStore.fetchUpcomingAppointments(30) // 获取未来30天的预约
    console.log('Home.vue - onMounted: 预约数据加载完成')
  } catch (error) {
    console.error('Home.vue - onMounted: 加载预约数据失败:', error)
  }
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 80px;
}

/* 内容区域 */
.content {
  max-width: 430px;
  margin: 0 auto;
  padding: 20px 15px;
}

/* 加载状态 */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top: 4px solid #1989fa;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #666;
  font-size: 18px;
  font-weight: 500;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
  opacity: 0.6;
}

.empty-title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin-bottom: 10px;
}

.empty-subtitle {
  font-size: 18px;
  color: #666;
  font-weight: 500;
}
</style>