<template>
  <div class="quick-actions">
    <button class="action-btn primary" @click="$emit('showAppointment')">
      <span class="btn-icon">📅</span>
      新增预约
    </button>
    <button class="action-btn secondary" @click="$emit('editStudent')">
      <span class="btn-icon">✏️</span>
      编辑信息
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
  margin-bottom: 20px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 20px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-btn.primary {
  background: linear-gradient(135deg, #1989fa 0%, #096dd9 100%);
  color: #fff;
}

.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 137, 250, 0.4);
}

.action-btn.secondary {
  background: #fff;
  color: #1989fa;
  border: 2px solid #1989fa;
}

.action-btn.secondary:hover {
  background: #f0f9ff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 137, 250, 0.3);
}

.btn-icon {
  font-size: 18px;
}
</style>