import React, { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  MenuItem,
  TextField,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  Stack,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  Assessment as ReportIcon,
  Download as DownloadIcon,
  TrendingUp as TrendingIcon,
  DateRange as DateIcon,
  Print as PrintIcon,
  FileDownload as FileDownloadIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
import { tripService, ticketService, parcelService, paymentService, employeeService, cityService } from '../services'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

interface ReportData {
  title: string
  data: any
  timestamp: string
}

export const ReportsPage: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

  const [reportType, setReportType] = useState('monthly')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [startDate, setStartDate] = useState(new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().split('T')[0])
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0])

  // Mock data pour les graphiques
  const mockTripsData = [
    { day: 'Lun', trips: 45, revenue: 2250000 },
    { day: 'Mar', trips: 52, revenue: 2600000 },
    { day: 'Mer', trips: 48, revenue: 2400000 },
    { day: 'Jeu', trips: 55, revenue: 2750000 },
    { day: 'Ven', trips: 60, revenue: 3000000 },
    { day: 'Sam', trips: 72, revenue: 3600000 },
    { day: 'Dim', trips: 38, revenue: 1900000 },
  ]

  const reportTypes = [
    { value: 'monthly', label: 'Rapport mensuel' },
    { value: 'operations', label: 'Opérations de transport' },
    { value: 'financial', label: 'Rapports financiers' },
    { value: 'employees', label: 'Ressources humaines' },
    { value: 'network', label: 'Réseau et couverture' },
  ]

  useEffect(() => {
    loadReport()
  }, [reportType, startDate, endDate])

  const loadReport = async () => {
    setLoading(true)
    setError(null)
    try {
      let reportData: any = {
        title: reportTypes.find(r => r.value === reportType)?.label,
        timestamp: new Date().toLocaleString('fr-FR'),
      }

      if (reportType === 'monthly') {
        const [trips, tickets, parcels, payments] = await Promise.all([
          tripService.list({ limit: 100 }),
          ticketService.list({ limit: 100 }),
          parcelService.list({ limit: 100 }),
          paymentService.list({ limit: 100 }),
        ])

        reportData.trips = trips.data.results?.length || 0
        reportData.tickets = tickets.data.results?.length || 0
        reportData.parcels = parcels.data.results?.length || 0
        reportData.payments = payments.data.results?.length || 0
        reportData.revenue = payments.data.results?.reduce((sum: number, p: any) => sum + (p.status === 'completed' ? p.amount : 0), 0) || 0
      } else if (reportType === 'operations') {
        const [trips, cities] = await Promise.all([
          tripService.list({ limit: 100 }),
          cityService.list({ limit: 100 }),
        ])
        
        reportData.totalTrips = trips.data.results?.length || 0
        reportData.totalCities = cities.data.results?.length || 0
        reportData.activeCities = cities.data.results?.filter((c: any) => c.is_active).length || 0
        reportData.hubs = cities.data.results?.filter((c: any) => c.is_hub).length || 0
      } else if (reportType === 'financial') {
        const payments = await paymentService.list({ limit: 100 })
        const results = payments.data.results || []
        
        reportData.totalTransactions = results.length
        reportData.completedPayments = results.filter((p: any) => p.status === 'completed').length
        reportData.pendingPayments = results.filter((p: any) => p.status === 'pending').length
        reportData.totalRevenue = results.reduce((sum: number, p: any) => sum + p.amount, 0)
        reportData.averageTransaction = results.length > 0 ? reportData.totalRevenue / results.length : 0
      } else if (reportType === 'employees') {
        const employees = await employeeService.list({ limit: 100 })
        const results = employees.data.results || []
        
        reportData.totalEmployees = results.length
        reportData.activeEmployees = results.filter((e: any) => e.is_active).length
        reportData.byDepartment = {}
        results.forEach((e: any) => {
          const dept = e.department || 'Non assigné'
          reportData.byDepartment[dept] = (reportData.byDepartment[dept] || 0) + 1
        })
      } else if (reportType === 'network') {
        const cities = await cityService.list()
        const results = cities.data.results || []
        reportData.totalCities = results.length
        reportData.revenue = results.reduce((sum: number, c: any) => sum + (c.revenue || 0), 0)
      }

      setData(reportData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement du rapport')
    } finally {
      setLoading(false)
    }
  }

  const handleExportPDF = () => {
    alert('Export PDF en cours...')
  }

  const handleExportCSV = () => {
    alert('Export CSV en cours...')
  }

  const handleExportExcel = () => {
    alert('Export Excel en cours...')
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <MainLayout hideGovernmentHeader={true}>
      <GovPageWrapper maxWidth="xl">
        <GovPageHeader
          title="Rapports et Statistiques"
          icon="📊"
          subtitle="Génération et analyse complète des rapports TKF"
          actions={[
            {
              label: 'Imprimer',
              icon: <PrintIcon />,
              onClick: handlePrint,
              variant: 'secondary',
            },
          ]}
        />

        {error && <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>{error}</Alert>}

        {/* Filtres et Export - ULTRA RESPONSIVE */}
        <Paper sx={{ p: { xs: 1.5, sm: 2, md: 2 }, mb: { xs: 2, sm: 3, md: 4 }, ...govStyles.contentCard }}>
          <Grid container spacing={{ xs: 1.5, sm: 2, md: 2 }} alignItems={{ xs: 'stretch', sm: 'stretch', md: 'flex-end' }}>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel htmlFor="report-type-select" sx={{ fontSize: { xs: '0.85rem', sm: '0.9rem', md: '1rem' } }}>Type de rapport</InputLabel>
                <Select
                  id="report-type-select"
                  label="Type de rapport"
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  sx={{ fontSize: { xs: '0.85rem', sm: '0.9rem', md: '1rem' } }}
                >
                  {reportTypes.map(rt => (
                    <MenuItem key={rt.value} value={rt.value}>{rt.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                type="date"
                label="Date début"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                sx={{ '& .MuiOutlinedInput-root': { fontSize: { xs: '0.85rem', sm: '0.9rem', md: '1rem' } } }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                type="date"
                label="Date fin"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                sx={{ '& .MuiOutlinedInput-root': { fontSize: { xs: '0.85rem', sm: '0.9rem', md: '1rem' } } }}
              />
            </Grid>
            <Grid item xs={12} sm={12} md={3}>
              <Stack direction={{ xs: 'row', md: 'row' }} spacing={{ xs: 0.5, md: 1 }} sx={{ width: '100%' }}>
                <Button
                  startIcon={<FileDownloadIcon />}
                  onClick={handleExportPDF}
                  variant="contained"
                  size="small"
                  fullWidth
                  sx={{
                    backgroundColor: govStyles.colors.danger,
                    fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.85rem' },
                    py: { xs: 0.75, md: 1 },
                    '&:hover': { backgroundColor: '#a00d20' },
                  }}
                >
                  PDF
                </Button>
                <Button
                  startIcon={<FileDownloadIcon />}
                  onClick={handleExportExcel}
                  variant="contained"
                  size="small"
                  fullWidth
                  sx={{
                    backgroundColor: govStyles.colors.success,
                    fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.85rem' },
                    py: { xs: 0.75, md: 1 },
                    '&:hover': { backgroundColor: '#005c45' },
                  }}
                >
                  Excel
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </Paper>

        {/* Graphiques - RESPONSIVE */}
        {reportType === 'monthly' && (
          <Grid container spacing={{ xs: 1.5, sm: 2, md: 3 }} sx={{ mb: 4 }}>
            <Grid item xs={12} md={8}>
              <Card sx={govStyles.contentCard}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, color: govStyles.colors.primary, fontSize: { xs: '0.95rem', sm: '1.1rem', md: '1.25rem' } }}>
                    📈 Trajets et Revenus (Hebdomadaire)
                  </Typography>
                  <ResponsiveContainer width="100%" height={{ xs: 250, sm: 280, md: 300 }}>
                    <BarChart data={mockTripsData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" tick={{ fontSize: { xs: 10, sm: 12, md: 14 } }} />
                      <YAxis yAxisId="left" tick={{ fontSize: { xs: 10, sm: 12, md: 14 } }} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fontSize: { xs: 10, sm: 12, md: 14 } }} />
                      <Tooltip formatter={(value: any) => value.toLocaleString('fr-FR')} />
                      <Legend wrapperStyle={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '1rem' } }} />
                      <Bar yAxisId="left" dataKey="trips" fill={govStyles.colors.primary} name="Trajets" />
                      <Bar yAxisId="right" dataKey="revenue" fill={govStyles.colors.success} name="Revenus (CFA)" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Grid container spacing={{ xs: 1, sm: 1.5, md: 2 }}>
                <Grid item xs={12}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.primary}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important', p: { xs: 1.5, sm: 2, md: 2 } }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}>
                        Trajets
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.primary, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                        1,420
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.success}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important', p: { xs: 1.5, sm: 2, md: 2 } }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}>
                        Billets
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.success, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                        3,250
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.warning}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important', p: { xs: 1.5, sm: 2, md: 2 } }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}>
                        Colis
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.warning, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                        4,100
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        )}

        {/* Report Content */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress sx={{ color: govStyles.colors.primary }} />
          </Box>
        ) : data ? (
          <Grid container spacing={3}>
            {/* Summary Cards */}
            {reportType === 'monthly' && (
              <>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.primary}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Trajets
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.primary }}>
                        {data.trips}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.success}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Billets vendus
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.success }}>
                        {data.tickets}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.warning}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Colis transportés
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.warning }}>
                        {data.parcels}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.danger}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Revenu
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.danger }}>
                        {(data.revenue / 1000000).toFixed(1)}M
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}

            {reportType === 'financial' && (
              <>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.primary}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Transactions
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.primary }}>
                        {data.totalTransactions}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.success}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Complétées
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.success }}>
                        {data.completedPayments}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.warning}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        En attente
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.warning }}>
                        {data.pendingPayments}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.danger}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Revenu total
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.danger }}>
                        {(data.totalRevenue / 1000000).toFixed(1)}M
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}

            {reportType === 'employees' && (
              <>
                <Grid item xs={12} sm={6}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.primary}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Employés totaux
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.primary }}>
                        {data.totalEmployees}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.success}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Actifs
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.success }}>
                        {data.activeEmployees}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12}>
                  <Paper sx={{ p: 2, ...govStyles.contentCard }}>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                      Répartition par département
                    </Typography>
                    <List>
                      {Object.entries(data.byDepartment || {}).map(([dept, count]: any) => (
                        <ListItem key={dept}>
                          <ListItemText
                            primary={dept}
                            secondary={`${count} employé${count > 1 ? 's' : ''}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Grid>
              </>
            )}

            {reportType === 'network' && (
              <>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.success}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Villes
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.success }}>
                        {data.totalCities}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ borderLeft: `5px solid ${govStyles.colors.warning}`, ...govStyles.contentCard }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                        Couverture
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.warning }}>
                        100%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}

            {/* Report Footer */}
            <Grid item xs={12}>
              <Paper sx={{ p: 2, ...govStyles.contentCard, backgroundColor: '#f5f5f5' }}>
                <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
                  📊 {data.title} | Généré le {data.timestamp}
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        ) : null}

        <GovPageFooter text="Système de Gestion du Transport - Rapports et Statistiques" />
      </GovPageWrapper>
    </MainLayout>
  )
}

export default ReportsPage
