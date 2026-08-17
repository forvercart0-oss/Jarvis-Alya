import { useState, useEffect, useCallback } from 'react'
import { Monitor, Play, Type, MousePointer, Eye, Maximize2, List } from 'lucide-react'
import { Button } from '../../components/Common/Button'
import { Input } from '../../components/Common/Input'
import { api } from '../../services/api'
import type { TabId } from '../../types'

interface ComputerPanelProps {
  onNavigate: (tab: TabId) => void
}

interface ComputerStatus {
  platform: string
  available: boolean
  mode?: string
  active_window?: string
  cursor?: { x: number; y: number }
  monitors?: Array<{ id: string; width: number; height: number; scale: number }>
}

export function ComputerPanel({ onNavigate: _onNavigate }: ComputerPanelProps) {
  const [status, setStatus] = useState<ComputerStatus | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [appName, setAppName] = useState('')
  const [textToType, setTextToType] = useState('')
  const [clickX, setClickX] = useState('')
  const [clickY, setClickY] = useState('')
  const [windows, setWindows] = useState<string[]>([])

  const addLog = useCallback((msg: string) => {
    setLogs((prev) => [...prev.slice(-100), `[${new Date().toLocaleTimeString()}] ${msg}`])
  }, [])

  const refreshStatus = useCallback(async () => {
    try {
      const res = await api.getComputerStatus()
      if (res) {
        setStatus({
          platform: res.platform || 'unknown',
          available: res.available || false,
          mode: res.mode || 'off',
          active_window: res.active_window,
          cursor: res.cursor,
          monitors: res.monitors,
        })
      }
    } catch {
      setStatus({ platform: 'unknown', available: false })
    }
  }, [])

  const refreshWindows = useCallback(async () => {
    try {
      const res = await api.getComputerWindows()
      if (res?.success && Array.isArray(res.windows)) {
        setWindows(res.windows)
      }
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    refreshStatus()
    refreshWindows()
    const timer = setInterval(refreshStatus, 5000)
    return () => clearInterval(timer)
  }, [refreshStatus, refreshWindows])

  const handleOpenApp = async () => {
    if (!appName.trim()) return
    setBusy(true)
    addLog(`Opening ${appName}...`)
    try {
      const res = await api.computerAction('open_application', { app: appName.trim() })
      if (res?.success) addLog(`Opened ${appName}`)
      else if (res?.confirmation_required) addLog(`Confirmation required for opening ${appName}`)
      else addLog(`Failed: ${res?.error}`)
      setAppName('')
      refreshWindows()
    } catch {
      addLog('Error opening application')
    } finally {
      setBusy(false)
    }
  }

  const handleType = async () => {
    if (!textToType.trim()) return
    setBusy(true)
    addLog(`Typing: ${textToType}`)
    try {
      const res = await api.computerAction('type_text', { text: textToType.trim() })
      if (res?.success) addLog(`Typed: ${textToType}`)
      else if (res?.confirmation_required) addLog(`Confirmation required for typing`)
      else addLog(`Failed: ${res?.error}`)
      setTextToType('')
    } catch {
      addLog('Error typing text')
    } finally {
      setBusy(false)
    }
  }

  const handleClick = async () => {
    const x = parseInt(clickX, 10)
    const y = parseInt(clickY, 10)
    if (Number.isNaN(x) || Number.isNaN(y)) return
    setBusy(true)
    addLog(`Clicking at ${x}, ${y}`)
    try {
      const res = await api.computerAction('click_at', { x, y, button: 1 })
      if (res?.success) addLog(`Clicked at ${x}, ${y}`)
      else addLog(`Click failed: ${res?.error}`)
    } catch {
      addLog('Click error')
    } finally {
      setBusy(false)
    }
  }

  const handleScreenshot = async () => {
    setBusy(true)
    addLog('Taking screenshot...')
    try {
      const res = await api.computerScreenshot('full')
      if (res?.ok || res?.success) addLog('Screenshot taken')
      else addLog(`Screenshot failed: ${res?.error}`)
    } catch {
      addLog('Screenshot error')
    } finally {
      setBusy(false)
    }
  }

  const handleScreenshotWindow = async () => {
    setBusy(true)
    addLog('Taking window screenshot...')
    try {
      const res = await api.computerScreenshot('window')
      if (res?.ok || res?.success) addLog('Window screenshot taken')
      else addLog(`Screenshot failed: ${res?.error}`)
    } catch {
      addLog('Screenshot error')
    } finally {
      setBusy(false)
    }
  }

  const handleGetActiveWindow = async () => {
    setBusy(true)
    addLog('Getting active window...')
    try {
      const res = await api.computerAction('get_active_window', {})
      if (res?.success) addLog(`Active window: ${res.title}`)
      else addLog(`Failed: ${res?.error}`)
    } catch {
      addLog('Active window error')
    } finally {
      setBusy(false)
    }
  }

  const handleListWindows = async () => {
    setBusy(true)
    addLog('Listing windows...')
    try {
      await refreshWindows()
      addLog(`Found ${windows.length} windows`)
    } catch {
      addLog('List windows error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Monitor className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-medium text-slate-200">Computer Agent</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${status?.available ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <span className="text-xs text-slate-400">{status?.available ? `${status.platform} · ${status.mode || 'off'}` : 'Unavailable'}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Active Window</label>
          {status?.active_window ? (
            <p className="text-xs text-slate-300">{status.active_window}</p>
          ) : (
            <p className="text-xs text-slate-500">No active window</p>
          )}
          {status?.cursor && (
            <p className="text-[10px] text-slate-500">Cursor: {status.cursor.x}, {status.cursor.y}</p>
          )}
          {status?.monitors && status.monitors.length > 0 && (
            <p className="text-[10px] text-slate-500">Monitors: {status.monitors.length}</p>
          )}
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Open Application</label>
          <div className="flex gap-2">
            <Input
              value={appName}
              onChange={setAppName}
              onKeyDown={(e) => e.key === 'Enter' && handleOpenApp()}
              placeholder="Application name (e.g., firefox, code)"
              className="flex-1"
            />
            <Button size="sm" onClick={handleOpenApp} disabled={busy || !appName.trim()}>
              <Play className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Type Text</label>
          <div className="flex gap-2">
            <Input
              value={textToType}
              onChange={setTextToType}
              onKeyDown={(e) => e.key === 'Enter' && handleType()}
              placeholder="Text to type..."
              className="flex-1"
            />
            <Button size="sm" onClick={handleType} disabled={busy || !textToType.trim()}>
              <Type className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Mouse</label>
          <div className="flex gap-2 items-center">
            <Input
              value={clickX}
              onChange={setClickX}
              placeholder="X"
              className="w-16"
              type="number"
            />
            <Input
              value={clickY}
              onChange={setClickY}
              placeholder="Y"
              className="w-16"
              type="number"
            />
            <Button size="sm" onClick={handleClick} disabled={busy || !clickX || !clickY}>
              <MousePointer className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Screen</label>
          <div className="flex gap-2 flex-wrap">
            <Button size="sm" variant="secondary" onClick={handleScreenshot} disabled={busy}>
              <Maximize2 className="w-3.5 h-3.5 mr-1" /> Full
            </Button>
            <Button size="sm" variant="secondary" onClick={handleScreenshotWindow} disabled={busy}>
              <Eye className="w-3.5 h-3.5 mr-1" /> Window
            </Button>
            <Button size="sm" variant="secondary" onClick={handleGetActiveWindow} disabled={busy}>
              <List className="w-3.5 h-3.5 mr-1" /> Window Info
            </Button>
            <Button size="sm" variant="secondary" onClick={handleListWindows} disabled={busy}>
              <List className="w-3.5 h-3.5 mr-1" /> List Windows
            </Button>
          </div>
        </div>

        {windows.length > 0 && (
          <div className="glass-panel p-3 space-y-2">
            <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Open Windows</label>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {windows.slice(0, 20).map((win, idx) => (
                <div key={idx} className="text-xs text-slate-400 truncate">{win}</div>
              ))}
            </div>
          </div>
        )}

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
