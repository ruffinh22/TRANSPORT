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
  useTheme,
  Tab,
  useMediaQuery,
} from '@mui/material'
import { TabContext, TabList, TabPanel } from '@mui/lab'
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
import { AdminDashboardContent } from './admin/AdminDashboard'
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

// Interface pour les props de DashboardContent
interface DashboardContentProps {
  hasPermission: (action: 'view' | 'create' | 'edit' | 'delete', resource: string) => boolean
  stats: Stats
  navigate: (path: string) => void
  GovStatCard: React.FC<any>
  GovActionButton: React.FC<any>
}

// Permissions par rôle avec actions CRUD
interface RolePermissions {
  view: string[]
  create: string[]
  edit: string[]
  delete: string[]
}

const ROLE_PERMISSIONS: Record<string, RolePermissions> = {
  ADMIN: {
    view: ['trips', 'tickets', 'parcels', 'payments', 'revenue', 'employees', 'cities', 'reports', 'manage_users'],
    create: ['trips', 'tickets', 'parcels', 'payments', 'employees', 'cities', 'users'],
    edit: ['trips', 'tickets', 'parcels', 'payments', 'employees', 'cities', 'users'],
    delete: ['trips', 'tickets', 'parcels', 'payments', 'employees', 'cities', 'users'],
  },
  COMPTABLE: {
    view: ['payments', 'revenue', 'reports', 'employees'],
    create: ['payments', 'reports'],
    edit: ['payments', 'reports'],
    delete: [],
  },
  GUICHETIER: {
    view: ['tickets', 'parcels', 'trips'],
    create: ['tickets', 'parcels'],
    edit: ['tickets', 'parcels'],
    delete: [],
  },
  CHAUFFEUR: {
    view: ['trips', 'tickets'],
    create: [],
    edit: ['trips'],
    delete: [],
  },
  CONTROLEUR: {
    view: ['tickets', 'trips', 'employees'],
    create: [],
    edit: ['trips', 'tickets'],
    delete: [],
  },
  GESTIONNAIRE_COURRIER: {
    view: ['parcels', 'cities'],
    create: ['parcels'],
    edit: ['parcels'],
    delete: [],
  },
  CLIENT: {
    view: ['trips', 'tickets', 'parcels'],
    create: [],
    edit: [],
    delete: [],
  },
}

// Titres de rôles en français
const ROLE_TITLES: Record<string, string> = {
  ADMIN: 'Administrateur',
  COMPTABLE: 'Comptable',
  GUICHETIER: 'Guichetier',
  CHAUFFEUR: 'Chauffeur',
  CONTROLEUR: 'Contrôleur',
  GESTIONNAIRE_COURRIER: 'Gestionnaire de Courrier',
  CLIENT: 'Client',
}

