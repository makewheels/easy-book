<template>
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
</template>

<script setup>
defineProps({
  student: {
    type: Object,
    required: true
  },
  attendances: {
    type: Array,
    default: () => []
  }
})

const getStatusClass = (status) => {
  return {
    'status-attended': status === 'attended',
    'status-absent': status === 'absent',
    'status-cancel': status === 'cancel'
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'attended': '已上课',
    'absent': '缺席',
    'cancel': '已取消'
  }
  return statusMap[status] || status
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDateShort = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<style scoped>
.detail-cards {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e8e8e8;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.title-icon {
  font-size: 18px;
}

.card-content {
  padding: 20px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row.highlight {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  margin: 0 -20px;
  padding: 12px 20px;
  border-radius: 8px;
  border: 1px solid #e3f2fd;
}

.detail-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.detail-value {
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 600;
}

.detail-value.price {
  color: #52c41a;
}

.detail-value.profit {
  color: #1989fa;
  font-weight: 700;
}

/* 上课记录样式 */
.empty-records {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.6;
}

.empty-text {
  font-size: 16px;
  color: #666;
  font-weight: 500;
}

.attendance-timeline {
  position: relative;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.timeline-item:last-child {
  border-bottom: none;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
}

.timeline-dot.status-attended {
  background: #52c41a;
}

.timeline-dot.status-absent {
  background: #fa541c;
}

.timeline-dot.status-cancel {
  background: #999;
}

.timeline-content {
  flex: 1;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.timeline-date {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}

.timeline-time {
  font-size: 13px;
  color: #666;
}

.timeline-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.timeline-status.status-attended {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #d9f7be;
}

.timeline-status.status-absent {
  background: #fff2e8;
  color: #fa541c;
  border: 1px solid #ffd591;
}

.timeline-status.status-cancel {
  background: #f5f5f5;
  color: #999;
  border: 1px solid #d9d9d9;
}

.timeline-detail {
  font-size: 13px;
  color: #666;
}
</style>