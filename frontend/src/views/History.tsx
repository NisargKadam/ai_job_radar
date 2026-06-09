import { Radio, SendHorizontal } from 'lucide-react'
import { api } from '../api'
import { fmtClock, usePolling } from '../lib'

export function History() {
  const sent = usePolling(api.history, 5000)
  const rows = sent.data ?? []

  return (
    <div className="mx-auto max-w-[1000px]">
      <div className="mono text-[13px]" style={{ color: 'var(--color-muted)' }}>
        <span style={{ color: 'var(--color-accent)' }}>{rows.length}</span> delivered transmission(s)
      </div>

      {rows.length === 0 ? (
        <div className="panel mt-5 flex flex-col items-center justify-center px-6 py-20 text-center">
          <Radio size={34} style={{ color: 'var(--color-faint)' }} />
          <p className="font-display mt-4 text-[17px]" style={{ fontWeight: 600 }}>No transmissions yet</p>
          <p className="mono mt-2 max-w-md text-[12px]" style={{ color: 'var(--color-muted)' }}>
            Approved jobs you send will be logged here with channel, group, and timestamp.
          </p>
        </div>
      ) : (
        <div className="panel mt-5 overflow-hidden">
          <div
            className="eyebrow grid grid-cols-[120px_1fr_140px_120px] gap-3 border-b px-5 py-3"
            style={{ borderColor: 'var(--color-line)' }}
          >
            <span>when</span>
            <span>job</span>
            <span>group</span>
            <span>channel</span>
          </div>
          {rows.map((r, i) => (
            <div
              key={r.id}
              className="grid grid-cols-[120px_1fr_140px_120px] items-center gap-3 border-b px-5 py-3.5 text-[13px] last:border-0"
              style={{ borderColor: 'var(--color-line)', background: i % 2 ? 'rgba(255,255,255,0.012)' : 'transparent' }}
            >
              <span className="mono text-[11px]" style={{ color: 'var(--color-muted)' }}>{fmtClock(r.sent_at)}</span>
              <span className="truncate">
                <span style={{ fontWeight: 600 }}>{r.role_title ?? 'Digest'}</span>
                {r.company && <span className="mono ml-2 text-[11px]" style={{ color: 'var(--color-muted)' }}>{r.company}</span>}
              </span>
              <span className="mono truncate text-[11px]" style={{ color: 'var(--color-muted)' }}>{r.group_id}</span>
              <span className="pill self-start" style={{ color: 'var(--color-accent)' }}>
                <SendHorizontal size={11} /> {r.channel}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
