import { apiRequest } from './api'

export const ENTERPRISE_AGREEMENT_ROUTE = '/enterprise-agreement'

export async function fetchEnterpriseAgreementStatus(token) {
  return apiRequest('/enterprise/agreement/status', { token })
}

export function isEnterpriseAgreementBlockedStatus(status) {
  return Boolean(status && !status.is_signed)
}

export function isEnterpriseAgreementBlockingErrorMessage(message) {
  const normalized = String(message || '')
  return (
    normalized.includes('请先完成企业协议签署后再访问演员广场')
    || normalized.includes('协议内容已更新，请重新签署后再继续使用')
    || normalized.includes('协议模板尚未配置完成')
  )
}

export async function ensureEnterpriseAgreementSigned({ token, router, onBlocked }) {
  const status = await fetchEnterpriseAgreementStatus(token)
  if (!isEnterpriseAgreementBlockedStatus(status)) {
    return { allowed: true, status }
  }

  if (typeof onBlocked === 'function') {
    onBlocked(status.message || '请先完成企业协议签署后再访问演员广场。')
  }

  if (router) {
    await router.push(ENTERPRISE_AGREEMENT_ROUTE)
  }

  return { allowed: false, status }
}
