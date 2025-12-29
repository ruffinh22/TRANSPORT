import apiClient from './api'

export interface User {
  id: number
  email: string
  phone: string
  first_name: string
  last_name: string
  is_active: boolean
  email_verified: boolean
  roles?: string[]  // Rôles utilisateur RBAC
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface RegisterData {
  email: string
  phone: string
  first_name: string
  last_name: string
  password: string
  password2: string
}

/**
 * Service d'authentification amélioré avec gestion des sessions
 */
export const authService = {
  register: (data: RegisterData) => apiClient.post<LoginResponse>('/users/register/', data),

  login: (credentials: LoginRequest) =>
    apiClient.post<LoginResponse>('/users/login/', credentials),

  logout: () => apiClient.post('/users/logout/'),

  getProfile: () => apiClient.get<User>('/users/profile/'),

  refreshToken: (refreshToken: string) =>
    apiClient.post('/users/refresh/', { refresh: refreshToken }),

  // Gestion des mots de passe
  requestPasswordReset: (email: string) =>
    apiClient.post('/users/password-reset-request/', { email }),

  resetPassword: (email: string, code: string, newPassword: string) =>
    apiClient.post('/users/password-reset/', {
      email,
      code,
      new_password: newPassword,
    }),

  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.post('/users/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    }),

  // Vérification email/téléphone
  verifyEmail: (token: string) =>
    apiClient.post('/users/verify-email/', { token }),

  requestEmailVerification: () =>
    apiClient.post('/users/request-email-verification/'),

  verifyPhone: (code: string) =>
    apiClient.post('/users/verify-phone/', { code }),

  requestPhoneVerification: () =>
    apiClient.post('/users/request-phone-verification/'),

  // Sessions
  getSessions: () => apiClient.get('/users/sessions/'),

  terminateSession: (sessionId: string) =>
    apiClient.delete(`/users/sessions/${sessionId}/`),

  terminateOtherSessions: () =>
    apiClient.post('/users/sessions/terminate-others/'),
}

export const tripService = {
  list: (params?: any) => apiClient.get('/trips/', { params }),
  get: (id: number) => apiClient.get(`/trips/${id}/`),
  create: (data: any) => apiClient.post('/trips/', data),
  update: (id: number, data: any) => apiClient.put(`/trips/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/trips/${id}/`),
}

export const ticketService = {
  list: (params?: any) => apiClient.get('/tickets/', { params }),
  get: (id: number) => apiClient.get(`/tickets/${id}/`),
  create: (data: any) => apiClient.post('/tickets/', data),
  update: (id: number, data: any) => apiClient.put(`/tickets/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/tickets/${id}/`),
}

export const parcelService = {
  list: (params?: any) => apiClient.get('/parcels/', { params }),
  get: (id: number) => apiClient.get(`/parcels/${id}/`),
  create: (data: any) => apiClient.post('/parcels/', data),
  update: (id: number, data: any) => apiClient.put(`/parcels/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/parcels/${id}/`),
  seed: () => apiClient.post('/parcels/seed/', {}),
}

export const paymentService = {
  list: (params?: any) => apiClient.get('/payments/', { params }),
  get: (id: number) => apiClient.get(`/payments/${id}/`),
  create: (data: any) => apiClient.post('/payments/', data),
  update: (id: number, data: any) => apiClient.put(`/payments/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/payments/${id}/`),
}

export const employeeService = {
  list: (params?: any) => apiClient.get('/employees/employees/', { params }),
  get: (id: number) => apiClient.get(`/employees/employees/${id}/`),
  create: (data: any) => apiClient.post('/employees/employees/', data),
  update: (id: number, data: any) => apiClient.put(`/employees/employees/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/employees/employees/${id}/`),
  getStatistics: () => apiClient.get('/employees/statistics/'),
  getLeaves: (id: number) => apiClient.get(`/employees/${id}/leaves/`),
  getPerformance: (id: number) => apiClient.get(`/employees/${id}/performance/`),
  bulkUpdateStatus: (data: any) => apiClient.post('/employees/bulk_update_status/', data),
}

export const cityService = {
  list: (params?: any) => apiClient.get('/cities/', { params }),
  get: (id: number) => apiClient.get(`/cities/${id}/`),
  create: (data: any) => apiClient.post('/cities/', data),
  update: (id: number, data: any) => apiClient.put(`/cities/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/cities/${id}/`),
  getStatistics: () => apiClient.get('/cities/statistics/'),
  getHubs: () => apiClient.get('/cities/hubs/'),
  getOperational: () => apiClient.get('/cities/operational/'),
  getByRegion: (region: string) => apiClient.get('/cities/by_region/', { params: { region } }),
  getGeolocation: () => apiClient.get('/cities/geolocation/'),
  updateStatistics: (id: number) => apiClient.post(`/cities/${id}/update_statistics/`),
  updateAllStatistics: () => apiClient.post('/cities/update_all_statistics/'),
}

export { exportService } from './exportService'
export { WebSocketService, useWebSocket, useWebSocketNotifications } from './WebSocketService'
export type { WebSocketMessage } from './WebSocketService'
export { NotificationProvider, useNotification } from './NotificationService'
export type { Notification, NotificationType } from './NotificationService'
