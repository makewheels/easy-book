<template>
  <div class="calendar-page">
    <div class="calendar-container">
      <div v-if="loading" class="loading">
        加载中...
      </div>

      <div v-else class="calendar-wrapper">
        <div class="calendar-grid">
          <!-- 时间列头 -->
          <div class="time-header-cell"></div>

          <!-- 日期列头 -->
          <div v-for="day in weekDates" :key="day.date" class="date-header-cell">
            {{ day.weekday }}<br>{{ day.displayDate }}
          </div>

          <!-- 时间行和内容 -->
          <template v-for="timeSlot in timeSlots" :key="timeSlot">
            <!-- 时间单元格 -->
            <div class="time-cell">
              {{ timeSlot }}
            </div>

            <!-- 每个日期的时间段单元格 -->
            <div
              v-for="day in weekDates"
              :key="`${day.date}-${timeSlot}`"
              class="time-slot"
              >
              <span
                v-if="!hasStudents(day.date, timeSlot)"
                class="empty-cell"
              ></span>

              <div v-else class="students-container">
                <div
                  v-for="student in getStudents(day.date, timeSlot)"
                  :key="`${student.appointment_id}-${student.student_id}`"
                  class="student-card"
                  :class="getStatusClass(student, day.date, timeSlot)"
                  @click="goToStudent(student.student_id)"
                >
                  <div class="student-name">{{ student.name }}</div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <BottomNavigation :active-tab="'calendar'" @navigate="navigateTo" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppointmentStore } from '@/stores/appointment'
import { format, addDays, isSameDay } from 'date-fns'
import BottomNavigation from '@/components/BottomNavigation.vue'

const router = useRouter()
const appointmentStore = useAppointmentStore()

const loading = ref(false)
// 计算本周的开始（周一）
const getWeekStart = () => {
  const today = new Date()
  const day = today.getDay() || 7 // 将周日(0)转换为7
  const diff = today.getDate() - day + 1 // 周一的日期
  return new Date(today.setDate(diff))
}

const currentWeekStart = ref(getWeekStart())
const weekData = ref({})

const timeSlots = [
  '07:00', '08:00', '09:00', '10:00', '11:00',
  '12:00', '14:00', '15:00', '16:00', '17:00',
  '18:00', '19:00'
]

const weekDates = computed(() => {
  const dates = []
  const startDate = new Date(currentWeekStart.value)

  // 从周二开始，只循环6次（周二到周日），跳过周一
  for (let i = 1; i < 7; i++) {
    const currentDate = addDays(startDate, i)
    const dayOfWeek = currentDate.getDay() === 0 ? 7 : currentDate.getDay()

    // 如果是周一(dayOfWeek=1)，跳过不显示
    if (dayOfWeek === 1) continue

    const dateStr = format(currentDate, 'yyyy-MM-dd')
    const isToday = isSameDay(currentDate, new Date())

    const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    let weekdayIndex = dayOfWeek - 1
    if (weekdayIndex > 0) weekdayIndex--

    dates.push({
      date: dateStr,
      displayDate: format(currentDate, 'MM/dd'),
      weekday: weekdayNames[weekdayIndex],
      isToday: isToday
    })
  }

  return dates
})

const todayDate = computed(() => {
  return format(new Date(), 'yyyy-MM-dd')
})

const fetchWeekData = async () => {
  loading.value = true
  try {
    const weekDataMap = await appointmentStore.fetchWeekAppointments(currentWeekStart.value)
    weekData.value = weekDataMap
  } catch (error) {
    console.error('获取周数据失败:', error)
  } finally {
    loading.value = false
  }
}

const hasStudents = (date, timeSlot) => {
  const dayData = weekData.value[date]
  if (!dayData || !dayData.slots) return false

  const slot = dayData.slots.find(s => s.time === timeSlot)
  return slot && slot.students && slot.students.length > 0
}

const getStudents = (date, timeSlot) => {
  const dayData = weekData.value[date]
  if (!dayData || !dayData.slots) return []

  const slot = dayData.slots.find(s => s.time === timeSlot)
  return slot ? slot.students : []
}

