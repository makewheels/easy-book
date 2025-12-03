<template>
  <div class="calendar-page" :class="{ transitioning: isTransitioning }"
       @touchstart="handleTouchStart"
       @touchmove="handleTouchMove"
       @touchend="handleTouchEnd">
    <!-- 顶部导航栏 -->
    <header class="header">
      <h1>{{ dateRangeText }}</h1>
    </header>

    <!-- 状态图例 -->
    <div class="status-legend">
      <div class="legend-title">状态说明：</div>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-color upcoming"></div>
          <span>未到上课时间</span>
        </div>
        <div class="legend-item">
          <div class="legend-color during"></div>
          <span>到了上课时间</span>
        </div>
        <div class="legend-item">
          <div class="legend-color checked"></div>
          <span>已签到</span>
        </div>
        <div class="legend-item">
          <div class="legend-color cancel"></div>
          <span>已取消</span>
        </div>
      </div>
    </div>

    <!-- 日历表格 -->
    <div class="calendar-container" :class="{ transitioning: isTransitioning }">
      <div v-if="loading" class="loading">
        加载中...
      </div>

      <table v-else class="calendar-table" :class="{ transitioning: isTransitioning }">
        <thead>
          <tr>
            <th class="time-column">时间</th>
            <th v-for="day in weekDates" :key="day.date" :class="getDayClass(day)">
              {{ day.weekday }}<br>{{ day.displayDate }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="timeSlot in timeSlots" :key="timeSlot">
            <td class="time-column">{{ timeSlot }}</td>
            <td
              v-for="day in weekDates"
              :key="`${day.date}-${timeSlot}`"
              class="time-slot"
              :class="getTimeSlotClass(day.date, timeSlot)"
            >
              <!-- 空时段 -->
              <span
                v-if="!hasStudents(day.date, timeSlot)"
                class="empty-cell"
                @click="showQuickMenu(day.date, timeSlot)"
              >
                + 添加预约
              </span>

              <!-- 多学生垂直堆叠显示 -->
              <div v-else class="students-container">
                <div
                  v-for="student in getStudents(day.date, timeSlot)"
                  :key="student.id"
                  class="student-card"
                  :class="getStatusClass(student.status)"
                  @click="goToStudent(student.student_id)"
                >
                  <div class="student-name">{{ student.name }}</div>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 底部导航 -->
    <nav class="bottom-nav">
      <div class="nav-item" @click="navigateTo('home')">
        <div class="nav-icon">🏠</div>
        <span>预约管理</span>
      </div>
      <div class="nav-item active" @click="navigateTo('calendar')">
        <div class="nav-icon">📅</div>
        <span>课程日历</span>
      </div>
      <div class="nav-item" @click="navigateTo('students')">
        <div class="nav-icon">👥</div>
        <span>学生管理</span>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppointmentStore } from '@/stores/appointment'
import { format, addDays, startOfWeek, endOfWeek, isSameDay, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const router = useRouter()
const appointmentStore = useAppointmentStore()

// 响应式数据
const loading = ref(false)
const currentWeekStart = ref(new Date())
const weekData = ref({})
const touchStartX = ref(0)
const touchEndX = ref(0)
const minSwipeDistance = 50
const isTransitioning = ref(false)

// 时间段配置
const timeSlots = [
  '08:00', '09:00', '10:00', '11:00',
  '14:00', '15:00', '16:00', '17:00',
  '18:00', '19:00', '20:00'
]

// 计算属性
const weekDates = computed(() => {
  const dates = []
  const startDate = startOfWeek(currentWeekStart.value, { weekStartsOn: 1 }) // 周一开始

  for (let i = 0; i < 7; i++) {
    const currentDate = addDays(startDate, i)
    dates.push({
      date: format(currentDate, 'yyyy-MM-dd'),
      displayDate: format(currentDate, 'MM/dd'),
      weekday: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i],
      isToday: isSameDay(currentDate, new Date()),
      isPast: currentDate < new Date().setHours(0, 0, 0, 0)
    })
  }

  return dates
})

