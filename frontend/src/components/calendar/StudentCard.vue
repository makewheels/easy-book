<template>
  <div
    class="student-card"
    :class="statusClass"
    @click.stop="$emit('click', student.student_id)"
  >
    <div class="student-name">{{ student.name }}</div>

    <!-- 已签到状态 -->
    <div v-if="student.status === 'checked'" class="status-label checked-label">
      ✓ 已签到
    </div>

    <!-- 已取消状态 -->
    <div v-else-if="student.status === 'cancel'" class="status-label cancel-label">
      ✗ 已取消
    </div>

    <!-- 操作按钮 -->
    <div v-else class="action-buttons">
      <button
        class="btn-checkin"
        :disabled="actionLoading"
        @click.stop="handleCheckin"
      >来了</button>
      <button
        class="btn-cancel"
        :disabled="actionLoading"
        @click.stop="handleCancel"
      >没来</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { attendanceApi } from '@/api/attendance'

const props = defineProps({
  student: {
    type: Object,
    required: true
  },
  date: {
    type: String,
    required: true
  },
  timeSlot: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['click', 'checkin-updated'])

const actionLoading = ref(false)

const statusClass = computed(() => {
  if (props.student.status === 'checked') return 'status-checked'
  if (props.student.status === 'cancel') return 'status-cancel'

  const appointmentDateTime = new Date(`${props.date}T${props.timeSlot}:00`)
  const now = new Date()
  return appointmentDateTime > now ? 'status-upcoming' : 'status-during'
})

const handleCheckin = async (e) => {
  e.stopPropagation()
  if (actionLoading.value) return
  actionLoading.value = true
  try {
    await attendanceApi.checkin(props.student.appointment_id, props.student.student_id)
    emit('checkin-updated')
  } catch (error) {
    console.error('签到失败:', error)
  } finally {
    actionLoading.value = false
  }
}

const handleCancel = async (e) => {
  e.stopPropagation()
  if (actionLoading.value) return
  actionLoading.value = true
  try {
    await attendanceApi.markCancel(props.student.appointment_id, props.student.student_id)
    emit('checkin-updated')
  } catch (error) {
    console.error('取消失败:', error)
  } finally {
    actionLoading.value = false
  }
}
</script>

<style scoped>
.student-card {
  background: #fff;
  color: #1a1a1a;
  font-weight: 700;
  padding: 4px 2px;
  height: 100%;
  min-height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  text-align: center;
  box-sizing: border-box;
  line-height: 1.2;
  margin: 0;
  border: none;
  gap: 2px;
}

.student-name {
  font-size: 14px;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.status-label {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 0;
}

.checked-label {
  color: #fff;
}

.cancel-label {
  color: #999;
}

.action-buttons {
  display: flex;
  gap: 2px;
  width: 100%;
  padding: 0 2px;
  box-sizing: border-box;
}

.btn-checkin,
.btn-cancel {
  flex: 1;
  min-height: 24px;
  border: none;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  padding: 2px 0;
  line-height: 1;
  touch-action: manipulation;
}

.btn-checkin {
  background: #52c41a;
  color: #fff;
}

.btn-checkin:active {
  background: #389e0d;
}

.btn-cancel {
  background: #d9d9d9;
  color: #666;
}

.btn-cancel:active {
  background: #bfbfbf;
}

.btn-checkin:disabled,
.btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 状态颜色 */
.status-upcoming {
  background: #1890ff;
  color: #fff;
}

.status-upcoming .student-name {
  color: #fff;
}

.status-active {
  background: #faad14;
  color: #fff;
}

.status-checked {
  background: #52c41a;
  color: #fff;
}

.status-checked .student-name {
  color: #fff;
}

.status-during {
  background: #d9d9d9;
  color: #666;
}

.status-during .student-name {
  color: #666;
}

.status-cancel {
  background: #f5f5f5;
  color: #bfbfbf;
}

.status-cancel .student-name {
  color: #bfbfbf;
}

@media (min-width: 430px) {
  .btn-checkin,
  .btn-cancel {
    min-height: 36px;
    font-size: 13px;
  }
}
</style>