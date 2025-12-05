import axios from 'axios'
import { toast } from '@/utils/toast'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { data } = response

    // 如果有code字段，统一处理
    if (data.code !== undefined && data.code !== 200) {
      const errorMessage = data.message || '请求失败'
      console.error(errorMessage)
      // 显示错误信息给用户
      toast.error(errorMessage)
      return Promise.reject(new Error(errorMessage))
    }

    return data
  },
  (error) => {
    let message = '网络错误'

    if (error.response) {
      const { status, data } = error.response

      // 优先使用新的错误格式
      if (data.code !== undefined && data.message) {
        message = data.message
      } else {
        switch (status) {
          case 400:
            message = data.detail || '请求参数错误'
            break
          case 401:
            message = '登录已过期，请重新登录'
            break
          case 403:
            message = '没有权限访问'
            break
          case 404:
            message = '资源不存在'
            break
          case 422:
            message = data.detail || '数据验证失败'
            break
          case 500:
            message = '服务器错误'
            break
          case 502:
            message = '网关错误'
            break
          case 503:
            message = '服务暂时不可用'
            break
          case 504:
            message = '网关超时'
            break
          default:
            message = data.detail || `请求失败 (${status})`
        }
      }
    } else if (error.request) {
      // 网络错误
      message = '网络连接失败，请检查网络设置'
    } else {
      // 其他错误
      message = error.message || '未知错误'
    }

    console.error(message)
    // 显示错误信息给用户
    toast.error(message)
    return Promise.reject(new Error(message))
  }
)

export default request