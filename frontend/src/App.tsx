import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { TabId } from './types'
import { Orb } from './components/Orb/Orb'
import { ChatPanel } from './components/Chat/ChatPanel'
import { SystemPanel } from './components/System/SystemPanel'
import { ToolsPanel } from './components/Tools/ToolsPanel'
import { MemoryPanel } from './components/Memory/MemoryPanel'
import { ConversationHistory } from './components/Memory/ConversationHistory'
import { AutomationsPanel } from './components/Automations/AutomationsPanel'
import { SettingsPanel } from './components/Settings/SettingsPanel'
import { VoicePanel } from './components/Voice/VoicePanel'
import { CodingPanel } from './components/Coding/CodingPanel'
import { DiagnosticsPanel } from './components/Diagnostics/DiagnosticsPanel'
import { HealthDashboard } from './components/System/HealthDashboard'
import { AboutPanel } from './components/About/AboutPanel'
import { SkillsPanel } from './components/Skills/SkillsPanel'
import { Sidebar } from './components/Sidebar/Sidebar'
import { ActivityFeed } from './components/Activity/ActivityFeed'
import { HomePanel } from './components/Home/HomePanel'
import { StartupSequence } from './components/Startup/StartupSequence'
import { OfflineScreen } from './components/Common/OfflineScreen'
import { MediaGenerationPanel } from './components/Media/MediaGenerationPanel'
import { FirstRunSetup } from './components/Common/FirstRunSetup'
import TitleBar from './components/TitleBar'
import { AgentPanel } from './components/Agent/AgentPanel'
import { BrowserPanel } from './components/Browser/BrowserPanel'
import { ComputerPanel } from './components/Computer/ComputerPanel'
import { VisionPanel } from './components/Vision/VisionPanel'
import { TasksPanel } from './components/Tasks/TasksPanel'
import { WorkflowsPanel } from './components/Workflows/WorkflowsPanel'
import { ResearchPanel } from './components/Research/ResearchPanel'
import { ResearchHistory } from './components/Research/ResearchHistory'
import { useJarvis } from './hooks/useJarvis'
import { api } from './services/api'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'
import { Activity, Cpu, Radio } from 'lucide-react'

type ViewMode = 'orb' | 'split'

const PERSONA_ACCENTS: Record<string, string> = {
  jarvis: '#00f0ff',
  alya: '#ff6ec7',
}

