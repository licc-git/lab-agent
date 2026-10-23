import { getToken } from '@/utils/auth';
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
    { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') },
    {
      path: '/manager', name: 'Layout', component: () => import('@/layouts/Layout.vue'),
      children: [
        { path: 'home', name: 'Home', component: () => import('@/views/Home.vue') },
        { path: 'lab', name: 'Lab', component: () => import('@/views/Lab.vue') },
        { path: 'equ', name: 'Equ', component: () => import('@/views/Equ.vue') },
        { path: 'user', name: 'User', component: () => import('@/views/User.vue') },
        { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue') },
        { path: 'password', name: 'Password', component: () => import('@/views/Password.vue') },
        { path: 'lab_list', name: 'LabList', component: () => import('@/views/LabList.vue') },
        { path: 'lab-equipment/:id', name: 'LabEquipment', component: () => import('@/views/LabEquipment.vue') },
        { path: 'audit-reservation', name: 'AuditReservation', component: () => import('@/views/AuditReservation.vue') },
        { path: 'my-reservation', name: 'MyReservation', component: () => import('@/views/MyReservation.vue') },
        { path: 'ai-chat', name: 'AiChat', component: () => import('@/views/AiChatStream.vue') },
      ]
    }

  ],
});

// 路由守卫
const whiteList = ['/login', '/register']

router.beforeEach((to, from) => {
  const token = getToken();

  if (token) {
    if (to.path === '/login' || to.path === '/register') {
      return '/manager/home'
    }
  } else {
    if (whiteList.includes(to.path)) {          // whiteList白名单
      return true
    } else {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }
})

export default router
