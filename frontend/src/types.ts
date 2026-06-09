export interface Settings {
  keywords: string[]
  schedule_time: string
  min_posts: number
  auto_send: boolean
  dry_run: boolean
  delivery_channel: string
  group_ids: string[]
  ollama_model: string
  fixture_mode: boolean
  send_individual: boolean
}

export type CandidateStatus = 'pending' | 'approved' | 'rejected' | 'sent'

export interface Candidate {
  id: number
  run_id: number | null
  permalink: string
  author: string | null
  role_title: string | null
  company: string | null
  location: string | null
  seniority: string | null
  relevance_score: number
  summary: string | null
  raw_text: string | null
  status: CandidateStatus
  created_at: string
}

export type RunStatus = 'running' | 'finished' | 'error'

export interface Run {
  id: number
  started_at: string
  finished_at: string | null
  status: RunStatus
  posts_seen: number
  jobs_found: number
  sent_count: number
  error: string | null
}

export interface RunEvent {
  ts: string
  level: 'info' | 'warn' | 'error'
  message: string
}

export interface RunDetail extends Run {
  events: RunEvent[]
}

export interface Health {
  status: string
  ollama: boolean
  browser_session: boolean
  delivery: boolean
}

export interface SendResult {
  sent: number
  failed: number
  dry_run: boolean
  details: string[]
}

export interface SentItem {
  id: number
  channel: string
  group_id: string
  sent_at: string
  message: string
  role_title: string | null
  company: string | null
}
