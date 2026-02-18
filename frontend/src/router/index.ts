import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView    from '@/views/HomeView.vue'
import BuilderView from '@/views/BuilderView.vue'

const router = createRouter({
  // Hash history works on GitHub Pages without server-side config
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/',      name: 'home',    component: HomeView },
    { path: '/build', name: 'builder', component: BuilderView },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
