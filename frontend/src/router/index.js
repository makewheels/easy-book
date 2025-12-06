import { createRouter, createWebHistory } from 'vue-router'
import Students from '@/views/Students.vue'
import StudentDetail from '@/views/StudentDetail.vue'
import AddStudent from '@/views/AddStudent.vue'
import EditStudent from '@/views/EditStudent.vue'
import CalendarView from '@/views/CalendarView.vue'
import AddAppointment from '@/views/AddAppointment.vue'
import CalendarAppointment from '@/views/CalendarAppointment.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: CalendarView
  },
  {
    path: '/calendar',
    name: 'Calendar',
    component: CalendarView
  },
  {
    path: '/students',
    name: 'Students',
    component: Students
  },
  {
    path: '/student/:id',
    name: 'StudentDetail',
    component: StudentDetail
  },
  {
    path: '/student/:id/edit',
    name: 'EditStudent',
    component: EditStudent
  },
  {
    path: '/add-student',
    name: 'AddStudent',
    component: AddStudent
  },
  {
    path: '/student/:studentId/add-appointment',
    name: 'AddAppointment',
    component: AddAppointment
  },
  {
    path: '/calendar-appointment',
    name: 'CalendarAppointment',
    component: CalendarAppointment
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router