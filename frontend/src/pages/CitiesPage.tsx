import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  Rating,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
  LocationOn as LocationIcon,
  Map as MapIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../hooks';

interface City {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  population: number;
  infrastructure: string;
  routes_count: number;
  trips_handled: number;
  active: boolean;
}

interface Route {
  id: number;
  origin: string;
  destination: string;
  distance_km: number;
  estimated_time_hours: number;
  base_price: number;
  status: string;
}

const CitiesPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [cities, setCities] = useState<City[]>([]);
  const [filteredCities, setFilteredCities] = useState<City[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [openRouteDialog, setOpenRouteDialog] = useState(false);
  const [editingCity, setEditingCity] = useState<City | null>(null);
  const [selectedCity, setSelectedCity] = useState<City | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    total_cities: 0,
    total_routes: 0,
    active_routes: 0,
    total_distance: 0,
  });

  const [formData, setFormData] = useState({
    name: '',
    latitude: 0,
    longitude: 0,
    population: 0,
    infrastructure: '',
  });

  const [routeFormData, setRouteFormData] = useState({
    origin: '',
    destination: '',
    distance_km: 0,
    estimated_time_hours: 0,
    base_price: 0,
  });

  // Chargement des données
  useEffect(() => {
    fetchCities();
    fetchRoutes();
  }, []);

  // Filtrage
  useEffect(() => {
    let filtered = cities;

    if (searchTerm) {
      filtered = filtered.filter((city) =>
        city.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredCities(filtered);
  }, [cities, searchTerm]);

  const fetchCities = async () => {
    try {
      setLoading(true);
      // Simuler l'appel API
      const mockCities: City[] = [
        {
          id: 1,
          name: 'Ouagadougou',
          latitude: 12.3654,
          longitude: -1.5197,
          population: 2500000,
          infrastructure: 'Gare principale, Routes goudronnées',
          routes_count: 15,
          trips_handled: 450,
          active: true,
        },
        {
          id: 2,
          name: 'Bobo-Dioulasso',
          latitude: 12.1652,
          longitude: -4.2977,
          population: 900000,
          infrastructure: 'Gare routière, Carrefour routier',
          routes_count: 12,
          trips_handled: 380,
          active: true,
        },
        {
          id: 3,
          name: 'Koudougou',
          latitude: 12.2545,
          longitude: -2.6339,
          population: 120000,
          infrastructure: 'Arrêt routier principal',
          routes_count: 8,
          trips_handled: 220,
          active: true,
        },
        {
          id: 4,
          name: 'Banfora',
          latitude: 10.6276,
          longitude: -4.7608,
          population: 80000,
          infrastructure: 'Arrêt routier, Point commerce',
          routes_count: 5,
          trips_handled: 140,
          active: true,
        },
        {
          id: 5,
          name: 'Gaoua',
          latitude: 10.3175,
          longitude: -3.1847,
          population: 45000,
          infrastructure: 'Petit arrêt routier',
          routes_count: 3,
          trips_handled: 80,
          active: true,
        },
      ];

      setCities(mockCities);

      // Calculer les stats
      const totalDistance = routes.reduce((acc, r) => acc + r.distance_km, 0);
      setStats({
        total_cities: mockCities.length,
        total_routes: routes.length,
        active_routes: routes.filter((r) => r.status === 'active').length,
        total_distance: totalDistance,
      });
    } catch (err) {
      setError('Erreur lors du chargement des villes');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRoutes = async () => {
    try {
      // Simuler l'appel API
      const mockRoutes: Route[] = [
        {
          id: 1,
          origin: 'Ouagadougou',
          destination: 'Bobo-Dioulasso',
          distance_km: 365,
          estimated_time_hours: 6,
          base_price: 15000,
          status: 'active',
        },
        {
          id: 2,
          origin: 'Ouagadougou',
          destination: 'Koudougou',
          distance_km: 160,
          estimated_time_hours: 3,
          base_price: 8000,
          status: 'active',
        },
        {
          id: 3,
          origin: 'Bobo-Dioulasso',
          destination: 'Banfora',
          distance_km: 240,
          estimated_time_hours: 4,
          base_price: 12000,
          status: 'active',
        },
        {
          id: 4,
          origin: 'Bobo-Dioulasso',
          destination: 'Gaoua',
          distance_km: 285,
          estimated_time_hours: 5,
          base_price: 14000,
          status: 'active',
        },
        {
          id: 5,
          origin: 'Koudougou',
          destination: 'Ouagadougou',
          distance_km: 160,
          estimated_time_hours: 3,
          base_price: 8000,
          status: 'active',
        },
      ];

      setRoutes(mockRoutes);
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenDialog = (city?: City) => {
    if (city) {
      setEditingCity(city);
      setFormData({
        name: city.name,
        latitude: city.latitude,
        longitude: city.longitude,
        population: city.population,
        infrastructure: city.infrastructure,
      });
    } else {
      setEditingCity(null);
      setFormData({
        name: '',
        latitude: 0,
        longitude: 0,
        population: 0,
        infrastructure: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingCity(null);
  };

  const handleOpenRouteDialog = (city: City) => {
    setSelectedCity(city);
    setRouteFormData({
      origin: city.name,
      destination: '',
      distance_km: 0,
      estimated_time_hours: 0,
      base_price: 0,
    });
    setOpenRouteDialog(true);
  };

  const handleCloseRouteDialog = () => {
    setOpenRouteDialog(false);
    setSelectedCity(null);
  };

  const handleSaveCity = async () => {
    try {
      if (editingCity) {
        // Mise à jour
        setCities(
          cities.map((city) =>
            city.id === editingCity.id
              ? { ...city, ...formData }
              : city
          )
        );
      } else {
        // Création
        const newCity: City = {
          id: Math.max(...cities.map((c) => c.id), 0) + 1,
          ...formData,
          routes_count: 0,
          trips_handled: 0,
          active: true,
        };
        setCities([...cities, newCity]);
      }
      handleCloseDialog();
    } catch (err) {
      setError('Erreur lors de la sauvegarde');
    }
  };

  const handleSaveRoute = async () => {
    try {
      const newRoute: Route = {
        id: Math.max(...routes.map((r) => r.id), 0) + 1,
        ...routeFormData,
        status: 'active',
      };
      setRoutes([...routes, newRoute]);
      handleCloseRouteDialog();
    } catch (err) {
      setError('Erreur lors de la sauvegarde de la route');
    }
  };

  const handleDeleteCity = (id: number) => {
    setCities(cities.filter((city) => city.id !== id));
  };

  const handleExportPDF = () => {
    alert('Export PDF en cours de développement...');
  };

  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    // Formule de Haversine simplifiée
    const R = 6371; // Rayon de la Terre en km
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c * 10) / 10;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold', color: '#CE1126' }}>
        ★ Gestion des Villes et Itinéraires
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Statistiques */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #A00E1A 100%)', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Villes</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.total_cities}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #007A5E 0%, #004D3A 100%)', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Routes</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.total_routes}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Distance totale</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.total_distance} km
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #FF6B6B 0%, #FF8C00 100%)', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Routes actives</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.active_routes}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Barre de filtre et actions */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              placeholder="Chercher une ville..."
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'gray' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              fullWidth
              onClick={handleExportPDF}
            >
              Exporter
            </Button>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              fullWidth
              sx={{
                background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)',
              }}
              onClick={() => handleOpenDialog()}
            >
              Ajouter Ville
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Tableau des villes */}
      <TableContainer component={Paper} sx={{ mb: 4 }}>
        <Table>
          <TableHead sx={{ backgroundColor: '#CE1126' }}>
            <TableRow>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Ville</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Localisation</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Population</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Infrastructure</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="center">
                Routes
              </TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="center">
                Trajets
              </TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="center">
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCities.map((city) => (
              <TableRow key={city.id} hover>
                <TableCell sx={{ fontWeight: 'bold' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocationIcon sx={{ color: '#CE1126' }} />
                    {city.name}
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {city.latitude.toFixed(4)}°N, {Math.abs(city.longitude).toFixed(4)}°O
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {(city.population / 1000000).toFixed(2)}M
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ color: 'gray' }}>
                    {city.infrastructure}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={city.routes_count}
                    size="small"
                    sx={{
                      background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
                    }}
                  />
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={city.trips_handled}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Voir routes">
                    <IconButton
                      size="small"
                      color="info"
                      onClick={() => handleOpenRouteDialog(city)}
                    >
                      <MapIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Modifier">
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => handleOpenDialog(city)}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Supprimer">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteCity(city.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Section Routes */}
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: '#007A5E' }}>
        📍 Itinéraires Actifs ({routes.length})
      </Typography>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead sx={{ backgroundColor: '#007A5E' }}>
            <TableRow>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Origine</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Destination</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Distance</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Temps estimé</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Prix de base</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Statut</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {routes.map((route) => (
              <TableRow key={route.id} hover>
                <TableCell>{route.origin}</TableCell>
                <TableCell>{route.destination}</TableCell>
                <TableCell>
                  <Chip label={`${route.distance_km} km`} size="small" variant="outlined" />
                </TableCell>
                <TableCell>{route.estimated_time_hours}h</TableCell>
                <TableCell sx={{ fontWeight: 'bold', color: '#CE1126' }}>
                  {route.base_price.toLocaleString()} FCFA
                </TableCell>
                <TableCell>
                  <Chip
                    label={route.status === 'active' ? 'Actif' : 'Inactif'}
                    size="small"
                    color={route.status === 'active' ? 'success' : 'default'}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog Ville */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)', color: 'white' }}>
          {editingCity ? 'Modifier Ville' : 'Ajouter une Nouvelle Ville'}
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Stack spacing={2}>
            <TextField
              fullWidth
              label="Nom de la ville"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Latitude"
              type="number"
              inputProps={{ step: '0.0001' }}
              value={formData.latitude}
              onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
            />
            <TextField
              fullWidth
              label="Longitude"
              type="number"
              inputProps={{ step: '0.0001' }}
              value={formData.longitude}
              onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
            />
            <TextField
              fullWidth
              label="Population"
              type="number"
              value={formData.population}
              onChange={(e) => setFormData({ ...formData, population: parseInt(e.target.value) })}
            />
            <TextField
              fullWidth
              label="Infrastructure"
              multiline
              rows={3}
              value={formData.infrastructure}
              onChange={(e) => setFormData({ ...formData, infrastructure: e.target.value })}
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseDialog}>Annuler</Button>
          <Button
            variant="contained"
            onClick={handleSaveCity}
            sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)' }}
          >
            Enregistrer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog Route */}
      <Dialog open={openRouteDialog} onClose={handleCloseRouteDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)', color: 'white' }}>
          Créer Itinéraire depuis {selectedCity?.name}
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Stack spacing={2}>
            <TextField
              fullWidth
              label="Ville d'origine"
              value={routeFormData.origin}
              disabled
            />
            <TextField
              fullWidth
              label="Ville de destination"
              value={routeFormData.destination}
              onChange={(e) => setRouteFormData({ ...routeFormData, destination: e.target.value })}
            />
            <TextField
              fullWidth
              label="Distance (km)"
              type="number"
              value={routeFormData.distance_km}
              onChange={(e) =>
                setRouteFormData({ ...routeFormData, distance_km: parseFloat(e.target.value) })
              }
            />
            <TextField
              fullWidth
              label="Temps estimé (heures)"
              type="number"
              inputProps={{ step: '0.5' }}
              value={routeFormData.estimated_time_hours}
              onChange={(e) =>
                setRouteFormData({ ...routeFormData, estimated_time_hours: parseFloat(e.target.value) })
              }
            />
            <TextField
              fullWidth
              label="Prix de base (FCFA)"
              type="number"
              value={routeFormData.base_price}
              onChange={(e) =>
                setRouteFormData({ ...routeFormData, base_price: parseFloat(e.target.value) })
              }
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseRouteDialog}>Annuler</Button>
          <Button
            variant="contained"
            onClick={handleSaveRoute}
            sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)' }}
          >
            Créer Route
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CitiesPage;
