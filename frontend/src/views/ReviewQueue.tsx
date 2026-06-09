import { useState } from 'react'
import { CheckCheck, Inbox, RefreshCw } from 'lucide-react'
import { CandidateCard } from '../components/CandidateCard'
import { api } from '../api'
import { errMsg, usePolling } from '../lib'

export function ReviewQueue() {
  const pending = usePolling(() => api.listCandidates('pending'), 4000)
  const [bulkBusy, setBulkBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const cards = pending.data ?? []

  async function approve(id: number) {
    try {
      await api.approve(id)
      setErr(null)
      pending.refresh()
    } catch (e) {
      setErr(errMsg(e))
    }
  }
  async function reject(id: number) {
    try {
      await api.reject(id)
      setErr(null)
      pending.refresh()
    } catch (e) {
      setErr(errMsg(e))
    }
  }
  async function bulkApprove() {
    setBulkBusy(true)
    try {
      await api.bulkApprove()
      setErr(null)
      pending.refresh()
    } catch (e) {
      setErr(errMsg(e))
    } finally {
      setBulkBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-[1100px]">
      <div className="flex flex-wrap items-center gap-3">
        <div className="mono text-[13px]" style={{ color: 'var(--color-muted)' }}>
          <span style={{ color: 'var(--color-accent)' }}>{cards.length}</span> candidate(s) pending · sorted by relevance
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button className="btn btn-ghost" onClick={() => pending.refresh()}>
            <RefreshCw size={14} /> refresh
          </button>
          <button className="btn btn-accent" onClick={bulkApprove} disabled={bulkBusy || cards.length === 0}>
            <CheckCheck size={15} /> {bulkBusy ? 'Approving…' : 'Approve all'}
          </button>
        </div>
      </div>

      {err && (
        <div className="mono mt-3 text-[12px]" style={{ color: 'var(--color-err)' }}>
          {err}
        </div>
      )}

      {cards.length === 0 ? (
        <EmptyState loading={pending.loading} error={pending.error} />
      ) : (
        <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {cards.map((c, i) => (
            <CandidateCard key={c.id} c={c} index={i} onApprove={approve} onReject={reject} />
          ))}
        </div>
      )}
    </div>
  )
}

function EmptyState({ loading, error }: { loading: boolean; error: string | null }) {
  return (
    <div className="panel mt-5 flex flex-col items-center justify-center px-6 py-20 text-center">
      <Inbox size={34} style={{ color: 'var(--color-faint)' }} />
      <p className="font-display mt-4 text-[17px]" style={{ fontWeight: 600 }}>
        {error ? 'Backend unreachable' : loading ? 'Scanning…' : 'Queue is clear'}
      </p>
      <p className="mono mt-2 max-w-md text-[12px]" style={{ color: 'var(--color-muted)' }}>
        {error
          ? error
          : 'No candidates pending review. Trigger a run from the Dashboard — fresh AI/ML job posts will land here for one-click triage.'}
      </p>
    </div>
  )
}
