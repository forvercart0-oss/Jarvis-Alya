import type { JarvisSettings, HealthStatus, MemoryItem, Automation, ToolInfo, Message, SystemStats, ConversationSummary, NotificationItem, DiagnosticInfo, VoiceInfo, CodingProject, ProjectFileEntry, PersonaInfo, Skill, SkillActivity } from '../types'

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

  async addMemory(content: string, category?: string): Promise<MemoryItem> {
    return request<MemoryItem>('/memory', {
      method: 'POST',
      body: JSON.stringify({ content, category }),
    })
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
}
