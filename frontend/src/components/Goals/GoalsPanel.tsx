import { useState, useEffect, useCallback } from 'react'
import { api } from '../../services/api'
import { Pause, Square, ChevronRight, ChevronDown, Play } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  pending: 'text-slate-400',
  analyzing: 'text-yellow-400',
  planning: 'text-yellow-400',
  executing: 'text-cyan-400',
  verifying: 'text-purple-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
  cancelled: 'text-slate-600',
  paused: 'text-orange-400',
}

export function GoalsPanel({ pauseGoal, resumeGoal, cancelGoal }: { pauseGoal: (id: string) => void, resumeGoal: (id: string) => void, cancelGoal: (id: string) => void }) {
  const [goals, setGoals] = useState<any[]>([])
  const [newGoal, setNewGoal] = useState('')
  const [expandedGoal, setExpandedGoal] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const res = await api.getGoals()
      setGoals(res.goals || [])
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreate = async () => {
    if (!newGoal.trim()) return
    await api.createGoal({ request: newGoal.trim() })
    setNewGoal('')
    load()
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">Goals</h3>
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="space-y-1">
          <span className="text-[10px] tracking-widest text-slate-500 uppercase">New Goal</span>
          <input
            value={newGoal}
            onChange={(e) => setNewGoal(e.target.value)}
            placeholder="e.g., Build me a complete online store"
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          />
        </div>
        <button onClick={handleCreate} disabled={!newGoal.trim()} className="w-full px-3 py-1.5 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all disabled:opacity-50">
          Execute Goal
        </button>
      </div>

      {goals.length === 0 && <div className="text-center text-slate-500 py-10 text-xs">No goals yet.</div>}

      {goals.map((goal) => (
        <div key={goal.goal_id} className="glass-panel p-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-mono ${STATUS_COLORS[goal.status] || 'text-slate-400'}`}>{goal.status}</span>
                <span className="text-sm text-slate-200 truncate">{goal.user_request}</span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] text-slate-500">{goal.tasks?.length || 0} tasks</span>
                <span className="text-[10px] text-slate-500">{Math.round((goal.progress || 0) * 100)}%</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {goal.status === 'executing' && (
                <button onClick={() => pauseGoal(goal.goal_id)} className="p-1.5 rounded text-orange-400 hover:bg-orange-500/10 transition-colors" title="Pause">
                  <Pause className="w-4 h-4" />
                </button>
              )}
              {goal.status === 'paused' && (
                <button onClick={() => resumeGoal(goal.goal_id)} className="p-1.5 rounded text-cyan-400 hover:bg-cyan-500/10 transition-colors" title="Resume">
                  <Play className="w-4 h-4" />
                </button>
              )}
              {['executing', 'paused'].includes(goal.status) && (
                <button onClick={() => cancelGoal(goal.goal_id)} className="p-1.5 rounded text-red-400 hover:bg-red-500/10 transition-colors" title="Cancel">
                  <Square className="w-4 h-4" />
                </button>
              )}
              <button onClick={() => setExpandedGoal(expandedGoal === goal.goal_id ? null : goal.goal_id)} className="p-1.5 rounded text-slate-400 hover:text-cyan-400 transition-colors" title="Details">
                {expandedGoal === goal.goal_id ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {expandedGoal && (
            <div className="mt-3 space-y-2">
              {goal.tasks?.map((task: any) => (
                <div key={task.task_id} className="flex items-center justify-between py-1.5 px-2 bg-slate-900/30 rounded">
                  <div className="flex-1 min-w-0">
                    <span className="text-xs text-slate-300">{task.title}</span>
                    <span className={`text-[10px] ml-2 ${STATUS_COLORS[task.status] || 'text-slate-500'}`}>{task.status}</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{task.agent}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
