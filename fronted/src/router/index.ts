import { createRouter, createWebHistory } from 'vue-router'
// 引入你的组件
import Login from '../views/Login.vue'
import Layout from '../views/Layout.vue'
import UploadPage from '../views/UploadPage.vue'
import HistoryPage from '../views/HistoryPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      component: Login
    },
    {
      path: '/',
      component: Layout,
      redirect: '/upload', // <--- 关键点：访问 / 时重定向到 /upload
      children: [
        { path: 'upload', component: UploadPage },
        { path: 'history', component: HistoryPage }
      ]
    }
  ]
})

// 路由守卫：没登录就踢回 login
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login') // 强制跳转登录页
  } else {
    next()
  }
})

export default router
