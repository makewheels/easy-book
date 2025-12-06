import axios from 'axios'

const API_BASE_URL = 'http://localhost:8004/api/packages'

export const packageApi = {
  /**
   * 获取所有套餐列表
   */
  async getAllPackages() {
    try {
      const response = await axios.get(API_BASE_URL)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || '获取套餐列表失败')
    }
  },

  /**
   * 根据ID获取套餐详情
   */
  async getPackageById(id) {
    try {
      const response = await axios.get(`${API_BASE_URL}/${id}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || '获取套餐详情失败')
    }
  },

  /**
   * 创建新套餐
   */
  async createPackage(packageData) {
    try {
      const response = await axios.post(API_BASE_URL, packageData)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || '创建套餐失败')
    }
  },

  /**
   * 更新套餐
   */
  async updatePackage(id, packageData) {
    try {
      const response = await axios.put(`${API_BASE_URL}/${id}`, packageData)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || '更新套餐失败')
    }
  },

  /**
   * 删除套餐
   */
  async deletePackage(id) {
    try {
      const response = await axios.delete(`${API_BASE_URL}/${id}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || '删除套餐失败')
    }
  },

  /**
   * 获取学生的套餐列表
   */
  async getStudentPackages(studentId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/student/${studentId}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || '获取学生套餐列表失败')
    }
  },

  /**
   * 为学生购买套餐
   */
  async purchasePackage(studentId, packageId) {
    try {
      const response = await axios.post(`${API_BASE_URL}/purchase`, {
        student_id: studentId,
        package_id: packageId
      })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || '购买套餐失败')
    }
  }
}