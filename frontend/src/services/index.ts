import apiClient from './api'

export interface User {
  id: number
  email: string
  phone: string
  first_name: string
  last_name: string
  is_active: boolean
  email_verified: boolean
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

export const authService = {
  register: (data: {
    email: string
    phone: string
    first_name: string
    last_name: string
    password: string
  }) => apiClient.post<any>('/users/register/', data),

  login: (credentials: LoginRequest) =>
    apiClient.post<LoginResponse>('/users/login/', credentials),

  logout: () => apiClient.post('/users/logout/'),

  getProfile: () => apiClient.get<User>('/users/profile/'),

  refreshToken: (refreshToken: string) =>
    apiClient.post('/users/refresh/', { refresh: refreshToken }),
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
}

export const employeeService = {
  list: (params?: any) => apiClient.get('/employees/', { params }),
  get: (id: number) => apiClient.get(`/employees/${id}/`),
  create: (data: any) => apiClient.post('/employees/', data),
  update: (id: number, data: any) => apiClient.put(`/employees/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/employees/${id}/`),
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
