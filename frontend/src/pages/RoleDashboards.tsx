import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  TrendingUp as TrendingIcon,
  TrendingDown as TrendingDownIcon,
  DirectionsRun as TripsIcon,
  ConfirmationNumber as TicketsIcon,
  LocalShipping as ParcelsIcon,
  Payment as PaymentIcon,
  AttachMoney as MoneyIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material'

// ========================================
// DASHBOARD COMPTABLE
// ========================================
export const ComptableDashboard: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

  const [kpis, setKpis] = useState({
    totalRevenue: 45230.50,
    totalExpenses: 12340.75,
    netProfit: 32889.75,
    pendingTransactions: 23,
    revenueGrowth: 12.5,
    expenseChange: -3.2,
    profitChange: 18.3,
    pendingChange: -5.1,
  })

  const [transactions, setTransactions] = useState([
    {
      id: 1,
      date: '29/12/2025',
      type: 'REVENUE',
      description: 'Paiement trajet #1234',
      amount: 250.00,
      status: 'COMPLETED',
      reference: 'TRIP-1234',
    },
    {
      id: 2,
      date: '28/12/2025',
      type: 'EXPENSE',
      description: 'Essence véhicule',
      amount: -45.50,
      status: 'COMPLETED',
      reference: 'EXP-2024-001',
    },
  ])

  const KPICard = ({
    title,
    value,
    growth,
    icon: Icon,
    color = '#003D66',
  }: {
    title: string
    value: string | number
    growth: number
    icon: any
    color?: string
  }) => (
    <Card
      sx={{
        border: `2px solid ${color}`,
        borderRadius: '8px',
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' }, flex: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="body2"
              sx={{
                fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' },
                fontWeight: 700,
                color: '#666',
                textTransform: 'uppercase',
                mb: { xs: 0.5, sm: 0.75 },
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 800,
                color: color,
                fontSize: { xs: '1rem', sm: '1.3rem', md: '1.8rem' },
                mb: { xs: 0.5, sm: 0.75 },
              }}
            >
              {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {growth >= 0 ? (
                <TrendingIcon sx={{ fontSize: { xs: 14, md: 16 }, color: '#07A960' }} />
              ) : (
                <TrendingDownIcon sx={{ fontSize: { xs: 14, md: 16 }, color: '#E74C3C' }} />
              )}
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 700,
                  color: growth >= 0 ? '#07A960' : '#E74C3C',
                  fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' },
                }}
              >
                {growth >= 0 ? '+' : ''}{growth}%
              </Typography>
            </Box>
          </Box>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: { xs: 36, sm: 44, md: 56 },
              height: { xs: 36, sm: 44, md: 56 },
              borderRadius: '6px',
              backgroundColor: `${color}15`,
              flexShrink: 0,
            }}
          >
            <Icon sx={{ fontSize: { xs: 18, sm: 22, md: 28 }, color: color }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête Comptable */}
      <Box sx={{ mb: { xs: 2.5, sm: 3, md: 4 }, borderBottom: '3px solid #003D66', pb: { xs: 1.5, sm: 2, md: 3 } }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 800,
            color: '#003D66',
            mb: 0.5,
            fontSize: { xs: '1.1rem', sm: '1.4rem', md: '2rem' },
          }}
        >
          💰 Tableau de Bord Comptable
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: '#666',
            fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
          }}
        >
          Résumé financier et transactions
        </Typography>
      </Box>

      {/* KPIs principaux */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: { xs: 1, sm: 1.5, md: 2.5 },
          mb: { xs: 2, sm: 2.5, md: 4 },
        }}
      >
        <KPICard
          title="Revenus Totaux"
          value={`${kpis.totalRevenue.toLocaleString('fr-FR')} USD`}
          growth={kpis.revenueGrowth}
          icon={MoneyIcon}
          color="#07A960"
        />
        <KPICard
          title="Dépenses Totales"
          value={`${kpis.totalExpenses.toLocaleString('fr-FR')} USD`}
          growth={kpis.expenseChange}
          icon={PaymentIcon}
          color="#E74C3C"
        />
        <KPICard
          title="Bénéfice Net"
          value={`${kpis.netProfit.toLocaleString('fr-FR')} USD`}
          growth={kpis.profitChange}
          icon={AssessmentIcon}
          color="#003D66"
        />
        <KPICard
          title="Trans. Pendantes"
          value={kpis.pendingTransactions}
          growth={kpis.pendingChange}
          icon={TrendingIcon}
          color="#FFD700"
        />
      </Box>

      {/* Tableau des transactions */}
      <Card
        sx={{
          border: '2px solid #003D66',
          borderRadius: '8px',
          backgroundColor: '#ffffff',
          boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
        }}
      >
        <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' } }}>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 800,
              color: '#003D66',
              mb: { xs: 1.5, sm: 2 },
              fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' },
            }}
          >
            📊 Transactions Récentes
          </Typography>

          <TableContainer component={Paper} sx={{ boxShadow: 'none', backgroundColor: 'transparent' }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Date</TableCell>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Type</TableCell>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Description</TableCell>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Montant</TableCell>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Statut</TableCell>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Référence</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' } }}>{tx.date}</TableCell>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' } }}>
                      <Box
                        sx={{
                          display: 'inline-block',
                          px: 1,
                          py: 0.5,
                          borderRadius: '4px',
                          backgroundColor: tx.type === 'REVENUE' ? '#d4edda' : '#f8d7da',
                          color: tx.type === 'REVENUE' ? '#155724' : '#721c24',
                          fontWeight: 600,
                          fontSize: { xs: '0.6rem', sm: '0.7rem', md: '0.75rem' },
                        }}
                      >
                        {tx.type === 'REVENUE' ? '📥 REVENU' : '📤 DÉPENSE'}
                      </Box>
                    </TableCell>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' } }}>{tx.description}</TableCell>
                    <TableCell
                      align="right"
                      sx={{
                        fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' },
                        color: tx.amount >= 0 ? '#07A960' : '#E74C3C',
                        fontWeight: 700,
                      }}
                    >
                      {tx.amount >= 0 ? '+' : ''}{tx.amount.toLocaleString('fr-FR')} USD
                    </TableCell>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' } }}>
                      <Box
                        sx={{
                          display: 'inline-block',
                          px: 1,
                          py: 0.5,
                          borderRadius: '4px',
                          backgroundColor: '#d1ecf1',
                          color: '#0c5460',
                          fontWeight: 600,
                          fontSize: { xs: '0.6rem', sm: '0.7rem', md: '0.75rem' },
                        }}
                      >
                        ✓ {tx.status}
                      </Box>
                    </TableCell>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, color: '#666' }}>{tx.reference}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  )
}

