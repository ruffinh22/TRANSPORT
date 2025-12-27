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
  Stepper,
  Step,
  StepLabel,
} from '@mui/material'
import { govStyles } from '../styles/govStyles'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import EmailIcon from '@mui/icons-material/Email'
import LockIcon from '@mui/icons-material/Lock'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'

/**
 * Page de récupération de mot de passe
 * Processus en 3 étapes: Email -> Code -> Nouveau mot de passe
 */
const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate()
  const [activeStep, setActiveStep] = useState(0) // 0=Email, 1=Code, 2=Nouveau MDP
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})

  const validateEmail = (emailValue: string): boolean => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return re.test(emailValue)
  }

  // Étape 1: Envoyer le code de reset
  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault()
    const errors: Record<string, string> = {}

    if (!email) {
      errors.email = 'Email requis'
    } else if (!validateEmail(email)) {
      errors.email = 'Email invalide'
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }

    setFormErrors({})
    setLoading(true)
    setError('')

    try {
      // TODO: Appel API pour envoyer le code de reset
      // const response = await authService.requestPasswordReset(email)
      
      setSuccess('Un code a été envoyé à votre email')
      setTimeout(() => setActiveStep(1), 1500)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'envoi du code')
    } finally {
      setLoading(false)
    }
  }

  // Étape 2: Valider le code
  const handleValidateCode = async (e: React.FormEvent) => {
    e.preventDefault()
    const errors: Record<string, string> = {}

    if (!code || code.length < 6) {
      errors.code = 'Code à 6 chiffres requis'
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }

    setFormErrors({})
    setLoading(true)
    setError('')

    try {
      // TODO: Appel API pour valider le code
      // const response = await authService.validateResetCode(email, code)
      
      setSuccess('Code valide. Entrez votre nouveau mot de passe.')
      setTimeout(() => setActiveStep(2), 1500)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Code invalide')
    } finally {
      setLoading(false)
    }
  }

  // Étape 3: Définir le nouveau mot de passe
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    const errors: Record<string, string> = {}

    if (!newPassword || newPassword.length < 8) {
      errors.newPassword = 'Minimum 8 caractères'
    }
    if (newPassword !== confirmPassword) {
      errors.confirmPassword = 'Les mots de passe ne correspondent pas'
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }

    setFormErrors({})
    setLoading(true)
    setError('')

    try {
      // TODO: Appel API pour réinitialiser le mot de passe
      // const response = await authService.resetPassword(email, code, newPassword)
      
      setSuccess('Mot de passe réinitialisé avec succès!')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la réinitialisation')
    } finally {
      setLoading(false)
    }
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
      {/* Bouton retour */}
      <Box sx={{ width: '100%', maxWidth: '500px', mb: 2 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          sx={{ color: govStyles.colors.primary }}
          onClick={() => navigate('/login')}
        >
          Retour à la connexion
        </Button>
      </Box>

      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: govStyles.colors.primary }}>
          Récupérer l'accès
        </Typography>
      </Box>

      {/* Carte principale */}
      <Container maxWidth="sm">
        <Card
          sx={{
            boxShadow: '0 8px 32px rgba(0, 61, 102, 0.1)',
            borderRadius: '12px',
            border: `2px solid ${govStyles.colors.primary}30`,
          }}
        >
          <CardContent sx={{ p: 4 }}>
            {/* Stepper */}
            <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
              <Step>
                <StepLabel>Email</StepLabel>
              </Step>
              <Step>
                <StepLabel>Code</StepLabel>
              </Step>
              <Step>
                <StepLabel>Nouveau MDP</StepLabel>
              </Step>
            </Stepper>

            {/* Messages */}
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

            {/* Étape 1: Email */}
            {activeStep === 0 && (
              <Box component="form" onSubmit={handleSendCode}>
                <Typography variant="h6" sx={{ mb: 2, color: govStyles.colors.primary }}>
                  Entrez votre email
                </Typography>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  error={!!formErrors.email}
                  helperText={formErrors.email}
                  margin="normal"
                  InputProps={{
                    startAdornment: <EmailIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                  autoFocus
                />
                <Button
                  fullWidth
                  variant="contained"
                  type="submit"
                  disabled={loading}
                  sx={{
                    backgroundColor: govStyles.colors.primary,
                    color: 'white',
                    mt: 3,
                    py: 1.5,
                    fontWeight: 'bold',
                  }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Envoyer le code'}
                </Button>
              </Box>
            )}

            {/* Étape 2: Code */}
            {activeStep === 1 && (
              <Box component="form" onSubmit={handleValidateCode}>
                <Typography variant="h6" sx={{ mb: 2, color: govStyles.colors.primary }}>
                  Entrez le code reçu
                </Typography>
                <TextField
                  fullWidth
                  label="Code (6 chiffres)"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  error={!!formErrors.code}
                  helperText={formErrors.code}
                  margin="normal"
                  placeholder="000000"
                  inputProps={{ maxLength: 6 }}
                  disabled={loading}
                  autoFocus
                />
                <Typography variant="caption" sx={{ color: 'gray', display: 'block', mt: 1 }}>
                  Vérifiez votre email (spam/promotions compris)
                </Typography>
                <Button
                  fullWidth
                  variant="contained"
                  type="submit"
                  disabled={loading}
                  sx={{
                    backgroundColor: govStyles.colors.primary,
                    color: 'white',
                    mt: 3,
                    py: 1.5,
                    fontWeight: 'bold',
                  }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Valider'}
                </Button>
              </Box>
            )}

            {/* Étape 3: Nouveau mot de passe */}
            {activeStep === 2 && (
              <Box component="form" onSubmit={handleResetPassword}>
                <Typography variant="h6" sx={{ mb: 2, color: govStyles.colors.primary }}>
                  Définir un nouveau mot de passe
                </Typography>
                <TextField
                  fullWidth
                  label="Nouveau mot de passe"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  error={!!formErrors.newPassword}
                  helperText={formErrors.newPassword}
                  margin="normal"
                  InputProps={{
                    startAdornment: <LockIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                  autoFocus
                />
                <TextField
                  fullWidth
                  label="Confirmer le mot de passe"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  error={!!formErrors.confirmPassword}
                  helperText={formErrors.confirmPassword}
                  margin="normal"
                  InputProps={{
                    startAdornment: <LockIcon sx={{ mr: 1, color: govStyles.colors.primary }} />,
                  }}
                  disabled={loading}
                />
                <Button
                  fullWidth
                  variant="contained"
                  type="submit"
                  disabled={loading}
                  sx={{
                    backgroundColor: govStyles.colors.primary,
                    color: 'white',
                    mt: 3,
                    py: 1.5,
                    fontWeight: 'bold',
                  }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Réinitialiser'}
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      </Container>
    </Box>
  )
}

export default ForgotPasswordPage
