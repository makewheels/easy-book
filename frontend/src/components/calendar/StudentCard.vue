<template>
  <div
    class="student-card"
    :class="statusClass"
    @click.stop="$emit('click', student.student_id)"
  >
    <div class="student-name">{{ student.name }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

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

const emit = defineEmits(['click'])

const statusClass = computed(() => {
  // 创建预约时间来与当前时间比较
  const appointmentDateTime = new Date(`${props.date}T${props.timeSlot}:00`)
  const now = new Date()

  // 如果预约时间还未到，显示蓝色（未上课）
  if (appointmentDateTime > now) {
    return 'status-upcoming'   // 未来时间 - 蓝色
  } else {
    // 预约时间已过，显示灰色（已完成或已错过）
    return 'status-during'     // 过去时间 - 灰色
  }
})
</script>

<style scoped>
.student-card {
  background: #fff;
  color: #1a1a1a;
  font-weight: 700;
  padding: 8px 4px;
  height: 100%;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  text-align: center;
  box-sizing: border-box;
  line-height: 1.2;
  margin: 0;
  border: none;
}

.student-name {
  font-size: 16px;
  font-weight: 800;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 状态颜色 - 填满整个单元格 */
.status-upcoming {
  background: #1890ff;
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

.status-during {
  background: #d9d9d9;
  color: #666;
}

.status-cancel {
  background: #f5f5f5;
  color: #bfbfbf;
}
</style>