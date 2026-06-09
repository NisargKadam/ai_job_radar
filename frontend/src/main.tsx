import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

// Self-hosted variable fonts (no Google Fonts CDN — keeps the app fully local).
import '@fontsource-variable/bricolage-grotesque'
import '@fontsource-variable/jetbrains-mono'

import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
