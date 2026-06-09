import type {
  Candidate,
  CandidateStatus,
  Health,
  Run,
  RunDetail,
  SendResult,
  SentItem,
  Settings,
} from './types'

const BASE = '/api'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status} ${detail}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  health: () => req<Health>('/health'),

  getSettings: () => req<Settings>('/settings'),
  putSettings: (patch: Partial<Settings>) =>
    req<Settings>('/settings', { method: 'PUT', body: JSON.stringify(patch) }),

  triggerRun: () => req<{ run_id: number }>('/run', { method: 'POST' }),
  listRuns: () => req<Run[]>('/runs'),
  getRun: (id: number) => req<RunDetail>(`/runs/${id}`),

  listCandidates: (status?: CandidateStatus) =>
    req<Candidate[]>(`/candidates${status ? `?status=${status}` : ''}`),
  approve: (id: number) => req<Candidate>(`/candidates/${id}/approve`, { method: 'POST' }),
  reject: (id: number) => req<Candidate>(`/candidates/${id}/reject`, { method: 'POST' }),
  bulkApprove: (ids?: number[]) =>
    req<{ approved: number }>('/candidates/bulk-approve', {
      method: 'POST',
      body: JSON.stringify({ ids: ids ?? null }),
    }),

  send: () => req<SendResult>('/send', { method: 'POST' }),
  history: () => req<SentItem[]>('/history'),
  reauth: () => req<{ status: string; message: string }>('/linkedin/reauth', { method: 'POST' }),
}
