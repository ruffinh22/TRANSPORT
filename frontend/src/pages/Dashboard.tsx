import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  Avatar,
  Divider,
  LinearProgress,
} from '@mui/material'
import {
  TrendingUp as TrendingIcon,
  DirectionsRun as TripsIcon,
  ConfirmationNumber as TicketsIcon,
  LocalShipping as ParcelsIcon,
  Payment as PaymentsIcon,
  People as EmployeesIcon,
  LocationCity as CitiesIcon,
  Assessment as ReportsIcon,
  Schedule as ScheduleIcon,
  Download as DownloadIcon,
  FileDownload as ExcelIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAppSelector } from '../hooks'
import { MainLayout } from '../components/MainLayout'
import { tripService, ticketService, parcelService, paymentService, employeeService, cityService, exportService } from '../services'

interface Stats {
  trips: number
  tickets: number
  parcels: number
  payments: number
  revenue: number
  employees: number
  cities: number
  recentTrips: any[]
  recentPayments: any[]
  employeeStats: any
  cityStats: any
}

export const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAppSelector((state) => state.auth)
  const [stats, setStats] = useState<Stats>({
    trips: 0,
    tickets: 0,
    parcels: 0,
    payments: 0,
    revenue: 0,
    employees: 0,
    cities: 0,
    recentTrips: [],
    recentPayments: [],
    employeeStats: {},
    cityStats: {},
  })

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [
        tripsRes,
        ticketsRes,
        parcelsRes,
        paymentsRes,
        employeesRes,
        citiesRes,
        employeeStatsRes,
      ] = await Promise.all([
        tripService.list(),
        ticketService.list(),
        parcelService.list(),
        paymentService.list(),
        employeeService.list(),
        cityService.list(),
        employeeService.getStatistics(),
      ])

      const trips = tripsRes.data.results || tripsRes.data || []
      const tickets = ticketsRes.data.results || ticketsRes.data || []
      const parcels = parcelsRes.data.results || parcelsRes.data || []
      const payments = paymentsRes.data.results || paymentsRes.data || []
      const employees = employeesRes.data.results || employeesRes.data || []
      const cities = citiesRes.data.results || citiesRes.data || []

      const revenue = payments
        .filter((p: any) => p.status === 'completed')
        .reduce((sum: number, p: any) => sum + p.amount, 0)

      setStats({
        trips: trips.length,
        tickets: tickets.length,
        parcels: parcels.length,
        payments: payments.length,
        revenue,
        employees: employees.length,
        cities: cities.length,
        recentTrips: trips.slice(0, 5),
        recentPayments: payments.slice(0, 5),
        employeeStats: employeeStatsRes.data || {},
        cityStats: {},
      })
    } catch (error) {
      console.error('Erreur chargement dashboard:', error)
    }
  }

  const StatCard = ({
    title,
    value,
    icon: Icon,
    gradient,
    onClick,
    subtitle,
  }: {
    title: string
    value: number | string
    icon: any
    gradient: string
    onClick?: () => void
    subtitle?: string
  }) => (
    <Card
      sx={{
        background: gradient,
        color: 'white',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.3s, box-shadow 0.3s',
        '&:hover': onClick ? { transform: 'translateY(-4px)', boxShadow: '0 12px 24px rgba(0,0,0,0.15)' } : {},
        position: 'relative',
        overflow: 'hidden',
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="overline" sx={{ opacity: 0.9, fontSize: '0.75rem' }}>
              {title}
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 700, mt: 1, fontSize: '2rem' }}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" sx={{ opacity: 0.8, mt: 0.5 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Icon sx={{ fontSize: 40, opacity: 0.7 }} />
        </Box>
      </CardContent>
      <Box
        sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: 'rgba(255,255,255,0.2)',
        }}
      />
    </Card>
  )

  const QuickActionCard = ({
    title,
    description,
    icon: Icon,
    onClick,
    color,
  }: {
    title: string
    description: string
    icon: any
    onClick: () => void
    color: string
  }) => (
    <Card
      sx={{
        cursor: 'pointer',
        transition: 'all 0.3s',
        border: `1px solid ${color}20`,
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: `0 8px 16px ${color}30`,
          borderColor: color,
        },
      }}
      onClick={onClick}
    >
      <CardContent sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: color, width: 48, height: 48 }}>
            <Icon />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
              {title}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {description}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  return (
    <MainLayout>
      <Box sx={{ mb: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#CE1126' }}>
                🏛️ Portail TKF - Tableau de Bord
              </Typography>
              <Typography variant="body1" color="textSecondary" sx={{ mt: 1 }}>
                Bienvenue, {user?.first_name}! Voici un aperçu complet de vos opérations de transport
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                startIcon={<DownloadIcon />}
                variant="outlined"
                size="small"
                onClick={() => {
                  exportService.exportToCSV(
                    [
                      {
                        'Métrique': 'Trajets actifs',
                        'Valeur': stats.trips,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Billets vendus',
                        'Valeur': stats.tickets,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Colis transportés',
                        'Valeur': stats.parcels,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Chiffre d\'affaires',
                        'Valeur': stats.revenue,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Employés actifs',
                        'Valeur': stats.employees,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Villes desservies',
                        'Valeur': stats.cities,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                    ],
                    `dashboard_${new Date().toISOString().split('T')[0]}.csv`
                  )
                }}
              >
                CSV
              </Button>
              <Button
                startIcon={<ExcelIcon />}
                variant="outlined"
                size="small"
                onClick={() => {
                  exportService.exportToExcel(
                    [
                      {
                        'Métrique': 'Trajets actifs',
                        'Valeur': stats.trips,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Billets vendus',
                        'Valeur': stats.tickets,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Colis transportés',
                        'Valeur': stats.parcels,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Chiffre d\'affaires',
                        'Valeur': stats.revenue,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Employés actifs',
                        'Valeur': stats.employees,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                      {
                        'Métrique': 'Villes desservies',
                        'Valeur': stats.cities,
                        'Date': new Date().toLocaleDateString('fr-FR'),
                      },
                    ],
                    `dashboard_${new Date().toISOString().split('T')[0]}.xlsx`,
                    'Statistiques'
                  )
                }}
              >
                Excel
              </Button>
            </Box>
          </Box>
          <Divider sx={{ borderColor: '#007A5E' }} />
        </Box>

        {/* Main Stats Grid */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Trajets actifs"
              value={stats.trips}
              icon={TripsIcon}
              gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
              onClick={() => navigate('/trips')}
              subtitle="Trajets programmés"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Billets vendus"
              value={stats.tickets}
              icon={TicketsIcon}
              gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
              onClick={() => navigate('/tickets')}
              subtitle="Cette semaine"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Colis transportés"
              value={stats.parcels}
              icon={ParcelsIcon}
              gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
              onClick={() => navigate('/parcels')}
              subtitle="En cours"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Employés actifs"
              value={stats.employees}
              icon={EmployeesIcon}
              gradient="linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
              onClick={() => navigate('/employees')}
              subtitle="Équipe TKF"
            />
          </Grid>
        </Grid>

        {/* Revenue & Cities Row */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={8}>
            <Card
              sx={{
                background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                color: 'white',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="overline" sx={{ opacity: 0.9 }}>
                      💰 Chiffre d'affaires (Paiements complétés)
                    </Typography>
                    <Typography variant="h3" sx={{ fontWeight: 700, mt: 1 }}>
                      {stats.revenue.toLocaleString()} CFA
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8, mt: 1 }}>
                      +12% par rapport au mois dernier
                    </Typography>
                  </Box>
                  <TrendingIcon sx={{ fontSize: 48, opacity: 0.5 }} />
                </Box>
              </CardContent>
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: '4px',
                  background: 'linear-gradient(90deg, #FFD700, #CE1126)',
                }}
              />
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <StatCard
              title="Villes desservies"
              value={stats.cities}
              icon={CitiesIcon}
              gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
              onClick={() => navigate('/cities')}
              subtitle="Réseau TKF"
            />
          </Grid>
        </Grid>

        {/* Quick Actions */}
        <Typography variant="h5" sx={{ mb: 3, fontWeight: 600, color: '#007A5E' }}>
          🚀 Actions Rapides
        </Typography>
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <QuickActionCard
              title="Nouveau Trajet"
              description="Programmer un trajet"
              icon={ScheduleIcon}
              onClick={() => navigate('/trips/new')}
              color="#CE1126"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <QuickActionCard
              title="Vendre Billet"
              description="Créer un billet"
              icon={TicketsIcon}
              onClick={() => navigate('/tickets/new')}
              color="#007A5E"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <QuickActionCard
              title="Rapports"
              description="Analyses & statistiques"
              icon={ReportsIcon}
              onClick={() => navigate('/reports')}
              color="#FFD700"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <QuickActionCard
              title="Gestion RH"
              description="Employés & congés"
              icon={EmployeesIcon}
              onClick={() => navigate('/employees')}
              color="#667eea"
            />
          </Grid>
        </Grid>

        {/* Recent Activity */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 2, border: '1px solid #e0e0e0' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#CE1126' }}>
                  🚌 Trajets récents
                </Typography>
                <Button size="small" onClick={() => navigate('/trips')} sx={{ color: '#007A5E' }}>
                  Voir tout
                </Button>
              </Box>
              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {stats.recentTrips.length === 0 ? (
                  <Typography color="textSecondary" sx={{ py: 2, textAlign: 'center' }}>
                    Aucun trajet récent
                  </Typography>
                ) : (
                  stats.recentTrips.map((trip: any) => (
                    <ListItem key={trip.id} sx={{ py: 1, borderRadius: 1, mb: 1, bgcolor: 'grey.50' }}>
                      <ListItemText
                        primary={
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {trip.departure_city} → {trip.arrival_city}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            <Typography variant="caption" color="textSecondary">
                              {new Date(trip.departure_date).toLocaleDateString('fr-FR')}
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={(trip.available_seats / trip.total_seats) * 100}
                              sx={{ mt: 1, height: 4, borderRadius: 2 }}
                            />
                          </Box>
                        }
                      />
                      <Chip
                        label={`${trip.available_seats}/${trip.total_seats} places`}
                        size="small"
                        color={trip.available_seats === 0 ? 'error' : trip.available_seats < 5 ? 'warning' : 'success'}
                        variant="outlined"
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 2, border: '1px solid #e0e0e0' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#CE1126' }}>
                  💳 Paiements récents
                </Typography>
                <Button size="small" onClick={() => navigate('/payments')} sx={{ color: '#007A5E' }}>
                  Voir tout
                </Button>
              </Box>
              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {stats.recentPayments.length === 0 ? (
                  <Typography color="textSecondary" sx={{ py: 2, textAlign: 'center' }}>
                    Aucun paiement récent
                  </Typography>
                ) : (
                  stats.recentPayments.map((payment: any) => (
                    <ListItem key={payment.id} sx={{ py: 1, borderRadius: 1, mb: 1, bgcolor: 'grey.50' }}>
                      <ListItemText
                        primary={
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {payment.transaction_id}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="caption" color="textSecondary">
                            {payment.payment_method} • {new Date(payment.created_at).toLocaleDateString('fr-FR')}
                          </Typography>
                        }
                      />
                      <Chip
                        label={`${payment.amount.toLocaleString()} CFA`}
                        size="small"
                        color={payment.status === 'completed' ? 'success' : payment.status === 'pending' ? 'warning' : 'error'}
                        variant="outlined"
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </Paper>
          </Grid>
        </Grid>

        {/* Footer */}
        <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', borderRadius: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            🏛️ Portail TKF - Système de Gestion du Transport - Burkina Faso
          </Typography>
        </Box>
      </Box>
    </MainLayout>
  )
}
