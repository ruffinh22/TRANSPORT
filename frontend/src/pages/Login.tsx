import React, { useState } from 'react'
import {
  Container,
  Paper,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
} from '@mui/material'
import { useAppDispatch, useAppSelector } from '../hooks'
import { login } from '../store/authSlice'
import { useNavigate } from 'react-router-dom'
import { GovernmentHeader } from '../components/GovernmentHeader'
import { GovernmentFooter } from '../components/GovernmentFooter'

export const Login: React.FC = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { loading, error } = useAppSelector((state) => state.auth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    const result = await dispatch(login({ email, password }))
    if (result.meta.requestStatus === 'fulfilled') {
      navigate('/dashboard')
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Government Header */}
      <GovernmentHeader language="fr" />
      
      {/* Login Content */}
      <Container maxWidth="sm" sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', py: 8 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          <Typography component="h1" variant="h4" sx={{ mb: 3, fontWeight: 700, background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)', backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Accès Administrateur
          </Typography>
          {error && <Alert severity="error" sx={{ mb: 2, width: '100%' }}>{error}</Alert>}
          <Paper sx={{ p: 4, width: '100%', borderTop: '4px solid #CE1126' }}>
            <form onSubmit={handleLogin}>
              <TextField
                fullWidth
                margin="normal"
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <TextField
                fullWidth
                margin="normal"
              label="Mot de passe"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)' }}
              disabled={loading}
            >
              {loading ? 'Connexion en cours...' : 'Se connecter'}
            </Button>
          </form>
        </Paper>
        </Box>
      </Container>
      
      {/* Government Footer */}
      <GovernmentFooter language="fr" />
    </Box>
  )
}
