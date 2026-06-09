import { useState } from 'react'
import { Sidebar } from './components/Sidebar'
import type { ViewKey } from './components/Sidebar'
import { TopBar } from './components/TopBar'
import { Banner } from './components/Banner'
import { Dashboard } from './views/Dashboard'
import { ReviewQueue } from './views/ReviewQueue'
import { History } from './views/History'
import { Settings } from './views/Settings'
import { Activity } from './views/Activity'
import { api } from './api'
import { usePolling } from './lib'

function App() {
  const [view, setView] = useState<ViewKey>('dashboard')

  // Shell-level telemetry for the sidebar + top bar.
  const health = usePolling(api.health, 5000)
  const runs = usePolling(api.listRuns, 3000)
  const pending = usePolling(() => api.listCandidates('pending'), 4000)
  const settings = usePolling(api.getSettings, 8000)

  const activeRun = runs.data?.find((r) => r.status === 'running') ?? null

  return (
    <div className="radar-bg grain relative min-h-full">
      <div className="relative z-[2] flex min-h-screen">
        <Sidebar
          view={view}
          setView={setView}
          pendingCount={pending.data?.length ?? 0}
          running={!!activeRun}
          settings={settings.data}
        />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar view={view} health={health.data} activeRun={activeRun} settings={settings.data} />
          <Banner />
          <main key={view} className="flex-1 overflow-auto px-7 py-7">
            {view === 'dashboard' && <Dashboard settings={settings.data} goto={setView} />}
            {view === 'review' && <ReviewQueue />}
            {view === 'history' && <History />}
            {view === 'activity' && <Activity />}
            {view === 'settings' && <Settings onSaved={() => settings.refresh()} />}
          </main>
        </div>
      </div>
    </div>
  )
}

export default App
