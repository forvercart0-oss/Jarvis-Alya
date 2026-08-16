import { BookOpen, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import type { ResearchJob } from '../../types'

interface ResearchHistoryProps {
  jobs: ResearchJob[]
  onSelect: (job: ResearchJob) => void
  onRefresh: () => void
}

const STATUS_ICONS: Record<string, React.ReactNode> = {
  completed: <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />,
  failed: <XCircle className="w-3.5 h-3.5 text-red-400" />,
  running: <Loader2 className="w-3.5 h-3.5 text-yellow-400 animate-spin" />,
  queued: <Loader2 className="w-3.5 h-3.5 text-slate-400" />,
  cancelled: <XCircle className="w-3.5 h-3.5 text-slate-500" />,
}

export function ResearchHistory({ jobs, onSelect, onRefresh }: ResearchHistoryProps) {
  const formatDate = (ts: number) => {
    const d = new Date(ts)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const days = Math.floor(diff / 86400000)
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    return d.toLocaleDateString()
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-red-500/10">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-red-400/70" />
          <span className="text-[11px] tracking-[0.2em] text-red-400/70 uppercase font-medium">Research</span>
        </div>
        <button onClick={onRefresh} className="text-[10px] text-slate-500 hover:text-red-300 transition-colors uppercase tracking-wider">
          Refresh
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {jobs.length === 0 && (
          <div className="text-xs text-slate-600 text-center py-8">No research yet</div>
        )}
        {jobs.map((job) => (
          <button
            key={job.id}
            onClick={() => onSelect(job)}
            className="w-full text-left p-3 rounded-lg bg-black/20 hover:bg-red-500/5 border border-transparent hover:border-red-500/20 transition-all group"
          >
            <div className="flex items-start gap-2">
              <div className="mt-0.5">{STATUS_ICONS[job.status] || STATUS_ICONS.queued}</div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-slate-300 font-medium truncate group-hover:text-red-200 transition-colors">
                  {job.topic}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-slate-600">{formatDate(job.started_at)}</span>
                  <span className={`text-[10px] uppercase tracking-wider ${job.status === 'completed' ? 'text-green-400' : job.status === 'failed' ? 'text-red-400' : 'text-slate-600'}`}>
                    {job.status}
                  </span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
