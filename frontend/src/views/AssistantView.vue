<template>
  <div class="assistant-page">
    <iframe
      class="assistant-frame"
      src="/ai/"
      title="AI 助手"
      allow="microphone; clipboard-write"
    ></iframe>
    <BottomNavigation :active-tab="'ai'" @navigate="navigateTo" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import BottomNavigation from '@/components/BottomNavigation.vue'

const router = useRouter()

const navigateTo = (page) => {
  switch (page) {
    case 'home':
      router.push('/')
      break
    case 'calendar':
      router.push('/')
      break
    case 'students':
      router.push('/students')
      break
    case 'ai':
      break
  }
}
</script>

<style scoped>
.assistant-page {
  height: 100vh;
  background: #f5f5f5;
}

/* Chainlit 以 iframe 嵌入，占满底部导航之上的区域（导航固定 70px 高） */
.assistant-frame {
  width: 100%;
  height: calc(100vh - 70px);
  border: none;
  display: block;
  background: #fff;
}
</style>
