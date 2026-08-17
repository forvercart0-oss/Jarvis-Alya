import type { JarvisSettings, HealthStatus, MemoryItem, MemoryDashboard, SessionMemory, MemoryAuditEntry, Automation, ToolInfo, Message, SystemStats, ConversationSummary, NotificationItem, DiagnosticInfo, VoiceInfo, CodingProject, ProjectFileEntry, PersonaInfo, Skill, SkillActivity, GitStatus, ResearchJob, Workflow, WorkflowRun, WorkflowApproval, WorkflowStep, AdaptivePreference, Suggestion, EnvironmentProfile, PersonalizationContext, PersonalizationAnalytics } from '../types'

const isTauri = !!(window as any).__TAURI__ || !!(window as any).__TAURI_INTERNALS__
const API_BASE = isTauri ? 'http://127.0.0.1:8000/api' : '/api'

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`API ${res.status}: ${text}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  async getHealth(): Promise<HealthStatus> {
    return request<HealthStatus>('/health')
  },

  async sendChat(message: string): Promise<{ response: string }> {
    return request<{ response: string }>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    })
  },

  async getSystemStats(): Promise<SystemStats> {
    return request<SystemStats>('/system/stats')
  },

  async getPersona(): Promise<PersonaInfo> {
    return request<PersonaInfo>('/persona')
  },

  async switchPersona(persona: string): Promise<PersonaInfo> {
    return request<PersonaInfo>('/persona', {
      method: 'POST',
      body: JSON.stringify({ persona }),
    })
  },

  async getSettings(): Promise<JarvisSettings> {
    return request<JarvisSettings>('/settings')
  },

  async updateSettings(patch: Partial<JarvisSettings>): Promise<JarvisSettings> {
    return request<JarvisSettings>('/settings', {
      method: 'PUT',
      body: JSON.stringify(patch),
    })
  },

  async getMemory(): Promise<MemoryItem[]> {
    return request<MemoryItem[]>('/memory')
  },

  async addMemory(content: string, category?: string, project?: string, profile?: string): Promise<any> {
    return request('/memory', {
      method: 'POST',
      body: JSON.stringify({ content, category, project, profile }),
    })
  },

  async searchMemory(query: string, category?: string, project?: string, profile?: string, minConfidence?: number, limit?: number): Promise<MemoryItem[]> {
    const params = new URLSearchParams({ query })
    if (category) params.set('category', category)
    if (project) params.set('project', project)
    if (profile) params.set('profile', profile)
    if (minConfidence !== undefined) params.set('min_confidence', String(minConfidence))
    if (limit) params.set('limit', String(limit))
    return request<MemoryItem[]>(`/memory/search?${params.toString()}`)
  },

  async getMemoryStats(): Promise<any> {
    return request('/memory/stats')
  },

  async getMemoryCategories(): Promise<{ categories: string[] }> {
    return request('/memory/categories')
  },

  async updateMemory(id: string, content: string, confidence?: number, source?: string): Promise<any> {
    return request(`/memory/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ content, confidence, source }),
    })
  },

  async getPreferences(profile?: string): Promise<MemoryItem[]> {
    const q = profile ? `?profile=${encodeURIComponent(profile)}` : ''
    return request<MemoryItem[]>(`/memory/preferences${q}`)
  },

  async setPreference(key: string, value: string, profile?: string): Promise<any> {
    return request('/memory/preferences', {
      method: 'POST',
      body: JSON.stringify({ key, value, profile }),
    })
  },

  async getProjects(): Promise<{ projects: string[] }> {
    return request('/memory/projects')
  },

  async getProjectMemory(project: string, query?: string, limit?: number): Promise<MemoryItem[]> {
    const params = new URLSearchParams()
    if (query) params.set('query', query)
    if (limit) params.set('limit', String(limit))
    const qs = params.toString() ? `?${params.toString()}` : ''
    return request<MemoryItem[]>(`/memory/projects/${encodeURIComponent(project)}${qs}`)
  },

  async getConversationSummaries(conversationId?: string, limit?: number): Promise<any[]> {
    const params = new URLSearchParams()
    if (conversationId) params.set('conversation_id', conversationId)
    if (limit) params.set('limit', String(limit))
    const qs = params.toString() ? `?${params.toString()}` : ''
    return request<any[]>(`/memory/summaries${qs}`)
  },

  async createConversationSummary(conversationId: string, summary: string, messageCount?: number): Promise<any> {
    return request('/memory/summaries', {
      method: 'POST',
      body: JSON.stringify({ conversation_id: conversationId, summary, message_count: messageCount }),
    })
  },

  async getPrivacySettings(): Promise<any> {
    return request('/memory/privacy')
  },

  async setPrivacyMode(mode: string): Promise<any> {
    return request('/memory/privacy', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    })
  },

  async getMemoryHealth(): Promise<any> {
    return request('/memory/health')
  },

  async searchMemoriesRanked(query: string, category?: string, project?: string, profile?: string, limit = 20): Promise<MemoryItem[]> {
    const params = new URLSearchParams({ query })
    if (category) params.set('category', category)
    if (project) params.set('project', project)
    if (profile) params.set('profile', profile)
    params.set('limit', String(limit))
    return request<MemoryItem[]>(`/memory/ranked?${params.toString()}`)
  },

  async getMemoryContext(query: string, project?: string, profile = 'jarvis', maxMemories = 8, maxTokens = 2000): Promise<any> {
    const params = new URLSearchParams({ query, profile })
    if (project) params.set('project', project)
    params.set('max_memories', String(maxMemories))
    params.set('max_tokens', String(maxTokens))
    return request(`/memory/context?${params.toString()}`)
  },

  async getMemoryDuplicates(threshold = 0.85): Promise<{ duplicates: any[] }> {
    return request(`/memory/duplicates?threshold=${threshold}`)
  },

  async getMemoryContradictions(): Promise<{ contradictions: any[] }> {
    return request('/memory/contradictions')
  },

  async applyMemoryDecay(decayRate = 0.01): Promise<{ updated: number }> {
    return request('/memory/decay', {
      method: 'POST',
      body: JSON.stringify({ decay_rate: decayRate }),
    })
  },

  async getRelatedMemories(memoryId: string, limit = 10): Promise<{ related: any[] }> {
    return request(`/memory/${encodeURIComponent(memoryId)}/related?limit=${limit}`)
  },

  async exportMemories(category?: string, project?: string, profile?: string): Promise<any> {
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (project) params.set('project', project)
    if (profile) params.set('profile', profile)
    const qs = params.toString() ? `?${params.toString()}` : ''
    return request(`/memory/export${qs}`)
  },

  async importMemories(data: any, mode = 'merge'): Promise<any> {
    return request('/memory/import', {
      method: 'POST',
      body: JSON.stringify({ data, mode }),
    })
  },

  async updateMemoryFields(id: string, updates: Record<string, any>): Promise<any> {
    return request(`/memory/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  },

  async getMemoryDashboard(): Promise<MemoryDashboard> {
    return request<MemoryDashboard>('/memory/dashboard')
  },

  async confirmMemory(content: string, category?: string, importance?: string, memoryType?: string): Promise<any> {
    return request('/memory/confirm', {
      method: 'POST',
      body: JSON.stringify({ content, category, importance, memory_type: memoryType }),
    })
  },

  async rememberSessionMemory(sessionId: string, content: string, category = 'general', memoryType = 'fact', importance = 0.5, expiresAt?: string): Promise<any> {
    return request('/memory/session', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, content, category, memory_type: memoryType, importance, expires_at: expiresAt }),
    })
  },

  async getSessionMemories(sessionId: string, limit = 50): Promise<{ memories: SessionMemory[] }> {
    return request(`/memory/session/${encodeURIComponent(sessionId)}?limit=${limit}`)
  },

  async clearSessionMemories(sessionId: string): Promise<{ status: string; count: number }> {
    return request(`/memory/session/${encodeURIComponent(sessionId)}`, { method: 'DELETE' })
  },

  async getMemoryAudit(limit = 100): Promise<{ audit: MemoryAuditEntry[] }> {
    return request(`/memory/audit?limit=${limit}`)
  },

  async resolveMemoryConflict(memoryId: string, keep = true): Promise<any> {
    return request('/memory/conflicts/resolve', {
      method: 'POST',
      body: JSON.stringify({ memory_id: memoryId, keep }),
    })
  },

  async getReminders(enabled?: boolean): Promise<any[]> {
    const q = enabled !== undefined ? `?enabled=${enabled}` : ''
    return request<any[]>(`/reminders${q}`)
  },

  async createReminder(title: string, description?: string, dueAt?: string, repeat?: string): Promise<any> {
    return request('/reminders', {
      method: 'POST',
      body: JSON.stringify({ title, description, due_at: dueAt, repeat }),
    })
  },

  async updateReminder(id: string, updates: Record<string, any>): Promise<any> {
    return request(`/reminders/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  },

  async deleteReminder(id: string): Promise<void> {
    return request(`/reminders/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  async deleteMemory(key: string): Promise<void> {
    return request(`/memory/${encodeURIComponent(key)}`, { method: 'DELETE' })
  },

  async getTools(): Promise<ToolInfo[]> {
    return request<ToolInfo[]>('/tools')
  },

  async executeTool(name: string, args: Record<string, any>): Promise<any> {
    return request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name, arguments: args }),
    })
  },

  async getAutomations(): Promise<Automation[]> {
    return request<Automation[]>('/automations')
  },

  async createAutomation(automation: Omit<Automation, 'id'>): Promise<Automation> {
    return request<Automation>('/automations', {
      method: 'POST',
      body: JSON.stringify(automation),
    })
  },

  async updateAutomation(id: string, patch: Partial<Automation>): Promise<Automation> {
    return request<Automation>(`/automations/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(patch),
    })
  },

  async deleteAutomation(id: string): Promise<void> {
    return request(`/automations/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  async getTasks(status?: string): Promise<any[]> {
    const q = status ? `?status=${encodeURIComponent(status)}` : ''
    return request<any[]>(`/tasks${q}`)
  },

  async getActiveTasks(): Promise<any[]> {
    return request<any[]>('/tasks/active')
  },

  async getTask(id: string): Promise<any> {
    return request<any>(`/tasks/${encodeURIComponent(id)}`)
  },

  async createTask(payload: { description: string; task_type?: string; auto_execute?: boolean; context?: Record<string, any> }): Promise<any> {
    return request<any>('/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async startTask(id: string): Promise<any> {
    return request<any>(`/tasks/${encodeURIComponent(id)}/start`, { method: 'POST' })
  },

  async pauseTask(id: string): Promise<any> {
    return request<any>(`/tasks/${encodeURIComponent(id)}/pause`, { method: 'POST' })
  },

  async resumeTask(id: string): Promise<any> {
    return request<any>(`/tasks/${encodeURIComponent(id)}/resume`, { method: 'POST' })
  },

  async cancelTask(id: string): Promise<any> {
    return request<any>(`/tasks/${encodeURIComponent(id)}/cancel`, { method: 'POST' })
  },

  async approveTask(id: string): Promise<any> {
    return request<any>(`/tasks/${encodeURIComponent(id)}/approve`, { method: 'POST' })
  },

  async denyTask(id: string): Promise<any> {
    return request<any>(`/tasks/${encodeURIComponent(id)}/deny`, { method: 'POST' })
  },

  async deleteTask(id: string): Promise<void> {
    return request(`/tasks/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  async createTaskAdvanced(payload: { description: string; task_type?: string; auto_execute?: boolean; context?: Record<string, any>; dry_run?: boolean }): Promise<any> {
    return request<any>('/tasks/advanced', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async getTaskQueue(): Promise<{ queue: any[] }> {
    return request('/tasks/queue')
  },

  async getTaskProcesses(): Promise<{ processes: any[] }> {
    return request('/tasks/processes')
  },

  async setTaskAutonomy(level: string): Promise<{ level: string }> {
    return request('/tasks/autonomy', {
      method: 'POST',
      body: JSON.stringify({ level }),
    })
  },

  async getTasksByProject(project: string): Promise<any[]> {
    return request<any[]>(`/tasks/project/${encodeURIComponent(project)}`)
  },

  async retryTask(id: string): Promise<any> {
    return request<any>(`/tasks/${encodeURIComponent(id)}/retry`, { method: 'POST' })
  },

  async speak(text: string): Promise<{ success: boolean }> {
    return request<{ success: boolean }>('/voice/speak', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },

  async listen(): Promise<{ transcript?: string }> {
    return request<{ transcript?: string }>('/voice/listen', { method: 'POST' })
  },

  async getHistory(): Promise<Message[]> {
    return request<Message[]>('/history')
  },

  async clearHistory(): Promise<void> {
    return request('/history', { method: 'DELETE' })
  },

  async getConversations(limit: number = 50): Promise<ConversationSummary[]> {
    return request<ConversationSummary[]>(`/memory/conversations?limit=${limit}`)
  },

  async getConversationMessages(conversationId: string, limit: number = 200): Promise<Message[]> {
    return request<Message[]>(`/memory/conversations/${encodeURIComponent(conversationId)}?limit=${limit}`)
  },

  async deleteConversation(conversationId: string): Promise<void> {
    return request(`/memory/conversations/${encodeURIComponent(conversationId)}`, { method: 'DELETE' })
  },

  async testVoice(text: string): Promise<{ status: string }> {
    return request<{ status: string }>('/voice/test', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },

  async getVoiceStatus(): Promise<{
    initialized: boolean
    mic_available: boolean
    tts_available: boolean
    tts_backend: string | null
    tts_engine: string
    speaking: boolean
  }> {
    return request('/voice/status')
  },

  async getVoiceVoices(): Promise<{ voices: string[]; engine: string; backend: string | null; tts_available: boolean; mic_available: boolean }> {
    return request('/voice/voices')
  },

  async getNotifications(limit: number = 20): Promise<NotificationItem[]> {
    return request<NotificationItem[]>(`/notifications?limit=${limit}`)
  },

  async getSystemHistory(): Promise<{ cpu: any[]; ram: any[] }> {
    return request('/system/history')
  },

  async getDiagnostics(): Promise<DiagnosticInfo> {
    return request<DiagnosticInfo>('/system/diagnostics')
  },

  async getVoiceInfo(): Promise<VoiceInfo> {
    return request<VoiceInfo>('/voice/voices')
  },

  async listProjects(): Promise<{ projects: CodingProject[]; base_dir: string }> {
    const res: any = await request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name: 'list_projects', arguments: {} }),
    })
    return res?.result ?? res
  },

  async createProject(payload: { name: string; description?: string; stack?: string }): Promise<any> {
    const res: any = await request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name: 'create_project', arguments: payload }),
    })
    return res?.result ?? res
  },

  async deleteProject(name: string): Promise<any> {
    const res: any = await request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name: 'delete_project', arguments: { name } }),
    })
    return res?.result ?? res
  },

  async listProjectFiles(name: string): Promise<{ files: ProjectFileEntry[] }> {
    const res: any = await request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name: 'list_project_files', arguments: { name } }),
    })
    return res?.result ?? res
  },

  async readProjectFile(name: string, path: string): Promise<{ content: string; path: string; size: number }> {
    const res: any = await request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name: 'read_project_file', arguments: { name, path } }),
    })
    return res?.result ?? res
  },

  async writeProjectFile(name: string, path: string, content: string): Promise<any> {
    const res: any = await request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name: 'write_project_file', arguments: { name, path, content } }),
    })
    return res?.result ?? res
  },

  async runProjectCommand(name: string, command: string): Promise<any> {
    const res: any = await request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name: 'run_project_command', arguments: { name, command } }),
    })
    return res?.result ?? res
  },

  async takeScreenshot(): Promise<{ format: string; data: string }> {
    const res: any = await request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name: 'take_screenshot', arguments: {} }),
    })
    return res?.result ?? res
  },

  async generateImage(prompt: string, provider?: string, width = 1024, height = 1024, negativePrompt = ''): Promise<any> {
    return request('/generate/image', {
      method: 'POST',
      body: JSON.stringify({ prompt, provider, width, height, negative_prompt: negativePrompt }),
    })
  },

  async generateVideo(prompt: string, provider?: string, duration = 5, resolution = '720p', aspectRatio = '16:9'): Promise<any> {
    return request('/generate/video', {
      method: 'POST',
      body: JSON.stringify({ prompt, provider, duration, resolution, aspect_ratio: aspectRatio }),
    })
  },

  async listSkills(): Promise<Skill[]> {
    return request<Skill[]>('/skills')
  },

  async getSkill(id: string): Promise<Skill> {
    return request<Skill>(`/skills/${encodeURIComponent(id)}`)
  },

  async createSkill(skill: Partial<Skill>): Promise<{ id: string }> {
    return request<{ id: string }>('/skills', {
      method: 'POST',
      body: JSON.stringify(skill),
    })
  },

  async updateSkill(id: string, patch: Partial<Skill>): Promise<Skill> {
    return request<Skill>(`/skills/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(patch),
    })
  },

  async deleteSkill(id: string): Promise<void> {
    return request(`/skills/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  async toggleSkill(id: string, enabled: boolean): Promise<Skill> {
    return request<Skill>(`/skills/${encodeURIComponent(id)}/toggle`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    })
  },

  async reloadSkills(): Promise<{ status: string }> {
    return request('/skills/reload', { method: 'POST' })
  },

  async getSkillActivity(id?: string): Promise<SkillActivity[]> {
    const path = id ? `/skills/${encodeURIComponent(id)}/activity` : '/skills/activity'
    return request<SkillActivity[]>(path)
  },

  async exportSkill(id: string): Promise<string> {
    const res = await fetch(`${API_BASE}/skills/${encodeURIComponent(id)}/export`)
    if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
    const data = await res.json()
    return data.json
  },

  async importSkill(jsonString: string): Promise<{ id: string }> {
    return request<{ id: string }>('/skills/import', {
      method: 'POST',
      body: JSON.stringify({ json: jsonString }),
    })
  },

  async agentStart(message: string, project?: string): Promise<any> {
    return request('/agent/start', {
      method: 'POST',
      body: JSON.stringify({ message, project }),
    })
  },

  async agentStartWithOptions(message: string, options?: { project?: string; project_root?: string; persona?: string; autonomy_level?: string; dry_run?: boolean }): Promise<any> {
    return request('/agent/start', {
      method: 'POST',
      body: JSON.stringify({ message, ...options }),
    })
  },

  async agentApprove(sessionId: string): Promise<any> {
    return request('/agent/approve', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async agentCancel(sessionId: string): Promise<any> {
    return request('/agent/cancel', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async agentPause(sessionId: string): Promise<any> {
    return request('/agent/pause', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async agentResume(sessionId: string): Promise<any> {
    return request('/agent/resume', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async agentKill(sessionId: string): Promise<any> {
    return request('/agent/kill', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async getAgentStatus(sessionId: string): Promise<any> {
    return request(`/agent/status/${encodeURIComponent(sessionId)}`)
  },

  async getAgentSessions(): Promise<{ sessions: any[] }> {
    return request('/agent/sessions')
  },

  async agentOrchestrate(message: string, persona = 'jarvis', autonomyLevel = 'assisted'): Promise<any> {
    return request('/agent/orchestrate', {
      method: 'POST',
      body: JSON.stringify({ message, persona, autonomy_level: autonomyLevel }),
    })
  },

  async getAgentRegistry(): Promise<{ agents: any[] }> {
    return request('/agent/registry')
  },

  async getOrchestratorTasks(): Promise<{ tasks: any[] }> {
    return request('/agent/orchestrator/tasks')
  },

  async getOrchestratorTask(taskId: string): Promise<any> {
    return request(`/agent/orchestrator/tasks/${encodeURIComponent(taskId)}`)
  },

  async cancelOrchestratorTask(taskId: string): Promise<any> {
    return request(`/agent/orchestrator/tasks/${encodeURIComponent(taskId)}/cancel`, { method: 'POST' })
  },

  async getGitStatus(path: string): Promise<GitStatus> {
    return request<GitStatus>(`/git/status?path=${encodeURIComponent(path)}`)
  },

  async getVisionStatus(): Promise<{ enabled: boolean; provider?: string | null }> {
    return request('/vision/status')
  },

  async visionScreenshot(mode: string = 'full', window?: string, region?: string, monitor?: number): Promise<any> {
    return request('/vision/screenshot', {
      method: 'POST',
      body: JSON.stringify({ mode, window, region, monitor }),
    })
  },

  async visionAnalyze(imagePath: string, mode: string = 'describe', prompt?: string): Promise<any> {
    return request('/vision/analyze', {
      method: 'POST',
      body: JSON.stringify({ image_path: imagePath, mode, prompt }),
    })
  },

  async visionFind(target: string, region?: string): Promise<any> {
    return request('/vision/find', {
      method: 'POST',
      body: JSON.stringify({ target, region }),
    })
  },

  async visionOcr(imagePath: string, region?: string): Promise<any> {
    return request('/vision/ocr', {
      method: 'POST',
      body: JSON.stringify({ image_path: imagePath, region }),
    })
  },

  async visionActiveWindow(): Promise<any> {
    return request('/vision/active_window')
  },

  async visionScreenInfo(): Promise<{ width: number; height: number }> {
    return request('/vision/screen_info')
  },

  async visionMonitors(): Promise<{ monitors: any[] }> {
    return request('/vision/monitors')
  },

  async visionMouseClick(x: number, y: number, button?: number): Promise<any> {
    return request('/vision/mouse/click', {
      method: 'POST',
      body: JSON.stringify({ x, y, button }),
    })
  },

  async visionMouseDoubleClick(x: number, y: number): Promise<any> {
    return request('/vision/mouse/double_click', {
      method: 'POST',
      body: JSON.stringify({ x, y }),
    })
  },

  async visionMouseDrag(x1: number, y1: number, x2: number, y2: number): Promise<any> {
    return request('/vision/mouse/drag', {
      method: 'POST',
      body: JSON.stringify({ x1, y1, x2, y2 }),
    })
  },

  async visionMouseScroll(x: number, y: number, direction: string = 'down', amount?: number): Promise<any> {
    return request('/vision/mouse/scroll', {
      method: 'POST',
      body: JSON.stringify({ x, y, direction, amount }),
    })
  },

  async visionKeyboardType(text: string): Promise<any> {
    return request('/vision/keyboard/type', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },

  async visionKeyboardHotkey(keys: string[]): Promise<any> {
    return request('/vision/keyboard/hotkey', {
      method: 'POST',
      body: JSON.stringify({ keys }),
    })
  },

  async visionKeyboardPress(key: string): Promise<any> {
    return request('/vision/keyboard/press', {
      method: 'POST',
      body: JSON.stringify({ key }),
    })
  },

  async visionCompare(imageA: string, imageB: string): Promise<any> {
    return request('/vision/compare', {
      method: 'POST',
      body: JSON.stringify({ image_a: imageA, image_b: imageB }),
    })
  },

  async visionCameraStart(): Promise<any> {
    return request('/vision/camera/start', { method: 'POST' })
  },

  async visionCameraStop(): Promise<any> {
    return request('/vision/camera/stop', { method: 'POST' })
  },

  async visionCameraCapture(): Promise<any> {
    return request('/vision/camera/capture', { method: 'POST' })
  },

  async visionRegionAnalyze(imagePath: string, region: string, prompt?: string): Promise<any> {
    return request('/vision/region/analyze', {
      method: 'POST',
      body: JSON.stringify({ image_path: imagePath, region, prompt }),
    })
  },

  async visionRemember(imagePath: string, description: string, tags?: string[], project?: string): Promise<any> {
    return request('/vision/remember', {
      method: 'POST',
      body: JSON.stringify({ image_path: imagePath, description, tags: tags || [], project: project || '' }),
    })
  },

  async visionQA(imagePath: string, question: string): Promise<any> {
    return request('/vision/qa', {
      method: 'POST',
      body: JSON.stringify({ image_path: imagePath, question }),
    })
  },

  async visionWindows(): Promise<{ windows: string[] }> {
    return request('/vision/windows')
  },

  async visionCameras(): Promise<{ cameras: any[] }> {
    return request('/vision/cameras')
  },

  async visionSensitiveCheck(text: string, windowTitle?: string): Promise<{ sensitive: boolean; reason: string }> {
    return request('/vision/sensitive/check', {
      method: 'POST',
      body: JSON.stringify({ text, window_title: windowTitle }),
    })
  },

  async visionSensitiveRedact(text: string): Promise<{ redacted: string }> {
    return request('/vision/sensitive/redact', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },

  async startResearch(topic: string): Promise<{ job_id: string; topic: string; status: string }> {
    return request('/research/start', {
      method: 'POST',
      body: JSON.stringify({ topic }),
    })
  },

  async cancelResearch(jobId: string): Promise<{ cancelled: boolean }> {
    return request(`/research/${encodeURIComponent(jobId)}/cancel`, { method: 'POST' })
  },

  async getResearchJobs(): Promise<{ jobs: ResearchJob[] }> {
    return request('/research/jobs')
  },

  async getResearchJob(jobId: string): Promise<any> {
    return request(`/research/${encodeURIComponent(jobId)}`)
  },

  async getResearchSettings(): Promise<{ max_sources: number; research_depth: string; document_format: string }> {
    return request('/research/settings')
  },

  async updateResearchSettings(patch: Record<string, any>): Promise<any> {
    return request('/research/settings', {
      method: 'PUT',
      body: JSON.stringify(patch),
    })
  },

  async startAgent(message: string, project?: string): Promise<any> {
    return request('/agent/start', {
      method: 'POST',
      body: JSON.stringify({ message, project }),
    })
  },

  async approveAgent(sessionId: string): Promise<any> {
    return request('/agent/approve', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async cancelAgent(sessionId: string): Promise<any> {
    return request('/agent/cancel', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async rollbackAgent(sessionId: string): Promise<any> {
    return request('/agent/rollback', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async getAgentPermissions(): Promise<any> {
    return request('/agent/permissions')
  },

  async updateAgentPermissions(updates: Record<string, any>): Promise<any> {
    return request('/agent/permissions', {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  },

  async createBrowserSession(browser: string, headless: boolean): Promise<any> {
    return request('/browser/session', {
      method: 'POST',
      body: JSON.stringify({ browser, headless }),
    })
  },

  async getBrowserSessions(): Promise<any> {
    return request('/browser/sessions')
  },

  async getBrowserSession(sessionId: string): Promise<any> {
    return request(`/browser/session/${encodeURIComponent(sessionId)}`)
  },

  async browserNavigate(sessionId: string, url: string): Promise<any> {
    return request(`/browser/session/${encodeURIComponent(sessionId)}/navigate`, {
      method: 'POST',
      body: JSON.stringify({ url, session_id: sessionId }),
    })
  },

  async browserAction(sessionId: string, action: string, params: Record<string, any> = {}): Promise<any> {
    return request(`/browser/session/${encodeURIComponent(sessionId)}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, session_id: sessionId, ...params }),
    })
  },

  async browserPause(sessionId: string): Promise<any> {
    return request(`/browser/session/${encodeURIComponent(sessionId)}/pause`, { method: 'POST' })
  },

  async browserResume(sessionId: string): Promise<any> {
    return request(`/browser/session/${encodeURIComponent(sessionId)}/resume`, { method: 'POST' })
  },

  async browserStop(sessionId: string): Promise<any> {
    return request(`/browser/session/${encodeURIComponent(sessionId)}/stop`, { method: 'POST' })
  },

  async getBrowserStatus(): Promise<any> {
    return request('/browser/status')
  },

  async getBrowserPageContext(sessionId: string): Promise<any> {
    return request(`/browser/session/${encodeURIComponent(sessionId)}/page/context`)
  },

  async browserFindElement(sessionId: string, target: string): Promise<any> {
    return request('/browser/element/find', {
      method: 'POST',
      body: JSON.stringify({ target, session_id: sessionId }),
    })
  },

  async browserTakeControl(sessionId: string): Promise<any> {
    return request('/browser/take-control', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async browserReleaseControl(sessionId: string): Promise<any> {
    return request('/browser/release-control', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async browserTakeoverStatus(sessionId: string): Promise<any> {
    return request(`/browser/takeover/status?session_id=${encodeURIComponent(sessionId)}`)
  },

  async browserCheckCaptcha(sessionId: string): Promise<any> {
    return request('/browser/check/captcha', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async browserCheckLogin(sessionId: string): Promise<any> {
    return request('/browser/check/login', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async browserCheckPurchase(sessionId: string): Promise<any> {
    return request('/browser/check/purchase', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async getComputerStatus(): Promise<any> {
    return request('/computer/status')
  },

  async getComputerWindows(): Promise<any> {
    return request('/computer/windows')
  },

  async getComputerMonitors(): Promise<any> {
    return request('/computer/monitors')
  },

  async computerScreenshot(mode?: string, region?: string, monitor?: number): Promise<any> {
    return request('/computer/screenshot', {
      method: 'POST',
      body: JSON.stringify({ mode: mode || 'full', region, monitor }),
    })
  },

  async computerAction(action: string, args: Record<string, any> = {}, sessionId = 'default'): Promise<any> {
    return request(`/computer/action`, {
      method: 'POST',
      body: JSON.stringify({ action, arguments: args, session_id: sessionId }),
    })
  },

  async computerPause(): Promise<any> {
    return request('/computer/pause', { method: 'POST' })
  },

  async computerResume(): Promise<any> {
    return request('/computer/resume', { method: 'POST' })
  },

  async computerStop(): Promise<any> {
    return request('/computer/stop', { method: 'POST' })
  },

  async getComputerProcesses(): Promise<any> {
    return request('/computer/processes')
  },

  async computerRunCommand(command: string, timeout = 30): Promise<any> {
    return request('/computer/action/command', {
      method: 'POST',
      body: JSON.stringify({ command, timeout }),
    })
  },

  async computerFilesList(path?: string): Promise<any> {
    return request('/computer/files/list', {
      method: 'POST',
      body: JSON.stringify({ path: path || '' }),
    })
  },

  async computerFilesSearch(query: string, path?: string): Promise<any> {
    return request('/computer/files/search', {
      method: 'POST',
      body: JSON.stringify({ query, path: path || '' }),
    })
  },

  async computerFilesCreate(path: string): Promise<any> {
    return request('/computer/files/create', {
      method: 'POST',
      body: JSON.stringify({ path }),
    })
  },

  async computerFilesRename(oldPath: string, newName: string): Promise<any> {
    return request('/computer/files/rename', {
      method: 'POST',
      body: JSON.stringify({ old_path: oldPath, new_name: newName }),
    })
  },

  async computerFilesMove(src: string, dst: string): Promise<any> {
    return request('/computer/files/move', {
      method: 'POST',
      body: JSON.stringify({ src, dst }),
    })
  },

  async computerFilesCopy(src: string, dst: string): Promise<any> {
    return request('/computer/files/copy', {
      method: 'POST',
      body: JSON.stringify({ src, dst }),
    })
  },

  async computerFilesDelete(path: string): Promise<any> {
    return request('/computer/files/delete', {
      method: 'POST',
      body: JSON.stringify({ path }),
    })
  },

  async computerFilesOpen(path: string): Promise<any> {
    return request('/computer/files/open', {
      method: 'POST',
      body: JSON.stringify({ path }),
    })
  },

  async computerClipboardRead(): Promise<any> {
    return request('/computer/clipboard/read', { method: 'POST' })
  },

  async computerClipboardWrite(text: string): Promise<any> {
    return request('/computer/clipboard/write', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },

  async computerTerminalOpen(command?: string): Promise<any> {
    return request('/computer/terminal/open', {
      method: 'POST',
      body: JSON.stringify({ command: command || '' }),
    })
  },

  async computerTakeControl(sessionId = 'default'): Promise<any> {
    return request('/computer/take-control', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async computerReleaseControl(sessionId = 'default'): Promise<any> {
    return request('/computer/release-control', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  async computerTakeoverStatus(sessionId = 'default'): Promise<any> {
    return request(`/computer/takeover/status?session_id=${encodeURIComponent(sessionId)}`)
  },

  async computerPermissions(): Promise<any> {
    return request('/computer/permissions')
  },

  async getWorkflows(status?: string, limit = 50): Promise<{ workflows: Workflow[] }> {
    const q = status ? `?status=${encodeURIComponent(status)}&limit=${limit}` : `?limit=${limit}`
    return request(`/workflows${q}`)
  },

  async createWorkflow(payload: { name: string; description?: string; trigger?: Record<string, any>; steps?: WorkflowStep[]; variables?: Record<string, any>; permissions?: Record<string, any>; enabled?: boolean; project?: string | null; tags?: string[] }): Promise<Workflow> {
    return request<Workflow>('/workflows', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async getWorkflow(id: string): Promise<Workflow> {
    return request<Workflow>(`/workflows/${encodeURIComponent(id)}`)
  },

  async updateWorkflow(id: string, patch: Partial<Workflow>): Promise<Workflow> {
    return request<Workflow>(`/workflows/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(patch),
    })
  },

  async deleteWorkflow(id: string): Promise<{ status: string }> {
    return request(`/workflows/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  async runWorkflow(id: string): Promise<{ status: string; workflow_id: string; run_id: string }> {
    return request(`/workflows/${encodeURIComponent(id)}/run`, { method: 'POST' })
  },

  async pauseWorkflow(id: string): Promise<Workflow> {
    return request<Workflow>(`/workflows/${encodeURIComponent(id)}/pause`, { method: 'POST' })
  },

  async resumeWorkflow(id: string): Promise<Workflow> {
    return request<Workflow>(`/workflows/${encodeURIComponent(id)}/resume`, { method: 'POST' })
  },

  async cancelWorkflow(id: string): Promise<Workflow> {
    return request<Workflow>(`/workflows/${encodeURIComponent(id)}/cancel`, { method: 'POST' })
  },

  async getWorkflowRuns(id: string, limit = 50): Promise<{ runs: WorkflowRun[] }> {
    return request(`/workflows/${encodeURIComponent(id)}/runs?limit=${limit}`)
  },

  async getApprovals(status?: string): Promise<{ approvals: WorkflowApproval[] }> {
    const q = status ? `?status=${encodeURIComponent(status)}` : ''
    return request(`/approvals${q}`)
  },

  async approveApproval(id: string): Promise<WorkflowApproval> {
    return request<WorkflowApproval>(`/approvals/${encodeURIComponent(id)}/approve`, { method: 'POST' })
  },

  async denyApproval(id: string): Promise<WorkflowApproval> {
    return request<WorkflowApproval>(`/approvals/${encodeURIComponent(id)}/deny`, { method: 'POST' })
  },

  async getPersonalization(profile = 'jarvis'): Promise<{ context: PersonalizationContext; suggestions: Suggestion[]; profile: string }> {
    return request(`/personalization?profile=${encodeURIComponent(profile)}`)
  },

  async getAdaptivePreferences(profile = 'jarvis', project?: string, sessionId?: string): Promise<AdaptivePreference[]> {
    const params = new URLSearchParams({ profile })
    if (project) params.set('project', project)
    if (sessionId) params.set('session_id', sessionId)
    return request<AdaptivePreference[]>(`/personalization/preferences?${params.toString()}`)
  },

  async setAdaptivePreference(payload: { key: string; value: string; source?: string; confidence?: string; profile?: string; project?: string; session_id?: string }): Promise<AdaptivePreference> {
    return request<AdaptivePreference>('/personalization/preferences', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async updateAdaptivePreference(id: string, payload: { key?: string; value?: string; source?: string; confidence?: string; profile?: string; project?: string; session_id?: string }): Promise<AdaptivePreference> {
    return request<AdaptivePreference>(`/personalization/preferences/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  async deleteAdaptivePreference(id: string): Promise<{ status: string }> {
    return request(`/personalization/preferences/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  async forgetPreference(payload: { preference_id?: string; key?: string; profile?: string }): Promise<{ status: string; count?: number }> {
    return request('/personalization/forget', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async getPersonalizationSuggestions(profile = 'jarvis'): Promise<{ suggestions: Suggestion[] }> {
    return request(`/personalization/suggestions?profile=${encodeURIComponent(profile)}`)
  },

  async getEnvironmentProfile(): Promise<EnvironmentProfile> {
    return request<EnvironmentProfile>('/personalization/environment')
  },

  async getPersonalizationAnalytics(profile = 'jarvis'): Promise<PersonalizationAnalytics> {
    return request<PersonalizationAnalytics>(`/personalization/analytics?profile=${encodeURIComponent(profile)}`)
  },

  async recordFeedback(payload: { user_message: string; assistant_response: string; feedback: string; profile?: string }): Promise<{ status: string; learned?: any }> {
    return request('/personalization/feedback', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async exportPersonalization(profile = 'jarvis'): Promise<any> {
    return request(`/personalization/export?profile=${encodeURIComponent(profile)}`, { method: 'POST' })
  },

  async importPersonalization(payload: { data: any; profile?: string }): Promise<{ status: string; count: number }> {
    return request('/personalization/import', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async getPersonalizationWorkflows(): Promise<{ workflows: any[] }> {
    return request('/personalization/workflows')
  },

  async recordWorkflowAction(payload: { action: string; tool: string; arguments: Record<string, any> }): Promise<{ status: string }> {
    return request('/personalization/workflow/record', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async recordTaskOutcome(payload: Record<string, any>): Promise<{ status: string }> {
    return request('/personalization/task-outcome', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
