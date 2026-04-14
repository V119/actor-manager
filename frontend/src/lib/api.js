const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const payload = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    const detail = isJson && payload && payload.detail
      ? payload.detail
      : `Request failed: ${response.status}`
    throw new Error(detail)
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
