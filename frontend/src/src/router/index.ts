import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import EmptyLayout from '@/layout/EmptyLayout.vue'
import DefaultLayout from '@/layout/DefaultLayout.vue'
import ChatLayout from '@/layout/ChatLayout.vue'

// Main pages
const Home = () => import('@/pages/HomeView.vue')
const Category = () => import('@/pages/CategoryView.vue')
const Articles = () => import('@/pages/ArticleContentView.vue')
const Search = () => import('@/pages/SearchPage.vue')
const Login = () => import('@/pages/LoginView.vue')
const Register = () => import('@/pages/RegisterView.vue')

const HomeChat = () => import('@/pages/chat/HomeChatView.vue')
const ActiveChat = () => import('@/pages/chat/ActiveChatView.vue')

// Array of categories (easy to scale in the future)
const CATEGORIES = ['security', 'privacy', 'tech', 'crypto']

// Generate category routes dynamically
const categoryRoutes: RouteRecordRaw[] = CATEGORIES.map((cat) => ({
  path: `/${cat}`,
  name: cat,
  component: Category,
  meta: { layout: DefaultLayout },
  props: { category: cat },
}))

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/home', meta: { layout: DefaultLayout } },
  { path: '/home', name: 'Home', component: Home, meta: { layout: DefaultLayout } },

  ...categoryRoutes,

  {
    path: '/article/:id',
    name: 'article-detail',
    component: Articles,
    meta: { layout: DefaultLayout },
  },
  { path: '/search', name: 'Search', component: Search, meta: { layout: DefaultLayout } },

  // === AUTH ===
  { path: '/login', name: 'Login', component: Login, meta: { layout: EmptyLayout } },
  { path: '/register', name: 'Register', component: Register, meta: { layout: EmptyLayout } },

  // === CHAT ===
  {
    path: '/chat',
    meta: { layout: ChatLayout },
    children: [
      { path: '', name: 'chat-home', component: HomeChat },
      { path: 'new', name: 'chat-new', redirect: { name: 'chat-home' } },
      { path: ':id', name: 'chat-active', component: ActiveChat },
    ],
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
