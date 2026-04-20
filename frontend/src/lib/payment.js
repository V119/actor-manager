import { apiRequest } from './api'

export async function fetchEnterpriseCart({ token }) {
  return apiRequest('/enterprise/cart', { token })
}

export async function addEnterpriseCartItem({ token, actorId }) {
  return apiRequest('/enterprise/cart', {
    method: 'POST',
    token,
    body: { actor_id: actorId }
  })
}

export async function removeEnterpriseCartItem({ token, actorId }) {
  return apiRequest('/enterprise/cart', {
    method: 'DELETE',
    token,
    body: { actor_id: actorId }
  })
}

export async function previewEnterpriseOrder({ token, actorIds = null }) {
  return apiRequest('/enterprise/orders/preview', {
    method: 'POST',
    token,
    body: { actor_ids: actorIds }
  })
}

export async function createEnterpriseOrder({ token, actorIds = null }) {
  return apiRequest('/enterprise/orders', {
    method: 'POST',
    token,
    body: { actor_ids: actorIds }
  })
}

export async function listEnterpriseOrders({ token, limit = 50 } = {}) {
  return apiRequest(`/enterprise/orders?limit=${encodeURIComponent(limit)}`, { token })
}

export async function getEnterpriseOrder({ token, orderNo }) {
  return apiRequest(`/enterprise/orders/${encodeURIComponent(orderNo)}`, { token })
}

export async function payEnterpriseOrder({ token, orderNo, channel }) {
  return apiRequest(`/enterprise/orders/${encodeURIComponent(orderNo)}/pay`, {
    method: 'POST',
    token,
    body: { channel }
  })
}

export async function acceptEnterpriseOrder({ token, orderNo }) {
  return apiRequest(`/enterprise/orders/${encodeURIComponent(orderNo)}/accept`, {
    method: 'POST',
    token
  })
}

export async function fetchAdminPaymentConfig({ token }) {
  return apiRequest('/admin/payments/config', { token })
}

export async function updateAdminPaymentConfig({ token, payload }) {
  return apiRequest('/admin/payments/config', {
    method: 'PUT',
    token,
    body: payload
  })
}

export async function listAdminPaymentOrders({ token, limit = 100 } = {}) {
  return apiRequest(`/admin/payments/orders?limit=${encodeURIComponent(limit)}`, { token })
}

export async function getAdminPaymentOrder({ token, orderNo }) {
  return apiRequest(`/admin/payments/orders/${encodeURIComponent(orderNo)}`, { token })
}

export async function listAdminRefunds({ token, limit = 100 } = {}) {
  return apiRequest(`/admin/payments/refunds?limit=${encodeURIComponent(limit)}`, { token })
}

export async function createAdminRefund({ token, payload }) {
  return apiRequest('/admin/payments/refunds', {
    method: 'POST',
    token,
    body: payload
  })
}

export async function approveAdminRefund({ token, outRefundNo }) {
  return apiRequest('/admin/payments/refunds/approve', {
    method: 'POST',
    token,
    body: { out_refund_no: outRefundNo }
  })
}

export async function runAdminDueSettlements({ token, limit = 200 }) {
  return apiRequest('/admin/payments/settlements/run', {
    method: 'POST',
    token,
    body: { limit }
  })
}

export async function listAdminWithdrawals({ token, limit = 100, status = '' } = {}) {
  const params = new URLSearchParams()
  params.set('limit', String(limit))
  if (status) params.set('status', String(status))
  return apiRequest(`/admin/payments/withdrawals?${params.toString()}`, { token })
}

export async function getAdminWithdrawal({ token, outWithdrawNo }) {
  return apiRequest(`/admin/payments/withdrawals/${encodeURIComponent(outWithdrawNo)}`, { token })
}

export async function reviewAdminWithdrawal({ token, payload }) {
  return apiRequest('/admin/payments/withdrawals/review', {
    method: 'POST',
    token,
    body: payload
  })
}

export async function fetchActorWalletSummary({ token }) {
  return apiRequest('/actors/me/wallet', { token })
}

export async function listActorWithdrawals({ token, limit = 50 } = {}) {
  return apiRequest(`/actors/me/withdrawals?limit=${encodeURIComponent(limit)}`, { token })
}

export async function createActorWithdrawal({ token, payload }) {
  return apiRequest('/actors/me/withdrawals', {
    method: 'POST',
    token,
    body: payload
  })
}
