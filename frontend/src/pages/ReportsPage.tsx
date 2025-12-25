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
} from '@mui/material'
import {
  Assessment as ReportIcon,
  Download as DownloadIcon,
  TrendingUp as TrendingIcon,
  DateRange as DateIcon,
  Print as PrintIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { tripService, ticketService, parcelService, paymentService, employeeService, cityService } from '../services'

interface ReportData {
  title: string
  data: any
  timestamp: string
}

export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState('monthly')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [startDate, setStartDate] = useState(new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().split('T')[0])
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0])

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
        const cities = await cityService.getStatistics()
        reportData = { ...reportData, ...cities.data }
      }

      setData(reportData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement du rapport')
    } finally {
      setLoading(false)
    }
  }

  const handleExportPDF = () => {
    // Implémentation export PDF
    alert('Fonction export PDF à implémenter')
  }

  const handleExportCSV = () => {
    // Implémentation export CSV
    alert('Fonction export CSV à implémenter')
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <MainLayout>
      <Box sx={{ mb: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ReportIcon sx={{ fontSize: 32, color: '#CE1126' }} />
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#CE1126' }}>
              Rapports et Analyses
            </Typography>
          </Box>
          <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
            Tableaux de bord analytiques et rapports détaillés du portail TKF
          </Typography>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Controls */}
        <Paper sx={{ p: 3, mb: 4 }}>
          <Grid container spacing={2} alignItems="flex-end">
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                select
                label="Type de rapport"
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                fullWidth
                size="small"
              >
                {reportTypes.map(rt => (
                  <MenuItem key={rt.value} value={rt.value}>{rt.label}</MenuItem>
                ))}
              </TextField>
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
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  startIcon={<PrintIcon />}
                  onClick={handlePrint}
                  variant="outlined"
                  size="small"
                >
                  Imprimer
                </Button>
                <Button
                  startIcon={<DownloadIcon />}
                  onClick={handleExportPDF}
                  variant="outlined"
                  size="small"
                >
                  PDF
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* Report Content */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : data ? (
          <Grid container spacing={3}>
            {/* Summary Cards */}
            {reportType === 'monthly' && (
              <>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Trajets</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.trips}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Billets vendus</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.tickets}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Colis transportés</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.parcels}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Revenu</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {(data.revenue / 1000).toFixed(0)}K
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}

            {reportType === 'financial' && (
              <>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Transactions</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.totalTransactions}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Complétées</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.completedPayments}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #f5576c 0%, #f093fb 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Revenu total</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {(data.totalRevenue / 1000000).toFixed(1)}M
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #ffa726 0%, #fb8c00 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Moyenne par transaction</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.averageTransaction.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}

            {reportType === 'employees' && (
              <>
                <Grid item xs={12} sm={6}>
                  <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Employés totaux</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.totalEmployees}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Card sx={{ background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Actifs</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.activeEmployees}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12}>
                  <Paper sx={{ p: 2 }}>
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
                  <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Villes</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.total_cities}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Hubs</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.hubs}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Terminaux</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {data.terminals}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)', color: 'white' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ opacity: 0.9 }}>Revenu réseau</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, mt: 1 }}>
                        {(data.total_revenue / 1000000).toFixed(1)}M
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}

            {/* Report Footer */}
            <Grid item xs={12}>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body2" color="textSecondary">
                  📊 {data.title} | Généré le {data.timestamp}
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        ) : null}
      </Box>
    </MainLayout>
  )
}

export default ReportsPage
