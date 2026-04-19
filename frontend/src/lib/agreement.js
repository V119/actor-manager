export async function fetchActorAgreementStatus(_token) {
  return {
    is_template_ready: true,
    is_signed: true,
    needs_resign: false,
    blocking_reason: null,
    message: '已在注册时同意协议，可正常发布内容。',
    template_version: 1,
    signed_template_version: 1,
    signed_at: null
  }
}

export function isAgreementBlockedStatus(_status) {
  return false
}

export async function ensureAgreementSignedForPublish({ token }) {
  const status = await fetchActorAgreementStatus(token)
  return { allowed: true, status }
}
