import { useCallback, useEffect, useState } from 'react'
import type { JarvisSettings } from '../types'
import { api } from '../services/api'

export function useSettings() {
  const [settings, setSettings] = useState<JarvisSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSettings = useCallback(async () => {
    try {
      const data = await api.getSettings()
      setSettings(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch settings')
    } finally {
      setLoading(false)
    }
  }, [])

  const updateSettings = useCallback(
    async (patch: Partial<JarvisSettings>) => {
      setSaving(true)
      try {
        const data = await api.updateSettings(patch)
        setSettings(data)
        setError(null)
        return data
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to update settings')
        throw err
      } finally {
        setSaving(false)
      }
    },
    []
  )

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  return { settings, loading, saving, error, updateSettings, refetch: fetchSettings }
}
