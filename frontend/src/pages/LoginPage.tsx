import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Box,
  TextField,
  Button,
  Typography,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Link,
  Tab,
  Tabs,
} from '@mui/material'
import { useDispatch, useSelector } from 'react-redux'
import { login } from '../store/authSlice'
import { govStyles } from '../styles/govStyles'
import LockIcon from '@mui/icons-material/Lock'
import PersonIcon from '@mui/icons-material/Person'
import EmailIcon from '@mui/icons-material/Email'
import PhoneIcon from '@mui/icons-material/Phone'

/**
 * Page de connexion unifiée pour tous les rôles
 * Design gouvernemental professionnel
 */
const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { loading, error } = useSelector((state: any) => state.auth)
  
  const [tabValue, setTabValue] = useState(0) // 0=Connexion, 1=Inscription
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    // Inscription
    first_name: '',
    last_name: '',
    phone: '',
    password2: '',
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [showPassword, setShowPassword] = useState(false)

  // Validation du formulaire
  const validateEmail = (email: string): boolean => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return re.test(email)
  }

  const validatePassword = (password: string): boolean => {
    return password.length >= 8
  }

  const validatePhone = (phone: string): boolean => {
    const re = /^\+?[1-9]\d{1,14}$/
    return re.test(phone.replace(/\s/g, ''))
  }

  // Gérer la connexion
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    const errors: Record<string, string> = {}

    // Validation
    if (!formData.email) {
      errors.email = 'Email requis'
    } else if (!validateEmail(formData.email)) {
      errors.email = 'Email invalide'
    }

    if (!formData.password) {
      errors.password = 'Mot de passe requis'
    } else if (!validatePassword(formData.password)) {
      errors.password = 'Minimum 8 caractères'
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }

    setFormErrors({})

    try {
      const result = await dispatch(
        login({
          email: formData.email,
          password: formData.password,
        }) as any
      )

      if (result.payload) {
        // Connexion réussie - rediriger vers dashboard
        navigate('/dashboard')
      }
    } catch (err) {
      console.error('Login error:', err)
    }
  }

  // Gérer l'inscription
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    const errors: Record<string, string> = {}

    // Validation
    if (!formData.first_name.trim()) {
      errors.first_name = 'Prénom requis'
    }
    if (!formData.last_name.trim()) {
      errors.last_name = 'Nom requis'
    }
    if (!formData.email) {
      errors.email = 'Email requis'
    } else if (!validateEmail(formData.email)) {
      errors.email = 'Email invalide'
    }
    if (!formData.phone) {
      errors.phone = 'Téléphone requis'
    } else if (!validatePhone(formData.phone)) {
      errors.phone = 'Téléphone invalide'
    }
    if (!formData.password) {
      errors.password = 'Mot de passe requis'
    } else if (!validatePassword(formData.password)) {
      errors.password = 'Minimum 8 caractères'
    }
    if (formData.password !== formData.password2) {
      errors.password2 = 'Les mots de passe ne correspondent pas'
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }

    setFormErrors({})

    // TODO: Implémenter l'appel API d'inscription
    console.log('Registration data:', formData)
  }

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    setFormErrors({})
    setFormData({
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
      password2: '',
    })
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${govStyles.colors.primary}15 0%, ${govStyles.colors.secondary}10 100%)`,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        py: 4,
      }}
    >
      {/* Header */}
      <Box
        sx={{
          textAlign: 'center',
          mb: 4,
          width: '100%',
        }}
      >
        <Typography
          variant="h3"
          sx={{
            fontWeight: 'bold',
            color: govStyles.colors.primary,
            mb: 1,
          }}
        >
          🚌 TKF Transport
        </Typography>
        <Typography
          variant="subtitle1"
          sx={{
            color: govStyles.colors.text,
            fontSize: '1rem',
          }}
        >
          Plateforme de Gestion Moderne des Transports
        </Typography>
      </Box>

      {/* Carte de connexion */}
      <Container maxWidth="sm">
        <Card
          sx={{
            boxShadow: '0 8px 32px rgba(0, 61, 102, 0.1)',
            borderRadius: '12px',
            border: `2px solid ${govStyles.colors.primary}30`,
          }}
        >
          <CardContent sx={{ p: 4 }}>
            {/* Tabs */}
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              variant="fullWidth"
              sx={{
                mb: 3,
                '& .MuiTab-root': {
                  color: govStyles.colors.text,
                  fontWeight: 500,
                  fontSize: '0.95rem',
                },
                '& .Mui-selected': {
                  color: govStyles.colors.primary,
                  fontWeight: 'bold',
                },
                '& .MuiTabs-indicator': {
                  backgroundColor: govStyles.colors.primary,
                  height: 3,
                },
              }}
            >
              <Tab label="Connexion" icon={<LockIcon />} iconPosition="start" />
              <Tab label="Inscription" icon={<PersonIcon />} iconPosition="start" />
            </Tabs>

            {/* Erreur globale */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {/* Panel Connexion */}
            {tabValue === 0 && (
              <Box component="form" onSubmit={handleLogin}>
                <Typography variant="h5" sx={{ mb: 3, color: govStyles.colors.primary }}>
                  Se Connecter
                </Typography>

                {/* Email */}
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  error={!!formErrors.email}
                  helperText={formErrors.email}
                  margin="normal"
                  variant="outlined"
                  InputProps={{
                    startAdornment: <EmailIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                  autoFocus
                />

                {/* Mot de passe */}
                <TextField
                  fullWidth
                  label="Mot de passe"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  error={!!formErrors.password}
                  helperText={formErrors.password}
                  margin="normal"
                  variant="outlined"
                  InputProps={{
                    startAdornment: <LockIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                />

                {/* Boutons d'action */}
                <Box sx={{ display: 'flex', gap: 1, mt: 3, mb: 2 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    type="submit"
                    disabled={loading}
                    sx={{
                      backgroundColor: govStyles.colors.primary,
                      color: 'white',
                      fontWeight: 'bold',
                      py: 1.5,
                      '&:hover': {
                        backgroundColor: govStyles.colors.primaryDark,
                      },
                      '&:disabled': {
                        backgroundColor: govStyles.colors.disabled,
                      },
                    }}
                  >
                    {loading ? <CircularProgress size={24} color="inherit" /> : 'Se Connecter'}
                  </Button>
                </Box>

                {/* Lien Mot de passe oublié */}
                <Box sx={{ textAlign: 'center' }}>
                  <Link
                    href="/forgot-password"
                    sx={{
                      color: govStyles.colors.primary,
                      textDecoration: 'none',
                      fontSize: '0.9rem',
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Mot de passe oublié ?
                  </Link>
                </Box>
              </Box>
            )}

            {/* Panel Inscription */}
            {tabValue === 1 && (
              <Box component="form" onSubmit={handleRegister}>
                <Typography variant="h5" sx={{ mb: 3, color: govStyles.colors.primary }}>
                  Créer un Compte
                </Typography>

                {/* Prénom */}
                <TextField
                  fullWidth
                  label="Prénom"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  error={!!formErrors.first_name}
                  helperText={formErrors.first_name}
                  margin="normal"
                  variant="outlined"
                  disabled={loading}
                  autoFocus
                />

                {/* Nom */}
                <TextField
                  fullWidth
                  label="Nom"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  error={!!formErrors.last_name}
                  helperText={formErrors.last_name}
                  margin="normal"
                  variant="outlined"
                  disabled={loading}
                />

                {/* Email */}
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  error={!!formErrors.email}
                  helperText={formErrors.email}
                  margin="normal"
                  variant="outlined"
                  InputProps={{
                    startAdornment: <EmailIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                />

                {/* Téléphone */}
                <TextField
                  fullWidth
                  label="Téléphone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  error={!!formErrors.phone}
                  helperText={formErrors.phone}
                  margin="normal"
                  variant="outlined"
                  InputProps={{
                    startAdornment: <PhoneIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                  placeholder="+237600000000"
                />

                {/* Mot de passe */}
                <TextField
                  fullWidth
                  label="Mot de passe"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  error={!!formErrors.password}
                  helperText={formErrors.password}
                  margin="normal"
                  variant="outlined"
                  InputProps={{
                    startAdornment: <LockIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                />

                {/* Confirmation mot de passe */}
                <TextField
                  fullWidth
                  label="Confirmer le mot de passe"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password2}
                  onChange={(e) => setFormData({ ...formData, password2: e.target.value })}
                  error={!!formErrors.password2}
                  helperText={formErrors.password2}
                  margin="normal"
                  variant="outlined"
                  InputProps={{
                    startAdornment: <LockIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                />

                {/* Bouton S'inscrire */}
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  type="submit"
                  disabled={loading}
                  sx={{
                    backgroundColor: govStyles.colors.primary,
                    color: 'white',
                    fontWeight: 'bold',
                    py: 1.5,
                    mt: 3,
                    '&:hover': {
                      backgroundColor: govStyles.colors.primaryDark,
                    },
                    '&:disabled': {
                      backgroundColor: govStyles.colors.disabled,
                    },
                  }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'S\'inscrire'}
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <Box sx={{ textAlign: 'center', mt: 4, color: govStyles.colors.text }}>
          <Typography variant="caption">
            © 2024 TKF Transport - Système de Gestion Moderne
          </Typography>
        </Box>
      </Container>
    </Box>
  )
}

export default LoginPage
