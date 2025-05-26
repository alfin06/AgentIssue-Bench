import { createRouter, createWebHistory } from 'vue-router'
import Leaderboard from './components/Leaderboard.vue'

const routes = [
  {
    path: '/',
    redirect: '/leaderboard',
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: Leaderboard,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
