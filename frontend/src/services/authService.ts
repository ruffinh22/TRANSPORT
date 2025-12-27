/**
 * Service d'authentification complet avec gestion des sessions
 * Inclut login, logout, refresh tokens, password reset, etc.
 */
import apiClient from './api'

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  phone: string
  first_name: string
  last_name: string
  password: string
  password2: string
}

export interface AuthResponse {
  access: string
  refresh: string
  user: {
    id: number
    email: string
    phone: string
    first_name: string
    last_name: string
    roles?: string[]
    is_active: boolean
    email_verified: boolean
  }
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordReset {
  email: string
  code: string
  new_password: string
}

/**
 * Service d'authentification centralisé
 */
export const authService = {
  /**
   * Connexion utilisateur
   */
  login: (credentials: LoginCredentials) =>
    apiClient.post<AuthResponse>('/users/login/', credentials),

  /**
   * Déconnexion utilisateur
   */
  logout: () => apiClient.post('/users/logout/'),

  /**
   * Obtenir le profil utilisateur actuel
   */
  getProfile: () => apiClient.get('/users/profile/'),

  /**
   * Rafraîchir le token d'accès
   */
  refreshToken: (refreshToken: string) =>
    apiClient.post('/users/refresh/', { refresh: refreshToken }),

  /**
   * Inscription d'un nouvel utilisateur
   */
  register: (data: RegisterData) =>
    apiClient.post<AuthResponse>('/users/register/', data),

  /**
   * Demander la réinitialisation du mot de passe
   */
  requestPasswordReset: (data: PasswordResetRequest) =>
    apiClient.post('/users/password-reset-request/', data),

  /**
   * Valider le code de reset et définir un nouveau mot de passe
   */
  resetPassword: (data: PasswordReset) =>
    apiClient.post('/users/password-reset/', data),

  /**
   * Vérifier l'email
   */
  verifyEmail: (token: string) =>
    apiClient.post('/users/verify-email/', { token }),

  /**
   * Demander une nouvelle vérification d'email
   */
  requestEmailVerification: () =>
    apiClient.post('/users/request-email-verification/'),

  /**
   * Vérifier le téléphone avec un code OTP
   */
  verifyPhone: (code: string) =>
    apiClient.post('/users/verify-phone/', { code }),

  /**
   * Demander un code OTP pour vérifier le téléphone
   */
  requestPhoneVerification: () =>
    apiClient.post('/users/request-phone-verification/'),

  /**
   * Changer le mot de passe (utilisateur authentifié)
   */
  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.post('/users/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    }),

  /**
   * Activer l'authentification à deux facteurs
   */
  enableTwoFactor: () =>
    apiClient.post('/users/2fa-enable/'),

  /**
   * Valider la configuration 2FA
   */
  validateTwoFactor: (code: string) =>
    apiClient.post('/users/2fa-validate/', { code }),

  /**
   * Désactiver la 2FA
   */
  disableTwoFactor: (password: string) =>
    apiClient.post('/users/2fa-disable/', { password }),

  /**
   * Obtenir les sessions actives
   */
  getSessions: () =>
    apiClient.get('/users/sessions/'),

  /**
   * Terminer une session
   */
  terminateSession: (sessionId: string) =>
    apiClient.delete(`/users/sessions/${sessionId}/`),

  /**
   * Terminer toutes les autres sessions
   */
  terminateOtherSessions: () =>
    apiClient.post('/users/sessions/terminate-others/'),
}

/**
 * Helper pour gérer les tokens localement
 */
export const tokenManager = {
  /**
   * Sauvegarder les tokens
   */
  saveTokens: (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('token_timestamp', new Date().getTime().toString())
  },

  /**
   * Obtenir le token d'accès
   */
  getAccessToken: (): string | null => {
    return localStorage.getItem('access_token')
  },

  /**
   * Obtenir le token de refresh
   */
  getRefreshToken: (): string | null => {
    return localStorage.getItem('refresh_token')
  },

  /**
   * Supprimer les tokens
   */
  clearTokens: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_timestamp')
  },

  /**
   * Vérifier si les tokens existent
   */
  hasTokens: (): boolean => {
    return !!localStorage.getItem('access_token') && !!localStorage.getItem('refresh_token')
  },

  /**
   * Obtenir le temps écoulé depuis la dernière authentification (en secondes)
   */
  getTokenAge: (): number => {
    const timestamp = localStorage.getItem('token_timestamp')
    if (!timestamp) return 999999
    const now = new Date().getTime()
    return Math.floor((now - parseInt(timestamp)) / 1000)
  },

  /**
   * Vérifier si les tokens sont proches de l'expiration (par défaut 5 minutes)
   */
  isTokenExpiringSoon: (expiryThreshold: number = 300): boolean => {
    const age = tokenManager.getTokenAge()
    // Les tokens JWT expirent généralement après 15 minutes, donc 300s c'est une bonne limite
    return age > expiryThreshold
  },
}

/**
 * Helper pour gérer les préférences utilisateur
 */
export const userPreferencesManager = {
  /**
   * Sauvegarder la préférence de connexion automatique
   */
  setRememberMe: (remember: boolean) => {
    if (remember) {
      localStorage.setItem('remember_me', 'true')
    } else {
      localStorage.removeItem('remember_me')
    }
  },

  /**
   * Vérifier si "Remember me" est activé
   */
  isRememberMeEnabled: (): boolean => {
    return localStorage.getItem('remember_me') === 'true'
  },

  /**
   * Sauvegarder la langue préférée
   */
  setLanguage: (language: string) => {
    localStorage.setItem('preferred_language', language)
  },

  /**
   * Obtenir la langue préférée
   */
  getLanguage: (): string => {
    return localStorage.getItem('preferred_language') || 'fr'
  },

  /**
   * Sauvegarder le fuseau horaire préféré
   */
  setTimezone: (timezone: string) => {
    localStorage.setItem('preferred_timezone', timezone)
  },

  /**
   * Obtenir le fuseau horaire préféré
   */
  getTimezone: (): string => {
    return localStorage.getItem('preferred_timezone') || 'Africa/Douala'
  },
}

/**
 * Helper pour la sécurité
 */
export const securityManager = {
  /**
   * Enregistrer une tentative de connexion échouée
   */
  recordFailedLogin: (email: string) => {
    const key = `failed_login_${email}`
    const count = parseInt(localStorage.getItem(key) || '0') + 1
    localStorage.setItem(key, count.toString())

    // Expirer après 30 minutes
    setTimeout(() => {
      localStorage.removeItem(key)
    }, 30 * 60 * 1000)
  },

  /**
   * Obtenir le nombre de tentatives échouées
   */
  getFailedLoginCount: (email: string): number => {
    return parseInt(localStorage.getItem(`failed_login_${email}`) || '0')
  },

  /**
   * Réinitialiser les tentatives échouées
   */
  resetFailedLogin: (email: string) => {
    localStorage.removeItem(`failed_login_${email}`)
  },

  /**
   * Vérifier si le compte est verrouillé (après 5 tentatives)
   */
  isAccountLocked: (email: string): boolean => {
    return securityManager.getFailedLoginCount(email) >= 5
  },

  /**
   * Sauvegarder l'IP de connexion
   */
  recordLoginIP: async (userEmail: string) => {
    try {
      const response = await fetch('https://api.ipify.org?format=json')
      const data = await response.json()
      localStorage.setItem(`last_login_ip_${userEmail}`, data.ip)
    } catch (error) {
      console.error('Could not fetch IP:', error)
    }
  },

  /**
   * Obtenir la dernière IP de connexion
   */
  getLastLoginIP: (userEmail: string): string | null => {
    return localStorage.getItem(`last_login_ip_${userEmail}`)
  },
}
