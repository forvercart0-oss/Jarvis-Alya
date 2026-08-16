import { useCallback, useEffect, useRef, useState } from 'react'
import type { OrbState, Message, ToolCall, SystemStats, JarvisSettings, MemoryItem, Automation, ToolInfo, HealthStatus, VoiceInfo, DiagnosticInfo, CodingProject, PersonaInfo, Skill, TaskItem, TaskPlan, SeriousModeState, ResearchJob } from '../types'
import { api } from '../services/api'
import { WebSocketManager } from '../services/websocket'

let idCounter = 0
const nextId = () => `m${++idCounter}-${Date.now()}`

export function useJarvis() {
  const [connection, setConnection] = useState<'connecting' | 'online' | 'offline'>('connecting')
  const [orbState, setOrbState] = useState<OrbState>('idle')
  const [messages, setMessages] = useState<Message[]>([])
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([])
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [settings, _setSettings] = useState<JarvisSettings | null>(null)
  const [memories, _setMemories] = useState<MemoryItem[]>([])
  const [automations, setAutomations] = useState<Automation[]>([])
  const [tools, setTools] = useState<ToolInfo[]>([])
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [voiceInfo, setVoiceInfo] = useState<VoiceInfo | null>(null)
  const [diagnostics, setDiagnostics] = useState<DiagnosticInfo | null>(null)
  const [projects, setProjects] = useState<CodingProject[]>([])
  const [persona, setPersona] = useState<PersonaInfo | null>(null)
  const [skills, setSkills] = useState<Skill[]>([])
  const [lastError, setLastError] = useState<string | null>(null)
  const [streaming, setStreaming] = useState(false)
  const [pendingToolConfirmation, setPendingToolConfirmation] = useState<{ tool: string; arguments: Record<string, any>; message: string; tool_call_id: string } | null>(null)
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [visionStatus, setVisionStatus] = useState<{ enabled: boolean; provider?: string | null } | null>(null)
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [activeTask, setActiveTask] = useState<TaskItem | null>(null)
  const [taskPlan, setTaskPlan] = useState<TaskPlan | null>(null)
  const [reminders, setReminders] = useState<any[]>([])
  const [summaries, setSummaries] = useState<any[]>([])
  const [privacyMode, setPrivacyMode] = useState<string>('normal')
  const [seriousMode, setSeriousMode] = useState<SeriousModeState>('inactive')
  const [researchJob, _setResearchJob] = useState<ResearchJob | null>(null)
  const [researchPhase, setResearchPhase] = useState<string>('')
  const [researchSourcesFound, setResearchSourcesFound] = useState(0)
  const [researchSourcesProcessed, setResearchSourcesProcessed] = useState(0)
  const [researchClaimsChecked, setResearchClaimsChecked] = useState(0)
  const [researchHistory, setResearchHistory] = useState<ResearchJob[]>([])

  const wsRef = useRef<WebSocketManager | null>(null)
  const abortRef = useRef(false)
  const errorSinceRef = useRef<number | null>(null)

  const connect = useCallback(() => {
    const isTauri = !!(window as any).__TAURI__ || !!(window as any).__TAURI_INTERNALS__
    const wsUrl = isTauri
      ? 'ws://127.0.0.1:8000/ws/jarvis'
      : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/jarvis`
    const ws = new WebSocketManager(wsUrl)
    wsRef.current = ws

    ws.on('connected', () => {
      errorSinceRef.current = null
      setConnection('online')
      setOrbState((s) => (s === 'thinking' || s === 'listening' ? s : 'idle'))
    })

    ws.on('disconnected', () => {
      if (connection === 'online') {
        setConnection('connecting')
      }
    })

    ws.on('status', (_event, data: any) => {
      if (data?.state === 'reconnecting') {
        setConnection('connecting')
      }
    })

    ws.on('error', (_event, data: any) => {
      const now = Date.now()
      errorSinceRef.current ??= now
      // The backend takes a few seconds to boot on app launch and the WebSocket
      // manager keeps retrying. Only show the offline screen for real outages.
      if (now - errorSinceRef.current < 6000) {
        setConnection('connecting')
        return
      }
      setConnection('offline')
      setLastError(data?.message || 'WebSocket connection error')
      setOrbState('error')
      setStreaming(false)
      setTimeout(() => setOrbState((s) => (s === 'error' ? 'idle' : s)), 4000)
    })

    ws.connect()

    ws.on('thinking', () => setOrbState('thinking'))
    ws.on('listening', () => setOrbState('listening'))
    ws.on('processing', () => setOrbState('processing'))
    ws.on('speaking', () => setOrbState('speaking'))
    ws.on('done', (_event, data: any) => {
      setOrbState('idle')
      if (data?.conversation_id) {
        setCurrentConversationId(data.conversation_id)
      }
    })

    ws.on('persona_switched', (_event, data: any) => {
      setPersona({ ...(persona ?? {}), ...data })
      if (data?.accent_color) {
        window.dispatchEvent(new CustomEvent('jarvis-accent', { detail: { color: data.accent_color } }))
      }
      if (data?.assistant_name) {
        _setSettings((prev) => (prev ? { ...prev, assistant_name: data.assistant_name, persona: data.id } : prev))
      }
    })

    ws.on('message_notification', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: `New message from ${data?.from ?? 'contact'}`, type: 'info', data } }))
    })

    ws.on('token', (_event, data: any) => {
      setStreaming(true)
      const chunk = data.chunk ?? data.content ?? ''
      if (!chunk) return
      setMessages((prev) => {
        const copy = [...prev]
        const last = copy[copy.length - 1]
        if (last && last.role === 'assistant') {
          last.content += chunk
        } else {
          copy.push({
            id: nextId(),
            role: 'assistant',
            content: chunk,
            timestamp: Date.now(),
            provider: data.provider,
          })
        }
        return copy
      })
    })

    ws.on('tool_start', (_event, data: any) => {
      setToolCalls((prev) => [
        ...prev,
        {
          id: nextId(),
          name: data.name || 'unknown',
          arguments: data.arguments || {},
          status: 'running',
        },
      ])
    })

    ws.on('tool_result', (_event, data: any) => {
      setToolCalls((prev) => {
        const copy = [...prev]
        const entry = copy.find((t) => t.name === data.tool && t.status === 'running')
        if (entry) {
          entry.result = data.result
          entry.status = data.success ? 'success' : 'error'
        }
        return copy
      })
    })

    ws.on('tool_confirmation', (_event, data: any) => {
      setPendingToolConfirmation({
        tool: data.tool,
        arguments: data.arguments || {},
        message: data.message || `Confirm ${data.tool}?`,
        tool_call_id: data.tool_call_id || '',
      })
    })

    ws.on('notification', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: data }))
    })

    ws.on('history', (_event, data: Message[]) => {
      setMessages(data.map((m) => ({ ...m, id: m.id || nextId() })))
    })

    ws.on('tts_first_audio', () => {
      // First audio frame started - useful for UI timing metrics
    })

    ws.on('browser_action', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: `Browser: ${data.action}`, type: 'info', data } }))
    })

    ws.on('browser_result', (_event, data: any) => {
      const ok = data.result?.success !== false
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: `Browser ${data.action}: ${ok ? 'Done' : 'Failed'}`, type: ok ? 'info' : 'error', data } }))
    })

    ws.on('computer_action', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: `Computer: ${data.action}`, type: 'info', data } }))
    })

    ws.on('computer_result', (_event, data: any) => {
      const ok = data.result?.success !== false
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: `Computer ${data.action}: ${ok ? 'Done' : 'Failed'}`, type: ok ? 'info' : 'error', data } }))
    })

    ws.on('vision_capture', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-vision-capture', { detail: data }))
    })

    ws.on('vision_analysis_started', () => {
      window.dispatchEvent(new CustomEvent('jarvis-vision-analyzing', { detail: {} }))
    })

    ws.on('vision_analysis_completed', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-vision-done', { detail: data }))
    })

    ws.on('vision_target_found', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-vision-target', { detail: data }))
    })

    ws.on('vision_action_started', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-vision-action', { detail: data }))
    })

    ws.on('vision_action_completed', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-vision-action-done', { detail: data }))
    })

    ws.on('vision_failed', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: `Vision: ${data.error || 'Failed'}`, type: 'error', data } }))
    })

    ws.on('voice_state', (_event, data: any) => {
      if (data?.state === 'speaking') setOrbState('speaking')
      else if (data?.state === 'listening') setOrbState('listening')
      else if (data?.state === 'processing') setOrbState('thinking')
      else if (data?.state === 'idle') setOrbState('idle')
    })

    ws.on('vision_started', (_event, data: any) => {
      setVisionStatus({ enabled: true, provider: data?.provider })
    })

    ws.on('vision_ready', () => {
      setVisionStatus((prev) => ({ ...prev, enabled: true }))
    })

    ws.on('task_created', (_event, data: any) => {
      setTasks((prev) => [data, ...prev])
    })

    ws.on('task_planning', (_event, data: any) => {
      setTaskPlan(data.plan || null)
    })

    ws.on('task_started', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => t.id === data.task_id ? { ...t, status: 'running' } : t))
    })

    ws.on('task_step_started', (_event, data: any) => {
      setActiveTask((prev) => prev ? { ...prev, current_action: data.current_action, current_step: data.step_index + 1 } : prev)
    })

    ws.on('task_step_completed', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => {
        if (t.id !== data.task_id) return t
        const logs = [...(t.logs || []), { timestamp: new Date().toISOString(), action: data.current_action || `Step ${data.step_index}`, result: data.success ? 'success' : `Failed: ${data.error}`, duration_ms: data.duration_ms || 0 }]
        return { ...t, logs, current_step: (t.current_step || 0) + 1 }
      }))
    })

    ws.on('task_step_failed', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => t.id === data.task_id ? { ...t, error: data.error } : t))
    })

    ws.on('task_verifying', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => t.id === data.task_id ? { ...t, status: 'verifying' } : t))
    })

    ws.on('task_completed', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => t.id === data.task_id ? { ...t, status: data.status || 'completed', result: data.result || 'Task completed.' } : t))
      setActiveTask((prev) => prev && prev.id === data.task_id ? { ...prev, status: data.status || 'completed' } : prev)
    })

    ws.on('task_failed', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => t.id === data.task_id ? { ...t, status: 'failed', error: data.error } : t))
      setActiveTask((prev) => prev && prev.id === data.task_id ? { ...prev, status: 'failed' } : prev)
    })

    ws.on('task_cancelled', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => t.id === data.task_id ? { ...t, status: 'cancelled' } : t))
      setActiveTask((prev) => prev && prev.id === data.task_id ? { ...prev, status: 'cancelled' } : prev)
    })

    ws.on('task_paused', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => t.id === data.task_id ? { ...t, status: 'paused' } : t))
    })

    ws.on('task_resumed', (_event, data: any) => {
      setTasks((prev) => prev.map((t) => t.id === data.task_id ? { ...t, status: 'running' } : t))
    })

    ws.on('task_permission_required', (_event, data: any) => {
      setPendingToolConfirmation({
        tool: data.tool || 'task_step',
        arguments: data.arguments || {},
        message: data.message || 'Confirmation required for task step.',
        tool_call_id: data.request_id || '',
      })
    })

    ws.on('task_approved', (_event, _data: any) => {
      setTaskPlan((prev) => prev ? { ...prev, approved: true } : prev)
    })

    ws.on('task_denied', (_event, _data: any) => {
      setTaskPlan((prev) => prev && prev.task_id === _data.task_id ? { ...prev, approved: false } : prev)
    })

    ws.on('memory_created', (_event, data: any) => {
      _setMemories((prev) => [data, ...prev])
    })

    ws.on('memory_updated', (_event, data: any) => {
      _setMemories((prev) => prev.map((m) => m.id === data.id ? { ...m, ...data } : m))
    })

    ws.on('memory_deleted', (_event, data: any) => {
      _setMemories((prev) => prev.filter((m) => m.id !== data.id))
    })

    ws.on('reminder_triggered', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: data.title || 'Reminder', type: 'info', data } }))
    })

    ws.on('notification_created', (_event, data: any) => {
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: data }))
    })

    ws.on('serious_mode_started', () => {
      setSeriousMode('active')
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: 'Serious Mode Activated', type: 'warning' } }))
    })

    ws.on('serious_mode_stopped', () => {
      setSeriousMode('inactive')
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: 'Normal Mode Restored', type: 'info' } }))
    })

    ws.on('research_started', (_event, data: any) => {
      _setResearchJob({
        id: data.job_id,
        topic: data.topic,
        status: data.status || 'running',
        phase: data.phase || '',
        started_at: Date.now(),
        completed_at: null,
        sources_found: 0,
        sources_processed: 0,
        claims_checked: 0,
        document_path: '',
        error: '',
      })
      setResearchPhase('starting')
      setResearchSourcesFound(0)
      setResearchSourcesProcessed(0)
      setResearchClaimsChecked(0)
      setOrbState('processing')
    })

    ws.on('research_query_updated', (_event, data: any) => {
      setResearchPhase(data.phase || '')
      if (data.topic) {
        _setResearchJob((prev: any) => prev ? { ...prev, topic: data.topic } : prev)
      }
    })

    ws.on('research_source_found', (_event, data: any) => {
      setResearchSourcesFound(data.sources_found || 0)
    })

    ws.on('research_source_processed', (_event, data: any) => {
      setResearchSourcesProcessed(data.sources_processed || 0)
      setResearchSourcesFound(data.sources_found || 0)
      if (data.claims_checked !== undefined) {
        setResearchClaimsChecked(data.claims_checked || 0)
      }
      if (data.status) {
        _setResearchJob((prev: any) => prev ? { ...prev, ...data } : prev)
      }
    })

    ws.on('research_analysis_started', (_event, _data: any) => {
      setResearchPhase('analyzing')
    })

    ws.on('research_writing_started', (_event, _data: any) => {
      setResearchPhase('writing')
    })

    ws.on('research_completed', (_event, data: any) => {
      const completedJob: ResearchJob = {
        id: data.job_id,
        topic: data.topic || '',
        status: 'completed',
        phase: 'completed',
        started_at: Date.now(),
        completed_at: Date.now(),
        sources_found: data.sources_found || 0,
        sources_processed: data.sources_processed || 0,
        claims_checked: data.claims_checked || 0,
        document_path: data.document_path || '',
        error: '',
      }
      _setResearchJob((prev: any) => prev ? {
        ...prev,
        ...completedJob,
      } : completedJob)
      setResearchPhase('completed')
      setOrbState('idle')
      setResearchHistory((prev) => {
        if (!prev.find((j) => j.id === completedJob.id)) {
          return [completedJob, ...prev]
        }
        return prev
      })
    })

    ws.on('research_failed', (_event, data: any) => {
      _setResearchJob((prev: any) => prev ? { ...prev, status: 'failed', error: data.error || 'Unknown error' } : prev)
      setResearchPhase('failed')
      setOrbState('idle')
    })

    ws.on('research_cancelled', (_event, _data: any) => {
      _setResearchJob((prev: any) => prev ? { ...prev, status: 'cancelled' } : prev)
      setResearchPhase('cancelled')
      setOrbState('idle')
    })

    ws.on('research_document_created', (_event, data: any) => {
      _setResearchJob((prev: any) => prev ? { ...prev, document_path: data.document_path || '' } : prev)
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: `Research document created: ${data.document_path}`, type: 'success' } }))
    })
  }, [])


  const startSeriousMode = useCallback(() => {
    const sysMsg: Message = {
      id: nextId(),
      role: 'system',
      content: 'SERIOUS MODE ACTIVATED',
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, sysMsg])
    wsRef.current?.send('serious_mode_start', {})
  }, [])

  const stopSeriousMode = useCallback(() => {
    const sysMsg: Message = {
      id: nextId(),
      role: 'system',
      content: 'NORMAL MODE RESTORED',
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, sysMsg])
    wsRef.current?.send('serious_mode_stop', {})
  }, [])

  const startResearch = useCallback((topic: string) => {
    const sysMsg: Message = {
      id: nextId(),
      role: 'system',
      content: `DEEP RESEARCH STARTED: ${topic}`,
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, sysMsg])
    wsRef.current?.send('research_start', { topic })
  }, [])

  const cancelResearch = useCallback((jobId: string) => {
    wsRef.current?.send('research_cancel', { job_id: jobId })
  }, [])

  const loadResearchHistory = useCallback(async () => {
    try {
      const res = await api.getResearchJobs()
      if (res?.jobs) {
        setResearchHistory(res.jobs.map((j: any) => ({
          id: j.id,
          topic: j.topic,
          status: j.status,
          phase: j.phase,
          started_at: j.started_at,
          completed_at: j.completed_at,
          sources_found: j.sources_found,
          sources_processed: j.sources_processed,
          claims_checked: j.claims_checked,
          document_path: j.document_path,
          error: j.error,
        })))
      }
    } catch {
      // ignore
    }
  }, [])

  const sendChat = useCallback(
    async (text: string) => {
      if (!text.trim() || !wsRef.current) return
      abortRef.current = false

      const lower = text.toLowerCase().trim()
      if (lower.includes('go into serious mode') || lower.includes('enter serious mode') || lower === 'serious mode') {
        startSeriousMode()
        return
      }
      if (lower.includes('exit serious mode') || lower.includes('leave serious mode') || lower === 'normal mode' || lower.includes('cancel serious mode')) {
        stopSeriousMode()
        return
      }
      if ((lower.includes('deep search on') || lower.includes('deep research on') || lower.includes('deep search'))) {
        const topicMatch = text.match(/(?:deep search on|deep research on|deep search)\s+(.+)/i)
        const topic = topicMatch ? topicMatch[1].trim() : text
        if (topic) {
          startResearch(topic)
          return
        }
      }
      if (lower === 'stop research' || lower === 'cancel research') {
        if (researchJob?.id) {
          cancelResearch(researchJob.id)
        }
        return
      }

      const userMsg: Message = {
        id: nextId(),
        role: 'user',
        content: text.trim(),
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, userMsg])
      setToolCalls([])
      setStreaming(false)
      setOrbState('thinking')

      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send('chat', { message: text.trim(), conversation_id: currentConversationId })
      } else {
        try {
          const data = await api.sendChat(text.trim())
          const assistantMsg: Message = {
            id: nextId(),
            role: 'assistant',
            content: data.response,
            timestamp: Date.now(),
          }
          setMessages((prev) => [...prev, assistantMsg])
          setOrbState('idle')
        } catch (err) {
          setLastError(err instanceof Error ? err.message : 'Failed to send message')
          setOrbState('error')
        }
      }
    },
    [currentConversationId, startSeriousMode, stopSeriousMode, startResearch, cancelResearch, researchJob]
  )

  const stopGeneration = useCallback(() => {
    abortRef.current = true
    setStreaming(false)
    setOrbState('idle')
    wsRef.current?.send('stop', {})
  }, [])

  const voiceListen = useCallback(async () => {
    setOrbState('listening')
    try {
      const data = await api.listen()
      if (data.transcript) {
        await sendChat(data.transcript)
      } else {
        setOrbState('idle')
      }
    } catch {
      setOrbState('error')
    }
  }, [sendChat])

  const speak = useCallback(
    async (text: string) => {
      try {
        await api.speak(text)
      } catch {
        // ignore
      }
    },
    []
  )

  const clearHistory = useCallback(() => {
    setMessages([])
    setToolCalls([])
    setCurrentConversationId(null)
    wsRef.current?.send('clear_history', {})
  }, [])

  const newConversation = useCallback(() => {
    setMessages([])
    setToolCalls([])
    setCurrentConversationId(null)
    setOrbState('idle')
    wsRef.current?.send('new_conversation', {})
  }, [])

  const loadConversation = useCallback(async (conversationId: string) => {
    try {
      const msgs = await api.getConversationMessages(conversationId, 200)
      setMessages(
        msgs.map((m) => ({
          id: m.id || nextId(),
          role: m.role,
          content: m.content,
          timestamp: typeof m.timestamp === 'number' ? m.timestamp : Date.parse(m.timestamp) || Date.now(),
        }))
      )
      setToolCalls([])
      setCurrentConversationId(conversationId)
      setStreaming(false)
      setOrbState('idle')
    } catch {
      // ignore
    }
  }, [])

  const confirmTool = useCallback((confirmed: boolean) => {
    if (!wsRef.current || !pendingToolConfirmation) return
    wsRef.current.send('tool_confirm', { confirmed, tool_call_id: pendingToolConfirmation.tool_call_id })
    setPendingToolConfirmation(null)
  }, [pendingToolConfirmation])

  const fetchProjects = useCallback(async () => {
    try {
      const res = await api.listProjects()
      if (res?.projects) setProjects(res.projects)
    } catch {
      // ignore
    }
  }, [])

  const refreshProjects = useCallback(() => {
    fetchProjects()
  }, [fetchProjects])

  const fetchData = useCallback(async () => {
    try {
      const [h, s, t, a, m, set, v, d, pr, per, sk, vs, tk, r, sum, p] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getSystemStats().catch(() => null),
        api.getTools().catch(() => []),
        api.getAutomations().catch(() => []),
        api.getMemory().catch(() => []),
        api.getSettings().catch(() => null),
        api.getVoiceInfo().catch(() => null),
        api.getDiagnostics().catch(() => null),
        api.listProjects().catch(() => null),
        api.getPersona().catch(() => null),
        api.listSkills().catch(() => []),
        api.getVisionStatus().catch(() => null),
        api.getTasks().catch(() => []),
        api.getReminders().catch(() => []),
        api.getConversationSummaries().catch(() => []),
        api.getPrivacySettings().catch(() => ({ privacy_mode: 'normal' })),
      ])
      if (h) setHealth(h)
      if (s) setStats(s)
      setTools(t)
      setAutomations(a)
      if (m) _setMemories(m)
      if (set) _setSettings(set)
      if (v) setVoiceInfo(v)
      if (d) setDiagnostics(d)
      if (pr?.projects) setProjects(pr.projects)
      if (per) setPersona(per)
      if (sk) setSkills(sk)
      if (vs) setVisionStatus(vs)
      if (tk) setTasks(tk)
      setReminders(r)
      setSummaries(sum)
      setPrivacyMode(p?.privacy_mode || 'normal')
    } catch {
      // ignore
    }
  }, [])

  const switchPersona = useCallback(async (personaId: string) => {
    try {
      const payload = await api.switchPersona(personaId)
      setPersona(payload)
      if (payload?.accent_color) {
        window.dispatchEvent(new CustomEvent('jarvis-accent', { detail: { color: payload.accent_color } }))
      }
      fetchData()
      return payload
    } catch {
      return null
    }
  }, [fetchData])

  const createTask = useCallback(async (description: string, auto_execute = false) => {
    try {
      const task = await api.createTask({ description, auto_execute })
      setTasks((prev) => [task, ...prev])
      return task
    } catch {
      return null
    }
  }, [])

  const startTask = useCallback(async (id: string) => {
    try {
      await api.startTask(id)
      setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status: 'running' } : t))
    } catch { /* ignore */ }
  }, [])

  const pauseTask = useCallback(async (id: string) => {
    try {
      await api.pauseTask(id)
      setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status: 'paused' } : t))
    } catch { /* ignore */ }
  }, [])

  const resumeTask = useCallback(async (id: string) => {
    try {
      await api.resumeTask(id)
      setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status: 'running' } : t))
    } catch { /* ignore */ }
  }, [])

  const cancelTask = useCallback(async (id: string) => {
    try {
      await api.cancelTask(id)
      setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status: 'cancelled' } : t))
    } catch { /* ignore */ }
  }, [])

  const approveTaskPlan = useCallback(async (id: string) => {
    try {
      await api.approveTask(id)
      setTaskPlan((prev) => prev && prev.task_id === id ? { ...prev, approved: true } : prev)
    } catch { /* ignore */ }
  }, [])

  const denyTaskPlan = useCallback(async (id: string) => {
    try {
      await api.denyTask(id)
      setTaskPlan((prev) => prev && prev.task_id === id ? { ...prev, approved: false } : prev)
    } catch { /* ignore */ }
  }, [])

  const addMemory = useCallback(async (content: string, category = 'general', project?: string, profile?: string) => {
    try {
      await api.addMemory(content, category, project, profile)
      fetchData()
    } catch { /* ignore */ }
  }, [fetchData])

  const updateMemory = useCallback(async (id: string, content: string, confidence?: number, source?: string) => {
    try {
      await api.updateMemory(id, content, confidence, source)
      fetchData()
    } catch { /* ignore */ }
  }, [fetchData])

  const deleteMemory = useCallback(async (id: string) => {
    try {
      await api.deleteMemory(id)
      fetchData()
    } catch { /* ignore */ }
  }, [fetchData])

  const searchMemory = useCallback(async (query: string, category?: string, project?: string, profile?: string) => {
    try {
      return await api.searchMemory(query, category, project, profile)
    } catch {
      return []
    }
  }, [])

  const addReminder = useCallback(async (title: string, description = '', dueAt = '', repeat = 'once') => {
    try {
      await api.createReminder(title, description, dueAt, repeat)
      fetchData()
    } catch { /* ignore */ }
  }, [fetchData])

  const updateReminder = useCallback(async (id: string, updates: Record<string, any>) => {
    try {
      await api.updateReminder(id, updates)
      fetchData()
    } catch { /* ignore */ }
  }, [fetchData])

  const deleteReminder = useCallback(async (id: string) => {
    try {
      await api.deleteReminder(id)
      fetchData()
    } catch { /* ignore */ }
  }, [fetchData])

  const updatePrivacyMode = useCallback(async (mode: string) => {
    try {
      await api.setPrivacyMode(mode)
      setPrivacyMode(mode)
    } catch { /* ignore */ }
  }, [])

  const refreshMemory = useCallback(async () => {
    try {
      const [m, r, s, p] = await Promise.all([
        api.getMemory().catch(() => []),
        api.getReminders().catch(() => []),
        api.getConversationSummaries().catch(() => []),
        api.getPrivacySettings().catch(() => ({ privacy_mode: 'normal' })),
      ])
      _setMemories(m)
      setReminders(r)
      setSummaries(s)
      setPrivacyMode(p?.privacy_mode || 'normal')
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.disconnect()
    }
  }, [connect])

  useEffect(() => {
    fetchData()
    const timer = setInterval(fetchData, 8000)
    return () => clearInterval(timer)
  }, [fetchData])

  const reconnect = useCallback(() => {
    errorSinceRef.current = null
    wsRef.current?.disconnect()
    setConnection('connecting')
    setLastError(null)
    setMessages([])
    connect()
  }, [connect])

  return {
    connection,
    orbState,
    messages,
    toolCalls,
    streaming,
    stats,
    settings,
    memories,
    automations,
    tools,
    health,
    voiceInfo,
    diagnostics,
    projects,
    persona,
    skills,
    lastError,
    sendChat,
    stopGeneration,
    voiceListen,
    speak,
    clearHistory,
    newConversation,
    loadConversation,
    currentConversationId,
    fetchData,
    fetchProjects,
    refreshProjects,
    switchPersona,
    pendingToolConfirmation,
    confirmTool,
    reconnect,
    visionStatus,
    tasks,
    activeTask,
    taskPlan,
    reminders,
    summaries,
    privacyMode,
    createTask,
    startTask,
    pauseTask,
    resumeTask,
    cancelTask,
    approveTaskPlan,
    denyTaskPlan,
    setTaskPlan,
    addMemory,
    updateMemory,
    deleteMemory,
    searchMemory,
    addReminder,
    updateReminder,
    deleteReminder,
    updatePrivacyMode,
    refreshMemory,
    seriousMode,
    researchJob,
    researchPhase,
    researchSourcesFound,
    researchSourcesProcessed,
    researchClaimsChecked,
    researchHistory,
    startSeriousMode,
    stopSeriousMode,
    startResearch,
    cancelResearch,
    loadResearchHistory,
    setResearchJob: _setResearchJob,
  }
}
