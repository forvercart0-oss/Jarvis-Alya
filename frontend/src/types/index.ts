export type OrbState = 'idle' | 'listening' | 'thinking' | 'processing' | 'speaking' | 'error'

export type TabId = 'home' | 'chat' | 'voice' | 'system' | 'tools' | 'coding' | 'memory' | 'automations' | 'media' | 'settings' | 'diagnostics' | 'health' | 'about' | 'skills' | 'agent' | 'browser' | 'computer'

export type ConnectionState = 'connecting' | 'online' | 'offline'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  provider?: string
  toolCalls?: ToolCall[]
}

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, any>
  result?: any
  status: 'running' | 'success' | 'error'
}

export interface SystemStats {
  cpu: { percent: number | null; error?: string }
  ram: { percent: number | null; used_gb?: number; total_gb?: number; error?: string }
  disk: { percent: number | null; path?: string; error?: string }
  battery: { present: boolean; percent?: number; power_plugged?: boolean; error?: string }
  network: { error?: string; interfaces?: string[] }
  uptime: { seconds: number | null; error?: string }
  os: { name?: string; version?: string; kernel?: string; hostname?: string; error?: string }
}

export interface JarvisSettings {
  assistant_name: string
  user_name: string
  persona: string
  voice_enabled: boolean
  voice_language: string
  tts_enabled: boolean
  tts_engine: string
  tts_voice: string
  tts_speed: number
  tts_volume: number
  tts_cache_dir?: string
  wake_word_enabled: boolean
  wake_word: string
  memory_enabled: boolean
  vector_memory_enabled?: boolean
  message_notifications_enabled?: boolean
  browser_notifications_enabled?: boolean
  voice_notifications_enabled?: boolean
  desktop_notifications_enabled?: boolean
  groq_model: string
  groq_api_key: string
  gemini_api_key: string
  gemini_model: string
  openrouter_api_key: string
  openrouter_model: string
  local_llm_enabled: boolean
  local_llm_url: string
  local_llm_model: string
  local_llm_api_type: string
  local_llm_timeout: number
  auto_failover: boolean
  provider_priority: string
  response_style: string
  language: string
  theme: string
  accent_color: string
  glow_intensity: number
  animation_level: string
  orb_size: number
  compact_ui?: boolean
  panel_transparency?: number
  background_particles?: boolean
  reduced_motion?: boolean
  font_size?: string
  ui_preset?: string
  language_mode?: string
  image_generation_enabled?: boolean
  image_provider?: string
  pixazo_api_key?: string
  puter_api_key?: string
  video_generation_enabled?: boolean
  video_provider?: string
  fal_api_key?: string
  magic_hour_api_key?: string
  gesture_control_enabled?: boolean
  gesture_camera_device?: string
  gesture_sensitivity?: number
  call_control_enabled?: boolean
  call_provider?: string
  call_api_key?: string
  call_assist_mode?: string
}

export interface PersonaInfo {
  id: string
  name: string
  gender: string
  accent_color: string
  secondary_color: string
  logo_id: string
  default_voice: string
  description: string
  assistant_name?: string
  tts_voice?: string
  available?: string[]
}

export interface ProviderStatus {
  status: 'online' | 'offline' | 'unknown'
  provider?: string
  model?: string
  url?: string
  api_type?: string
  latency_ms?: number
  error?: string
}

export interface ToolInfo {
  name: string
  description: string
  requires_confirmation: boolean
}

export interface MemoryItem {
  id: string
  key: string
  value: string
  category?: string
  timestamp: string
}

export interface Automation {
  id: string
  name: string
  trigger: string
  action: string
  schedule?: string
  keywords?: string[]
  action_payload?: Record<string, any>
  enabled: boolean
}

export interface ConversationSummary {
  id: string
  title: string | null
  timestamp: string
  message_count: number
  preview?: string
}

export interface NotificationItem {
  id: number
  message: string
  type: string
  timestamp: string
  data?: Record<string, any>
}