// ========================================
// DASHBOARD GUICHETIER
// ========================================
export const GuichethierDashboard: React.FC = () => {
  const [kpis, setKpis] = useState({
    ticketsVendus: 156,
    calisTraites: 42,
    revenus: 15420.50,
    clientsAujourd: 28,
    ticketsGrowth: 8.3,
    calisGrowth: 12.1,
    revenuesGrowth: 5.4,
    clientsGrowth: 3.2,
  })

  const KPICard = ({
    title,
    value,
    growth,
    icon: Icon,
    color = '#003D66',
  }: {
    title: string
    value: string | number
    growth: number
    icon: any
    color?: string
  }) => (
    <Card
      sx={{
        border: `2px solid ${color}`,
        borderRadius: '8px',
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' }, flex: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="body2"
              sx={{
                fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' },
                fontWeight: 700,
                color: '#666',
                textTransform: 'uppercase',
                mb: { xs: 0.5, sm: 0.75 },
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 800,
                color: color,
                fontSize: { xs: '1rem', sm: '1.3rem', md: '1.8rem' },
                mb: { xs: 0.5, sm: 0.75 },
              }}
            >
              {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {growth >= 0 ? (
                <TrendingIcon sx={{ fontSize: { xs: 14, md: 16 }, color: '#07A960' }} />
              ) : (
                <TrendingDownIcon sx={{ fontSize: { xs: 14, md: 16 }, color: '#E74C3C' }} />
              )}
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 700,
                  color: growth >= 0 ? '#07A960' : '#E74C3C',
                  fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' },
                }}
              >
                {growth >= 0 ? '+' : ''}{growth}%
              </Typography>
            </Box>
          </Box>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: { xs: 36, sm: 44, md: 56 },
              height: { xs: 36, sm: 44, md: 56 },
              borderRadius: '6px',
              backgroundColor: `${color}15`,
              flexShrink: 0,
            }}
          >
            <Icon sx={{ fontSize: { xs: 18, sm: 22, md: 28 }, color: color }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête Guichetier */}
      <Box sx={{ mb: { xs: 2.5, sm: 3, md: 4 }, borderBottom: '3px solid #CE1126', pb: { xs: 1.5, sm: 2, md: 3 } }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 800,
            color: '#CE1126',
            mb: 0.5,
            fontSize: { xs: '1.1rem', sm: '1.4rem', md: '2rem' },
          }}
        >
          🎫 Tableau de Bord Guichetier
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: '#666',
            fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
          }}
        >
          Ventes tickets et colis
        </Typography>
      </Box>

      {/* KPIs principaux */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: { xs: 1, sm: 1.5, md: 2.5 },
          mb: { xs: 2, sm: 2.5, md: 4 },
        }}
      >
        <KPICard
          title="Tickets Vendus"
          value={kpis.ticketsVendus}
          growth={kpis.ticketsGrowth}
          icon={TicketsIcon}
          color="#CE1126"
        />
        <KPICard
          title="Colis Traités"
          value={kpis.calisTraites}
          growth={kpis.calisGrowth}
          icon={ParcelsIcon}
          color="#007A5E"
        />
        <KPICard
          title="Revenus du Jour"
          value={`${kpis.revenus.toLocaleString('fr-FR')} USD`}
          growth={kpis.revenuesGrowth}
          icon={MoneyIcon}
          color="#003D66"
        />
        <KPICard
          title="Clients Aujourd'hui"
          value={kpis.clientsAujourd}
          growth={kpis.clientsGrowth}
          icon={TrendingIcon}
          color="#FFD700"
        />
      </Box>

      {/* Activités récentes */}
      <Card
        sx={{
          border: '2px solid #CE1126',
          borderRadius: '8px',
          backgroundColor: '#ffffff',
          boxShadow: '0 2px 8px rgba(206, 17, 38, 0.08)',
        }}
      >
        <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' } }}>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 800,
              color: '#CE1126',
              mb: { xs: 1.5, sm: 2 },
              fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' },
            }}
          >
            📋 Activités Récentes
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {[
              { type: '🎫', desc: 'Vente ticket trajet #1234', time: 'Il y a 2 min' },
              { type: '📦', desc: 'Traitement colis client', time: 'Il y a 5 min' },
              { type: '🎫', desc: 'Retour ticket #5678', time: 'Il y a 12 min' },
            ].map((activity, idx) => (
              <Box
                key={idx}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 1.5,
                  backgroundColor: '#f9f9f9',
                  borderRadius: '6px',
                  borderLeft: '3px solid #CE1126',
                }}
              >
                <Box>
                  <Typography sx={{ fontSize: '1.2rem', mb: 0.25 }}>{activity.type}</Typography>
                  <Typography sx={{ fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' }, color: '#666' }}>
                    {activity.desc}
                  </Typography>
                </Box>
                <Typography sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, color: '#999' }}>
                  {activity.time}
                </Typography>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

// ========================================
// DASHBOARD CHAUFFEUR
// ========================================
export const ChauffeurdashboardContent: React.FC = () => {
  const [kpis, setKpis] = useState({
    trajetsAujourd: 8,
    kmParcourus: 284,
    revenus: 3240.50,
    evaluations: 4.8,
    trajetsGrowth: 5.2,
    kmGrowth: 2.1,
    revenuesGrowth: 7.3,
    evaluationsGrowth: 2.1,
  })

  const KPICard = ({
    title,
    value,
    growth,
    icon: Icon,
    color = '#003D66',
  }: {
    title: string
    value: string | number
    growth: number
    icon: any
    color?: string
  }) => (
    <Card
      sx={{
        border: `2px solid ${color}`,
        borderRadius: '8px',
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' }, flex: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="body2"
              sx={{
                fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' },
                fontWeight: 700,
                color: '#666',
                textTransform: 'uppercase',
                mb: { xs: 0.5, sm: 0.75 },
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 800,
                color: color,
                fontSize: { xs: '1rem', sm: '1.3rem', md: '1.8rem' },
                mb: { xs: 0.5, sm: 0.75 },
              }}
            >
              {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {growth >= 0 ? (
                <TrendingIcon sx={{ fontSize: { xs: 14, md: 16 }, color: '#07A960' }} />
              ) : (
                <TrendingDownIcon sx={{ fontSize: { xs: 14, md: 16 }, color: '#E74C3C' }} />
              )}
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 700,
                  color: growth >= 0 ? '#07A960' : '#E74C3C',
                  fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' },
                }}
              >
                {growth >= 0 ? '+' : ''}{growth}%
              </Typography>
            </Box>
          </Box>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: { xs: 36, sm: 44, md: 56 },
              height: { xs: 36, sm: 44, md: 56 },
              borderRadius: '6px',
              backgroundColor: `${color}15`,
              flexShrink: 0,
            }}
          >
            <Icon sx={{ fontSize: { xs: 18, sm: 22, md: 28 }, color: color }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête Chauffeur */}
      <Box sx={{ mb: { xs: 2.5, sm: 3, md: 4 }, borderBottom: '3px solid #003D66', pb: { xs: 1.5, sm: 2, md: 3 } }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 800,
            color: '#003D66',
            mb: 0.5,
            fontSize: { xs: '1.1rem', sm: '1.4rem', md: '2rem' },
          }}
        >
          🚗 Tableau de Bord Chauffeur
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: '#666',
            fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
          }}
        >
          Trajets et performances
        </Typography>
      </Box>

      {/* KPIs principaux */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: { xs: 1, sm: 1.5, md: 2.5 },
          mb: { xs: 2, sm: 2.5, md: 4 },
        }}
      >
        <KPICard
          title="Trajets Aujourd'hui"
          value={kpis.trajetsAujourd}
          growth={kpis.trajetsGrowth}
          icon={TripsIcon}
          color="#003D66"
        />
        <KPICard
          title="km Parcourus"
          value={`${kpis.kmParcourus} km`}
          growth={kpis.kmGrowth}
          icon={TrendingIcon}
          color="#007A5E"
        />
        <KPICard
          title="Revenus du Jour"
          value={`${kpis.revenus.toLocaleString('fr-FR')} USD`}
          growth={kpis.revenuesGrowth}
          icon={MoneyIcon}
          color="#CE1126"
        />
        <KPICard
          title="Évaluations"
          value={`${kpis.evaluations} ⭐`}
          growth={kpis.evaluationsGrowth}
          icon={AssessmentIcon}
          color="#FFD700"
        />
      </Box>

      {/* Trajets du jour */}
      <Card
        sx={{
          border: '2px solid #003D66',
          borderRadius: '8px',
          backgroundColor: '#ffffff',
          boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
        }}
      >
        <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' } }}>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 800,
              color: '#003D66',
              mb: { xs: 1.5, sm: 2 },
              fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' },
            }}
          >
            🚗 Trajets du Jour
          </Typography>

          <TableContainer component={Paper} sx={{ boxShadow: 'none', backgroundColor: 'transparent' }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Heure</TableCell>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Itinéraire</TableCell>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Distance</TableCell>
                  <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' }, fontWeight: 700 }}>Statut</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[
                  { time: '07:00', route: 'Ouagadougou → Bobo', distance: '32 km', status: 'COMPLÉTÉ' },
                  { time: '09:30', route: 'Bobo → Ouagadougou', distance: '32 km', status: 'EN COURS' },
                  { time: '12:00', route: 'Ouagadougou → Koudougou', distance: '45 km', status: 'PLANIFIÉ' },
                ].map((trip, idx) => (
                  <TableRow key={idx}>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' } }}>{trip.time}</TableCell>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' } }}>{trip.route}</TableCell>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' } }}>{trip.distance}</TableCell>
                    <TableCell sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' } }}>
                      <Box
                        sx={{
                          display: 'inline-block',
                          px: 1,
                          py: 0.5,
                          borderRadius: '4px',
                          backgroundColor:
                            trip.status === 'COMPLÉTÉ' ? '#d4edda' : trip.status === 'EN COURS' ? '#fff3cd' : '#d1ecf1',
                          color:
                            trip.status === 'COMPLÉTÉ' ? '#155724' : trip.status === 'EN COURS' ? '#856404' : '#0c5460',
                          fontWeight: 600,
                          fontSize: { xs: '0.6rem', sm: '0.7rem', md: '0.75rem' },
                        }}
                      >
                        {trip.status}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  )
}
