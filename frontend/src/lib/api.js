const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

function normalizeErrorDetail(detail) {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => normalizeErrorDetail(item))
      .filter(Boolean)
      .join('；')
  }
  if (typeof detail === 'object') {
    if (typeof detail.msg === 'string') {
      return detail.msg
    }
    if (detail.detail) {
      return normalizeErrorDetail(detail.detail)
    }
    return Object.values(detail)
      .map((item) => normalizeErrorDetail(item))
      .filter(Boolean)
      .join('；')
  }
  return String(detail)
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const payload = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    const detail = isJson && payload && Object.prototype.hasOwnProperty.call(payload, 'detail')
      ? payload.detail
      : `Request failed: ${response.status}`
    const error = new Error(normalizeErrorDetail(detail))
    if (detail && typeof detail === 'object') {
      error.detail = detail
    }
    throw error
  }

  return payload
}

export async function apiRequest(path, { method = 'GET', token = '', body, formData } = {}) {
  if (body !== undefined && formData !== undefined) {
    throw new Error('body 和 formData 不能同时传入')
  }

  const headers = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: formData !== undefined
      ? formData
      : body !== undefined
        ? JSON.stringify(body)
        : undefined
  })

  return parseResponse(response)
}
