import type { ReactNode } from 'react'
import { cn } from '../lib'

type Tone = 'ok' | 'warn' | 'err' | 'idle'

const TONE_COLOR: Record<Tone, string> = {
  ok: 'var(--color-ok)',
  warn: 'var(--color-accent)',
  err: 'var(--color-err)',
  idle: 'var(--color-faint)',
}

export function StatusPill({
  tone,
  label,
  pulse = false,
}: {
  tone: Tone
  label: string
  pulse?: boolean
}) {
  return (
    <span className="pill" style={{ color: TONE_COLOR[tone], borderColor: 'var(--color-line2)' }}>
      <span className={cn('dot', pulse && 'pulsing')} style={{ background: TONE_COLOR[tone] }} />
      {label}
    </span>
  )
}

export function Toggle({
  checked,
  onChange,
  disabled = false,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className="relative h-[26px] w-[46px] rounded-full border transition-colors disabled:opacity-40"
      style={{
        background: checked ? 'rgba(242,169,59,0.22)' : 'var(--color-bg2)',
        borderColor: checked ? 'var(--color-accentdim)' : 'var(--color-line2)',
      }}
    >
      <span
        className="absolute top-1/2 h-[18px] w-[18px] -translate-y-1/2 rounded-full transition-all"
        style={{
          left: checked ? '23px' : '3px',
          background: checked ? 'var(--color-accent)' : 'var(--color-faint)',
          boxShadow: checked ? '0 0 10px rgba(242,169,59,0.6)' : 'none',
        }}
      />
    </button>
  )
}

export function MetricTile({
  label,
  value,
  sub,
  accent = false,
  delay = 0,
}: {
  label: string
  value: ReactNode
  sub?: ReactNode
  accent?: boolean
  delay?: number
}) {
  return (
    <div className="panel anim-fade-up p-5" style={{ animationDelay: `${delay}ms` }}>
      <div className="eyebrow">{label}</div>
      <div
        className="mono mt-3 leading-none"
        style={{ fontSize: 38, color: accent ? 'var(--color-accent)' : 'var(--color-ink)', fontWeight: 200 }}
      >
        {value}
      </div>
      {sub && <div className="mono mt-2 text-[11px]" style={{ color: 'var(--color-muted)' }}>{sub}</div>}
    </div>
  )
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <div className="eyebrow mb-2" style={{ color: 'var(--color-muted)' }}>{label}</div>
      {children}
      {hint && <div className="mono mt-1.5 text-[11px]" style={{ color: 'var(--color-faint)' }}>{hint}</div>}
    </label>
  )
}
