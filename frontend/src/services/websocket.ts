type EventHandler = (event: string, data: any) => void

const HEARTBEAT_INTERVAL_MS = 30000
const HEARTBEAT_TIMEOUT_MS = 10000

export class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, Set<EventHandler>> = new Map()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private lastPong: number = 0
  private lastPingAt: number = 0
  private manualClose = false
  private reconnectDelay = 1000
  private maxReconnectDelay = 30000

  constructor(url: string) {
    this.url = url
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return
    this.manualClose = false

    try {
      this.ws = new WebSocket(this.url)
    } catch {
      this.scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this.reconnectDelay = 1000
      this.lastPong = Date.now()
      this.lastPingAt = 0
      this.startHeartbeat()
      this.emit('connected', null)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.event === 'pong') {
          this.lastPong = Date.now()
          return
        }
        this.emit(data.event, data.data)
      } catch {
        // ignore malformed
      }
    }

    this.ws.onclose = () => {
      this.stopHeartbeat()
      if (!this.manualClose) {
        this.scheduleReconnect()
      }
      this.emit('disconnected', null)
    }

    this.ws.onerror = () => {
      this.emit('error', null)
    }
  }

  send(event: string, data?: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ event, data }))
    }
  }

  on(event: string, handler: EventHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler)
    return () => this.off(event, handler)
  }

  off(event: string, handler: EventHandler) {
    this.handlers.get(event)?.delete(handler)
  }

  private emit(event: string, data: any) {
    this.handlers.get(event)?.forEach((fn) => fn(event, data))
    this.handlers.get('*')?.forEach((fn) => fn(event, data))
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) return
      const now = Date.now()
      // Only enforce the timeout for a ping that was actually sent and never
      // answered. lastPong is updated when the server responds.
      if (
        this.lastPingAt > 0 &&
        this.lastPong < this.lastPingAt &&
        now - this.lastPingAt > HEARTBEAT_TIMEOUT_MS
      ) {
        // Server unresponsive — force reconnect.
        this.emit('status', { state: 'reconnecting', reason: 'heartbeat_timeout' })
        this.ws.close()
        return
      }
      this.lastPingAt = now
      this.send('ping', {})
    }, HEARTBEAT_INTERVAL_MS)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return
    const delay = this.reconnectDelay + Math.random() * 500
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.emit('status', { state: 'reconnecting', reason: 'scheduled' })
      this.connect()
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.7, this.maxReconnectDelay)
    }, delay)
  }

  disconnect() {
    this.manualClose = true
    this.stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  get readyState() {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }
}
