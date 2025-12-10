<template>
  <div class="time-column">
    <div class="time-header"></div>
    <div
      v-for="timeSlot in timeSlots"
      :key="timeSlot"
      class="time-cell-fixed"
    >
      {{ timeSlot }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  timeSlots: {
    type: Array,
    required: true
  }
})
</script>

<style scoped>
.time-column {
  width: 60px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  margin-top: 0px;
}

.time-header {
  height: 54px;
  background: #f5f5f5;
  border-bottom: 2px solid #e3f2fd;
  border-right: 0.5px solid #e0e0e0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
}

.time-cell-fixed {
  background: #f9f9f9;
  font-size: 12px;
  font-weight: 700;
  color: #0050b3;
  border-bottom: 0.5px solid #e0e0e0;
  border-right: 0.5px solid #e0e0e0;
  padding: 0;
  text-align: center;
  vertical-align: middle;
  height: var(--time-slot-height);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
  box-sizing: border-box;
  margin: 0;
}
</style>