const dateRangeText = computed(() => {
  if (weekDates.value.length === 0) return ''
  const start = weekDates.value[0]
  const end = weekDates.value[6]
  return `${start.displayDate} - ${end.displayDate}`
})

// 方法
const fetchWeekData = async () => {
  if (loading.value || isTransitioning.value) return

  loading.value = true
  try {
    console.log('CalendarView: 开始获取周数据')
    // 直接使用appointment store的fetchWeekAppointments方法
    const weekDataMap = await appointmentStore.fetchWeekAppointments(currentWeekStart.value)
    weekData.value = weekDataMap
    console.log('CalendarView: 周数据获取成功', weekDataMap)

    // 预加载相邻周的数据
    preloadAdjacentWeeks()
  } catch (error) {
    console.error('CalendarView: 获取周数据失败:', error)
  } finally {
    loading.value = false
  }
}

const preloadAdjacentWeeks = async () => {
  try {
    const prevWeekStart = format(addDays(currentWeekStart.value, -7), 'yyyy-MM-dd')
    const nextWeekStart = format(addDays(currentWeekStart.value, 7), 'yyyy-MM-dd')

    // 异步预加载，不阻塞主界面
    Promise.all([
      appointmentStore.fetchWeekAppointments(new Date(prevWeekStart)),
      appointmentStore.fetchWeekAppointments(new Date(nextWeekStart))
    ]).catch(error => {
      console.warn('预加载失败:', error)
    })
  } catch (error) {
    console.warn('预加载出错:', error)
  }
}

// 触摸手势处理
const handleTouchStart = (e) => {
  touchStartX.value = e.touches[0].clientX
}

const handleTouchMove = (e) => {
  touchEndX.value = e.touches[0].clientX
}

const handleTouchEnd = () => {
  if (!touchStartX.value || !touchEndX.value) return

  const distance = touchStartX.value - touchEndX.value
  const isLeftSwipe = distance > minSwipeDistance
  const isRightSwipe = distance < -minSwipeDistance

  if (isTransitioning.value) return

  if (isLeftSwipe) {
    // 左滑 - 下一周
    goToNextWeek()
  } else if (isRightSwipe) {
    // 右滑 - 上一周
    goToPreviousWeek()
  }

  // 重置触摸位置
  touchStartX.value = 0
  touchEndX.value = 0
}

const goToPreviousWeek = async () => {
  if (isTransitioning.value) return
  isTransitioning.value = true
  currentWeekStart.value = addDays(currentWeekStart.value, -7)
  await fetchWeekData()
  setTimeout(() => {
    isTransitioning.value = false
  }, 300)
}

const goToNextWeek = async () => {
  if (isTransitioning.value) return
  isTransitioning.value = true
  currentWeekStart.value = addDays(currentWeekStart.value, 7)
  await fetchWeekData()
  setTimeout(() => {
    isTransitioning.value = false
  }, 300)
}

const getDayClass = (day) => {
  return {
    'today': day.isToday,
    'past': day.isPast,
    'weekend': [5, 6].includes(weekDates.value.indexOf(day)) // 周六、周日
  }
}

