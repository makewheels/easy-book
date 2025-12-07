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
        <div class="detail-row">
          <span class="detail-label">录入时间</span>
          <span class="detail-value">{{ formatDate(student.create_time) }}</span>
        </div>
      </div>
    </div>

    <!-- 套餐信息 -->
    <div class="detail-card">
      <div class="card-title">
        <span class="title-icon">📦</span>
        套餐信息
      </div>
      <div class="card-content">
        <!-- 套餐列表第一行：新增按钮 -->
        <div class="package-list-header">
          <button class="btn-add-package" @click="goToAddPackage">
            <span class="add-icon">+</span>
            新增套餐
          </button>
        </div>

        <div v-if="packagesLoading" class="empty-packages">
          <div class="empty-text">加载套餐信息中...</div>
        </div>
        <div v-else-if="studentPackages.length === 0" class="empty-packages">
          <div class="empty-icon">📦</div>
          <div class="empty-text">该学员暂无套餐</div>
          <div class="empty-desc">点击上方按钮为学员购买套餐</div>
        </div>
        <div v-else class="package-list">
          <div
            v-for="pkg in studentPackages"
            :key="pkg.id"
            class="package-item"
            @click="goToEditPackage(pkg.id)"
          >
            <div class="package-header">
              <div class="package-name">{{ pkg.name }}</div>
              <div class="package-status" :class="getPackageStatusClass(pkg)">
                {{ getPackageStatusText(pkg) }}
              </div>
            </div>
            <div class="package-info">
              <div class="info-row">
                <span class="info-label">套餐类型:</span>
                <span class="info-value">{{ getPackageTypeText(pkg) }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">计费方式:</span>
                <span class="info-value">{{ pkg.package_category === 'count_based' ? '记次套餐' : '时长套餐' }}</span>
              </div>
              <div v-if="pkg.package_category === 'count_based'" class="info-row">
                <span class="info-label">课程余量:</span>
                <span class="info-value">{{ pkg.remaining_lessons || 0 }}/{{ pkg.total_lessons || 0 }}节</span>
              </div>
              <div v-else class="info-row">
                <span class="info-label">有效期至:</span>
                <span class="info-value">{{ getPackageExpiryText(pkg) }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">套餐价格:</span>
                <span class="info-value price">¥{{ pkg.price }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上课记录 -->
    <div class="detail-card">
      <div class="card-title">
        <span class="title-icon">📚</span>
        上课记录
        <span class="title-count">(共{{ attendances.length }}次)</span>
      </div>
      <div class="card-content">
        <div v-if="attendances.length === 0" class="empty-records">
          <div class="empty-text">暂无上课记录</div>
        </div>
        <div v-else>
          <div class="attendance-timeline">
            <div
              v-for="record in displayedAttendances"
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

          <!-- 展开/折叠按钮 -->
          <div v-if="props.attendances.length > 3" class="attendance-toggle">
            <button class="btn-toggle" @click="toggleAttendances">
              {{ showAllAttendances ? '收起' : '查看更多' }}
              <span class="toggle-icon">{{ showAllAttendances ? '▲' : '▼' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, toRefs, watch } from 'vue'
import { useRouter } from 'vue-router'
import { packageApi } from '@/api/package'

const router = useRouter()
const emit = defineEmits(['add-package', 'edit-package'])

const props = defineProps({
  student: {
    type: Object,
    required: true
  },
  attendances: {
    type: Array,
    default: () => []
  }
})

// Real package data from API
const studentPackages = ref([])
const packagesLoading = ref(false)

// 上课记录展开/折叠状态
const showAllAttendances = ref(false)

// 加载学生套餐数据
const loadStudentPackages = async () => {
  if (!props.student?.id) return

  try {
    packagesLoading.value = true
    const packages = await packageApi.getStudentPackages(props.student.id)
    studentPackages.value = packages
  } catch (error) {
    console.error('加载学生套餐失败:', error)
    studentPackages.value = []
  } finally {
    packagesLoading.value = false
  }
}

// 组件挂载时加载套餐数据
onMounted(() => {
  loadStudentPackages()
})

// 监听学生ID变化，重新加载套餐数据
const { student } = toRefs(props)
watch(student, () => {
  loadStudentPackages()
}, { deep: true })

// 计算显示的上课记录
const displayedAttendances = computed(() => {
  if (showAllAttendances.value) {
    return props.attendances
  }
  return props.attendances.slice(0, 3)
})

const toggleAttendances = () => {
  showAllAttendances.value = !showAllAttendances.value
}

const goToAddPackage = () => {
  router.push(`/student/${props.student.id}/add-package`)
}

const goToEditPackage = (packageId) => {
  router.push(`/packages/${packageId}/edit`)
}

const getPackageStatusClass = (pkg) => {
  if (pkg.package_category === 'time_based') {
    const now = new Date()
    const endDate = new Date(pkg.package_end_date)
    if (endDate < now) return 'status-expired'
    const diffDays = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24))
    if (diffDays <= 7) return 'status-expiring'
    return 'status-active'
  } else {
    const remainingLessons = pkg.remaining_lessons || 0
    if (remainingLessons === 0) return 'status-exhausted'
    if (remainingLessons <= 2) return 'status-low'
    return 'status-active'
  }
}

const getPackageStatusText = (pkg) => {
  if (pkg.package_category === 'time_based') {
    const now = new Date()
    const endDate = new Date(pkg.package_end_date)
    if (endDate < now) return '已过期'
    const diffDays = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24))
    if (diffDays <= 7) return `即将到期(${diffDays}天)`
    return '有效期内'
  } else {
    const remainingLessons = pkg.remaining_lessons || 0
    if (remainingLessons === 0) return '已用完'
    if (remainingLessons <= 2) return `剩余${remainingLessons}次`
    return `剩余${remainingLessons}次`
  }
}

