import axios from 'axios'

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
      console.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
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
          case 404:
            message = '资源不存在'
            break
          case 500:
            message = '服务器错误'
            break
          default:
            message = data.detail || `请求失败 (${status})`
        }
      }
    }
    
    console.error(message)
    return Promise.reject(new Error(message))
  }
)

export default request