import { defineStore } from 'pinia'
import { appointmentApi } from '@/api/appointment'
import { getToday } from '@/utils/date'
import { format, addDays, startOfWeek, endOfWeek } from 'date-fns'

export const useAppointmentStore = defineStore('appointment', {
  state: () => ({
    appointments: [],
    todayAppointments: [],
    dailyAppointmentsData: null,
    upcomingAppointmentsData: [], // 存储从今天到未来的所有预约
    selectedDate: getToday(),
    loading: false,
    error: null,
    // 周数据缓存
    weekCache: new Map(), // key: startDate, value: { weekData, timestamp }
    weekLoading: false
  }),
  
  getters: {
    appointmentsByDate: (state) => {
      // 首先尝试返回未来预约数据，如果没有则返回当日数据
      if (state.upcomingAppointmentsData && state.upcomingAppointmentsData.length > 0) {
        return state.upcomingAppointmentsData
      }

      // 如果没有未来预约数据，回退到当日数据
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

        return this.dailyAppointmentsData

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
    },

    // 获取从今天到未来的所有预约
    async fetchUpcomingAppointments(days = 30) {
      this.loading = true
      this.error = null

      try {
        console.log(`获取未来${days}天的预约数据`)
        const response = await appointmentApi.getUpcoming(days)
        console.log('未来预约API响应:', response)

        // 存储返回的多日数据
        if (response && response.data && Array.isArray(response.data)) {
          this.upcomingAppointmentsData = response.data
          console.log('存储的未来预约数据:', this.upcomingAppointmentsData)
        } else {
          console.warn('未来预约API响应数据结构不正确:', response)
          this.upcomingAppointmentsData = []
        }

        return this.upcomingAppointmentsData

      } catch (error) {
        console.error('获取未来预约数据失败:', error)
        this.error = error.message
        this.upcomingAppointmentsData = []
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取一周的数据
    async fetchWeekAppointments(weekStartDate = startOfWeek(new Date(), { weekStartsOn: 1 })) {
      this.weekLoading = true
      this.error = null

      const cacheKey = format(weekStartDate, 'yyyy-MM-dd')

      // 检查缓存（缓存有效期5分钟）
      const cached = this.weekCache.get(cacheKey)
      if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
        this.weekLoading = false
        return cached.weekData
      }

      try {
        console.log('获取周数据，开始日期:', cacheKey)

        // 生成7天的日期
        const dates = []
        for (let i = 0; i < 7; i++) {
          const date = addDays(weekStartDate, i)
          dates.push(format(date, 'yyyy-MM-dd'))
        }

        // 并发获取一周的数据
        const promises = dates.map(date =>
          appointmentApi.getDaily(date)
            .catch(error => {
              console.error(`获取${date}数据失败:`, error)
              return null
            })
        )

        const results = await Promise.allSettled(promises)

        // 转换为周视图数据格式
        const weekData = {}
        results.forEach((result, index) => {
          const date = dates[index]
          if (result.status === 'fulfilled' && result.value?.data) {
            weekData[date] = result.value.data
          } else {
            weekData[date] = { slots: [] }
          }
        })

        // 缓存数据
        this.weekCache.set(cacheKey, {
          weekData,
          timestamp: Date.now()
        })

        this.weekLoading = false
        return weekData

      } catch (error) {
        console.error('获取周数据失败:', error)
        this.error = error.message
        this.weekLoading = false
        throw error
      }
    },

    // 清除周缓存
    clearWeekCache() {
      this.weekCache.clear()
    }
  }
})

function getWeekday(date) {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekdays[new Date(date).getDay()]
}