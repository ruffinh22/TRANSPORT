import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  TextField,
  Select,
  MenuItem,
  Alert,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  Settings as SettingsIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'

interface SystemSetting {
  id: string
  name: string
  value: string | boolean | number
  type: 'string' | 'boolean' | 'number'
  description: string
}

interface ApiKey {
  id: string
  name: string
  key: string
  createdAt: string
  lastUsed?: string
}

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<SystemSetting[]>([
    {
      id: 'app_name',
      name: 'Nom de l\'application',
      value: 'Portail TKF',
      type: 'string',
      description: 'Nom affiché dans le header',
    },
    {
      id: 'company_email',
      name: 'Email de l\'entreprise',
      value: 'contact@tkf.bf',
      type: 'string',
      description: 'Email principal de contact',
    },
    {
      id: 'company_phone',
      name: 'Téléphone de l\'entreprise',
      value: '+226 25 30 00 00',
      type: 'string',
      description: 'Numéro de contact principal',
    },
    {
      id: 'enable_notifications',
      name: 'Activer les notifications',
      value: true,
      type: 'boolean',
      description: 'Notifications système activées',
    },
    {
      id: 'max_upload_size',
      name: 'Taille maximum d\'upload (MB)',
      value: 100,
      type: 'number',
      description: 'Taille maximum pour les fichiers uploadés',
    },
    {
      id: 'maintenance_mode',
      name: 'Mode maintenance',
      value: false,
      type: 'boolean',
      description: 'Mode maintenance du système',
    },
  ])

  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    {
      id: '1',
      name: 'Production API Key',
      key: 'sk_live_51234567890abcdefghijk',
      createdAt: '2024-01-15',
      lastUsed: '2024-12-25',
    },
  ])

  const [savedAlert, setSavedAlert] = useState(false)
  const [openApiDialog, setOpenApiDialog] = useState(false)
  const [newApiKeyName, setNewApiKeyName] = useState('')

  const handleSettingChange = (id: string, value: any) => {
    setSettings(settings.map(s => s.id === id ? { ...s, value } : s))
    setSavedAlert(true)
    setTimeout(() => setSavedAlert(false), 3000)
  }

  const handleAddApiKey = () => {
    if (!newApiKeyName.trim()) return
    
    const newKey: ApiKey = {
      id: Date.now().toString(),
      name: newApiKeyName,
      key: `sk_live_${Math.random().toString(36).substring(2, 15)}`,
      createdAt: new Date().toISOString().split('T')[0],
    }
    
    setApiKeys([...apiKeys, newKey])
    setNewApiKeyName('')
    setOpenApiDialog(false)
  }

  const handleDeleteApiKey = (id: string) => {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette clé API?')) {
      setApiKeys(apiKeys.filter(k => k.id !== id))
    }
  }

  return (
    <MainLayout>
      <Box sx={{ mb: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={() => window.history.back()}
              variant="outlined"
              size="small"
            >
              Retour
            </Button>
            <SettingsIcon sx={{ fontSize: 32, color: '#CE1126' }} />
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#CE1126' }}>
              Paramètres du Système
            </Typography>
          </Box>
          <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
            Configuration générale de la plateforme TKF
          </Typography>
        </Box>

        {/* Save Alert */}
        {savedAlert && (
          <Alert severity="success" onClose={() => setSavedAlert(false)} sx={{ mb: 3 }}>
            ✅ Paramètres sauvegardés avec succès!
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* General Settings */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                🔧 Paramètres Généraux
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {settings.filter(s => s.type === 'string').map(setting => (
                  <TextField
                    key={setting.id}
                    label={setting.name}
                    value={setting.value}
                    onChange={(e) => handleSettingChange(setting.id, e.target.value)}
                    fullWidth
                    size="small"
                    helperText={setting.description}
                  />
                ))}

                {settings.filter(s => s.type === 'number').map(setting => (
                  <TextField
                    key={setting.id}
                    label={setting.name}
                    type="number"
                    value={setting.value}
                    onChange={(e) => handleSettingChange(setting.id, parseInt(e.target.value))}
                    fullWidth
                    size="small"
                    helperText={setting.description}
                  />
                ))}
              </Box>
            </Paper>
          </Grid>

          {/* Boolean Settings */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                ⚙️ Options Système
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {settings.filter(s => s.type === 'boolean').map(setting => (
                  <Card key={setting.id} sx={{ bgcolor: 'grey.50' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {setting.name}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {setting.description}
                          </Typography>
                        </Box>
                        <Switch
                          checked={Boolean(setting.value)}
                          onChange={(e) => handleSettingChange(setting.id, e.target.checked)}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </Paper>
          </Grid>

          {/* Email Configuration */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                📧 Configuration Email
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Serveur SMTP"
                    defaultValue="smtp.gmail.com"
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Port SMTP"
                    type="number"
                    defaultValue="587"
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Nom d'utilisateur"
                    defaultValue="contact@tkf.bf"
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Mot de passe"
                    type="password"
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="outlined"
                    onClick={() => alert('Email de test envoyé!')}
                  >
                    Envoyer un email de test
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* API Keys */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  🔑 Clés API
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setOpenApiDialog(true)}
                  sx={{ bgcolor: '#CE1126', '&:hover': { bgcolor: '#9B0C1F' } }}
                >
                  Nouvelle clé
                </Button>
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                      <TableCell sx={{ fontWeight: 700 }}>Nom</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Clé</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Créée le</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Dernière utilisation</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {apiKeys.map(key => (
                      <TableRow key={key.id}>
                        <TableCell>{key.name}</TableCell>
                        <TableCell>
                          <code style={{ fontSize: '0.75rem', color: '#666' }}>
                            {key.key.substring(0, 10)}...{key.key.substring(key.key.length - 4)}
                          </code>
                        </TableCell>
                        <TableCell>{key.createdAt}</TableCell>
                        <TableCell>{key.lastUsed || 'Jamais'}</TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => alert('Fonction de révision à implémenter')}
                            color="info"
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteApiKey(key.id)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          {/* Backup & Maintenance */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                💾 Sauvegarde & Maintenance
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={() => alert('Sauvegarde en cours...')}
                  >
                    Créer une sauvegarde
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    color="warning"
                    onClick={() => alert('Maintenance en cours...')}
                  >
                    Basculer en mode maintenance
                  </Button>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    ℹ️ Dernière sauvegarde: 25 Décembre 2024 à 14:30
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* System Info */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                ℹ️ Informations Système
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="caption" color="textSecondary">Version</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>2.0.0</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="caption" color="textSecondary">Environnement</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>Production</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="caption" color="textSecondary">Uptime</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>99.9%</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="caption" color="textSecondary">Utilisateurs Actifs</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>1,247</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* API Key Dialog */}
      <Dialog open={openApiDialog} onClose={() => setOpenApiDialog(false)}>
        <DialogTitle>Créer une nouvelle clé API</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            autoFocus
            label="Nom de la clé"
            fullWidth
            value={newApiKeyName}
            onChange={(e) => setNewApiKeyName(e.target.value)}
            placeholder="ex: Production API Key"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenApiDialog(false)}>Annuler</Button>
          <Button
            onClick={handleAddApiKey}
            variant="contained"
            sx={{ bgcolor: '#CE1126', '&:hover': { bgcolor: '#9B0C1F' } }}
          >
            Créer
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  )
}

export default SettingsPage
