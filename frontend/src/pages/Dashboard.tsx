import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Container,
  Typography,
  Button,
  CircularProgress,
  Grid,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import {
  TrendingUp as TrendingIcon,
  DirectionsRun as TripsIcon,
  ConfirmationNumber as TicketsIcon,
  LocalShipping as ParcelsIcon,
  People as EmployeesIcon,
  LocationCity as CitiesIcon,
  Download as DownloadIcon,
  Schedule as ScheduleIcon,
  BarChart as ReportsIcon,
  Description as ExcelIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAppSelector } from '../hooks'
import { MainLayout } from '../components/MainLayout'
import { tripService, ticketService, parcelService, paymentService, employeeService, cityService } from '../services'

interface Stats {
  trips: number
  tickets: number
  parcels: number
  payments: number
  revenue: number
  employees: number
  cities: number
}

export const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAppSelector((state) => state.auth)
  const theme = useTheme()

  const [stats, setStats] = useState<Stats>({
    trips: 0,
    tickets: 0,
    parcels: 0,
    payments: 0,
    revenue: 0,
    employees: 0,
    cities: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      const [tripsRes, ticketsRes, parcelsRes, paymentsRes, employeesRes, citiesRes] = await Promise.all([
        tripService.list().catch(() => ({ data: [] })),
        ticketService.list().catch(() => ({ data: [] })),
        parcelService.list().catch(() => ({ data: [] })),
        paymentService.list().catch(() => ({ data: [] })),
        employeeService.list().catch(() => ({ data: [] })),
        cityService.list().catch(() => ({ data: [] })),
      ])

      const getLength = (res: any) => {
        if (!res || !res.data) return 0
        if (Array.isArray(res.data)) return res.data.length
        if (res.data.results) return res.data.results.length
        return 0
      }

      const trips = getLength(tripsRes)
      const tickets = getLength(ticketsRes)
      const parcels = getLength(parcelsRes)
      const payments = getLength(paymentsRes)
      const employees = getLength(employeesRes)
      const cities = getLength(citiesRes)

      const getArray = (res: any) => {
        if (!res || !res.data) return []
        if (Array.isArray(res.data)) return res.data
        if (res.data.results) return res.data.results
        return []
      }

      const paymentsList = getArray(paymentsRes)
      const revenue = paymentsList
        .filter((p: any) => p.status === 'completed')
        .reduce((sum: number, p: any) => sum + (p.amount || 0), 0)

      setStats({
        trips,
        tickets,
        parcels,
        payments,
        revenue,
        employees,
        cities,
      })
    } catch (error) {
      console.error('Erreur chargement dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  // Composant Carte Stat Gouvernementale
  const GovStatCard = ({
    title,
    value,
    icon: Icon,
    onClick,
    color = '#003D66',
  }: {
    title: string
    value: number | string
    icon: any
    onClick?: () => void
    color?: string
  }) => (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        border: `2px solid ${color}`,
        borderRadius: '8px',
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
        '&:hover': onClick
          ? {
              boxShadow: '0 8px 24px rgba(0, 61, 102, 0.15)',
              transform: 'translateY(-2px)',
              borderColor: color,
            }
          : {},
        position: 'relative',
        overflow: 'hidden',
      }}
      onClick={onClick}
    >
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          backgroundColor: color,
        }}
      />

      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="body2"
              sx={{
                fontSize: '0.85rem',
                fontWeight: 600,
                color: '#666',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                mb: 1,
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: color,
                fontSize: { xs: '1.8rem', md: '2.2rem' },
              }}
            >
              {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
            </Typography>
          </Box>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 56,
              height: 56,
              borderRadius: '8px',
              backgroundColor: `${color}10`,
            }}
          >
            <Icon sx={{ fontSize: 28, color: color }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  // Bouton d'action gouvernemental
  const GovActionButton = ({
    label,
    icon: Icon,
    onClick,
    variant = 'primary',
  }: {
    label: string
    icon: any
    onClick: () => void
    variant?: 'primary' | 'secondary'
  }) => (
    <Button
      startIcon={<Icon />}
      onClick={onClick}
      fullWidth
      variant="contained"
      sx={{
        backgroundColor: variant === 'primary' ? '#003D66' : '#E8E8E8',
        color: variant === 'primary' ? '#ffffff' : '#003D66',
        textTransform: 'uppercase',
        fontWeight: 600,
        fontSize: '0.875rem',
        padding: '12px 16px',
        borderRadius: '6px',
        border: `2px solid ${variant === 'primary' ? '#003D66' : '#999'}`,
        transition: 'all 0.3s ease',
        '&:hover': {
          backgroundColor: variant === 'primary' ? '#002A47' : '#D3D3D3',
          boxShadow: '0 4px 12px rgba(0, 61, 102, 0.15)',
          transform: 'translateY(-1px)',
        },
      }}
    >
      {label}
    </Button>
  )

  if (loading) {
    return (
      <MainLayout>
        <Container maxWidth="lg" sx={{ py: 8, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress sx={{ color: '#003D66', mb: 2 }} />
            <Typography color="textSecondary">Chargement du tableau de bord...</Typography>
          </Box>
        </Container>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <Container maxWidth="lg" sx={{ py: { xs: 2, md: 4 } }}>
        {/* En-tête gouvernemental */}
        <Box sx={{ mb: 4, borderBottom: '3px solid #003D66', pb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 700,
                  color: '#003D66',
                  mb: 0.5,
                  fontSize: { xs: '1.5rem', md: '2rem' },
                }}
              >
                🏛️ TABLEAU DE BORD TKF
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color: '#666',
                  fontSize: '0.95rem',
                }}
              >
                Système de Gestion du Transport - Burkina Faso
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexDirection: { xs: 'column', sm: 'row' }, width: { xs: '100%', md: 'auto' } }}>
              <GovActionButton label="Télécharger CSV" icon={DownloadIcon} onClick={() => {}} variant="secondary" />
              <GovActionButton label="Imprimer" icon={ExcelIcon} onClick={() => {}} />
            </Box>
          </Box>
          {user && (
            <Typography variant="body2" sx={{ color: '#007A5E', fontWeight: 500 }}>
              Bienvenue, <strong>{user.first_name} {user.last_name}</strong> • Connecté depuis le {new Date().toLocaleDateString('fr-FR')}
            </Typography>
          )}
        </Box>

        {/* Grille Principale de Statistiques */}
        <Grid container spacing={2.5} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <GovStatCard
              title="Trajets Actifs"
              value={stats.trips}
              icon={TripsIcon}
              onClick={() => navigate('/trips')}
              color="#003D66"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <GovStatCard
              title="Billets Vendus"
              value={stats.tickets}
              icon={TicketsIcon}
              onClick={() => navigate('/tickets')}
              color="#CE1126"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <GovStatCard
              title="Colis Transportés"
              value={stats.parcels}
              icon={ParcelsIcon}
              onClick={() => navigate('/parcels')}
              color="#007A5E"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <GovStatCard
              title="Employés Actifs"
              value={stats.employees}
              icon={EmployeesIcon}
              onClick={() => navigate('/employees')}
              color="#FFD700"
            />
          </Grid>
        </Grid>

        {/* Rangée Secondaire */}
        <Grid container spacing={2.5} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            {/* Revenu Total */}
            <Card
              sx={{
                backgroundColor: '#003D66',
                color: '#ffffff',
                borderRadius: '8px',
                border: '2px solid #003D66',
                boxShadow: '0 4px 16px rgba(0, 61, 102, 0.2)',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <Box
                sx={{
                  position: 'absolute',
                  top: '-50px',
                  right: '-50px',
                  width: '200px',
                  height: '200px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(206, 17, 38, 0.1)',
                }}
              />
              <CardContent sx={{ p: 3, position: 'relative', zIndex: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography
                      variant="body2"
                      sx={{
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        opacity: 0.9,
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                      }}
                    >
                      Chiffre d'Affaires Total
                    </Typography>
                    <Typography variant="h3" sx={{ fontWeight: 700, mt: 1 }}>
                      {stats.revenue.toLocaleString('fr-FR')} CFA
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.85, mt: 1 }}>
                      Paiements complétés
                    </Typography>
                  </Box>
                  <TrendingIcon sx={{ fontSize: 40, opacity: 0.6 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            {/* Villes et Couverture */}
            <GovStatCard
              title="Villes Desservies"
              value={stats.cities}
              icon={CitiesIcon}
              onClick={() => navigate('/cities')}
              color="#CE1126"
            />
          </Grid>
        </Grid>

        {/* Actions Rapides Professionnelles */}
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: '#003D66',
              mb: 2,
              fontSize: '1.1rem',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            📋 Actions Disponibles
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <GovActionButton label="Ajouter un Trajet" icon={ScheduleIcon} onClick={() => navigate('/trips')} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GovActionButton label="Vendre un Billet" icon={TicketsIcon} onClick={() => navigate('/tickets')} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GovActionButton label="Gestion RH" icon={EmployeesIcon} onClick={() => navigate('/employees')} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GovActionButton label="Rapports" icon={ReportsIcon} onClick={() => navigate('/reports')} />
            </Grid>
          </Grid>
        </Box>

        {/* Pied de page officiel */}
        <Box
          sx={{
            mt: 6,
            pt: 3,
            borderTop: '2px solid #ddd',
            textAlign: 'center',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px',
            p: 3,
          }}
        >
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            🏛️ <strong>TKF - Transporteur Kendrick Faso</strong> | Système de Gestion du Transport
          </Typography>
          <Typography variant="caption" sx={{ color: '#999', mt: 1 }}>
            © 2024-2025 • République du Burkina Faso • Tous droits réservés
          </Typography>
        </Box>
      </Container>
    </MainLayout>
  )
}
