import { cn } from '../lib'

export function RadarMark({ size = 34, active = false }: { size?: number; active?: boolean }) {
  return (
    <div
      className="relative overflow-hidden rounded-full"
      style={{ width: size, height: size }}
      aria-hidden
    >
      {/* sweeping beam (only while a run is active) */}
      {active && (
        <div
          className="sweeping absolute inset-0"
          style={{
            background:
              'conic-gradient(from 0deg, transparent 0deg, rgba(242,169,59,0.5) 34deg, transparent 70deg)',
          }}
        />
      )}
      {/* rings + crosshair */}
      <svg viewBox="0 0 100 100" className="absolute inset-0" width={size} height={size}>
        <circle cx="50" cy="50" r="46" fill="none" stroke="var(--color-line2)" strokeWidth="1.5" />
        <circle cx="50" cy="50" r="29" fill="none" stroke="var(--color-line)" strokeWidth="1.5" />
        <circle cx="50" cy="50" r="13" fill="none" stroke="var(--color-line)" strokeWidth="1.5" />
        <line x1="50" y1="3" x2="50" y2="97" stroke="var(--color-line)" strokeWidth="1" />
        <line x1="3" y1="50" x2="97" y2="50" stroke="var(--color-line)" strokeWidth="1" />
      </svg>
      <div
        className={cn('dot absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2', active && 'pulsing')}
        style={{ background: 'var(--color-accent)', boxShadow: '0 0 8px var(--color-accent)' }}
      />
    </div>
  )
}
