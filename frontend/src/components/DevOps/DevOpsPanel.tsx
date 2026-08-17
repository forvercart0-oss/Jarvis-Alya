// Frontend DevOps panel for JARVIS Phase 28.

import { useState, useEffect, useCallback } from 'react'
import { Server, RefreshCw, Play, Square, RotateCcw, Shield } from 'lucide-react'
import { Button } from '../../components/Common/Button'
import { Input } from '../../components/Common/Input'
import { api } from '../../services/api'

interface DevOpsPanelProps {
  onNavigate: (tab: any) => void
}

export function DevOpsPanel({ onNavigate: _onNavigate }: DevOpsPanelProps) {
  const [status, setStatus] = useState<any>(null)
  const [containers, setContainers] = useState<any[]>([])
  const [servers, setServers] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [logs, setLogs] = useState<string[]>([])
  const [project, setProject] = useState('')
  const [environment, setEnvironment] = useState('local')
  const [busy, setBusy] = useState(false)

  const addLog = useCallback((msg: string) => {
    setLogs((prev) => [...prev.slice(-100), `[${new Date().toLocaleTimeString()}] ${msg}`])
  }, [])

  const refresh = useCallback(async () => {
    try {
      const res = await api.getDevOpsStatus()
      if (res) setStatus(res)
      const containersRes = await api.getDevOpsContainers()
      if (containersRes?.success) setContainers(containersRes.containers || [])
      const serversRes = await api.getDevOpsServers()
      if (serversRes?.success) setServers(serversRes.servers || [])
      const alertsRes = await api.getDevOpsAlerts()
      if (alertsRes?.success) setAlerts(alertsRes.alerts || [])
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 10000)
    return () => clearInterval(timer)
  }, [refresh])

  const handleDeploy = async () => {
    if (!project.trim()) return
    setBusy(true)
    addLog(`Deploying ${project} to ${environment}...`)
    try {
      const res = await api.deployDevOps('Deploy project', project.trim(), environment)
      if (res?.success) {
        addLog(`Deployment completed: ${res.task?.status}`)
      } else {
        addLog(`Deployment failed: ${res?.error || 'Unknown'}`)
      }
    } catch (err) {
      addLog(`Deployment error: ${err instanceof Error ? err.message : 'Unknown'}`)
    } finally {
      setBusy(false)
    }
  }

  const handleContainerAction = async (action: string, service: string) => {
    setBusy(true)
    addLog(`${action} ${service}...`)
    try {
      let res
      if (action === 'start') res = await api.startDevOpsContainer(service)
      else if (action === 'stop') res = await api.stopDevOpsContainer(service)
      else if (action === 'logs') res = await api.getDevOpsContainerLogs(service)
      if (res?.success) addLog(`${action} completed`)
      else addLog(`${action} failed: ${res?.error || 'Unknown'}`)
      refresh()
    } catch {
      addLog(`${action} error`)
    } finally {
      setBusy(false)
    }
  }

  const handleRollback = async () => {
    setBusy(true)
    addLog('Rollback not available in this build.')
    setBusy(false)
  }

  const handleScan = async () => {
    setBusy(true)
    addLog('Supply chain scan not available in this build.')
    setBusy(false)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-medium text-slate-200">DevOps</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={refresh} disabled={busy}><RefreshCw className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Deploy</label>
          <div className="flex gap-2">
            <Input value={project} onChange={setProject} placeholder="Project name" className="flex-1" />
            <select value={environment} onChange={(e) => setEnvironment(e.target.value)} className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200">
              <option value="local">Local</option>
              <option value="staging">Staging</option>
              <option value="production">Production</option>
            </select>
            <Button size="sm" onClick={handleDeploy} disabled={busy || !project.trim()}><Play className="w-3.5 h-3.5" /></Button>
            <Button size="sm" variant="secondary" onClick={handleRollback} disabled={busy || !project.trim()}><RotateCcw className="w-3.5 h-3.5" /></Button>
            <Button size="sm" variant="secondary" onClick={handleScan} disabled={busy || !project.trim()}><Shield className="w-3.5 h-3.5" /></Button>
          </div>
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Containers</label>
          {containers.length === 0 ? (
            <p className="text-xs text-slate-500">No containers</p>
          ) : (
            <div className="space-y-1">
              {containers.map((c, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs text-slate-300 p-2 rounded bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${c.status === 'running' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                    <span>{c.name}</span>
                  </div>
                  <div className="flex gap-1">
                    <Button size="sm" variant="secondary" onClick={() => handleContainerAction('start', c.name)} disabled={busy}><Play className="w-3 h-3" /></Button>
                    <Button size="sm" variant="secondary" onClick={() => handleContainerAction('stop', c.name)} disabled={busy}><Square className="w-3 h-3" /></Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Servers</label>
          {servers.length === 0 ? (
            <p className="text-xs text-slate-500">No servers configured</p>
          ) : (
            <div className="space-y-1">
              {servers.map((s, idx) => (
                <div key={idx} className="text-xs text-slate-300 p-2 rounded bg-slate-800/50 flex items-center justify-between">
                  <span>{s.name} ({s.host})</span>
                  <span className={`text-[10px] ${s.status === 'online' ? 'text-emerald-400' : 'text-red-400'}`}>{s.status}</span>
                </div>
              ))}
            </div>
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

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Infrastructure</label>
          <div className="grid grid-cols-2 gap-2 text-xs text-slate-300">
            <div>Proxy: {status?.docker_available ? 'Docker' : 'None'}</div>
            <div>K8s: {status?.kubernetes_available ? 'Available' : 'N/A'}</div>
            <div>Cloud: {status?.cloud || 'None'}</div>
            <div>Alerts: {alerts.length}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
