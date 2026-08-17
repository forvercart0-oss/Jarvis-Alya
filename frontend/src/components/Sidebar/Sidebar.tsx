import { MessageSquare, Cpu, Wrench, Zap, Settings, AudioLines, FileCode2, Activity, Home, BookOpen, ImageIcon, HeartPulse, Puzzle, Bot, Globe, Monitor, Eye, ListTodo, FlaskConical } from 'lucide-react'
import type { TabId, PersonaInfo } from '../../types'

interface SidebarItemProps {
  id: string
  label: string
  icon: React.ReactNode
  active: boolean
  accent: string
  onClick: () => void
  serious?: boolean
}

function SidebarItem({ label, icon, active, accent, onClick, serious }: SidebarItemProps) {
  const color = serious && active ? '#ff1a1a' : active ? accent : undefined
  return (
    <button
      onClick={onClick}
      className={[
        'w-12 h-12 flex flex-col items-center justify-center gap-1 rounded-lg transition-all relative',
        active ? 'bg-slate-800/40' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50',
      ].join(' ')}
      style={color ? { color } : undefined}
      title={label}
    >
      {icon}
      <span className="text-[8px] tracking-wider uppercase">{label.slice(0, 3)}</span>
      {active && (
        <div
          className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-5 rounded-r"
          style={{ background: color || accent, boxShadow: `0 0 8px ${color || accent}` }}
        />
      )}
    </button>
  )
}

interface SidebarProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  connection: 'connecting' | 'online' | 'offline'
  persona?: PersonaInfo | null
  onSwitchPersona?: (personaId: string) => void
  accentColor?: string
  seriousMode?: boolean
  onToggleSeriousMode?: () => void
}

