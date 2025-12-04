<template>
  <div class="student-detail-page">
    <div class="header">
      <button class="back-btn" @click="goBack">
        ← 返回
      </button>
      <h1>学员详情</h1>
    </div>
    
    <div class="content">
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <div v-else-if="student" class="student-info">
        <div class="info-section">
          <h3>基本信息</h3>
          <div class="info-item">
            <label>姓名:</label>
            <span>{{ student.name || '-' }}</span>
          </div>
          <div class="info-item">
            <label>学习项目:</label>
            <span>{{ student.learning_item || '-' }}</span>
          </div>
          <div class="info-item">
            <label>备注:</label>
            <span>{{ student.note || '' }}</span>
          </div>
        </div>
        
        <div class="info-section">
          <h3>套餐信息</h3>
          <div class="info-item">
            <label>套餐类型:</label>
            <span>{{ student.package_type || '-' }}</span>
          </div>
          <div class="info-item">
            <label>剩余:</label>
            <span class="remaining-lessons">{{ student.remaining_lessons || 0 }} 次</span>
          </div>
          <div class="info-item">
            <label>总共:</label>
            <span>{{ student.total_lessons || 0 }} 次</span>
          </div>
          <div class="info-item">
            <label>已上课:</label>
            <span class="completed-lessons">{{ (student.total_lessons || 0) - (student.remaining_lessons || 0) }} 次</span>
          </div>
          <div class="info-item">
            <label>售价:</label>
            <span>{{ student.price || 0 }} 元</span>
          </div>
          <div class="info-item">
            <label>上交俱乐部:</label>
            <span>{{ student.venue_share || 0 }} 元</span>
          </div>
          <div class="info-item">
            <label>利润:</label>
            <span>{{ student.profit || 0 }} 元</span>
          </div>
        </div>
        
        <div class="info-section">
          <h3>上课记录</h3>
          <div v-if="attendances.length === 0" class="no-records">
            暂无上课记录
          </div>
          <div v-else class="attendance-list">
            <div 
              v-for="record in attendances" 
              :key="record.id"
              class="attendance-item"
            >
              <div class="record-info">
                <div class="date-time">
                  {{ record.date }} {{ record.time }}
                </div>
                <div class="status" :class="getStatusClass(record.status)">
                  {{ getStatusText(record.status) }}
                </div>
              </div>
              <div class="lessons-info">
                上课前: {{ record.lessons_before }} 次 → 
                上课后: {{ record.lessons_after }} 次
              </div>
            </div>
          </div>
        </div>

        <div class="info-section">
          <h3>其他信息</h3>
          <div class="info-item">
            <label>创建时间:</label>
            <span>{{ formatDate(student.create_time) }}</span>
          </div>
          <div class="info-item">
            <label>最后更新:</label>
            <span>{{ formatDate(student.update_time) }}</span>
          </div>
        </div>

        <div class="actions">
          <button class="btn-appointment" @click="showAppointmentDialog = true">
            新增预约
          </button>
          <button class="btn-edit" @click="goToEdit">
            编辑信息
          </button>
        </div>
      </div>
    </div>
    
    <!-- 预约弹窗 -->
    <div v-if="showAppointmentDialog" class="appointment-dialog" @click.self="closeAppointmentDialog">
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>新增预约 - {{ student?.name }}</h3>
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
import { useRoute, useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'
import { attendanceApi } from '@/api/attendance'
import { appointmentApi } from '@/api/appointment'
import { getToday, isMonday } from '@/utils/date'
import { toast } from '@/utils/toast'

const route = useRoute()
const router = useRouter()
const studentStore = useStudentStore()

const loading = ref(false)
const attendances = ref([])
const showAppointmentDialog = ref(false)
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

const student = computed(() => studentStore.currentStudent)

onMounted(async () => {
  const studentId = route.params.id
  await fetchStudentData(studentId)
  await fetchAttendanceData(studentId)
})

const fetchStudentData = async (studentId) => {
  loading.value = true
  try {
    await studentStore.fetchStudentById(studentId)
  } catch (error) {
    toast.error('获取学员信息失败')
    router.push('/students')
  } finally {
    loading.value = false
  }
}

const fetchAttendanceData = async (studentId) => {
  try {
    const response = await attendanceApi.getByStudent(studentId)
    attendances.value = response.data || []
  } catch (error) {
    console.error('获取上课记录失败:', error)
  }
}

const goBack = () => {
  router.push('/students')
}

const goToEdit = () => {
  router.push(`/student/${student.value._id}/edit`)
}

const closeAppointmentDialog = () => {
  showAppointmentDialog.value = false
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
      student_id: student.value._id,
      start_time: startDateTime.toISOString(),
      end_time: endDateTime.toISOString()
    })

    toast.success('预约创建成功')
    closeAppointmentDialog()
  } catch (error) {
    toast.error(error.message || '预约失败')
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
  return statusMap[status] || status
}

const formatDate = (dateString) => {
  if (!dateString) return '未知时间'

  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return '时间格式错误'
  }
}
</script>

<style scoped>
.student-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: #1989fa;
  color: #fff;
  padding: 15px;
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
}

.back-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  margin-right: 15px;
}

.header h1 {
  font-size: 22px;
  margin: 0;
}

.content {
  padding: 15px;
}

.loading {
  text-align: center;
  padding: 50px 0;
  color: #666;
}

.info-section {
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.info-section h3 {
  margin: 0 0 15px 0;
  color: #1989fa;
  font-size: 18px;
}

.info-item {
  display: flex;
  margin-bottom: 10px;
  align-items: center;
}

.info-item label {
  min-width: 80px;
  color: #666;
  font-size: 14px;
}

.info-item span {
  color: #333;
  font-size: 14px;
}

.remaining-lessons {
  color: #1989fa;
  font-weight: bold;
}

.completed-lessons {
  color: #52c41a;
  font-weight: bold;
}

.no-records {
  text-align: center;
  color: #999;
  padding: 20px 0;
}

.attendance-list {
  max-height: 300px;
  overflow-y: auto;
}

.attendance-item {
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.attendance-item:last-child {
  border-bottom: none;
}

.record-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.date-time {
  font-size: 14px;
  color: #333;
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
  background: #f5f5f5;
  color: #999;
}

.lessons-info {
  font-size: 12px;
  color: #666;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-appointment,
.btn-edit {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.btn-appointment {
  background: #1989fa;
  color: #fff;
}

.btn-edit {
  background: #52c41a;
  color: #fff;
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