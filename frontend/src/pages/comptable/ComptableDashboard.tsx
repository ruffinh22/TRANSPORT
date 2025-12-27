import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Container,
  Grid,
  Typography,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Tab,
  Tabs,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Alert,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Filter as FilterIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`comptable-tabpanel-${index}`}
      aria-labelledby={`comptable-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

interface Transaction {
  id: string;
  date: string;
  type: 'REVENUE' | 'EXPENSE' | 'REFUND' | 'ADJUSTMENT';
  description: string;
  amount: number;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  reference: string;
  user: string;
}

interface StatCard {
  title: string;
  value: string;
  change: number;
  color: string;
}

export const ComptableDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });
  const [openExport, setOpenExport] = useState(false);

  // Mock data
  const stats: StatCard[] = [
    {
      title: 'Revenus Totaux',
      value: '45,230.50 USD',
      change: 12.5,
      color: '#007A5E',
    },
    {
      title: 'Dépenses Totales',
      value: '12,340.75 USD',
      change: -3.2,
      color: '#CE1126',
    },
    {
      title: 'Bénéfice Net',
      value: '32,889.75 USD',
      change: 18.3,
      color: '#003D66',
    },
    {
      title: 'Transactions Pendantes',
      value: '23',
      change: -5.1,
      color: '#FFD700',
    },
  ];

  const monthlyData = [
    { month: 'Jan', revenus: 3500, depenses: 1200 },
    { month: 'Fév', revenus: 4200, depenses: 1400 },
    { month: 'Mar', revenus: 3800, depenses: 1100 },
    { month: 'Avr', revenus: 5100, depenses: 1600 },
    { month: 'Mai', revenus: 4900, depenses: 1300 },
    { month: 'Juin', revenus: 6200, depenses: 1800 },
  ];

  const categoryData = [
    { name: 'Trajets', value: 35 },
    { name: 'Livraisons', value: 40 },
    { name: 'Services', value: 15 },
    { name: 'Autres', value: 10 },
  ];

  const COLORS = ['#003D66', '#007A5E', '#CE1126', '#FFD700'];

  useEffect(() => {
    loadTransactions();
  }, [dateRange]);

  const loadTransactions = async () => {
    setLoading(true);
    setError('');
    try {
      // TODO: Remplacer par authService.getTransactions(dateRange)
      const mockTransactions: Transaction[] = [
        {
          id: '1',
          date: new Date().toISOString(),
          type: 'REVENUE',
          description: 'Paiement trajet #1234',
          amount: 250.0,
          status: 'COMPLETED',
          reference: 'TRIP-1234',
          user: 'client@example.com',
        },
        {
          id: '2',
          date: new Date(Date.now() - 86400000).toISOString(),
          type: 'EXPENSE',
          description: 'Essence véhicule',
          amount: -45.5,
          status: 'COMPLETED',
          reference: 'EXP-2024-001',
          user: 'chauffeur@example.com',
        },
      ];
      setTransactions(mockTransactions);
    } catch (err) {
      setError('Erreur lors du chargement des transactions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format: 'pdf' | 'csv' | 'excel') => {
    console.log(`Exporting as ${format}`);
    // TODO: Implémenter export
    setOpenExport(false);
  };

  const totalRevenue = transactions
    .filter((t) => t.type === 'REVENUE' && t.status === 'COMPLETED')
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpense = transactions
    .filter((t) => t.type === 'EXPENSE' && t.status === 'COMPLETED')
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#003D66' }}>
            Tableau de Bord Comptable
          </Typography>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => setOpenExport(true)}
            sx={{ borderColor: '#007A5E', color: '#007A5E' }}
          >
            Exporter
          </Button>
        </Box>
        <Divider sx={{ mt: 2 }} />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                      {stat.title}
                    </Typography>
                    <Typography variant="h5" sx={{ color: stat.color, fontWeight: 'bold' }}>
                      {stat.value}
                    </Typography>
                  </Box>
                  <Chip
                    label={`${stat.change > 0 ? '+' : ''}${stat.change}%`}
                    size="small"
                    color={stat.change > 0 ? 'success' : 'error'}
                    icon={<TrendingUpIcon />}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Tabs */}
      <Card>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          aria-label="comptable-tabs"
          sx={{
            borderBottom: '1px solid #ddd',
            '& .MuiTab-root': {
              textTransform: 'none',
              fontSize: '1rem',
            },
            '& .Mui-selected': {
              color: '#003D66',
              fontWeight: 'bold',
            },
          }}
        >
          <Tab label="Transactions" id="comptable-tab-0" />
          <Tab label="Rapports" id="comptable-tab-1" />
          <Tab label="Analystes" id="comptable-tab-2" />
        </Tabs>

        {/* Tab 0: Transactions */}
        <TabPanel value={tabValue} index={0}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Date</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Type</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Description</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }} align="right">
                      Montant
                    </TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }} align="center">
                      Statut
                    </TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Référence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactions.map((transaction) => (
                    <TableRow key={transaction.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                      <TableCell>{new Date(transaction.date).toLocaleDateString('fr-FR')}</TableCell>
                      <TableCell>
                        <Chip
                          label={transaction.type}
                          size="small"
                          color={transaction.type === 'REVENUE' ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>{transaction.description}</TableCell>
                      <TableCell
                        align="right"
                        sx={{
                          color: transaction.amount > 0 ? '#007A5E' : '#CE1126',
                          fontWeight: 'bold',
                        }}
                      >
                        {transaction.amount > 0 ? '+' : ''} {transaction.amount.toFixed(2)} USD
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={transaction.status}
                          size="small"
                          color={
                            transaction.status === 'COMPLETED'
                              ? 'success'
                              : transaction.status === 'PENDING'
                                ? 'warning'
                                : 'error'
                          }
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{transaction.reference}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Tab 1: Reports */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="Revenus vs Dépenses (Derniers 6 mois)" />
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={monthlyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="revenus" stroke="#007A5E" strokeWidth={2} />
                      <Line type="monotone" dataKey="depenses" stroke="#CE1126" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="Distribution par Catégorie" />
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {categoryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardHeader title="Rapport Mensuel Détaillé" />
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={monthlyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="revenus" fill="#007A5E" />
                      <Bar dataKey="depenses" fill="#CE1126" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 2: Analytics */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                    Résumé Financier
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
                    <Box>
                      <Typography color="textSecondary" sx={{ fontSize: '0.875rem' }}>
                        Total Revenus (période)
                      </Typography>
                      <Typography variant="h6" sx={{ color: '#007A5E', fontWeight: 'bold' }}>
                        {totalRevenue.toFixed(2)} USD
                      </Typography>
                    </Box>
                    <Box>
                      <Typography color="textSecondary" sx={{ fontSize: '0.875rem' }}>
                        Total Dépenses (période)
                      </Typography>
                      <Typography variant="h6" sx={{ color: '#CE1126', fontWeight: 'bold' }}>
                        {totalExpense.toFixed(2)} USD
                      </Typography>
                    </Box>
                    <Box>
                      <Typography color="textSecondary" sx={{ fontSize: '0.875rem' }}>
                        Bénéfice Net
                      </Typography>
                      <Typography variant="h6" sx={{ color: '#003D66', fontWeight: 'bold' }}>
                        {(totalRevenue - totalExpense).toFixed(2)} USD
                      </Typography>
                    </Box>
                    <Box>
                      <Typography color="textSecondary" sx={{ fontSize: '0.875rem' }}>
                        Marge Bénéficiaire
                      </Typography>
                      <Typography variant="h6" sx={{ color: '#007A5E', fontWeight: 'bold' }}>
                        {totalRevenue > 0 ? (((totalRevenue - totalExpense) / totalRevenue) * 100).toFixed(1) : 0}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

      {/* Export Dialog */}
      <Dialog open={openExport} onClose={() => setOpenExport(false)}>
        <DialogTitle>Exporter les données</DialogTitle>
        <DialogContent sx={{ minWidth: '400px', pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography color="textSecondary">Sélectionnez le format d'export :</Typography>
          <Button
            variant="outlined"
            onClick={() => handleExport('pdf')}
            sx={{ justifyContent: 'flex-start', color: '#CE1126' }}
          >
            📄 Exporter en PDF
          </Button>
          <Button
            variant="outlined"
            onClick={() => handleExport('csv')}
            sx={{ justifyContent: 'flex-start', color: '#007A5E' }}
          >
            📊 Exporter en CSV
          </Button>
          <Button
            variant="outlined"
            onClick={() => handleExport('excel')}
            sx={{ justifyContent: 'flex-start', color: '#003D66' }}
          >
            📈 Exporter en Excel
          </Button>
        </DialogContent>
      </Dialog>
    </Container>
  );
};

export default ComptableDashboard;
