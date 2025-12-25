import React, { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  FormControlLabel,
  Checkbox,
  MenuItem,
} from '@mui/material'
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  LocationCity as CityIcon,
  TrendingUp as TrendingIcon,
  Map as MapIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { cityService } from '../services'

interface City {
  id: number
  name: string
  code: string
  region: string
  address: string
  population: number
  latitude: number
  longitude: number
  is_hub: boolean
  has_parking: boolean
  has_terminal: boolean
  is_active: boolean
  description?: string
  trip_count?: number
  annual_revenue?: number
}

interface Statistics {
  total_cities: number
  hubs: number
  terminals: number
  total_revenue: number
  total_population: number
  average_revenue: number
}

export const CitiesPage: React.FC = () => {
  const [cities, setCities] = useState<City[]>([])
  const [stats, setStats] = useState<Statistics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selectedRegion, setSelectedRegion] = useState<string>('all')
  
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    region: '',
    address: '',
    population: 0,
    latitude: 0,
    longitude: 0,
    is_hub: false,
    has_parking: false,
    has_terminal: false,
    is_active: true,
    description: '',
  })

  const regions = [
    'Kadiogo',
    'Houet',
    'Boucle du Mouhoun',
    'Yatenga',
    'Poni',
    'Boulgou',
    'Sanmatenga',
    'Cascades',
    'Hauts-Bassins',
  ]

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [citiesRes, statsRes] = await Promise.all([
        cityService.list(),
        cityService.getStatistics(),
      ])
      
      setCities(citiesRes.data.results || citiesRes.data || [])
      setStats(statsRes.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des villes')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = (city?: City) => {
    if (city) {
      setEditingId(city.id)
      setFormData({
        name: city.name,
        code: city.code,
        region: city.region,
        address: city.address,
        population: city.population,
        latitude: city.latitude,
        longitude: city.longitude,
        is_hub: city.is_hub,
        has_parking: city.has_parking,
        has_terminal: city.has_terminal,
        is_active: city.is_active,
        description: city.description || '',
      })
    } else {
      setEditingId(null)
      setFormData({
        name: '',
        code: '',
        region: '',
        address: '',
        population: 0,
        latitude: 0,
        longitude: 0,
        is_hub: false,
        has_parking: false,
        has_terminal: false,
        is_active: true,
        description: '',
      })
    }
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingId(null)
  }

  const handleInputChange = (e: any) => {
    const { name, value, type, checked } = e.target
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseFloat(value) || 0 : value,
    })
  }

  const handleSave = async () => {
    try {
      if (editingId) {
        await cityService.update(editingId, formData)
      } else {
        await cityService.create(formData)
      }
      loadData()
      handleCloseDialog()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la sauvegarde')
    }
  }

  const handleDelete = async (id: number) => {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette ville?')) {
      try {
        await cityService.delete(id)
        loadData()
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Erreur lors de la suppression')
      }
    }
  }

  const filteredCities = selectedRegion === 'all' 
    ? cities 
    : cities.filter(c => c.region === selectedRegion)

  return (
    <MainLayout>
      <Box sx={{ mb: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <CityIcon sx={{ fontSize: 32, color: '#CE1126' }} />
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#CE1126' }}>
              Gestion des Villes
            </Typography>
          </Box>
          <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
            Gestion du réseau de villes TKF - Villes desservies et hubs de distribution
          </Typography>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Statistics Cards */}
        {stats && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>Villes totales</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, mt: 1 }}>
                    {stats.total_cities}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>Hubs majeurs</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, mt: 1 }}>
                    {stats.hubs}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>Terminaux</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, mt: 1 }}>
                    {stats.terminals}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: 'white' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>Population</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, mt: 1 }}>
                    {(stats.total_population / 1000000).toFixed(1)}M
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)', color: 'white' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>Revenu moyen</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, mt: 1 }}>
                    {(stats.average_revenue / 1000).toFixed(0)}K
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Controls */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ bgcolor: '#CE1126', '&:hover': { bgcolor: '#9B0C1F' } }}
          >
            Ajouter une ville
          </Button>
          <TextField
            select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            size="small"
            sx={{ minWidth: 200 }}
            label="Filtrer par région"
          >
            <MenuItem value="all">Toutes les régions</MenuItem>
            {regions.map(r => (
              <MenuItem key={r} value={r}>{r}</MenuItem>
            ))}
          </TextField>
          <Button
            startIcon={<MapIcon />}
            onClick={() => {/* Ouvrir carte */}}
            variant="outlined"
          >
            Voir la carte
          </Button>
        </Box>

        {/* Cities Table */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: '#CE1126' }}>
                  <TableCell sx={{ color: 'white', fontWeight: 700 }}>Ville</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700 }}>Code</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700 }}>Région</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700 }}>Population</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700 }}>Infrastructure</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700 }}>Trajets</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700 }} align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredCities.map(city => (
                  <TableRow key={city.id} hover>
                    <TableCell sx={{ fontWeight: 600 }}>{city.name}</TableCell>
                    <TableCell>
                      <Chip label={city.code} size="small" color="primary" variant="outlined" />
                    </TableCell>
                    <TableCell>{city.region}</TableCell>
                    <TableCell>{city.population?.toLocaleString()}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {city.is_hub && <Chip label="Hub" size="small" color="error" />}
                        {city.has_terminal && <Chip label="Terminal" size="small" color="success" />}
                        {city.has_parking && <Chip label="Parking" size="small" color="info" />}
                      </Box>
                    </TableCell>
                    <TableCell>{city.trip_count || 0}</TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(city)}
                        color="primary"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(city.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ bgcolor: '#CE1126', color: 'white', fontWeight: 700 }}>
          {editingId ? 'Modifier la ville' : 'Ajouter une nouvelle ville'}
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Nom"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              label="Code"
              name="code"
              value={formData.code}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              select
              label="Région"
              name="region"
              value={formData.region}
              onChange={handleInputChange}
              fullWidth
              required
            >
              {regions.map(r => (
                <MenuItem key={r} value={r}>{r}</MenuItem>
              ))}
            </TextField>
            <TextField
              label="Adresse"
              name="address"
              value={formData.address}
              onChange={handleInputChange}
              fullWidth
            />
            <TextField
              label="Population"
              name="population"
              type="number"
              value={formData.population}
              onChange={handleInputChange}
              fullWidth
            />
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Latitude"
                name="latitude"
                type="number"
                inputProps={{ step: '0.0001' }}
                value={formData.latitude}
                onChange={handleInputChange}
              />
              <TextField
                label="Longitude"
                name="longitude"
                type="number"
                inputProps={{ step: '0.0001' }}
                value={formData.longitude}
                onChange={handleInputChange}
              />
            </Box>
            <TextField
              label="Description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              fullWidth
              multiline
              rows={3}
            />
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <FormControlLabel
                control={
                  <Checkbox
                    name="is_hub"
                    checked={formData.is_hub}
                    onChange={handleInputChange}
                  />
                }
                label="Hub majeur"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="has_terminal"
                    checked={formData.has_terminal}
                    onChange={handleInputChange}
                  />
                }
                label="Terminal"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="has_parking"
                    checked={formData.has_parking}
                    onChange={handleInputChange}
                  />
                }
                label="Parking"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                  />
                }
                label="Actif"
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Annuler</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            sx={{ bgcolor: '#CE1126', '&:hover': { bgcolor: '#9B0C1F' } }}
          >
            {editingId ? 'Mettre à jour' : 'Ajouter'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  )
}

export default CitiesPage
