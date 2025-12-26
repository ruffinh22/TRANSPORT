#!/bin/bash

# Script pour rendre TOUTES les pages responsive
# Ceci rewrite les pages existantes avec la structure responsive

set -e

PAGES_DIR="/home/lidruf/TRANSPORT/frontend/src/pages"

echo "🚀 Conversion TOTALE au Responsive Design Pro"
echo "=============================================="
echo ""

# 1. Mettre à jour TripsPage
cat > "$PAGES_DIR/TripsPage.tsx" << 'EOF'
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
EOF

echo "✅ TripsPage convertie"

# 2. Mettre à jour TicketsPage
cat > "$PAGES_DIR/TicketsPage.tsx" << 'EOF'
import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Typography,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { ResponsivePageTemplate, ResponsiveTable, ResponsiveFilters } from '../components'
import { responsiveStyles } from '../styles/responsiveStyles'
import { ticketService } from '../services'

interface Ticket {
  id: number
  trip: number
  passenger_name: string
  passenger_email: string
  passenger_phone: string
  seat_number: string
  price: number
  status: string
  qr_code: string
  created_at: string
}

export const TicketsPage: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    trip: 1,
    passenger_name: '',
    passenger_email: '',
    passenger_phone: '',
    seat_number: '',
    price: 5000,
    status: 'confirmed',
  })

  useEffect(() => {
    loadTickets()
  }, [filterStatus])

  const loadTickets = async () => {
    setLoading(true)
    try {
      const params = filterStatus !== 'all' ? { status: filterStatus } : {}
      const response = await ticketService.list(params)
      setTickets(response.data.results || response.data || [])
      setError(null)
    } catch (err) {
      setError('Erreur au chargement des billets')
      console.error(err)
    }
    setLoading(false)
  }

  const handleOpenDialog = (ticket?: Ticket) => {
    if (ticket) {
      setEditingId(ticket.id)
      setFormData({
        trip: ticket.trip,
        passenger_name: ticket.passenger_name,
        passenger_email: ticket.passenger_email,
        passenger_phone: ticket.passenger_phone,
        seat_number: ticket.seat_number,
        price: ticket.price,
        status: ticket.status,
      })
    } else {
      setEditingId(null)
      setFormData({
        trip: 1,
        passenger_name: '',
        passenger_email: '',
        passenger_phone: '',
        seat_number: '',
        price: 5000,
        status: 'confirmed',
      })
    }
    setOpenDialog(true)
  }

  const handleSave = async () => {
    try {
      if (editingId) {
        await ticketService.update(editingId, formData)
      } else {
        await ticketService.create(formData)
      }
      await loadTickets()
      setOpenDialog(false)
    } catch (err) {
      setError('Erreur lors de la sauvegarde')
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await ticketService.delete(id)
        await loadTickets()
      } catch (err) {
        setError('Erreur lors de la suppression')
      }
    }
  }

  const filteredTickets = tickets.filter(
    (ticket) =>
      ticket.passenger_name.toLowerCase().includes(search.toLowerCase()) ||
      ticket.passenger_email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <ResponsivePageTemplate
        title="Gestion des Billets"
        subtitle="Consultez et gérez tous vos billets"
        actions={[
          <Button
            key="add"
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Nouveau Billet
          </Button>,
        ]}
      >
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <ResponsiveFilters
          fields={[
            { name: 'search', label: 'Recherche (nom/email)', value: search, onChange: setSearch },
            {
              name: 'status',
              label: 'Statut',
              value: filterStatus,
              onChange: setFilterStatus,
              options: [
                { label: 'Tous', value: 'all' },
                { label: 'Confirmé', value: 'confirmed' },
                { label: 'Annulé', value: 'cancelled' },
                { label: 'Utilisé', value: 'used' },
              ],
            },
          ]}
          onApply={() => loadTickets()}
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
              { key: 'passenger_name', label: 'Passager' },
              { key: 'passenger_email', label: 'Email' },
              { key: 'seat_number', label: 'Siège' },
              { key: 'price', label: 'Prix (FCFA)' },
              {
                key: 'status',
                label: 'Statut',
                render: (val) => (
                  <Chip
                    label={val}
                    color={val === 'confirmed' ? 'success' : val === 'cancelled' ? 'error' : 'warning'}
                    size="small"
                  />
                ),
              },
              {
                key: 'actions',
                label: 'Actions',
                render: (_, row) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" variant="text" onClick={() => handleOpenDialog(row)}>
                      ✏️
                    </Button>
                    <Button size="small" variant="text" color="error" onClick={() => handleDelete(row.id)}>
                      🗑️
                    </Button>
                  </Stack>
                ),
              },
            ]}
            data={filteredTickets}
            emptyMessage="Aucun billet trouvé"
          />
        )}

        {/* Dialog Form */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>{editingId ? 'Éditer le billet' : 'Nouveau billet'}</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <Stack spacing={2}>
              <TextField
                label="Nom du passager"
                fullWidth
                value={formData.passenger_name}
                onChange={(e) => setFormData({ ...formData, passenger_name: e.target.value })}
              />
              <TextField
                label="Email"
                type="email"
                fullWidth
                value={formData.passenger_email}
                onChange={(e) => setFormData({ ...formData, passenger_email: e.target.value })}
              />
              <TextField
                label="Téléphone"
                fullWidth
                value={formData.passenger_phone}
                onChange={(e) => setFormData({ ...formData, passenger_phone: e.target.value })}
              />
              <TextField
                label="Numéro de siège"
                fullWidth
                value={formData.seat_number}
                onChange={(e) => setFormData({ ...formData, seat_number: e.target.value })}
              />
              <TextField
                label="Prix (FCFA)"
                type="number"
                fullWidth
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: parseInt(e.target.value) })}
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
EOF

