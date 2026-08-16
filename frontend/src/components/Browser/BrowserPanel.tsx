import { useState, useEffect, useCallback } from 'react'
import { Globe, ExternalLink, ArrowLeft, ArrowRight, RotateCw, Eye } from 'lucide-react'
import { Button } from '../../components/Common/Button'
import { Input } from '../../components/Common/Input'
import { api } from '../../services/api'
import type { TabId } from '../../types'

interface BrowserPanelProps {
  onNavigate: (tab: TabId) => void
}

interface BrowserSessionInfo {
  url: string
  title: string
  connected: boolean
  tabs: { title: string; url: string }[]
}

export function BrowserPanel({ onNavigate: _onNavigate }: BrowserPanelProps) {
  const [url, setUrl] = useState('')
  const [status, setStatus] = useState<BrowserSessionInfo | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [busy, setBusy] = useState(false)

  const addLog = useCallback((msg: string) => {
    setLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 50))
  }, [])

  const refreshStatus = useCallback(async () => {
    try {
      const res: any = await api.executeTool('browser_status', {})
      if (res?.success && res?.result) {
        setStatus({
          url: res.result.url || '',
          title: res.result.title || '',
          connected: res.result.connected || false,
          tabs: res.result.tabs || [],
        })
      }
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    refreshStatus()
    const timer = setInterval(refreshStatus, 5000)
    return () => clearInterval(timer)
  }, [refreshStatus])

  const handleNavigate = async () => {
    if (!url.trim()) return
    setBusy(true)
    addLog(`Navigating to ${url}`)
    try {
      const res: any = await api.executeTool('browser_navigate', { url: url.trim() })
      if (res?.success && res?.result?.success) {
        addLog(`Opened: ${res.result.url || res.result.title}`)
        setUrl('')
        refreshStatus()
      } else {
        addLog(`Navigation failed: ${res?.error || res?.result?.error || 'Unknown error'}`)
      }
    } catch (err) {
      addLog(`Navigation error: ${err instanceof Error ? err.message : 'Unknown'}`)
    } finally {
      setBusy(false)
    }
  }

  const handleBack = async () => {
    setBusy(true)
    addLog('Going back...')
    try {
      const res: any = await api.executeTool('browser_back', {})
      if (res?.success) addLog('Went back')
      else addLog(`Back failed: ${res?.error || 'Unknown'}`)
      refreshStatus()
    } catch {
      addLog('Back error')
    } finally {
      setBusy(false)
    }
  }

  const handleForward = async () => {
    setBusy(true)
    addLog('Going forward...')
    try {
      const res: any = await api.executeTool('browser_forward', {})
      if (res?.success) addLog('Went forward')
      else addLog(`Forward failed: ${res?.error || 'Unknown'}`)
      refreshStatus()
    } catch {
      addLog('Forward error')
    } finally {
      setBusy(false)
    }
  }

  const handleReload = async () => {
    setBusy(true)
    addLog('Reloading...')
    try {
      const res: any = await api.executeTool('browser_reload', {})
      if (res?.success) addLog('Reloaded')
      else addLog(`Reload failed: ${res?.error || 'Unknown'}`)
      refreshStatus()
    } catch {
      addLog('Reload error')
    } finally {
      setBusy(false)
    }
  }

  const handleScreenshot = async () => {
    setBusy(true)
    addLog('Taking screenshot...')
    try {
      const res: any = await api.executeTool('browser_screenshot', {})
      if (res?.success) addLog('Screenshot taken')
      else addLog(`Screenshot failed: ${res?.error || 'Unknown'}`)
    } catch {
      addLog('Screenshot error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-medium text-slate-200">Browser Agent</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${status?.connected ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <span className="text-xs text-slate-400">{status?.connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Current URL</label>
          {status?.url ? (
            <div className="flex items-center gap-2 text-xs text-slate-300 font-mono break-all">
              <ExternalLink className="w-3 h-3 text-slate-500 flex-shrink-0" />
              {status.url}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No page loaded</p>
          )}
          {status?.title && <p className="text-[10px] text-slate-500 truncate">{status.title}</p>}
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Navigate</label>
          <div className="flex gap-2">
            <Input
              value={url}
              onChange={setUrl}
              onKeyDown={(e) => e.key === 'Enter' && handleNavigate()}
              placeholder="Enter URL or search..."
              className="flex-1"
            />
            <Button size="sm" onClick={handleNavigate} disabled={busy || !url.trim()}>
              <ExternalLink className="w-3.5 h-3.5" />
            </Button>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={handleBack} disabled={busy}><ArrowLeft className="w-3.5 h-3.5" /></Button>
            <Button size="sm" variant="secondary" onClick={handleForward} disabled={busy}><ArrowRight className="w-3.5 h-3.5" /></Button>
            <Button size="sm" variant="secondary" onClick={handleReload} disabled={busy}><RotateCw className="w-3.5 h-3.5" /></Button>
            <Button size="sm" variant="secondary" onClick={handleScreenshot} disabled={busy}><Eye className="w-3.5 h-3.5" /></Button>
          </div>
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Open Tabs</label>
          {status?.tabs && status.tabs.length > 0 ? (
            <div className="space-y-1">
              {status.tabs.map((tab, idx) => (
                <div key={idx} className="text-xs text-slate-400 truncate">
                  {tab.title || tab.url}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No tabs</p>
          )}
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Activity Log</label>
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {logs.map((log, idx) => (
              <div key={idx} className="text-[10px] text-slate-500 font-mono break-all">{log}</div>
            ))}
            {logs.length === 0 && <p className="text-[10px] text-slate-600">No activity yet</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
