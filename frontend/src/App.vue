<template>
  <div class="app-container">
    <router-view />
    <Toast ref="toastRef" message="" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Toast from '@/components/Toast.vue'

const toastRef = ref(null)
</script>

<style>
.app-container {
  max-width: 430px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f5f5;
  position: relative;
}
</style>