import { apiRequest } from './api'

export const ENTERPRISE_AGREEMENT_ROUTE = '/enterprise-agreement'
export const ENTERPRISE_DISCOVERY_BLOCKED_NOTICE = '当前企业账号尚未完成协议签署，暂时不能进入演员发布广场。请先完成下方协议签署，签署后即可继续浏览演员信息。'
export const ENTERPRISE_ACTOR_DETAIL_BLOCKED_NOTICE = '当前企业账号尚未完成协议签署，暂时不能查看演员详情。请先完成下方协议签署，签署后即可继续查看演员资料。'

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

export function buildEnterpriseAgreementRoute(message = '') {
  return message
    ? { path: ENTERPRISE_AGREEMENT_ROUTE, query: { notice: message } }
    : { path: ENTERPRISE_AGREEMENT_ROUTE }
}

export async function ensureEnterpriseAgreementSigned({ token, router, onBlocked, blockedNotice = '' }) {
  const status = await fetchEnterpriseAgreementStatus(token)
  if (!isEnterpriseAgreementBlockedStatus(status)) {
    return { allowed: true, status }
  }

  const nextMessage = blockedNotice || status.message || '请先完成企业协议签署后再访问演员广场。'

  if (typeof onBlocked === 'function') {
    onBlocked(nextMessage)
  }

  if (router) {
    await router.push(buildEnterpriseAgreementRoute(nextMessage))
  }

  return { allowed: false, status }
}
