import { useEffect, useState, useCallback } from 'react'
import { api } from '../../services/api'
import type { Workflow, WorkflowRun, WorkflowApproval } from '../../types'
import type { TabId } from '../../types'

interface WorkflowsPanelProps {
  onNavigate: (tab: TabId) => void
}

export function WorkflowsPanel(_props: WorkflowsPanelProps) {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [runs, setRuns] = useState<WorkflowRun[]>([])
  const [approvals, setApprovals] = useState<WorkflowApproval[]>([])
  const [loading, setLoading] = useState(true)
  const [showEditor, setShowEditor] = useState(false)
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [triggerType, setTriggerType] = useState('manual')
  const [schedule, setSchedule] = useState('')
  const [steps, setSteps] = useState<Array<{ type: string; name: string; config: Record<string, any> }>>([])
  const [stepType, setStepType] = useState('action')
  const [stepName, setStepName] = useState('')
  const [stepTool, setStepTool] = useState('')
  const [stepArgs, setStepArgs] = useState('')

  const load = useCallback(async () => {
    try {
      const [wfRes, appRes] = await Promise.all([
        api.getWorkflows(undefined, 50),
        api.getApprovals('pending'),
      ])
      setWorkflows(wfRes.workflows || [])
      setApprovals(appRes.approvals || [])
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [load])

  const handleCreate = async () => {
    if (!name.trim()) return
    const payload = {
      name,
      description,
      trigger: { type: triggerType, schedule: triggerType === 'scheduled' || triggerType === 'recurring' ? schedule : undefined },
      steps: steps.map((s, i) => ({
        step_id: `step_${i}`,
        type: s.type,
        name: s.name,
        config: s.config,
        order: i,
        next_step_id: i < steps.length - 1 ? `step_${i + 1}` : null,
      })),
      enabled: false,
      status: 'draft',
    }
    try {
      await api.createWorkflow(payload)
      setShowEditor(false)
      setName('')
      setDescription('')
      setTriggerType('manual')
      setSchedule('')
      setSteps([])
      load()
    } catch {
      // ignore
    }
  }

  const addStep = () => {
    if (!stepName.trim()) return
    const config: Record<string, any> = {}
    if (stepType === 'action') {
      config.tool = stepTool
      try {
        config.arguments = JSON.parse(stepArgs || '{}')
      } catch {
        config.arguments = {}
      }
    }
    setSteps([...steps, { type: stepType, name: stepName, config }])
    setStepName('')
    setStepTool('')
    setStepArgs('')
  }

  const toggleWorkflow = async (wf: Workflow) => {
    try {
      if (wf.enabled) {
        await api.pauseWorkflow(wf.workflow_id)
      } else {
        await api.updateWorkflow(wf.workflow_id, { status: 'active', enabled: true })
      }
      load()
    } catch {
      // ignore
    }
  }

  const runNow = async (wf: Workflow) => {
    try {
      await api.runWorkflow(wf.workflow_id)
    } catch {
      // ignore
    }
  }

  const deleteWorkflow = async (wf: Workflow) => {
    try {
      await api.deleteWorkflow(wf.workflow_id)
      load()
    } catch {
      // ignore
    }
  }

  const viewRuns = async (wf: Workflow) => {
    try {
      const res = await api.getWorkflowRuns(wf.workflow_id, 20)
      setRuns(res.runs || [])
      setSelectedWorkflow(wf)
    } catch {
      // ignore
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-emerald-400'
      case 'paused': return 'text-yellow-400'
      case 'running': return 'text-cyan-400'
      case 'failed': return 'text-red-400'
      case 'completed': return 'text-emerald-400'
      case 'draft': return 'text-slate-400'
      default: return 'text-slate-400'
    }
  }

  if (showEditor) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400">New Workflow</h2>
          <button
            onClick={() => setShowEditor(false)}
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-900/50 border border-slate-700/50 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-500/50"
              placeholder="Workflow name"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-900/50 border border-slate-700/50 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-500/50"
              rows={2}
              placeholder="What this workflow does"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Trigger</label>
              <select
                value={triggerType}
                onChange={(e) => setTriggerType(e.target.value)}
                className="w-full bg-slate-900/50 border border-slate-700/50 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-500/50"
              >
                <option value="manual">Manual</option>
                <option value="scheduled">Scheduled</option>
                <option value="recurring">Recurring</option>
                <option value="event_based">Event Based</option>
                <option value="one_time">One Time</option>
              </select>
            </div>
            {(triggerType === 'scheduled' || triggerType === 'recurring') && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">Schedule (HH:MM)</label>
                <input
                  value={schedule}
                  onChange={(e) => setSchedule(e.target.value)}
                  className="w-full bg-slate-900/50 border border-slate-700/50 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-500/50"
                  placeholder="09:00"
                />
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-2">Steps</label>
            <div className="space-y-2">
              {steps.map((step, idx) => (
                <div key={idx} className="bg-slate-900/30 border border-slate-700/30 rounded px-3 py-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">{idx + 1}. {step.name}</span>
                    <span className="text-slate-500">{step.type}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2">
              <select
                value={stepType}
                onChange={(e) => setStepType(e.target.value)}
                className="bg-slate-900/50 border border-slate-700/50 rounded px-2 py-1 text-xs focus:outline-none focus:border-cyan-500/50"
              >
                <option value="action">Action</option>
                <option value="browser">Browser</option>
                <option value="computer">Computer</option>
                <option value="research">Research</option>
                <option value="document">Document</option>
                <option value="notification">Notification</option>
                <option value="delay">Delay</option>
              </select>
              <input
                value={stepName}
                onChange={(e) => setStepName(e.target.value)}
                className="bg-slate-900/50 border border-slate-700/50 rounded px-2 py-1 text-xs focus:outline-none focus:border-cyan-500/50"
                placeholder="Step name"
              />
            </div>
            {stepType === 'action' && (
              <div className="mt-2 grid grid-cols-2 gap-2">
                <input
                  value={stepTool}
                  onChange={(e) => setStepTool(e.target.value)}
                  className="bg-slate-900/50 border border-slate-700/50 rounded px-2 py-1 text-xs focus:outline-none focus:border-cyan-500/50"
                  placeholder="Tool name"
                />
                <input
                  value={stepArgs}
                  onChange={(e) => setStepArgs(e.target.value)}
                  className="bg-slate-900/50 border border-slate-700/50 rounded px-2 py-1 text-xs focus:outline-none focus:border-cyan-500/50"
                  placeholder='{"key": "value"}'
                />
              </div>
            )}
            <button
              onClick={addStep}
              className="mt-2 w-full bg-slate-800 hover:bg-slate-700 border border-slate-700/50 rounded px-3 py-1 text-xs text-slate-300 transition-all"
            >
              Add Step
            </button>
          </div>

          <button
            onClick={handleCreate}
            disabled={!name.trim()}
            className="w-full bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/40 rounded px-4 py-2 text-sm text-cyan-300 transition-all disabled:opacity-50"
          >
            Create Workflow
          </button>
        </div>
      </div>
    )
  }

  if (selectedWorkflow && runs.length > 0) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400">History</h2>
            <p className="text-xs text-slate-500 mt-0.5">{selectedWorkflow.name}</p>
          </div>
          <button
            onClick={() => { setSelectedWorkflow(null); setRuns([]) }}
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            Back
          </button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2">
          {runs.map((run) => (
            <div key={run.run_id} className="bg-slate-900/30 border border-slate-700/30 rounded px-3 py-2">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-medium ${statusColor(run.status)}`}>{run.status}</span>
                <span className="text-[10px] text-slate-500">{run.started_at}</span>
              </div>
              {(run.errors?.length ?? 0) > 0 && (
                <div className="mt-1 text-[10px] text-red-400">
                  {(run.errors || []).map((e: any, i: number) => (
                    <div key={i}>{e.error || JSON.stringify(e)}</div>
                  ))}
                </div>
              )}
            </div>
          ))}
          {runs.length === 0 && (
            <p className="text-xs text-slate-500 text-center py-8">No runs yet</p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400">Workflows</h2>
        <button
          onClick={() => setShowEditor(true)}
          className="text-xs bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/40 rounded px-3 py-1.5 text-cyan-300 transition-all"
        >
          + New
        </button>
      </div>

      {approvals.length > 0 && (
        <div className="mb-4 space-y-2">
          <h3 className="text-xs font-medium text-yellow-400 uppercase tracking-wider">Pending Approvals</h3>
          {approvals.map((appr) => (
            <div key={appr.approval_id} className="bg-yellow-500/10 border border-yellow-500/30 rounded px-3 py-2">
              <p className="text-xs text-yellow-200">{appr.action}</p>
              <p className="text-[10px] text-yellow-400/70 mt-0.5">Risk: {appr.risk_level}</p>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-xs text-slate-500">Loading...</div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2">
          {workflows.map((wf) => (
            <div
              key={wf.workflow_id}
              className="bg-slate-900/30 border border-slate-700/30 rounded px-3 py-2.5 hover:border-cyan-500/20 transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-200 truncate">{wf.name}</span>
                    <span className={`text-[10px] uppercase tracking-wider ${statusColor(wf.status)}`}>{wf.status}</span>
                  </div>
                  {wf.description && <p className="text-[11px] text-slate-500 mt-0.5 truncate">{wf.description}</p>}
                  {wf.trigger?.schedule && <p className="text-[10px] text-cyan-400/70 mt-0.5">Schedule: {wf.trigger.schedule}</p>}
                </div>
                <button
                  onClick={() => toggleWorkflow(wf)}
                  className={`ml-2 w-8 h-4 rounded-full transition-all ${wf.enabled ? 'bg-emerald-500/30' : 'bg-slate-700/50'}`}
                >
                  <div className={`w-3 h-3 rounded-full transition-all ${wf.enabled ? 'translate-x-4 bg-emerald-400' : 'translate-x-0.5 bg-slate-400'}`} />
                </button>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <button onClick={() => runNow(wf)} className="text-[10px] bg-slate-800 hover:bg-slate-700 border border-slate-700/50 rounded px-2 py-1 text-slate-300 transition-all">Run</button>
                <button onClick={() => viewRuns(wf)} className="text-[10px] bg-slate-800 hover:bg-slate-700 border border-slate-700/50 rounded px-2 py-1 text-slate-300 transition-all">History</button>
                <button onClick={() => setSelectedWorkflow(wf)} className="text-[10px] bg-slate-800 hover:bg-slate-700 border border-slate-700/50 rounded px-2 py-1 text-slate-300 transition-all">Edit</button>
                <button onClick={() => deleteWorkflow(wf)} className="text-[10px] bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded px-2 py-1 text-red-300 transition-all">Delete</button>
              </div>
            </div>
          ))}
          {workflows.length === 0 && (
            <div className="text-center py-12">
              <p className="text-xs text-slate-500 mb-2">No workflows yet</p>
              <button onClick={() => setShowEditor(true)} className="text-xs text-cyan-400 hover:text-cyan-300">Create your first workflow</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
