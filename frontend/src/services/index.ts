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
}

export const paymentService = {
  list: (params?: any) => apiClient.get('/payments/', { params }),
  get: (id: number) => apiClient.get(`/payments/${id}/`),
  create: (data: any) => apiClient.post('/payments/', data),
}
