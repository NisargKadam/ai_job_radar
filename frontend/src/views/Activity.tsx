import { useEffect, useState } from 'react'
import { api } from '../api'
import { cn, fmtClock, fmtRelative, usePolling } from '../lib'

const LEVEL_COLOR: Record<string, string> = {
  info: 'var(--color-muted)',
  warn: 'var(--color-accent)',
  error: 'var(--color-err)',
}

export function Activity() {
  const runs = usePolling(api.listRuns, 3000)
  const [selected, setSelected] = useState<number | null>(null)

  useEffect(() => {
    if (selected === null && runs.data && runs.data.length > 0) {
      setSelected(runs.data[0].id)
    }
  }, [runs.data, selected])

  const detail = usePolling(
    () => (selected ? api.getRun(selected) : Promise.resolve(null)),
    2000,
  )
  const run = detail.data

  // Fetch immediately when the selected run changes (don't wait for the next tick).
  const refreshDetail = detail.refresh
  useEffect(() => {
    if (selected) refreshDetail()
  }, [selected, refreshDetail])

  return (
    <div className="mx-auto grid max-w-[1100px] gap-4 lg:grid-cols-[260px_1fr]">
      {/* run list */}
      <div className="panel max-h-[70vh] overflow-auto p-2">
        {(runs.data ?? []).map((r) => (
          <button
            key={r.id}
            onClick={() => setSelected(r.id)}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left transition-colors"
            style={{ background: selected === r.id ? 'var(--color-panel2)' : 'transparent' }}
          >
            <span
              className={cn('dot', r.status === 'running' && 'pulsing')}
              style={{
                background:
                  r.status === 'finished' ? 'var(--color-ok)' : r.status === 'error' ? 'var(--color-err)' : 'var(--color-accent)',
              }}
            />
            <span className="mono text-[12px]">run #{r.id}</span>
            <span className="mono ml-auto text-[10px]" style={{ color: 'var(--color-faint)' }}>
              {fmtRelative(r.started_at)}
            </span>
          </button>
        ))}
        {(runs.data?.length ?? 0) === 0 && (
          <p className="mono p-3 text-[12px]" style={{ color: 'var(--color-faint)' }}>No runs yet.</p>
        )}
      </div>

      {/* log */}
      <div className="panel flex max-h-[70vh] flex-col overflow-hidden">
        <div className="flex items-center gap-3 border-b px-5 py-3" style={{ borderColor: 'var(--color-line)' }}>
          <span className="eyebrow">{run ? `run #${run.id} · ${run.status}` : 'no run selected'}</span>
          {run && (
            <span className="mono ml-auto text-[11px]" style={{ color: 'var(--color-muted)' }}>
              {run.posts_seen} scanned · {run.jobs_found} jobs · {fmtClock(run.started_at)}
            </span>
          )}
        </div>
        <div className="flex-1 overflow-auto px-5 py-4" style={{ background: 'rgba(0,0,0,0.25)' }}>
          {run && run.events.length > 0 ? (
            run.events.map((e, i) => (
              <div key={i} className="mono flex gap-3 py-0.5 text-[12px] leading-relaxed">
                <span style={{ color: 'var(--color-faint)' }}>{fmtClock(e.ts).split(', ')[1] ?? fmtClock(e.ts)}</span>
                <span style={{ color: LEVEL_COLOR[e.level] ?? 'var(--color-muted)' }}>
                  [{e.level}]
                </span>
                <span style={{ color: 'var(--color-ink)' }}>{e.message}</span>
              </div>
            ))
          ) : (
            <p className="mono text-[12px]" style={{ color: 'var(--color-faint)' }}>
              {run ? 'Waiting for telemetry…' : 'Select a run to view its log.'}
            </p>
          )}
          {run?.error && (
            <div className="mono mt-3 rounded p-2 text-[12px]" style={{ background: 'rgba(224,101,95,0.1)', color: 'var(--color-err)' }}>
              {run.error}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
