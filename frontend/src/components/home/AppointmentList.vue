<template>
  <div class="appointments">
    <div v-for="dayData in dailyData" :key="dayData.date" class="day-section">
      <!-- 日期标题 -->
      <div class="date-header">
        {{ dayData.date }} {{ dayData.weekday }}
      </div>

      <div v-if="dayData.slots.length === 0" class="no-appointments-card">
        <div class="no-appointments-icon">📅</div>
        <div class="no-appointments-text">当天无预约</div>
      </div>

      <div v-else class="slots-container">
        <div
          v-for="slot in dayData.slots"
          :key="`${dayData.date}-${slot.time}`"
          class="time-slot-card"
        >
          <!-- 时间段头部 -->
          <div class="slot-header">
            <div class="time-text">{{ slot.time }}</div>
          </div>

          <!-- 学员列表 -->
          <div class="students-list">
            <div
              v-for="student in slot.students"
              :key="student.id"
              class="student-card"
              @click="goToStudent(student.student_id)"
            >
              <div class="student-main-info">
                <div class="name-section">
                  <div class="student-name">{{ student.name }}</div>
                  <div class="package-badge">{{ student.package_type }}</div>
                </div>
              </div>

              <div class="student-details">
                <div class="detail-item learning-info">
                  <span class="detail-text">{{ student.learning_item }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps({
  dailyData: {
    type: Array,
    default: () => []
  }
})

const goToStudent = (studentId) => {
  router.push({
    name: 'StudentDetail',
    params: { id: studentId }
  })
}
</script>

<style scoped>
/* 预约列表容器 */
.appointments {
  max-width: 430px;
  margin: 0 auto;
}

.day-section {
  margin-bottom: 25px;
}

/* 日期标题 */
.date-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 15px 20px;
  margin-bottom: 15px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  text-align: center;
}

/* 无预约状态 */
.no-appointments-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 40px 20px;
  margin-bottom: 20px;
  text-align: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.no-appointments-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.6;
}

.no-appointments-text {
  font-size: 16px;
  color: #666;
  font-weight: 500;
}

/* 时间段容器 */
.slots-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 时间段卡片 */
.time-slot-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.time-slot-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* 时间段头部 */
.slot-header {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  padding: 12px 20px;
  border-bottom: 2px solid #e3f2fd;
}

.time-text {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

/* 学员列表 */
.students-list {
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 学员卡片 */
.student-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.student-card:hover {
  border-color: #1989fa;
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.15);
}

.student-main-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.name-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.student-name {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a1a;
}

.package-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.student-details {
  flex-shrink: 0;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-text {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}
</style>