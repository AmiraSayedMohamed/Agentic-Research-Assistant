"use client"

import { useEffect, useRef, useState } from "react"

interface WebSocketMessage {
  type: string
  data: any
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<string | null>(null)

  const ws = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const maxAttempts = options.maxReconnectAttempts || 5
  const reconnectInterval = options.reconnectInterval || 3000

  const connect = () => {
    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        setIsConnected(true)
        setError(null)
        reconnectAttempts.current = 0
        options.onOpen?.()
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          options.onMessage?.(message)
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err)
        }
      }

      ws.current.onclose = () => {
        setIsConnected(false)
        options.onClose?.()

        // Attempt to reconnect
        if (reconnectAttempts.current < maxAttempts) {
          setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, reconnectInterval)
        }
      }

      ws.current.onerror = (error) => {
        setError("WebSocket connection error")
        options.onError?.(error)
      }
    } catch (err) {
      setError("Failed to create WebSocket connection")
    }
  }

  const sendMessage = (message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }

  const disconnect = () => {
    ws.current?.close()
  }

  useEffect(() => {
    connect()

    return () => {
      ws.current?.close()
    }
  }, [url])

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    disconnect,
  }
}
