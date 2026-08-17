import { useState } from 'react'
import type { TaskItem, TaskPlan } from '../../types'
import { Play, Pause, Square, CheckCircle2, XCircle, Clock, ChevronRight, ChevronDown, Zap, RotateCcw, AlertTriangle } from 'lucide-react'

interface TasksPanelProps {
  tasks: TaskItem[]
  taskPlan: TaskPlan | null
  onCreate: (description: string, autoExecute?: boolean) => void
  onStart: (id: string) => void
  onPause: (id: string) => void
  onResume: (id: string) => void
  onCancel: (id: string) => void
  onApprove: (id: string) => void
  onDeny: (id: string) => void
  onClearPlan: () => void
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'text-slate-400',
  planning: 'text-yellow-400',
  ready: 'text-blue-400',
  running: 'text-cyan-400',
  waiting: 'text-orange-400',
  paused: 'text-orange-400',
  verifying: 'text-purple-400',
  needs_approval: 'text-red-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
  cancelled: 'text-slate-600',
  blocked: 'text-red-400',
}

const STATUS_BG: Record<string, string> = {
  pending: 'bg-slate-500/10',
  planning: 'bg-yellow-500/10',
  ready: 'bg-blue-500/10',
  running: 'bg-cyan-500/10',
  waiting: 'bg-orange-500/10',
  paused: 'bg-orange-500/10',
  verifying: 'bg-purple-500/10',
  needs_approval: 'bg-red-500/10',
  completed: 'bg-green-500/10',
  failed: 'bg-red-500/10',
  cancelled: 'bg-slate-500/10',
  blocked: 'bg-red-500/10',
}

const inputCls = 'w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60'
const labelCls = 'text-[10px] tracking-widest text-slate-500 uppercase'

