<template>
  <div class="quick-actions">
    <button class="action-btn primary" @click="$emit('showAppointment')">
      📅 预约
    </button>
    <button class="action-btn secondary" @click="$emit('editStudent')">
      ✏️ 编辑
    </button>
  </div>
</template>

<script setup>
defineEmits(['showAppointment', 'editStudent'])
</script>

<style scoped>
.quick-actions {
  display: flex;
  gap: 15px;
  margin-top: 15px;
  margin-bottom: 15px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 20px;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
}

.action-btn.primary {
  background: #fff;
  color: #1989fa;
  border: 2px solid #1989fa;
}

.action-btn.primary:hover {
  background: #f0f9ff;
}

.action-btn.secondary {
  background: #fff;
  color: #1989fa;
  border: 2px solid #1989fa;
}

.action-btn.secondary:hover {
  background: #f0f9ff;
}

</style>