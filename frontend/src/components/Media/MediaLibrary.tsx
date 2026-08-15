import { useState, useEffect } from 'react'
import { ImageIcon, VideoIcon, Trash2, FolderOpen, RefreshCw } from 'lucide-react'
import { api } from '../../services/api'

interface MediaHistoryItem {
  id: string
  type: 'image' | 'video'
  prompt: string
  provider: string
  date: string
  path?: string
  url?: string
}

interface MediaLibraryProps {
  settings: any
}

export function MediaLibrary({ settings }: MediaLibraryProps) {
  const [items, setItems] = useState<MediaHistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState<'all' | 'images' | 'videos'>('all')

  const loadHistory = async () => {
    setLoading(true)
    try {
      const data = await api.getDiagnostics()
      const history: MediaHistoryItem[] = []
      if (data.image && Array.isArray(data.image)) {
        data.image.forEach((img: any) => {
          history.push({
            id: img.id || `img-${Date.now()}-${Math.random()}`,
            type: 'image',
            prompt: img.prompt || '',
            provider: img.provider || 'unknown',
            date: img.date || new Date().toISOString(),
            url: img.url,
          })
        })
      }
      if (data.video && Array.isArray(data.video)) {
        data.video.forEach((vid: any) => {
          history.push({
            id: vid.id || `vid-${Date.now()}-${Math.random()}`,
            type: 'video',
            prompt: vid.prompt || '',
            provider: vid.provider || 'unknown',
            date: vid.date || new Date().toISOString(),
            url: vid.url,
          })
        })
      }
      setItems(history)
    } catch {
      // Media history not available yet
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const filtered = items.filter(item => {
    if (filter === 'all') return true
    return item.type === filter.slice(0, -1)
  })

  const handleDelete = async (id: string) => {
    setItems(items.filter(item => item.id !== id))
  }

  const handleOpen = (url?: string) => {
    if (url) {
      window.open(url, '_blank')
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-500/10">
        <h2 className="text-sm tracking-[0.2em] text-cyan-400/70 uppercase">Media Library</h2>
        <button
          onClick={loadHistory}
          disabled={loading}
          className="text-[10px] tracking-widest text-slate-500 hover:text-cyan-300 transition-colors uppercase flex items-center gap-1"
        >
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="flex gap-2">
          {[
            { id: 'all', label: 'All' },
            { id: 'images', label: 'Images' },
            { id: 'videos', label: 'Videos' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id as any)}
              className={`flex-1 py-2 text-xs tracking-wider uppercase rounded border transition-colors ${
                filter === tab.id
                  ? 'border-cyan-400/40 text-cyan-300 bg-cyan-500/10'
                  : 'border-slate-700 text-slate-500 hover:text-slate-300'
              }`}
            >
              {tab.id === 'all' ? <ImageIcon className="w-3.5 h-3.5 inline mr-1" /> :
               tab.id === 'images' ? <ImageIcon className="w-3.5 h-3.5 inline mr-1" /> :
               <VideoIcon className="w-3.5 h-3.5 inline mr-1" />}
              {tab.label}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <ImageIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-xs">No media generated yet.</p>
            <p className="text-[10px] mt-1">Generated images and videos will appear here.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {filtered.map((item) => (
              <div key={item.id} className="glass-panel p-2 space-y-2">
                <div className="aspect-video bg-black/30 rounded flex items-center justify-center overflow-hidden">
                  {item.url ? (
                    <img src={item.url} alt={item.prompt} className="w-full h-full object-cover" />
                  ) : (
                    <div className="text-slate-600">
                      {item.type === 'image' ? <ImageIcon className="w-8 h-8" /> : <VideoIcon className="w-8 h-8" />}
                    </div>
                  )}
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] text-slate-400 line-clamp-2">{item.prompt || 'No prompt'}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-600">{item.provider}</span>
                    <span className="text-[9px] text-slate-600">
                      {new Date(item.date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex gap-1">
                    {item.url && (
                      <button
                        onClick={() => handleOpen(item.url)}
                        className="flex-1 py-1 text-[9px] border border-cyan-500/20 rounded text-cyan-300 hover:bg-cyan-500/10 transition-colors"
                      >
                        Open
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="px-2 py-1 text-[9px] border border-red-500/20 rounded text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
