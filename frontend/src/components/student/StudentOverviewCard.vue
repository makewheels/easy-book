<template>
  <div class="overview-card">
    <div class="student-header">
      <div class="student-name">{{ student.name }}</div>
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
    </div>
  </div>
</template>

<script setup>
defineProps({
  student: {
    type: Object,
    required: true
  }
})

const getRemainingClass = (remaining) => {
  if (remaining <= 0) return 'empty'
  if (remaining <= 3) return 'low'
  if (remaining <= 6) return 'medium'
  return 'high'
}

const getProgressPercentage = (remaining, total) => {
  if (!total || total === 0) return 0
  const completed = total - remaining
  return Math.round((completed / total) * 100)
}
</script>

<style scoped>
.overview-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 0;
  border: 1px solid #e0e0e0;
}

.student-header {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 20px;
  padding-left: 20px;
}

.student-name {
  font-size: 28px;
  font-weight: 800;
  color: #1a1a1a;
}


.course-stats {
  display: flex;
  align-items: center;
  justify-content: space-around;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  flex: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-number.high {
  color: #52c41a;
}

.stat-number.medium {
  color: #52c41a;
}

.stat-number.low {
  color: #52c41a;
}

.stat-number.empty {
  color: #52c41a;
}

.stat-number.completed {
  color: #1a1a1a;
}

.stat-number.total {
  color: #1a1a1a;
}

.stat-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.progress-divider {
  width: 1px;
  height: 40px;
  background: #e8e8e8;
}

.progress-section {
  margin-top: 15px;
}

.progress-bar-container {
  width: 90%;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
  margin: 0 auto;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #52c41a 0%, #73d13d 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}
</style>