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
        <!-- 学员概览卡片 -->
        <div class="overview-card">
          <div class="student-header">
            <div class="student-name">{{ student.name }}</div>
            <div class="package-badge">{{ student.package_type }}</div>
          </div>

          <div class="course-stats">
            <div class="stat-item">
              <div class="stat-number" :class="getRemainingClass(student.remaining_lessons)">
                {{ student.remaining_lessons || 0 }}
              </div>
              <div class="stat-label">剩余</div>
            </div>
            <div class="progress-divider"></div>
            <div class="stat-item">
              <div class="stat-number completed">{{ (student.total_lessons || 0) - (student.remaining_lessons || 0) }}</div>
              <div class="stat-label">已上课</div>
            </div>
            <div class="progress-divider"></div>
            <div class="stat-item">
              <div class="stat-number total">{{ student.total_lessons || 0 }}</div>
              <div class="stat-label">总共</div>
            </div>
          </div>
          <!-- 进度条 -->
          <div class="progress-section">
            <div class="progress-bar-container">
              <div class="progress-fill" :style="{ width: getProgressPercentage(student.remaining_lessons, student.total_lessons) + '%' }"></div>
            </div>
            <div class="progress-text">课程进度: {{ Math.round(getProgressPercentage(student.remaining_lessons, student.total_lessons)) }}%</div>
          </div>
        </div>

        <!-- 快捷操作按钮 -->
        <div class="quick-actions">
          <button class="action-btn primary" @click="showAppointmentDialog = true">
            <span class="btn-icon">📅</span>
            新增预约
          </button>
          <button class="action-btn secondary" @click="goToEdit">
            <span class="btn-icon">✏️</span>
            编辑信息
          </button>
        </div>

        <!-- 详细信息卡片 -->
        <div class="detail-cards">
          <!-- 基本信息 -->
          <div class="detail-card">
            <div class="card-title">
              <span class="title-icon">👤</span>
              基本信息
            </div>
            <div class="card-content">
              <div class="detail-row">
                <span class="detail-label">学习项目</span>
                <span class="detail-value">{{ student.learning_item || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">备注</span>
                <span class="detail-value">{{ student.note || '暂无备注' }}</span>
              </div>
            </div>
          </div>

          <!-- 财务信息 -->
          <div class="detail-card">
            <div class="card-title">
              <span class="title-icon">💰</span>
              财务信息
            </div>
            <div class="card-content">
              <div class="detail-row">
                <span class="detail-label">课程售价</span>
                <span class="detail-value price">¥{{ student.price || 0 }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">俱乐部分成</span>
                <span class="detail-value">¥{{ student.venue_share || 0 }}</span>
              </div>
              <div class="detail-row highlight">
                <span class="detail-label">净利润</span>
                <span class="detail-value profit">¥{{ student.profit || 0 }}</span>
              </div>
            </div>
          </div>

          <!-- 上课记录 -->
          <div class="detail-card">
            <div class="card-title">
              <span class="title-icon">📚</span>
              上课记录
            </div>
            <div class="card-content">
              <div v-if="attendances.length === 0" class="empty-records">
                <div class="empty-icon">📝</div>
                <div class="empty-text">暂无上课记录</div>
              </div>
              <div v-else class="attendance-timeline">
                <div
                  v-for="record in attendances.slice().reverse()"
                  :key="record.id"
                  class="timeline-item"
                >
                  <div class="timeline-dot" :class="getStatusClass(record.status)"></div>
                  <div class="timeline-content">
                    <div class="timeline-header">
                      <span class="timeline-date">{{ formatDateShort(record.date) }}</span>
                      <span class="timeline-time">{{ record.time }}</span>
                      <span class="timeline-status" :class="getStatusClass(record.status)">
                        {{ getStatusText(record.status) }}
                      </span>
                    </div>
                    <div class="timeline-detail">
                      课程消耗: {{ record.lessons_before }} → {{ record.lessons_after }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 系统信息 -->
          <div class="detail-card">
            <div class="card-title">
              <span class="title-icon">⚙️</span>
              系统信息
            </div>
            <div class="card-content">
              <div class="detail-row">
                <span class="detail-label">创建时间</span>
                <span class="detail-value">{{ formatDate(student.create_time) }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">最后更新</span>
                <span class="detail-value">{{ formatDate(student.update_time) }}</span>
              </div>
            </div>
          </div>
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

// 格式化短日期
const formatDateShort = (dateString) => {
  if (!dateString) return '未知时间'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit'
    })
  } catch (error) {
    return '时间格式错误'
  }
}

// 计算课程进度百分比
const getProgressPercentage = (remaining, total) => {
  if (!total || total === 0) return 0
  const completed = total - remaining
  return (completed / total) * 100
}

// 根据剩余课程数量获取状态样式
const getRemainingClass = (remaining) => {
  if (remaining === 0) return 'remaining-empty'
  if (remaining <= 2) return 'remaining-low'
  if (remaining <= 5) return 'remaining-medium'
  return 'remaining-good'
}
</script>

<style scoped>
.student-detail-page {
  min-height: 100vh;
  background: #f8f9fa;
  position: relative;
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.back-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  margin-right: 15px;
  padding: 8px 16px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.back-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.header h1 {
  font-size: 20px;
  margin: 0;
  font-weight: 600;
}

.content {
  padding: 20px;
  max-width: 500px;
  margin: 0 auto;
}

.loading {
  text-align: center;
  padding: 50px 0;
  color: #666;
}

/* 概览卡片 */
.overview-card {
  background: #fff;
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.overview-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.student-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.student-name {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
}

.package-badge {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  flex-shrink: 0;
}

.course-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
  flex: 1;
  min-width: 60px;
  white-space: nowrap;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  line-height: 1.2;
  margin-bottom: 2px;
}

.stat-number.remaining-good {
  color: #52c41a;
}

.stat-number.remaining-medium {
  color: #faad14;
}

.stat-number.remaining-low {
  color: #ff7a45;
}

.stat-number.remaining-empty {
  color: #ff4d4f;
}

.stat-number.completed {
  color: #1890ff;
}

.stat-number.total {
  color: #722ed1;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.progress-divider {
  width: 1px;
  height: 40px;
  background: #e8e8e8;
  margin: 0 4px;
  flex-shrink: 0;
}

.progress-section {
  margin-top: 16px;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #666;
  text-align: center;
}

/* 快捷操作 */
.quick-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.action-btn {
  flex: 1;
  padding: 16px;
  border: none;
  border-radius: 16px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.action-btn.primary {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: #fff;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}

.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(24, 144, 255, 0.4);
}

.action-btn.secondary {
  background: #fff;
  color: #1890ff;
  border: 2px solid #1890ff;
}

.action-btn.secondary:hover {
  background: #f0f9ff;
  transform: translateY(-2px);
}

.btn-icon {
  font-size: 18px;
}

/* 详细信息卡片 */
.detail-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.detail-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.title-icon {
  font-size: 20px;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.detail-row.highlight {
  background: #f6ffed;
  margin: 0 -8px;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid #52c41a;
}

.detail-label {
  font-size: 14px;
  color: #666;
  min-width: 80px;
}

.detail-value {
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 500;
  text-align: right;
  flex: 1;
}

.detail-value.price {
  color: #fa8c16;
  font-weight: 600;
}

.detail-value.profit {
  color: #52c41a;
  font-weight: 700;
}

/* 上课记录时间线 */
.empty-records {
  text-align: center;
  padding: 30px 0;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
}

.attendance-timeline {
  position: relative;
  padding-left: 20px;
}

.attendance-timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e8e8e8;
}

.timeline-item {
  position: relative;
  margin-bottom: 16px;
  padding-bottom: 8px;
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -16px;
  top: 6px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.timeline-dot.status-checked {
  background: #52c41a;
}

.timeline-dot.status-cancel {
  background: #ff4d4f;
}

.timeline-content {
  background: #fafafa;
  border-radius: 8px;
  padding: 12px;
  margin-left: 4px;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.timeline-date {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

.timeline-time {
  font-size: 12px;
  color: #666;
}

.timeline-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
}

.timeline-status.status-checked {
  background: #e6f7e6;
  color: #52c41a;
}

.timeline-status.status-cancel {
  background: #fff2f0;
  color: #ff4d4f;
}

.timeline-detail {
  font-size: 12px;
  color: #666;
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