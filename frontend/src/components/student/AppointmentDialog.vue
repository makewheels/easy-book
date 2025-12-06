<template>
  <div v-if="show" class="appointment-dialog" @click.self="$emit('close')">
    <div class="dialog-content">
      <div class="dialog-header">
        <h3>新增预约 - {{ studentName }}</h3>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="dialog-body">
        <div class="form-group">
          <label>选择日期</label>
          <div class="calendar-input">
            <input
              type="date"
              v-model="form.selectedDate"
              :min="minDate"
              class="date-picker"
            />
          </div>
          <div class="date-options">
            <button
              v-for="option in dateOptions"
              :key="option.value"
              type="button"
              class="date-btn"
              :class="{ active: form.selectedDate === option.value }"
              @click="selectDate(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div class="form-group">
          <label>选择开始时间</label>
          <div class="time-groups">
            <div v-for="group in timeGroups" :key="group.label" class="time-group">
              <div class="time-group-content">
                <div class="time-group-label">{{ group.label }}</div>
                <div class="time-grid" :class="{ 'nowrap-grid': group.nowrap }">
                  <button
                    v-for="hour in group.hours"
                    :key="hour"
                    type="button"
                    class="time-btn"
                    :class="{ active: form.selectedHour === hour }"
                    @click="selectTime(hour)"
                  >
                    {{ hour }}:00
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>课程时长</label>
          <div class="duration-options">
            <button
              v-for="option in durationOptions"
              :key="option.value"
              type="button"
              class="duration-btn"
              :class="{
                active: form.duration === option.value,
                disabled: option.disabled
              }"
              :disabled="option.disabled"
              @click="!option.disabled && selectDuration(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div class="form-group" v-if="form.startDateTime && form.duration">
          <label>结束时间</label>
          <div class="end-time-display">
            {{ formatEndTime }}
          </div>
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <div class="dialog-actions">
          <button class="btn-cancel" @click="$emit('close')">
            取消
          </button>
          <button class="btn-confirm" @click="handleSubmit">
            确认预约
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  studentName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'submit'])

// 格式化日期函数
const formatDate = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const form = reactive({
  selectedDate: '',
  selectedHour: null,
  duration: 60  // 默认1小时，单位分钟
})

const errorMessage = ref('')

// 初始化默认选择明天的日期
const initializeDefaultDate = () => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  form.selectedDate = formatDate(tomorrow)
}

// 在组件创建时初始化默认日期
initializeDefaultDate()

// 时间分组
const timeGroups = [
  {
    label: '上午',
    hours: [7, 8, 9, 10, 11, 12]
  },
  {
    label: '下午',
    hours: [13, 14, 15, 16, 17]
  },
  {
    label: '晚上',
    hours: [18, 19],
    nowrap: true
  }
]

// 可选的小时列表（7:00 - 19:00）
const availableHours = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

// 日期快捷选项
const dateOptions = computed(() => {
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  const dayAfterTomorrow = new Date(today)
  dayAfterTomorrow.setDate(today.getDate() + 2)

  // 获取月日
  const getMonthDay = (date) => {
    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}/${day}`
  }

  return [
    {
      value: formatDate(today),
      label: `今天 (${getMonthDay(today)})`
    },
    {
      value: formatDate(tomorrow),
      label: `明天 (${getMonthDay(tomorrow)})`
    },
    {
      value: formatDate(dayAfterTomorrow),
      label: `后天 (${getMonthDay(dayAfterTomorrow)})`
    }
  ]
})

// 最小可选日期为今天
const minDate = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
})

// 选择日期
const selectDate = (dateValue) => {
  form.selectedDate = dateValue
  errorMessage.value = '' // 清除错误消息
}

// 计算结束时间显示
const formatEndTime = computed(() => {
  if (!form.selectedDate || form.selectedHour === null || !form.duration) return ''

  const startDate = new Date(`${form.selectedDate}T${String(form.selectedHour).padStart(2, '0')}:00:00`)
  const endDate = new Date(startDate.getTime() + form.duration * 60 * 1000)

  const year = endDate.getFullYear()
  const month = String(endDate.getMonth() + 1).padStart(2, '0')
  const day = String(endDate.getDate()).padStart(2, '0')
  const hours = String(endDate.getHours()).padStart(2, '0')
  const minutes = String(endDate.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}`
})

