import { createApp } from 'vue'
import Toast from '@/components/Toast.vue'

const toastPool = []

export const toast = {
  info(message, duration = 3000) {
    this.show(message, 'info', duration)
  },
  success(message, duration = 3000) {
    this.show(message, 'success', duration)
  },
  warning(message, duration = 3000) {
    this.show(message, 'warning', duration)
  },
  error(message, duration = 3000) {
    this.show(message, 'error', duration)
  },
  show(message, type = 'info', duration = 3000) {
    const mountPoint = document.createElement('div')
    document.body.appendChild(mountPoint)
    
    const app = createApp(Toast, {
      message,
      type,
      duration
    })
    
    const instance = app.mount(mountPoint)
    
    toastPool.push({
      app,
      mountPoint
    })
    
    // 自动清理
    if (duration > 0) {
      setTimeout(() => {
        app.unmount()
        document.body.removeChild(mountPoint)
        const index = toastPool.findIndex(item => item.mountPoint === mountPoint)
        if (index > -1) {
          toastPool.splice(index, 1)
        }
      }, duration + 300) // 等待动画完成
    }
  }
}

// 替代 alert 的函数
export const alert = (message) => {
  toast.info(message)
}

// 替代 confirm 的函数（简化版，只显示信息）
export const confirm = (message) => {
  toast.info(message)
  return Promise.resolve(false) // 总是返回 false，表示取消
}