export default function App() {
  const [loading, setLoading] = useState(true)
  const [booted, setBooted] = useState(false)
  const [viewMode] = useState<ViewMode>('split')
  const [activeTab, setActiveTab] = useState<TabId>('chat')
  const [accentColor, setAccentColor] = useState('#00f0ff')
  const [notifications, setNotifications] = useState<{ id: string; message: string; type: 'info' | 'warning' | 'error' }[]>([])
  const [copiedContent, setCopiedContent] = useState('')
  const [showFirstRun, setShowFirstRun] = useState(false)
  const [seriousMode, setSeriousMode] = useState(false)
  const [showResearchPanel, setShowResearchPanel] = useState(false)

  const {
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
    clearHistory,
    newConversation,
    loadConversation,
    currentConversationId,
    fetchData,
    switchPersona,
    pendingToolConfirmation,
    confirmTool,
    reconnect,
    tasks,
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
    seriousMode: hookSeriousMode,
    researchJob,
    researchPhase: _researchPhase,
    researchSourcesFound: _researchSourcesFound,
    researchSourcesProcessed: _researchSourcesProcessed,
    researchClaimsChecked: _researchClaimsChecked,
    researchHistory,
    startSeriousMode,
    stopSeriousMode,
    startResearch: _startResearch,
    cancelResearch,
    loadResearchHistory,
    setResearchJob: _setResearchJob,
    startAgent,
    approveAgent,
    cancelAgent,
    pauseAgent,
    resumeAgent,
    killAgent,
    rollbackAgent,
    updateAgentPermissions,
    loadAgentPermissions,
  } = useJarvis()

  useKeyboardShortcuts([
    { key: ' ', ctrl: true, handler: () => voiceListen() },
    { key: 'Enter', ctrl: true, handler: () => { const input = document.querySelector('input[type="text"]') as HTMLInputElement | null; if (input) { input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' })); } } },
    { key: 'Escape', handler: () => { if (streaming) stopGeneration(); } },
    { key: 'k', ctrl: true, handler: () => setActiveTab('chat') },
    { key: 'm', ctrl: true, shift: true, handler: () => voiceListen() },
    { key: 'j', ctrl: true, shift: true, handler: () => setActiveTab('chat') },
  ])

  const handleCopy = useCallback(async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedContent(content)
      setTimeout(() => setCopiedContent(''), 2000)
    } catch {
      // ignore
    }
  }, [])

  const handleToolExecute = useCallback(async (name: string, args: Record<string, any>) => {
    try {
      await api.executeTool(name, args)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Tool execution failed'
      window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: errorMsg, type: 'error' } }))
    }
  }, [])

  const handleAutomationCreate = useCallback(
    async (automation: Omit<import('./types').Automation, 'id'>) => {
      try {
        await api.createAutomation(automation)
        fetchData()
      } catch (err) {
        window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: 'Failed to create automation', type: 'error' } }))
      }
    },
    [fetchData]
  )

  const handleAutomationUpdate = useCallback(
    async (id: string, patch: Partial<import('./types').Automation>) => {
      try {
        await api.updateAutomation(id, patch)
        fetchData()
      } catch {
        // ignore
      }
    },
    [fetchData]
  )

  const handleAutomationDelete = useCallback(
    async (id: string) => {
      try {
        await api.deleteAutomation(id)
        fetchData()
      } catch {
        // ignore
      }
    },
    [fetchData]
  )

  const handleAutomationExecute = useCallback(
    async (id: string) => {
      const automation = automations.find((a) => a.id === id)
      if (!automation) return
      try {
        await api.executeTool('execute_automation', { automation_id: id })
      } catch {
        // ignore
      }
    },
    [automations]
  )

  const handleMemoryAdd = useCallback(
    async (content: string, category?: string, project?: string, profile?: string) => {
      try {
        await api.addMemory(content, category, project, profile)
        fetchData()
      } catch {
        window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message: 'Failed to add memory', type: 'error' } }))
      }
    },
    [fetchData]
  )

  const handleMemoryUpdate = useCallback(
    async (id: string, content: string, confidence?: number, source?: string) => {
      try {
        await api.updateMemory(id, content, confidence, source)
        fetchData()
      } catch {
        // ignore
      }
    },
    [fetchData]
  )

  const handleMemoryDelete = useCallback(
    async (id: string) => {
      try {
        await api.deleteMemory(id)
        fetchData()
      } catch {
        // ignore
      }
    },
    [fetchData]
  )

  const handleAddReminder = useCallback(
    async (title: string, description: string, dueAt: string, repeat: string) => {
      try {
        await api.createReminder(title, description, dueAt, repeat)
        fetchData()
      } catch {
        // ignore
      }
    },
    [fetchData]
  )

  const handleUpdateReminder = useCallback(
    async (id: string, updates: Record<string, any>) => {
      try {
        await api.updateReminder(id, updates)
        fetchData()
      } catch {
        // ignore
      }
    },
    [fetchData]
  )

  const handleDeleteReminder = useCallback(
    async (id: string) => {
      try {
        await api.deleteReminder(id)
        fetchData()
      } catch {
        // ignore
      }
    },
    [fetchData]
  )

  const handleSetPrivacyMode = useCallback(
    async (mode: string) => {
      try {
        await api.setPrivacyMode(mode)
      } catch {
        // ignore
      }
    },
    []
  )

  const handleConversationDelete = useCallback(
    async (convId: string) => {
      try {
        await api.deleteConversation(convId)
        if (convId === currentConversationId) {
          newConversation()
        }
        fetchData()
      } catch {
        // ignore
      }
    },
    [currentConversationId, newConversation, fetchData]
  )

  const handleSettingsUpdate = useCallback(
    async (patch: Partial<import('./types').JarvisSettings>) => {
      try {
        await api.updateSettings(patch)
        if (patch.accent_color) setAccentColor(patch.accent_color)
      } catch {
        // ignore
      }
    },
    []
  )

  const handleRetry = useCallback(() => {
    reconnect()
  }, [reconnect])

  const handleNotification = useCallback((e: Event) => {
    const detail = (e as CustomEvent).detail
    const id = `n${Date.now()}`
    setNotifications((prev) => [...prev, { id, ...detail }])
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id))
    }, 5000)
  }, [])

  useEffect(() => {
    window.addEventListener('jarvis-notification', handleNotification)
    return () => window.removeEventListener('jarvis-notification', handleNotification)
  }, [handleNotification])

  useEffect(() => {
    if (hookSeriousMode) {
      setSeriousMode(true)
    } else {
      setSeriousMode(false)
    }
  }, [hookSeriousMode])

  useEffect(() => {
    if (activeTab === 'research') {
      loadResearchHistory()
    }
  }, [activeTab, loadResearchHistory])

  useEffect(() => {
    const handleAccent = (e: Event) => {
      const color = (e as CustomEvent).detail?.color
      if (color) setAccentColor(color)
    }
    window.addEventListener('jarvis-accent', handleAccent)
    return () => window.removeEventListener('jarvis-accent', handleAccent)
  }, [])

  useEffect(() => {
    if (settings?.accent_color) {
      setAccentColor(settings.accent_color)
    } else if (persona?.accent_color) {
      setAccentColor(persona.accent_color)
    } else if (settings?.persona) {
      setAccentColor(PERSONA_ACCENTS[settings.persona] || '#00f0ff')
    }
  }, [settings?.accent_color, settings?.persona, persona?.accent_color])

  useEffect(() => {
    if (persona?.accent_color && !settings?.accent_color) {
      setAccentColor(persona.accent_color)
    }
  }, [persona?.accent_color, settings?.accent_color])

  useEffect(() => {
    if (settings && !settings.groq_api_key && !settings.local_llm_enabled) {
      setShowFirstRun(true)
    }
  }, [settings])

  const handleOrbClick = useCallback(() => {
    if (orbState === 'listening') {
      // Stop listening - handled by voiceListen completion
      return
    }
    voiceListen()
  }, [orbState, voiceListen])

  // Right panel content
  const rightPanel = (
    <div className="h-full flex flex-col gap-3 p-3 overflow-y-auto">
      {/* Connection Status */}
      <div className="glass-panel p-3">
        <div className="flex items-center gap-2 mb-2">
          <Radio className="w-3.5 h-3.5 text-cyan-400/70" />
          <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Connection</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connection === 'online' ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : connection === 'connecting' ? 'bg-yellow-400 animate-pulse' : 'bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.6)]'}`} />
          <span className="text-xs text-slate-300 uppercase tracking-wider">{connection}</span>
        </div>
      </div>

      {/* System Mini Stats */}
      {stats && (
        <div className="glass-panel p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5 text-cyan-400/70" />
            <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">System</span>
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">CPU</span>
              <span className={`font-mono ${typeof stats.cpu.percent === 'number' && stats.cpu.percent > 90 ? 'text-red-400' : 'text-slate-300'}`}>
                {stats.cpu.percent ?? '--'}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">RAM</span>
              <span className={`font-mono ${typeof stats.ram.percent === 'number' && stats.ram.percent > 90 ? 'text-red-400' : 'text-slate-300'}`}>
                {stats.ram.percent ?? '--'}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Disk</span>
              <span className={`font-mono ${typeof stats.disk.percent === 'number' && stats.disk.percent > 90 ? 'text-red-400' : 'text-slate-300'}`}>
                {stats.disk.percent ?? '--'}%
              </span>
            </div>
            {stats.battery.present && (
              <div className="flex justify-between">
                <span className="text-slate-500">Battery</span>
                <span className="font-mono text-slate-300">{stats.battery.percent ?? '--'}%</span>
              </div>
            )}
            {stats.uptime.seconds != null && (
              <div className="flex justify-between">
                <span className="text-slate-500">Uptime</span>
                <span className="font-mono text-slate-300">
                  {Math.floor(stats.uptime.seconds / 3600)}h {Math.floor((stats.uptime.seconds % 3600) / 60)}m
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Active Provider */}
      {health && (
        <div className="glass-panel p-3">
          <div className="flex items-center gap-2 mb-2">
            <Radio className="w-3.5 h-3.5 text-cyan-400/70" />
            <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">AI Provider</span>
          </div>
          <div className="space-y-1">
            {Object.entries(health.providers).map(([name, p]) => (
              <div key={name} className="flex items-center justify-between text-xs">
                <span className="text-slate-500 capitalize">{name.replace('_', ' ')}</span>
                <span className={`flex items-center gap-1 ${p.status === 'online' ? 'text-emerald-400' : 'text-slate-600'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${p.status === 'online' ? 'bg-emerald-400' : 'bg-slate-700'}`} />
                  {p.status === 'online' && p.latency_ms != null ? `${p.latency_ms}ms` : p.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activity Feed */}
      <div className="glass-panel p-3 flex-1 min-h-0 flex flex-col">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-3.5 h-3.5 text-cyan-400/70" />
          <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Activity</span>
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          <ActivityFeed toolCalls={toolCalls} notifications={notifications.map((n) => ({ ...n }))} />
        </div>
      </div>
    </div>
  )

  const leftPanel = viewMode === 'split' && activeTab === 'chat' ? (
    <div className={`w-72 border-r flex flex-col items-center bg-black/20 overflow-hidden ${seriousMode ? 'border-red-500/20' : 'border-cyan-500/10'}`}>
      <div className="flex-1 flex flex-col items-center justify-center p-4 w-full">
        <Orb
          state={orbState}
          assistantName={settings?.assistant_name || 'JARVIS'}
          accentColor={seriousMode ? '#ff1a1a' : accentColor}
          size={88}
          onClick={handleOrbClick}
        />
        <div className="mt-4 text-[10px] tracking-[0.3em] uppercase flex items-center gap-2" style={{ color: seriousMode ? '#ff1a1a' : undefined }}>
          {seriousMode && <span className="w-2 h-2 rounded-full bg-red-500 serious-pulse" />}
          {orbState === 'listening' ? 'Listening...' : orbState === 'thinking' ? 'Thinking' : orbState === 'speaking' ? 'Speaking' : orbState === 'processing' ? 'Processing' : 'Click to speak'}
        </div>
        {seriousMode && (
          <div className="mt-2 text-[10px] tracking-[0.2em] text-red-400/70 uppercase font-bold">Serious Mode Active</div>
        )}
      </div>
    </div>
  ) : null

  if (loading && !booted) {
    return <StartupSequence onComplete={() => { setLoading(false); setBooted(true) }} />
  }

  if (showFirstRun && settings) {
    return <FirstRunSetup settings={settings} onComplete={() => setShowFirstRun(false)} onUpdate={handleSettingsUpdate} />
  }

  if (connection === 'offline' && messages.length === 0) {
    return <OfflineScreen error={lastError || undefined} onRetry={handleRetry} />
  }

  const isChatTab = activeTab === 'chat'

  const handleOpenDocument = useCallback(() => {
    if (researchJob?.document_path) {
      window.open(`file://${researchJob.document_path}`, '_blank')
    }
  }, [researchJob])

  const handleOpenFolder = useCallback(() => {
    if (researchJob?.document_path) {
      const folder = researchJob.document_path.split('/').slice(0, -1).join('/')
      window.open(`file://${folder}`, '_blank')
    }
  }, [researchJob])

  const handleCopyPath = useCallback(() => {
    if (researchJob?.document_path) {
      navigator.clipboard.writeText(researchJob.document_path)
      setCopiedContent(researchJob.document_path)
      setTimeout(() => setCopiedContent(''), 2000)
    }
  }, [researchJob])

  const handleResearchHistorySelect = useCallback((job: any) => {
    _setResearchJob(job)
    setShowResearchPanel(true)
  }, [_setResearchJob])

  return (
    <div className={`h-screen w-screen flex flex-col bg-jarvis-dark relative overflow-hidden ${seriousMode ? 'serious-mode' : ''}`}>
      <TitleBar />
      {/* HUD overlay effects */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,240,255,0.03)_0%,transparent_70%)]" />
        <div className="absolute inset-0 opacity-[0.02]" style={{ backgroundImage: 'linear-gradient(rgba(0,240,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,0.5) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {notifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
          <AnimatePresence>
            {notifications.map((n) => (
              <motion.div
                key={n.id}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`glass-panel p-3 text-xs ${n.type === 'error' ? 'border-red-400/30' : n.type === 'warning' ? 'border-yellow-400/30' : ''}`}
              >
                {n.message}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden relative z-10">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} connection={connection} persona={persona} onSwitchPersona={(id) => switchPersona(id)} accentColor={accentColor} seriousMode={seriousMode} onToggleSeriousMode={() => seriousMode ? stopSeriousMode() : startSeriousMode()} />

        <div className="flex-1 flex min-w-0">
          {isChatTab && viewMode === 'split' ? (
            <>
              {leftPanel}
              <div className="flex-1 flex flex-col min-w-0 border-r border-cyan-500/10">
                <ChatPanel
                  messages={messages}
                  toolCalls={toolCalls}
                  orbState={orbState}
                  streaming={streaming}
                  onSend={sendChat}
                  onVoice={voiceListen}
                  onStop={stopGeneration}
                  onClear={clearHistory}
                  onCopy={handleCopy}
                  micAvailable={connection === 'online'}
                  pendingToolConfirmation={pendingToolConfirmation}
                  onConfirmTool={confirmTool}
                  onQuickAction={sendChat}
                />
              </div>
              <div className="w-80 hidden xl:block overflow-hidden">
                {rightPanel}
              </div>
            </>
          ) : isChatTab && viewMode === 'orb' ? (
            <div className="flex-1 flex flex-col min-w-0">
              <ChatPanel
                messages={messages}
                toolCalls={toolCalls}
                orbState={orbState}
                streaming={streaming}
                onSend={sendChat}
                onVoice={voiceListen}
                onStop={stopGeneration}
                onClear={clearHistory}
                onCopy={handleCopy}
                micAvailable={connection === 'online'}
                pendingToolConfirmation={pendingToolConfirmation}
                onConfirmTool={confirmTool}
                onQuickAction={sendChat}
              />
            </div>
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.15 }}
                className="flex-1 flex min-w-0"
              >
                <div className="flex-1 min-w-0 overflow-hidden">
                  {activeTab === 'home' && (
                    <HomePanel
                      settings={settings}
                      health={health}
                      voiceInfo={voiceInfo}
                      diagnostics={diagnostics}
                      stats={stats}
                      projects={projects}
                      connection={connection}
                      orbState={orbState}
                      accentColor={accentColor}
                      onNavigate={setActiveTab}
                      onAction={sendChat}
                    />
                  )}
                  {activeTab === 'system' && <SystemPanel stats={stats} health={health} />}
                  {activeTab === 'tools' && <ToolsPanel tools={tools} onExecute={handleToolExecute} />}
                  {activeTab === 'memory' && (
                    <div className="h-full flex">
                      <div className="flex-1 min-w-0">
                        <MemoryPanel
                          memories={memories}
                          onAdd={handleMemoryAdd}
                          onDelete={handleMemoryDelete}
                          onUpdate={handleMemoryUpdate}
                          onRefresh={fetchData}
                          reminders={reminders}
                          onAddReminder={handleAddReminder}
                          onUpdateReminder={handleUpdateReminder}
                          onDeleteReminder={handleDeleteReminder}
                          summaries={summaries}
                          privacy={privacyMode ? { privacy_mode: privacyMode } : null}
                          onSetPrivacyMode={handleSetPrivacyMode}
                          projects={projects.map((p) => p.name)}
                          profile={persona?.id || 'jarvis'}
                          onSearchMemory={async (query: string, category?: string, project?: string) => {
                            const results = await api.searchMemory(query, category, project)
                            return results
                          }}
                        />
                      </div>
                      <div className="w-80 border-l border-cyan-500/10 hidden md:block">
                        <ConversationHistory
                          currentConversationId={currentConversationId}
                          onSelect={loadConversation}
                          onNew={newConversation}
                          onDelete={handleConversationDelete}
                        />
                      </div>
                    </div>
                  )}
                  {activeTab === 'automations' && (
                    <AutomationsPanel
                      automations={automations}
                      onCreate={handleAutomationCreate}
                      onUpdate={handleAutomationUpdate}
                      onDelete={handleAutomationDelete}
                      onExecute={handleAutomationExecute}
                    />
                  )}
                  {activeTab === 'tasks' && (
                    <TasksPanel
                      tasks={tasks}
                      taskPlan={taskPlan}
                      onCreate={createTask}
                      onStart={startTask}
                      onPause={pauseTask}
                      onResume={resumeTask}
                      onCancel={cancelTask}
                      onApprove={approveTaskPlan}
                      onDeny={denyTaskPlan}
                      onClearPlan={() => setTaskPlan(null)}
                    />
                  )}
                  {activeTab === 'media' && (
                    <MediaGenerationPanel settings={settings} onUpdate={handleSettingsUpdate} />
                  )}
                  {activeTab === 'settings' && (
                    <SettingsPanel settings={settings} persona={persona} onSwitchPersona={(id) => switchPersona(id)} onUpdate={handleSettingsUpdate} onClose={() => setActiveTab('chat')} />
                  )}
                  {activeTab === 'voice' && (
                    <VoicePanel
                      orbState={orbState}
                      onVoice={voiceListen}
                      onSpeak={(text) => api.speak(text)}
                      voiceAvailable={connection === 'online'}
                      settings={settings}
                      voiceInfo={voiceInfo}
                      onUpdate={handleSettingsUpdate}
                    />
                  )}
                  {activeTab === 'coding' && <CodingPanel projects={projects} onRefresh={fetchData} />}
                  {activeTab === 'diagnostics' && <DiagnosticsPanel />}
                  {activeTab === 'health' && (
                    <HealthDashboard
                      health={health}
                      diagnostics={diagnostics}
                    />
                  )}
                  {activeTab === 'about' && <AboutPanel />}
                  {activeTab === 'skills' && <SkillsPanel />}
                  {activeTab === 'agent' && (
                    <AgentPanel
                      projects={projects.map((p) => ({ name: p.name, stack: p.stack ?? undefined }))}
                      onStartAgent={startAgent}
                      onApproveAgent={approveAgent}
                      onCancelAgent={cancelAgent}
                      onPauseAgent={pauseAgent}
                      onResumeAgent={resumeAgent}
                      onKillAgent={killAgent}
                      onRollbackAgent={rollbackAgent}
                      onUpdateAgentPermissions={updateAgentPermissions}
                      onLoadAgentPermissions={loadAgentPermissions}
                      settings={settings}
                    />
                  )}
                  {activeTab === 'browser' && <BrowserPanel onNavigate={setActiveTab} />}
                  {activeTab === 'computer' && <ComputerPanel onNavigate={setActiveTab} />}
                  {activeTab === 'vision' && <VisionPanel />}
                  {activeTab === 'workflows' && <WorkflowsPanel onNavigate={setActiveTab} />}
                  {activeTab === 'research' && (
                    <div className="h-full flex">
                      <div className="flex-1 min-w-0">
                        {showResearchPanel && researchJob ? (
                          <ResearchPanel
                            job={researchJob}
                            onClose={() => setShowResearchPanel(false)}
                            onCancel={() => cancelResearch(researchJob.id)}
                            onOpenDocument={handleOpenDocument}
                            onOpenFolder={handleOpenFolder}
                            onCopyPath={handleCopyPath}
                          />
                        ) : (
                          <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                            Select a research item from history or start new research
                          </div>
                        )}
                      </div>
                      <div className="w-80 border-l border-red-500/10 hidden md:block">
                        <ResearchHistory jobs={researchHistory} onSelect={handleResearchHistorySelect} onRefresh={loadResearchHistory} />
                      </div>
                    </div>
                  )}
                </div>
                {activeTab !== 'chat' && (
                  <div className="w-72 border-l border-cyan-500/10 hidden lg:block overflow-hidden">
                    {rightPanel}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </div>

      <AnimatePresence>
        {copiedContent && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 glass-panel px-4 py-2 text-xs text-cyan-400"
          >
            Copied to clipboard
          </motion.div>
        )}

        {pendingToolConfirmation && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="relative w-full max-w-md glass-panel shadow-2xl p-6"
            >
              <h3 className="text-sm tracking-[0.2em] text-yellow-400/70 uppercase mb-2">Confirmation Required</h3>
              <p className="text-sm text-slate-300 mb-4">{pendingToolConfirmation.message}</p>
              {pendingToolConfirmation.arguments && Object.keys(pendingToolConfirmation.arguments).length > 0 && (
                <div className="glass-panel p-2 mb-4 text-xs text-slate-400 font-mono">
                  {JSON.stringify(pendingToolConfirmation.arguments, null, 2)}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => confirmTool(false)}
                  className="px-4 py-2 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={() => confirmTool(true)}
                  className="px-4 py-2 bg-yellow-500/15 border border-yellow-400/40 rounded text-xs text-yellow-200 hover:bg-yellow-400/25 transition-all"
                >
                  Confirm
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
