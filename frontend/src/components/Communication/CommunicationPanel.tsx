import { useState, useEffect, useCallback } from 'react'
import { MessageSquare, Inbox, Send, Users, Calendar, Settings } from 'lucide-react'
import { Button } from '../../components/Common/Button'
import { Input } from '../../components/Common/Input'
import { api } from '../../services/api'

interface CommunicationPanelProps {
  onNavigate: (tab: any) => void
}

export function CommunicationPanel({ onNavigate: _onNavigate }: CommunicationPanelProps) {
  const [status, setStatus] = useState<{ enabled: boolean; providers: any[] } | null>(null)
  const [inbox, setInbox] = useState<any[]>([])
  const [contacts, setContacts] = useState<any[]>([])
  const [scheduled, setScheduled] = useState<any[]>([])
  const [logs, setLogs] = useState<string[]>([])
  const [tab, setTab] = useState<'inbox' | 'contacts' | 'scheduled' | 'settings'>('inbox')
  const [goal, setGoal] = useState('')

  const addLog = useCallback((msg: string) => {
    setLogs((prev) => [...prev.slice(-100), `[${new Date().toLocaleTimeString()}] ${msg}`])
  }, [])

  const refreshStatus = useCallback(async () => {
    try {
      const res = await api.getCommunicationStatus()
      if (res) setStatus(res)
    } catch { /* ignore */ }
  }, [])

  const refreshInbox = useCallback(async () => {
    try {
      const res = await api.getCommunicationInbox()
      if (res?.success) setInbox(res.inbox || [])
    } catch { /* ignore */ }
  }, [])

  const refreshContacts = useCallback(async () => {
    try {
      const res = await api.getContacts()
      if (res?.success) setContacts(res.contacts || [])
    } catch { /* ignore */ }
  }, [])

  const refreshScheduled = useCallback(async () => {
    try {
      const res = await api.getScheduledMessages()
      if (res?.success) setScheduled(res.scheduled || [])
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    refreshStatus()
    refreshInbox()
    refreshContacts()
    refreshScheduled()
    const timer = setInterval(() => {
      refreshStatus()
      if (tab === 'inbox') refreshInbox()
    }, 5000)
    return () => clearInterval(timer)
  }, [tab, refreshStatus, refreshInbox, refreshContacts, refreshScheduled])

  const handleGoal = async () => {
    if (!goal.trim()) return
    addLog(`Processing: ${goal}`)
    try {
      const res = await api.communicationTask(goal.trim())
      if (res?.success) {
        addLog(`Intent: ${res.intent?.intent || 'unknown'}`)
        addLog(`Actions: ${res.actions?.length || 0}`)
      } else {
        addLog(`Failed: ${res?.error || 'Unknown'}`)
      }
    } catch (err) {
      addLog(`Error: ${err instanceof Error ? err.message : 'Unknown'}`)
    }
    setGoal('')
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-medium text-slate-200">Communication</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${status?.enabled ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <span className="text-xs text-slate-400">{status?.enabled ? 'Connected' : 'Disabled'}</span>
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        <Button size="sm" variant={tab === 'inbox' ? 'primary' : 'secondary'} onClick={() => setTab('inbox')}>
          <Inbox className="w-3.5 h-3.5" />
        </Button>
        <Button size="sm" variant={tab === 'contacts' ? 'primary' : 'secondary'} onClick={() => setTab('contacts')}>
          <Users className="w-3.5 h-3.5" />
        </Button>
        <Button size="sm" variant={tab === 'scheduled' ? 'primary' : 'secondary'} onClick={() => setTab('scheduled')}>
          <Calendar className="w-3.5 h-3.5" />
        </Button>
        <Button size="sm" variant={tab === 'settings' ? 'primary' : 'secondary'} onClick={() => setTab('settings')}>
          <Settings className="w-3.5 h-3.5" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Command</label>
          <div className="flex gap-2">
            <Input
              value={goal}
              onChange={setGoal}
              onKeyDown={(e) => e.key === 'Enter' && handleGoal()}
              placeholder="Check my messages, send email, call Ali..."
              className="flex-1"
            />
            <Button size="sm" onClick={handleGoal} disabled={!goal.trim()}>
              <Send className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        {tab === 'inbox' && (
          <div className="glass-panel p-3 space-y-2">
            <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Inbox</label>
            {inbox.length === 0 ? (
              <p className="text-xs text-slate-500">No messages</p>
            ) : (
              <div className="space-y-1">
                {inbox.slice(0, 10).map((item, idx) => (
                  <div key={idx} className="text-xs text-slate-300 p-2 rounded bg-slate-800/50">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{item.sender || item.title || 'Unknown'}</span>
                      <span className="text-[10px] text-slate-500">{item.last_timestamp || ''}</span>
                    </div>
                    <p className="text-[10px] text-slate-400 truncate">{item.last_message || ''}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'contacts' && (
          <div className="glass-panel p-3 space-y-2">
            <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Contacts</label>
            {contacts.length === 0 ? (
              <p className="text-xs text-slate-500">No contacts</p>
            ) : (
              <div className="space-y-1">
                {contacts.slice(0, 10).map((contact, idx) => (
                  <div key={idx} className="text-xs text-slate-300 p-2 rounded bg-slate-800/50">
                    <span className="font-medium">{contact.name}</span>
                    <span className="text-[10px] text-slate-500 ml-2">{contact.tags?.join(', ') || ''}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'scheduled' && (
          <div className="glass-panel p-3 space-y-2">
            <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Scheduled Messages</label>
            {scheduled.length === 0 ? (
              <p className="text-xs text-slate-500">No scheduled messages</p>
            ) : (
              <div className="space-y-1">
                {scheduled.slice(0, 10).map((msg, idx) => (
                  <div key={idx} className="text-xs text-slate-300 p-2 rounded bg-slate-800/50">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{msg.recipient}</span>
                      <span className="text-[10px] text-slate-500">{msg.schedule_time}</span>
                    </div>
                    <p className="text-[10px] text-slate-400 truncate">{msg.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'settings' && status?.providers && (
          <div className="glass-panel p-3 space-y-2">
            <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Providers</label>
            {status.providers.map((provider, idx) => (
              <div key={idx} className="text-xs text-slate-300 p-2 rounded bg-slate-800/50 flex items-center justify-between">
                <span className="font-medium">{provider.name}</span>
                <span className={`text-[10px] ${provider.health?.status === 'online' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {provider.health?.status || 'unknown'}
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="glass-panel p-3 space-y-2">
          <label className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Activity Log</label>
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {logs.map((log, idx) => (
              <div key={idx} className="text-[10px] text-slate-500 font-mono break-all">{log}</div>
            ))}
            {logs.length === 0 && <p className="text-[10px] text-slate-600">No activity yet</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
