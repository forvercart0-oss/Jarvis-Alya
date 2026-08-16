import { useState } from 'react'
import type { MemoryItem, ConversationSummaryItem, ReminderItem, PrivacySettings } from '../../types'
import { Plus, Search, Trash2, Clock, Shield, Bell, FileText, FolderOpen, ListTodo, Sparkles, RefreshCw } from 'lucide-react'
import { MemoryItemComponent } from './MemoryItem'
import { MemorySearch } from './MemorySearch'
import { MemoryTimeline } from './MemoryTimeline'
import { RemindersPanel } from './RemindersPanel'
import { ConversationSummariesPanel } from './ConversationSummariesPanel'
import { MemoryPrivacy } from './MemoryPrivacy'
import { MemoryManagement } from './MemoryManagement'

interface MemoryPanelProps {
  memories: MemoryItem[]
  onAdd: (content: string, category?: string, project?: string, profile?: string) => void
  onDelete: (id: string) => void
  onUpdate: (id: string, content: string, confidence?: number, source?: string) => void
  onRefresh: () => void
  reminders: ReminderItem[]
  onAddReminder: (title: string, description: string, dueAt: string, repeat: string) => void
  onUpdateReminder: (id: string, updates: Record<string, any>) => void
  onDeleteReminder: (id: string) => void
  summaries: ConversationSummaryItem[]
  privacy: PrivacySettings | null
  onSetPrivacyMode: (mode: string) => void
  projects: string[]
  profile: string
  onSearchMemory: (query: string, category?: string, project?: string) => Promise<MemoryItem[]>
}

type Tab = 'recent' | 'preferences' | 'projects' | 'tasks' | 'summaries' | 'reminders' | 'search' | 'privacy' | 'manage'

export function MemoryPanel({
  memories,
  onAdd,
  onDelete,
  onUpdate,
  onRefresh,
  reminders,
  onAddReminder,
  onUpdateReminder,
  onDeleteReminder,
  summaries,
  privacy,
  onSetPrivacyMode,
  projects,
  profile,
  onSearchMemory,
}: MemoryPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>('recent')
  const [showAddForm, setShowAddForm] = useState(false)
  const [newContent, setNewContent] = useState('')
  const [newCategory, setNewCategory] = useState('')
  const [newProject, setNewProject] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<MemoryItem[]>([])

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'recent', label: 'Recent', icon: <Clock className="w-3 h-3" /> },
    { id: 'preferences', label: 'Prefs', icon: <Sparkles className="w-3 h-3" /> },
    { id: 'projects', label: 'Projects', icon: <FolderOpen className="w-3 h-3" /> },
    { id: 'tasks', label: 'Tasks', icon: <ListTodo className="w-3 h-3" /> },
    { id: 'summaries', label: 'Summaries', icon: <FileText className="w-3 h-3" /> },
    { id: 'reminders', label: 'Reminders', icon: <Bell className="w-3 h-3" /> },
    { id: 'search', label: 'Search', icon: <Search className="w-3 h-3" /> },
    { id: 'privacy', label: 'Privacy', icon: <Shield className="w-3 h-3" /> },
    { id: 'manage', label: 'Manage', icon: <Trash2 className="w-3 h-3" /> },
  ]

  const handleAdd = () => {
    if (!newContent.trim()) return
    onAdd(newContent.trim(), newCategory.trim() || undefined, newProject.trim() || undefined, profile)
    setNewContent('')
    setNewCategory('')
    setNewProject('')
    setShowAddForm(false)
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    const results = await onSearchMemory(searchQuery.trim())
    setSearchResults(results)
  }

  const filteredMemories = (() => {
    switch (activeTab) {
      case 'preferences':
        return memories.filter((m) => m.category === 'preferences')
      case 'projects':
        return memories.filter((m) => m.category === 'projects')
      case 'tasks':
        return memories.filter((m) => m.category === 'tasks')
      default:
        return memories
    }
  })()

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">Memory</h3>
        <div className="flex gap-2">
          <button
            onClick={onRefresh}
            className="text-[10px] tracking-widest text-slate-500 hover:text-cyan-300 transition-colors uppercase"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="text-[10px] tracking-widest text-cyan-400 hover:text-cyan-300 transition-colors uppercase flex items-center gap-1"
          >
            <Plus className="w-3 h-3" /> Add
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`text-[9px] tracking-wider px-2 py-1 rounded transition-colors ${
              activeTab === tab.id ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {showAddForm && (
        <div className="glass-panel p-3 space-y-2">
          <input
            type="text"
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            placeholder='Memory content...'
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
          />
          <input
            type="text"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
            placeholder='Category (optional)'
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
          />
          {projects.length > 0 && (
            <input
              type="text"
              value={newProject}
              onChange={(e) => setNewProject(e.target.value)}
              placeholder='Project (optional)'
              list="memory-projects"
              className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
            />
          )}
          <datalist id="memory-projects">
            {projects.map((p) => (
              <option key={p} value={p} />
            ))}
          </datalist>
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              disabled={!newContent.trim()}
              className="px-3 py-1 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all disabled:opacity-50"
            >
              Save
            </button>
            <button
              onClick={() => setShowAddForm(false)}
              className="px-3 py-1 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {activeTab === 'search' && (
        <MemorySearch
          query={searchQuery}
          onQueryChange={setSearchQuery}
          results={searchResults}
          onSearch={handleSearch}
        />
      )}

      {activeTab === 'summaries' && (
        <ConversationSummariesPanel summaries={summaries} />
      )}

      {activeTab === 'reminders' && (
        <RemindersPanel
          reminders={reminders}
          onAdd={onAddReminder}
          onUpdate={onUpdateReminder}
          onDelete={onDeleteReminder}
        />
      )}

      {activeTab === 'privacy' && (
        <MemoryPrivacy
          privacy={privacy}
          onSetMode={onSetPrivacyMode}
        />
      )}

      {activeTab === 'manage' && (
        <MemoryManagement memories={memories} onRefresh={onRefresh} />
      )}

      {activeTab !== 'search' && activeTab !== 'summaries' && activeTab !== 'reminders' && activeTab !== 'privacy' && activeTab !== 'manage' && (
        <>
          {filteredMemories.length === 0 ? (
            <div className="text-center text-slate-500 py-10">No memories in this section.</div>
          ) : (
            <div className="space-y-2">
              {filteredMemories.map((m) => (
                <MemoryItemComponent key={m.id} memory={m} onDelete={onDelete} onUpdate={onUpdate} />
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === 'recent' && (
        <MemoryTimeline memories={memories} />
      )}
    </div>
  )
}
