import React, { useState, useEffect } from 'react'
import {
  Container,
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Tab,
  Divider,
  Grid,
  IconButton,
  InputAdornment,
  CircularProgress,
  Chip,
} from '@mui/material'
import { TabContext, TabList, TabPanel } from '@mui/lab'
import { Visibility, VisibilityOff, Edit as EditIcon, Save as SaveIcon, Close as CloseIcon } from '@mui/icons-material'
import { authService } from '../services'
import { govStyles } from '../styles/govStyles'
import DeleteIcon from '@mui/icons-material/Delete'
import SecurityIcon from '@mui/icons-material/Security'
import LogoutIcon from '@mui/icons-material/Logout'

/**
 * Page de profil utilisateur et gestion des sessions
 */
const ProfilePage: React.FC = () => {
  // Récupérer l'utilisateur depuis localStorage
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;
  
  const [tabValue, setTabValue] = useState('0') // 0=Profil, 1=Mots de passe, 2=Sessions
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [sessions, setSessions] = useState<any[]>([])

  // Formulas pour les dialogs
  const [changePasswordOpen, setChangePasswordOpen] = useState(false)
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // Charger les sessions
  useEffect(() => {
    if (tabValue === '2') {
      loadSessions()
    }
  }, [tabValue])

  const loadSessions = async () => {
    setLoading(true)
    try {
      const response = await authService.getSessions()
      setSessions(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des sessions')
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async () => {
    setError('')
    setSuccess('')

    if (!oldPassword || !newPassword || !confirmPassword) {
      setError('Tous les champs sont requis')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Les nouveaux mots de passe ne correspondent pas')
      return
    }

    if (newPassword.length < 8) {
      setError('Le nouveau mot de passe doit avoir au moins 8 caractères')
      return
    }

    setLoading(true)
    try {
      await authService.changePassword(oldPassword, newPassword)
      setSuccess('Mot de passe changé avec succès')
      setChangePasswordOpen(false)
      setOldPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du changement de mot de passe')
    } finally {
      setLoading(false)
    }
  }

  const handleTerminateSession = async (sessionId: string) => {
    if (!window.confirm('Êtes-vous sûr de vouloir terminer cette session ?')) {
      return
    }

    setLoading(true)
    try {
      await authService.terminateSession(sessionId)
      setSuccess('Session terminée')
      loadSessions()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la terminaison de la session')
    } finally {
      setLoading(false)
    }
  }

  const handleTerminateOtherSessions = async () => {
    if (!window.confirm('Cela terminera toutes les autres sessions. Continuer ?')) {
      return
    }

    setLoading(true)
    try {
      await authService.terminateOtherSessions()
      setSuccess('Toutes les autres sessions ont été terminées')
      loadSessions()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la terminaison des sessions')
    } finally {
      setLoading(false)
    }
  }

  if (!user) {
    return <Typography>Chargement...</Typography>
  }

  return (
    <Box>
      <Box
        sx={{
          backgroundColor: '#f5f5f5',
          py: 3,
          px: 3,
          borderBottom: '2px solid #ddd',
          mb: 2,
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#003D66', mb: 1 }}>
            Mon Profil
          </Typography>
          <Typography variant="body2" sx={{ color: 'textSecondary' }}>
            Gestion de votre compte et vos sessions
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="md" sx={{ my: 4 }}>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <TabContext value={tabValue}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <TabList
              onChange={(_, newValue) => setTabValue(newValue)}
              sx={{
                '& .MuiTab-root': {
                  color: govStyles.colors.text,
                  fontWeight: 500,
                },
                '& .Mui-selected': {
                  color: govStyles.colors.primary,
                  fontWeight: 'bold',
                },
                '& .MuiTabs-indicator': {
                  backgroundColor: govStyles.colors.primary,
                },
              }}
            >
              <Tab label="Informations Personnelles" value="0" />
              <Tab label="Sécurité" value="1" icon={<SecurityIcon />} />
              <Tab label="Sessions Actives" value="2" />
            </TabList>
          </Box>

          {/* Onglet 0: Profil */}
          <TabPanel value="0" sx={{ py: 3 }}>
            <Card>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 3, color: govStyles.colors.primary }}>
                  Informations Générales
                </Typography>

                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                  <TextField
                    fullWidth
                    label="Prénom"
                    value={user.first_name}
                    disabled
                    variant="outlined"
                  />
                  <TextField
                    fullWidth
                    label="Nom"
                    value={user.last_name}
                    disabled
                    variant="outlined"
                  />
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={user.email}
                    disabled
                    variant="outlined"
                  />
                  <TextField
                    fullWidth
                    label="Téléphone"
                    value={user.phone}
                    disabled
                    variant="outlined"
                  />
                </Box>

                {/* Rôles */}
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Rôles Assignés:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {user.roles && user.roles.length > 0 ? (
                      user.roles.map((role) => (
                        <Chip
                          key={role}
                          label={role}
                          color="primary"
                          variant="outlined"
                          sx={{
                            borderColor: govStyles.colors.primary,
                            color: govStyles.colors.primary,
                          }}
                        />
                      ))
                    ) : (
                      <Typography variant="caption" sx={{ color: 'gray' }}>
                        Aucun rôle assigné
                      </Typography>
                    )}
                  </Box>
                </Box>

                {/* Statuts de vérification */}
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Vérifications:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Chip
                      label={`Email: ${user.email_verified ? '✓ Vérifié' : '✗ Non vérifié'}`}
                      color={user.email_verified ? 'success' : 'error'}
                      variant="outlined"
                    />
                    <Chip
                      label={`Compte: ${user.is_active ? '✓ Actif' : '✗ Inactif'}`}
                      color={user.is_active ? 'success' : 'error'}
                      variant="outlined"
                    />
                  </Box>
                </Box>

                <Button
                  variant="contained"
                  startIcon={<EditIcon />}
                  sx={{
                    mt: 3,
                    backgroundColor: govStyles.colors.primary,
                    color: 'white',
                  }}
                  disabled
                >
                  Modifier le Profil (À venir)
                </Button>
              </CardContent>
            </Card>
          </TabPanel>

          {/* Onglet 1: Sécurité */}
          <TabPanel value="1" sx={{ py: 3 }}>
            <Card>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 3, color: govStyles.colors.primary }}>
                  Sécurité du Compte
                </Typography>

                <Button
                  variant="contained"
                  sx={{
                    backgroundColor: govStyles.colors.primary,
                    color: 'white',
                    mb: 2,
                  }}
                  onClick={() => setChangePasswordOpen(true)}
                >
                  Changer le Mot de Passe
                </Button>

                <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
                  Authentification à Deux Facteurs (2FA):
                </Typography>
                <Typography variant="body2" sx={{ color: 'gray', mb: 2 }}>
                  Ajoutez une couche de sécurité supplémentaire à votre compte
                </Typography>
                <Button
                  variant="outlined"
                  sx={{
                    color: govStyles.colors.primary,
                    borderColor: govStyles.colors.primary,
                  }}
                  disabled
                >
                  Configurer 2FA (À venir)
                </Button>
              </CardContent>
            </Card>
          </TabPanel>

          {/* Onglet 2: Sessions */}
          <TabPanel value="2" sx={{ py: 3 }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <>
                <Box sx={{ mb: 2 }}>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<LogoutIcon />}
                    onClick={handleTerminateOtherSessions}
                    disabled={sessions.filter((s) => !s.is_current).length === 0}
                  >
                    Terminer les Autres Sessions
                  </Button>
                </Box>

                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ backgroundColor: `${govStyles.colors.primary}15` }}>
                        <TableCell>Appareil</TableCell>
                        <TableCell>Adresse IP</TableCell>
                        <TableCell>Dernière Activité</TableCell>
                        <TableCell>Statut</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {sessions.length > 0 ? (
                        sessions.map((session) => (
                          <TableRow key={session.id}>
                            <TableCell>{session.device_name || 'Appareil inconnu'}</TableCell>
                            <TableCell>{session.ip_address}</TableCell>
                            <TableCell>
                              {new Date(session.last_activity).toLocaleDateString('fr-FR')}
                            </TableCell>
                            <TableCell>
                              <Chip
                                size="small"
                                label={session.is_current ? 'Session Actuelle' : 'Inactif'}
                                color={session.is_current ? 'success' : 'default'}
                              />
                            </TableCell>
                            <TableCell>
                              {!session.is_current && (
                                <Button
                                  size="small"
                                  startIcon={<DeleteIcon />}
                                  color="error"
                                  onClick={() => handleTerminateSession(session.id)}
                                >
                                  Terminer
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={5} sx={{ textAlign: 'center', py: 3 }}>
                            Aucune session active
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </TabPanel>
        </TabContext>
      </Container>

      {/* Dialog Changement de mot de passe */}
      <Dialog open={changePasswordOpen} onClose={() => setChangePasswordOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Changer le Mot de Passe</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <TextField
            fullWidth
            label="Mot de passe actuel"
            type="password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            margin="normal"
            variant="outlined"
            disabled={loading}
          />
          <TextField
            fullWidth
            label="Nouveau mot de passe"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            margin="normal"
            variant="outlined"
            disabled={loading}
          />
          <TextField
            fullWidth
            label="Confirmer le mot de passe"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            margin="normal"
            variant="outlined"
            disabled={loading}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChangePasswordOpen(false)}>Annuler</Button>
          <Button
            variant="contained"
            onClick={handleChangePassword}
            disabled={loading}
            sx={{ backgroundColor: govStyles.colors.primary }}
          >
            {loading ? <CircularProgress size={24} /> : 'Changer'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ProfilePage
