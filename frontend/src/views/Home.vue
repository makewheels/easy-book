<template>
  <div class="home-page">
    <div class="header">
      <h1>泳课预约系统</h1>
    </div>
    
    <div class="content">
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <div v-else-if="dailyData && dailyData.slots.length === 0" class="empty-state">
        <div class="empty-message">暂无预约</div>
      </div>
      
      <div v-else-if="dailyData" class="appointments">
        <div class="date-header">
          <span class="date-weekday">{{ dailyData.date }} {{ dailyData.weekday }}</span>
        </div>
        <div v-for="slot in dailyData.slots" :key="slot.time" class="time-slot">
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
                  <span v-if="dailyData.isPast || student.status !== 'scheduled'" class="status" :class="getStatusClass(student.status)">
                    {{ getStatusText(student.status) }}
                  </span>
                </div>

                <div class="details">
                  <span class="lessons">次数[{{ student.attended_lessons }}/{{ student.total_lessons }}]</span>
                  <span class="project">{{ student.learning_item }}</span>
                </div>
              </div>

              <div v-if="!dailyData.isPast && student.status === 'scheduled'" class="actions">
                <button class="btn-checkin" @click="handleCheckIn(student)">
                  签到
                </button>
                <button class="btn-absent" @click="handleAbsent(student)">
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>
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
        <span>学生管理</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppointmentStore } from '@/stores/appointment'
import { attendanceApi } from '@/api/attendance'
import { getToday, getTomorrow } from '@/utils/date'
import { toast } from '@/utils/toast'

const router = useRouter()
const appointmentStore = useAppointmentStore()

const loading = computed(() => appointmentStore.loading)
const dailyData = computed(() => {
  const appointmentsByDate = appointmentStore.appointmentsByDate
  return appointmentsByDate && appointmentsByDate.length > 0 ? appointmentsByDate[0] : null
})

onMounted(() => {
  appointmentStore.fetchDailyAppointments(getToday())
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
    'status-checked': status === 'checked',
    'status-cancel': status === 'cancel'
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'checked': '已签到',
    'cancel': '已取消'
  }
  return statusMap[status] || ''
}

const handleCheckIn = async (student) => {
  try {
    // 添加调试日志
    console.log('签到学生数据:', student)
    
    // 检查必要字段
    if (!student.appointment_id || !student.student_id) {
      throw new Error('缺少必要的预约ID或学生ID')
    }
    
    await attendanceApi.checkin(student.appointment_id, student.student_id)
    await appointmentStore.fetchDailyAppointments(getToday())
    toast.success('签到成功')
  } catch (error) {
    console.error('签到错误:', error)
    toast.error(error.message || '签到失败')
  }
}

const handleAbsent = async (student) => {
  try {
    // 添加调试日志
    console.log('标记取消学生数据:', student)

    // 检查必要字段
    if (!student.appointment_id || !student.student_id) {
      throw new Error('缺少必要的预约ID或学生ID')
    }

    await attendanceApi.markCancel(student.appointment_id, student.student_id)
    await appointmentStore.fetchDailyAppointments(getToday())
    toast.success('标记取消成功')
  } catch (error) {
    console.error('标记取消错误:', error)
    toast.error(error.message || '标记取消失败')
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

.appointments {
  margin-bottom: 20px;
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
  background: #fff2e8;
  color: #fa8c16;
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

.btn-checkin, .btn-absent {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.btn-checkin {
  background: #52c41a;
  color: #fff;
}

.btn-absent {
  background: #fa8c16;
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