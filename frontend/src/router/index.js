import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Students from '@/views/Students.vue'
import StudentDetail from '@/views/StudentDetail.vue'
import AddStudent from '@/views/AddStudent.vue'
import EditStudent from '@/views/EditStudent.vue'
import CalendarView from '@/views/CalendarView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
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
    path: '/calendar',
    name: 'Calendar',
    component: CalendarView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router