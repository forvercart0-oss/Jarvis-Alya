export type OrbState = 'idle' | 'listening' | 'thinking' | 'processing' | 'speaking' | 'error'

export type TabId = 'home' | 'chat' | 'voice' | 'system' | 'tools' | 'coding' | 'memory' | 'automations' | 'media' | 'settings' | 'diagnostics' | 'health' | 'about'

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
  wake_word_enabled: boolean
  wake_word: string
  memory_enabled: boolean
  vector_memory_enabled?: boolean
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
