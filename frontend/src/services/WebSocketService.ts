/**
 * Service WebSocket pour les notifications en temps réel
 */

import { useNotification } from './NotificationService'

export interface WebSocketMessage {
  type: 'notification' | 'update' | 'alert' | 'sync'
  category: string
  title?: string
  message: string
  data?: Record<string, any>
  timestamp: number
}

interface WebSocketConfig {
  url: string
  reconnectAttempts?: number
  reconnectDelay?: number
  autoConnect?: boolean
}

/**
 * Classe pour gérer la connexion WebSocket
 */
export class WebSocketService {
  private ws: WebSocket | null = null
  private config: WebSocketConfig
  private reconnectAttempts = 0
  private maxReconnectAttempts: number
  private reconnectDelay: number
  private messageHandlers: Map<string, Set<(data: any) => void>> = new Map()
  private isConnecting = false
  private messageQueue: WebSocketMessage[] = []
  private connectionPromise: Promise<void> | null = null

  constructor(config: WebSocketConfig) {
    this.config = config
    this.maxReconnectAttempts = config.reconnectAttempts ?? 5
    this.reconnectDelay = config.reconnectDelay ?? 3000

    if (config.autoConnect !== false) {
      this.connect()
    }
  }

  /**
   * Établir la connexion WebSocket
   */
  public connect(): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise
    }

    this.connectionPromise = new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      if (this.isConnecting) {
        reject(new Error('Connexion en cours'))
        return
      }

      this.isConnecting = true

      try {
        this.ws = new WebSocket(this.config.url)

        this.ws.onopen = () => {
          console.log('[WebSocket] Connecté au serveur')
          this.reconnectAttempts = 0
          this.isConnecting = false

          // Envoyer les messages en attente
          this.flushMessageQueue()

          resolve()
          this.connectionPromise = null
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('[WebSocket] Erreur parsing message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Erreur:', error)
          this.isConnecting = false
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('[WebSocket] Déconnecté')
          this.isConnecting = false
          this.connectionPromise = null
          this.attemptReconnect()
        }
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })

    return this.connectionPromise
  }

  /**
   * Gérer les messages reçus
   */
  private handleMessage(message: WebSocketMessage) {
    const handlers = this.messageHandlers.get(message.type)
    if (handlers) {
      handlers.forEach((handler) => handler(message))
    }

    // Gestionnaires spécifiques par catégorie
    const categoryHandlers = this.messageHandlers.get(`${message.type}:${message.category}`)
    if (categoryHandlers) {
      categoryHandlers.forEach((handler) => handler(message))
    }
  }

  /**
   * S'abonner aux messages d'un type
   */
  public subscribe(type: string, handler: (data: any) => void): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set())
    }

    this.messageHandlers.get(type)!.add(handler)

    // Retourner une fonction de désinscription
    return () => {
      const handlers = this.messageHandlers.get(type)
      if (handlers) {
        handlers.delete(handler)
      }
    }
  }

  /**
   * Envoyer un message
   */
  public send(message: WebSocketMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      // Mettre en queue si pas connecté
      this.messageQueue.push(message)
    }
  }

  /**
   * Envoyer les messages en attente
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()
      if (message) {
        this.ws.send(JSON.stringify(message))
      }
    }
  }

  /**
   * Tenter de se reconnecter
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(
        `[WebSocket] Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts} dans ${this.reconnectDelay}ms`
      )

      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('[WebSocket] Erreur reconnexion:', error)
        })
      }, this.reconnectDelay)
    } else {
      console.error('[WebSocket] Nombre maximum de tentatives de reconnexion atteint')
    }
  }

  /**
   * Fermer la connexion
   */
  public disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * Vérifier si connecté
   */
  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * Obtenir l'état de la connexion
   */
  public getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }
}

/**
 * Hook React pour WebSocket
 */
export const useWebSocket = (url: string, shouldConnect: boolean = true) => {
  const [service] = React.useState(() => {
    const baseUrl = url || (`ws://${window.location.host}/ws`)
    return new WebSocketService({
      url: baseUrl,
      reconnectAttempts: 5,
      reconnectDelay: 3000,
      autoConnect: shouldConnect,
    })
  })

  const [isConnected, setIsConnected] = React.useState(service.isConnected())

  React.useEffect(() => {
    if (shouldConnect) {
      service.connect().catch((error) => {
        console.error('Erreur connexion WebSocket:', error)
      })

      const unsubscribeStatus = service.subscribe('connection:status', () => {
        setIsConnected(service.isConnected())
      })

      return () => {
        unsubscribeStatus()
      }
    }
  }, [service, shouldConnect])

  return {
    service,
    isConnected,
    subscribe: (type: string, handler: (data: any) => void) => service.subscribe(type, handler),
    send: (message: WebSocketMessage) => service.send(message),
    disconnect: () => service.disconnect(),
  }
}

/**
 * Hook pour intégrer WebSocket avec les notifications
 */
export const useWebSocketNotifications = (url: string) => {
  const { success, error, warning, info } = useNotification()
  const { service, isConnected, subscribe } = useWebSocket(url, true)

  React.useEffect(() => {
    // S'abonner aux notifications
    const unsubNotif = subscribe('notification', (message: WebSocketMessage) => {
      switch (message.category) {
        case 'success':
          success(message.message, message.title)
          break
        case 'error':
          error(message.message, message.title)
          break
        case 'warning':
          warning(message.message, message.title)
          break
        case 'info':
        default:
          info(message.message, message.title)
          break
      }
    })

    // S'abonner aux mises à jour
    const unsubUpdate = subscribe('update', (message: WebSocketMessage) => {
      console.log('[WebSocket] Mise à jour reçue:', message)
    })

    return () => {
      unsubNotif()
      unsubUpdate()
    }
  }, [subscribe, success, error, warning, info])

  return { service, isConnected }
}

import React from 'react'

export default WebSocketService
