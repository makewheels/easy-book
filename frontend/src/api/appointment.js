import request from './index'

export const appointmentApi = {
  // 创建预约
  create(data) {
    return request.post('/appointments/', data)
  },
  
  // 获取学员预约
  getByStudent(studentId, futureOnly = false) {
    return request.get(`/appointments/student/${studentId}?future_only=${futureOnly}`)
  },
  
  // 获取每日预约
  getDaily(date) {
    return request.get(`/appointments/daily/${date}`)
  },

  // 获取从今天到未来的所有预约
  getUpcoming(days = 30) {
    return request.get(`/appointments/upcoming?days=${days}`)
  },
  
  // 更新预约
  update(id, data) {
    return request.put(`/appointments/${id}`, data)
  },
  
  // 删除预约
  delete(id) {
    return request.delete(`/appointments/${id}`)
  }
}