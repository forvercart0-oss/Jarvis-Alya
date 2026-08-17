import { useState, useEffect, useCallback } from 'react'
import type { UpdaterConfig, UpdaterProgress, UpdateInfo } from '../../types'
import { api } from '../../services/api'
import { RefreshCw, Download, CheckCircle2, XCircle, AlertTriangle, ExternalLink } from 'lucide-react'

type UpdaterTab = 'status' | 'settings' | 'history'

const CHECK_FREQUENCIES = [
  { value: 1, label: 'Every 1 hour' },
  { value: 6, label: 'Every 6 hours' },
  { value: 12, label: 'Every 12 hours' },
  { value: 24, label: 'Every 24 hours' },
]

export function UpdateSettings() {
  const [tab, setTab] = useState<UpdaterTab>('status')
  const [config, setConfig] = useState<UpdaterConfig | null>(null)
  const [progress, setProgress] = useState<UpdaterProgress | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadStatus = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getUpdaterStatus()
      setConfig(data.config)
      setProgress(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load updater status')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStatus()
    const interval = setInterval(loadStatus, 30000)
    return () => clearInterval(interval)
  }, [loadStatus])

  const handleCheck = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.checkForUpdate(true)
      setProgress(result)
      if (result.available_update) {
        setConfig((c) => c ? { ...c, last_check: new Date().toISOString() } : c)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Check failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.downloadUpdate()
      setProgress(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Download failed')
    } finally {
      setLoading(false)
    }
  }

  const handleInstall = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.installUpdate()
      setProgress(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Installation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleConfigUpdate = async (patch: Partial<UpdaterConfig>) => {
    try {
      const updated = await api.updateUpdaterConfig(patch)
      setConfig(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update settings')
    }
  }

  const formatDate = (iso: string) => {
    if (!iso) return 'Never'
    const d = new Date(iso)
    return d.toLocaleString()
  }

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'up_to_date': return <CheckCircle2 className="w-5 h-5 text-green-400" />
      case 'update_available': return <AlertTriangle className="w-5 h-5 text-yellow-400" />
      case 'downloading': return <Download className="w-5 h-5 text-blue-400 animate-pulse" />
      case 'failed': return <XCircle className="w-5 h-5 text-red-400" />
      default: return <RefreshCw className="w-5 h-5 text-slate-400" />
    }
  }

  const renderStatus = () => {
    if (!progress || !config) return <div className="text-slate-500">Loading...</div>

    const updateInfo = progress.available_update as UpdateInfo | null

    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3 p-4 rounded-lg border border-cyan-500/10 bg-cyan-500/5">
          {getStateIcon(progress.state)}
          <div className="flex-1">
            <div className="text-sm text-slate-300">
              {progress.state === 'up_to_date' && "You're up to date"}
              {progress.state === 'update_available' && 'Update Available'}
              {progress.state === 'downloading' && `Downloading... ${progress.progress_percent}%`}
              {progress.state === 'downloaded' && 'Download Complete'}
              {progress.state === 'verifying' && 'Verifying Update...'}
              {progress.state === 'ready_to_install' && 'Ready to Install'}
              {progress.state === 'installing' && 'Installing...'}
              {progress.state === 'restarting' && 'Restarting...'}
              {progress.state === 'updated' && 'Updated Successfully'}
              {progress.state === 'failed' && `Failed: ${progress.error || 'Unknown error'}`}
              {progress.state === 'offline' && 'GitHub Unavailable'}
              {progress.state === 'disabled' && 'Updates Disabled'}
              {progress.state === 'development' && 'Development Installation'}
            </div>
            {progress.message && <div className="text-xs text-slate-500 mt-1">{progress.message}</div>}
          </div>
        </div>

        {progress.state === 'downloading' && progress.total > 0 && (
          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-cyan-500 transition-all duration-300"
              style={{ width: `${progress.progress_percent}%` }}
            />
          </div>
        )}

        {updateInfo && (
          <div className="p-4 rounded-lg border border-slate-700 bg-slate-800/50 space-y-2">
            <div className="text-xs text-slate-400 uppercase tracking-wider">Update Details</div>
            <div className="text-sm text-slate-300">
              <span className="text-slate-500">Commit:</span> {updateInfo.commit_sha.slice(0, 7)}
            </div>
            <div className="text-sm text-slate-300">
              <span className="text-slate-500">Author:</span> {updateInfo.commit_author}
            </div>
            <div className="text-sm text-slate-300">
              <span className="text-slate-500">Date:</span> {formatDate(updateInfo.committed_at)}
            </div>
            <div className="text-sm text-slate-300">
              <span className="text-slate-500">Message:</span> {updateInfo.commit_message}
            </div>
            <a
              href={updateInfo.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 mt-2"
            >
              View Changes <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="p-3 rounded border border-slate-700 bg-slate-800/30">
            <div className="text-slate-500 uppercase tracking-wider mb-1">Current Version</div>
            <div className="text-slate-300 font-mono">{config.current_commit.slice(0, 7) || 'unknown'}</div>
          </div>
          <div className="p-3 rounded border border-slate-700 bg-slate-800/30">
            <div className="text-slate-500 uppercase tracking-wider mb-1">Last Checked</div>
            <div className="text-slate-300">{formatDate(config.last_check)}</div>
          </div>
          <div className="p-3 rounded border border-slate-700 bg-slate-800/30">
            <div className="text-slate-500 uppercase tracking-wider mb-1">Last Updated</div>
            <div className="text-slate-300">{formatDate(config.last_update)}</div>
          </div>
          <div className="p-3 rounded border border-slate-700 bg-slate-800/30">
            <div className="text-slate-500 uppercase tracking-wider mb-1">Installation Type</div>
            <div className="text-slate-300 capitalize">{config.installation_type}</div>
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <button
            onClick={handleCheck}
            disabled={loading || !config.enabled}
            className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded text-cyan-400 text-xs hover:bg-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            Check Now
          </button>
          {progress.state === 'update_available' || progress.state === 'downloaded' || progress.state === 'ready_to_install' ? (
            <>
              <button
                onClick={handleDownload}
                disabled={loading}
                className="px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded text-blue-400 text-xs hover:bg-blue-500/20 disabled:opacity-50 flex items-center gap-2"
              >
                <Download className="w-3 h-3" />
                Download
              </button>
              <button
                onClick={handleInstall}
                disabled={loading}
                className="px-4 py-2 bg-green-500/10 border border-green-500/30 rounded text-green-400 text-xs hover:bg-green-500/20 disabled:opacity-50 flex items-center gap-2"
              >
                Update Now
              </button>
            </>
          ) : null}
        </div>
      </div>
    )
  }

  const renderSettings = () => {
    if (!config) return <div className="text-slate-500">Loading...</div>

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between p-3 rounded border border-slate-700 bg-slate-800/30">
          <div>
            <div className="text-sm text-slate-300">Automatic Updates</div>
            <div className="text-xs text-slate-500">Enable automatic update checking</div>
          </div>
          <button
            onClick={() => handleConfigUpdate({ enabled: !config.enabled })}
            className={`px-3 py-1 rounded text-xs border ${
              config.enabled
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                : 'bg-slate-700 border-slate-600 text-slate-400'
            }`}
          >
            {config.enabled ? 'ON' : 'OFF'}
          </button>
        </div>

        <div className="p-3 rounded border border-slate-700 bg-slate-800/30">
          <div className="text-sm text-slate-300 mb-2">Check Frequency</div>
          <div className="flex flex-wrap gap-2">
            {CHECK_FREQUENCIES.map((freq) => (
              <button
                key={freq.value}
                onClick={() => handleConfigUpdate({ check_interval_hours: freq.value })}
                className={`px-3 py-1 rounded text-xs border ${
                  config.check_interval_hours === freq.value
                    ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                    : 'bg-slate-700 border-slate-600 text-slate-400 hover:bg-slate-600'
                }`}
              >
                {freq.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between p-3 rounded border border-slate-700 bg-slate-800/30">
          <div>
            <div className="text-sm text-slate-300">Download Updates Automatically</div>
            <div className="text-xs text-slate-500">Download updates in the background</div>
          </div>
          <button
            onClick={() => handleConfigUpdate({ auto_download: !config.auto_download })}
            className={`px-3 py-1 rounded text-xs border ${
              config.auto_download
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                : 'bg-slate-700 border-slate-600 text-slate-400'
            }`}
          >
            {config.auto_download ? 'ON' : 'OFF'}
          </button>
        </div>

        <div className="flex items-center justify-between p-3 rounded border border-slate-700 bg-slate-800/30">
          <div>
            <div className="text-sm text-slate-300">Install Updates Automatically</div>
            <div className="text-xs text-slate-500">Install after download (requires restart)</div>
          </div>
          <button
            onClick={() => handleConfigUpdate({ auto_install: !config.auto_install })}
            className={`px-3 py-1 rounded text-xs border ${
              config.auto_install
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                : 'bg-slate-700 border-slate-600 text-slate-400'
            }`}
          >
            {config.auto_install ? 'ON' : 'OFF'}
          </button>
        </div>

        <div className="flex items-center justify-between p-3 rounded border border-slate-700 bg-slate-800/30">
          <div>
            <div className="text-sm text-slate-300">Update on Metered Connection</div>
            <div className="text-xs text-slate-500">Allow updates on metered networks</div>
          </div>
          <button
            onClick={() => handleConfigUpdate({ install_on_metered: !config.install_on_metered })}
            className={`px-3 py-1 rounded text-xs border ${
              config.install_on_metered
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                : 'bg-slate-700 border-slate-600 text-slate-400'
            }`}
          >
            {config.install_on_metered ? 'ON' : 'OFF'}
          </button>
        </div>

        <div className="flex items-center justify-between p-3 rounded border border-slate-700 bg-slate-800/30">
          <div>
            <div className="text-sm text-slate-300">Require Confirmation Before Installing</div>
            <div className="text-xs text-slate-500">Show confirmation dialog before installing</div>
          </div>
          <button
            onClick={() => handleConfigUpdate({ require_confirmation: !config.require_confirmation })}
            className={`px-3 py-1 rounded text-xs border ${
              config.require_confirmation
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                : 'bg-slate-700 border-slate-600 text-slate-400'
            }`}
          >
            {config.require_confirmation ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Updates</h3>

      {error && (
        <div className="p-3 rounded border border-red-500/30 bg-red-500/10 text-red-400 text-xs">
          {error}
        </div>
      )}

      <div className="flex border-b border-slate-700">
        {[
          { id: 'status', label: 'Status' },
          { id: 'settings', label: 'Settings' },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as UpdaterTab)}
            className={`px-4 py-2 text-xs transition-colors ${
              tab === t.id
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="min-h-[200px]">
        {tab === 'status' && renderStatus()}
        {tab === 'settings' && renderSettings()}
      </div>
    </div>
  )
}