import { apiRequest } from './api'

export const ACTOR_AGREEMENT_ROUTE = '/actor-agreement'

export async function fetchActorAgreementStatus(token) {
  return apiRequest('/actor/agreement/status', { token })
}

export function isAgreementBlockedStatus(status) {
  return Boolean(status && !status.is_signed)
}

export function isAgreementBlockingErrorMessage(message) {
  const normalized = String(message || '')
  return (
    normalized.includes('请先完成协议签署后再发布内容')
    || normalized.includes('协议内容已更新，请重新签署后再发布内容')
    || normalized.includes('协议模板尚未配置完成')
  )
}

export async function ensureAgreementSignedForPublish({ token, router, onBlocked }) {
  const status = await fetchActorAgreementStatus(token)
  if (!isAgreementBlockedStatus(status)) {
    return { allowed: true, status }
  }

  if (typeof onBlocked === 'function') {
    onBlocked(status.message || '请先完成协议签署后再发布内容。')
  }

  if (router) {
    await router.push(ACTOR_AGREEMENT_ROUTE)
  }

  return { allowed: false, status }
}
