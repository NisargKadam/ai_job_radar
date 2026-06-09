import { useMemo } from 'react'
import { RadarMark } from './RadarMark'
import { StatusPill } from './ui'
import { fmtDuration, msUntilNext, useTick } from '../lib'
import type { Health, Run, Settings } from '../types'
import type { ViewKey } from './Sidebar'

const TITLES: Record<ViewKey, { title: string; eyebrow: string }> = {
  dashboard: { title: 'Dashboard', eyebrow: 'Mission overview' },
  review: { title: 'Review Queue', eyebrow: 'Triage today’s signal' },
  history: { title: 'History', eyebrow: 'Delivered transmissions' },
  activity: { title: 'Activity', eyebrow: 'Run telemetry' },
  settings: { title: 'Settings', eyebrow: 'Console configuration' },
}

export function TopBar({
  view,
  health,
  activeRun,
  settings,
}: {
  view: ViewKey
  health: Health | null
  activeRun: Run | null
  settings: Settings | null
}) {
  useTick(1000)
  const { title, eyebrow } = TITLES[view]
  const countdown = useMemo(
    () => (settings ? fmtDuration(msUntilNext(settings.schedule_time)) : '—'),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [settings, Date.now()],
  )

  const running = !!activeRun

  return (
    <header
      className="flex items-center gap-5 border-b px-7 py-4"
      style={{ borderColor: 'var(--color-line)', background: 'rgba(9,12,13,0.5)', backdropFilter: 'blur(6px)' }}
    >
      <div className="min-w-0">
        <div className="eyebrow">{eyebrow}</div>
        <h1 className="font-display text-[22px] leading-tight tracking-tight" style={{ fontWeight: 700 }}>
          {title}
        </h1>
      </div>

      <div className="ml-auto flex items-center gap-2.5">
        <HealthDot label="ollama" up={health?.ollama} />
        <HealthDot label="session" up={health?.browser_session} />
        <HealthDot label="delivery" up={health?.delivery} />

        <div className="mx-1 h-8 w-px" style={{ background: 'var(--color-line)' }} />

        <div className="flex items-center gap-2 rounded-[10px] border px-3 py-1.5"
             style={{ borderColor: 'var(--color-line2)', background: 'var(--color-panel)' }}>
          <RadarMark size={20} active={running} />
          {running ? (
            <StatusPill tone="warn" label="scanning" pulse />
          ) : (
            <StatusPill tone="idle" label="idle" />
          )}
        </div>

        <div className="hidden items-center gap-2 rounded-[10px] border px-3 py-1.5 lg:flex"
             style={{ borderColor: 'var(--color-line2)', background: 'var(--color-panel)' }}>
          <span className="eyebrow">next run</span>
          <span className="mono text-[13px]" style={{ color: 'var(--color-accent)' }}>{countdown}</span>
        </div>
      </div>
    </header>
  )
}

function HealthDot({ label, up }: { label: string; up: boolean | undefined }) {
  const color = up === undefined ? 'var(--color-faint)' : up ? 'var(--color-ok)' : 'var(--color-err)'
  return (
    <div className="flex items-center gap-1.5" title={`${label}: ${up === undefined ? 'unknown' : up ? 'ok' : 'down'}`}>
      <span className="dot" style={{ background: color }} />
      <span className="mono text-[10px] uppercase tracking-wider" style={{ color: 'var(--color-faint)' }}>{label}</span>
    </div>
  )
}
