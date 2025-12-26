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
