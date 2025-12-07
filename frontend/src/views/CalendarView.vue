<template>
  <div class="calendar-page">
    <div class="calendar-container">
      <div v-if="loading" class="loading">
        加载中...
      </div>

      <div v-else class="calendar-wrapper" ref="calendarWrapper">
        <div class="calendar-layout">
          <!-- 左侧时间列 - 固定不动 -->
          <div class="time-column">
            <div class="time-header"></div>
            <div v-for="timeSlot in timeSlots" :key="timeSlot" class="time-cell-fixed">
              {{ timeSlot }}
            </div>
          </div>

          <!-- 右侧日期列 - 可滚动 -->
          <div
            class="calendar-scroll-container"
            @scroll="handleScroll"
            @touchstart="handleTouchStart"
            @touchmove="handleTouchMove"
            @touchend="handleTouchEnd"
            @wheel="handleWheel"
            ref="scrollContainer"
          >
            <table class="calendar-table">
            <thead>
              <tr>
                <!-- 动态生成日期列头 -->
                <th v-for="day in visibleWeeks.slice(0, 5)" :key="day.date" class="date-header-cell" :class="{ today: day.isToday }" style="width: 75px;">
                  {{ day.weekday }}<br>{{ day.displayDate }}
                </th>
              </tr>
            </thead>
            <tbody>
              <!-- 时间行和内容 -->
              <tr v-for="timeSlot in timeSlots" :key="timeSlot">
                <!-- 动态生成每个日期的时间段单元格 -->
                <td
                  v-for="day in visibleWeeks.slice(0, 5)"
                  :key="`${day.date}-${timeSlot}`"
                  class="time-slot"
                  :class="{ today: day.isToday }"
                  style="width: 75px;"
                  @click="goToCalendarAppointment(day.date, timeSlot)"
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
                </td>
              </tr>
            </tbody>
          </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <BottomNavigation :active-tab="'calendar'" @navigate="navigateTo" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAppointmentStore } from '@/stores/appointment'
import { format, addDays, isSameDay, addWeeks, subWeeks } from 'date-fns'
import BottomNavigation from '@/components/BottomNavigation.vue'

const router = useRouter()
const appointmentStore = useAppointmentStore()

const loading = ref(false)
const scrollContainer = ref(null)
const calendarWrapper = ref(null)

// Infinite scrolling setup
const weeksBefore = ref(4) // 显示前4周
const weeksAfter = ref(4)  // 显示后4周
const currentWeekIndex = ref(4) // 当前周在数组中的索引
const dayWidth = 120 // 每天的宽度
const timeColumnWidth = 60 // 时间列宽度
const weekDays = 6 // 每周显示6天（周二到周日）

// 计算显示的起始日期（昨天）
const getDisplayStart = () => {
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  return yesterday
}

const currentWeekStart = ref(getDisplayStart())
const weekData = ref({})

const timeSlots = [
  '07:00', '08:00', '09:00', '10:00', '11:00',
  '12:00', '14:00', '15:00', '16:00', '17:00',
  '18:00', '19:00'
]

// 计算所有可见的日期（从昨天开始连续显示）
const visibleWeeks = computed(() => {
  const dates = []
  const totalDays = (weeksBefore.value + weeksAfter.value + 1) * weekDays // 总天数

  for (let dayIndex = 0; dayIndex < totalDays; dayIndex++) {
    const currentDate = addDays(currentWeekStart.value, dayIndex)
    const dayOfWeek = currentDate.getDay() === 0 ? 7 : currentDate.getDay()

    const dateStr = format(currentDate, 'yyyy-MM-dd')
    const isToday = isSameDay(currentDate, new Date())

    const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    const weekdayIndex = dayOfWeek - 1

    dates.push({
      date: dateStr,
      displayDate: format(currentDate, 'MM/dd'),
      weekday: weekdayNames[weekdayIndex],
      isToday: isToday,
      dayIndex: dayIndex
    })
  }

  return dates
})

// 计算总宽度
const totalWidth = computed(() => {
  return timeColumnWidth + (visibleWeeks.value.length * dayWidth)
})


const todayDate = computed(() => {
  return format(new Date(), 'yyyy-MM-dd')
})

