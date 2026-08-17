import { useState, useEffect, useCallback } from 'react'
import { Monitor, Maximize, Crop, Search, Type, MousePointerClick, Keyboard, Scan, Check, Eye } from 'lucide-react'
import { api } from '../../services/api'

interface VisionPanelProps {
  onNavigate?: (tab: string) => void
}

export function VisionPanel(_props: VisionPanelProps) {
  const [visionEnabled, setVisionEnabled] = useState(false)
  const [activeWindow, setActiveWindow] = useState<any>(null)
  const [screenInfo, setScreenInfo] = useState<any>(null)
  const [monitors, setMonitors] = useState<any[]>([])
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [target, setTarget] = useState('')
  const [targetResult, setTargetResult] = useState<any>(null)
  const [ocrText, setOcrText] = useState('')
  const [actionResult, setActionResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [imageA, setImageA] = useState('')
  const [imageB, setImageB] = useState('')
  const [compareResult, setCompareResult] = useState<any>(null)

  const refreshStatus = useCallback(async () => {
    try {
      const status = await api.getVisionStatus()
      setVisionEnabled(status.enabled)
    } catch {
      // ignore
    }
  }, [])

  const refreshWindow = useCallback(async () => {
    try {
      const w = await api.visionActiveWindow()
      setActiveWindow(w)
    } catch {
      // ignore
    }
  }, [])

  const refreshScreen = useCallback(async () => {
    try {
      const s = await api.visionScreenInfo()
      setScreenInfo(s)
    } catch {
      // ignore
    }
  }, [])

  const refreshMonitors = useCallback(async () => {
    try {
      const m = await api.visionMonitors()
      setMonitors(m.monitors || [])
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    refreshStatus()
    refreshWindow()
    refreshScreen()
    refreshMonitors()
  }, [refreshStatus, refreshWindow, refreshScreen, refreshMonitors])

  const handleScreenshot = async (mode: string) => {
    setLoading(true)
    setError(null)
    setAnalysis(null)
    try {
      const result = await api.visionScreenshot(mode)
      if (result.ok || result.success) {
        const analyze = await api.visionAnalyze(result.path || '', 'describe')
        setAnalysis(analyze)
      } else {
        setError(result.error || 'Screenshot failed')
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFind = async () => {
    if (!target.trim()) return
    setLoading(true)
    setError(null)
    setTargetResult(null)
    try {
      const result = await api.visionFind(target.trim())
      setTargetResult(result)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleOcr = async () => {
    setLoading(true)
    setError(null)
    setOcrText('')
    try {
      const result = await api.visionScreenshot('full')
      if (result.ok || result.success) {
        const ocr = await api.visionOcr(result.path || '')
        setOcrText(ocr.text || '')
      } else {
        setError(result.error || 'OCR failed')
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (action: string, args: any) => {
    setLoading(true)
    setError(null)
    setActionResult(null)
    try {
      let result: any = {}
      switch (action) {
        case 'click':
          result = await api.visionMouseClick(args.x, args.y, args.button)
          break
        case 'double_click':
          result = await api.visionMouseDoubleClick(args.x, args.y)
          break
        case 'drag':
          result = await api.visionMouseDrag(args.x1, args.y1, args.x2, args.y2)
          break
        case 'scroll':
          result = await api.visionMouseScroll(args.x, args.y, args.direction, args.amount)
          break
        case 'type':
          result = await api.visionKeyboardType(args.text)
          break
        case 'hotkey':
          result = await api.visionKeyboardHotkey(args.keys)
          break
        case 'press':
          result = await api.visionKeyboardPress(args.key)
          break
      }
      setActionResult(result)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-y-auto">
      <div className="flex items-center gap-2">
        <Eye className="w-4 h-4" style={{ color: 'var(--accent-color, #00f0ff)' }} />
        <span className="text-xs tracking-[0.2em] uppercase" style={{ color: 'var(--accent-color, #00f0ff)' }}>
          Vision
        </span>
        <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full ${visionEnabled ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'}`}>
          {visionEnabled ? '● ACTIVE' : '○ OFF'}
        </span>
      </div>

      {error && (
        <div className="glass-panel p-3 text-xs text-red-400 border-red-400/30">
          {error}
        </div>
      )}

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Screen Capture</div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => handleScreenshot('full')} disabled={loading} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            <Maximize className="w-3 h-3 inline mr-1" />Full Screen
          </button>
          <button onClick={() => handleScreenshot('window')} disabled={loading} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            <Monitor className="w-3 h-3 inline mr-1" />Active Window
          </button>
          <button onClick={() => handleScreenshot('region')} disabled={loading} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            <Crop className="w-3 h-3 inline mr-1" />Region
          </button>
          <button onClick={handleOcr} disabled={loading} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            <Scan className="w-3 h-3 inline mr-1" />OCR
          </button>
        </div>
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Active Window</div>
        {activeWindow && (
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-500">App</span>
              <span className="text-slate-300 font-mono">{activeWindow.app || '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Title</span>
              <span className="text-slate-300 font-mono truncate max-w-[180px]">{activeWindow.title || '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Size</span>
              <span className="text-slate-300 font-mono">{activeWindow.width}x{activeWindow.height}</span>
            </div>
          </div>
        )}
        {!activeWindow && <div className="text-xs text-slate-600">No active window info</div>}
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Screen Info</div>
        {screenInfo && (
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Resolution</span>
              <span className="text-slate-300 font-mono">{screenInfo.width}x{screenInfo.height}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Monitors</span>
              <span className="text-slate-300 font-mono">{monitors.length}</span>
            </div>
          </div>
        )}
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Find Target</div>
        <div className="flex gap-2">
          <input
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Login button..."
            className="flex-1 px-2 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50"
            onKeyDown={(e) => e.key === 'Enter' && handleFind()}
          />
          <button onClick={handleFind} disabled={loading || !target.trim()} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            <Search className="w-3 h-3" />
          </button>
        </div>
        {targetResult && (
          <div className="text-xs space-y-1 mt-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Found</span>
              <span className={targetResult.found ? 'text-emerald-400' : 'text-red-400'}>{targetResult.found ? 'Yes' : 'No'}</span>
            </div>
            {targetResult.found && (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-500">Position</span>
                  <span className="text-slate-300 font-mono">{targetResult.x}, {targetResult.y}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Confidence</span>
                  <span className="text-slate-300 font-mono">{(targetResult.confidence * 100).toFixed(0)}%</span>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Analysis</div>
        {analysis && (
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Mode</span>
              <span className="text-slate-300 font-mono">{analysis.mode || 'describe'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Latency</span>
              <span className="text-slate-300 font-mono">{analysis.latency_ms ?? '--'}ms</span>
            </div>
            {analysis.description && (
              <div className="text-slate-300 mt-1">{analysis.description}</div>
            )}
            {analysis.text && (
              <div className="text-slate-300 mt-1 whitespace-pre-wrap font-mono text-[10px]">{analysis.text}</div>
            )}
          </div>
        )}
        {!analysis && !loading && <div className="text-xs text-slate-600">Capture a screen to analyze</div>}
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">OCR Result</div>
        {ocrText ? (
          <div className="text-xs text-slate-300 whitespace-pre-wrap font-mono max-h-40 overflow-y-auto">{ocrText}</div>
        ) : (
          <div className="text-xs text-slate-600">No OCR result yet</div>
        )}
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Camera</div>
        <div className="flex gap-2">
          <button onClick={async () => { setLoading(true); try { await api.visionCameraStart() } finally { setLoading(false) } }} disabled={loading} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            Start Camera
          </button>
          <button onClick={async () => { setLoading(true); try { await api.visionCameraStop() } finally { setLoading(false) } }} disabled={loading} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            Stop Camera
          </button>
          <button onClick={async () => { setLoading(true); try { await api.visionCameraCapture() } finally { setLoading(false) } }} disabled={loading} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            Capture
          </button>
        </div>
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Image Compare</div>
        <div className="flex gap-2">
          <input
            type="text"
            value={imageA}
            onChange={(e) => setImageA(e.target.value)}
            placeholder="Image A path"
            className="flex-1 px-2 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50"
          />
          <input
            type="text"
            value={imageB}
            onChange={(e) => setImageB(e.target.value)}
            placeholder="Image B path"
            className="flex-1 px-2 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50"
          />
          <button onClick={async () => { setLoading(true); setError(null); try { const res = await api.visionCompare(imageA, imageB); setCompareResult(res) } catch (err: any) { setError(err.message) } finally { setLoading(false) } }} disabled={loading || !imageA || !imageB} className="px-3 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50">
            Compare
          </button>
        </div>
        {compareResult && (
          <div className="text-xs space-y-1 mt-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Identical</span>
              <span className={compareResult.identical ? 'text-emerald-400' : 'text-yellow-400'}>{compareResult.identical ? 'Yes' : 'No'}</span>
            </div>
            {compareResult.difference && (
              <div className="text-slate-400">{compareResult.difference}</div>
            )}
          </div>
        )}
      </div>

      <div className="glass-panel p-3 space-y-2">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Quick Actions</div>
        <div className="grid grid-cols-2 gap-2">
          <button onClick={() => handleAction('click', { x: 500, y: 500 })} disabled={loading} className="px-2 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50 flex items-center gap-1">
            <MousePointerClick className="w-3 h-3" />Click
          </button>
          <button onClick={() => handleAction('type', { text: 'Hello' })} disabled={loading} className="px-2 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50 flex items-center gap-1">
            <Type className="w-3 h-3" />Type
          </button>
          <button onClick={() => handleAction('hotkey', { keys: ['ctrl', 'c'] })} disabled={loading} className="px-2 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50 flex items-center gap-1">
            <Keyboard className="w-3 h-3" />Hotkey
          </button>
          <button onClick={() => handleAction('scroll', { x: 500, y: 500, direction: 'down', amount: 3 })} disabled={loading} className="px-2 py-1.5 text-[10px] bg-slate-800 border border-slate-600/30 rounded hover:bg-slate-700 transition-all disabled:opacity-50 flex items-center gap-1">
            <MousePointerClick className="w-3 h-3" />Scroll
          </button>
        </div>
        {actionResult && (
          <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
            <Check className="w-3 h-3" /> Action completed
          </div>
        )}
      </div>

      {loading && (
        <div className="text-[10px] text-cyan-400 animate-pulse tracking-wider uppercase">Processing...</div>
      )}
    </div>
  )
}
