import { createRouter, createWebHistory } from 'vue-router'
import EditPortrait from '../views/EditPortrait.vue'
import StyleLab from '../views/StyleLab.vue'
import ProtocolManagement from '../views/ProtocolManagement.vue'
import DiscoverySquare from '../views/DiscoverySquare.vue'
import ActorProfile from '../views/ActorProfile.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'
import AdminEnterpriseUsersView from '../views/AdminEnterpriseUsersView.vue'
import { authStore } from '../lib/auth'

function loginPathForRoute(to) {
  const roles = Array.isArray(to?.meta?.roles) ? to.meta.roles : []
  if (roles.length === 1 && roles[0] === 'admin') {
    return '/admin/login'
  }
  if (roles.length === 1 && roles[0] === 'enterprise') {
    return '/login/enterprise'
  }
  return '/login/individual'
}

const routes = [
  { path: '/', redirect: '/login/individual' },
  { path: '/login', redirect: '/login/individual' },
  { path: '/admin', redirect: '/admin/login' },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminLoginView,
    meta: { guestOnly: true, loginRole: 'admin' }
  },
  {
    path: '/login/individual',
    name: 'LoginIndividual',
    component: LoginView,
    meta: { guestOnly: true, loginRole: 'individual' }
  },
  {
    path: '/login/enterprise',
    name: 'LoginEnterprise',
    component: LoginView,
    meta: { guestOnly: true, loginRole: 'enterprise' }
  },
  { path: '/register', name: 'Register', component: RegisterView, meta: { guestOnly: true } },
  {
    path: '/admin/enterprise-users',
    name: 'AdminEnterpriseUsers',
    component: AdminEnterpriseUsersView,
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/edit-portrait',
    name: 'EditPortrait',
    component: EditPortrait,
    meta: { requiresAuth: true, roles: ['individual'] }
  },
  {
    path: '/style-lab',
    name: 'StyleLab',
    component: StyleLab,
    meta: { requiresAuth: true, roles: ['individual'] }
  },
  {
    path: '/protocols',
    name: 'ProtocolManagement',
    component: ProtocolManagement,
    meta: { requiresAuth: true, roles: ['individual', 'enterprise'] }
  },
  {
    path: '/discovery',
    name: 'DiscoverySquare',
    component: DiscoverySquare,
    meta: { requiresAuth: true, roles: ['enterprise'] }
  },
  {
    path: '/actor/:id',
    name: 'ActorProfile',
    component: ActorProfile,
    props: true,
    meta: { requiresAuth: true, roles: ['enterprise'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  await authStore.restoreSession()

  const isAuthed = authStore.isAuthenticated()
  const currentRole = authStore.state.user?.role

  if (to.meta.guestOnly && isAuthed) {
    return authStore.defaultRouteForRole(currentRole)
  }

  if (to.meta.requiresAuth && !isAuthed) {
    return { path: loginPathForRoute(to), query: { redirect: to.fullPath } }
  }

  if (to.meta.roles && isAuthed && !to.meta.roles.includes(currentRole)) {
    return authStore.defaultRouteForRole(currentRole)
  }

  return true
})

export default router
