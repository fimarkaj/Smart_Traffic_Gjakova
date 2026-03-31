import { useEffect, useRef } from 'react'
import { useAuthStore, useLiveStore } from '../store'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useWebSocket() {
  const token        = useAuthStore((s) => s.token)
  const setConnected = useLiveStore((s) => s.setConnected)
  const handleFrame  = useLiveStore((s) => s.handleFrame)
  const wsRef        = useRef(null)
  const retryRef     = useRef(null)

  useEffect(() => {
    if (!token) return

    const connect = () => {
      const ws = new WebSocket(`${WS_URL}/api/live/ws?token=${token}`)
      wsRef.current = ws

      ws.onopen  = () => { setConnected(true); clearTimeout(retryRef.current) }
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          if (data.type === 'frame') handleFrame(data)
        } catch (_) {}
      }
      ws.onclose = () => { setConnected(false); retryRef.current = setTimeout(connect, 2000) }
      ws.onerror = () => ws.close()
    }

    connect()
    return () => { clearTimeout(retryRef.current); wsRef.current?.close() }
  }, [token])
}
