import axios from 'axios'

const BASE_URL = '/api'

export const appointmentApi = {
  // 获取学员预约列表
  async getStudentAppointments(studentId, status = null) {
    try {
      const params = status ? `?status=${status}` : ''
      const response = await axios.get(`${BASE_URL}/appointments/student/${studentId}${params}`)
      return response.data
    } catch (error) {
      console.error('获取学员预约失败:', error)
      throw error
    }
  },

  // 创建学生预约
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
      const response = await axios.post(`${BASE_URL}/appointments/${appointmentId}/cancel`)
      return response.data
    } catch (error) {
      console.error('取消预约失败:', error)
      throw error
    }
  },

  // 学员签到
  async checkin(appointmentId) {
    try {
      const response = await axios.post(`${BASE_URL}/appointments/${appointmentId}/checkin`)
      return response.data
    } catch (error) {
      console.error('签到失败:', error)
      throw error
    }
  },

  // 获取每日预约（用于日历显示）
  async getDailyAppointments(date) {
    try {
      const response = await axios.get(`${BASE_URL}/appointments/daily/${date}`)
      return response.data
    } catch (error) {
      console.error('获取每日预约失败:', error)
      throw error
    }
  },

  // 批量获取时间范围内的预约数据（用于日历优化）
  async getBatchAppointments(startDate, endDate) {
    try {
      const response = await axios.get(`${BASE_URL}/appointments/batch`, {
        params: {
          start_date: startDate,
          end_date: endDate
        }
      })
      return response.data
    } catch (error) {
      console.error('批量获取预约失败:', error)
      throw error
    }
  },

  // 获取课程的预约列表
  async getCourseAppointments(courseId) {
    try {
      const response = await axios.get(`${BASE_URL}/appointments/course/${courseId}`)
      return response.data
    } catch (error) {
      console.error('获取课程预约失败:', error)
      throw error
    }
  }
}