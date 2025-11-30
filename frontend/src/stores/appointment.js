import { defineStore } from 'pinia'
import { appointmentApi } from '@/api/appointment'
import { getToday } from '@/utils/date'

export const useAppointmentStore = defineStore('appointment', {
  state: () => ({
    appointments: [],
    todayAppointments: [],
    dailyAppointmentsData: null,
    selectedDate: getToday(),
    loading: false,
    error: null
  }),
  
  getters: {
    appointmentsByDate: (state) => {
      // 直接返回后端数据，包装成数组格式以兼容现有逻辑
      if (!state.dailyAppointmentsData) {
        return []
      }
      
      // 确保slots存在
      if (!state.dailyAppointmentsData.slots) {
        return []
      }
      
      return [state.dailyAppointmentsData]
    }
  },
  
  actions: {
    async fetchDailyAppointments(date = this.selectedDate) {
      this.loading = true
      this.error = null
      
      try {
        console.log('获取每日预约数据，日期:', date)
        const response = await appointmentApi.getDaily(date)
        console.log('API响应:', response)
        
        // 直接存储后端返回的数据，让getter处理数据转换
        if (response && response.data) {
          this.dailyAppointmentsData = response.data
          console.log('存储的每日预约数据:', this.dailyAppointmentsData)
        } else {
          console.warn('API响应数据结构不正确:', response)
          this.dailyAppointmentsData = null
        }
        
        this.selectedDate = date
        
      } catch (error) {
        console.error('获取每日预约数据失败:', error)
        this.error = error.message
        this.dailyAppointmentsData = null
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async createAppointment(appointmentData) {
      this.loading = true
      
      try {
        const newAppointment = await appointmentApi.create(appointmentData)
        this.appointments.push(newAppointment)
        
        // 刷新当日预约
        await this.fetchDailyAppointments(this.selectedDate)
        
        return newAppointment
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async updateAppointment(id, data) {
      this.loading = true
      
      try {
        const updatedAppointment = await appointmentApi.update(id, data)
        const index = this.appointments.findIndex(a => a.id === id)
        if (index !== -1) {
          this.appointments[index] = updatedAppointment
        }
        
        return updatedAppointment
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async deleteAppointment(id) {
      this.loading = true
      
      try {
        await appointmentApi.delete(id)
        this.appointments = this.appointments.filter(a => a.id !== id)
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    setSelectedDate(date) {
      this.selectedDate = date
    },
    
    clearError() {
      this.error = null
    }
  }
})

function getWeekday(date) {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekdays[new Date(date).getDay()]
}