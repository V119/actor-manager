export async function fetchEnterpriseAgreementStatus(_token) {
  return {
    is_template_ready: true,
    is_signed: true,
    needs_resign: false,
    blocking_reason: null,
    message: '已在登录时同意企业协议，可正常访问演员广场。',
    template_version: 1,
    signed_template_version: 1,
    signed_at: null
  }
}

export function isEnterpriseAgreementBlockedStatus(_status) {
  return false
}

export async function ensureEnterpriseAgreementSigned({ token }) {
  const status = await fetchEnterpriseAgreementStatus(token)
  return { allowed: true, status }
}
