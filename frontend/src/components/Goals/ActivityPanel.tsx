import { useState, useEffect } from 'react'
import { Activity } from 'lucide-react'

interface ActivityEntry {
  timestamp: string
  event: string
  detail: string
  type: 'info' | 'success' | 'error' | 'warning'
}

export function ActivityPanel() {
  const [activities, setActivities] = useState<ActivityEntry[]>([])

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/jarvis`
    const socket = new WebSocket(wsUrl)

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const entry: ActivityEntry = {
          timestamp: new Date().toLocaleTimeString(),
          event: data.event || 'unknown',
          detail: data.data?.message || data.data?.request || JSON.stringify(data.data || {}).slice(0, 100),
          type: data.event?.includes('failed') || data.event?.includes('error') ? 'error' :
               data.event?.includes('completed') || data.event?.includes('success') ? 'success' :
               data.event?.includes('started') ? 'info' : 'warning',
        }
        setActivities((prev) => [entry, ...prev].slice(0, 50))
      } catch {
        // ignore
      }
    }

    return () => { socket.close() }
  }, [])

  const typeColor = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-400'
      case 'error': return 'text-red-400'
      case 'warning': return 'text-yellow-400'
      default: return 'text-cyan-400'
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <Activity className="w-3.5 h-3.5 text-cyan-400/70" />
        <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Activity</span>
      </div>
      <div className="flex-1 overflow-y-auto space-y-1">
        {activities.length === 0 && (
          <div className="text-xs text-slate-600 py-4 text-center">No activity yet</div>
        )}
        {activities.map((a, i) => (
          <div key={i} className="flex items-start gap-2 text-[10px]">
            <span className="text-slate-600 font-mono shrink-0">{a.timestamp}</span>
            <span className={`${typeColor(a.type)} flex-1`}>{a.detail}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
