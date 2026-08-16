import { motion } from 'framer-motion'
import { X, Square, ExternalLink, FolderOpen, Copy, CheckCircle2, AlertTriangle } from 'lucide-react'
import type { ResearchJob } from '../../types'

interface ResearchPanelProps {
  job: ResearchJob
  onClose: () => void
  onCancel: () => void
  onOpenDocument: () => void
  onOpenFolder: () => void
  onCopyPath: () => void
}

const PHASE_LABELS: Record<string, string> = {
  understanding_query: 'Understanding query',
  searching_sources: 'Searching sources',
  collecting_evidence: 'Collecting evidence',
  cross_checking: 'Cross-checking information',
  analyzing_sources: 'Analyzing sources',
  writing_report: 'Writing report',
  saving_document: 'Saving document',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
  starting: 'Starting',
}

export function ResearchPanel({ job, onClose, onCancel, onOpenDocument, onOpenFolder, onCopyPath }: ResearchPanelProps) {
  const isRunning = job.status === 'running' || job.status === 'queued'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg glass-panel-strong p-6 border-red-500/30">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-red-500 serious-pulse" />
            <h2 className="text-sm tracking-[0.2em] text-red-400/90 uppercase font-medium">Deep Research</h2>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-6">
          <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-1">Topic</div>
          <div className="text-sm text-slate-200 font-medium">{job.topic}</div>
        </div>

        <div className="mb-6">
          <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-2">Status</div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${job.phase === 'understanding_query' || job.phase === 'starting' ? 'bg-red-400 animate-pulse' : 'bg-slate-700'}`} />
              <span className="text-xs text-slate-400">{PHASE_LABELS.understanding_query}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${job.phase === 'searching_sources' ? 'bg-red-400 animate-pulse' : 'bg-slate-700'}`} />
              <span className="text-xs text-slate-400">{PHASE_LABELS.searching_sources}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${job.phase === 'collecting_evidence' ? 'bg-red-400 animate-pulse' : 'bg-slate-700'}`} />
              <span className="text-xs text-slate-400">{PHASE_LABELS.collecting_evidence}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${job.phase === 'cross_checking' ? 'bg-red-400 animate-pulse' : 'bg-slate-700'}`} />
              <span className="text-xs text-slate-400">{PHASE_LABELS.cross_checking}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${job.phase === 'analyzing_sources' ? 'bg-red-400 animate-pulse' : 'bg-slate-700'}`} />
              <span className="text-xs text-slate-400">{PHASE_LABELS.analyzing_sources}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${job.phase === 'writing_report' ? 'bg-red-400 animate-pulse' : 'bg-slate-700'}`} />
              <span className="text-xs text-slate-400">{PHASE_LABELS.writing_report}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${job.phase === 'saving_document' ? 'bg-red-400 animate-pulse' : 'bg-slate-700'}`} />
              <span className="text-xs text-slate-400">{PHASE_LABELS.saving_document}</span>
            </div>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-3 gap-3">
          <div className="glass-panel p-3 text-center">
            <div className="text-lg font-mono text-red-400">{job.sources_found}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Sources Found</div>
          </div>
          <div className="glass-panel p-3 text-center">
            <div className="text-lg font-mono text-red-400">{job.sources_processed}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Processed</div>
          </div>
          <div className="glass-panel p-3 text-center">
            <div className="text-lg font-mono text-red-400">{job.claims_checked}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Claims</div>
          </div>
        </div>

        {job.status === 'completed' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/30"
          >
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-4 h-4 text-green-400" />
              <span className="text-xs text-green-400 font-medium">Research Complete</span>
            </div>
            {job.document_path && (
              <div className="text-xs text-slate-400 font-mono mb-3 break-all">{job.document_path}</div>
            )}
            <div className="flex gap-2">
              <button onClick={onOpenDocument} className="flex items-center gap-1 px-3 py-1.5 bg-red-500/15 border border-red-500/40 rounded text-xs text-red-200 hover:bg-red-500/25 transition-all">
                <ExternalLink className="w-3 h-3" />
                Open Document
              </button>
              <button onClick={onOpenFolder} className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all">
                <FolderOpen className="w-3 h-3" />
                Open Folder
              </button>
              <button onClick={onCopyPath} className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all">
                <Copy className="w-3 h-3" />
                Copy Path
              </button>
            </div>
          </motion.div>
        )}

        {job.status === 'failed' && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-xs text-red-400">Research failed: {job.error || 'Unknown error'}</span>
            </div>
          </div>
        )}

        {isRunning && (
          <button
            onClick={onCancel}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-300 hover:bg-red-500/20 transition-all"
          >
            <Square className="w-3 h-3" />
            STOP RESEARCH
          </button>
        )}
      </div>
    </motion.div>
  )
}
