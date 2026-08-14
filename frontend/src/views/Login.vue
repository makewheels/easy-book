<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-logo">🏊</div>
      <h1 class="login-title">泳课预约系统</h1>
      <p class="login-subtitle">登录后管理学员、课包与排课</p>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-field">
          <label>手机号</label>
          <input
            v-model.trim="phone"
            type="tel"
            autocomplete="tel"
            maxlength="20"
            placeholder="请输入手机号"
            :disabled="loading"
          />
        </div>
        <div class="form-field">
          <label>密码</label>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            :disabled="loading"
          />
        </div>
        <button type="submit" class="login-btn" :disabled="loading || !phone || !password">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api'
import { toast } from '@/utils/toast'

const router = useRouter()
const phone = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!phone.value || !password.value) return
  loading.value = true
  try {
    const data = await request.post('/auth/login', {
      phone: phone.value,
      password: password.value
    })
    localStorage.setItem('eb_token', data.token)
    localStorage.setItem('eb_phone', data.phone)
    // 会话 cookie：nginx 用它拦截 /ai（未登录跳回本页）
    document.cookie = `eb_token=${data.token}; path=/; max-age=${data.expires_in || 43200}; SameSite=Lax`
    toast.success('登录成功')
    router.replace('/')
  } catch (e) {
    // 401 等错误提示由拦截器/此处兜底
    toast.error(e?.response?.data?.detail || '手机号或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  max-width: 430px;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background: linear-gradient(180deg, #eff6ff 0%, #f5f5f5 40%);
}

.login-card {
  width: 100%;
  background: white;
  border-radius: 16px;
  padding: 40px 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.login-logo {
  font-size: 48px;
  text-align: center;
}

.login-title {
  margin: 12px 0 6px;
  text-align: center;
  font-size: 22px;
  color: #333;
}

.login-subtitle {
  margin: 0 0 28px;
  text-align: center;
  font-size: 13px;
  color: #999;
}

.form-field {
  margin-bottom: 18px;
}

.form-field label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  margin-bottom: 6px;
}

.form-field input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 15px;
  outline: none;
  box-sizing: border-box;
}

.form-field input:focus {
  border-color: #2196f3;
}

.login-btn {
  width: 100%;
  padding: 13px;
  margin-top: 8px;
  border: none;
  border-radius: 8px;
  background: #2196f3;
  color: white;
  font-size: 16px;
  font-weight: 500;
}

.login-btn:disabled {
  background: #a8d3f7;
}
</style>
