<template>
  <div class="student-detail-page">
    <div class="header">
      <BackButton :to="backDestination" />
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
          @showAppointment="goToAddAppointment"
          @editStudent="goToEdit"
        />

        <!-- 详细信息卡片组件 -->
        <StudentDetailCards :student="student" :attendances="attendances" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'
import { appointmentApi } from '@/api/appointment'
import { isMonday } from '@/utils/date'
import { toast } from '@/utils/toast'

// 导入组件
import BackButton from '@/components/common/BackButton.vue'
import StudentOverviewCard from '@/components/student/StudentOverviewCard.vue'
import QuickActions from '@/components/student/QuickActions.vue'
import StudentDetailCards from '@/components/student/StudentDetailCards.vue'

const route = useRoute()
const router = useRouter()
const studentStore = useStudentStore()

// 存储来源页面，用于智能返回导航
const referrerUrl = ref('')

const loading = ref(false)
const attendances = ref([])

const student = computed(() => studentStore.currentStudent)

// 智能返回导航：如果记录了有效的referrer，则使用它；否则默认到学员列表页
const backDestination = computed(() => {
  if (referrerUrl.value) {
    return referrerUrl.value
  }
  // 默认返回到学员列表页
  return '/students'
})

onMounted(async () => {
  const studentId = route.params.id

  // 捕获来源页面信息
  if (document.referrer) {
    try {
      const referrer = new URL(document.referrer)
      const currentOrigin = window.location.origin

      // 只记录同源的引用页面，且排除编辑页面
      if (referrer.origin === currentOrigin && !referrer.pathname.includes('/edit')) {
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
    const response = await appointmentApi.getStudentAppointments(studentId)
    const appointments = response.data || []

    // 转换预约数据为考勤记录格式，使用课程的实际上课时间而不是预约创建时间
    attendances.value = await Promise.all(appointments.map(async (appointment) => {
      // 获取课程信息以获取实际的上课时间
      let courseDate = appointment.create_time.split('T')[0] // 默认使用创建时间日期
      let courseTime = '00:00' // 默认时间

      try {
        // 尝试获取课程详情以获取准确的上课时间
        const courseResponse = await fetch(`/api/courses/${appointment.course_id}`)
        if (courseResponse.ok) {
          const courseData = await courseResponse.json()
          if (courseData.data && courseData.data.start_time) {
            const courseStartTime = new Date(courseData.data.start_time)
            courseDate = courseStartTime.toISOString().split('T')[0]
            courseTime = courseStartTime.toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit'
            })
          }
        }
      } catch (courseError) {
        console.warn('获取课程信息失败:', courseError)
        // 如果获取课程信息失败，继续使用默认的预约时间
      }

      return {
        id: appointment.id,
        date: courseDate,
        time: courseTime,
        status: appointment.lesson_consumed ? 'completed' : appointment.status,
        statusText: appointment.lesson_consumed ? '已完成' :
                   appointment.status === 'scheduled' ? '已预约' : appointment.status,
        lessons_before: appointment.lesson_consumed ? '上课前' : '-',
        lessons_after: appointment.lesson_consumed ? '已消耗' : '-',
        courseTitle: `(课程)` // 可以后续添加课程标题
      }
    }))
  } catch (error) {
    console.error('获取预约记录失败:', error)
    attendances.value = []
  }
}


const goToEdit = () => {
  router.push(`/student/${student.value.id}/edit`)
}

const goToAddAppointment = () => {
  router.push(`/student/${student.value.id}/add-appointment`)
}
</script>

<style scoped>
.student-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
  position: relative;
  font-size: 20px; /* 整体页面字体放大 */
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

.back-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  margin-right: 15px;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.back-btn:hover {
  background: #f0f0f0;
  color: #1a1a1a;
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

.loading {
  text-align: center;
  padding: 50px 0;
  color: #666;
}
</style>
