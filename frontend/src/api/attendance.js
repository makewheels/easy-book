import request from './index'

export const attendanceApi = {
  // 签到
  checkin(appointmentId, studentId) {
    return request.post('/attendance/checkin', {
      appointment_id: appointmentId,
      student_id: studentId
    })
  },
  
  // 标记取消
  markCancel(appointmentId, studentId) {
    return request.post('/attendance/cancel', {
      appointment_id: appointmentId,
      student_id: studentId
    })
  },
  
  // 获取学员上课记录
  getByStudent(studentId) {
    return request.get(`/attendance/student/${studentId}`)
  }
}