// 批量获取多周数据
const fetchWeeksData = async (weekStartDates) => {
  loading.value = true
  try {
    const weekDataPromises = weekStartDates.map(startDate =>
      appointmentStore.fetchWeekAppointments(startDate)
    )
    const weekDataResults = await Promise.all(weekDataPromises)

    // 合并所有周数据
    const combinedData = {}
    weekDataResults.forEach(weekDataMap => {
      Object.assign(combinedData, weekDataMap)
    })

    weekData.value = combinedData
  } catch (error) {
    console.error('获取周数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化获取数据
const fetchInitialData = async () => {
  // 获取所有可见日期的数据
  const startDate = currentWeekStart.value
  const totalDays = (weeksBefore.value + weeksAfter.value + 1) * weekDays
  const endDate = addDays(startDate, totalDays - 1)

  // 按周获取数据以确保API兼容性
  const weekDates = []
  let currentWeekStart = new Date(startDate)

  while (currentWeekStart <= endDate) {
    weekDates.push(new Date(currentWeekStart))
    currentWeekStart = addDays(currentWeekStart, 7) // 移动到下周
  }

  await fetchWeeksData(weekDates)
}

// 预加载额外数据
const preloadWeekData = async (direction) => {
  // 这里简化处理，因为我们现在使用连续日期显示
  // 在实际滚动时，会通过fetchInitialData获取更多数据
  console.log(`预加载 ${direction} 侧数据`)
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

const goToCalendarAppointment = (date, time) => {
  router.push({
    name: 'CalendarAppointment',
    query: { date, time }
  })
}

// 触摸处理相关
const touchStartX = ref(0)
const touchStartY = ref(0)
const touchEndX = ref(0)
const touchEndY = ref(0)

// 滚动处理（添加防抖）
let scrollTimeout = null
const handleScroll = async (event) => {
  const container = event.target

  // 清除之前的超时
  if (scrollTimeout) {
    clearTimeout(scrollTimeout)
  }

  // 设置新的超时，减少频繁触发
  scrollTimeout = setTimeout(async () => {
    const scrollLeft = container.scrollLeft
    const containerWidth = container.clientWidth
    const totalWidth = container.scrollWidth

    // 计算滚动位置百分比
    const scrollPercentage = scrollLeft / (totalWidth - containerWidth)

    // 当滚动到左边缘时，扩展左侧
    if (scrollPercentage < 0.15) {
      await extendCalendarLeft()
    }
    // 当滚动到右边缘时，扩展右侧
    else if (scrollPercentage > 0.85) {
      await extendCalendarRight()
    }
  }, 150) // 150ms 防抖延迟
}

// 触摸开始
const handleTouchStart = (event) => {
  touchStartX.value = event.touches[0].clientX
  touchStartY.value = event.touches[0].clientY
}

// 触摸移动
const handleTouchMove = (event) => {
  const container = scrollContainer.value
  if (!container) return

  const deltaX = event.touches[0].clientX - touchStartX.value

  // 如果是水平滑动，阻止默认的垂直滚动
  if (Math.abs(deltaX) > Math.abs(event.touches[0].clientY - touchStartY.value)) {
    event.preventDefault()
  }
}

// 触摸结束
const handleTouchEnd = async (event) => {
  touchEndX.value = event.changedTouches[0].clientX
  touchEndY.value = event.changedTouches[0].clientY

  const deltaX = touchEndX.value - touchStartX.value
  const deltaY = touchEndY.value - touchStartY.value

  // 确保是水平滑动
  if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
    const container = scrollContainer.value
    if (!container) return

    const currentScrollLeft = container.scrollLeft

    // 直接根据滑动距离滚动
    const scrollDistance = deltaX * 1.5 // 放大滑动灵敏度

    container.scrollTo({
      left: Math.max(0, currentScrollLeft - scrollDistance),
      behavior: 'auto'
    })
  }
}

// 鼠标滚轮处理（为电脑端优化）
const handleWheel = (event) => {
  event.preventDefault()

  const container = scrollContainer.value
  if (!container) return

  const currentScrollLeft = container.scrollLeft
  const wheelDelta = event.deltaY

  // 降低滚轮灵敏度，减小滚动量
  const scrollAmount = Math.abs(wheelDelta) * 0.3 // 将灵敏度降低到30%
  const maxScroll = Math.min(scrollAmount, dayWidth * 0.5) // 限制最大滚动量为半列宽度

  if (wheelDelta > 0) {
    // 向下滚动 - 向左（未来日期）
    container.scrollTo({
      left: currentScrollLeft + maxScroll,
      behavior: 'auto'
    })
  } else {
    // 向上滚动 - 向右（过去日期）
    container.scrollTo({
      left: Math.max(0, currentScrollLeft - maxScroll),
      behavior: 'auto'
    })
  }
}

// 向左扩展日历
const extendCalendarLeft = async () => {
  // 在左侧增加更多的天数
  const currentStart = new Date(currentWeekStart.value)
  currentWeekStart.value = addDays(currentStart, -7) // 向左扩展7天

  // 预加载新数据
  await preloadWeekData('left')

  // 保持滚动位置
  await nextTick()
  if (scrollContainer.value) {
    const additionalWidth = 7 * dayWidth
    scrollContainer.value.scrollLeft += additionalWidth
  }
}

// 向右扩展日历
const extendCalendarRight = async () => {
  // 预加载新数据
  await preloadWeekData('right')
}

// 初始化滚动位置到今天（第二列）
const initializeScrollPosition = () => {
  if (scrollContainer.value) {
    // 今天是第二列，所以滚动到第二列的位置
    const todayOffset = 1 * dayWidth // 第二列偏移量
    scrollContainer.value.scrollLeft = todayOffset
  }
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

onMounted(async () => {
  await fetchInitialData()
  await nextTick()
  initializeScrollPosition()
})
</script>

<style scoped>
.calendar-page {
  max-width: none;
  margin: 0;
  padding: 0;
  height: 100vh;
  background: #f5f5f5;
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
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
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

.calendar-wrapper {
  background: #fff;
  padding: 0px 20px 0px 0;
  position: relative;
  margin: 0px 10px 0px 10px;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 新的布局容器 */
.calendar-layout {
  display: flex;
  height: 100%;
  flex: 1;
  margin-bottom: 0;
  align-items: stretch;
}

/* 左侧时间列 - 固定 */
.time-column {
  width: 60px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  margin-top: 0px;
}

.time-header {
  height: 50px;
  background: #f5f5f5;
  border-bottom: 2px solid #e3f2fd;
  border-right: 1px solid #e0e0e0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.time-cell-fixed {
  background: #f9f9f9;
  font-size: 12px;
  font-weight: 700;
  color: #0050b3;
  border-bottom: 1px solid #e0e0e0;
  border-right: 1px solid #e0e0e0;
  padding: 2px 2px;
  text-align: center;
  vertical-align: middle;
  height: calc((100vh - 70px - 50px) / 12);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
  box-sizing: border-box;
}

/* 右侧滚动容器 */
.calendar-scroll-container {
  overflow-y: hidden;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: auto;
  scrollbar-width: thin;
  scrollbar-color: #d9d9d9 #f5f5f5;
  flex: 1;
  height: 100%;
  display: flex;
  margin-top: 0;
  padding-top: 0;
}

.calendar-scroll-container::-webkit-scrollbar {
  height: 6px;
}

.calendar-scroll-container::-webkit-scrollbar-track {
  background: #f5f5f5;
}

.calendar-scroll-container::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.calendar-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

/* Table 样式 */
.calendar-table {
  width: 100%;
  height: 100%;
  border-collapse: collapse;
  background: #fff;
  table-layout: fixed;
  display: table !important;
  margin: 0;
  padding: 0;
  border-spacing: 0;
}

.calendar-table thead,
.calendar-table tbody,
.calendar-table tr,
.calendar-table th,
.calendar-table td {
  display: table-cell !important;
}

.calendar-table thead,
.calendar-table tbody {
  display: table-row-group !important;
}

.calendar-table tr {
  display: table-row !important;
}

/* 时间列头 */
.time-header-cell {
  background: #f5f5f5;
  font-size: 14px;
  font-weight: 700;
  color: #0050b3;
  border-bottom: 2px solid #e3f2fd;
  border-right: 2px solid #e0e0e0;
  padding: 8px 2px;
  text-align: center;
  width: 25px;
  vertical-align: middle;
  height: 35px;
}

/* 时间单元格 */
.time-cell {
  background: #f9f9f9;
  font-size: 14px;
  font-weight: 700;
  color: #0050b3;
  border-bottom: 1px solid #e0e0e0;
  border-right: 2px solid #e0e0e0;
  padding: 8px 1px;
  text-align: center;
  vertical-align: middle;
  height: 50px;
  width: 25px;
}

/* 日期列头 */
.date-header-cell {
  background: #f5f5f5;
  font-size: 14px;
  font-weight: 700;
  color: #0050b3;
  padding: 8px 2px;
  line-height: 1.2;
  text-align: center;
  border-bottom: 2px solid #e3f2fd;
  border-right: 1px solid #e0e0e0;
  vertical-align: middle;
  height: 50px;
  width: 75px;
}

.date-header-cell.today {
  background: #fff7e6 !important;
  color: #d46b08 !important;
  border-bottom: 2px solid #ffd591 !important;
  border-right: 1px solid #ffd591 !important;
}

.time-slot {
  position: relative;
  padding: 0;
  height: calc((100vh - 70px - 50px) / 12);
  font-size: 12px;
  cursor: pointer;
  background: #f9f9f9;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  border-right: none;
  border-left: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  vertical-align: top;
  width: 75px;
}

/* 第一个时间槽不要左边框 */
.time-slot:first-child {
  border-left: none;
}

.time-slot.today {
  background: #fff7e6;
  border-right: 1px solid #ffd591;
}

.students-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  box-sizing: border-box;
  padding: 0;
  height: 100%;
}

.student-card {
  background: #fff;
  color: #1a1a1a;
  font-weight: 700;
  padding: 8px 4px;
  height: 100%;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  text-align: center;
  box-sizing: border-box;
  line-height: 1.2;
  margin: 0;
  border: none;
}

.student-name {
  font-size: 16px;
  font-weight: 800;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 状态颜色 - 填满整个单元格 */
.status-upcoming {
  background: #1890ff;
  color: #fff;
}

.status-active {
  background: #faad14;
  color: #fff;
}

.status-checked {
  background: #52c41a;
  color: #fff;
}

.status-during {
  background: #d9d9d9;
  color: #666;
}

.status-cancel {
  background: #f5f5f5;
  color: #bfbfbf;
}

.empty-cell {
  width: 100%;
  height: 100%;
  background: #fff;
  border: 1px dashed #e8e8e8;
  cursor: pointer;
  position: absolute;
  top: 0;
  left: 0;
  margin: 0;
}

.time-slot.today .empty-cell {
  background: #fff7e6;
  border: 1px dashed #ffd591;
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
    font-size: 14px;
  }

  .student-name {
    font-size: 14px;
  }
}
</style>