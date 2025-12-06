import axios from 'axios'

const BASE_URL = 'http://localhost:8003/api'

export const appointmentApi = {
  // 获取学员预约列表
  async getStudentAppointments(studentId, options = {}) {
    const params = new URLSearchParams()
    if (options.futureOnly) {
      params.append('future_only', 'true')
    }

    try {
      const response = await axios.get(`${BASE_URL}/appointments/student/${studentId}?${params}`)
      return response.data
    } catch (error) {
      console.error('获取学员预约失败:', error)
      throw error
    }
  },

  // 创建预约
  async create(appointmentData) {
    try {
      const response = await axios.post(`${BASE_URL}/appointments/`, appointmentData)
      return response.data
    } catch (error) {
      console.error('创建预约失败:', error)
      throw error
    }
  },

  // 取消预约
  async cancel(appointmentId) {
    try {
      const response = await axios.put(`${BASE_URL}/appointments/${appointmentId}/cancel`)
      return response.data
    } catch (error) {
      console.error('取消预约失败:', error)
      throw error
    }
  },

  // 获取每日预约
  async getDailyAppointments(date) {
    try {
      const response = await axios.get(`${BASE_URL}/appointments/daily/${date}`)
      return response.data
    } catch (error) {
      console.error('获取每日预约失败:', error)
      throw error
    }
  },

  // 获取未来预约
  async getUpcomingAppointments(days = 30) {
    try {
      const response = await axios.get(`${BASE_URL}/appointments/upcoming?days=${days}`)
      return response.data
    } catch (error) {
      console.error('获取未来预约失败:', error)
      throw error
    }
  }
}