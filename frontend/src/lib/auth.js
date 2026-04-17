import { reactive } from 'vue'
import { apiRequest } from './api'

const TOKEN_KEY = 'actor_manager_token'

const state = reactive({
  token: localStorage.getItem(TOKEN_KEY) || '',
  user: null,
  restored: false
})

function persistToken(token) {
  state.token = token
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

function clearSession() {
  persistToken('')
  state.user = null
}

async function restoreSession({ force = false } = {}) {
  if (!force && state.restored) {
    return
  }
  if (!state.token) {
    state.user = null
    state.restored = true
    return
  }

  try {
    state.user = await apiRequest('/auth/me', { token: state.token })
  } catch (_error) {
    clearSession()
  } finally {
    state.restored = true
  }
}

function setAuthFromResponse(payload) {
  persistToken(payload.token)
  state.user = payload.user
  state.restored = true
}

async function login(account, password) {
  const payload = await apiRequest('/auth/login', {
    method: 'POST',
    body: { username: account, password }
  })
  setAuthFromResponse(payload)
  return payload.user
}

async function adminLogin(username, password) {
  const payload = await apiRequest('/admin/auth/login', {
    method: 'POST',
    body: { username, password }
  })
  setAuthFromResponse(payload)
  return payload.user
}

async function register({ phone, password, confirm_password }) {
  const payload = await apiRequest('/auth/register', {
    method: 'POST',
    body: { phone, password, confirm_password }
  })
  setAuthFromResponse(payload)
  return payload.user
}

async function logout() {
  if (state.token) {
    try {
      await apiRequest('/auth/logout', {
        method: 'POST',
        token: state.token
      })
    } catch (_error) {
      // Ignore logout errors; local cleanup still happens.
    }
  }
  clearSession()
}

function isAuthenticated() {
  return Boolean(state.token && state.user)
}

function defaultRouteForRole(role) {
  if (role === 'admin') {
    return '/admin/enterprise-users'
  }
  return role === 'enterprise' ? '/enterprise-basic-info' : '/edit-portrait'
}

export const authStore = {
  state,
  restoreSession,
  login,
  adminLogin,
  register,
  logout,
  isAuthenticated,
  defaultRouteForRole
}
