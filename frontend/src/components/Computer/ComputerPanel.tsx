import { useState, useEffect, useCallback } from 'react'
import { Monitor, Play, Volume2, Type, Maximize2 } from 'lucide-react'
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
}

export function ComputerPanel({ onNavigate: _onNavigate }: ComputerPanelProps) {
  const [status, setStatus] = useState<ComputerStatus | null>(null)
  const [appName, setAppName] = useState('')
  const [textToType, setTextToType] = useState('')
  const [logs, setLogs] = useState<string[]>([])
  const [busy, setBusy] = useState(false)

  const addLog = useCallback((msg: string) => {
    setLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 50))
  }, [])

  const refreshStatus = useCallback(async () => {
    try {
      const res: any = await api.executeTool('computer_control', { action: 'audio_server_status' })
      if (res?.success) {
        setStatus({
          platform: res.result?.platform || 'unknown',
          available: true,
        })
      } else {
        setStatus({ platform: 'unknown', available: false })
      }
    } catch {
      setStatus({ platform: 'unknown', available: false })
    }
  }, [])

  useEffect(() => {
    refreshStatus()
    const timer = setInterval(refreshStatus, 10000)
    return () => clearInterval(timer)
  }, [refreshStatus])

  const handleOpenApp = async () => {
    if (!appName.trim()) return
    setBusy(true)
    addLog(`Opening ${appName}...`)
    try {
      const res: any = await api.executeTool('computer_control', { action: 'open_application', arguments: { app: appName.trim() } })
      if (res?.success) addLog(`Opened ${appName}`)
      else if (res?.confirmation_required) addLog(`Confirmation required for opening ${appName}`)
      else addLog(`Failed: ${res?.error}`)
      setAppName('')
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
      const res: any = await api.executeTool('computer_control', { action: 'type_text', arguments: { text: textToType.trim() } })
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

  const handleScreenshot = async () => {
    setBusy(true)
    addLog('Taking screenshot...')
    try {
      const res: any = await api.executeTool('computer_control', { action: 'take_screenshot', arguments: {} })
      if (res?.success) addLog('Screenshot taken')
      else addLog(`Screenshot failed: ${res?.error}`)
    } catch {
      addLog('Screenshot error')
    } finally {
      setBusy(false)
    }
  }

  const handleSetVolume = async (level: number) => {
    setBusy(true)
    addLog(`Setting volume to ${level}%`)
    try {
      const res: any = await api.executeTool('computer_control', { action: 'set_volume', arguments: { level } })
      if (res?.success) addLog(`Volume set to ${level}%`)
      else addLog(`Volume failed: ${res?.error}`)
    } catch {
      addLog('Volume error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Monitor className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-medium text-slate-200">Computer Control</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${status?.available ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <span className="text-xs text-slate-400">{status?.available ? `Ready (${status.platform})` : 'Unavailable'}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
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
              placeholder="Text to type into focused window..."
              className="flex-1"
            />
            <Button size="sm" onClick={handleType} disabled={busy || !textToType.trim()}>
              <Type className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Volume</label>
          <div className="flex gap-2">
            {[25, 50, 75, 100].map((level) => (
              <Button key={level} size="sm" variant="secondary" onClick={() => handleSetVolume(level)} disabled={busy}>
                <Volume2 className="w-3.5 h-3.5 mr-1" /> {level}%
              </Button>
            ))}
          </div>
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Screenshot</label>
          <Button size="sm" onClick={handleScreenshot} disabled={busy} className="w-full">
            <Maximize2 className="w-3.5 h-3.5 mr-1" /> Take Screenshot
          </Button>
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
