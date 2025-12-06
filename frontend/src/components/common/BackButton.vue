<template>
  <button class="back-btn" @click="handleBack">
    {{ text }}
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  // 自定义返回路径，如果未提供则使用 router.back() 返回上一个页面
  to: {
    type: [String, Object],
    default: null
  },
  // 是否禁用返回功能
  disabled: {
    type: Boolean,
    default: false
  },
  // 自定义按钮文字
  text: {
    type: String,
    default: '← 返回'
  },
  // 自定义按钮样式类名
  customClass: {
    type: String,
    default: ''
  }
})

const router = useRouter()

const handleBack = () => {
  if (props.disabled) return

  if (props.to) {
    // 如果指定了返回路径，则导航到指定路径
    if (typeof props.to === 'string') {
      router.push(props.to)
    } else {
      router.push(props.to)
    }
  } else {
    // 默认行为：返回上一个页面
    router.back()
  }
}
</script>

<style scoped>
.back-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  margin-right: 15px;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: fit-content;
}

.back-btn:hover:not(:disabled) {
  background: #f0f0f0;
  color: #1a1a1a;
}

.back-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 如果需要自定义样式类名 */
.back-btn.custom-style {
  /* 可以通过 props.customClass 覆盖样式 */
}
</style>