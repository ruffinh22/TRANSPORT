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
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material'
import {
  Add as AddIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
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
      <GovPageWrapper maxWidth="lg">
        <GovPageHeader
          title="Gestion des Billets"
          icon="🎫"
          subtitle="Consultez et gérez tous vos billets"
          actions={[
            {
              label: 'Nouveau Billet',
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
              label="Recherche (nom/email)"
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
                <option value="confirmed">Confirmé</option>
                <option value="cancelled">Annulé</option>
                <option value="used">Utilisé</option>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              onClick={() => {
                setSearch('')
                setFilterStatus('all')
                loadTickets()
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
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Passager</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Email</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Siège</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="right">Prix</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTickets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4, color: '#999' }}>
                      Aucun billet trouvé
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTickets.map((ticket) => (
                    <TableRow key={ticket.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                      <TableCell>{ticket.passenger_name}</TableCell>
                      <TableCell>{ticket.passenger_email}</TableCell>
                      <TableCell>{ticket.seat_number}</TableCell>
                      <TableCell align="right">{ticket.price.toLocaleString('fr-FR')} CFA</TableCell>
                      <TableCell>
                        <Chip
                          label={
                            ticket.status === 'confirmed'
                              ? 'Confirmé'
                              : ticket.status === 'cancelled'
                                ? 'Annulé'
                                : ticket.status === 'used'
                                  ? 'Utilisé'
                                  : 'Pending'
                          }
                          color={
                            ticket.status === 'confirmed'
                              ? 'success'
                              : ticket.status === 'cancelled'
                                ? 'error'
                                : ticket.status === 'used'
                                  ? 'warning'
                                  : 'default'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} justifyContent="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleOpenDialog(ticket)}
                            sx={{ color: govStyles.colors.primary }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(ticket.id)}
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
            {editingId ? '✏️ Éditer le billet' : '➕ Nouveau billet'}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Stack spacing={2}>
              <TextField
                label="Nom du passager"
                fullWidth
                value={formData.passenger_name}
                onChange={(e) => setFormData({ ...formData, passenger_name: e.target.value })}
                variant="outlined"
              />
              <TextField
                label="Email"
                type="email"
                fullWidth
                value={formData.passenger_email}
                onChange={(e) => setFormData({ ...formData, passenger_email: e.target.value })}
                variant="outlined"
              />
              <TextField
                label="Téléphone"
                fullWidth
                value={formData.passenger_phone}
                onChange={(e) => setFormData({ ...formData, passenger_phone: e.target.value })}
                variant="outlined"
              />
              <TextField
                label="Numéro de siège"
                fullWidth
                value={formData.seat_number}
                onChange={(e) => setFormData({ ...formData, seat_number: e.target.value })}
                variant="outlined"
              />
              <TextField
                label="Prix (FCFA)"
                type="number"
                fullWidth
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: parseInt(e.target.value) })}
                variant="outlined"
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

        <GovPageFooter text="Système de Gestion du Transport - Gestion des Billets" />
      </GovPageWrapper>
    </MainLayout>
  )
}
