import request from './index'

export const studentApi = {
  // 获取学员列表
  getAll() {
    return request.get('/students/?skip=0&limit=100')
  },
  
  // 获取学员详情
  getById(id) {
    return request.get(`/students/${id}`)
  },
  
  // 创建学员
  create(data) {
    return request.post('/students/', data)
  },
  
  // 更新学员
  update(id, data) {
    return request.put(`/students/${id}`, data)
  },
  
  // 删除学员
  delete(id) {
    return request.delete(`/students/${id}`)
  }
}