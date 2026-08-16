import type { MemoryItem } from '../../types'
import { Download, Upload, AlertTriangle } from 'lucide-react'

interface MemoryManagementProps {
  memories: MemoryItem[]
  onRefresh: () => void
}

export function MemoryManagement({ memories, onRefresh }: MemoryManagementProps) {
  const handleExport = async () => {
    try {
      const blob = new Blob([JSON.stringify(memories, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `jarvis-memory-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch { /* ignore */ }
  }

  const handleImport = async () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'application/json'
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return
      try {
        const text = await file.text()
        const data = JSON.parse(text)
        if (!Array.isArray(data)) {
          alert('Invalid memory file format.')
          return
        }
        for (const item of data) {
          if (item.value && typeof item.value === 'string') {
            await fetch('/api/memory', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ content: item.value, category: item.category || 'general', project: item.project || '', profile: item.profile || 'jarvis' }),
            })
          }
        }
        onRefresh()
      } catch {
        alert('Failed to import memory file.')
      }
    }
    input.click()
  }

  const handleClear = async () => {
    if (!confirm('Delete ALL memories? This cannot be undone.')) return
    try {
      await fetch('/api/memory', { method: 'DELETE' })
      onRefresh()
    } catch { /* ignore */ }
  }

  return (
    <div className="space-y-4">
      <h4 className="text-xs tracking-widest text-slate-400 uppercase">Memory Management</h4>
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={handleExport}
          className="px-3 py-2 bg-slate-800/50 border border-slate-600/20 rounded text-[10px] text-slate-300 hover:bg-slate-800 transition-all flex items-center justify-center gap-1"
        >
          <Download className="w-3 h-3" /> Export
        </button>
        <button
          onClick={handleImport}
          className="px-3 py-2 bg-slate-800/50 border border-slate-600/20 rounded text-[10px] text-slate-300 hover:bg-slate-800 transition-all flex items-center justify-center gap-1"
        >
          <Upload className="w-3 h-3" /> Import
        </button>
      </div>
      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] text-slate-500">Total memories: {memories.length}</div>
        <button
          onClick={handleClear}
          className="w-full px-3 py-2 bg-red-500/10 border border-red-400/20 rounded text-[10px] text-red-300 hover:bg-red-400/20 transition-all flex items-center justify-center gap-1"
        >
          <AlertTriangle className="w-3 h-3" /> Clear All Memory
        </button>
      </div>
    </div>
  )
}
