import type { JarvisSettings, HealthStatus, MemoryItem, Automation, ToolInfo, Message, SystemStats, ConversationSummary, NotificationItem, DiagnosticInfo, VoiceInfo, CodingProject, ProjectFileEntry, PersonaInfo, Skill, SkillActivity, GitStatus } from '../types'

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
}
