export function formatDate(date) {
  const d = new Date(date)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

export function formatDateText(date) {
  const d = new Date(date)
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${formatDate(date)} ${weekdays[d.getDay()]}`
}

export function formatTime(time) {
  return time.slice(0, 5)
}

export function getToday() {
  return new Date().toISOString().split('T')[0]
}

export function getWeekday(date) {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekdays[new Date(date).getDay()]
}

export function isPastDate(date) {
  return new Date(date) < new Date().setHours(0, 0, 0, 0)
}

export function addDays(date, days) {
  const result = new Date(date)
  result.setDate(result.getDate() + days)
  return result.toISOString().split('T')[0]
}

export function getTomorrow() {
  return addDays(getToday(), 1)
}

export function isMonday(date) {
  return new Date(date).getDay() === 1 // 周一返回1
}