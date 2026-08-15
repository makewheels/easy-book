import { createRouter, createWebHistory } from 'vue-router'
import Students from '@/views/Students.vue'
import StudentDetail from '@/views/StudentDetail.vue'
import AddStudent from '@/views/AddStudent.vue'
import EditStudent from '@/views/EditStudent.vue'
import CalendarView from '@/views/CalendarView.vue'
import AddAppointment from '@/views/AddAppointment.vue'
import CalendarAppointment from '@/views/CalendarAppointment.vue'
import AddPackage from '@/views/AddPackage.vue'
import EditPackage from '@/views/EditPackage.vue'
import Login from '@/views/Login.vue'
import AssistantView from '@/views/AssistantView.vue'

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
  },
  {
    path: '/student/:studentId/add-package',
    name: 'AddPackage',
    component: AddPackage
  },
  {
    path: '/packages/:id/edit',
    name: 'EditPackage',
    component: EditPackage
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/assistant',
    name: 'Assistant',
    component: AssistantView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 总是滚动到页面顶部
    return { top: 0 }
  }
})

// 登录守卫：无令牌一律先回登录页（后端生产环境强制鉴权）
router.beforeEach((to) => {
  const token = localStorage.getItem('eb_token')
  if (!token && to.path !== '/login') {
    return '/login'
  }
  if (token && to.path === '/login') {
    return '/'
  }
})

export default router