import React from 'react'
import {
  Container,
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  IconButton,
} from '@mui/material'
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { useNotification } from '../services/NotificationService'

export const UserProfilePage: React.FC = () => {
  const { success } = useNotification()

  const handleBackClick = () => {
    window.history.back()
  }

  return (
    <MainLayout>
      <Container maxWidth="md" sx={{ py: 4 }}>
        {/* Header avec bouton retour */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
          <IconButton onClick={handleBackClick} size="small">
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Profil Utilisateur
          </Typography>
        </Box>

        {/* Profil Card */}
        <Card>
          <CardContent>
            <Stack spacing={3}>
              <Box>
                <Typography variant="subtitle2" color="textSecondary">
                  Nom
                </Typography>
                <Typography variant="body1">Jean Dupont</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="textSecondary">
                  Email
                </Typography>
                <Typography variant="body1">jean.dupont@transport.bf</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="textSecondary">
                  Position
                </Typography>
                <Typography variant="body1">Manager Opérations</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="textSecondary">
                  Département
                </Typography>
                <Typography variant="body1">Opérations</Typography>
              </Box>

              <Stack direction="row" spacing={2}>
                <Button variant="contained" color="primary">
                  Éditer le profil
                </Button>
                <Button variant="outlined">
                  Changer le mot de passe
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>

        {/* Préférences Card */}
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
              Préférences
            </Typography>
            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" color="textSecondary">
                  Langue
                </Typography>
                <Typography variant="body1">Français</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="textSecondary">
                  Fuseau horaire
                </Typography>
                <Typography variant="body1">Afrique/Ouagadougou</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="textSecondary">
                  Notifications
                </Typography>
                <Typography variant="body2">
                  Email: Activé | SMS: Désactivé | Push: Activé
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Container>
    </MainLayout>
  )
}

export default UserProfilePage
