import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Chip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  Container,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
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
  const [error, setError] = useState<string | null>(null)

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
      setTrips(response.data.results || response.data || [])
      setError(null)
    } catch (err) {
      setError('Erreur au chargement des trajets')
      console.error(err)
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

  const handleSave = async () => {
    try {
      if (editingId) {
        await tripService.update(editingId, formData)
      } else {
        await tripService.create(formData)
      }
      await loadTrips()
      setOpenDialog(false)
    } catch (err) {
      setError('Erreur lors de la sauvegarde')
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await tripService.delete(id)
        await loadTrips()
      } catch (err) {
        setError('Erreur lors de la suppression')
      }
    }
  }

  const filteredTrips = trips.filter(
    (trip) =>
      trip.departure_city.toLowerCase().includes(search.toLowerCase()) ||
      trip.arrival_city.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <GovPageWrapper maxWidth="lg">
        <GovPageHeader
          title="Gestion des Trajets"
          icon="🚌"
          subtitle="Consultez et gérez l'ensemble de vos trajets"
          actions={[
            {
              label: 'Nouveau Trajet',
              icon: <AddIcon />,
              onClick: () => handleOpenDialog(),
              variant: 'primary',
            },
          ]}
        />

        {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

        {/* Filtres */}
        <Paper sx={{ p: 2, mb: 3, ...govStyles.contentCard }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="Rechercher (ville)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              variant="outlined"
              size="small"
              fullWidth
              sx={{ maxWidth: { md: '300px' } }}
            />
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Statut</InputLabel>
              <Select
                label="Statut"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="all">Tous</option>
                <option value="scheduled">Planifié</option>
                <option value="ongoing">En cours</option>
                <option value="completed">Terminé</option>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              onClick={() => {
                setSearch('')
                setFilterStatus('all')
                loadTrips()
              }}
              sx={govStyles.govButton.secondary}
            >
              Réinitialiser
            </Button>
          </Stack>
        </Paper>

        {/* Table */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
            <CircularProgress sx={{ color: govStyles.colors.primary }} />
          </Box>
        ) : (
          <TableContainer component={Paper} sx={govStyles.contentCard}>
            <Table sx={govStyles.table}>
              <TableHead>
                <TableRow sx={{ backgroundColor: govStyles.colors.primary }}>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Départ</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Arrivée</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Date Départ</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Sièges</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Dispo</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTrips.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 4, color: '#999' }}>
                      Aucun trajet trouvé
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTrips.map((trip) => (
                    <TableRow key={trip.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                      <TableCell>{trip.departure_city}</TableCell>
                      <TableCell>{trip.arrival_city}</TableCell>
                      <TableCell>{new Date(trip.departure_date).toLocaleDateString('fr-FR')}</TableCell>
                      <TableCell align="center">{trip.total_seats}</TableCell>
                      <TableCell align="center">
                        <Chip
                          label={trip.available_seats}
                          color={trip.available_seats === 0 ? 'error' : trip.available_seats < 5 ? 'warning' : 'success'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={trip.status === 'scheduled' ? 'Planifié' : trip.status === 'ongoing' ? 'En cours' : 'Terminé'}
                          color={trip.status === 'scheduled' ? 'primary' : trip.status === 'ongoing' ? 'warning' : 'success'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} justifyContent="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleOpenDialog(trip)}
                            sx={{ color: govStyles.colors.primary }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(trip.id)}
                            sx={{ color: govStyles.colors.danger }}
                          >
                            🗑️
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {/* Dialog Form */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle sx={{ backgroundColor: govStyles.colors.primary, color: 'white', fontWeight: 700 }}>
            {editingId ? '✏️ Éditer le trajet' : '➕ Nouveau trajet'}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Stack spacing={2}>
              <TextField
                label="Ville de départ"
                fullWidth
                value={formData.departure_city}
                onChange={(e) => setFormData({ ...formData, departure_city: e.target.value })}
                variant="outlined"
              />
              <TextField
                label="Ville d'arrivée"
                fullWidth
                value={formData.arrival_city}
                onChange={(e) => setFormData({ ...formData, arrival_city: e.target.value })}
                variant="outlined"
              />
              <TextField
                label="Date de départ"
                type="datetime-local"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={formData.departure_date}
                onChange={(e) => setFormData({ ...formData, departure_date: e.target.value })}
              />
              <TextField
                label="Date d'arrivée"
                type="datetime-local"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={formData.arrival_date}
                onChange={(e) => setFormData({ ...formData, arrival_date: e.target.value })}
              />
              <TextField
                label="Nombre de sièges"
                type="number"
                fullWidth
                value={formData.total_seats}
                onChange={(e) => setFormData({ ...formData, total_seats: parseInt(e.target.value) })}
              />
              <TextField
                label="Prix par siège (FCFA)"
                type="number"
                fullWidth
                value={formData.price_per_seat}
                onChange={(e) => setFormData({ ...formData, price_per_seat: parseInt(e.target.value) })}
              />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: 2, gap: 1 }}>
            <Button onClick={() => setOpenDialog(false)} sx={govStyles.govButton.secondary}>
              Annuler
            </Button>
            <Button variant="contained" onClick={handleSave} sx={govStyles.govButton.primary}>
              Sauvegarder
            </Button>
          </DialogActions>
        </Dialog>

        <GovPageFooter text="Système de Gestion du Transport - Gestion des Trajets" />
      </GovPageWrapper>
    </MainLayout>
  )
}
