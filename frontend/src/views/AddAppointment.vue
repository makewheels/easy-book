<template>
  <div class="add-appointment-page">
    <div class="header">
      <BackButton />
      <h1>新增预约 - {{ studentName }}</h1>
    </div>

    <div class="content">
      <form @submit.prevent="handleSubmit" class="appointment-form">
        <div class="form-section">
          <h3>请选择日期</h3>

          <div class="form-group">
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
        </div>

        <div class="form-section">
          <h3>请选择时间</h3>

          <div class="form-group">
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
        </div>

        <div class="form-section">
          <h3>请选择课程时长</h3>

          <div class="form-group">
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
        </div>

    
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="handleCancel">
            取消
          </button>
          <button type="submit" class="btn-save" :disabled="loading">
            {{ loading ? '预约中...' : '确认预约' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppointmentStore } from '@/stores/appointment'
import { useStudentStore } from '@/stores/student'
import { toast } from '@/utils/toast'
import BackButton from '@/components/common/BackButton.vue'

const route = useRoute()
const router = useRouter()
const appointmentStore = useAppointmentStore()
const studentStore = useStudentStore()

const loading = ref(false)
const errorMessage = ref('')
const studentId = route.params.studentId

// 获取学生信息
const student = ref(null)
const studentName = computed(() => student.value?.name || '未知学员')

// 表单数据
const form = reactive({
  selectedDate: '',
  selectedHour: null,
  duration: 60  // 默认1小时，单位分钟
})

// 计算属性
const minDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

const startDateTime = computed(() => {
  if (form.selectedDate && form.selectedHour !== null) {
    return new Date(`${form.selectedDate}T${form.selectedHour.toString().padStart(2, '0')}:00:00`)
  }
  return null
})

const formatEndTime = computed(() => {
  if (startDateTime && form.duration) {
    const endTime = new Date(startDateTime.getTime() + form.duration * 60 * 1000)
    return endTime.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  return ''
})

// 日期选项
const dateOptions = computed(() => {
  const options = []
  const today = new Date()

  // 提供未来6天的选项（包括今天）
  for (let i = 0; i < 6; i++) {
    const date = new Date(today)
    date.setDate(today.getDate() + i)

    const month = date.getMonth() + 1
    const day = date.getDate()
    const dateStr = `${month}/${day}`

    let label
    if (i === 0) {
      label = `今天 ${dateStr}`
    } else if (i === 1) {
      label = `明天 ${dateStr}`
    } else if (i === 2) {
      label = `后天 ${dateStr}`
    } else {
      // 第4天及以后只显示日期，去掉星期文字
      label = dateStr
    }

    options.push({
      label,
      value: date.toISOString().split('T')[0]
    })
  }

  return options
})

// 时间选项
const timeGroups = computed(() => {
  const groups = [
    {
      label: '上午',
      hours: [7, 8, 9, 10, 11],
      nowrap: false
    },
    {
      label: '下午',
      hours: [12, 14, 15, 16, 17],
      nowrap: false
    },
    {
      label: '晚上',
      hours: [18, 19],
      nowrap: false
    }
  ]

  return groups
})

// 时长选项
const durationOptions = computed(() => {
  return [
    { value: 60, label: '1小时 (目前固定)', disabled: true }
  ]
})

// 方法
const selectDate = (date) => {
  form.selectedDate = date
  errorMessage.value = ''
}

const selectTime = (hour) => {
  form.selectedHour = hour
  errorMessage.value = ''
}

const selectDuration = (duration) => {
  form.duration = duration
  errorMessage.value = ''
}

const handleCancel = () => {
  router.back()
}

const handleSubmit = async () => {
  // 验证表单
  if (!form.selectedDate || form.selectedHour === null || !form.duration) {
    toast.warning('请填写所有必填字段')
    return
  }

  
  loading.value = true
  errorMessage.value = ''

  try {
    // 构建完整的datetime字符串，保持本地时间不变
    const timeString = `${form.selectedHour.toString().padStart(2, '0')}:00`
    const startDateTime = `${form.selectedDate}T${timeString}`

    const appointmentData = {
      student_id: studentId,
      start_time: startDateTime,
      duration_in_minutes: form.duration
    }

    await appointmentStore.createAppointment(appointmentData)

    toast.success('预约成功')
    router.push(`/student/${studentId}`)
  } catch (error) {
    errorMessage.value = error.message || '创建失败'
    toast.error(error.message || '创建失败')
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(async () => {
  try {
    await studentStore.fetchStudentById(studentId)
    student.value = studentStore.currentStudent

    // 默认选择明天
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    form.selectedDate = tomorrow.toISOString().split('T')[0]
  } catch (error) {
    toast.error('获取学生信息失败')
    router.back()
  }
})
</script>

<style scoped>
.add-appointment-page {
  min-height: 100vh;
  background: #f5f5f5;
  position: relative;
  font-size: 20px;
}

.header {
  background: #fff;
  color: #1a1a1a;
  padding: 16px 20px;
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
}

.header h1 {
  font-size: 20px;
  margin: 0;
  font-weight: 600;
}

.content {
  padding: 20px 0;
  margin: 0;
}

.appointment-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin: 0;
  border: 1px solid #e0e0e0;
  overflow: hidden;
}

.form-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  margin: -20px -20px 20px -20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e8e8e8;
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  min-height: 44px;
  box-sizing: border-box;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
  color: #1a1a1a;
  font-weight: 600;
}

.calendar-input {
  margin-bottom: 15px;
}

.date-picker {
  width: 100%;
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  font-size: 16px;
  font-family: inherit;
  box-sizing: border-box;
  background: #fff;
  transition: border-color 0.3s ease;
}

.date-picker:focus {
  outline: none;
  border-color: #1989fa;
}

.date-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.date-btn {
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
  color: #1a1a1a;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 44px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.date-btn.active {
  background: #1989fa;
  color: #fff;
  border-color: #1989fa;
}

.date-btn:hover:not(.active) {
  border-color: #1989fa;
  color: #1989fa;
}

.time-groups {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.time-group {
  border: none;
  padding: 16px;
  padding-top: 0px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.time-group:last-child {
  border-bottom: none;
}

.time-group-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.time-group-label {
  font-weight: 600;
  color: #1a1a1a;
  min-width: 60px;
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 8px;
  border: none;
  background: none;
}

.time-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  flex: 1;
}

.time-btn {
  padding: 12px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
  color: #1a1a1a;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  height: 44px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.time-btn.active {
  background: #1989fa;
  color: #fff;
  border-color: #1989fa;
}

.time-btn:hover:not(.active) {
  border-color: #1989fa;
  color: #1989fa;
}

.duration-options {
  display: flex;
  gap: 12px;
}

.duration-btn {
  flex: 1;
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
  color: #1a1a1a;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.duration-btn.active {
  background: #1989fa;
  color: #fff;
  border-color: #1989fa;
}

.duration-btn:hover:not(.active):not(.disabled) {
  border-color: #1989fa;
  color: #1989fa;
}

.duration-btn.disabled {
  background: #f5f5f5;
  color: #ccc;
  cursor: not-allowed;
}

.end-time-display {
  padding: 16px;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.error-message {
  padding: 12px 16px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  color: #ff4d4f;
  font-size: 14px;
  margin: 0 0 20px 0;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin: 0 20px 20px 20px;
}

.btn-save,
.btn-cancel {
  flex: 1;
  padding: 16px 20px;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-save {
  background: #1989fa;
  color: #fff;
  border: 2px solid #1989fa;
}

.btn-save:hover:not(:disabled) {
  background: #096dd9;
  border-color: #096dd9;
}

.btn-cancel {
  background: #fff;
  color: #1989fa;
  border: 2px solid #1989fa;
}

.btn-cancel:hover {
  background: #f0f9ff;
  color: #1989fa;
  border-color: #1989fa;
}

.btn-save:disabled {
  background: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .time-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
  }

  .duration-options {
    flex-direction: column;
  }

  .date-options {
    flex-direction: column;
  }
}
</style>