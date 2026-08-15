import { useCallback, useEffect, useRef, useState } from 'react'
import type { SystemStats } from '../types'
import { api } from '../services/api'

export function useSystemStats(pollInterval = 5000) {
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval>>()

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.getSystemStats()
      setStats(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats')
    }
  }, [])

  useEffect(() => {
    fetchStats()
    timerRef.current = setInterval(fetchStats, pollInterval)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [fetchStats, pollInterval])

  return { stats, error, refetch: fetchStats }
}
