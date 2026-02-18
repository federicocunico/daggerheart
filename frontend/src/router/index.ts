import { createRouter, createWebHashHistory } from 'vue-router'
import BuilderView from '@/views/BuilderView.vue'
import SchemaView  from '@/views/SchemaView.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/',       name: 'builder', component: BuilderView },
    { path: '/schema', name: 'schema',  component: SchemaView  },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
