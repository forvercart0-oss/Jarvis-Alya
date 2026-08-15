import { useCallback, useEffect, useRef, useState } from 'react'
import type { OrbState, Message, ToolCall, SystemStats, JarvisSettings, MemoryItem, Automation, ToolInfo, HealthStatus, VoiceInfo, DiagnosticInfo, CodingProject, PersonaInfo } from '../types'
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
  const [lastError, setLastError] = useState<string | null>(null)
  const [streaming, setStreaming] = useState(false)
  const [pendingToolConfirmation, setPendingToolConfirmation] = useState<{ tool: string; arguments: Record<string, any>; message: string; tool_call_id: string } | null>(null)
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)

  const wsRef = useRef<WebSocketManager | null>(null)
  const abortRef = useRef(false)

  const connect = useCallback(() => {
    const isTauri = !!(window as any).__TAURI__
    const wsUrl = isTauri
      ? 'ws://127.0.0.1:8000/ws/jarvis'
      : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/jarvis`
    const ws = new WebSocketManager(wsUrl)
    wsRef.current = ws

    ws.on('connected', () => {
      setConnection('online')
      setOrbState((s) => (s === 'thinking' || s === 'listening' ? s : 'idle'))
    })

    ws.on('disconnected', () => {
      setConnection('offline')
    })

    ws.on('status', (_event, data: any) => {
      if (data?.state === 'reconnecting') {
        setConnection('connecting')
      }
    })

    ws.on('error', () => {
      setConnection('offline')
    })

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

    ws.on('error', (_event, data: any) => {
      setLastError(data?.message || 'Unknown error')
      setOrbState('error')
      setStreaming(false)
      setTimeout(() => setOrbState((s) => (s === 'error' ? 'idle' : s)), 4000)
    })

    ws.on('history', (_event, data: Message[]) => {
      setMessages(data.map((m) => ({ ...m, id: m.id || nextId() })))
    })

    ws.connect()
  }, [])

  const sendChat = useCallback(
    async (text: string) => {
      if (!text.trim() || !wsRef.current) return
      abortRef.current = false
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
    [currentConversationId]
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
      const [h, s, t, a, m, set, v, d, pr, per] = await Promise.all([
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
  }
}
