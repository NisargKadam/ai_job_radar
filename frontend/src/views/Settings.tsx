import { useEffect, useState } from 'react'
import { KeyRound, Save, TriangleAlert } from 'lucide-react'
import { Field, Toggle } from '../components/ui'
import { api } from '../api'
import type { Settings as S } from '../types'

export function Settings({ onSaved }: { onSaved: () => void }) {
  const [draft, setDraft] = useState<S | null>(null)
  const [kwText, setKwText] = useState('')
  const [groupsText, setGroupsText] = useState('')
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)
  const [reauthMsg, setReauthMsg] = useState<string | null>(null)

  useEffect(() => {
    api.getSettings().then((s) => {
      setDraft(s)
      setKwText(s.keywords.join('\n'))
      setGroupsText(s.group_ids.join('\n'))
    })
  }, [])

  if (!draft) {
    return <p className="mono text-[13px]" style={{ color: 'var(--color-muted)' }}>Loading settings…</p>
  }

  const set = <K extends keyof S>(k: K, v: S[K]) => setDraft({ ...draft, [k]: v })

  async function save() {
    setSaving(true)
    setNotice(null)
    try {
      const patch: Partial<S> = {
        ...draft!,
        keywords: kwText.split('\n').map((s) => s.trim()).filter(Boolean),
        group_ids: groupsText.split('\n').map((s) => s.trim()).filter(Boolean),
      }
      const saved = await api.putSettings(patch)
      setDraft(saved)
      setKwText(saved.keywords.join('\n'))
      setGroupsText(saved.group_ids.join('\n'))
      setNotice({ kind: 'ok', text: 'Settings saved.' })
      onSaved()
    } catch (e) {
      setNotice({ kind: 'err', text: e instanceof Error ? e.message : String(e) })
    } finally {
      setSaving(false)
    }
  }

  async function reauth() {
    setReauthMsg('Opening browser…')
    try {
      const r = await api.reauth()
      setReauthMsg(r.message)
    } catch (e) {
      setReauthMsg(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <div className="mx-auto max-w-[860px] pb-12">
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Scanning */}
        <section className="panel p-6">
          <div className="eyebrow mb-4">Scanning</div>
          <div className="space-y-4">
            <Field label="Match keywords" hint="One per line. Used for search + classifier judgment.">
              <textarea className="field h-32 resize-none" value={kwText} onChange={(e) => setKwText(e.target.value)} />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Schedule time" hint="Daily run (local)">
                <input type="time" className="field" value={draft.schedule_time} onChange={(e) => set('schedule_time', e.target.value)} />
              </Field>
              <Field label="Min posts / day" hint="Low-yield notice below this">
                <input type="number" min={1} className="field" value={draft.min_posts} onChange={(e) => set('min_posts', Number(e.target.value))} />
              </Field>
            </div>
            <Field label="Ollama model" hint="Must exist in `ollama list`">
              <input className="field" value={draft.ollama_model} onChange={(e) => set('ollama_model', e.target.value)} />
            </Field>
          </div>
        </section>

        {/* Delivery */}
        <section className="panel p-6">
          <div className="eyebrow mb-4">Delivery</div>
          <div className="space-y-4">
            <Field label="Channel">
              <select className="field" value={draft.delivery_channel} onChange={(e) => set('delivery_channel', e.target.value)}>
                <option value="telegram">Telegram (recommended)</option>
                <option value="whatsapp">WhatsApp — macOS app (deferred)</option>
              </select>
            </Field>
            {draft.delivery_channel === 'whatsapp' && (
              <div className="flex items-start gap-2 rounded-lg p-3" style={{ background: 'rgba(224,101,95,0.08)' }}>
                <TriangleAlert size={14} style={{ color: 'var(--color-err)', marginTop: 2 }} />
                <p className="mono text-[11px]" style={{ color: 'var(--color-muted)' }}>
                  Unofficial macOS-app automation, against WhatsApp ToS, risk of number ban. Not yet implemented — use a non-primary number when it ships.
                </p>
              </div>
            )}
            <Field label="Target group / chat IDs" hint="One per line (e.g. -1001234567890)">
              <textarea className="field h-24 resize-none" value={groupsText} onChange={(e) => setGroupsText(e.target.value)} />
            </Field>
            <ToggleRow
              label="Send individually"
              hint="Off = one digest per group (recommended)"
              checked={draft.send_individual}
              onChange={(v) => set('send_individual', v)}
            />
          </div>
        </section>
      </div>

      {/* Behaviour */}
      <section className="panel mt-4 p-6">
        <div className="eyebrow mb-4">Behaviour</div>
        <div className="grid gap-4 md:grid-cols-3">
          <ToggleRow label="Dry-run" hint="Log messages instead of sending" checked={draft.dry_run} onChange={(v) => set('dry_run', v)} />
          <ToggleRow
            label="Auto-send"
            hint="⚠ Sends without your approval"
            danger={draft.auto_send}
            checked={draft.auto_send}
            onChange={(v) => set('auto_send', v)}
          />
          <ToggleRow label="Fixture mode" hint="Use sample posts, skip the browser" checked={draft.fixture_mode} onChange={(v) => set('fixture_mode', v)} />
        </div>
        {draft.auto_send && !draft.dry_run && (
          <div className="mt-4 flex items-start gap-2 rounded-lg p-3" style={{ background: 'rgba(224,101,95,0.08)' }}>
            <TriangleAlert size={14} style={{ color: 'var(--color-err)', marginTop: 2 }} />
            <p className="mono text-[11px]" style={{ color: 'var(--color-muted)' }}>
              Auto-send + live delivery: scheduled runs will push jobs to your groups with no human review. Make sure that’s intended.
            </p>
          </div>
        )}
      </section>

      {/* LinkedIn session */}
      <section className="panel mt-4 flex flex-wrap items-center gap-4 p-6">
        <div className="flex-1">
          <div className="eyebrow mb-1">LinkedIn session</div>
          <p className="mono text-[12px]" style={{ color: 'var(--color-muted)' }}>
            Opens a real browser to log in manually. Your session persists; no password is ever stored.
          </p>
          {reauthMsg && <p className="mono mt-2 text-[12px]" style={{ color: 'var(--color-accent)' }}>{reauthMsg}</p>}
        </div>
        <button className="btn" onClick={reauth}>
          <KeyRound size={15} /> Re-authenticate LinkedIn
        </button>
      </section>

      {/* Save bar */}
      <div className="mt-5 flex items-center gap-3">
        <button className="btn btn-accent" onClick={save} disabled={saving}>
          <Save size={15} /> {saving ? 'Saving…' : 'Save settings'}
        </button>
        {notice && (
          <span className="mono text-[12px]" style={{ color: notice.kind === 'ok' ? 'var(--color-ok)' : 'var(--color-err)' }}>
            {notice.text}
          </span>
        )}
      </div>
    </div>
  )
}

function ToggleRow({
  label,
  hint,
  checked,
  onChange,
  danger = false,
}: {
  label: string
  hint?: string
  checked: boolean
  onChange: (v: boolean) => void
  danger?: boolean
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border px-3 py-3" style={{ borderColor: 'var(--color-line)' }}>
      <div>
        <div className="text-[14px]" style={{ fontWeight: 600, color: danger ? 'var(--color-err)' : 'var(--color-ink)' }}>{label}</div>
        {hint && <div className="mono mt-0.5 text-[10.5px]" style={{ color: 'var(--color-faint)' }}>{hint}</div>}
      </div>
      <Toggle checked={checked} onChange={onChange} />
    </div>
  )
}
