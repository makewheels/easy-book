<template>
  <div class="page">
    <div class="header">
      <BackButton to="/calendar" />
      <h1>日历预约</h1>
    </div>

    <div class="content">
      <div v-if="loading" class="loading">
        加载中...
      </div>

      <div v-else>
        <div class="appointment-form">
          <!-- 预约时间信息 -->
          <div class="form-section">
            <h3>预约时间</h3>

            <div class="date-line mb-3">
              <div class="label-section">
                <span class="label">日期</span>
              </div>
              <div class="value-section">
                <span class="value text-primary">{{ formatDisplayDate }} {{ formatWeekday }}</span>
              </div>
            </div>
            <div class="time-line mb-3">
              <div class="label-section">
                <span class="label">开始时间</span>
              </div>
              <div class="value-section">
                <span class="value text-primary">{{ selectedTime }}</span>
              </div>
            </div>
            <div class="time-line">
              <div class="label-section">
                <span class="label">课程时长</span>
              </div>
              <div class="value-section">
                <span class="value text-primary">1小时 (目前固定)</span>
              </div>
            </div>
          </div>

          <!-- 已预约学生 -->
          <div class="existing-section">
            <h3 class="section-title">
              已预约学员{{ existingAppointments.length > 0 ? `（总共${existingAppointments.length}人）` : '' }}
            </h3>
            <div v-if="existingAppointments.length > 0" class="existing-students">
              <div
                v-for="appointment in existingAppointments"
                :key="appointment.id"
                class="existing-student-item"
              >
                <div class="existing-student-content">
                  <div class="student-info-row">
                    <span class="student-name">{{ appointment.name }}</span>
                  </div>
                  <div class="existing-student-price-row">
                    <span v-if="appointment.package_type || appointment.learning_item" class="course-type-text">{{ getCourseTypeTextForAppointment(appointment) }}</span>
                    <span v-else class="course-type-text">1v1</span>
                    <span class="remaining-text">剩{{ getRemainingLessons(appointment) }}次</span>
                    <span class="price-info">{{ appointment.price || 0 }}元/节</span>
                  </div>
                </div>
                <div class="cancel-button-container">
                  <button
                    type="button"
                    class="cancel-appointment-btn"
                    @click="cancelAppointment(appointment.id)"
                    :disabled="loading"
                  >
                    取消
                  </button>
                </div>
              </div>
            </div>
            <div v-else class="empty-appointments">
              <div class="empty-text">暂无预约</div>
            </div>
          </div>

          <!-- 新增学生 -->
          <div class="new-section">
            <h3 class="section-title">
              新增预约学员
            </h3>

            <div class="students-list">
              <div
                v-for="student in displayStudents"
                :key="student.id"
                class="student-item"
                :class="{ active: isSelected(student.id) }"
                @click="toggleStudent(student)"
              >
                <div class="student-checkbox">
                  <div class="checkbox" :class="{ checked: isSelected(student.id) }">
                    <span class="checkmark" v-if="isSelected(student.id)">✓</span>
                  </div>
                </div>
                <div class="student-content">
                  <div class="student-row">
                    <div class="student-left">
                      <span class="student-name">{{ student.name }}</span>
                      <div class="student-price-row">
                        <span v-if="student.package_type || student.learning_item" class="course-type-text">{{ getCourseTypeText(student) }}</span>
                        <span class="remaining-text">剩{{ student.remaining_lessons }}次</span>
                        <span class="price-info">{{ student.price || 0 }}元/节</span>
                      </div>
                    </div>
                    <div class="student-right">
                      <span class="student-info">{{ getNonOneOnOneText(student) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 展开/折叠按钮 -->
              <div
                v-if="needsCollapse"
                class="collapse-toggle"
                @click="toggleExpand"
              >
                <span class="toggle-text">
                  {{ isExpanded ? '收起' : `还有${availableStudents.length - 3}个学员，点击展开` }}
                </span>
                <span class="toggle-icon">
                  {{ isExpanded ? '▲' : '▼' }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <div class="form-actions mt-3">
            <BackButton text="取消" to="/calendar" />
            <button
              type="button"
              class="btn-save"
              :disabled="selectedStudents.length === 0 || loading"
              @click="handleSubmit"
            >
              {{ loading ? '预约中...' : `确认预约 (${selectedStudents.length}人)` }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'
import { useAppointmentStore } from '@/stores/appointment'
import { appointmentApi } from '@/api/appointment'
import { toast } from '@/utils/toast'
import BackButton from '@/components/common/BackButton.vue'

const route = useRoute()
const router = useRouter()
const studentStore = useStudentStore()
const appointmentStore = useAppointmentStore()

const loading = ref(false)
const errorMessage = ref('')
const selectedDate = ref('')
const selectedTime = ref('')
const selectedStudents = ref([])
const students = ref([])
const existingAppointments = ref([])
const isExpanded = ref(false)

// 格式化显示日期
const formatDisplayDate = computed(() => {
  if (!selectedDate.value) return ''
  const date = new Date(selectedDate.value)
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${year}年${month}月${day}日`
})

// 格式化星期几
const formatWeekday = computed(() => {
  if (!selectedDate.value) return ''
  const date = new Date(selectedDate.value)
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekdays[date.getDay()]
})

// 显示的学员列表（折叠状态）
const displayStudents = computed(() => {
  if (availableStudents.value.length <= 3) {
    return availableStudents.value
  }
  return isExpanded.value ? availableStudents.value : availableStudents.value.slice(0, 3)
})

// 获取可用学员（未预约的学员）
const availableStudents = computed(() => {
  const existingStudentIds = existingAppointments.value.map(appointment => {
    const student = students.value.find(s => s.name === appointment.name)
    return student ? student.id : null
  }).filter(id => id !== null)

  return students.value.filter(student =>
    !existingStudentIds.includes(student.id)
  )
})

// 是否需要折叠
const needsCollapse = computed(() => {
  return availableStudents.value.length > 3
})

// 从路由参数获取日期和时间
onMounted(() => {
  const { date, time } = route.query

  if (date && time) {
    selectedDate.value = date
    selectedTime.value = time
    fetchStudents()
  } else {
    toast.error('缺少日期或时间参数')
    router.back()
  }
})

const fetchStudents = async () => {
  try {
    await studentStore.fetchStudents()
    students.value = studentStore.students

    // 获取当前时间段已预约的学生
    await fetchExistingAppointments()
  } catch (error) {
    toast.error('获取学员列表失败')
  }
}

const fetchExistingAppointments = async () => {
  try {
    // 直接调用API获取指定日期的预约数据
    const response = await appointmentApi.getDailyAppointments(selectedDate.value)
    const dayData = response.data

    if (dayData && dayData.slots) {
      const timeSlot = dayData.slots.find(slot => slot.time === selectedTime.value)
      if (timeSlot && timeSlot.students) {
        existingAppointments.value = timeSlot.students
      } else {
        // 如果没有找到对应的时间段，清空列表
        existingAppointments.value = []
      }
    } else {
      // 如果没有当天数据，清空列表
      existingAppointments.value = []
    }
  } catch (error) {
    console.error('获取已预约学生失败:', error)
    existingAppointments.value = []
  }
}

const isSelected = (studentId) => {
  return selectedStudents.value.some(student => student.id === studentId)
}

const toggleStudent = (student) => {
  const index = selectedStudents.value.findIndex(s => s.id === student.id)
  if (index > -1) {
    selectedStudents.value.splice(index, 1)
  } else {
    selectedStudents.value.push(student)
  }
  errorMessage.value = ''
}

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

// 获取课程类型标签文本
const getCourseTypeText = (student) => {
  return student.package_type || student.learning_item || ''
}

// 获取已预约学员的课程类型文本
const getCourseTypeTextForAppointment = (appointment) => {
  return appointment.package_type || appointment.learning_item || ''
}

// 获取已预约学员的剩余次数
const getRemainingLessons = (appointment) => {
  return appointment.remaining_lessons || 0
}

// 获取非标签课程类型的描述
const getNonOneOnOneText = (student) => {
  const packageType = student.package_type || student.learning_item || ''
  // 现在所有课程类型都有标签了，所以右侧不显示课程类型
  return ''
}

const cancelAppointment = async (appointmentId) => {
  if (loading.value) return

  try {
    loading.value = true
    await appointmentStore.cancelAppointment(appointmentId)
    toast.success('取消预约成功')

    // 重新获取已预约学生列表
    await fetchExistingAppointments()
  } catch (error) {
    console.error('取消预约失败:', error)
    toast.error(error.message || '取消预约失败')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (selectedStudents.value.length === 0) {
    toast.warning('请选择学员')
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    // 为每个选中的学员创建预约
    const promises = selectedStudents.value.map(student => {
      // 将日期和时间合并为ISO格式的datetime字符串
      const startDateTime = new Date(`${selectedDate.value}T${selectedTime.value}:00`).toISOString()

      const appointmentData = {
        student_id: student.id,
        start_time: startDateTime,
        duration_in_minutes: 60
      }
      return appointmentStore.createAppointment(appointmentData)
    })

    await Promise.all(promises)

    toast.success(`预约成功，共创建${selectedStudents.value.length}个预约`)

    // 清空选中的学生并重新获取已预约学生列表
    selectedStudents.value = []

    // 重新获取学生数据（更新剩余课程次数）
    await studentStore.fetchStudents()
    students.value = studentStore.students

    // 重新获取已预约学生列表
    await fetchExistingAppointments()
  } catch (error) {
    errorMessage.value = error.message || '创建失败'
    toast.error(error.message || '创建失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 覆盖通用内容区域样式 */
.content {
  padding: 0 !important;
  margin: 0 !important;
}

.date-line,
.time-line {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.label-section {
  flex: 0 0 80px;
  text-align: left;
}

.value-section {
  flex: 1;
  text-align: left;
  margin-left: 40px;
}

.label {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.appointment-form {
  gap: 12px;
}

.students-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 覆盖通用表单样式 */
.appointment-form .form-section {
  background: #fff !important;
  border-radius: 0 !important;
  padding: 16px 20px !important;
  border: none !important;
  box-shadow: none !important;
  border-bottom: 1px solid #e9ecef !important;
  margin: 0 0 24px 0 !important;
}

.appointment-form .form-section h3 {
  font-size: 18px !important;
  font-weight: 600 !important;
  margin: 4px 0 16px 0 !important;
  color: #333 !important;
  padding: 0 !important;
  background: none !important;
  border: none !important;
  min-height: auto !important;
}

/* 已预约学生样式 */
.existing-section {
  margin: 0 0 24px 0 !important;
  background: #fff !important;
  border-radius: 0 !important;
  padding: 16px 20px !important;
  border: none !important;
  box-shadow: none !important;
  border-bottom: 1px solid #e9ecef !important;
}

.new-section {
  margin: 0 0 24px 0 !important;
  background: #fff !important;
  border-radius: 0 !important;
  padding: 16px 20px !important;
  border: none !important;
  box-shadow: none !important;
}

.section-title {
  font-size: 18px !important;
  font-weight: 600 !important;
  margin: 4px 0 16px 0 !important;
  color: #333 !important;
  padding: 0 !important;
  background: none !important;
  border: none !important;
  min-height: auto !important;
}

.existing-students {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.existing-student-item {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  display: flex;
  align-items: center;
}

.existing-student-content {
  flex: 1;
  min-width: 0;
  margin-left: 36px; /* 对齐新增预约学员中checkbox + 名字的位置 */
}

.cancel-button-container {
  flex-shrink: 0;
  margin-left: 30px;
}

.cancel-appointment-btn {
  padding: 8px 20px;
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 80px;
}

.cancel-appointment-btn:hover:not(:disabled) {
  background: #ff3838;
}

.cancel-appointment-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.student-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.student-details {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.student-price {
  margin-top: 4px;
}

.student-price-row {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.existing-student-price-row {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.price-info {
  font-size: 13px;
  color: #ff6b35;
  font-weight: 500;
  padding: 0;
  display: inline-block;
  margin-left: 0;
  line-height: 1.2;
  height: 20px;
  display: flex;
  align-items: center;
  white-space: nowrap;
  flex-shrink: 0;
}

.collapse-toggle {
  padding: 12px 16px;
  background: #f8f9fa;
  border: 1px dashed #d0d0d0;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.collapse-toggle:hover {
  background: #e6f7ff;
  border-color: #91d5ff;
}

.toggle-text {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.toggle-icon {
  font-size: 12px;
  color: #999;
  transition: transform 0.3s ease;
}

.student-item {
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-item:hover {
  border-color: #1989fa;
  background: #f0f9ff;
}

.student-item.active {
  border-color: #1989fa;
  background: #f0f9ff;
}

.one-on-one-badge {
  display: inline-block;
  background: #1890ff;
  color: #fff;
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
  line-height: 1.2;
  height: 20px;
  display: flex;
  align-items: center;
}

.course-type-badge {
  display: inline-block;
  background: #722ed1;
  color: #fff;
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
  line-height: 1.2;
  height: 20px;
  display: flex;
  align-items: center;
}

.course-type-text {
  font-size: 13px;
  color: #1a1a1a;
  white-space: nowrap;
  flex-shrink: 0;
  height: 20px;
  display: flex;
  align-items: center;
  line-height: 1.2;
}

.one-v1-badge {
  display: inline-block;
  background: #722ed1;
  color: #fff;
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
  line-height: 1.2;
  height: 20px;
  display: flex;
  align-items: center;
}

.remaining-badge {
  display: inline-block;
  background: #faad14;
  color: #fff;
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
  line-height: 1.2;
  height: 20px;
  display: flex;
  align-items: center;
}

.remaining-text {
  font-size: 13px;
  color: #1a1a1a;
  white-space: nowrap;
  flex-shrink: 0;
  height: 20px;
  display: flex;
  align-items: center;
  line-height: 1.2;
}

.student-checkbox {
  flex-shrink: 0;
}

.checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid #d0d0d0;
  border-radius: 6px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.checkbox.checked {
  background: #1989fa;
  border-color: #1989fa;
}

.checkmark {
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  line-height: 1;
}

.student-content {
  flex: 1;
  min-width: 0;
}

.student-row {
  display: flex;
  align-items: center;
}

.student-left {
  flex: 0 0 80px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  text-align: left;
}

.student-right {
  flex: 1;
  text-align: right;
  margin-left: 40px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.student-name {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.student-info {
  font-size: 16px;
  color: #666;
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

.empty-appointments {
  padding: 24px 16px;
  text-align: center;
  background: #fafafa;
  border-radius: 8px;
  border: 1px dashed #d9d9d9;
}

.empty-text {
  color: #999;
  font-size: 16px;
  font-weight: 500;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin: 15px 20px 20px 20px;
}

.btn-save,
.form-actions :deep(.back-btn) {
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

.btn-save:disabled {
  background: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

.form-actions :deep(.back-btn) {
  background: #fff;
  color: #1989fa;
  border: 2px solid #1989fa;
}

</style>