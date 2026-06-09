import { Activity, ClipboardCheck, Gauge, History, SlidersHorizontal } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { RadarMark } from './RadarMark'
import { cn } from '../lib'
import type { Settings } from '../types'

export type ViewKey = 'dashboard' | 'review' | 'history' | 'settings' | 'activity'

const NAV: { key: ViewKey; label: string; icon: LucideIcon }[] = [
  { key: 'dashboard', label: 'Dashboard', icon: Gauge },
  { key: 'review', label: 'Review Queue', icon: ClipboardCheck },
  { key: 'history', label: 'History', icon: History },
  { key: 'activity', label: 'Activity', icon: Activity },
  { key: 'settings', label: 'Settings', icon: SlidersHorizontal },
]

export function Sidebar({
  view,
  setView,
  pendingCount,
  running,
  settings,
}: {
  view: ViewKey
  setView: (v: ViewKey) => void
  pendingCount: number
  running: boolean
  settings: Settings | null
}) {
  return (
    <aside
      className="flex w-[248px] flex-none flex-col border-r"
      style={{ borderColor: 'var(--color-line)', background: 'rgba(9,12,13,0.6)' }}
    >
      <div className="flex items-center gap-3 px-6 py-6">
        <RadarMark size={38} active={running} />
        <div>
          <div className="font-display text-[17px] leading-none tracking-tight" style={{ fontWeight: 700 }}>
            Job Radar
          </div>
          <div className="eyebrow mt-1.5">Operator&nbsp;Console</div>
        </div>
      </div>

      <nav className="mt-2 flex flex-col gap-1 px-3">
        {NAV.map(({ key, label, icon: Icon }) => {
          const active = view === key
          return (
            <button
              key={key}
              onClick={() => setView(key)}
              className={cn(
                'group relative flex items-center gap-3 rounded-[10px] px-3 py-2.5 text-left transition-colors',
              )}
              style={{
                background: active ? 'var(--color-panel2)' : 'transparent',
                color: active ? 'var(--color-ink)' : 'var(--color-muted)',
              }}
            >
              {active && (
                <span
                  className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r"
                  style={{ background: 'var(--color-accent)' }}
                />
              )}
              <Icon size={17} style={{ color: active ? 'var(--color-accent)' : 'currentColor' }} />
              <span className="text-[14px]" style={{ fontWeight: active ? 600 : 400 }}>
                {label}
              </span>
              {key === 'review' && pendingCount > 0 && (
                <span
                  className="mono ml-auto rounded-full px-1.5 py-0.5 text-[10px]"
                  style={{ background: 'rgba(242,169,59,0.18)', color: 'var(--color-accent)' }}
                >
                  {pendingCount}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      <div className="mt-auto px-5 py-5">
        <div className="flex flex-wrap gap-1.5">
          {settings?.dry_run && (
            <span className="pill" style={{ color: 'var(--color-accent)' }}>dry-run</span>
          )}
          {settings?.auto_send && (
            <span className="pill" style={{ color: 'var(--color-err)' }}>auto-send</span>
          )}
          {settings?.fixture_mode && (
            <span className="pill" style={{ color: 'var(--color-muted)' }}>fixture</span>
          )}
        </div>
        <div className="mono mt-3 text-[10px]" style={{ color: 'var(--color-faint)' }}>
          {settings ? `model · ${settings.ollama_model}` : 'connecting…'}
        </div>
      </div>
    </aside>
  )
}
