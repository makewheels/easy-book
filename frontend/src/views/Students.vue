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
              <div class="package-type">{{ student.package_type }}</div>
            </div>
          </div>

          <div class="card-body">
            <!-- 简化的课程信息 -->
            <div class="lessons-info">
              <span class="lessons-text">{{ student.remaining_lessons }}/{{ student.total_lessons }} 节课</span>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: getProgressPercentage(student.remaining_lessons, student.total_lessons) + '%' }"
                ></div>
              </div>
            </div>

            <!-- 简化的学习项目 -->
            <div class="learning-item">
              <span class="learning-label">学习项目：</span>
              <span class="learning-value">{{ student.learning_item }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-nav">
      <div class="nav-item" @click="navigateTo('calendar')">
        <div class="nav-icon">📅</div>
        <span>课程日历</span>
      </div>
      <div class="nav-item active" @click="navigateTo('students')">
        <div class="nav-icon">👥</div>
        <span>学员管理</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'

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
  const completed = total - remaining
  return (completed / total) * 100
}
</script>

<style scoped>
.students-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 80px;
}

/* 头部样式 */
.header {
  background: #fff;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 430px;
  margin: 0 auto;
}

.header h1 {
  font-size: 32px;
  font-weight: 800;
  margin: 0 0 20px 0;
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
  max-width: 430px;
  margin: 0 auto;
  padding: 20px 15px;
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
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #fff;
  font-size: 18px;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-message {
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  opacity: 0.9;
}

.add-first-btn {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 16px 32px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

/* 新增学员按钮 */
.add-student-btn {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  color: #1989fa;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 18px;
  text-align: center;
  margin: 0 0 25px 0;
  cursor: pointer;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

/* 学员卡片 */
.student-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  margin-bottom: 20px;
  padding: 25px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.2);
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

.student-info .package-type {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 6px 16px;
  border-radius: 16px;
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

/* 课程信息 */
.lessons-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lessons-text {
  font-size: 18px;
  color: #1989fa;
  font-weight: 700;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(25, 137, 250, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1989fa 0%, #096dd9 100%);
  border-radius: 4px;
}

/* 学习项目 */
.learning-item {
  padding: 16px 20px;
  background: rgba(240, 249, 255, 0.8);
  border-radius: 12px;
  border-left: 4px solid #1989fa;
}

.learning-label {
  font-size: 14px;
  color: #666;
  margin-right: 8px;
  font-weight: 500;
}

.learning-value {
  font-size: 16px;
  color: #1a1a1a;
  font-weight: 600;
}

/* 底部导航 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 430px;
  height: 70px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.3s;
  padding: 5px;
}

.nav-item.active {
  color: #1989fa;
}

.nav-icon {
  font-size: 24px;
  margin-bottom: 4px;
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