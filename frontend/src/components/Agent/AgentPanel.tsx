import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  CheckCircle2, XCircle, Loader2,
  GitBranch, Send, Bot
} from 'lucide-react'
import { Button } from '../Common/Button'
import { api } from '../../services/api'
import type { AgentSession, AgentTask, GitStatus } from '../../types'

const STATE_COLORS: Record<string, string> = {
  idle: 'text-slate-400',
  planning: 'text-yellow-400',
  waiting_approval: 'text-orange-400',
  executing: 'text-cyan-400',
  waiting_confirmation: 'text-purple-400',
  testing: 'text-blue-400',
  completed: 'text-emerald-400',
  failed: 'text-red-400',
  cancelled: 'text-slate-500',
}

export function AgentPanel() {
  const [mode, setMode] = useState<'chat' | 'agent'>('chat')
  const [input, setInput] = useState('')
  const [session, setSession] = useState<AgentSession | null>(null)
  const [busy, setBusy] = useState(false)
  const [projects, setProjects] = useState<{ name: string; stack?: string }[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null)
  const [output, setOutput] = useState<string>('')

  useEffect(() => {
    api.listProjects().then((res: any) => setProjects(res.projects || [])).catch(() => {})
  }, [])

  const loadGitStatus = useCallback(async (project: string) => {
    if (!project) return
    try {
      const res = await fetch(`/api/git/status?path=${encodeURIComponent(project)}`)
      if (res.ok) {
        const data = await res.json()
        setGitStatus(data)
      }
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    if (selectedProject) {
      loadGitStatus(selectedProject)
    }
  }, [selectedProject, loadGitStatus])

  const handleSend = async () => {
    if (!input.trim() || busy) return
    setBusy(true)
    setOutput('')
    try {
      const res = await fetch('/api/agent/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input.trim(), project: selectedProject || undefined, persona: 'jarvis' }),
      })
      const data = await res.json()
      if (data.events && data.events.length > 0) {
        const last = data.events[data.events.length - 1]
        if (last.event === 'agent_plan') {
          setSession({
            session_id: data.events[0].data.session_id,
            state: 'waiting_approval',
            plan: last.data.plan,
            current_task_index: 0,
            history: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        }
      }
    } catch (err) {
      setOutput(err instanceof Error ? err.message : 'Agent failed to start')
    } finally {
      setBusy(false)
      setInput('')
    }
  }

  const handleApprove = async () => {
    if (!session) return
    setBusy(true)
    try {
      const res = await fetch('/api/agent/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: session.session_id }),
      })
      const data = await res.json()
      setOutput(JSON.stringify(data, null, 2))
    } catch (err) {
      setOutput(err instanceof Error ? err.message : 'Approval failed')
    } finally {
      setBusy(false)
    }
  }

  const handleCancel = async () => {
    if (!session) return
    setBusy(true)
    try {
      await fetch('/api/agent/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: session.session_id }),
      })
      setSession((prev) => prev ? { ...prev, state: 'cancelled' } : null)
    } catch {
      // ignore
    } finally {
      setBusy(false)
    }
  }

  const renderTask = (task: AgentTask, _index: number) => {
    const statusIcon = task.status === 'completed' ? (
      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
    ) : task.status === 'running' ? (
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
                {session.state === 'waiting_approval' && (
                  <div className="flex gap-2 pt-2">
                    <Button size="sm" className="flex-1" onClick={handleApprove} disabled={busy}>
                      <CheckCircle2 className="w-3.5 h-3.5" /> Approve Plan
                    </Button>
                    <Button size="sm" variant="secondary" className="flex-1" onClick={handleCancel} disabled={busy}>
                      <XCircle className="w-3.5 h-3.5" /> Cancel
                    </Button>
                  </div>
                )}
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

            {output && (
              <div className="glass-panel p-3">
                <pre className="text-[10px] font-mono text-slate-300 whitespace-pre-wrap max-h-64 overflow-y-auto">{output}</pre>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
