import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Chip,
  Stack,
  Grid,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { tripService } from '../services'

interface Trip {
  id: number
  departure_city: string
  arrival_city: string
  departure_date: string
  arrival_date: string
  total_seats: number
  available_seats: number
  price_per_seat: number
  status: string
  vehicle: number
  driver: number
  created_at: string
}

export const TripsPage: React.FC = () => {
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  
  const [formData, setFormData] = useState({
    departure_city: '',
    arrival_city: '',
    departure_date: '',
    arrival_date: '',
    total_seats: 45,
    price_per_seat: 5000,
    status: 'scheduled',
    vehicle: 1,
    driver: 1,
  })

  useEffect(() => {
    loadTrips()
  }, [filterStatus])

  const loadTrips = async () => {
    setLoading(true)
    try {
      const params = filterStatus !== 'all' ? { status: filterStatus } : {}
      const response = await tripService.list(params)
      setTrips(response.data.results || response.data)
    } catch (error) {
      console.error('Erreur au chargement des trajets:', error)
    }
    setLoading(false)
  }

  const handleOpenDialog = (trip?: Trip) => {
    if (trip) {
      setEditingId(trip.id)
      setFormData({
        departure_city: trip.departure_city,
        arrival_city: trip.arrival_city,
        departure_date: trip.departure_date,
        arrival_date: trip.arrival_date,
        total_seats: trip.total_seats,
        price_per_seat: trip.price_per_seat,
        status: trip.status,
        vehicle: trip.vehicle,
        driver: trip.driver,
      })
    } else {
      setEditingId(null)
      setFormData({
        departure_city: '',
        arrival_city: '',
        departure_date: '',
        arrival_date: '',
        total_seats: 45,
        price_per_seat: 5000,
        status: 'scheduled',
        vehicle: 1,
        driver: 1,
      })
    }
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingId(null)
  }

  const handleSaveTrip = async () => {
    try {
      if (editingId) {
        await tripService.update(editingId, formData)
      } else {
        await tripService.create(formData)
      }
      handleCloseDialog()
      loadTrips()
    } catch (error) {
      console.error('Erreur:', error)
    }
  }

  const handleDeleteTrip = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await tripService.delete(id)
        loadTrips()
      } catch (error) {
        console.error('Erreur:', error)
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'info'
      case 'completed': return 'success'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  const filteredTrips = trips.filter(trip =>
    trip.departure_city.toLowerCase().includes(search.toLowerCase()) ||
    trip.arrival_city.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
          Gestion des Trajets
        </Typography>

        {/* Stats Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Total trajets
                </Typography>
                <Typography variant="h4">{trips.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Programmés
                </Typography>
                <Typography variant="h4">
                  {trips.filter(t => t.status === 'scheduled').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Terminés
                </Typography>
                <Typography variant="h4">
                  {trips.filter(t => t.status === 'completed').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Places disponibles
                </Typography>
                <Typography variant="h4">
                  {trips.reduce((sum, t) => sum + t.available_seats, 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters and Search */}
        <Card sx={{ mb: 3, p: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              label="Rechercher (ville de départ/arrivée)"
              variant="outlined"
              size="small"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ flex: 1 }}
            />
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Statut</InputLabel>
              <Select
                value={filterStatus}
                label="Statut"
                onChange={(e) => setFilterStatus(e.target.value)}
                size="small"
              >
                <option value="all">Tous</option>
                <option value="scheduled">Programmés</option>
                <option value="completed">Terminés</option>
                <option value="cancelled">Annulés</option>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              }}
            >
              Ajouter trajet
            </Button>
          </Stack>
        </Card>

        {/* Trips Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead sx={{ backgroundColor: '#f5f6fa' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>De / Vers</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Date départ</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Places</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Prix/place</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Statut</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredTrips.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography color="textSecondary">
                      Aucun trajet trouvé
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredTrips.map((trip) => (
                  <TableRow key={trip.id} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {trip.departure_city} → {trip.arrival_city}
                      </Typography>
                    </TableCell>
                    <TableCell>{new Date(trip.departure_date).toLocaleDateString('fr-FR')}</TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${trip.available_seats}/${trip.total_seats}`}
                        size="small"
                        variant={trip.available_seats === 0 ? 'filled' : 'outlined'}
                        color={trip.available_seats === 0 ? 'error' : 'success'}
                      />
                    </TableCell>
                    <TableCell align="right">{trip.price_per_seat} CFA</TableCell>
                    <TableCell>
                      <Chip
                        label={trip.status}
                        size="small"
                        color={getStatusColor(trip.status) as any}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={1} justifyContent="center">
                        <Button
                          size="small"
                          startIcon={<ViewIcon />}
                          onClick={() => console.log('View', trip.id)}
                        >
                          Voir
                        </Button>
                        <Button
                          size="small"
                          startIcon={<EditIcon />}
                          onClick={() => handleOpenDialog(trip)}
                        >
                          Éditer
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          startIcon={<DeleteIcon />}
                          onClick={() => handleDeleteTrip(trip.id)}
                        >
                          Supprimer
                        </Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          {editingId ? 'Éditer trajet' : 'Ajouter un trajet'}
        </DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            label="Ville de départ"
            variant="outlined"
            value={formData.departure_city}
            onChange={(e) => setFormData({ ...formData, departure_city: e.target.value })}
            fullWidth
          />
          <TextField
            label="Ville d'arrivée"
            variant="outlined"
            value={formData.arrival_city}
            onChange={(e) => setFormData({ ...formData, arrival_city: e.target.value })}
            fullWidth
          />
          <TextField
            label="Date départ"
            type="datetime-local"
            variant="outlined"
            value={formData.departure_date}
            onChange={(e) => setFormData({ ...formData, departure_date: e.target.value })}
            fullWidth
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Date arrivée"
            type="datetime-local"
            variant="outlined"
            value={formData.arrival_date}
            onChange={(e) => setFormData({ ...formData, arrival_date: e.target.value })}
            fullWidth
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Nombre de places"
            type="number"
            variant="outlined"
            value={formData.total_seats}
            onChange={(e) => setFormData({ ...formData, total_seats: parseInt(e.target.value) })}
            fullWidth
          />
          <TextField
            label="Prix par place"
            type="number"
            variant="outlined"
            value={formData.price_per_seat}
            onChange={(e) => setFormData({ ...formData, price_per_seat: parseInt(e.target.value) })}
            fullWidth
          />
          <FormControl fullWidth>
            <InputLabel>Statut</InputLabel>
            <Select
              value={formData.status}
              label="Statut"
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            >
              <option value="scheduled">Programmé</option>
              <option value="completed">Terminé</option>
              <option value="cancelled">Annulé</option>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Annuler</Button>
          <Button onClick={handleSaveTrip} variant="contained">
            {editingId ? 'Mettre à jour' : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  )
}
