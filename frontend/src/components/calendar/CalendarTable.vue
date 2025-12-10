<template>
  <div class="calendar-scroll-container">
    <table class="calendar-table">
      <thead>
        <tr>
          <!-- 动态生成日期列头 -->
          <th
            v-for="day in visibleWeeks.slice(0, 5)"
            :key="day.date"
            class="date-header-cell"
            :class="{ today: day.isToday }"
            style="width: 75px;"
          >
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
            @click="$emit('slot-click', day.date, timeSlot)"
          >
            <span
              v-if="!hasStudents(day.date, timeSlot)"
              class="empty-cell"
            ></span>

            <div v-else class="students-container">
              <StudentCard
                v-for="student in getStudents(day.date, timeSlot)"
                :key="`${student.appointment_id}-${student.student_id}`"
                :student="student"
                :date="day.date"
                :time-slot="timeSlot"
                @click="$emit('slot-click', day.date, timeSlot)"
              />
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StudentCard from './StudentCard.vue'

const props = defineProps({
  timeSlots: {
    type: Array,
    required: true
  },
  visibleWeeks: {
    type: Array,
    required: true
  },
  weekData: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['slot-click', 'student-click'])

const hasStudents = (date, timeSlot) => {
  const dayData = props.weekData[date]
  if (!dayData || !dayData.slots) return false

  // 计算选择的时间对应的UTC时间
  const selectedDateTime = new Date(`${date}T${timeSlot}:00`)
  const utcHour = selectedDateTime.getUTCHours()
  const utcTimeString = utcHour.toString().padStart(2, '0') + ':00'

  // 匹配本地时间或UTC时间，但后续会去重
  const localSlot = dayData.slots.find(s => s.time === timeSlot)
  const utcSlot = dayData.slots.find(s => s.time === utcTimeString)

  const localStudents = localSlot ? localSlot.students || [] : []
  const utcStudents = utcSlot ? utcSlot.students || [] : []

  // 合并学生并去重 - 使用更精确的键去重
  const allStudents = [...localStudents, ...utcStudents]
  const uniqueStudents = []
  const seenKeys = new Set()

  for (const student of allStudents) {
    // 使用 student_id + appointment_id 作为唯一键，如果没有 appointment_id 则只用 student_id
    const uniqueKey = student.appointment_id
      ? `${student.student_id}-${student.appointment_id}`
      : student.student_id

    if (!seenKeys.has(uniqueKey)) {
      seenKeys.add(uniqueKey)
      uniqueStudents.push(student)
    }
  }

  return uniqueStudents.length > 0
}

const getStudents = (date, timeSlot) => {
  const dayData = props.weekData[date]
  if (!dayData || !dayData.slots) return []

  // 计算选择的时间对应的UTC时间
  const selectedDateTime = new Date(`${date}T${timeSlot}:00`)
  const utcHour = selectedDateTime.getUTCHours()
  const utcTimeString = utcHour.toString().padStart(2, '0') + ':00'

  // 匹配本地时间或UTC时间
  const localSlot = dayData.slots.find(s => s.time === timeSlot)
  const utcSlot = dayData.slots.find(s => s.time === utcTimeString)

  const localStudents = localSlot ? localSlot.students || [] : []
  const utcStudents = utcSlot ? utcSlot.students || [] : []

  // 合并学生并去重 - 使用更精确的键去重
  const allStudents = [...localStudents, ...utcStudents]
  const uniqueStudents = []
  const seenKeys = new Set()

  for (const student of allStudents) {
    // 使用 student_id + appointment_id 作为唯一键，如果没有 appointment_id 则只用 student_id
    const uniqueKey = student.appointment_id
      ? `${student.student_id}-${student.appointment_id}`
      : student.student_id

    if (!seenKeys.has(uniqueKey)) {
      seenKeys.add(uniqueKey)
      uniqueStudents.push(student)
    }
  }

  return uniqueStudents
}
</script>

<style scoped>
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

/* 日期列头 */
.date-header-cell {
  background: #f5f5f5;
  font-size: 14px;
  font-weight: 700;
  color: #0050b3;
  padding: 0;
  line-height: 1.2;
  text-align: center;
  border-bottom: 2px solid #e3f2fd;
  border-right: 0.5px solid #e0e0e0;
  vertical-align: middle;
  height: 54px;
  width: 75px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.date-header-cell.today {
  background: #fff7e6 !important;
  color: #d46b08 !important;
  border-bottom: 2px solid #ffd591 !important;
  border-right: 0.5px solid #ffd591 !important;
}

.time-slot {
  position: relative;
  padding: 0;
  height: var(--time-slot-height);
  font-size: 12px;
  cursor: pointer;
  background: #f9f9f9;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  border-right: 0.5px solid #e0e0e0;
  border-left: none;
  border-bottom: 0.5px solid #e0e0e0;
  vertical-align: top;
  width: 75px;
  margin: 0;
}

/* 第一个时间槽不要左边框 */
.time-slot:first-child {
  border-left: none;
}

.time-slot.today {
  background: #fff7e6;
  border-right: 0.5px solid #ffd591;
}

.students-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  box-sizing: border-box;
  padding: 0;
  height: 100%;
}

.empty-cell {
  width: 100%;
  height: 100%;
  background: #fff;
  cursor: pointer;
  position: absolute;
  top: 0;
  left: 0;
  margin: 0;
}

.time-slot.today .empty-cell {
  background: #fff7e6;
}
</style>