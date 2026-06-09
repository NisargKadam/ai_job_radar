import { TriangleAlert } from 'lucide-react'

export function Banner() {
  return (
    <div
      className="flex items-center gap-2.5 border-b px-7 py-2"
      style={{ borderColor: 'var(--color-line)', background: 'rgba(242,169,59,0.06)' }}
    >
      <TriangleAlert size={14} style={{ color: 'var(--color-accent)' }} />
      <p className="mono text-[11px]" style={{ color: 'var(--color-muted)' }}>
        Automating LinkedIn violates its User Agreement and risks account restriction. Keep frequency low,
        log in manually, and use this responsibly.
      </p>
    </div>
  )
}
