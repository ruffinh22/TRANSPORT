import React from 'react'
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  Stack,
  Divider,
} from '@mui/material'
import {
  DirectionsRun as TransportIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
  Public as GlobalIcon,
  VerifiedUser as TrustIcon,
  Language as LanguageIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { GovernmentHeader } from '../components/GovernmentHeader'
import { GovernmentFooter } from '../components/GovernmentFooter'

export const LandingPage: React.FC = () => {
  const navigate = useNavigate()

  const features = [
    {
      icon: <TransportIcon sx={{ fontSize: 40 }} />,
      title: 'Gestion Complète du Transport',
      description: 'Suivi en temps réel des trajets, billets et colis avec portail passager',
    },
    {
      icon: <SecurityIcon sx={{ fontSize: 40 }} />,
      title: 'Sécurité Gouvernementale',
      description: 'Normes de sécurité burkinabée, chiffrement des données, audit trail complet',
    },
    {
      icon: <PerformanceIcon sx={{ fontSize: 40 }} />,
      title: 'Performance Optimale',
      description: 'Infrastructure rapide et fiable conforme aux standards internationaux',
    },
    {
      icon: <TrustIcon sx={{ fontSize: 40 }} />,
      title: 'Conformité & Certifications',
      description: 'Conforme aux régulations burkinabées et normes OHADA',
    },
    {
      icon: <GlobalIcon sx={{ fontSize: 40 }} />,
      title: 'Couverture Nationale',
      description: 'Opère dans toutes les régions du Burkina Faso avec support local',
    },
    {
      icon: <LanguageIcon sx={{ fontSize: 40 }} />,
      title: 'Multi-Langues',
      description: 'Français, Mooré, Dioula et autres langues locales',
    },
  ]

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {/* Government Header */}
      <GovernmentHeader language="fr" />

      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
          py: { xs: 6, md: 10 },
          borderBottom: '1px solid #e0e0e0',
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography
                variant="h2"
                sx={{
                  fontWeight: 800,
                  mb: 2,
                  background: 'linear-gradient(135deg, #EF3B39 0%, #007A5E 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Plateforme Nationale de Gestion du Transport
              </Typography>
              <Typography variant="h5" color="textSecondary" sx={{ mb: 4, fontWeight: 500 }}>
                Système officiel du gouvernement du Burkina Faso pour la gestion intégrée du transport routier
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => navigate('/login')}
                  sx={{
                    background: 'linear-gradient(135deg, #EF3B39 0%, #C62C2A 100%)',
                    color: 'white',
                    fontSize: '1.05rem',
                  }}
                >
                  Accès Administrateur
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  sx={{
                    borderColor: '#007A5E',
                    color: '#007A5E',
                    fontSize: '1.05rem',
                  }}
                >
                  En savoir plus
                </Button>
              </Stack>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper
                elevation={3}
                sx={{
                  p: 4,
                  background: 'white',
                  borderTop: '4px solid #EF3B39',
                  borderLeft: '4px solid #007A5E',
                }}
              >
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3 }}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#EF3B39' }}>
                      1000+
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Trajets quotidiens
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#007A5E' }}>
                      500K+
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Passagers/mois
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#EF3B39' }}>
                      13
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Régions couvertes
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#007A5E' }}>
                      99.9%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Disponibilité
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Box sx={{ py: { xs: 8, md: 12 }, backgroundColor: '#ffffff' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 2 }}>
              Fonctionnalités Principales
            </Typography>
            <Divider sx={{ width: 100, mx: 'auto', height: 4, backgroundColor: '#EF3B39', mb: 2 }} />
            <Typography variant="h6" color="textSecondary">
              Une solution complète pour la gestion moderne du transport au Burkina Faso
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-8px)',
                      boxShadow: '0 8px 24px rgba(239, 59, 57, 0.15)',
                    },
                  }}
                >
                  <CardContent sx={{ flex: 1, textAlign: 'center' }}>
                    <Box
                      sx={{
                        display: 'inline-flex',
                        p: 1.5,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #EF3B39 0%, #007A5E 100%)',
                        color: 'white',
                        mb: 2,
                      }}
                    >
                      {feature.icon}
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #EF3B39 0%, #007A5E 100%)',
          color: 'white',
          py: { xs: 6, md: 8 },
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h3" sx={{ fontWeight: 700, mb: 2 }}>
            Prêt à commencer?
          </Typography>
          <Typography variant="h6" sx={{ mb: 4, opacity: 0.95 }}>
            Connectez-vous avec vos identifiants gouvernementaux pour accéder au tableau de bord
          </Typography>
          <Button
            variant="contained"
            size="large"
            sx={{
              backgroundColor: 'white',
              color: '#EF3B39',
              fontWeight: 700,
              fontSize: '1.05rem',
              px: 4,
              '&:hover': {
                backgroundColor: '#f0f0f0',
              },
            }}
            onClick={() => navigate('/login')}
          >
            Accès Sécurisé →
          </Button>
        </Container>
      </Box>

      {/* Footer */}
      <GovernmentFooter language="fr" />
    </Box>
  )
}
