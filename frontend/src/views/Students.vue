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
          </div>

          <div class="card-body">
            <!-- 学习项目和类型在左下角 -->
            <div class="bottom-row">
              <div class="left-info">
                <span class="learning-value">{{ student.learning_item }}</span>
                <span class="package-type">{{ student.package_type }}</span>
              </div>
              <div class="right-info">
                <span class="lessons-text">{{ student.remaining_lessons }} / {{ student.total_lessons }} 节课</span>
              </div>
            </div>

            <!-- 进度条 -->
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: getProgressPercentage(student.remaining_lessons, student.total_lessons) + '%' }"
              ></div>
            </div>
          </div>
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

// 计算课程进度百分比
const getProgressPercentage = (remaining, total) => {
  if (!total || total === 0) return 0
  // 假设remaining实际上是已完成课数
  return (remaining / total) * 100
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
  border-radius: 4px;
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
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 18px 10px;
  text-align: center;
  margin: 0 0 10px 0;
  cursor: pointer;
  font-size: 22px;
  font-weight: 700;
  transition: all 0.3s ease;
  width: 100%;
  box-sizing: border-box;
}

/* 学员卡片 */
.student-card {
  background: #fff;
  border-radius: 4px;
  margin: 0 0 10px 0;
  padding: 20px 30px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.student-info .name {
  font-size: 24px;
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 8px;
  line-height: 1.2;
}

.package-type {
  background: #f5f5f5;
  color: #666;
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  display: inline-block;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.lessons-text {
  font-size: 24px;
  color: #0066cc;
  font-weight: 700;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #1989fa;
  border-radius: 4px;
}

/* 底部信息行 */
.bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.left-info {
  display: flex;
  gap: 20px;
  align-items: center;
}

.right-info {
  display: flex;
  gap: 20px;
  align-items: center;
}

/* 学习项目 */
.learning-item {
  display: block;
}

.learning-label {
  font-size: 16px;
  color: #666;
  margin-right: 8px;
  font-weight: 500;
}

.learning-value {
  font-size: 16px;
  color: #1a1a1a;
  font-weight: 400;
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