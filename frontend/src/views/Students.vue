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
          新增学员
        </div>

        <div class="students-grid">
          <StudentOverviewCard
            v-for="student in students"
            :key="student.id"
            :student="student"
            @click="goToDetail(student._id)"
          />
        </div>
      </div>
    </div>

    <BottomNavigation :active-tab="'students'" @navigate="navigateTo" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'
import BottomNavigation from '@/components/BottomNavigation.vue'
import StudentOverviewCard from '@/components/student/StudentOverviewCard.vue'

const router = useRouter()
const studentStore = useStudentStore()

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

</script>

<style scoped>
.students-page {
  max-width: none;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background: #f5f5f5;
  position: relative;
  padding-bottom: 80px;
  width: 100%;
}

/* 头部样式 */
.header {
  background: #fff;
  padding: 20px;
}

.header-content {
  margin: 0 10px;
}

.header h1 {
  font-size: 32px;
  font-weight: 800;
  margin: 0 0 10px 0;
  text-align: center;
  color: #1a1a1a;
  border-radius: 12px;
}

.header .stats {
  text-align: center;
  margin-top: 5px;
  font-size: 16px;
  opacity: 0.9;
  font-weight: 500;
}

/* 内容区域 */
.content {
  margin: 0;
  padding: 20px 0;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #1989fa;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #666;
  font-size: 18px;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-message {
  color: #666;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
}

.add-first-btn {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 16px 32px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

/* 新增学员按钮 */
.add-student-btn {
  background: #fff;
  color: #1989fa;
  border: 1px solid #e0e0e0;
  padding: 18px 10px;
  text-align: center;
  margin: 0 0 10px 0;
  cursor: pointer;
  font-size: 22px;
  font-weight: 700;
  transition: all 0.3s ease;
  width: 100%;
  box-sizing: border-box;
  border-radius: 12px;
}

.add-student-btn:hover {
  background: #f0f9ff;
  border-color: #1989fa;
}



/* 学员网格布局 */
.students-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .header h1 {
    font-size: 28px;
  }

  .student-info .name {
    font-size: 22px;
  }

  .lessons-text {
    font-size: 16px;
  }

  .learning-value {
    font-size: 15px;
  }
}
</style>