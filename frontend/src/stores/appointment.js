import { defineStore } from 'pinia'
import { appointmentApi } from '@/api/appointment'
import { format, addDays, startOfWeek, endOfWeek, parseISO } from 'date-fns'

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
        // 获取未来30天的预约数据
        const response = await appointmentApi.getUpcomingAppointments(30)
        const upcomingData = response.data || []

  
        // 计算一周的日期范围
        const weekStart = startOfWeek(startDate, { weekStartsOn: 1 }) // 周一开始
        const weekEnd = endOfWeek(startDate, { weekStartsOn: 1 }) // 周日结束

        // 初始化一周的数据结构
        const appointmentsByDate = {}

        // 为一周的每一天创建数据结构（从周二到周日，跳过周一）
        for (let i = 1; i <= 6; i++) {
          const currentDate = format(addDays(weekStart, i), 'yyyy-MM-dd')
          appointmentsByDate[currentDate] = {
            date: currentDate,
            slots: []
          }
        }

        // 处理API返回的数据（API已经按日期和时间段组织好了）
        upcomingData.forEach(dayData => {
          const dateStr = dayData.date

          // 如果预约在这一周内
          if (appointmentsByDate[dateStr]) {
            // 直接使用API返回的slots数据
            if (dayData.slots && dayData.slots.length > 0) {
              appointmentsByDate[dateStr].slots = dayData.slots
            }
          }
        })

        // 对每个时间段按学生数量排序
        Object.values(appointmentsByDate).forEach(dayData => {
          dayData.slots.sort((a, b) => b.students.length - a.students.length)
        })

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

    // 取消预约
    async cancelAppointment(appointmentId) {
      this.loading = true
      this.error = null

      try {
        const response = await appointmentApi.cancel(appointmentId)
        return response
      } catch (error) {
        console.error('取消预约失败:', error)
        this.error = error.message || '取消预约失败'
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