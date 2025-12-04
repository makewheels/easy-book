<template>
  <div class="students-page">
    <div class="header">
      <h1>学员管理</h1>
      <div class="stats">共 {{ totalStudents }} 人，活跃 {{ activeStudents }} 人</div>
    </div>
    
    <div class="content">
      <div v-if="loading" class="loading">
        加载中...
      </div>

      <div v-else-if="students.length === 0" class="empty-state">
        <div class="empty-message">暂无学员</div>
        <button class="add-first-btn" @click="goToAddStudent">
          添加学员
        </button>
      </div>

      <div v-else>
        <!-- 新增学生按钮 - 移到顶部 -->
        <div class="add-student-btn" @click="goToAddStudent">
          + 新增学员
        </div>

        <div
          v-for="student in students"
          :key="student.id"
          class="student-card"
          @click="goToDetail(student._id)"
        >
          <div class="card-header">
            <div class="student-info">
              <div class="name">{{ student.name }}</div>
            </div>
            <button class="btn-appointment" @click.stop="quickAppointment(student)">
              预约
            </button>
          </div>

          <div class="card-body">
            <div class="info-row">
              <span class="label">次数:</span>
              <span class="value">[{{ student.total_lessons - student.remaining_lessons }}/{{ student.total_lessons }}]</span>
              <span class="type">{{ student.package_type }}</span>
            </div>
            <div class="info-row">
              <span class="label">项目:</span>
              <span class="value">{{ student.learning_item }}</span>
            </div>
            <div class="info-row">
              <span class="label">剩余:</span>
              <span class="value">{{ student.remaining_lessons }} 次</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="bottom-nav">
      <div class="nav-item" @click="navigateTo('home')">
        <div class="nav-icon">🏠</div>
        <span>预约管理</span>
      </div>
      <div class="nav-item" @click="navigateTo('calendar')">
        <div class="nav-icon">📅</div>
        <span>课程日历</span>
      </div>
      <div class="nav-item active" @click="navigateTo('students')">
        <div class="nav-icon">👥</div>
        <span>学员管理</span>
      </div>
    </div>
    
    <!-- 快速预约弹窗 -->
    <div v-if="showAppointmentDialog" class="appointment-dialog" @click.self="closeAppointmentDialog">
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>预约课程 - {{ selectedStudent?.name }}</h3>
          <button class="close-btn" @click="closeAppointmentDialog">×</button>
        </div>
        
        <div class="dialog-body">
          <div class="form-group">
            <label>选择日期</label>
            <input
              type="date"
              v-model="appointmentForm.date"
            />
          </div>
          
          <div class="form-group">
            <label>选择时间</label>
            <select v-model="appointmentForm.time">
              <option value="">请选择时间</option>
              <option v-for="time in timeSlots" :key="time" :value="time">
                {{ time }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>课程时长</label>
            <select v-model="appointmentForm.duration">
              <option v-for="option in durationOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          
          <div class="dialog-actions">
            <button class="btn-cancel" @click="closeAppointmentDialog">
              取消
            </button>
            <button class="btn-confirm" @click="handleAppointmentSubmit">
              确认预约
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'
import { useAppointmentStore } from '@/stores/appointment'
import { appointmentApi } from '@/api/appointment'
import { getToday, isMonday } from '@/utils/date'
import { toast } from '@/utils/toast'

const router = useRouter()
const studentStore = useStudentStore()
const appointmentStore = useAppointmentStore()

const showAppointmentDialog = ref(false)
const selectedStudent = ref(null)
const appointmentForm = ref({
  date: '',
  time: '',
  duration: 60  // 默认1小时，单位分钟
})

const timeSlots = [
  '07:00', '08:00', '09:00', '10:00', '11:00',
  '12:00', '14:00', '15:00', '16:00', '17:00',
  '18:00', '19:00'
]

const durationOptions = [
  { value: 60, label: '1小时' },
  { value: 90, label: '1.5小时' },
  { value: 120, label: '2小时' }
]

const loading = computed(() => studentStore.loading)
const students = computed(() => studentStore.students)
const totalStudents = computed(() => studentStore.totalStudents)
const activeStudents = computed(() => studentStore.activeStudents.length)

onMounted(() => {
  studentStore.fetchStudents()
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

const goToDetail = (studentId) => {
  router.push(`/student/${studentId}`)
}

const goToAddStudent = () => {
  router.push('/add-student')
}

const quickAppointment = (student) => {
  selectedStudent.value = student
  appointmentForm.value = {
    date: '',
    time: ''
  }
  showAppointmentDialog.value = true
}

const closeAppointmentDialog = () => {
  showAppointmentDialog.value = false
  selectedStudent.value = null
  appointmentForm.value = { date: '', time: '', duration: 60 }
}

const handleAppointmentSubmit = async () => {
  if (!appointmentForm.value.date || !appointmentForm.value.time) {
    toast.warning('请选择日期和时间')
    return
  }

  // 检查是否为周一（游泳馆闭馆）
  if (isMonday(appointmentForm.value.date)) {
    toast.warning('游泳馆周一闭馆，不能预约')
    return
  }

  try {
    // 构建新的时间格式数据
    const startDateTime = new Date(`${appointmentForm.value.date}T${appointmentForm.value.time}:00`)
    const endDateTime = new Date(startDateTime.getTime() + appointmentForm.value.duration * 60 * 1000) // 使用选择的时长

    await appointmentApi.create({
      student_id: selectedStudent.value._id,
      start_time: startDateTime.toISOString(),
      end_time: endDateTime.toISOString()
    })

    toast.success('预约创建成功')
    closeAppointmentDialog()
  } catch (error) {
    toast.error(error.message || '预约失败')
  }
}
</script>

<style scoped>
.students-page {
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
  margin: 0 0 10px 0;
  text-align: center;
}

.stats {
  font-size: 14px;
  opacity: 0.8;
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
  margin-bottom: 20px;
}

.add-first-btn {
  background: #1989fa;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
}

.student-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 10px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s;
}

.student-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.student-info .name {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.btn-appointment {
  background: #1989fa;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 14px;
  cursor: pointer;
}

.card-body {
  margin-top: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  font-size: 14px;
}

.info-row .label {
  color: #666;
  margin-right: 5px;
  min-width: 40px;
}

.info-row .value {
  color: #333;
  flex: 1;
}

.info-row .type {
  background: #f0f9ff;
  color: #1989fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 5px;
}

.add-student-btn {
  background: #1989fa;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  margin: 10px 0 20px 0;  /* 顶部按钮：上边距10px，下边距20px */
  cursor: pointer;
  font-size: 16px;
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
}

.dialog-content {
  background: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  overflow: hidden;
}

.dialog-header {
  padding: 15px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.dialog-body {
  padding: 15px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.dialog-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-confirm {
  background: #1989fa;
  color: #fff;
}
</style>