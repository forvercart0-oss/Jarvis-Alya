import type { MemoryItem } from '../../types'

interface MemorySearchProps {
  query: string
  onQueryChange: (query: string) => void
  results: MemoryItem[]
  onSearch: () => void
}

export function MemorySearch({ query, onQueryChange, results, onSearch }: MemorySearchProps) {
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onSearch()}
          placeholder='Search memories...'
          className="flex-1 bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
        />
        <button
          onClick={onSearch}
          disabled={!query.trim()}
          className="px-3 py-1 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all disabled:opacity-50"
        >
          Search
        </button>
      </div>
      {results.length > 0 ? (
        <div className="space-y-2">
          {results.map((m) => (
            <div key={m.id} className="glass-panel p-3 space-y-1">
              <div className="text-xs text-slate-300 break-words">{m.value}</div>
              <div className="flex items-center gap-2 text-[10px] text-slate-600">
                <span>{m.category}</span>
                {m.project && <span>• {m.project}</span>}
                {m.confidence !== undefined && <span>• {Math.round(m.confidence * 100)}%</span>}
              </div>
            </div>
          ))}
        </div>
      ) : query ? (
        <div className="text-center text-slate-500 py-6">No results found.</div>
      ) : (
        <div className="text-center text-slate-500 py-6">Enter a query to search memories.</div>
      )}
    </div>
  )
}
