<template>
  <div class="calendar-page">
    <div class="calendar-container">
      <div v-if="loading" class="loading">
        加载中...
      </div>

      <div v-else class="calendar-wrapper" ref="calendarWrapper">
        <div class="calendar-layout">
          <!-- 左侧时间列 - 固定不动 -->
          <TimeColumn :time-slots="timeSlots" />

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
            <CalendarTable
              :time-slots="timeSlots"
              :visible-weeks="visibleWeeks"
              :week-data="weekData"
              @slot-click="goToCalendarAppointment"
              @student-click="goToStudent"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <BottomNavigation :active-tab="'calendar'" @navigate="navigateTo" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAppointmentStore } from '@/stores/appointment'
import { appointmentApi } from '@/api/appointment'
import { format, addDays, isSameDay, addWeeks, subWeeks } from 'date-fns'
import BottomNavigation from '@/components/BottomNavigation.vue'
import TimeColumn from '@/components/calendar/TimeColumn.vue'
import CalendarTable from '@/components/calendar/CalendarTable.vue'

const router = useRouter()
const appointmentStore = useAppointmentStore()

const loading = ref(false)
const scrollContainer = ref(null)
const calendarWrapper = ref(null)

// Infinite scrolling setup - 进一步减少初始加载数量
const weeksBefore = ref(0) // 显示前0周（不显示过去周）
const weeksAfter = ref(2)  // 显示后2周（当前周+未来2周）
const currentWeekIndex = ref(0) // 当前周在数组中的索引
const dayWidth = 120 // 每天的宽度
const timeColumnWidth = 60 // 时间列宽度
const weekDays = 6 // 每周显示6天（周二到周日）

// 时间槽定义
const timeSlots = [
  '07:00', '08:00', '09:00', '10:00', '11:00',
  '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
  '18:00', '19:00'
]

// 计算显示的起始日期（昨天）
const getDisplayStart = () => {
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  return yesterday
}

const currentWeekStart = ref(getDisplayStart())
const weekData = ref({})

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

// 批量获取多周数据 - 使用新的批量接口优化性能
const fetchWeeksData = async (weekStartDates) => {
  loading.value = true
  try {
    // 计算日期范围
    const allDates = []
    weekStartDates.forEach(startDate => {
      for (let dayOffset = 0; dayOffset < 7; dayOffset++) {
        const currentDate = format(addDays(startDate, dayOffset), 'yyyy-MM-dd')
        if (!allDates.includes(currentDate)) {
          allDates.push(currentDate)
        }
      }
    })

    // 按日期排序
    allDates.sort()

    // 获取开始和结束日期
    const startDate = allDates[0]
    const endDate = allDates[allDates.length - 1]

    console.log(`使用批量接口获取预约数据: ${startDate} 到 ${endDate}`)

    // 调用批量接口
    const response = await appointmentApi.getBatchAppointments(startDate, endDate)
    weekData.value = response.data || {}

    console.log(`批量获取完成，共 ${Object.keys(response.data || {}).length} 天的数据`)
  } catch (error) {
    console.error('批量获取数据失败，回退到逐周获取:', error)

    // 回退到原来的逐周获取方式
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
  let weekStartDate = new Date(startDate)

  while (weekStartDate <= endDate) {
    weekDates.push(new Date(weekStartDate))
    weekStartDate = addDays(weekStartDate, 7) // 移动到下周
  }

  await fetchWeeksData(weekDates)
}

// 预加载额外数据
const preloadWeekData = async (direction) => {
  // 这里简化处理，因为我们现在使用连续日期显示
  // 在实际滚动时，会通过fetchInitialData获取更多数据
  console.log(`预加载 ${direction} 侧数据`)
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

// 简单可靠的高度更新函数
const updateCalendarHeights = () => {
  const viewportHeight = window.innerHeight
  const slotHeight = Math.max(30, Math.floor((viewportHeight - 124) / 13))

  const calendarPage = document.querySelector('.calendar-page')
  if (calendarPage) {
    calendarPage.style.setProperty('--time-slot-height', slotHeight + 'px')
    console.log('Updated height to:', slotHeight + 'px (viewport:', viewportHeight + ')')
  }
}

// 保留简单的syncHeights用于初始调用
const syncHeights = updateCalendarHeights

// 初始化滚动位置到今天（第二列）
const initializeScrollPosition = () => {
  if (scrollContainer.value) {
    // 今天是第二列，所以滚动到第二列的位置
    const todayOffset = 1 * dayWidth // 第二列偏移量
    scrollContainer.value.scrollLeft = todayOffset
  }

  // 同步高度
  syncHeights()
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
  console.log('Calendar: component mounting...')

  await fetchInitialData()
  await nextTick()
  initializeScrollPosition()

  // 立即执行一次高度更新
  console.log('Calendar: calling updateCalendarHeights')
  updateCalendarHeights()

  // 添加简单可靠的全局监听器
  if (!window.calendarHeightListener) {
    window.calendarHeightListener = true
    window.addEventListener('resize', updateCalendarHeights)
    console.log('Calendar: Global resize listener added')
  }

  // 延迟执行一次确保DOM已完全加载
  setTimeout(updateCalendarHeights, 500)
})

// 组件卸载时清理事件监听器
onUnmounted(() => {
  console.log('Calendar: component unmounting')
  // 全局监听器不需要清理，让它保持工作
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
  --header-height: 54px;
  --footer-height: 70px;
  --time-slot-height: 54px; /* JavaScript会动态更新这个值 */
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
  align-self: flex-start;
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