const getStatusClass = (student, date, timeSlot) => {
  // 创建预约时间来与当前时间比较
  const appointmentDateTime = new Date(`${date}T${timeSlot}:00`)
  const now = new Date()

  // 如果预约时间还未到，显示蓝色（未上课）
  if (appointmentDateTime > now) {
    return 'status-upcoming'   // 未来时间 - 蓝色
  } else {
    // 预约时间已过，显示灰色（已完成或已错过）
    return 'status-during'     // 过去时间 - 灰色
  }
}

const goToStudent = (studentId) => {
  router.push({
    name: 'StudentDetail',
    params: { id: studentId }
  })
}

const navigateTo = (page) => {
  switch(page) {
    case 'home':
      router.push('/')
      break
    case 'calendar':
      break
    case 'students':
      router.push('/students')
      break
  }
}

onMounted(() => {
  fetchWeekData()
})
</script>

<style scoped>
.calendar-page {
  max-width: none;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background: #f5f5f5;
  position: relative;
  padding-bottom: 80px;
  width: 100%;
}

.header {
  background: #fff;
  color: #1a1a1a;
  padding: 20px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header h1 {
  font-size: 32px;
  font-weight: 800;
  margin: 0;
  text-align: center;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.calendar-container {
  padding: 0;
  max-width: none;
  width: 100%;
  box-sizing: border-box;
}

.calendar-wrapper {
  background: #fff;
  padding: 40px 20px 20px 0;
  position: relative;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: -30px 10px 0 10px;
}

.calendar-grid {
  display: grid;
  grid-template-columns: 100px repeat(6, minmax(120px, 1fr));
  grid-auto-rows: 70px;
  background: transparent;
  min-width: 900px;
  width: 100%;
  border-collapse: collapse;
}

.time-header-cell {
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #0050b3;
  border-bottom: 2px solid #e3f2fd;
  grid-row: 1;
  position: sticky;
  top: 0;
  left: 0;
  z-index: 20;
}

.date-header-cell {
  background: #f5f5f5;
  font-size: 16px;
  font-weight: 700;
  color: #0050b3;
  padding: 12px 8px;
  line-height: 1.3;
  text-align: center;
  grid-row: 1;
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 2px solid #e3f2fd;
  border-right: 1px solid #e0e0e0;
}


.time-cell {
  background: #f9f9f9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #0050b3;
  width: 100px;
  border-bottom: 1px solid #e0e0e0;
  grid-column: 1;
  position: sticky;
  left: 0;
  z-index: 15;
  box-sizing: border-box;
  border-right: 2px solid #e0e0e0;
}

.time-slot {
  position: relative;
  padding: 4px;
  min-height: 70px;
  font-size: 14px;
  cursor: pointer;
  background: #f9f9f9;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #e0e0e0;
  border-right: 1px solid #e0e0e0;
}

.students-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
  box-sizing: border-box;
  padding: 3px 0;
}

.student-card {
  background: #fff;
  color: #1a1a1a;
  font-weight: 700;
  padding: 8px 10px;
  height: auto;
  min-height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  text-align: center;
  box-sizing: border-box;
  line-height: 1.2;
  margin: 0;
  border: 1px solid #e0e0e0;
}

.student-name {
  font-size: 16px;
  font-weight: 800;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 状态颜色 */
.status-upcoming {
  background: #e6f7ff;
  color: #0050b3;
}

.status-active {
  background: #fff7e6;
  color: #ad6800;
}

.status-checked {
  background: #f6ffed;
  color: #389e0d;
}

.status-during {
  background: #f5f5f5;
  color: #8c8c8c;
}

.status-cancel {
  background: #fafafa;
  color: #bfbfbf;
}

.empty-cell {
  width: calc(100% - 8px);
  height: calc(100% - 8px);
  background: #fff;
  border: 1px dashed #d0d0d0;
  cursor: pointer;
  position: absolute;
  top: 4px;
  left: 4px;
  margin: 0;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

.loading-text {
  color: #fff;
  font-size: 18px;
  font-weight: 500;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}


/* 响应式设计 */
@media (max-width: 480px) {
  .header h1 {
    font-size: 28px;
  }

  .time-header-cell {
    font-size: 16px;
  }

  .date-header-cell {
    font-size: 14px;
  }

  .time-cell {
    font-size: 16px;
  }

  .student-name {
    font-size: 14px;
  }
}
</style>