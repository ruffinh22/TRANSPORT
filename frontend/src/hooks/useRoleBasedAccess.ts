import { useAppSelector } from './index'

/**
 * Hook pour vérifier les rôles et permissions de l'utilisateur
 */
export const useRoleBasedAccess = () => {
  const { user } = useAppSelector((state) => state.auth)

  const hasRole = (role: string): boolean => {
    if (!user?.roles) return false
    return user.roles.includes(role)
  }

  const hasAnyRole = (roles: string[]): boolean => {
    if (!user?.roles) return false
    return roles.some((role) => user.roles!.includes(role))
  }

  const hasAllRoles = (roles: string[]): boolean => {
    if (!user?.roles) return false
    return roles.every((role) => user.roles!.includes(role))
  }

  /**
   * Vérifier si l'utilisateur est administrateur
   */
  const isAdmin = (): boolean => {
    return hasRole('ADMIN') || hasRole('SUPER_ADMIN')
  }

  /**
   * Vérifier si l'utilisateur est manager
   */
  const isManager = (): boolean => {
    return hasRole('MANAGER')
  }

  /**
   * Vérifier si l'utilisateur est comptable
   */
  const isComptable = (): boolean => {
    return hasRole('COMPTABLE')
  }

  /**
   * Vérifier si l'utilisateur est guichetier
   */
  const isGuichetier = (): boolean => {
    return hasRole('GUICHETIER')
  }

  /**
   * Vérifier si l'utilisateur est chauffeur
   */
  const isCharffeur = (): boolean => {
    return hasRole('CHAUFFEUR')
  }

  /**
   * Vérifier si l'utilisateur est contrôleur
   */
  const isControleur = (): boolean => {
    return hasRole('CONTROLEUR')
  }

  /**
   * Vérifier si l'utilisateur est gestionnaire courrier
   */
  const isGestionnaireCourrier = (): boolean => {
    return hasRole('GESTIONNAIRE_COURRIER')
  }

  return {
    hasRole,
    hasAnyRole,
    hasAllRoles,
    isAdmin,
    isManager,
    isComptable,
    isGuichetier,
    isCharffeur,
    isControleur,
    isGestionnaireCourrier,
    userRoles: user?.roles || [],
  }
}
