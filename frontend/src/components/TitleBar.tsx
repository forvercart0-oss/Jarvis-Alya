import { useState, useEffect } from 'react'
import { Minus, Maximize2, X } from 'lucide-react'
import { getCurrentWindow } from '@tauri-apps/api/window'

const appWindow = getCurrentWindow()

function TitleBar() {
  const [isMaximized, setIsMaximized] = useState(false)
  const [isTauri, setIsTauri] = useState(false)

  useEffect(() => {
    setIsTauri(!!(window as any).__TAURI__)
  }, [])

  useEffect(() => {
    if (!isTauri) return
  }, [isTauri])

  if (!isTauri) return null

  const handleMinimize = async () => {
    try { await appWindow.minimize() } catch { /* ignore */ }
  }

  const handleMaximize = async () => {
    try {
      if (isMaximized) {
        await appWindow.unmaximize()
        setIsMaximized(false)
      } else {
        await appWindow.maximize()
        setIsMaximized(true)
      }
    } catch { /* ignore */ }
  }

  const handleClose = async () => {
    try { await appWindow.close() } catch { /* ignore */ }
  }

  return (
    <div
      data-tauri-drag-region
      className="h-8 bg-black/40 border-b border-cyan-500/10 flex items-center justify-between px-3 select-none"
    >
      <div className="flex items-center gap-2" data-tauri-drag-region>
        <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(0,240,255,0.5)]" data-tauri-drag-region />
        <span className="text-[10px] tracking-[0.2em] text-slate-400 uppercase" data-tauri-drag-region>
          JARVIS 2.0
        </span>
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={handleMinimize}
          className="w-7 h-6 flex items-center justify-center text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors rounded"
          title="Minimize"
        >
          <Minus className="w-3 h-3" />
        </button>
        <button
          onClick={handleMaximize}
          className="w-7 h-6 flex items-center justify-center text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors rounded"
          title={isMaximized ? 'Restore' : 'Maximize'}
        >
          <Maximize2 className="w-3 h-3" />
        </button>
        <button
          onClick={handleClose}
          className="w-7 h-6 flex items-center justify-center text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors rounded"
          title="Close"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
    </div>
  )
}

export default TitleBar