export function TasksPanel({ tasks, taskPlan, onCreate, onStart, onPause, onResume, onCancel, onApprove, onDeny, onClearPlan }: TasksPanelProps) {
  const [newTask, setNewTask] = useState('')
  const [autoExecute, setAutoExecute] = useState(false)
  const [dryRun, setDryRun] = useState(false)
  const [expandedTask, setExpandedTask] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'active' | 'completed' | 'failed'>('all')
  const [view, setView] = useState<'tasks' | 'queue' | 'processes'>('tasks')

  const handleCreate = () => {
    if (!newTask.trim()) return
    onCreate(newTask.trim(), autoExecute)
    setNewTask('')
    setAutoExecute(false)
    setDryRun(false)
  }

  const filteredTasks = tasks.filter((t) => {
    if (filter === 'active') return ['pending', 'planning', 'ready', 'running', 'waiting', 'paused', 'verifying', 'needs_approval', 'blocked'].includes(t.status)
    if (filter === 'completed') return t.status === 'completed'
    if (filter === 'failed') return ['failed', 'cancelled'].includes(t.status)
    return true
  })

  const activeTasks = filteredTasks.filter((t) => ['pending', 'planning', 'ready', 'running', 'waiting', 'paused', 'verifying', 'needs_approval', 'blocked'].includes(t.status))
  const completedTasks = filteredTasks.filter((t) => t.status === 'completed')
  const failedTasks = filteredTasks.filter((t) => ['failed', 'cancelled'].includes(t.status))

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase flex items-center gap-2">
          <Zap className="w-4 h-4" /> Tasks
        </h3>
        <div className="flex gap-1">
          {(['tasks', 'queue', 'processes'] as const).map((v) => (
            <button key={v} onClick={() => setView(v)} className={`px-2 py-1 text-[10px] rounded transition-colors ${view === v ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-300'}`}>
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {view === 'tasks' && (
        <div className="flex gap-1">
          {(['all', 'active', 'completed', 'failed'] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)} className={`px-2 py-1 text-[10px] rounded transition-colors ${filter === f ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-300'}`}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      )}

      {/* Plan Preview */}
      {taskPlan && (
        <div className="glass-panel p-4 space-y-3 border-yellow-400/30">
          <div className="flex items-center justify-between">
            <h4 className="text-xs tracking-widest text-yellow-400 uppercase">Plan Preview</h4>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${taskPlan.approved ? 'text-green-400 bg-green-400/10' : 'text-yellow-400 bg-yellow-400/10'}`}>
              {taskPlan.approved ? 'Approved' : 'Pending Approval'}
            </span>
          </div>
          <p className="text-xs text-slate-400">{taskPlan.description}</p>
          <div className="space-y-1.5">
            {taskPlan.steps.map((step, idx) => (
              <div key={step.step_id} className="flex items-start gap-2 text-xs">
                <span className="text-slate-600 font-mono w-4">{idx + 1}.</span>
                <div className="flex-1">
                  <span className="text-slate-300">{step.title}</span>
                  <span className="text-slate-600 ml-2">({step.tool || step.action})</span>
                </div>
                <span className={`text-[10px] px-1 py-0.5 rounded ${step.risk === 'low' ? 'text-green-400 bg-green-400/10' : step.risk === 'medium' ? 'text-yellow-400 bg-yellow-400/10' : 'text-red-400 bg-red-400/10'}`}>
                  {step.risk}
                </span>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            {!taskPlan.approved ? (
              <>
                <button onClick={() => onApprove(taskPlan.task_id)} className="px-3 py-1.5 bg-green-500/15 border border-green-400/40 rounded text-xs text-green-200 hover:bg-green-400/25 transition-all">
                  Approve
                </button>
                <button onClick={() => onDeny(taskPlan.task_id)} className="px-3 py-1.5 bg-red-500/15 border border-red-400/40 rounded text-xs text-red-200 hover:bg-red-400/25 transition-all">
                  Deny
                </button>
              </>
            ) : (
              <span className="text-[10px] text-green-400">Plan approved. Executing...</span>
            )}
            <button onClick={onClearPlan} className="px-3 py-1.5 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all">
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Create Task */}
      <div className="glass-panel p-3 space-y-2">
        <div className="space-y-1">
          <span className={labelCls}>New Task</span>
          <input
            type="text"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            placeholder="e.g., Create a React project, Open GitHub..."
            className={inputCls}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          />
        </div>
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-[10px] text-slate-500">
            <input type="checkbox" checked={autoExecute} onChange={(e) => setAutoExecute(e.target.checked)} className="rounded border-slate-600" />
            Auto-execute
          </label>
          <label className="flex items-center gap-2 text-[10px] text-slate-500">
            <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} className="rounded border-slate-600" />
            Dry run
          </label>
          <button onClick={handleCreate} disabled={!newTask.trim()} className="px-3 py-1.5 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all disabled:opacity-50">
            Create Task
          </button>
        </div>
      </div>

      {/* Active Tasks */}
      {activeTasks.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[10px] tracking-widest text-cyan-400 uppercase">Active Tasks</h4>
          {activeTasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              expanded={expandedTask === task.id}
              onToggleExpand={() => setExpandedTask(expandedTask === task.id ? null : task.id)}
              onStart={() => onStart(task.id)}
              onPause={() => onPause(task.id)}
              onResume={() => onResume(task.id)}
              onCancel={() => onCancel(task.id)}
            />
          ))}
        </div>
      )}

      {/* Completed Tasks */}
      {completedTasks.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[10px] tracking-widest text-green-400 uppercase">Completed Tasks</h4>
          {completedTasks.map((task) => (
            <TaskCard key={task.id} task={task} onToggleExpand={() => {}} onStart={() => {}} onPause={() => {}} onResume={() => {}} onCancel={() => {}} />
          ))}
        </div>
      )}

      {/* Failed Tasks */}
      {failedTasks.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[10px] tracking-widest text-red-400 uppercase">Failed / Cancelled Tasks</h4>
          {failedTasks.map((task) => (
            <TaskCard key={task.id} task={task} onToggleExpand={() => {}} onStart={() => {}} onPause={() => {}} onResume={() => {}} onCancel={() => {}} />
          ))}
        </div>
      )}

      {filteredTasks.length === 0 && view === 'tasks' && (
        <div className="text-center text-slate-500 py-10 text-xs">No tasks found.</div>
      )}

      {view === 'queue' && (
        <div className="space-y-2">
          <h4 className="text-[10px] tracking-widest text-yellow-400 uppercase">Task Queue</h4>
          <p className="text-[10px] text-slate-500">Queue view requires backend integration.</p>
        </div>
      )}

      {view === 'processes' && (
        <div className="space-y-2">
          <h4 className="text-[10px] tracking-widest text-purple-400 uppercase">Managed Processes</h4>
          <p className="text-[10px] text-slate-500">Process view requires backend integration.</p>
        </div>
      )}
    </div>
  )
}

function TaskCard({ task, expanded, onToggleExpand, onStart, onPause, onResume, onCancel }: {
  task: TaskItem
  expanded?: boolean
  onToggleExpand: () => void
  onStart: () => void
  onPause: () => void
  onResume: () => void
  onCancel: () => void
}) {
  const statusIcon = task.status === 'completed' ? <CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> :
    task.status === 'failed' || task.status === 'cancelled' ? <XCircle className="w-3.5 h-3.5 text-red-400" /> :
    task.status === 'running' ? <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" /> :
    <Clock className="w-3.5 h-3.5 text-slate-500" />

  return (
    <div className={`glass-panel p-3 ${STATUS_BG[task.status] || 'bg-slate-500/10'}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {statusIcon}
            <span className="text-sm text-slate-200 font-mono truncate">{task.description}</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase ${STATUS_COLORS[task.status] || 'text-slate-400'}`}>
              {task.status}
            </span>
            <span className="text-[10px] text-slate-500">{task.complexity}</span>
            <span className="text-[10px] text-slate-600">Step {task.current_step}/{task.total_steps}</span>
            {(task as any).agent && <span className="text-[10px] text-blue-400">{(task as any).agent}</span>}
            {(task as any).skill && <span className="text-[10px] text-purple-400">{(task as any).skill}</span>}
          </div>
          {(task as any).error && (
            <div className="flex items-center gap-1 mt-1 text-[10px] text-red-400">
              <AlertTriangle className="w-3 h-3" />
              {(task as any).error}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1">
          {task.status === 'pending' && (
            <button onClick={onStart} className="p-1.5 rounded text-green-400 hover:bg-green-500/10 transition-colors" title="Start">
              <Play className="w-4 h-4" />
            </button>
          )}
          {task.status === 'running' && (
            <button onClick={onPause} className="p-1.5 rounded text-orange-400 hover:bg-orange-500/10 transition-colors" title="Pause">
              <Pause className="w-4 h-4" />
            </button>
          )}
          {task.status === 'paused' && (
            <button onClick={onResume} className="p-1.5 rounded text-cyan-400 hover:bg-cyan-500/10 transition-colors" title="Resume">
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
          {['pending', 'running', 'paused'].includes(task.status) && (
            <button onClick={onCancel} className="p-1.5 rounded text-red-400 hover:bg-red-500/10 transition-colors" title="Cancel">
              <Square className="w-4 h-4" />
            </button>
          )}
          <button onClick={onToggleExpand} className="p-1.5 rounded text-slate-400 hover:text-cyan-400 transition-colors" title="Details">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-3 space-y-2">
          {task.logs && task.logs.length > 0 && (
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {task.logs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2 text-[10px]">
                  <span className="text-slate-600 font-mono shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  <span className="text-slate-400 flex-1">{log.action}</span>
                  <span className={log.result.includes('success') ? 'text-green-400' : 'text-red-400'}>
                    {log.result}
                  </span>
                </div>
              ))}
            </div>
          )}
          {(task.checkpoints && task.checkpoints.length > 0) && (
            <div className="text-[10px] text-slate-500">
              Checkpoints: {task.checkpoints.length}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
