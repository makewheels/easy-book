<template>
  <div class="home-page">
    <div class="header">
      <h1>预约管理</h1>
      <div class="stats">今日 {{ todayAppointments }} 个，明日 {{ tomorrowAppointments }} 个</div>
    </div>

    <div class="content">
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
    
      <div v-else-if="dailyData && dailyData.length > 0" class="appointments">
        <div v-for="dayData in dailyData" :key="dayData.date" class="day-section">
          <div class="date-header">
            <span class="date-weekday">{{ dayData.date }} {{ dayData.weekday }}</span>
          </div>

          <div v-if="dayData.slots.length === 0" class="no-appointments">
            <span class="no-appointments-text">当天无预约</span>
          </div>

          <div v-else>
            <div v-for="slot in dayData.slots" :key="`${dayData.date}-${slot.time}`" class="time-slot">
              <div class="time-header">
                <span class="time">{{ slot.time }}</span>
              </div>

              <div class="students">
                <div
                  v-for="student in slot.students"
                  :key="student.id"
                  class="student-item"
                >
                  <div class="student-info">
                    <div class="name-row">
                      <span class="name">{{ student.name }}</span>
                      <span class="type">{{ student.package_type }}</span>
                      <span v-if="dayData.isPast || student.status !== 'scheduled'" class="status" :class="getStatusClass(student.status)">
                        {{ getStatusText(student.status) }}
                      </span>
                    </div>

                    <div class="details">
                      <span class="lessons">次数[{{ student.attended_lessons }}/{{ student.total_lessons }}]</span>
                      <span class="project">{{ student.learning_item }}</span>
                    </div>
                  </div>

                  <div v-if="!dayData.isPast && student.status === 'scheduled'" class="actions">
                    <button class="btn-cancel" @click="handleCancel(student)">
                      取消
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

        <div v-else class="empty-state">
        <div class="empty-message">暂无预约</div>
      </div>
    </div>
    
    <div class="bottom-nav">
      <div class="nav-item active" @click="navigateTo('home')">
        <div class="nav-icon">🏠</div>
        <span>预约管理</span>
      </div>
      <div class="nav-item" @click="navigateTo('calendar')">
        <div class="nav-icon">📅</div>
        <span>课程日历</span>
      </div>
      <div class="nav-item" @click="navigateTo('students')">
        <div class="nav-icon">👥</div>
        <span>学员管理</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppointmentStore } from '@/stores/appointment'
import { appointmentApi } from '@/api/appointment'
import { getToday, getTomorrow } from '@/utils/date'
import { toast } from '@/utils/toast'

const router = useRouter()
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

const getStatusClass = (status) => {
  return {
    'status-cancel': status === 'cancel'
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'cancel': '已取消'
  }
  return statusMap[status] || ''
}

const handleCancel = async (student) => {
  try {
    console.log('取消预约学员数据:', student)

    if (!student.appointment_id || !student.student_id) {
      throw new Error('缺少必要的预约ID或学员ID')
    }

    const response = await appointmentApi.cancel(student.appointment_id)

    if (response && response.data) {
      await appointmentStore.fetchUpcomingAppointments(30)
      toast.success('预约取消成功，课程次数已恢复')
    } else {
      throw new Error('取消预约API返回数据异常')
    }
  } catch (error) {
    console.error('取消预约错误:', error)
    toast.error(error.message || '取消预约失败')
  }
}


</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 60px;
}

.header {
  background: #1989fa;
  color: #fff;
  padding: 15px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header h1 {
  font-size: 22px;
  margin: 0;
  text-align: center;
}

.header .stats {
  text-align: center;
  margin-top: 5px;
  font-size: 14px;
  opacity: 0.9;
}

.content {
  padding: 10px;
}

.loading {
  text-align: center;
  padding: 50px 0;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 50px 0;
}

.empty-message {
  color: #999;
  font-size: 16px;
}

.no-appointments {
  padding: 20px;
  text-align: center;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 15px;
}

.no-appointments-text {
  color: #999;
  font-size: 14px;
}

.appointments {
  margin-bottom: 20px;
}

.day-section {
  margin-bottom: 25px;
}

.date-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 15px;
  text-align: left;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.date-header .date-weekday {
  color: #1976d2;
  font-size: 24px;
  font-weight: bold;
}

.time-slot {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 15px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.time-header {
  background: #fafafa;
  padding: 12px;
  border-bottom: 2px solid #eee;
}

.time {
  font-size: 22px;
  font-weight: bold;
  color: #1989fa;
}

.students {
  padding: 0;
}

.student-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.student-item:last-child {
  border-bottom: none;
}

.student-info {
  margin-bottom: 8px;
}

.name-row {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.name {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-right: 8px;
}

.type {
  background: #f0f9ff;
  color: #1989fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
}

.status {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
}

.status-checked {
  background: #e6f7e6;
  color: #52c41a;
}

.status-cancel {
  background: #f5f5f5;
  color: #999;
}

.details {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #666;
}

.lessons {
  margin-right: 10px;
}

.actions {
  display: flex;
  gap: 10px;
}

.btn-cancel {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  background: #999;
  color: #fff;
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 430px;
  height: 60px;
  background: #fff;
  border-top: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-around;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: color 0.3s;
}

.nav-item.active {
  color: #1989fa;
}

.nav-icon {
  font-size: 20px;
  margin-bottom: 2px;
}
</style>