export const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAppSelector((state) => state.auth)
  const theme = useTheme()
  const [tabValue, setTabValue] = useState('0')
  // Fixed import reference for AdminDashboardContent
  
  // Media Queries pour responsivité
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))
  const isLargeScreen = useMediaQuery(theme.breakpoints.up('lg'))

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

  // Déterminer le rôle principal de l'utilisateur
  const userRole = user?.roles?.[0] || 'CLIENT'
  const isAdmin = user?.roles?.includes('ADMIN')
  const userPermissions = ROLE_PERMISSIONS[userRole as keyof typeof ROLE_PERMISSIONS] || ROLE_PERMISSIONS.CLIENT

  // Fonctions pour vérifier les permissions
  const hasPermission = (action: 'view' | 'create' | 'edit' | 'delete', resource: string): boolean => {
    return userPermissions[action].includes(resource)
  }

  const canView = (resource: string): boolean => hasPermission('view', resource)
  const canCreate = (resource: string): boolean => hasPermission('create', resource)
  const canEdit = (resource: string): boolean => hasPermission('edit', resource)
  const canDelete = (resource: string): boolean => hasPermission('delete', resource)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setTabValue(newValue)
  }

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      const [tripsRes, ticketsRes, parcelsRes, paymentsRes, employeesRes, citiesRes] = await Promise.all([
        canView('trips') ? tripService.list().catch(() => ({ data: [] })) : Promise.resolve({ data: [] }),
        canView('tickets') ? ticketService.list().catch(() => ({ data: [] })) : Promise.resolve({ data: [] }),
        canView('parcels') ? parcelService.list().catch(() => ({ data: [] })) : Promise.resolve({ data: [] }),
        canView('payments') ? paymentService.list().catch(() => ({ data: [] })) : Promise.resolve({ data: [] }),
        canView('employees') ? employeeService.list().catch(() => ({ data: [] })) : Promise.resolve({ data: [] }),
        canView('cities') ? cityService.list().catch(() => ({ data: [] })) : Promise.resolve({ data: [] }),
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

  // Composant Carte Stat Gouvernementale - RESPONSIVE
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
        borderRadius: { xs: '6px', sm: '8px', md: '8px' },
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
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
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

      <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' }, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: { xs: 1, md: 2 } }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography
              variant="body2"
              sx={{
                fontSize: { xs: '0.6rem', sm: '0.75rem', md: '0.85rem' },
                fontWeight: 700,
                color: '#666',
                textTransform: 'uppercase',
                letterSpacing: '0.3px',
                mb: { xs: 0.5, sm: 0.75 },
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
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
                lineHeight: 1.1,
                wordBreak: 'break-word',
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
              width: { xs: 36, sm: 44, md: 56 },
              height: { xs: 36, sm: 44, md: 56 },
              borderRadius: '6px',
              backgroundColor: `${color}15`,
              flexShrink: 0,
              minWidth: { xs: 36, sm: 44, md: 56 },
            }}
          >
            <Icon sx={{ fontSize: { xs: 18, sm: 22, md: 28 }, color: color }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  // Bouton d'action gouvernemental - RESPONSIVE
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
        fontWeight: 700,
        fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.875rem' },
        padding: { xs: '8px 8px', sm: '10px 12px', md: '12px 16px' },
        borderRadius: '6px',
        border: `2px solid ${variant === 'primary' ? '#003D66' : '#999'}`,
        transition: 'all 0.3s ease',
        minHeight: { xs: '32px', sm: '36px', md: '44px' },
        '& .MuiButton-startIcon': {
          marginRight: { xs: '3px', sm: '4px', md: '8px' },
          fontSize: { xs: '14px', sm: '16px', md: '20px' },
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        },
        '&:hover': {
          backgroundColor: variant === 'primary' ? '#002A47' : '#D3D3D3',
          boxShadow: '0 4px 12px rgba(0, 61, 102, 0.15)',
          transform: 'translateY(-1px)',
        },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      }}
    >
      {label}
    </Button>
  )

  if (loading) {
    return (
      <MainLayout>
        <Container maxWidth="lg" sx={{ py: { xs: 4, sm: 6, md: 8 }, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: { xs: '300px', md: '400px' } }}>
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress sx={{ color: '#003D66', mb: 2 }} />
            <Typography sx={{ fontSize: { xs: '0.85rem', sm: '0.95rem', md: '1rem' }, color: 'textSecondary' }}>
              Chargement du tableau de bord...
            </Typography>
          </Box>
        </Container>
      </MainLayout>
    )
  }

  return (
    <MainLayout hideGovernmentHeader={true}>
      <Container maxWidth="lg" sx={{ py: { xs: 1, sm: 1.5, md: 3 }, px: { xs: 1, sm: 1.5, md: 2 } }}>
        {/* En-tête gouvernemental - ULTRA RESPONSIVE */}
        <Box sx={{ mb: { xs: 2.5, sm: 3, md: 4 }, borderBottom: '3px solid #003D66', pb: { xs: 1.5, sm: 2, md: 3 } }}>
          <Box 
            sx={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'flex-start', 
              mb: { xs: 1.5, sm: 2, md: 3 },
              flexDirection: { xs: 'column', sm: 'column', md: 'row' },
              gap: { xs: 1.5, sm: 2, md: 3 }
            }}
          >
            <Box sx={{ flex: 1, width: '100%' }}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 800,
                  color: '#003D66',
                  mb: 0.5,
                  fontSize: { xs: '1.1rem', sm: '1.4rem', md: '2rem' },
                  lineHeight: 1.2,
                  wordBreak: 'break-word',
                }}
              >
                🏛️ TKF
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color: '#666',
                  fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
                  fontWeight: 500,
                  lineHeight: 1.4,
                }}
              >
                {ROLE_TITLES[userRole as keyof typeof ROLE_TITLES]} • Gestion du Transport
              </Typography>
            </Box>
            <Box 
              sx={{ 
                display: 'flex', 
                gap: { xs: 0.75, sm: 1 },
                flexDirection: { xs: 'column-reverse', sm: 'row' },
                width: { xs: '100%', sm: 'auto' },
              }}
            >
              <GovActionButton label="CSV" icon={DownloadIcon} onClick={() => {}} variant="secondary" />
              <GovActionButton label="Impr." icon={ExcelIcon} onClick={() => {}} />
            </Box>
          </Box>
          {user && (
            <Typography 
              variant="body2" 
              sx={{ 
                color: '#007A5E', 
                fontWeight: 500,
                fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.9rem' },
                lineHeight: 1.4,
                wordBreak: 'break-word',
              }}
            >
              <strong>Bienvenue {user.first_name} {user.last_name}</strong><br />
              {ROLE_TITLES[userRole as keyof typeof ROLE_TITLES]} • {new Date().toLocaleDateString('fr-FR')}
            </Typography>
          )}
        </Box>

        {/* Onglets pour les admins - ULTRA RESPONSIVE */}
        {isAdmin && (
          <Box sx={{ borderBottom: 3, borderColor: 'divider', mb: { xs: 2, sm: 2.5, md: 4 } }}>
            <TabContext value={tabValue}>
              <TabList 
                onChange={handleTabChange} 
                aria-label="dashboard tabs"
                variant={isMobile ? "fullWidth" : "standard"}
                sx={{
                  minHeight: { xs: '44px', sm: '48px', md: '56px' },
                  '& .MuiTab-root': {
                    fontSize: { xs: '0.65rem', sm: '0.8rem', md: '0.95rem' },
                    padding: { xs: '6px 8px', sm: '8px 12px', md: '12px 20px' },
                    minWidth: { xs: 'auto', sm: '120px', md: '160px' },
                    minHeight: { xs: '44px', sm: '48px', md: '56px' },
                    fontWeight: 600,
                  },
                  '& .MuiTabs-indicator': {
                    height: { xs: '3px', md: '4px' },
                  }
                }}
              >
                <Tab label="📊 Tableau" value="0" />
                <Tab label="🔧 Système" value="1" />
              </TabList>
              <TabPanel value="0" sx={{ p: { xs: 0.75, sm: 1, md: 2 }, pt: { xs: 1.5, sm: 2, md: 3 } }}>
                <DashboardContent
                  hasPermission={hasPermission}
                  stats={stats}
                  navigate={navigate}
                  GovStatCard={GovStatCard}
                  GovActionButton={GovActionButton}
                />
              </TabPanel>
              <TabPanel value="1" sx={{ p: { xs: 0.75, sm: 1, md: 2 } }}>
                <AdminDashboardContent />
              </TabPanel>
            </TabContext>
          </Box>
        )}

        {/* Contenu pour les non-admins */}
        {!isAdmin && (
          <DashboardContent
            hasPermission={hasPermission}
            stats={stats}
            navigate={navigate}
            GovStatCard={GovStatCard}
            GovActionButton={GovActionButton}
          />
        )}

        {/* Pied de page officiel - ULTRA RESPONSIVE */}
        <Box
          sx={{
            mt: { xs: 3, sm: 4, md: 6 },
            pt: { xs: 1.5, sm: 2, md: 3 },
            borderTop: '2px solid #ddd',
            textAlign: 'center',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px',
            p: { xs: 1.5, sm: 2, md: 3 },
          }}
        >
          <Typography 
            variant="body2" 
            sx={{ 
              color: '#666', 
              fontWeight: 600,
              fontSize: { xs: '0.7rem', sm: '0.85rem', md: '1rem' },
              lineHeight: 1.4,
            }}
          >
            🏛️ <strong>TKF</strong> | Système de Gestion du Transport
          </Typography>
          <Typography 
            variant="caption" 
            sx={{ 
              color: '#999', 
              mt: { xs: 0.5, sm: 0.75 },
              display: 'block',
              fontSize: { xs: '0.6rem', sm: '0.7rem', md: '0.8rem' },
              lineHeight: 1.3,
            }}
          >
            © 2024-2025 • Burkina Faso
          </Typography>
        </Box>
      </Container>
    </MainLayout>
  )
}

