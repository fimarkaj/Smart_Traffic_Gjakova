import client, { API_URL } from './client'

// ── Auth ──────────────────────────────────────────────
export const login = async (username, password) => {
  const form = new URLSearchParams({ username, password })
  const { data } = await client.post('/api/auth/token', form)
  return data
}
export const getMe = () => client.get('/api/auth/me').then(r => r.data)

// ── Analytics ────────────────────────────────────────
export const getCounts    = (p)   => client.get('/api/analytics/counts',  { params: p }).then(r => r.data)
export const getTotals    = (p)   => client.get('/api/analytics/totals',  { params: p }).then(r => r.data)
export const getSession   = ()    => client.get('/api/analytics/session'             ).then(r => r.data)
export const getSummary   = (p)   => client.get('/api/analytics/summary', { params: p }).then(r => r.data)
export const buildSummary = (day) => client.post('/api/analytics/summary/build', null, { params: { day } }).then(r => r.data)
export const exportCSV    = (p)   => `${API_URL}/api/analytics/export/csv?${new URLSearchParams(p)}`

// ── Alerts ────────────────────────────────────────────
export const getAlerts    = ()         => client.get('/api/alerts/').then(r => r.data)
export const createAlert  = (rule)     => client.post('/api/alerts/', rule).then(r => r.data)
export const updateAlert  = (id, rule) => client.put(`/api/alerts/${id}`, rule).then(r => r.data)
export const deleteAlert  = (id)       => client.delete(`/api/alerts/${id}`).then(r => r.data)

// ── Clips ─────────────────────────────────────────────
export const getClips   = ()         => client.get('/api/clips/').then(r => r.data)
export const deleteClip = (filename) => client.delete(`/api/clips/${filename}`).then(r => r.data)
export const getClipUrl = (filename) => `${API_URL}/api/clips/${filename}`

// ── Config ────────────────────────────────────────────
export const getLines       = ()      => client.get('/api/config/lines').then(r => r.data)
export const saveLines      = (lines) => client.put('/api/config/lines', lines).then(r => r.data)
export const getThresholds  = ()      => client.get('/api/config/thresholds').then(r => r.data)
export const saveThresholds = (t)     => client.put('/api/config/thresholds', t).then(r => r.data)
export const getModelStatus = ()      => client.get('/api/model/status').then(r => r.data)
export const swapModel      = (file)  => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/api/model/swap', form).then(r => r.data)
}

// ── Forecast ──────────────────────────────────────────
export const getForecastLive   = () => client.get('/api/forecast/live').then(r => r.data)
export const getForecastStatus = () => client.get('/api/forecast/status').then(r => r.data)
export const getForecastHistory = () => client.get('/api/forecast/history').then(r => r.data)

export const uploadForecastModel = (file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/api/forecast/model/import', form).then(r => r.data)
}
export const getForecastModelMeta = () => client.get('/api/forecast/model/meta').then(r => r.data)