echo "✅ TicketsPage convertie"

# 3. Mettre à jour ParcelsPage
cat > "$PAGES_DIR/ParcelsPage.tsx" << 'EOF'
import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Typography,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  LocalShipping as TrackIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { ResponsivePageTemplate, ResponsiveTable, ResponsiveFilters } from '../components'
import { responsiveStyles } from '../styles/responsiveStyles'
import { parcelService } from '../services'

interface Parcel {
  id: number
  trip: number
  sender_name: string
  sender_phone: string
  recipient_name: string
  recipient_phone: string
  description: string
  weight: number
  price: number
  status: string
  tracking_number: string
  created_at: string
}

export const ParcelsPage: React.FC = () => {
  const [parcels, setParcels] = useState<Parcel[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    trip: 1,
    sender_name: '',
    sender_phone: '',
    recipient_name: '',
    recipient_phone: '',
    description: '',
    weight: 0,
    price: 2500,
    status: 'pending',
  })

  useEffect(() => {
    loadParcels()
  }, [filterStatus])

  const loadParcels = async () => {
    setLoading(true)
    try {
      const params = filterStatus !== 'all' ? { status: filterStatus } : {}
      const response = await parcelService.list(params)
      setParcels(response.data.results || response.data || [])
      setError(null)
    } catch (err) {
      setError('Erreur au chargement des colis')
      console.error(err)
    }
    setLoading(false)
  }

  const handleOpenDialog = (parcel?: Parcel) => {
    if (parcel) {
      setEditingId(parcel.id)
      setFormData({
        trip: parcel.trip,
        sender_name: parcel.sender_name,
        sender_phone: parcel.sender_phone,
        recipient_name: parcel.recipient_name,
        recipient_phone: parcel.recipient_phone,
        description: parcel.description,
        weight: parcel.weight,
        price: parcel.price,
        status: parcel.status,
      })
    } else {
      setEditingId(null)
      setFormData({
        trip: 1,
        sender_name: '',
        sender_phone: '',
        recipient_name: '',
        recipient_phone: '',
        description: '',
        weight: 0,
        price: 2500,
        status: 'pending',
      })
    }
    setOpenDialog(true)
  }

  const handleSave = async () => {
    try {
      if (editingId) {
        await parcelService.update(editingId, formData)
      } else {
        await parcelService.create(formData)
      }
      await loadParcels()
      setOpenDialog(false)
    } catch (err) {
      setError('Erreur lors de la sauvegarde')
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await parcelService.delete(id)
        await loadParcels()
      } catch (err) {
        setError('Erreur lors de la suppression')
      }
    }
  }

  const filteredParcels = parcels.filter(
    (parcel) =>
      parcel.tracking_number.toLowerCase().includes(search.toLowerCase()) ||
      parcel.recipient_name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <ResponsivePageTemplate
        title="Gestion des Colis"
        subtitle="Suivez et gérez vos colis"
        actions={[
          <Button
            key="add"
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Nouveau Colis
          </Button>,
        ]}
      >
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <ResponsiveFilters
          fields={[
            { name: 'search', label: 'Recherche (tracking/destinataire)', value: search, onChange: setSearch },
            {
              name: 'status',
              label: 'Statut',
              value: filterStatus,
              onChange: setFilterStatus,
              options: [
                { label: 'Tous', value: 'all' },
                { label: 'En attente', value: 'pending' },
                { label: 'En transit', value: 'in_transit' },
                { label: 'Livré', value: 'delivered' },
              ],
            },
          ]}
          onApply={() => loadParcels()}
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
              { key: 'tracking_number', label: 'Suivi' },
              { key: 'sender_name', label: 'Expéditeur' },
              { key: 'recipient_name', label: 'Destinataire' },
              { key: 'weight', label: 'Poids (kg)' },
              { key: 'price', label: 'Prix (FCFA)' },
              {
                key: 'status',
                label: 'Statut',
                render: (val) => (
                  <Chip
                    label={val}
                    color={val === 'pending' ? 'warning' : val === 'in_transit' ? 'info' : 'success'}
                    size="small"
                  />
                ),
              },
              {
                key: 'actions',
                label: 'Actions',
                render: (_, row) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" variant="text" onClick={() => handleOpenDialog(row)}>
                      ✏️
                    </Button>
                    <Button size="small" variant="text" color="error" onClick={() => handleDelete(row.id)}>
                      🗑️
                    </Button>
                  </Stack>
                ),
              },
            ]}
            data={filteredParcels}
            emptyMessage="Aucun colis trouvé"
          />
        )}

        {/* Dialog Form */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>{editingId ? 'Éditer le colis' : 'Nouveau colis'}</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <Stack spacing={2}>
              <TextField
                label="Nom de l'expéditeur"
                fullWidth
                value={formData.sender_name}
                onChange={(e) => setFormData({ ...formData, sender_name: e.target.value })}
              />
              <TextField
                label="Téléphone expéditeur"
                fullWidth
                value={formData.sender_phone}
                onChange={(e) => setFormData({ ...formData, sender_phone: e.target.value })}
              />
              <TextField
                label="Nom du destinataire"
                fullWidth
                value={formData.recipient_name}
                onChange={(e) => setFormData({ ...formData, recipient_name: e.target.value })}
              />
              <TextField
                label="Téléphone destinataire"
                fullWidth
                value={formData.recipient_phone}
                onChange={(e) => setFormData({ ...formData, recipient_phone: e.target.value })}
              />
              <TextField
                label="Description"
                multiline
                rows={3}
                fullWidth
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
              <TextField
                label="Poids (kg)"
                type="number"
                fullWidth
                value={formData.weight}
                onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) })}
              />
              <TextField
                label="Prix (FCFA)"
                type="number"
                fullWidth
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: parseInt(e.target.value) })}
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
EOF

echo "✅ ParcelsPage convertie"

echo ""
echo "🎉 Conversion TOTALE aux Responsive terminée!"
echo ""
echo "Pages mises à jour:"
echo "  ✅ TripsPage"
echo "  ✅ TicketsPage"
echo "  ✅ ParcelsPage"
echo ""
echo "Caractéristiques:"
echo "  📱 Responsive sur tous les breakpoints"
echo "  🎨 Tableaux qui deviennent cartes sur mobile"
echo "  🔍 Filtres intelligents"
echo "  ⚡ Chargement et gestion d'erreurs"
echo "  🎯 Interface moderne et pro"
