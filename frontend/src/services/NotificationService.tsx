import React, { createContext, useState, useCallback, ReactNode } from 'react'
import {
  Alert,
  AlertTitle,
  Box,
  IconButton,
  Snackbar,
  Stack,
} from '@mui/material'
import {
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
  id: string
  type: NotificationType
  title?: string
  message: string
  autoClose?: boolean
  duration?: number
  timestamp?: number
  action?: {
    label: string
    callback: () => void
  }
}

interface NotificationContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => string
  removeNotification: (id: string) => void
  clearNotifications: () => void
  success: (message: string, title?: string) => string
  error: (message: string, title?: string) => string
  warning: (message: string, title?: string) => string
  info: (message: string, title?: string) => string
}

export const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

interface NotificationProviderProps {
  children: ReactNode
  maxNotifications?: number
  defaultDuration?: number
}

/**
 * Fournisseur de contexte pour les notifications
 */
export const NotificationProvider: React.FC<NotificationProviderProps> = ({
  children,
  maxNotifications = 5,
  defaultDuration = 4000,
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([])

  const addNotification = useCallback(
    (notification: Omit<Notification, 'id' | 'timestamp'>) => {
      const id = `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      const newNotification: Notification = {
        ...notification,
        id,
        timestamp: Date.now(),
        autoClose: notification.autoClose !== false,
        duration: notification.duration ?? defaultDuration,
      }

      setNotifications((prev) => {
        const updated = [...prev, newNotification]
        // Garder seulement les N dernières notifications
        return updated.slice(-maxNotifications)
      })

      // Auto-fermeture après délai
      if (newNotification.autoClose) {
        setTimeout(() => {
          removeNotification(id)
        }, newNotification.duration)
      }

      return id
    },
    [maxNotifications, defaultDuration]
  )

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== id))
  }, [])

  const clearNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  const success = useCallback(
    (message: string, title?: string) =>
      addNotification({
        type: 'success',
        message,
        title,
      }),
    [addNotification]
  )

  const error = useCallback(
    (message: string, title?: string) =>
      addNotification({
        type: 'error',
        message,
        title,
        autoClose: false, // Les erreurs doivent être fermées manuellement
      }),
    [addNotification]
  )

  const warning = useCallback(
    (message: string, title?: string) =>
      addNotification({
        type: 'warning',
        message,
        title,
      }),
    [addNotification]
  )

  const info = useCallback(
    (message: string, title?: string) =>
      addNotification({
        type: 'info',
        message,
        title,
      }),
    [addNotification]
  )

  const value: NotificationContextType = {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    success,
    error,
    warning,
    info,
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationStack notifications={notifications} onRemove={removeNotification} />
    </NotificationContext.Provider>
  )
}

/**
 * Hook pour utiliser les notifications
 */
export const useNotification = (): NotificationContextType => {
  const context = React.useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotification doit être utilisé à l\'intérieur de NotificationProvider')
  }
  return context
}

/**
 * Composant d'affichage des notifications
 */
interface NotificationStackProps {
  notifications: Notification[]
  onRemove: (id: string) => void
}

const NotificationStack: React.FC<NotificationStackProps> = ({ notifications, onRemove }) => {
  const getIcon = (type: NotificationType) => {
    switch (type) {
      case 'success':
        return <SuccessIcon sx={{ color: '#4caf50' }} />
      case 'error':
        return <ErrorIcon sx={{ color: '#f44336' }} />
      case 'warning':
        return <WarningIcon sx={{ color: '#ff9800' }} />
      case 'info':
        return <InfoIcon sx={{ color: '#2196f3' }} />
    }
  }

  const getSeverity = (type: NotificationType) => {
    return type as 'success' | 'error' | 'warning' | 'info'
  }

  return (
    <Stack
      spacing={1}
      sx={{
        position: 'fixed',
        top: 20,
        right: 20,
        zIndex: 9999,
        maxWidth: 400,
        maxHeight: '80vh',
        overflowY: 'auto',
      }}
    >
      {notifications.map((notif) => (
        <Snackbar
          key={notif.id}
          open={true}
          onClose={() => onRemove(notif.id)}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ position: 'relative' }}
        >
          <Alert
            severity={getSeverity(notif.type)}
            icon={getIcon(notif.type)}
            onClose={() => onRemove(notif.id)}
            action={
              notif.action ? (
                <Box>
                  <IconButton
                    size="small"
                    color="inherit"
                    onClick={() => {
                      notif.action?.callback()
                      onRemove(notif.id)
                    }}
                  >
                    {notif.action.label}
                  </IconButton>
                </Box>
              ) : undefined
            }
            sx={{
              width: '100%',
              mb: 1,
              boxShadow: 2,
              borderRadius: 1,
            }}
          >
            {notif.title && <AlertTitle>{notif.title}</AlertTitle>}
            {notif.message}
          </Alert>
        </Snackbar>
      ))}
    </Stack>
  )
}

export default NotificationProvider
