import { useCallback, useEffect, useRef, useState } from 'react'

export function cn(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(' ')
}

export const errMsg = (e: unknown): string => (e instanceof Error ? e.message : String(e))

const parseUtc = (iso: string): Date => new Date(iso.endsWith('Z') ? iso : iso + 'Z')

export function runStatusColor(status: string): string {
  if (status === 'finished') return 'var(--color-ok)'
  if (status === 'error') return 'var(--color-err)'
  if (status === 'running') return 'var(--color-accent)'
  return 'var(--color-ink)'
}

/** Poll a fetcher on an interval; returns latest data + manual refresh. */
export function usePolling<T>(fetcher: () => Promise<T>, intervalMs = 3000) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const ref = useRef(fetcher)
  ref.current = fetcher

  const refresh = useCallback(async () => {
    try {
      const d = await ref.current()
      setData(d)
      setError(null)
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    if (intervalMs <= 0) return
    const id = setInterval(refresh, intervalMs)
    return () => clearInterval(id)
  }, [intervalMs, refresh])

  return { data, error, loading, refresh }
}

const RELATIVE = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

export function fmtRelative(iso: string | null): string {
  if (!iso) return '—'
  const then = parseUtc(iso).getTime()
  const diff = then - Date.now()
  const abs = Math.abs(diff)
  const min = 60_000
  const hr = 60 * min
  const day = 24 * hr
  if (abs < min) return RELATIVE.format(Math.round(diff / 1000), 'second')
  if (abs < hr) return RELATIVE.format(Math.round(diff / min), 'minute')
  if (abs < day) return RELATIVE.format(Math.round(diff / hr), 'hour')
  return RELATIVE.format(Math.round(diff / day), 'day')
}

export function fmtClock(iso: string | null): string {
  if (!iso) return '—'
  return parseUtc(iso).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** ms until the next occurrence of an HH:MM local time. */
export function msUntilNext(scheduleTime: string): number {
  const [h, m] = scheduleTime.split(':').map(Number)
  if (Number.isNaN(h) || Number.isNaN(m)) return 0
  const now = new Date()
  const next = new Date()
  next.setHours(h, m, 0, 0)
  if (next.getTime() <= now.getTime()) next.setDate(next.getDate() + 1)
  return next.getTime() - now.getTime()
}

export function fmtDuration(ms: number): string {
  if (ms <= 0) return '00:00:00'
  const s = Math.floor(ms / 1000)
  const hh = String(Math.floor(s / 3600)).padStart(2, '0')
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0')
  const ss = String(s % 60).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

/** A ticking clock that re-renders every `everyMs`. */
export function useTick(everyMs = 1000): number {
  const [, setN] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setN((n) => n + 1), everyMs)
    return () => clearInterval(id)
  }, [everyMs])
  return Date.now()
}
