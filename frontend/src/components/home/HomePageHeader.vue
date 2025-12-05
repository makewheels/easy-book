<template>
  <div class="header">
    <div class="header-content">
      <h1 class="page-title">预约管理</h1>
      <div class="stats-container">
        <div class="stat-card today">
          <div class="stat-number">{{ todayAppointments }}</div>
          <div class="stat-label">今日预约</div>
        </div>
        <div class="stat-card tomorrow">
          <div class="stat-number">{{ tomorrowAppointments }}</div>
          <div class="stat-label">明日预约</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  todayAppointments: {
    type: Number,
    default: 0
  },
  tomorrowAppointments: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped>
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

.page-title {
  font-size: 32px;
  font-weight: 800;
  margin: 0 0 20px 0;
  text-align: center;
  color: #1a1a1a;
}

.stats-container {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.stat-card {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(25, 137, 250, 0.2);
}

.stat-card.today {
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  border-color: rgba(24, 144, 255, 0.3);
}

.stat-card.tomorrow {
  background: linear-gradient(135deg #f0f9ff 0%, #e0f2fe 100%);
  border-color: rgba(25, 137, 250, 0.2);
}

.stat-number {
  font-size: 36px;
  font-weight: 800;
  color: #1989fa;
  margin-bottom: 8px;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  opacity: 0.8;
}
</style>