export function Sidebar({ activeTab, onTabChange, connection, persona, onSwitchPersona, accentColor = '#00f0ff', seriousMode, onToggleSeriousMode }: SidebarProps) {
  const currentPersona = persona?.id || 'jarvis'
  const nextPersona = currentPersona === 'jarvis' ? 'alya' : 'jarvis'
  const logoId = persona?.logo_id || currentPersona

  return (
    <div className="w-16 border-r flex flex-col items-center py-4 gap-1 bg-black/40 z-20" style={{ borderColor: `${accentColor}22` }}>
      <div className="w-9 h-9 mb-4 flex items-center justify-center relative">
        {logoId === 'alya' ? (
          <svg viewBox="0 0 64 64" className="w-7 h-7" style={{ filter: `drop-shadow(0 0 8px ${accentColor}88)` }}>
            <defs>
              <linearGradient id="alyaSidebarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff6ec7" />
                <stop offset="100%" stopColor="#a855f7" />
              </linearGradient>
            </defs>
            <g transform="translate(32,32)">
              <polygon points="0,-24 20,-12 20,12 0,24 -20,12 -20,-12" fill="none" stroke="url(#alyaSidebarGrad)" strokeWidth="3" strokeLinejoin="round" />
              <circle cx="0" cy="0" r="5" fill="url(#alyaSidebarGrad)" />
            </g>
          </svg>
        ) : (
          <svg viewBox="0 0 64 64" className="w-7 h-7" style={{ filter: `drop-shadow(0 0 8px ${accentColor}88)` }}>
            <defs>
              <linearGradient id="jarvisSidebarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00f0ff" />
                <stop offset="100%" stopColor="#0077ff" />
              </linearGradient>
            </defs>
            <g transform="translate(32,32)">
              <polygon points="0,-24 20,-12 20,12 0,24 -20,12 -20,-12" fill="none" stroke="url(#jarvisSidebarGrad)" strokeWidth="3" strokeLinejoin="round" />
              <circle cx="0" cy="0" r="5" fill="url(#jarvisSidebarGrad)" />
            </g>
          </svg>
        )}
      </div>

      <SidebarItem id="home" label="Home" icon={<Home className="w-5 h-5" />} active={activeTab === 'home'} accent={accentColor} onClick={() => onTabChange('home')} />
      <SidebarItem id="chat" label="Chat" icon={<MessageSquare className="w-5 h-5" />} active={activeTab === 'chat'} accent={accentColor} onClick={() => onTabChange('chat')} />
      <SidebarItem id="voice" label="Voice" icon={<AudioLines className="w-5 h-5" />} active={activeTab === 'voice'} accent={accentColor} onClick={() => onTabChange('voice')} />
      <SidebarItem id="system" label="System" icon={<Cpu className="w-5 h-5" />} active={activeTab === 'system'} accent={accentColor} onClick={() => onTabChange('system')} />
      <SidebarItem id="tools" label="Tools" icon={<Wrench className="w-5 h-5" />} active={activeTab === 'tools'} accent={accentColor} onClick={() => onTabChange('tools')} />
      <SidebarItem id="coding" label="Coding" icon={<FileCode2 className="w-5 h-5" />} active={activeTab === 'coding'} accent={accentColor} onClick={() => onTabChange('coding')} />
      <SidebarItem id="memory" label="Memory" icon={<Zap className="w-5 h-5" />} active={activeTab === 'memory'} accent={accentColor} onClick={() => onTabChange('memory')} />
      <SidebarItem id="automations" label="Auto" icon={<Settings className="w-5 h-5" />} active={activeTab === 'automations'} accent={accentColor} onClick={() => onTabChange('automations')} />
      <SidebarItem id="tasks" label="Tasks" icon={<ListTodo className="w-5 h-5" />} active={activeTab === 'tasks'} accent={accentColor} onClick={() => onTabChange('tasks')} />
      <SidebarItem id="media" label="Media" icon={<ImageIcon className="w-5 h-5" />} active={activeTab === 'media'} accent={accentColor} onClick={() => onTabChange('media')} />
      <SidebarItem id="health" label="Health" icon={<HeartPulse className="w-5 h-5" />} active={activeTab === 'health'} accent={accentColor} onClick={() => onTabChange('health')} />
      <SidebarItem id="diagnostics" label="Diag" icon={<Activity className="w-5 h-5" />} active={activeTab === 'diagnostics'} accent={accentColor} onClick={() => onTabChange('diagnostics')} />
      <SidebarItem id="about" label="About" icon={<BookOpen className="w-5 h-5" />} active={activeTab === 'about'} accent={accentColor} onClick={() => onTabChange('about')} />
      <SidebarItem id="skills" label="Skills" icon={<Puzzle className="w-5 h-5" />} active={activeTab === 'skills'} accent={accentColor} onClick={() => onTabChange('skills')} />
      <SidebarItem id="agent" label="Agent" icon={<Bot className="w-5 h-5" />} active={activeTab === 'agent'} accent={accentColor} onClick={() => onTabChange('agent')} />
      <SidebarItem id="browser" label="Browser" icon={<Globe className="w-5 h-5" />} active={activeTab === 'browser'} accent={accentColor} onClick={() => onTabChange('browser')} />
      <SidebarItem id="computer" label="Computer" icon={<Monitor className="w-5 h-5" />} active={activeTab === 'computer'} accent={accentColor} onClick={() => onTabChange('computer')} />
      <SidebarItem id="vision" label="Vision" icon={<Eye className="w-5 h-5" />} active={activeTab === 'vision'} accent={accentColor} onClick={() => onTabChange('vision')} />
      <SidebarItem id="workflows" label="Workflows" icon={<Zap className="w-5 h-5" />} active={activeTab === 'workflows'} accent={accentColor} onClick={() => onTabChange('workflows')} />
      <SidebarItem id="research" label="Research" icon={<FlaskConical className="w-5 h-5" />} active={activeTab === 'research'} accent={accentColor} serious={seriousMode} onClick={() => onTabChange('research')} />
      <SidebarItem id="settings" label="Settings" icon={<Settings className="w-5 h-5" />} active={activeTab === 'settings'} accent={accentColor} onClick={() => onTabChange('settings')} />

      <div className="mt-auto flex flex-col items-center gap-3">
        {onToggleSeriousMode && (
          <button
            onClick={onToggleSeriousMode}
            title={seriousMode ? 'Exit Serious Mode' : 'Enter Serious Mode'}
            className={`group relative w-9 h-9 rounded-full flex items-center justify-center border transition-all hover:scale-110 ${seriousMode ? 'serious-pulse' : ''}`}
            style={{
              borderColor: seriousMode ? 'rgba(255,26,26,0.6)' : `${accentColor}66`,
              background: seriousMode ? 'rgba(255,26,26,0.15)' : `radial-gradient(circle, ${accentColor}22, transparent 70%)`,
              boxShadow: seriousMode ? '0 0 12px rgba(255,26,26,0.4)' : `0 0 12px ${accentColor}44`,
            }}
          >
            <span className="text-[11px] font-bold tracking-wider" style={{ color: seriousMode ? '#ff1a1a' : accentColor }}>
              {seriousMode ? '!' : 'S'}
            </span>
            <span
              className="absolute right-11 whitespace-nowrap text-[9px] tracking-wider uppercase px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ background: '#0a0f1a', color: seriousMode ? '#ff1a1a' : accentColor, border: `1px ${seriousMode ? 'rgba(255,26,26,0.4)' : `${accentColor}44`}` }}
            >
              {seriousMode ? 'Exit Serious Mode' : 'Serious Mode'}
            </span>
          </button>
        )}

        {onSwitchPersona && (
          <button
            onClick={() => onSwitchPersona(nextPersona)}
            title={`Switch to ${nextPersona.toUpperCase()}`}
            className="group relative w-9 h-9 rounded-full flex items-center justify-center border transition-all hover:scale-110"
            style={{
              borderColor: `${accentColor}66`,
              background: `radial-gradient(circle, ${accentColor}22, transparent 70%)`,
              boxShadow: `0 0 12px ${accentColor}44`,
            }}
          >
            <span className="text-[11px] font-bold tracking-wider" style={{ color: accentColor }}>
              {nextPersona[0].toUpperCase()}
            </span>
            <span
              className="absolute right-11 whitespace-nowrap text-[9px] tracking-wider uppercase px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ background: '#0a0f1a', color: accentColor, border: `1px solid ${accentColor}44` }}
            >
              Switch to {nextPersona.toUpperCase()}
            </span>
          </button>
        )}

        <div
          className={[
            'w-2 h-2 rounded-full',
            connection === 'online' ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.6)]' : connection === 'connecting' ? 'bg-yellow-400 animate-pulse' : 'bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.6)]',
          ].join(' ')}
        />
        <span className="text-[8px] text-slate-600 uppercase tracking-wider">
          {connection === 'online' ? 'ONLINE' : connection === 'connecting' ? 'SYNC' : 'OFFLINE'}
        </span>
      </div>
    </div>
  )
}
