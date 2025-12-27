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
  Button,
  Chip,
  Tab,
  Tabs,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
} from '@mui/material';
import {
  Navigation as NavigationIcon,
  DirectionsCar as CarIcon,
  Assignment as AssignmentIcon,
  AttachMoney as MoneyIcon,
  CheckCircle as CompleteIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

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
      id={`chauffeur-tabpanel-${index}`}
      aria-labelledby={`chauffeur-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

interface Trip {
  id: string;
  tripNumber: string;
  origin: string;
  destination: string;
  distance: number;
  estimatedTime: number;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  startTime?: string;
  endTime?: string;
  earnings: number;
  clientName: string;
  clientPhone: string;
}

interface Vehicle {
  id: string;
  registrationNumber: string;
  model: string;
  status: 'AVAILABLE' | 'IN_USE' | 'MAINTENANCE';
  fuelLevel: number;
  mileage: number;
  lastMaintenance: string;
}

interface StatCard {
  title: string;
  value: string;
  color: string;
  icon: React.ReactNode;
}

export const ChauffeurDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openTripDialog, setOpenTripDialog] = useState(false);
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null);

  // Mock data
  const stats: StatCard[] = [
    {
      title: 'Trajets Effectués',
      value: '24',
      color: '#007A5E',
      icon: <CompleteIcon sx={{ fontSize: 32 }} />,
    },
    {
      title: 'Revenus Aujourd\'hui',
      value: '45,230 XAF',
      color: '#003D66',
      icon: <MoneyIcon sx={{ fontSize: 32 }} />,
    },
    {
      title: 'Trajets en Attente',
      value: '3',
      color: '#FFD700',
      icon: <AssignmentIcon sx={{ fontSize: 32 }} />,
    },
    {
      title: 'Véhicule',
      value: 'CM-1234-AB',
      color: '#CE1126',
      icon: <CarIcon sx={{ fontSize: 32 }} />,
    },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      // Mock trips data
      const mockTrips: Trip[] = [
        {
          id: '1',
          tripNumber: 'TRIP-2024-001',
          origin: 'Yaoundé Centre',
          destination: 'Aéroport International',
          distance: 22.5,
          estimatedTime: 45,
          status: 'IN_PROGRESS',
          startTime: new Date().toISOString(),
          earnings: 15000,
          clientName: 'Mr. Kameni',
          clientPhone: '+237123456789',
        },
        {
          id: '2',
          tripNumber: 'TRIP-2024-002',
          origin: 'Douala Port',
          destination: 'Hôtel Hilton',
          distance: 18.0,
          estimatedTime: 35,
          status: 'COMPLETED',
          startTime: new Date(Date.now() - 7200000).toISOString(),
          endTime: new Date(Date.now() - 5400000).toISOString(),
          earnings: 12000,
          clientName: 'Mme. Assoumou',
          clientPhone: '+237987654321',
        },
        {
          id: '3',
          tripNumber: 'TRIP-2024-003',
          origin: 'Yaoundé Gare',
          destination: 'Yaoundé Aéroport',
          distance: 25.0,
          estimatedTime: 50,
          status: 'PENDING',
          earnings: 18000,
          clientName: 'Mr. Akono',
          clientPhone: '+237111222333',
        },
      ];

      const mockVehicle: Vehicle = {
        id: '1',
        registrationNumber: 'CM-1234-AB',
        model: 'Toyota Hiace 2023',
        status: 'IN_USE',
        fuelLevel: 65,
        mileage: 45230,
        lastMaintenance: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      };

      setTrips(mockTrips);
      setVehicle(mockVehicle);
    } catch (err) {
      setError('Erreur lors du chargement des données');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTrip = (trip: Trip) => {
    console.log('Starting trip:', trip.id);
    // TODO: Implement API call
  };

  const handleCompleteTrip = (trip: Trip) => {
    console.log('Completing trip:', trip.id);
    // TODO: Implement API call
  };

  const handleCancelTrip = (trip: Trip) => {
    console.log('Cancelling trip:', trip.id);
    // TODO: Implement API call
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return '#FFD700';
      case 'IN_PROGRESS':
        return '#007A5E';
      case 'COMPLETED':
        return '#003D66';
      case 'CANCELLED':
        return '#CE1126';
      default:
        return '#666';
    }
  };

  const getTotalEarnings = () => {
    return trips
      .filter((t) => t.status === 'COMPLETED')
      .reduce((sum, t) => sum + t.earnings, 0);
  };

  const getTotalDistance = () => {
    return trips
      .filter((t) => t.status === 'COMPLETED')
      .reduce((sum, t) => sum + t.distance, 0);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#003D66', mb: 2 }}>
          Tableau de Bord Chauffeur
        </Typography>
        <Divider />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Vehicle Status Alert */}
      {vehicle && (
        <Alert
          severity={vehicle.status === 'IN_USE' ? 'success' : 'warning'}
          icon={<CarIcon />}
          sx={{ mb: 3 }}
        >
          Véhicule: <strong>{vehicle.registrationNumber}</strong> - Carburant:{' '}
          <strong>{vehicle.fuelLevel}%</strong> - Kilométrage: <strong>{vehicle.mileage} km</strong>
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                      {stat.title}
                    </Typography>
                    <Typography variant="h5" sx={{ color: stat.color, fontWeight: 'bold' }}>
                      {stat.value}
                    </Typography>
                  </Box>
                  <Box sx={{ color: stat.color, opacity: 0.6 }}>{stat.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Fuel Level Progress */}
      {vehicle && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                Niveau de Carburant
              </Typography>
              <Typography sx={{ color: vehicle.fuelLevel > 50 ? '#007A5E' : '#CE1126', fontWeight: 'bold' }}>
                {vehicle.fuelLevel}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={vehicle.fuelLevel}
              sx={{
                height: 8,
                backgroundColor: '#ddd',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: vehicle.fuelLevel > 50 ? '#007A5E' : '#FFD700',
                },
              }}
            />
            {vehicle.fuelLevel < 25 && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                ⚠️ Niveau de carburant faible. Envisagez un ravitaillement.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Card>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          aria-label="chauffeur-tabs"
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
          <Tab label="Trajets Actifs" id="chauffeur-tab-0" />
          <Tab label="Historique" id="chauffeur-tab-1" />
          <Tab label="Revenus" id="chauffeur-tab-2" />
          <Tab label="Véhicule" id="chauffeur-tab-3" />
        </Tabs>

        {/* Tab 0: Active Trips */}
        <TabPanel value={tabValue} index={0}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3}>
              {trips
                .filter((t) => t.status === 'PENDING' || t.status === 'IN_PROGRESS')
                .map((trip) => (
                  <Grid item xs={12} key={trip.id}>
                    <Card sx={{ borderLeft: `4px solid ${getStatusColor(trip.status)}` }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Box>
                            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                              {trip.tripNumber}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                              <Box>
                                <Typography sx={{ fontSize: '0.875rem', color: 'textSecondary' }}>
                                  Origine
                                </Typography>
                                <Typography sx={{ fontWeight: '500' }}>{trip.origin}</Typography>
                              </Box>
                              <Box>
                                <Typography sx={{ fontSize: '0.875rem', color: 'textSecondary' }}>
                                  Destination
                                </Typography>
                                <Typography sx={{ fontWeight: '500' }}>{trip.destination}</Typography>
                              </Box>
                              <Box>
                                <Typography sx={{ fontSize: '0.875rem', color: 'textSecondary' }}>
                                  Distance
                                </Typography>
                                <Typography sx={{ fontWeight: '500' }}>{trip.distance} km</Typography>
                              </Box>
                              <Box>
                                <Typography sx={{ fontSize: '0.875rem', color: 'textSecondary' }}>
                                  Temps Estimé
                                </Typography>
                                <Typography sx={{ fontWeight: '500' }}>{trip.estimatedTime} min</Typography>
                              </Box>
                            </Box>

                            <Divider sx={{ my: 2 }} />

                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                              Informations Client
                            </Typography>
                            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                              <Typography sx={{ fontSize: '0.875rem' }}>
                                👤 <strong>{trip.clientName}</strong>
                              </Typography>
                              <Typography sx={{ fontSize: '0.875rem' }}>
                                📱 {trip.clientPhone}
                              </Typography>
                            </Box>
                          </Box>

                          <Box sx={{ textAlign: 'right' }}>
                            <Chip
                              label={trip.status === 'PENDING' ? 'En Attente' : 'En Cours'}
                              sx={{
                                backgroundColor: getStatusColor(trip.status),
                                color: trip.status === 'PENDING' ? 'black' : 'white',
                                fontWeight: 'bold',
                                mb: 2,
                              }}
                            />
                            <Typography variant="h6" sx={{ color: '#007A5E', fontWeight: 'bold' }}>
                              {trip.earnings.toLocaleString('fr-FR')} XAF
                            </Typography>
                          </Box>
                        </Box>

                        <Divider sx={{ my: 2 }} />

                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          {trip.status === 'PENDING' && (
                            <Button
                              variant="contained"
                              startIcon={<NavigationIcon />}
                              onClick={() => handleStartTrip(trip)}
                              sx={{
                                backgroundColor: '#007A5E',
                                '&:hover': { backgroundColor: '#005c47' },
                              }}
                            >
                              Démarrer Trajet
                            </Button>
                          )}
                          {trip.status === 'IN_PROGRESS' && (
                            <Button
                              variant="contained"
                              startIcon={<CompleteIcon />}
                              onClick={() => handleCompleteTrip(trip)}
                              sx={{
                                backgroundColor: '#007A5E',
                                '&:hover': { backgroundColor: '#005c47' },
                              }}
                            >
                              Marquer Complété
                            </Button>
                          )}
                          <Button
                            variant="outlined"
                            startIcon={<CancelIcon />}
                            onClick={() => handleCancelTrip(trip)}
                            sx={{ borderColor: '#CE1126', color: '#CE1126' }}
                          >
                            Annuler
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
            </Grid>
          )}
        </TabPanel>

        {/* Tab 1: History */}
        <TabPanel value={tabValue} index={1}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Numéro Trajet</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Trajet</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }} align="right">
                      Distance
                    </TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }} align="right">
                      Revenus
                    </TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Date</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }} align="center">
                      Statut
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trips
                    .filter((t) => t.status === 'COMPLETED' || t.status === 'CANCELLED')
                    .map((trip) => (
                      <TableRow key={trip.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                        <TableCell>{trip.tripNumber}</TableCell>
                        <TableCell>
                          {trip.origin} → {trip.destination}
                        </TableCell>
                        <TableCell align="right">{trip.distance} km</TableCell>
                        <TableCell align="right" sx={{ color: '#007A5E', fontWeight: 'bold' }}>
                          {trip.earnings.toLocaleString('fr-FR')} XAF
                        </TableCell>
                        <TableCell>{new Date(trip.startTime || '').toLocaleDateString('fr-FR')}</TableCell>
                        <TableCell align="center">
                          <Chip
                            label={trip.status === 'COMPLETED' ? 'Complété' : 'Annulé'}
                            color={trip.status === 'COMPLETED' ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Tab 2: Earnings */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                    Revenus Totaux
                  </Typography>
                  <Typography variant="h4" sx={{ color: '#007A5E', fontWeight: 'bold' }}>
                    {getTotalEarnings().toLocaleString('fr-FR')} XAF
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                    Distance Totale Parcourue
                  </Typography>
                  <Typography variant="h4" sx={{ color: '#003D66', fontWeight: 'bold' }}>
                    {getTotalDistance().toFixed(1)} km
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                    Revenu Moyen par Trajet
                  </Typography>
                  <Typography variant="h5" sx={{ color: '#007A5E', fontWeight: 'bold' }}>
                    {trips.length > 0
                      ? (getTotalEarnings() / trips.filter((t) => t.status === 'COMPLETED').length).toLocaleString('fr-FR')
                      : 0}{' '}
                    XAF
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 3: Vehicle */}
        <TabPanel value={tabValue} index={3}>
          {vehicle ? (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardHeader
                    title={`${vehicle.model} (${vehicle.registrationNumber})`}
                    sx={{ backgroundColor: '#f5f5f5' }}
                  />
                  <CardContent>
                    <Grid container spacing={3}>
                      <Grid item xs={12} sm={6} md={3}>
                        <Box>
                          <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                            Statut
                          </Typography>
                          <Chip
                            label={vehicle.status}
                            color={vehicle.status === 'AVAILABLE' ? 'success' : 'warning'}
                          />
                        </Box>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Box>
                          <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                            Kilométrage
                          </Typography>
                          <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#003D66' }}>
                            {vehicle.mileage} km
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Box>
                          <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                            Carburant
                          </Typography>
                          <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#007A5E' }}>
                            {vehicle.fuelLevel}%
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Box>
                          <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                            Dernier Entretien
                          </Typography>
                          <Typography sx={{ fontSize: '0.9rem' }}>
                            {new Date(vehicle.lastMaintenance).toLocaleDateString('fr-FR')}
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Alert icon={<InfoIcon />} severity="info">
                  💡 Assurez-vous que votre véhicule est en bon état avant de prendre des trajets. Signalez tout
                  problème au responsable.
                </Alert>
              </Grid>
            </Grid>
          ) : (
            <CircularProgress />
          )}
        </TabPanel>
      </Card>
    </Container>
  );
};

export default ChauffeurDashboard;
