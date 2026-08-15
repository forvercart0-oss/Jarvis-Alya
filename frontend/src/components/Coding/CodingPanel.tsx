import { useEffect, useState } from 'react'
import { FolderPlus, FolderOpen, FileCode2, Terminal, Save, Trash2, RefreshCw, Play } from 'lucide-react'
import type { CodingProject, ProjectFileEntry } from '../../types'
import { api } from '../../services/api'
import { Button } from '../Common/Button'
import { Input } from '../Common/Input'

interface CodingPanelProps {
  projects: CodingProject[]
  onRefresh: () => void
}

export function CodingPanel({ projects, onRefresh }: CodingPanelProps) {
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const [stack, setStack] = useState('')
  const [description, setDescription] = useState('')
  const [busy, setBusy] = useState(false)
  const [selected, setSelected] = useState<CodingProject | null>(null)
  const [files, setFiles] = useState<ProjectFileEntry[]>([])
  const [openFile, setOpenFile] = useState<string | null>(null)
  const [content, setContent] = useState('')
  const [dirty, setDirty] = useState(false)
  const [output, setOutput] = useState<{ cmd: string; stdout: string; stderr: string; code: number | null } | null>(null)
  const [command, setCommand] = useState('')
  const [error, setError] = useState<string | null>(null)

  const notify = (message: string, type: string = 'info') => {
    window.dispatchEvent(new CustomEvent('jarvis-notification', { detail: { message, type } }))
  }

  const loadFiles = async (p: CodingProject) => {
    setBusy(true)
    try {
      const res = await api.listProjectFiles(p.name)
      setFiles(res.files || [])
      setSelected(p)
      setOpenFile(null)
      setContent('')
      setDirty(false)
    } catch {
      notify('Failed to load project files', 'error')
    } finally {
      setBusy(false)
    }
  }

  const handleCreate = async () => {
    if (!name.trim()) return
    setBusy(true)
    setError(null)
    try {
      await api.createProject({ name: name.trim(), stack: stack.trim(), description: description.trim() })
      setCreating(false)
      setName('')
      setStack('')
      setDescription('')
      notify(`Project '${name}' created`)
      onRefresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project')
    } finally {
      setBusy(false)
    }
  }

  const handleDelete = async (p: CodingProject) => {
    if (!window.confirm(`Delete project '${p.name}' and all its files?`)) return
    setBusy(true)
    try {
      await api.deleteProject(p.name)
      if (selected?.name === p.name) {
        setSelected(null)
        setFiles([])
        setOpenFile(null)
        setContent('')
      }
      notify(`Project '${p.name}' deleted`)
      onRefresh()
    } catch {
      notify('Failed to delete project', 'error')
    } finally {
      setBusy(false)
    }
  }

  const openProjectFile = async (path: string) => {
    if (!selected) return
    setBusy(true)
    try {
      const res = await api.readProjectFile(selected.name, path)
      setOpenFile(path)
      setContent(res.content ?? '')
      setDirty(false)
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Failed to read file', 'error')
    } finally {
      setBusy(false)
    }
  }

  const handleSave = async () => {
    if (!selected || !openFile) return
    setBusy(true)
    try {
      await api.writeProjectFile(selected.name, openFile, content)
      setDirty(false)
      notify(`Saved ${openFile}`)
      onRefresh()
      loadFiles(selected)
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Failed to save file', 'error')
    } finally {
      setBusy(false)
    }
  }

  const runCommand = async () => {
    if (!selected || !command.trim()) return
    setBusy(true)
    try {
      const res = await api.runProjectCommand(selected.name, command.trim())
      setOutput({ cmd: command.trim(), stdout: res?.stdout ?? '', stderr: res?.stderr ?? '', code: res?.exit_code ?? null })
    } catch (err) {
      setOutput({ cmd: command.trim(), stdout: '', stderr: err instanceof Error ? err.message : 'Command failed', code: 1 })
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    if (selected) {
      loadFiles(selected)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="h-full flex overflow-hidden">
      {/* Project list */}
      <div className="w-64 border-r border-cyan-500/10 flex flex-col min-h-0">
        <div className="flex items-center justify-between px-3 py-2.5 border-b border-cyan-500/10">
          <span className="text-[10px] tracking-[0.3em] text-cyan-400/70 uppercase">Projects</span>
          <div className="flex gap-1">
            <button onClick={onRefresh} className="text-slate-500 hover:text-cyan-300 transition-colors" title="Refresh">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setCreating((c) => !c)} className="text-cyan-400 hover:text-cyan-200 transition-colors" title="New project">
              <FolderPlus className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {projects.length === 0 && !creating && (
            <p className="text-xs text-slate-600 p-3 text-center">No projects yet.<br />Create one to get started.</p>
          )}
          {projects.map((p) => (
            <div
              key={p.name}
              onClick={() => loadFiles(p)}
              className={`group flex items-center justify-between px-2.5 py-2 rounded cursor-pointer transition-colors ${
                selected?.name === p.name ? 'bg-cyan-500/10 border border-cyan-400/20' : 'hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              <div className="min-w-0">
                <div className="text-xs text-slate-300 truncate flex items-center gap-1.5">
                  <FolderOpen className="w-3.5 h-3.5 text-cyan-400/70 shrink-0" />
                  {p.name}
                </div>
                {p.stack && <div className="text-[10px] text-slate-600 truncate pl-5">{p.stack}</div>}
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); handleDelete(p) }}
                className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition-all"
                title="Delete project"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>

        {creating && (
          <div className="border-t border-cyan-500/10 p-3 space-y-2 bg-black/30">
            <p className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">New Project</p>
            <Input placeholder="Project name" value={name} onChange={setName} />
            <Input placeholder="Stack (e.g. python fastapi)" value={stack} onChange={setStack} />
            <Input placeholder="Description (optional)" value={description} onChange={setDescription} />
            {error && <p className="text-[10px] text-red-400">{error}</p>}
            <Button size="sm" className="w-full" onClick={handleCreate} disabled={busy || !name.trim()}>
              Create Project
            </Button>
          </div>
        )}
      </div>

      {/* File browser / editor */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        {!selected ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-600 gap-3">
            <FolderOpen className="w-12 h-12 opacity-30" />
            <p className="text-xs">Select a project to open its workspace</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-cyan-500/10">
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <FolderOpen className="w-4 h-4 text-cyan-400" />
                {selected.name}
                <span className="text-[10px] text-slate-600">{files.length} files</span>
              </div>
              <div className="flex items-center gap-2">
                {openFile && (
                  <Button size="sm" onClick={handleSave} disabled={!dirty || busy}>
                    <Save className="w-3.5 h-3.5" /> {dirty ? 'Save' : 'Saved'}
                  </Button>
                )}
              </div>
            </div>

            <div className="flex-1 flex overflow-hidden min-h-0">
              {/* File tree */}
              <div className="w-52 border-r border-cyan-500/10 overflow-y-auto p-2">
                {files.map((f) => (
                  <button
                    key={f.path}
                    onClick={() => openProjectFile(f.path)}
                    className={`w-full text-left px-2 py-1.5 rounded flex items-center gap-1.5 text-xs transition-colors ${
                      openFile === f.path ? 'bg-cyan-500/10 text-cyan-300' : 'text-slate-400 hover:bg-slate-800/50'
                    }`}
                  >
                    <FileCode2 className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                    <span className="truncate">{f.path}</span>
                  </button>
                ))}
              </div>

              {/* Editor */}
              <div className="flex-1 flex flex-col min-w-0 min-h-0">
                {openFile ? (
                  <textarea
                    value={content}
                    onChange={(e) => { setContent(e.target.value); setDirty(true) }}
                    spellCheck={false}
                    className="flex-1 bg-transparent text-xs font-mono text-slate-300 p-4 outline-none resize-none leading-relaxed"
                  />
                ) : (
                  <div className="flex-1 flex items-center justify-center text-slate-600 text-xs">
                    Select a file to edit
                  </div>
                )}
              </div>
            </div>

            {/* Terminal */}
            <div className="border-t border-cyan-500/10 bg-black/40 min-h-0">
              <div className="flex items-center gap-2 px-3 py-2 border-b border-cyan-500/10">
                <Terminal className="w-3.5 h-3.5 text-cyan-400/70" />
                <span className="text-[10px] tracking-[0.2em] text-slate-400 uppercase">Terminal</span>
                <div className="flex-1 flex gap-2">
                  <input
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && runCommand()}
                    placeholder="run a command in the project directory (npm run build, pytest, ...)"
                    className="flex-1 bg-transparent text-xs text-slate-300 px-2 py-1 outline-none border border-slate-700/50 rounded"
                  />
                  <Button size="sm" onClick={runCommand} disabled={busy || !command.trim()}>
                    <Play className="w-3.5 h-3.5" /> Run
                  </Button>
                </div>
              </div>
              {output && (
                <div className="p-3 text-[11px] font-mono max-h-44 overflow-y-auto">
                  <div className="text-cyan-500/70 mb-1">&gt; {output.cmd}</div>
                  {output.stdout && <pre className="text-slate-300 whitespace-pre-wrap">{output.stdout}</pre>}
                  {output.stderr && <pre className="text-red-400 whitespace-pre-wrap">{output.stderr}</pre>}
                  {output.code != null && (
                    <div className={`mt-1 ${output.code === 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      process exited with code {output.code}
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
