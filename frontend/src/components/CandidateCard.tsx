import { useState } from 'react'
import { Check, ExternalLink, MapPin, X } from 'lucide-react'
import { cn, fmtRelative } from '../lib'
import type { Candidate } from '../types'

function SignalBar({ score }: { score: number }) {
  const total = 12
  const filled = Math.round(score * total)
  return (
    <div className="flex h-5 items-end gap-[3px]" title={`relevance ${(score * 100).toFixed(0)}%`}>
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className="w-[3px] rounded-sm transition-colors"
          style={{
            height: `${28 + (i / total) * 72}%`,
            background: i < filled ? 'var(--color-accent)' : 'var(--color-line2)',
            boxShadow: i < filled ? '0 0 5px rgba(242,169,59,0.4)' : 'none',
          }}
        />
      ))}
    </div>
  )
}

const STATUS_TONE: Record<string, string> = {
  approved: 'var(--color-ok)',
  rejected: 'var(--color-err)',
  sent: 'var(--color-accent)',
}

export function CandidateCard({
  c,
  index,
  onApprove,
  onReject,
}: {
  c: Candidate
  index: number
  onApprove: (id: number) => Promise<void>
  onReject: (id: number) => Promise<void>
}) {
  const [busy, setBusy] = useState<null | 'approve' | 'reject'>(null)

  async function act(kind: 'approve' | 'reject') {
    setBusy(kind)
    try {
      await (kind === 'approve' ? onApprove(c.id) : onReject(c.id))
    } finally {
      setBusy(null)
    }
  }

  const headline = c.role_title || 'Untitled role'
  const meta = [c.company, c.location].filter(Boolean) as string[]

  return (
    <article
      className="panel anim-fade-up flex flex-col p-5"
      style={{ animationDelay: `${Math.min(index, 12) * 45}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <SignalBar score={c.relevance_score} />
        <div className="flex items-center gap-2">
          <span className="mono text-[12px]" style={{ color: 'var(--color-accent)' }}>
            {(c.relevance_score * 100).toFixed(0)}%
          </span>
          {c.status !== 'pending' && (
            <span className="pill" style={{ color: STATUS_TONE[c.status] ?? 'var(--color-muted)' }}>
              {c.status}
            </span>
          )}
        </div>
      </div>

      <h3 className="mt-4 font-display text-[19px] leading-snug tracking-tight" style={{ fontWeight: 700 }}>
        {headline}
      </h3>

      {meta.length > 0 && (
        <div className="mono mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px]" style={{ color: 'var(--color-muted)' }}>
          {c.company && <span>{c.company}</span>}
          {c.company && c.location && <span style={{ color: 'var(--color-faint)' }}>·</span>}
          {c.location && (
            <span className="inline-flex items-center gap-1">
              <MapPin size={11} /> {c.location}
            </span>
          )}
        </div>
      )}

      {c.seniority && (
        <span className="pill mt-3 self-start" style={{ color: 'var(--color-muted)' }}>{c.seniority}</span>
      )}

      <p className="mt-3 text-[14px] leading-relaxed" style={{ color: 'var(--color-ink)' }}>
        {c.summary || c.raw_text?.slice(0, 180) || 'No summary.'}
      </p>

      <div className="mono mt-3 text-[11px]" style={{ color: 'var(--color-faint)' }}>
        {c.author || 'unknown'} · seen {fmtRelative(c.created_at)}
      </div>

      <div className="mt-4 flex items-center gap-2 border-t pt-4" style={{ borderColor: 'var(--color-line)' }}>
        <a
          href={c.permalink}
          target="_blank"
          rel="noreferrer"
          className="btn btn-ghost px-2"
          title="View original on LinkedIn"
        >
          <ExternalLink size={14} /> original
        </a>
        <div className="ml-auto flex items-center gap-2">
          <button
            className="btn"
            disabled={busy !== null || c.status === 'rejected'}
            onClick={() => act('reject')}
            style={{ color: 'var(--color-muted)' }}
          >
            <X size={14} /> {busy === 'reject' ? '…' : 'Reject'}
          </button>
          <button
            className={cn('btn', c.status === 'approved' ? '' : 'btn-accent')}
            disabled={busy !== null || c.status === 'approved'}
            onClick={() => act('approve')}
          >
            <Check size={14} /> {busy === 'approve' ? '…' : c.status === 'approved' ? 'Approved' : 'Approve'}
          </button>
        </div>
      </div>
    </article>
  )
}
