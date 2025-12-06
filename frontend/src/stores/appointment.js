import { defineStore } from 'pinia'
import { appointmentApi } from '@/api/appointment'

export const useAppointmentStore = defineStore('appointment', {
  state: () => ({
    weekAppointments: {},
    loading: false,
    error: null
  }),

  actions: {
    // 获取一周的预约数据
    async fetchWeekAppointments(startDate) {
      this.loading = true
      this.error = null

      try {
        // 暂时返回空数据，让页面能正常显示
        const appointmentsByDate = {}

        // 延迟1秒模拟加载
        await new Promise(resolve => setTimeout(resolve, 1000))

        this.weekAppointments = appointmentsByDate
        return appointmentsByDate

      } catch (error) {
        console.error('获取一周预约数据失败:', error)
        this.error = error.message || '获取预约数据失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建预约
    async createAppointment(appointmentData) {
      this.loading = true
      this.error = null

      try {
        const response = await appointmentApi.create(appointmentData)
        return response
      } catch (error) {
        console.error('创建预约失败:', error)
        this.error = error.message || '创建预约失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 清除错误
    clearError() {
      this.error = null
    }
  }
})