const getTimeSlotClass = (date, timeSlot) => {
  const dayData = weekDates.value.find(d => d.date === date)
  return {
    'today': dayData?.isToday,
    'past': dayData?.isPast
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

const getStatusClass = (status) => {
  const statusMap = {
    'scheduled': 'status-upcoming',
    'checked': 'status-checked',
    'cancel': 'status-cancel',
    'during': 'status-during'
  }
  return statusMap[status] || ''
}

const goToStudent = (studentId) => {
  router.push({
    name: 'StudentDetail',
    params: { id: studentId }
  })
}

const showQuickMenu = (date, timeSlot) => {
  console.log(`显示快捷菜单：${timeSlot} - ${date}`)
  // TODO: 实现快速创建预约功能
}

const navigateTo = (page) => {
  switch(page) {
    case 'home':
      router.push('/')
      break
    case 'calendar':
      // 当前页面
      break
    case 'students':
      router.push('/students')
      break
  }
}

// 监听周变化
watch(currentWeekStart, () => {
  fetchWeekData()
})

// 生命周期
onMounted(() => {
  fetchWeekData()
})
</script>

<style scoped>
.calendar-page {
  max-width: 430px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f5f5;
  position: relative;
  padding-bottom: 60px;
}

/* 顶部导航栏 */
.header {
  background: #1989fa;
  color: #fff;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header h1 {
  font-size: 18px;
  font-weight: 500;
  transition: transform 0.3s ease;
}

/* 主容器样式 - 移除会导致路由切换冲突的transition */
.calendar-page {
  max-width: 430px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f5f5;
  position: relative;
  padding-bottom: 60px;
  touch-action: pan-y;
  user-select: none;
}

.calendar-page.transitioning {
  pointer-events: none;
  /* 只在周切换时应用过渡效果，避免与路由切换冲突 */
  transition: opacity 0.3s ease;
}

/* 状态图例 */
.status-legend {
  background: #fff;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.legend-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  margin-right: 6px;
  border: 1px solid #d9d9d9;
}

.legend-color.upcoming {
  background: #1890ff;
  border-color: #1890ff;
}

.legend-color.during {
  background: #fa8c16;
  border-color: #fa8c16;
}

.legend-color.checked {
  background: #52c41a;
  border-color: #52c41a;
}

.legend-color.cancel {
  background: #8c8c8c;
  border-color: #8c8c8c;
}

/* 日历表格 */
.calendar-container {
  background: #fff;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.calendar-table {
  border-collapse: collapse;
  width: 100%;
  table-layout: fixed;
  min-width: 600px;
}

.calendar-container.transitioning {
  opacity: 0.8;
  /* 只在周切换时应用过渡效果，避免与路由切换冲突 */
  transition: opacity 0.3s ease;
}

.calendar-table th,
.calendar-table td {
  border: 1px solid #e8e8e8;
  text-align: center;
  vertical-align: middle;
}

.calendar-table th {
  background: #f5f5f5;
  height: 40px;
  font-size: 14px;
  font-weight: 500;
  color: #666;
}

.time-column {
  background: #fafafa;
  width: 70px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
  border-right: 2px solid #e8e8e8;
}

/* 时间段样式 */
.time-slot {
  position: relative;
  border: 1px solid #e8e8e8;
  padding: 8px;
  min-height: 60px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
  background: #f5f5f5;
}

.time-slot:hover {
  filter: brightness(0.95);
}

.time-slot.today {
  border-color: #bae7ff;
  border-width: 2px;
}

/* 学生容器 */
.students-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* 学生卡片 */
.student-card {
  background: inherit;
  color: #000;
  font-weight: 600;
  padding: 6px 8px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  cursor: pointer;
  transition: transform 0.2s;
  text-align: center;
}

.student-card:hover {
  transform: scale(1.02);
}

.student-name {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 状态颜色 */
.status-upcoming {
  background: #1890ff;
  color: #000;
}

.status-checked {
  background: #52c41a;
  color: #000;
}

.status-during {
  background: #fa8c16;
  color: #000;
}

.status-cancel {
  background: #8c8c8c;
  color: #000;
}

/* 空状态 */
.empty-cell {
  color: #999;
  font-size: 12px;
  font-weight: 500;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 3px;
  border: 1px dashed #d9d9d9;
  transition: all 0.2s;
  white-space: nowrap;
  text-align: center;
  display: inline-block;
  cursor: pointer;
}

.empty-cell:hover {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
  border-color: #1890ff;
  transform: scale(1.05);
}

/* 加载状态 */
.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* 底部导航 */
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

/* 响应式设计 */
@media (max-width: 768px) {
  .calendar-table {
    font-size: 12px;
  }

  .time-column {
    width: 60px;
    font-size: 12px;
  }

  .student-card {
    min-height: 40px;
    padding: 4px 6px;
  }

  .student-name {
    font-size: 12px;
  }
}
</style>