const getPackageTypeText = (pkg) => {
  const typeMap = {
    '1v1': '一对一',
    '1v2': '一对二',
    '1v3': '一对三',
    '1v5': '一对五',
    '1v多': '一对多',
    'group': '团课',
    'online': '线上课',
    'time_based': '时长套餐'
  }
  return typeMap[pkg.package_type] || pkg.package_type || '课程套餐'
}

const getPackageExpiryText = (pkg) => {
  if (!pkg.package_end_date) return '永久有效'
  const endDate = new Date(pkg.package_end_date)
  return endDate.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const getStatusClass = (status) => {
  return {
    'status-attended': status === 'completed' || status === 'attended',
    'status-absent': status === 'absent',
    'status-cancel': status === 'cancel' || status === 'cancelled',
    'status-scheduled': status === 'scheduled'
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'completed': '已完成',
    'attended': '已上课',
    'absent': '缺席',
    'cancel': '已取消',
    'cancelled': '已取消',
    'scheduled': '已预约'
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
  border: 1px solid #e0e0e0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e8e8e8;
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
}

.title-icon {
  font-size: 20px;
}

.title-count {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  margin-left: 8px;
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
  font-size: 16px;
  color: #1a1a1a;
  font-weight: 600;
}

.detail-value {
  font-size: 16px;
  color: #1a1a1a;
  font-weight: 600;
}


/* 上课记录样式 */
.empty-records {
  text-align: center;
  padding: 60px 20px;
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

.timeline-dot.status-scheduled {
  background: #1890ff;
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
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.timeline-time {
  font-size: 14px;
  color: #666;
}

.timeline-status {
  font-size: 14px;
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

.timeline-status.status-scheduled {
  background: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.timeline-detail {
  font-size: 14px;
  color: #666;
}

/* 上课记录展开/折叠样式 */
.attendance-toggle {
  margin-top: 16px;
  text-align: center;
}

.btn-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #fff;
  color: #1890ff;
  border: 1px solid #1890ff;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-toggle:hover {
  background: #f0f9ff;
}

.toggle-icon {
  font-size: 12px;
  transition: transform 0.3s ease;
}

/* 套餐信息样式 */
.package-list-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.btn-add-package {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 16px 20px;
  background: #fff;
  color: #1890ff;
  border: 2px solid #1890ff;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
}

.btn-add-package:hover {
  background: #f0f9ff;
}

.add-icon {
  font-size: 18px;
  font-weight: 600;
  line-height: 1;
  display: inline-block;
}

.empty-packages {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  color: #666;
  font-weight: 500;
  margin-bottom: 4px;
}

.empty-desc {
  font-size: 14px;
  color: #999;
}

.package-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.package-item {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.package-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.package-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.package-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.package-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
  text-align: center;
  min-width: 60px;
}

.package-status.status-active {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #d9f7be;
}

.package-status.status-expiring {
  background: #fff7e6;
  color: #fa541c;
  border: 1px solid #ffd591;
}

.package-status.status-expired {
  background: #fff2e8;
  color: #fa541c;
  border: 1px solid #ffd591;
}

.package-status.status-low {
  background: #fff7e6;
  color: #fa541c;
  border: 1px solid #ffd591;
}

.package-status.status-exhausted {
  background: #f5f5f5;
  color: #999;
  border: 1px solid #d9d9d9;
}

.package-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 14px;
  color: #666;
  font-weight: 400;
}

.info-value {
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 500;
}

.info-value.price {
  font-weight: 600;
  color: #1890ff;
}
</style>