import axios from 'axios'

const BASE_URL = '/api'

export const courseApi = {
  // 获取每日课程
  async getDailyCourses(date) {
    try {
      const response = await axios.get(`${BASE_URL}/courses/daily/${date}`)
      return response.data
    } catch (error) {
      console.error('获取每日课程失败:', error)
      throw error
    }
  },

  // 获取日期范围内的课程
  async getCoursesByRange(startDate, endDate) {
    try {
      const response = await axios.get(`${BASE_URL}/courses/range?start_date=${startDate}&end_date=${endDate}`)
      return response.data
    } catch (error) {
      console.error('获取课程范围失败:', error)
      throw error
    }
  },

  // 获取单个课程
  async getCourse(courseId) {
    try {
      const response = await axios.get(`${BASE_URL}/courses/${courseId}`)
      return response.data
    } catch (error) {
      console.error('获取课程失败:', error)
      throw error
    }
  }
}