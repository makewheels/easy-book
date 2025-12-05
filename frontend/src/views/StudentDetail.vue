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
        <!-- 学员概览卡片组件 -->
        <StudentOverviewCard :student="student" />

        <!-- 快捷操作按钮组件 -->
        <QuickActions
          @show-appointment="showAppointmentDialog = true"
          @edit-student="goToEdit"
        />

        <!-- 详细信息卡片组件 -->
        <StudentDetailCards :student="student" :attendances="attendances" />
      </div>
    </div>

    <!-- 预约弹窗组件 -->
    <AppointmentDialog
      :show="showAppointmentDialog"
      :student-name="student?.name"
      @close="closeAppointmentDialog"
      @submit="handleAppointmentSubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'
import { attendanceApi } from '@/api/attendance'
import { appointmentApi } from '@/api/appointment'
import { isMonday } from '@/utils/date'
import { toast } from '@/utils/toast'

// 导入组件
import StudentOverviewCard from '@/components/student/StudentOverviewCard.vue'
import QuickActions from '@/components/student/QuickActions.vue'
import StudentDetailCards from '@/components/student/StudentDetailCards.vue'
import AppointmentDialog from '@/components/student/AppointmentDialog.vue'

const route = useRoute()
const router = useRouter()
const studentStore = useStudentStore()

// 存储来源页面，用于智能返回导航
const referrerUrl = ref('')

const loading = ref(false)
const attendances = ref([])
const showAppointmentDialog = ref(false)

const student = computed(() => studentStore.currentStudent)

onMounted(async () => {
  const studentId = route.params.id

  // 捕获来源页面信息
  if (document.referrer) {
    try {
      const referrer = new URL(document.referrer)
      const currentOrigin = window.location.origin

      // 只记录同源的引用页面
      if (referrer.origin === currentOrigin) {
        referrerUrl.value = referrer.pathname
      }
    } catch (error) {
      console.log('无法解析referrer:', document.referrer)
    }
  }

  console.log('Mounted - referrer:', referrerUrl.value)

  await fetchStudentData(studentId)
  await fetchAttendanceData(studentId)
})

const fetchStudentData = async (studentId) => {
  loading.value = true
  try {
    await studentStore.fetchStudentById(studentId)
  } catch (error) {
    toast.error('获取学员信息失败')
    // 智能返回导航：优先使用记录的referrer，其次使用router.back()
    if (referrerUrl.value) {
      router.push(referrerUrl.value)
    } else {
      router.back()
    }
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
  console.log('goBack called, referrer:', referrerUrl.value)
  console.log('current route:', router.currentRoute.value.path)
  console.log('router history length:', window.history.length)

  // 智能返回导航：优先使用记录的referrer，其次使用router.back()
  if (referrerUrl.value) {
    console.log('Navigating to referrer:', referrerUrl.value)
    router.push(referrerUrl.value)
  } else {
    console.log('Using router.back()')
    router.back()
  }
}

const goToEdit = () => {
  router.push(`/student/${student.value._id}/edit`)
}

const closeAppointmentDialog = () => {
  showAppointmentDialog.value = false
}

const handleAppointmentSubmit = async (formData) => {
  if (!formData.start_time || !formData.duration) {
    toast.warning('请选择开始时间和课程时长')
    return
  }

  // 检查是否为周一（游泳馆闭馆）
  const startDate = new Date(formData.start_time)
  if (isMonday(startDate.toISOString().split('T')[0])) {
    toast.warning('游泳馆周一闭馆，不能预约')
    return
  }

  try {
    await appointmentApi.create({
      student_id: student.value._id,
      start_time: formData.start_time,
      duration: formData.duration
    })

    toast.success('预约创建成功')
    closeAppointmentDialog()
  } catch (error) {
    toast.error(error.message || '预约失败')
  }
}
</script>

<style scoped>
.student-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
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
</style>
