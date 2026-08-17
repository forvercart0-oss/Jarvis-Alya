import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  CheckCircle2, XCircle, Loader2,
  GitBranch, Send, Bot, Play, Square,
  RotateCcw, Settings, Terminal, Pause
} from 'lucide-react'
import { Button } from '../Common/Button'
import type { AgentSession, AgentTask, GitStatus, JarvisSettings } from '../../types'

const STATE_COLORS: Record<string, string> = {
  idle: 'text-slate-400',
  planning: 'text-yellow-400',
  waiting_for_permission: 'text-orange-400',
  waiting_for_user: 'text-orange-400',
  executing: 'text-cyan-400',
  observing: 'text-blue-400',
  verifying: 'text-purple-400',
  recovering: 'text-yellow-400',
  paused: 'text-slate-400',
  completed: 'text-emerald-400',
  failed: 'text-red-400',
  cancelled: 'text-slate-500',
}

interface AgentPanelProps {
  projects: { name: string; stack?: string }[]
  onStartAgent: (message: string, project?: string, options?: { project_root?: string; persona?: string; autonomy_level?: string; dry_run?: boolean }) => Promise<any>
  onApproveAgent: (sessionId: string) => Promise<any>
  onCancelAgent: (sessionId: string) => Promise<any>
  onPauseAgent: (sessionId: string) => Promise<any>
  onResumeAgent: (sessionId: string) => Promise<any>
  onKillAgent: (sessionId: string) => Promise<any>
  onRollbackAgent: (sessionId: string) => Promise<any>
  onUpdateAgentPermissions: (updates: Record<string, any>) => Promise<any>
  onLoadAgentPermissions: () => Promise<any>
  settings: JarvisSettings | null
}