const DashboardContent: React.FC<DashboardContentProps> = ({ hasPermission, stats, navigate, GovStatCard, GovActionButton }) => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

  return (
    <>
      {/* PREMIÈRE RANGÉE - Cartes principales ULTRA RESPONSIVE */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: { xs: 1, sm: 1.5, md: 2.5 },
          mb: { xs: 2, sm: 2.5, md: 4 }
        }}
      >
        <GovStatCard
          title="Colis"
          value={stats.parcels}
          icon={ParcelsIcon}
          onClick={() => navigate('/parcels')}
          color="#007A5E"
        />
        <GovStatCard
          title="Tickets"
          value={stats.tickets}
          icon={TicketsIcon}
          onClick={() => navigate('/tickets')}
          color="#CE1126"
        />
        <GovStatCard
          title="Paiements"
          value={stats.payments}
          icon={TrendingIcon}
          onClick={() => navigate('/payments')}
          color="#003D66"
        />
        <GovStatCard
          title="Notif."
          value="2"
          icon={DownloadIcon}
          onClick={() => {}}
          color="#FFD700"
        />
      </Box>

      {/* DEUXIÈME RANGÉE - Trajets et Employés ULTRA RESPONSIVE */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
          gap: { xs: 1, sm: 1.5, md: 2.5 },
          mb: { xs: 2, sm: 2.5, md: 4 }
        }}
      >
        <GovStatCard
          title="Trajets"
          value={stats.trips}
          icon={TripsIcon}
          onClick={() => navigate('/trips')}
          color="#003D66"
        />
        <GovStatCard
          title="Employés"
          value={stats.employees}
          icon={EmployeesIcon}
          onClick={() => navigate('/employees')}
          color="#FFD700"
        />
      </Box>

      {/* TROISIÈME RANGÉE - Revenu et Villes ULTRA RESPONSIVE */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
          gap: { xs: 1, sm: 1.5, md: 2.5 },
          mb: { xs: 2, sm: 2.5, md: 4 }
        }}
      >
        <Card
            sx={{
              backgroundColor: '#003D66',
              color: '#ffffff',
              borderRadius: '8px',
              border: '2px solid #003D66',
              boxShadow: '0 4px 16px rgba(0, 61, 102, 0.2)',
              position: 'relative',
              overflow: 'hidden',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
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
            <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' }, position: 'relative', zIndex: 1, flex: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1.5 }}>
                <Box sx={{ minWidth: 0, flex: 1 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.85rem' },
                      fontWeight: 700,
                      opacity: 0.9,
                      textTransform: 'uppercase',
                      letterSpacing: '0.3px',
                      mb: { xs: 0.5, sm: 0.75 },
                    }}
                  >
                    Chiffre d'Affaires
                  </Typography>
                  <Typography 
                    variant="h4" 
                    sx={{ 
                      fontWeight: 800, 
                      mt: { xs: 0.5, sm: 0.75 },
                      fontSize: { xs: '1rem', sm: '1.3rem', md: '1.8rem' },
                      lineHeight: 1.1,
                      wordBreak: 'break-word',
                    }}
                  >
                    {stats.revenue.toLocaleString('fr-FR')}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      opacity: 0.85, 
                      mt: { xs: 0.25, sm: 0.5 },
                      fontSize: { xs: '0.6rem', sm: '0.7rem', md: '0.85rem' },
                    }}
                  >
                    CFA
                  </Typography>
                </Box>
                <TrendingIcon sx={{ fontSize: { xs: 24, sm: 28, md: 40 }, opacity: 0.6, flexShrink: 0 }} />
              </Box>
            </CardContent>
          </Card>

        <GovStatCard
          title="Villes"
          value={stats.cities}
          icon={CitiesIcon}
          onClick={() => navigate('/cities')}
          color="#CE1126"
        />
      </Box>

      {/* ACTIONS RAPIDES - ULTRA RESPONSIVE */}
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 800,
            color: '#003D66',
            mb: { xs: 1, sm: 1.5, md: 2 },
            fontSize: { xs: '0.8rem', sm: '0.95rem', md: '1.1rem' },
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
          }}
        >
          📋 Actions
        </Typography>
        <Box 
          sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
            gap: { xs: 1, sm: 1.5, md: 2 }
          }}
        >
          {/* Actions Trajets */}
          {(hasPermission('create', 'trips') || hasPermission('edit', 'trips')) && (
            <GovActionButton 
              label={hasPermission('create', 'trips') ? "➕ Trajet" : "✏️ Trajets"} 
              icon={ScheduleIcon} 
              onClick={() => navigate(hasPermission('create', 'trips') ? '/trips?action=create' : '/trips')} 
            />
          )}

          {/* Actions Tickets */}
          {(hasPermission('create', 'tickets') || hasPermission('edit', 'tickets')) && (
            <GovActionButton 
              label={hasPermission('create', 'tickets') ? "➕ Billet" : "✏️ Billets"} 
              icon={TicketsIcon} 
              onClick={() => navigate(hasPermission('create', 'tickets') ? '/tickets?action=create' : '/tickets')} 
            />
          )}

          {/* Actions Colis */}
          {(hasPermission('create', 'parcels') || hasPermission('edit', 'parcels')) && (
            <GovActionButton 
              label={hasPermission('create', 'parcels') ? "➕ Colis" : "✏️ Colis"} 
              icon={ParcelsIcon} 
              onClick={() => navigate(hasPermission('create', 'parcels') ? '/parcels?action=create' : '/parcels')} 
            />
          )}

          {/* Actions Paiements */}
          {(hasPermission('create', 'payments') || hasPermission('edit', 'payments')) && (
            <GovActionButton 
              label={hasPermission('create', 'payments') ? "➕ Paiem." : "✏️ Paiements"} 
              icon={TrendingIcon} 
              onClick={() => navigate(hasPermission('create', 'payments') ? '/payments?action=create' : '/payments')} 
            />
          )}

          {/* Actions Employés */}
          {(hasPermission('create', 'employees') || hasPermission('edit', 'employees')) && (
            <GovActionButton 
              label={hasPermission('create', 'employees') ? "➕ Emp." : "✏️ Employés"} 
              icon={EmployeesIcon} 
              onClick={() => navigate(hasPermission('create', 'employees') ? '/employees?action=create' : '/employees')} 
            />
          )}

          {/* Actions Rapports */}
          {hasPermission('create', 'reports') && (
            <GovActionButton 
              label="📊 Rapport" 
              icon={ReportsIcon} 
              onClick={() => navigate('/reports?action=create')} 
            />
          )}

          {/* Actions Gestion Utilisateurs */}
          {(hasPermission('create', 'users') || hasPermission('edit', 'users')) && (
            <GovActionButton 
              label={hasPermission('create', 'users') ? "➕ User" : "✏️ Users"} 
              icon={EmployeesIcon} 
              onClick={() => navigate(hasPermission('create', 'users') ? '/users?action=create' : '/users')} 
            />
          )}
        </Box>

        {/* Message si PAS d'actions disponibles */}
        {!hasPermission('create', 'trips') && 
         !hasPermission('edit', 'trips') && 
         !hasPermission('create', 'tickets') && 
         !hasPermission('edit', 'tickets') && 
         !hasPermission('create', 'parcels') && 
         !hasPermission('edit', 'parcels') && 
         !hasPermission('create', 'payments') && 
         !hasPermission('edit', 'payments') && 
         !hasPermission('create', 'employees') && 
         !hasPermission('edit', 'employees') && 
         !hasPermission('create', 'reports') && 
         !hasPermission('create', 'users') && 
         !hasPermission('edit', 'users') && (
          <Box 
            sx={{ 
              p: { xs: 1.5, sm: 2, md: 3 }, 
              backgroundColor: '#f0f0f0', 
              borderRadius: '8px', 
              textAlign: 'center', 
              mt: { xs: 1.5, sm: 2 }
            }}
          >
            <Typography 
              variant="body2" 
              sx={{ 
                color: '#666',
                fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
                lineHeight: 1.4,
              }}
            >
              👁️ Lecture seule
            </Typography>
          </Box>
        )}
      </Box>
    </>
  )
}
