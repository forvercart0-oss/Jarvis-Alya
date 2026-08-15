import { useState } from 'react'
import { ImageIcon, VideoIcon, Sparkles } from 'lucide-react'
import { api } from '../../services/api'

interface MediaGenerationPanelProps {
  settings: any
  onUpdate: (patch: any) => void
}

export function MediaGenerationPanel({ settings }: MediaGenerationPanelProps) {
  const [tab, setTab] = useState<'images' | 'videos'>('images')
  const [imagePrompt, setImagePrompt] = useState('')
  const [videoPrompt, setVideoPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handleImageGenerate = async () => {
    if (!imagePrompt.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await api.generateImage(imagePrompt, settings.image_provider)
      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Image generation failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleVideoGenerate = async () => {
    if (!videoPrompt.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await api.generateVideo(videoPrompt, settings.video_provider)
      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Video generation failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-500/10">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm tracking-[0.2em] text-cyan-400/70 uppercase">Media Generation</h2>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="flex gap-2">
          <button
            onClick={() => setTab('images')}
            className={`flex-1 py-2 text-xs tracking-wider uppercase rounded border transition-colors ${
              tab === 'images' ? 'border-cyan-400/40 text-cyan-300 bg-cyan-500/10' : 'border-slate-700 text-slate-500 hover:text-slate-300'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5 inline mr-1" />
            Images
          </button>
          <button
            onClick={() => setTab('videos')}
            className={`flex-1 py-2 text-xs tracking-wider uppercase rounded border transition-colors ${
              tab === 'videos' ? 'border-cyan-400/40 text-cyan-300 bg-cyan-500/10' : 'border-slate-700 text-slate-500 hover:text-slate-300'
            }`}
          >
            <VideoIcon className="w-3.5 h-3.5 inline mr-1" />
            Videos
          </button>
        </div>

        {tab === 'images' && (
          <div className="space-y-3">
            <textarea
              value={imagePrompt}
              onChange={(e) => setImagePrompt(e.target.value)}
              placeholder="Describe the image you want to generate..."
              className="w-full h-24 bg-black/30 border border-cyan-500/20 rounded p-3 text-xs text-slate-200 placeholder:text-slate-600 resize-none focus:outline-none focus:border-cyan-400/40"
            />
            <button
              onClick={handleImageGenerate}
              disabled={loading}
              className="w-full py-2 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 disabled:opacity-50 transition-all"
            >
              {loading ? 'Generating...' : 'Generate Image'}
            </button>
          </div>
        )}

        {tab === 'videos' && (
          <div className="space-y-3">
            <textarea
              value={videoPrompt}
              onChange={(e) => setVideoPrompt(e.target.value)}
              placeholder="Describe the video you want to generate..."
              className="w-full h-24 bg-black/30 border border-cyan-500/20 rounded p-3 text-xs text-slate-200 placeholder:text-slate-600 resize-none focus:outline-none focus:border-cyan-400/40"
            />
            <button
              onClick={handleVideoGenerate}
              disabled={loading}
              className="w-full py-2 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 disabled:opacity-50 transition-all"
            >
              {loading ? 'Generating...' : 'Generate Video'}
            </button>
          </div>
        )}

        {error && (
          <div className="text-xs text-red-400 bg-red-500/10 border border-red-400/30 rounded p-2">
            {error}
          </div>
        )}

        {result && (
          <div className="glass-panel p-3 space-y-2">
            <div className="text-[10px] tracking-wider uppercase text-slate-500">Result</div>
            <pre className="text-[10px] text-slate-400 whitespace-pre-wrap break-all">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
