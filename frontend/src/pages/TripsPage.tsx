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
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { ResponsivePageTemplate, ResponsiveTable, ResponsiveFilters } from '../components'
import { responsiveStyles } from '../styles/responsiveStyles'
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
      <ResponsivePageTemplate
        title="Gestion des Trajets"
        subtitle="Consultez et gérez l'ensemble de vos trajets"
        actions={[
          <Button
            key="add"
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Nouveau Trajet
          </Button>,
        ]}
      >
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <ResponsiveFilters
          fields={[
            { name: 'search', label: 'Recherche', value: search, onChange: setSearch },
            {
              name: 'status',
              label: 'Statut',
              value: filterStatus,
              onChange: setFilterStatus,
              options: [
                { label: 'Tous', value: 'all' },
                { label: 'Planifié', value: 'scheduled' },
                { label: 'En cours', value: 'ongoing' },
                { label: 'Terminé', value: 'completed' },
              ],
            },
          ]}
          onApply={() => loadTrips()}
          onReset={() => {
            setSearch('')
            setFilterStatus('all')
          }}
        />

        {loading ? (
          <Box sx={responsiveStyles.flexCenter}>
            <CircularProgress />
          </Box>
        ) : (
          <ResponsiveTable
            columns={[
              { key: 'departure_city', label: 'Départ' },
              { key: 'arrival_city', label: 'Arrivée' },
              { key: 'departure_date', label: 'Date départ' },
              { key: 'total_seats', label: 'Sièges' },
              { key: 'available_seats', label: 'Disponibles' },
              {
                key: 'status',
                label: 'Statut',
                render: (val) => (
                  <Chip
                    label={val}
                    color={val === 'scheduled' ? 'primary' : val === 'ongoing' ? 'warning' : 'success'}
                    size="small"
                  />
                ),
              },
              {
                key: 'actions',
                label: 'Actions',
                render: (_, row) => (
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      variant="text"
                      onClick={() => handleOpenDialog(row)}
                    >
                      ✏️
                    </Button>
                    <Button
                      size="small"
                      variant="text"
                      color="error"
                      onClick={() => handleDelete(row.id)}
                    >
                      🗑️
                    </Button>
                  </Stack>
                ),
              },
            ]}
            data={filteredTrips}
            emptyMessage="Aucun trajet trouvé"
          />
        )}

        {/* Dialog Form */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>{editingId ? 'Éditer le trajet' : 'Nouveau trajet'}</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <Stack spacing={2}>
              <TextField
                label="Ville de départ"
                fullWidth
                value={formData.departure_city}
                onChange={(e) => setFormData({ ...formData, departure_city: e.target.value })}
              />
              <TextField
                label="Ville d'arrivée"
                fullWidth
                value={formData.arrival_city}
                onChange={(e) => setFormData({ ...formData, arrival_city: e.target.value })}
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
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Annuler</Button>
            <Button variant="contained" onClick={handleSave}>
              Sauvegarder
            </Button>
          </DialogActions>
        </Dialog>
      </ResponsivePageTemplate>
    </MainLayout>
  )
}
