import { useState } from 'react'
import { Play, Send } from 'lucide-react'
import { MetricTile } from '../components/ui'
import { api } from '../api'
import { fmtClock, fmtRelative, usePolling } from '../lib'
import type { Settings } from '../types'
import type { ViewKey } from '../components/Sidebar'

export function Dashboard({
  settings,
  goto,
}: {
  settings: Settings | null
  goto: (v: ViewKey) => void
}) {
  const runs = usePolling(api.listRuns, 3000)
  const pending = usePolling(() => api.listCandidates('pending'), 3000)
  const approved = usePolling(() => api.listCandidates('approved'), 3000)
  const [busy, setBusy] = useState<null | 'run' | 'send'>(null)
  const [notice, setNotice] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const lastRun = runs.data?.[0] ?? null
  const lastFinished = runs.data?.find((r) => r.status === 'finished') ?? null
  const running = !!runs.data?.find((r) => r.status === 'running')

  async function runNow() {
    setBusy('run')
    setNotice(null)
    try {
      await api.triggerRun()
      setNotice({ kind: 'ok', text: 'Run started — watch Activity for telemetry.' })
      runs.refresh()
    } catch (e) {
      setNotice({ kind: 'err', text: e instanceof Error ? e.message : String(e) })
    } finally {
      setBusy(null)
    }
  }

  async function sendApproved() {
    setBusy('send')
    setNotice(null)
    try {
      const r = await api.send()
      setNotice({
        kind: r.failed > 0 ? 'err' : 'ok',
        text: r.dry_run
          ? `Dry-run: would send to ${settings?.group_ids.length ?? 0} group(s). Toggle off dry-run in Settings to deliver.`
          : `Sent ${r.sent}, failed ${r.failed}.`,
      })
      approved.refresh()
    } catch (e) {
      setNotice({ kind: 'err', text: e instanceof Error ? e.message : String(e) })
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="mx-auto max-w-[1100px]">
      {/* Action bar */}
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn btn-accent" onClick={runNow} disabled={busy !== null || running}>
          <Play size={15} /> {running ? 'Scanning…' : busy === 'run' ? 'Starting…' : 'Run now'}
        </button>
        <button className="btn" onClick={sendApproved} disabled={busy !== null || (approved.data?.length ?? 0) === 0}>
          <Send size={15} /> {busy === 'send' ? 'Sending…' : `Send approved (${approved.data?.length ?? 0})`}
        </button>
        {notice && (
          <span
            className="mono text-[12px]"
            style={{ color: notice.kind === 'ok' ? 'var(--color-ok)' : 'var(--color-err)' }}
          >
            {notice.text}
          </span>
        )}
      </div>

      {/* Metrics */}
      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricTile
          label="Latest yield"
          value={lastFinished ? lastFinished.jobs_found : '—'}
          sub={lastFinished ? `from ${lastFinished.posts_seen} posts scanned` : 'no completed runs'}
          accent
          delay={0}
        />
        <MetricTile
          label="Pending review"
          value={pending.data?.length ?? '—'}
          sub="awaiting your call"
          delay={60}
        />
        <MetricTile
          label="Approved"
          value={approved.data?.length ?? '—'}
          sub="ready to send"
          delay={120}
        />
        <MetricTile
          label="Delivered (last run)"
          value={lastRun ? lastRun.sent_count : '—'}
          sub={settings?.dry_run ? 'dry-run active' : 'live delivery'}
          delay={180}
        />
      </div>

      {/* Last run + queue cta */}
      <div className="mt-4 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="panel anim-fade-up p-5" style={{ animationDelay: '220ms' }}>
          <div className="eyebrow">Last run</div>
          {lastRun ? (
            <div className="mt-4 space-y-3">
              <Row k="status" v={lastRun.status} tone={lastRun.status} />
              <Row k="started" v={fmtClock(lastRun.started_at)} />
              <Row k="finished" v={lastRun.finished_at ? fmtRelative(lastRun.finished_at) : 'in progress'} />
              <Row k="posts scanned" v={String(lastRun.posts_seen)} />
              <Row k="jobs found" v={String(lastRun.jobs_found)} />
              {lastRun.error && <Row k="notice" v={lastRun.error} tone="warn" />}
            </div>
          ) : (
            <p className="mono mt-4 text-[13px]" style={{ color: 'var(--color-muted)' }}>
              No runs yet. Hit “Run now” to scan your feed.
            </p>
          )}
        </div>

        <div className="panel anim-fade-up flex flex-col p-5" style={{ animationDelay: '280ms' }}>
          <div className="eyebrow">Triage</div>
          <div className="mono mt-3 leading-none" style={{ fontSize: 46, fontWeight: 200 }}>
            {pending.data?.length ?? 0}
          </div>
          <p className="mono mt-2 text-[12px]" style={{ color: 'var(--color-muted)' }}>
            candidate(s) waiting in the review queue.
          </p>
          <button className="btn mt-auto self-start" onClick={() => goto('review')}>
            Open review queue →
          </button>
        </div>
      </div>
    </div>
  )
}

function Row({ k, v, tone }: { k: string; v: string; tone?: string }) {
  const color =
    tone === 'error' || tone === 'warn'
      ? 'var(--color-err)'
      : tone === 'finished'
        ? 'var(--color-ok)'
        : tone === 'running'
          ? 'var(--color-accent)'
          : 'var(--color-ink)'
  return (
    <div className="flex items-baseline justify-between gap-4">
      <span className="eyebrow">{k}</span>
      <span className="mono text-right text-[13px]" style={{ color }}>{v}</span>
    </div>
  )
}
