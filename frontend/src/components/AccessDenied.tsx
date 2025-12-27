import React from 'react'
import { Box, Container, Typography, Button, Alert } from '@mui/material'
import { govStyles } from '../styles/govStyles'
import { GovPageWrapper } from './GovPageComponents'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'

interface AccessDeniedProps {
  requiredRoles?: string[]
  message?: string
}

/**
 * Composant d'affichage pour accès refusé
 */
export const AccessDenied: React.FC<AccessDeniedProps> = ({
  requiredRoles = [],
  message = 'Vous n\'avez pas les permissions requises pour accéder à cette page.',
}) => {
  return (
    <GovPageWrapper>
      <Container maxWidth="sm" sx={{ my: 6 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3,
            textAlign: 'center',
            py: 6,
            px: 3,
            border: `3px solid ${govStyles.colors.primary}`,
            borderRadius: '8px',
            backgroundColor: '#f5f5f5',
          }}
        >
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              backgroundColor: govStyles.colors.danger,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <LockOutlinedIcon sx={{ fontSize: 40, color: 'white' }} />
          </Box>

          <Typography
            variant="h4"
            sx={{
              color: govStyles.colors.primary,
              fontWeight: 'bold',
              mb: 1,
            }}
          >
            Accès Refusé
          </Typography>

          <Alert severity="error" sx={{ width: '100%' }}>
            {message}
          </Alert>

          {requiredRoles && requiredRoles.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                <strong>Rôles requis :</strong>
              </Typography>
              <Typography variant="body2" sx={{ color: 'gray' }}>
                {requiredRoles.join(', ')}
              </Typography>
            </Box>
          )}

          <Typography variant="body2" sx={{ color: 'gray', mt: 2 }}>
            Si vous pensez que c'est une erreur, veuillez contacter votre administrateur système.
          </Typography>

          <Box sx={{ display: 'flex', gap: 2, mt: 3, width: '100%', justifyContent: 'center' }}>
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
            <Button
              variant="outlined"
              sx={{
                color: govStyles.colors.primary,
                borderColor: govStyles.colors.primary,
                '&:hover': {
                  backgroundColor: 'rgba(0, 61, 102, 0.04)',
                },
              }}
              href="/"
            >
              Accueil
            </Button>
          </Box>
        </Box>
      </Container>
    </GovPageWrapper>
  )
}

export default AccessDenied
