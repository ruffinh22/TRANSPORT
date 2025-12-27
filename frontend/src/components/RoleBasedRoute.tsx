import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAppSelector } from '../hooks'
import { Box, Alert, Button, Container } from '@mui/material'
import { govStyles } from '../styles/govStyles'

interface RoleBasedRouteProps {
  children: React.ReactNode
  requiredRoles?: string[]
  requiredPermissions?: string[]
}

/**
 * Composant RoleBasedRoute pour contrôler l'accès basé sur les rôles et permissions
 * Remplace ProtectedRoute et ajoute le support RBAC
 */
export const RoleBasedRoute: React.FC<RoleBasedRouteProps> = ({
  children,
  requiredRoles = [],
  requiredPermissions = [],
}) => {
  const { isAuthenticated, user, loading } = useAppSelector((state) => state.auth)

  // En cours de chargement
  if (loading) {
    return (
      <Container maxWidth="sm" sx={{ mt: 4 }}>
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <p>Chargement...</p>
        </Box>
      </Container>
    )
  }

  // Non authentifié
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Utilisateur n'existe pas
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Vérifier les rôles requis
  if (requiredRoles && requiredRoles.length > 0) {
    const userRoles = user.roles || []
    const hasRequiredRole = requiredRoles.some((role) =>
      userRoles.includes(role)
    )

    if (!hasRequiredRole) {
      return (
        <Container maxWidth="sm" sx={{ mt: 4 }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 3,
              py: 6,
            }}
          >
            <Alert severity="error" sx={{ width: '100%' }}>
              <strong>Accès refusé</strong>
              <br />
              Vous n'avez pas les permissions requises pour accéder à cette page.
              <br />
              <small>Rôles requis: {requiredRoles.join(', ')}</small>
            </Alert>
            <Button
              variant="contained"
              sx={{
                backgroundColor: govStyles.colors.primary,
                color: 'white',
                '&:hover': {
                  backgroundColor: govStyles.colors.primaryDark,
                },
              }}
              href="/dashboard"
            >
              Retourner au Tableau de Bord
            </Button>
          </Box>
        </Container>
      )
    }
  }

  // Les vérifications des permissions seraient implémentées par le backend
  // à travers les endpoints de l'API qui valident les permissions

  // Utilisateur authentifié et autorisé
  return <>{children}</>
}

export default RoleBasedRoute