// 选择时间
const selectTime = (hour) => {
  form.selectedHour = hour
  errorMessage.value = '' // 清除错误消息
}

// 选择时长
const selectDuration = (duration) => {
  form.duration = duration
}

const durationOptions = [
  { value: 60, label: '1小时 (目前固定)', disabled: true }
]

const handleSubmit = () => {
  // 清除之前的错误消息
  errorMessage.value = ''

  // 表单验证
  if (!form.selectedDate) {
    errorMessage.value = '请选择预约日期'
    return
  }

  if (form.selectedHour === null) {
    errorMessage.value = '请选择预约时间'
    return
  }

  // 构建开始时间
  const startDateTime = new Date(`${form.selectedDate}T${String(form.selectedHour).padStart(2, '0')}:00:00`)

  emit('submit', {
    start_time: startDateTime.toISOString(),
    duration_in_minutes: form.duration
  })
}
</script>

<style scoped>
.appointment-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog-content {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  max-height: 90vh;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #666;
}

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.calendar-input {
  margin-bottom: 12px;
}

/* 日期选项样式 */
.date-options {
  display: flex;
  gap: 8px;
}

.date-btn {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: #fff;
  color: #333;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.date-btn:hover {
  border-color: #1989fa;
  background: #f0f9ff;
}

.date-btn.active {
  background: #1989fa;
  color: #fff;
  border-color: #1989fa;
}

.date-picker {
  width: 100%;
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.3s ease;
}

.date-picker:focus {
  outline: none;
  border-color: #1989fa;
}

/* 时长选项样式 */
.duration-options {
  display: flex;
  gap: 8px;
}

.duration-btn {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: #fff;
  color: #333;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.duration-btn:hover {
  border-color: #1989fa;
  background: #f0f9ff;
}

.duration-btn.active {
  background: #1989fa;
  color: #fff;
  border-color: #1989fa;
}

.duration-btn.disabled {
  background: #f5f5f5;
  color: #bfbfbf;
  border-color: #e8e8e8;
  cursor: not-allowed;
  box-shadow: none;
}

.duration-btn.disabled:hover {
  background: #f5f5f5;
  color: #bfbfbf;
  border-color: #e8e8e8;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #1989fa;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-cancel {
  background: #fff;
  color: #1989fa;
  border: 2px solid #1989fa;
}

.btn-cancel:hover {
  background: #f0f9ff;
}

.btn-confirm {
  background: #1989fa;
  color: #fff;
}

.btn-confirm:hover {
  background: #096dd9;
}

.btn-confirm:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 时间分组容器 */
.time-groups {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.time-group {
  margin-bottom: 0;
}

.time-group-content {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 12px;
}

.time-group-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  padding: 10px 0;
  min-width: 40px;
  text-align: right;
  flex-shrink: 0;
}

/* 时间选择网格 */
.time-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 8px;
  padding: 4px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fafafa;
  flex: 1;
}

.time-grid.nowrap-grid {
  flex: 1;
  grid-template-columns: repeat(2, minmax(60px, 1fr));
  justify-content: flex-start;
  gap: 8px;
  padding: 4px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fafafa;
}

.time-btn {
  padding: 10px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: #fff;
  color: #333;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.time-btn:hover {
  border-color: #1989fa;
  background: #f0f9ff;
}

.time-btn.active {
  background: #1989fa;
  color: #fff;
  border-color: #1989fa;
}

.end-time-display {
  padding: 12px;
  background: #f8f9fa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.error-message {
  padding: 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  font-size: 14px;
  color: #ff4d4f;
  font-weight: 500;
  margin-bottom: 20px;
}
</style>