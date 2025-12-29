import React from 'react'
import { Box, Typography } from '@mui/material'

interface PermissionGateProps {
  hasPermission: boolean
  children: React.ReactNode
  fallback?: React.ReactNode
  hideOnDenied?: boolean
}

/**
 * Composant pour afficher du contenu basé sur les permissions
 * @param hasPermission - Résultat de la vérification de permission
 * @param children - Contenu à afficher si autorisé
 * @param fallback - Contenu alternatif si non autorisé
 * @param hideOnDenied - Si true, n'affiche rien si non autorisé (au lieu du fallback)
 */
export const PermissionGate: React.FC<PermissionGateProps> = ({
  hasPermission,
  children,
  fallback,
  hideOnDenied = true,
}) => {
  if (!hasPermission) {
    return hideOnDenied ? null : <>{fallback || <Typography color="error">Non autorisé</Typography>}</>
  }

  return <>{children}</>
}

/**
 * Hook personnalisé pour vérifier les permissions avec plus de flexibilité
 */
export const usePermission = (
  action: 'view' | 'create' | 'edit' | 'delete',
  resource: string,
  userPermissions: Record<string, string[]>
) => {
  return userPermissions[action]?.includes(resource) || false
}

export default PermissionGate
