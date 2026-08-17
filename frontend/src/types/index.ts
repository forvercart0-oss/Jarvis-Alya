export type OrbState = 'idle' | 'listening' | 'thinking' | 'processing' | 'speaking' | 'error'

export type TabId = 'home' | 'chat' | 'voice' | 'system' | 'tools' | 'coding' | 'memory' | 'automations' | 'tasks' | 'workflows' | 'media' | 'settings' | 'diagnostics' | 'health' | 'about' | 'skills' | 'agent' | 'browser' | 'computer' | 'vision' | 'research'

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
  vision_enabled?: boolean
  vision_provider?: string
  vision_confidence_threshold?: number
  vision_local_model?: string
  vision_cloud_model?: string
  vision_max_retries?: number
  vision_cache_ttl?: number
  vision_capture_hotkey?: string
  research_max_sources?: number
  research_depth?: string
  research_document_format?: string
  workflow_max_concurrent?: number
  workflow_default_timeout?: number
  workflow_default_retries?: number
  workflow_quiet_hours_start?: string
  workflow_quiet_hours_end?: string
  workflow_history_retention_days?: number
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

export interface ConversationSummaryItem {
  id: string
  conversation_id: string
  summary: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface ReminderItem {
  id: string
  title: string
  description: string
  due_at: string
  repeat: string
  enabled: boolean
  notified: boolean
  created_at: string
  updated_at: string
}

export interface PrivacySettings {
  privacy_mode?: string
  cloud_sharing?: string
}

export type MemoryType = 'user_preference' | 'user_profile' | 'project' | 'project_preference' | 'workflow' | 'skill' | 'task' | 'conversation' | 'fact' | 'decision' | 'goal' | 'important_context' | 'session' | 'profile' | 'general'
export type MemoryImportance = 'low' | 'medium' | 'high'
export type MemoryStatus = 'active' | 'archived' | 'conflicted' | 'expired'

export interface MemoryItem {
  id: string
  key: string
  value: string
  category?: string
  timestamp: string
  confidence?: number
  source?: string
  project?: string
  profile?: string
  expires_at?: string
  last_used_at?: string
  importance?: number
  access_count?: number
  tags?: string[]
  related_ids?: string[]
  memory_type?: string
  decay_factor?: number
  status?: MemoryStatus
  previous_value?: string
  updated_at?: string
}

export interface MemoryDashboard {
  total_memories: number
  storage_bytes: number
  by_category: Record<string, number>
  by_type: Record<string, number>
  by_importance: Record<string, number>
  recent: Array<{
    id: string
    content: string
    category: string
    memory_type: string
    importance: number
    created_at: string
  }>
  health?: Record<string, any>
}

export interface SessionMemory extends MemoryItem {
  session_id: string
}

export interface MemoryAuditEntry {
  audit_id: string
  event: string
  memory_id?: string
  category?: string
  memory_type?: string
  project?: string
  profile?: string
  detail: string
  timestamp: string
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
  vision?: { enabled: boolean; provider?: string | null; last_capture?: any }
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
  vision?: { enabled: boolean; provider?: string | null; last_capture?: any }
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

export type AgentState = 'idle' | 'planning' | 'waiting_for_permission' | 'waiting_for_user' | 'executing' | 'observing' | 'verifying' | 'recovering' | 'paused' | 'completed' | 'failed' | 'cancelled'

export interface AgentTask {
  task_id: string
  title: string
  type: string
  status: string
  risk: string
  command_category?: string
  arguments: Record<string, any>
  result?: any
  error?: string
  started_at?: string
  finished_at?: string
  retries: number
  max_retries: number
  output?: string
  command?: string
  files_changed?: string[]
  checkpoint_id?: string
  duration_ms?: number
  confidence?: string
  observation?: string
  verification?: string
  requires_approval?: boolean
  dry_run?: boolean
}

export interface AgentPlan {
  plan_id: string
  title: string
  description: string
  tasks: AgentTask[]
  approved: boolean
  project?: string
  autonomy_level?: string
  dry_run?: boolean
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
    autonomy_level?: string
  }
  plan?: AgentPlan
  current_task_index: number
  history: Array<Record<string, any>>
  created_at: string
  updated_at: string
  background_tasks?: string[]
  kill_switch?: boolean
}

export interface AgentDefinition {
  agent_id: string
  name: string
  description: string
  capabilities: string[]
  tools: string[]
  permissions: string[]
  status: string
  priority: string
  version: string
}

export interface OrchestrationTask {
  task_id: string
  user_request: string
  state: string
  plan?: AgentPlan
  results?: Record<string, any>
  errors?: string[]
  agent_assignments?: Record<string, string>
  created_at: number
  completed_at: number
}

export interface AgentMessage {
  sender: string
  receiver: string
  task_id: string
  type: string
  content: any
  metadata: Record<string, any>
  timestamp: string
}

export type OrchestratorState = 'idle' | 'planning' | 'dispatching' | 'running' | 'waiting_permission' | 'verifying' | 'completed' | 'failed' | 'cancelled'

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

export interface TaskStep {
  step_id: string
  title: string
  action: string
  tool?: string
  arguments: Record<string, any>
  risk: string
  verify?: string
  fallback: string[]
  estimated_duration: number
}

export interface TaskPlan {
  plan_id: string
  task_id: string
  title: string
  description: string
  complexity: 'simple' | 'moderate' | 'complex'
  steps: TaskStep[]
  approved: boolean
  dry_run: boolean
  variables: Record<string, any>
  created_at: string
}

export interface TaskItem {
  id: string
  description: string
  status: string
  task_type: string
  complexity: string
  created_at: string
  updated_at: string
  result?: string
  metadata?: Record<string, any>
  retries: number
  max_retries: number
  current_step: number
  total_steps: number
  elapsed_seconds: number
  pid?: number
  schedule?: string
  checkpoints?: Array<Record<string, any>>
  logs?: Array<{ timestamp: string; action: string; result: string; duration_ms: number }>
}

export type SeriousModeState = 'inactive' | 'active'

export interface ResearchJob {
  id: string
  topic: string
  status: 'queued' | 'running' | 'completed' | 'cancelled' | 'failed'
  phase: string
  started_at: number
  completed_at: number | null
  sources_found: number
  sources_processed: number
  claims_checked: number
  document_path: string
  error: string
}

export interface ResearchSource {
  title: string
  url: string
  publisher: string
  publication_date: string
  source_type: string
}

export interface BrowserSession {
  session_id: string
  url: string
  title: string
  tabs: Array<{ title: string; url: string }>
  active_tab_index: number
  connected: boolean
  error?: string
}

export interface BrowserSettings {
  enabled: boolean
  engine: string
  mode: string
  profile: string
  download_dir: string
  search_engine: string
  permission: string
  timeout: number
  max_retries: number
  trusted_domains: string[]
  visual_fallback: boolean
  ask_before_send: boolean
  ask_before_post: boolean
  ask_before_upload: boolean
  ask_before_download: boolean
  ask_before_purchase: boolean
  auto_captcha_pause: boolean
  max_actions: number
  max_page_reloads: number
  dom_first: boolean
}

export interface BrowserTask {
  goal: string
  state: string
  steps: Array<{ action: string; result: any; count: number }>
  current_step: number
  error?: string
}

export interface BrowserElement {
  type: string
  role: string
  text: string
  label: string
  selector: string
  visible: boolean
  enabled: boolean
  confidence: number
}

export interface ComputerStatus {
  platform: string
  available: boolean
  mode: string
  active_window?: string
  cursor?: { x: number; y: number }
  monitors?: Array<{ id: string; width: number; height: number; scale: number }>
  takeover?: boolean
  task?: ComputerTask
}

export interface ComputerSettings {
  enabled: boolean
  mode: string
  screen_access: string
  mouse_control: string
  keyboard_control: string
  application_launch: string
  window_control: string
  screen_preview: string
  mouse_failsafe: boolean
  max_retries: number
  file_automation: string
  terminal_automation: string
  process_control: string
  trust_level: string
  emergency_stop: string
  automation_timeout: number
  max_task_steps: number
  visual_confidence: number
  window_layouts: boolean
  clipboard_access: string
}

export interface ComputerTask {
  goal: string
  state: string
  steps: Array<{ action: string; result: any; count: number }>
  current_step: number
  error?: string
}

export interface WindowInfo {
  window_id: string
  title: string
  application: string
  process: string
  x: number
  y: number
  width: number
  height: number
  state: string
  monitor: number
}

export interface VisionStatus {
  enabled: boolean
  provider?: string | null
  providers?: number
  last_capture?: any
  confidence_threshold?: number
  camera_active?: boolean
  screen_access?: boolean
  continuous_vision?: boolean
  visual_overlay?: boolean
}

export interface VisionSettings {
  enabled: boolean
  provider: string
  confidence_threshold: number
  local_model: string
  cloud_model: string
  max_retries: number
  cache_ttl: number
  capture_hotkey: string
  max_image_size_mb: number
  max_image_width: number
  max_image_height: number
  image_quality: number
  ocr_enabled: boolean
  camera_enabled: boolean
  screen_analysis_enabled: boolean
  remember_visual_context: boolean
  external_provider_allowed: boolean
  screen_access: boolean
  continuous_vision: boolean
  camera_access: boolean
  visual_overlay: boolean
  screen_history_minutes: number
  max_visual_steps: number
  ocr_preprocessing: boolean
  offline_fallback: boolean
  prompt_injection_protection: boolean
}

export type WorkflowStatus = 'draft' | 'active' | 'paused' | 'running' | 'waiting' | 'completed' | 'failed' | 'cancelled'
export type WorkflowTriggerType = 'one_time' | 'scheduled' | 'recurring' | 'event_based' | 'manual' | 'conditional'

export interface WorkflowStep {
  step_id: string
  type: string
  name: string
  description?: string
  config?: Record<string, any>
  next_step_id?: string | null
  condition?: Record<string, any> | null
  retry_policy?: Record<string, any> | null
  timeout_seconds?: number
  order: number
}

export interface Workflow {
  workflow_id: string
  name: string
  description?: string
  trigger?: Record<string, any>
  steps?: WorkflowStep[]
  variables?: Record<string, any>
  permissions?: Record<string, any>
  status: WorkflowStatus
  enabled: boolean
  created_at: string
  updated_at: string
  last_run?: string | null
  next_run?: string | null
  tags?: string[]
  project?: string | null
}

export interface WorkflowRun {
  run_id: string
  workflow_id: string
  status: WorkflowStatus
  started_at: string
  finished_at?: string | null
  duration_seconds?: number
  steps?: Array<Record<string, any>>
  errors?: Array<Record<string, any>>
  result?: Record<string, any> | null
}

export interface WorkflowApproval {
  approval_id: string
  workflow_id: string
  run_id: string
  step_id: string
  action: string
  arguments: Record<string, any>
  risk_level: string
  status: string
  created_at: string
  resolved_at?: string | null
}