export function AgentPanel({
  projects,
  onStartAgent,
  onApproveAgent,
  onCancelAgent,
  onPauseAgent,
  onResumeAgent,
  onKillAgent,
  onRollbackAgent,
  onUpdateAgentPermissions,
  onLoadAgentPermissions,
  settings: _settings,
}: AgentPanelProps) {
  const [mode, setMode] = useState<'chat' | 'agent'>('chat')
  const [input, setInput] = useState('')
  const [session, setSession] = useState<AgentSession | null>(null)
  const [busy, setBusy] = useState(false)
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null)
  const [output, setOutput] = useState<string[]>([])
  const [permissions, setPermissions] = useState<any>(null)
  const [showPermissions, setShowPermissions] = useState(false)

  useEffect(() => {
    onLoadAgentPermissions().then((p) => { if (p) setPermissions(p) }).catch(() => {})
  }, [onLoadAgentPermissions])

  useEffect(() => {
    if (selectedProject) {
      fetch(`/api/git/status?path=${encodeURIComponent(selectedProject)}`)
        .then((res) => res.ok ? res.json() : null)
        .then((data) => { if (data) setGitStatus(data) })
        .catch(() => {})
    }
  }, [selectedProject])

  const addOutput = useCallback((line: string) => {
    setOutput((prev) => [...prev.slice(-200), line])
  }, [])

  const handleSend = async () => {
    if (!input.trim() || busy) return
    setBusy(true)
    setOutput([])
    try {
      const res = await onStartAgent(input.trim(), selectedProject || undefined)
      if (res?.events && res.events.length > 0) {
        const planEvent = res.events.find((e: any) => e.event === 'agent_plan')
        const startedEvent = res.events.find((e: any) => e.event === 'agent_started')
        if (planEvent || startedEvent) {
          const sessionId = startedEvent?.data?.session_id || res.events[0]?.data?.session_id
          setSession({
            session_id: sessionId,
            state: 'waiting_for_permission',
            plan: planEvent?.data?.plan || null,
            current_task_index: 0,
            history: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        }
        for (const ev of res.events) {
          addOutput(`[${ev.event}] ${JSON.stringify(ev.data).slice(0, 200)}`)
        }
      }
    } catch (err) {
      addOutput(err instanceof Error ? err.message : 'Agent failed to start')
    } finally {
      setBusy(false)
      setInput('')
    }
  }

  const handleApprove = async () => {
    if (!session) return
    setBusy(true)
    try {
      const res = await onApproveAgent(session.session_id)
      if (res?.events) {
        for (const ev of res.events) {
          addOutput(`[${ev.event}] ${JSON.stringify(ev.data).slice(0, 200)}`)
        }
      }
    } catch (err) {
      addOutput(err instanceof Error ? err.message : 'Approval failed')
    } finally {
      setBusy(false)
    }
  }

  const handleCancel = async () => {
    if (!session) return
    setBusy(true)
    try {
      await onCancelAgent(session.session_id)
      setSession((prev) => prev ? { ...prev, state: 'cancelled' } : null)
      addOutput('[agent_cancelled] User cancelled the operation')
    } catch {
      // ignore
    } finally {
      setBusy(false)
    }
  }

  const handlePause = async () => {
    if (!session) return
    setBusy(true)
    try {
      await onPauseAgent(session.session_id)
      setSession((prev) => prev ? { ...prev, state: 'paused' } : null)
      addOutput('[agent_paused] Task paused')
    } catch {
      // ignore
    } finally {
      setBusy(false)
    }
  }

  const handleResume = async () => {
    if (!session) return
    setBusy(true)
    try {
      await onResumeAgent(session.session_id)
      setSession((prev) => prev ? { ...prev, state: 'executing' } : null)
      addOutput('[agent_resumed] Task resumed')
    } catch {
      // ignore
    } finally {
      setBusy(false)
    }
  }

  const handleKill = async () => {
    if (!session) return
    setBusy(true)
    try {
      await onKillAgent(session.session_id)
      setSession((prev) => prev ? { ...prev, state: 'cancelled', kill_switch: true } : null)
      addOutput('[agent_kill] Kill switch activated')
    } catch {
      // ignore
    } finally {
      setBusy(false)
    }
  }

  const handleRollback = async () => {
    if (!session) return
    setBusy(true)
    try {
      const res = await onRollbackAgent(session.session_id)
      addOutput(`[rollback] ${JSON.stringify(res)}`)
    } catch {
      // ignore
    } finally {
      setBusy(false)
    }
  }

  const handlePermissionChange = async (key: string, value: any) => {
    const updates = { [key]: value }
    await onUpdateAgentPermissions(updates)
    setPermissions((prev: any) => ({ ...prev, ...updates }))
  }

  const renderTask = (task: AgentTask, _index: number) => {
    const statusIcon = task.status === 'completed' ? (
      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
    ) : task.status === 'running' || task.status === 'verifying' || task.status === 'fixing' ? (
      <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
    ) : task.status === 'failed' ? (
      <XCircle className="w-4 h-4 text-red-400" />
    ) : (
      <div className="w-4 h-4 rounded-full border border-slate-600" />
    )
    return (
      <motion.div
        key={task.task_id}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex items-start gap-3 p-3 rounded bg-slate-900/50 border border-slate-700/30"
      >
        {statusIcon}
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-300">{task.title}</p>
          <p className="text-[10px] text-slate-500">{task.type} · risk: {task.risk}</p>
          {task.error && <p className="text-[10px] text-red-400 mt-1">{task.error}</p>}
          {task.output && <p className="text-[10px] text-slate-400 mt-1 font-mono">{task.output.slice(0, 200)}</p>}
        </div>
      </motion.div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-medium text-slate-200">Agent Mode</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={mode === 'chat' ? 'secondary' : 'primary'}
            onClick={() => setMode('chat')}
          >
            Chat
          </Button>
          <Button
            size="sm"
            variant={mode === 'agent' ? 'primary' : 'secondary'}
            onClick={() => setMode('agent')}
          >
            <Bot className="w-3.5 h-3.5" /> Agent
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        {mode === 'chat' && (
          <div className="text-center py-12 text-slate-500 text-xs">
            Switch to Agent mode to plan and execute multi-step tasks.
          </div>
        )}

        {mode === 'agent' && (
          <>
            <div className="glass-panel p-3 space-y-2">
              <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Project</label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
              >
                <option value="">Select a project</option>
                {projects.map((p) => (
                  <option key={p.name} value={p.name}>{p.name} {p.stack ? `(${p.stack})` : ''}</option>
                ))}
              </select>
            </div>

            {gitStatus && (
              <div className="glass-panel p-3 space-y-1">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <GitBranch className="w-3.5 h-3.5" />
                  <span>Git: {gitStatus.branch || 'unknown'}</span>
                </div>
                <div className="flex gap-3 text-[10px]">
                  {gitStatus.modified.length > 0 && <span className="text-yellow-400">{gitStatus.modified.length} modified</span>}
                  {gitStatus.added.length > 0 && <span className="text-emerald-400">{gitStatus.added.length} added</span>}
                  {gitStatus.untracked.length > 0 && <span className="text-slate-400">{gitStatus.untracked.length} untracked</span>}
                  {gitStatus.clean && <span className="text-emerald-400">Clean</span>}
                </div>
              </div>
            )}

            {session?.plan && (
              <div className="glass-panel p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs tracking-[0.2em] text-cyan-400/70 uppercase">Agent Plan</h3>
                  <span className={`text-[10px] ${STATE_COLORS[session.state] || 'text-slate-400'}`}>
                    {session.state}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{session.plan.description}</p>
                <div className="space-y-2">
                  {session.plan.tasks.map((task, idx) => renderTask(task, idx))}
                </div>
                 <div className="flex gap-2 pt-2">
                  {session.state === 'waiting_for_permission' && (
                    <>
                      <Button size="sm" className="flex-1" onClick={handleApprove} disabled={busy}>
                        <Play className="w-3.5 h-3.5" /> Start
                      </Button>
                      <Button size="sm" variant="secondary" className="flex-1" onClick={handleCancel} disabled={busy}>
                        <Square className="w-3.5 h-3.5" /> Cancel
                      </Button>
                    </>
                  )}
                  {(session.state === 'executing' || session.state === 'observing' || session.state === 'verifying' || session.state === 'recovering') && (
                    <>
                      <Button size="sm" variant="secondary" onClick={handlePause} disabled={busy}>
                        <Pause className="w-3.5 h-3.5" /> Pause
                      </Button>
                      <Button size="sm" variant="secondary" onClick={handleKill} disabled={busy}>
                        <Square className="w-3.5 h-3.5" /> Kill
                      </Button>
                    </>
                  )}
                  {session.state === 'paused' && (
                    <>
                      <Button size="sm" className="flex-1" onClick={handleResume} disabled={busy}>
                        <Play className="w-3.5 h-3.5" /> Resume
                      </Button>
                      <Button size="sm" variant="secondary" onClick={handleKill} disabled={busy}>
                        <Square className="w-3.5 h-3.5" /> Kill
                      </Button>
                    </>
                  )}
                  {(session.state === 'completed' || session.state === 'failed' || session.state === 'cancelled') && (
                    <Button size="sm" variant="secondary" onClick={handleRollback} disabled={busy}>
                      <RotateCcw className="w-3.5 h-3.5" /> Rollback
                    </Button>
                  )}
                </div>
              </div>
            )}

            {!session && (
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask the agent to plan and execute a task..."
                    className="flex-1 bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
                  />
                  <Button size="sm" onClick={handleSend} disabled={busy || !input.trim()}>
                    <Send className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            )}

            {output.length > 0 && (
              <div className="glass-panel p-3">
                <div className="flex items-center gap-2 mb-2">
                  <Terminal className="w-3.5 h-3.5 text-cyan-400/70" />
                  <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Agent Terminal</span>
                </div>
                <pre className="text-[10px] font-mono text-slate-300 whitespace-pre-wrap max-h-64 overflow-y-auto">
                  {output.join('\n')}
                </pre>
              </div>
            )}

            <div className="glass-panel p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Settings className="w-3.5 h-3.5 text-cyan-400/70" />
                  <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Agent Settings</span>
                </div>
                <Button size="sm" variant="ghost" onClick={() => setShowPermissions(!showPermissions)}>
                  {showPermissions ? 'Hide' : 'Show'}
                </Button>
              </div>
              {showPermissions && permissions && (
                <div className="space-y-2 text-xs">
                  <label className="flex items-center justify-between">
                    <span className="text-slate-400">Auto Execute</span>
                    <input
                      type="checkbox"
                      checked={permissions.auto_execute}
                      onChange={(e) => handlePermissionChange('auto_execute', e.target.checked)}
                    />
                  </label>
                  <label className="flex items-center justify-between">
                    <span className="text-slate-400">Auto Fix</span>
                    <input
                      type="checkbox"
                      checked={permissions.auto_fix}
                      onChange={(e) => handlePermissionChange('auto_fix', e.target.checked)}
                    />
                  </label>
                  <div>
                    <span className="text-slate-400">Terminal:</span>
                    <select
                      value={permissions.terminal}
                      onChange={(e) => handlePermissionChange('terminal', e.target.value)}
                      className="ml-2 bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1 text-xs"
                    >
                      <option value="allow">Allow</option>
                      <option value="ask">Ask</option>
                      <option value="deny">Deny</option>
                    </select>
                  </div>
                  <div>
                    <span className="text-slate-400">Filesystem Delete:</span>
                    <select
                      value={permissions.filesystem_delete}
                      onChange={(e) => handlePermissionChange('filesystem_delete', e.target.value)}
                      className="ml-2 bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1 text-xs"
                    >
                      <option value="allow">Allow</option>
                      <option value="ask">Ask</option>
                      <option value="deny">Deny</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
