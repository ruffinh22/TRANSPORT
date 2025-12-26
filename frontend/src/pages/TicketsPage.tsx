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
  GetApp as DownloadIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
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
      setTickets(response.data.results || response.data)
    } catch (error) {
      console.error('Erreur:', error)
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

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingId(null)
  }

  const handleSaveTicket = async () => {
    try {
      if (editingId) {
        await ticketService.update(editingId, formData)
      } else {
        await ticketService.create(formData)
      }
      handleCloseDialog()
      loadTickets()
    } catch (error) {
      console.error('Erreur:', error)
    }
  }

  const handleDeleteTicket = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await ticketService.delete(id)
        loadTickets()
      } catch (error) {
        console.error('Erreur:', error)
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'success'
      case 'pending': return 'warning'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  const filteredTickets = tickets.filter(ticket =>
    ticket.passenger_name.toLowerCase().includes(search.toLowerCase()) ||
    ticket.passenger_email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => window.history.back()}
            variant="outlined"
            size="small"
          >
            Retour
          </Button>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Gestion des Billets
          </Typography>
        </Box>

        {/* Stats Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Total billets
                </Typography>
                <Typography variant="h4">{tickets.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Confirmés
                </Typography>
                <Typography variant="h4">
                  {tickets.filter(t => t.status === 'confirmed').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  En attente
                </Typography>
                <Typography variant="h4">
                  {tickets.filter(t => t.status === 'pending').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Chiffre d'affaires
                </Typography>
                <Typography variant="h4">
                  {tickets.reduce((sum, t) => sum + t.price, 0).toLocaleString()} CFA
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Card sx={{ mb: 3, p: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              label="Rechercher passager"
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
                <option value="confirmed">Confirmés</option>
                <option value="pending">En attente</option>
                <option value="cancelled">Annulés</option>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
              sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
            >
              Ajouter billet
            </Button>
          </Stack>
        </Card>

        {/* Tickets Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead sx={{ backgroundColor: '#f5f6fa' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Passager</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Email</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Téléphone</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Siège</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Prix</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Statut</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredTickets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography color="textSecondary">Aucun billet trouvé</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredTickets.map((ticket) => (
                  <TableRow key={ticket.id} hover>
                    <TableCell sx={{ fontWeight: 600 }}>{ticket.passenger_name}</TableCell>
                    <TableCell>{ticket.passenger_email}</TableCell>
                    <TableCell>{ticket.passenger_phone}</TableCell>
                    <TableCell align="right">
                      <Chip label={ticket.seat_number} variant="outlined" />
                    </TableCell>
                    <TableCell align="right">{ticket.price.toLocaleString()} CFA</TableCell>
                    <TableCell>
                      <Chip
                        label={ticket.status}
                        size="small"
                        color={getStatusColor(ticket.status) as any}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={0.5} justifyContent="center">
                        <Button
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => console.log('Download', ticket.id)}
                        />
                        <Button
                          size="small"
                          startIcon={<EditIcon />}
                          onClick={() => handleOpenDialog(ticket)}
                        />
                        <Button
                          size="small"
                          color="error"
                          startIcon={<DeleteIcon />}
                          onClick={() => handleDeleteTicket(ticket.id)}
                        />
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
          {editingId ? 'Éditer billet' : 'Ajouter un billet'}
        </DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            label="Nom passager"
            variant="outlined"
            value={formData.passenger_name}
            onChange={(e) => setFormData({ ...formData, passenger_name: e.target.value })}
            fullWidth
          />
          <TextField
            label="Email"
            type="email"
            variant="outlined"
            value={formData.passenger_email}
            onChange={(e) => setFormData({ ...formData, passenger_email: e.target.value })}
            fullWidth
          />
          <TextField
            label="Téléphone"
            variant="outlined"
            value={formData.passenger_phone}
            onChange={(e) => setFormData({ ...formData, passenger_phone: e.target.value })}
            fullWidth
          />
          <TextField
            label="Numéro de siège"
            variant="outlined"
            value={formData.seat_number}
            onChange={(e) => setFormData({ ...formData, seat_number: e.target.value })}
            fullWidth
          />
          <TextField
            label="Prix"
            type="number"
            variant="outlined"
            value={formData.price}
            onChange={(e) => setFormData({ ...formData, price: parseInt(e.target.value) })}
            fullWidth
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Annuler</Button>
          <Button onClick={handleSaveTicket} variant="contained">
            {editingId ? 'Mettre à jour' : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  )
}
