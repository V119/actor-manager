import { createRouter, createWebHistory } from 'vue-router'
import EditPortrait from '../views/EditPortrait.vue'
import ActorBasicInfo from '../views/ActorBasicInfo.vue'
import ActorAgreementSign from '../views/ActorAgreementSign.vue'
import EnterpriseBasicInfo from '../views/EnterpriseBasicInfo.vue'
import EnterpriseAgreementSign from '../views/EnterpriseAgreementSign.vue'
import StyleLab from '../views/StyleLab.vue'
import DiscoverySquare from '../views/DiscoverySquare.vue'
import ActorProfile from '../views/ActorProfile.vue'
import EnterpriseSignedActors from '../views/EnterpriseSignedActors.vue'
import ActorSignedEnterprises from '../views/ActorSignedEnterprises.vue'
import ActorSignedEnterpriseDetail from '../views/ActorSignedEnterpriseDetail.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'
import AdminEnterpriseUsersView from '../views/AdminEnterpriseUsersView.vue'
import AdminAgreementTemplateView from '../views/AdminAgreementTemplateView.vue'
import AdminEnterpriseAgreementTemplateView from '../views/AdminEnterpriseAgreementTemplateView.vue'
import AdminPortraitGuidanceView from '../views/AdminPortraitGuidanceView.vue'
import { authStore } from '../lib/auth'

const PUBLIC_LOGIN_PATHS = new Set([
  '/login/individual',
  '/login/enterprise',
  '/admin/login',
  '/register'
])

function loginPathForRoute(to) {
  if (typeof to?.path === 'string' && to.path.startsWith('/admin')) {
    return '/admin/login'
  }
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
    path: '/admin/portrait-guidance',
    name: 'AdminPortraitGuidance',
    component: AdminPortraitGuidanceView,
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/agreement-template',
    name: 'AdminAgreementTemplate',
    component: AdminAgreementTemplateView,
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/enterprise-agreement-template',
    name: 'AdminEnterpriseAgreementTemplate',
    component: AdminEnterpriseAgreementTemplateView,
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/actor-basic-info',
    name: 'ActorBasicInfo',
    component: ActorBasicInfo,
    meta: { requiresAuth: true, roles: ['individual'] }
  },
  {
    path: '/actor-agreement',
    name: 'ActorAgreementSign',
    component: ActorAgreementSign,
    meta: { requiresAuth: true, roles: ['individual'] }
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
    path: '/enterprise-basic-info',
    name: 'EnterpriseBasicInfo',
    component: EnterpriseBasicInfo,
    meta: { requiresAuth: true, roles: ['enterprise'] }
  },
  {
    path: '/enterprise-agreement',
    name: 'EnterpriseAgreementSign',
    component: EnterpriseAgreementSign,
    meta: { requiresAuth: true, roles: ['enterprise'] }
  },
  {
    path: '/discovery',
    name: 'DiscoverySquare',
    component: DiscoverySquare,
    meta: { requiresAuth: true, roles: ['enterprise'] }
  },
  {
    path: '/enterprise-signed-actors',
    name: 'EnterpriseSignedActors',
    component: EnterpriseSignedActors,
    meta: { requiresAuth: true, roles: ['enterprise'] }
  },
  {
    path: '/actor/:id',
    name: 'ActorProfile',
    component: ActorProfile,
    props: true,
    meta: { requiresAuth: true, roles: ['enterprise'] }
  },
  {
    path: '/actor-signed-enterprises',
    name: 'ActorSignedEnterprises',
    component: ActorSignedEnterprises,
    meta: { requiresAuth: true, roles: ['individual'] }
  },
  {
    path: '/actor-signed-enterprises/:enterpriseUserId',
    name: 'ActorSignedEnterpriseDetail',
    component: ActorSignedEnterpriseDetail,
    props: true,
    meta: { requiresAuth: true, roles: ['individual'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  await authStore.restoreSession({ force: true })

  const isAuthed = authStore.isAuthenticated()
  const currentRole = authStore.state.user?.role
  const isPublicLoginPage = PUBLIC_LOGIN_PATHS.has(to.path)

  if (!isAuthed && !isPublicLoginPage) {
    return { path: loginPathForRoute(to), query: { redirect: to.fullPath } }
  }

  if (to.meta.guestOnly && isAuthed) {
    return authStore.defaultRouteForRole(currentRole)
  }

  if (to.meta.roles && isAuthed && !to.meta.roles.includes(currentRole)) {
    return authStore.defaultRouteForRole(currentRole)
  }

  return true
})

export default router
