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
} from '@mui/material'
import {
  TrendingUp as TrendingIcon,
  DirectionsRun as TripsIcon,
  ConfirmationNumber as TicketsIcon,
  LocalShipping as ParcelsIcon,
  Payment as PaymentsIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAppSelector } from '../hooks'
import { MainLayout } from '../components/MainLayout'
import { tripService, ticketService, parcelService, paymentService } from '../services'

interface Stats {
  trips: number
  tickets: number
  parcels: number
  payments: number
  revenue: number
  recentTrips: any[]
  recentPayments: any[]
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
    recentTrips: [],
    recentPayments: [],
  })

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [tripsRes, ticketsRes, parcelsRes, paymentsRes] = await Promise.all([
        tripService.list(),
        ticketService.list(),
        parcelService.list(),
        paymentService.list(),
      ])

      const trips = tripsRes.data.results || tripsRes.data || []
      const tickets = ticketsRes.data.results || ticketsRes.data || []
      const parcels = parcelsRes.data.results || parcelsRes.data || []
      const payments = paymentsRes.data.results || paymentsRes.data || []

      const revenue = payments
        .filter((p: any) => p.status === 'completed')
        .reduce((sum: number, p: any) => sum + p.amount, 0)

      setStats({
        trips: trips.length,
        tickets: tickets.length,
        parcels: parcels.length,
        payments: payments.length,
        revenue,
        recentTrips: trips.slice(0, 5),
        recentPayments: payments.slice(0, 5),
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
  }: {
    title: string
    value: number | string
    icon: any
    gradient: string
    onClick?: () => void
  }) => (
    <Card
      sx={{
        background: gradient,
        color: 'white',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.3s, box-shadow 0.3s',
        '&:hover': onClick ? { transform: 'translateY(-4px)', boxShadow: '0 12px 24px rgba(0,0,0,0.15)' } : {},
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="overline" sx={{ opacity: 0.9 }}>
              {title}
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 700, mt: 1 }}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </Typography>
          </Box>
          <Icon sx={{ fontSize: 40, opacity: 0.7 }} />
        </Box>
      </CardContent>
    </Card>
  )

  return (
    <MainLayout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
          Bienvenue, {user?.first_name}! 👋
        </Typography>
        <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
          Voici un aperçu de vos opérations de transport
        </Typography>

        {/* Main Stats Grid */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Trajets"
              value={stats.trips}
              icon={TripsIcon}
              gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
              onClick={() => navigate('/trips')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Billets"
              value={stats.tickets}
              icon={TicketsIcon}
              gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
              onClick={() => navigate('/tickets')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Colis"
              value={stats.parcels}
              icon={ParcelsIcon}
              gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
              onClick={() => navigate('/parcels')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Paiements"
              value={stats.payments}
              icon={PaymentsIcon}
              gradient="linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
              onClick={() => navigate('/payments')}
            />
          </Grid>
        </Grid>

        {/* Revenue Card */}
        <Card
          sx={{
            background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
            color: 'white',
            mb: 4,
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="overline" sx={{ opacity: 0.9 }}>
                  Chiffre d'affaires (Paiements complétés)
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, mt: 1 }}>
                  {stats.revenue.toLocaleString()} CFA
                </Typography>
              </Box>
              <TrendingIcon sx={{ fontSize: 48, opacity: 0.5 }} />
            </Box>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Trajets récents
                </Typography>
                <Button size="small" onClick={() => navigate('/trips')}>
                  Voir tout
                </Button>
              </Box>
              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {stats.recentTrips.length === 0 ? (
                  <Typography color="textSecondary" sx={{ py: 2 }}>
                    Aucun trajet
                  </Typography>
                ) : (
                  stats.recentTrips.map((trip: any) => (
                    <ListItem key={trip.id} sx={{ py: 1 }}>
                      <ListItemText
                        primary={`${trip.departure_city} → ${trip.arrival_city}`}
                        secondary={new Date(trip.departure_date).toLocaleDateString('fr-FR')}
                      />
                      <Chip
                        label={`${trip.available_seats}/${trip.total_seats}`}
                        size="small"
                        color={trip.available_seats === 0 ? 'error' : 'success'}
                        variant="outlined"
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Paiements récents
                </Typography>
                <Button size="small" onClick={() => navigate('/payments')}>
                  Voir tout
                </Button>
              </Box>
              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {stats.recentPayments.length === 0 ? (
                  <Typography color="textSecondary" sx={{ py: 2 }}>
                    Aucun paiement
                  </Typography>
                ) : (
                  stats.recentPayments.map((payment: any) => (
                    <ListItem key={payment.id} sx={{ py: 1 }}>
                      <ListItemText
                        primary={payment.transaction_id}
                        secondary={`${payment.payment_method} • ${new Date(payment.created_at).toLocaleDateString('fr-FR')}`}
                      />
                      <Chip
                        label={`${payment.amount.toLocaleString()} CFA`}
                        size="small"
                        color={payment.status === 'completed' ? 'success' : 'warning'}
                        variant="outlined"
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </MainLayout>
  )
}