export interface HealthStatus {
  status?: string
  assistant?: string
  providers: Record<string, ProviderStatus>
  tts: { status: string; backend?: string | null; engine?: string }
  voice: { status: string; mic?: boolean }
  database: { status: string }
  websocket: { status: string; connections?: number }
}

export interface DiagnosticInfo {
  version: string
  assistant: string
  user: string
  uptime_seconds: number
  os: { name?: string; kernel?: string; hostname?: string }
  providers: Record<string, ProviderStatus>
  active_provider: string | null
  provider_count: number
  tools: number
  database: { status: string; error?: string }
  websocket_clients: number
  websocket: { status: string; connections?: number }
  tts: { available: boolean; backend: string | null; engine: string; voice: string; voices: number }
  pipewire: { status: string; error?: string }
  voice: { initialized: boolean; mic_available: boolean; tts_available: boolean }
  memory: { conversations: number }
  image?: Array<{ id?: string; prompt?: string; provider?: string; date?: string; url?: string }>
  video?: Array<{ id?: string; prompt?: string; provider?: string; date?: string; url?: string }>
  python: string
}

export interface VoiceCatalogEntry {
  id: string
  label: string
  group: string
  gender: string
  engine: string
}

export interface VoiceInfo {
  voices: string[]
  catalog: VoiceCatalogEntry[]
  current: string
  engine: string
  backend: string | null
  tts_available: boolean
  mic_available: boolean
}

export interface CodingProject {
  name: string
  files: number
  updated: string | null
  stack: string | null
  description?: string
  created?: string
  slug?: string
}

export interface ProjectFileEntry {
  path: string
  size: number
}

export interface SystemHistoryPoint {
  time: number
  value: number
}

export interface WsEvent {
  event: string
  data: any
}

export type SkillPriority = 'high' | 'normal' | 'low'

export interface SkillPermissions {
  network?: boolean
  filesystem_read?: boolean
  filesystem_write?: boolean
  terminal?: boolean
  camera?: boolean
  microphone?: boolean
  notifications?: boolean
  clipboard_read?: boolean
  clipboard_write?: boolean
  calls?: boolean
  messages?: boolean
  browser_read?: boolean
  browser_control?: boolean
}

export interface Skill {
  id: string
  name: string
  version: string
  description: string
  author: string
  enabled: boolean
  priority: SkillPriority
  triggers: string[]
  capabilities: string[]
  instructions: string[]
  permissions: SkillPermissions
  uses_memory?: boolean
  category?: string
  icon?: string
  created_at?: string
  updated_at?: string
}

export interface SkillActivity {
  id: string
  skill_id: string
  skill_name: string
  action: string
  timestamp: string
  permission: string
  result: 'success' | 'error' | 'denied'
}

export type AgentState = 'idle' | 'planning' | 'waiting_approval' | 'executing' | 'waiting_confirmation' | 'testing' | 'completed' | 'failed' | 'cancelled'

export interface AgentTask {
  task_id: string
  title: string
  type: string
  status: string
  risk: string
  arguments: Record<string, any>
  result?: any
  error?: string
  started_at?: string
  finished_at?: string
  retries: number
  max_retries: number
}

export interface AgentPlan {
  plan_id: string
  title: string
  description: string
  tasks: AgentTask[]
  approved: boolean
  project?: string
  created_at: string
}

export interface AgentSession {
  session_id: string
  state: AgentState
  context?: {
    user_request: string
    project?: string
    project_root?: string
    language?: string
    persona?: string
  }
  plan?: AgentPlan
  current_task_index: number
  history: Array<Record<string, any>>
  created_at: string
  updated_at: string
}

export interface GitStatus {
  path: string
  branch?: string
  ahead: number
  behind: number
  modified: string[]
  added: string[]
  deleted: string[]
  untracked: string[]
  clean: boolean
  error?: string
}

export interface GitDiff {
  path: string
  old_path?: string
  added?: boolean
  deleted?: boolean
  renamed?: boolean
  hunks: Array<Record<string, any>>
}
