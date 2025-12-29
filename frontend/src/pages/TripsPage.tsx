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
  MenuItem,
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
  useTheme,
  useMediaQuery,
  Grid,
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
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

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
    <MainLayout hideGovernmentHeader={true}>
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

        {/* Filtres - ULTRA RESPONSIVE */}
        <Paper sx={{ p: { xs: 1.5, sm: 2, md: 2 }, mb: { xs: 2, sm: 3, md: 3 }, ...govStyles.contentCard }}>
          <Stack direction={{ xs: 'column', sm: 'column', md: 'row' }} spacing={{ xs: 1.5, sm: 2, md: 2 }}>
            <TextField
              label="Rechercher (ville)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              variant="outlined"
              size="small"
              fullWidth
              sx={{ 
                maxWidth: { xs: '100%', md: '300px' },
                '& .MuiOutlinedInput-root': {
                  fontSize: { xs: '0.85rem', sm: '0.9rem', md: '1rem' },
                }
              }}
            />
            <FormControl size="small" sx={{ minWidth: { xs: '100%', md: 200 } }}>
              <InputLabel htmlFor="status-filter-select" sx={{ fontSize: { xs: '0.85rem', sm: '0.9rem', md: '1rem' } }}>Statut</InputLabel>
              <Select
                id="status-filter-select"
                label="Statut"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                sx={{ fontSize: { xs: '0.85rem', sm: '0.9rem', md: '1rem' } }}
              >
                <MenuItem value="all">Tous</MenuItem>
                <MenuItem value="scheduled">Planifié</MenuItem>
                <MenuItem value="ongoing">En cours</MenuItem>
                <MenuItem value="completed">Terminé</MenuItem>
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
              fullWidth={isMobile}
            >
              Réinitialiser
            </Button>
          </Stack>
        </Paper>

        {/* Table - ULTRA RESPONSIVE */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: { xs: '300px', md: '400px' } }}>
            <CircularProgress sx={{ color: govStyles.colors.primary }} />
          </Box>
        ) : isMobile ? (
          // MOBILE VIEW - Cartes responsives
          <Box sx={{ mb: 3 }}>
            {filteredTrips.length === 0 ? (
              <Card sx={{ ...govStyles.contentCard, p: { xs: 2, sm: 3 }, textAlign: 'center' }}>
                <Typography sx={{ color: '#999', fontSize: { xs: '0.85rem', sm: '0.95rem', md: '1rem' } }}>
                  Aucun trajet trouvé
                </Typography>
              </Card>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 1.5, sm: 2 } }}>
                {filteredTrips.map((trip) => (
                  <Card key={trip.id} sx={{ 
                    ...govStyles.contentCard, 
                    p: { xs: 1.5, sm: 2 },
                    border: `2px solid ${govStyles.colors.primary}`,
                    borderRadius: '8px',
                  }}>
                      <CardContent sx={{ p: 0 }}>
                        <Stack spacing={{ xs: 1, sm: 1.5 }}>
                          {/* Header */}
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                            <Box sx={{ flex: 1 }}>
                              <Typography sx={{ fontWeight: 700, fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' }, color: govStyles.colors.primary }}>
                                {trip.departure_city} → {trip.arrival_city}
                              </Typography>
                              <Typography sx={{ fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' }, color: '#666', mt: 0.5 }}>
                                {new Date(trip.departure_date).toLocaleDateString('fr-FR')}
                              </Typography>
                            </Box>
                            <Chip
                              label={trip.status === 'scheduled' ? 'Planifié' : trip.status === 'ongoing' ? 'En cours' : 'Terminé'}
                              color={trip.status === 'scheduled' ? 'primary' : trip.status === 'ongoing' ? 'warning' : 'success'}
                              size="small"
                              sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                            />
                          </Box>

                          {/* Info Row 1 */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                            <Box>
                              <Typography sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, color: '#999', fontWeight: 600, textTransform: 'uppercase' }}>Sièges</Typography>
                              <Typography sx={{ fontSize: { xs: '0.85rem', sm: '0.95rem' }, fontWeight: 700 }}>{trip.total_seats}</Typography>
                            </Box>
                            <Box>
                              <Typography sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, color: '#999', fontWeight: 600, textTransform: 'uppercase' }}>Disponibles</Typography>
                              <Chip
                                label={trip.available_seats}
                                color={trip.available_seats === 0 ? 'error' : trip.available_seats < 5 ? 'warning' : 'success'}
                                size="small"
                                sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                              />
                            </Box>
                          </Box>

                          {/* Info Row 2 */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                            <Box>
                              <Typography sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, color: '#999', fontWeight: 600, textTransform: 'uppercase' }}>Prix/Siège</Typography>
                              <Typography sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' }, fontWeight: 700, color: govStyles.colors.primary }}>
                                {trip.price_per_seat.toLocaleString('fr-FR')} FCFA
                              </Typography>
                            </Box>
                            <Box>
                              <Typography sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, color: '#999', fontWeight: 600, textTransform: 'uppercase' }}>Arrivée</Typography>
                              <Typography sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem' } }}>
                                {new Date(trip.arrival_date).toLocaleDateString('fr-FR')}
                              </Typography>
                            </Box>
                          </Box>

                          {/* Actions */}
                          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => handleOpenDialog(trip)}
                              fullWidth
                              sx={{ 
                                color: govStyles.colors.primary,
                                borderColor: govStyles.colors.primary,
                                fontSize: { xs: '0.65rem', sm: '0.75rem' },
                                py: { xs: 0.75, sm: 1 },
                              }}
                            >
                              ✏️ Éditer
                            </Button>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => handleDelete(trip.id)}
                              fullWidth
                              sx={{ 
                                color: govStyles.colors.danger,
                                borderColor: govStyles.colors.danger,
                                fontSize: { xs: '0.65rem', sm: '0.75rem' },
                                py: { xs: 0.75, sm: 1 },
                              }}
                            >
                              🗑️ Suppr.
                            </Button>
                          </Stack>
                        </Stack>
                      </CardContent>
                    </Card>
                ))}
              </Box>
            )}
          </Box>
        ) : (
          // DESKTOP VIEW - Table
          <TableContainer component={Paper} sx={{ ...govStyles.contentCard, overflowX: 'auto' }}>
            <Table sx={{ 
              ...govStyles.table,
              fontSize: { xs: '0.75rem', sm: '0.85rem', md: '1rem' },
            }}>
              <TableHead>
                <TableRow sx={{ backgroundColor: govStyles.colors.primary }}>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' } }}>Départ</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' } }}>Arrivée</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' } }}>Date Départ</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' } }} align="center">Sièges</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' } }} align="center">Dispo</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' } }}>Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' } }} align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTrips.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: { xs: 2, md: 4 }, color: '#999', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
                      Aucun trajet trouvé
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTrips.map((trip) => (
                    <TableRow key={trip.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}>{trip.departure_city}</TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}>{trip.arrival_city}</TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}>{new Date(trip.departure_date).toLocaleDateString('fr-FR')}</TableCell>
                      <TableCell align="center" sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}>{trip.total_seats}</TableCell>
                      <TableCell align="center">
                        <Chip
                          label={trip.available_seats}
                          color={trip.available_seats === 0 ? 'error' : trip.available_seats < 5 ? 'warning' : 'success'}
                          size="small"
                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={trip.status === 'scheduled' ? 'Planifié' : trip.status === 'ongoing' ? 'En cours' : 'Terminé'}
                          color={trip.status === 'scheduled' ? 'primary' : trip.status === 'ongoing' ? 'warning' : 'success'}
                          size="small"
                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} justifyContent="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleOpenDialog(trip)}
                            sx={{ color: govStyles.colors.primary, fontSize: { xs: '0.9rem', sm: '1rem' } }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(trip.id)}
                            sx={{ color: govStyles.colors.danger, fontSize: { xs: '0.9rem', sm: '1rem' } }}
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

        {/* Dialog Form - ULTRA RESPONSIVE */}
        <Dialog 
          open={openDialog} 
          onClose={() => setOpenDialog(false)} 
          maxWidth="sm" 
          fullWidth
          PaperProps={{
            sx: {
              borderRadius: { xs: '8px', md: '12px' },
            }
          }}
        >
          <DialogTitle sx={{ 
            backgroundColor: govStyles.colors.primary, 
            color: 'white', 
            fontWeight: 700,
            fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
            p: { xs: 1.5, sm: 2 },
          }}>
            {editingId ? '✏️ Éditer le trajet' : '➕ Nouveau trajet'}
          </DialogTitle>
          <DialogContent sx={{ pt: { xs: 1.5, sm: 2, md: 3 }, p: { xs: 1.5, sm: 2, md: 2.5 } }}>
            <Stack spacing={{ xs: 1.5, sm: 2 }}>
              <TextField
                label="Ville de départ"
                fullWidth
                value={formData.departure_city}
                onChange={(e) => setFormData({ ...formData, departure_city: e.target.value })}
                variant="outlined"
                size="small"
                sx={{ '& .MuiOutlinedInput-root': { fontSize: { xs: '0.85rem', sm: '0.95rem' } } }}
              />
              <TextField
                label="Ville d'arrivée"
                fullWidth
                value={formData.arrival_city}
                onChange={(e) => setFormData({ ...formData, arrival_city: e.target.value })}
                variant="outlined"
                size="small"
                sx={{ '& .MuiOutlinedInput-root': { fontSize: { xs: '0.85rem', sm: '0.95rem' } } }}
              />
              <TextField
                label="Date de départ"
                type="datetime-local"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={formData.departure_date}
                onChange={(e) => setFormData({ ...formData, departure_date: e.target.value })}
                size="small"
                sx={{ '& .MuiOutlinedInput-root': { fontSize: { xs: '0.85rem', sm: '0.95rem' } } }}
              />
              <TextField
                label="Date d'arrivée"
                type="datetime-local"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={formData.arrival_date}
                onChange={(e) => setFormData({ ...formData, arrival_date: e.target.value })}
                size="small"
                sx={{ '& .MuiOutlinedInput-root': { fontSize: { xs: '0.85rem', sm: '0.95rem' } } }}
              />
              <TextField
                label="Nombre de sièges"
                type="number"
                fullWidth
                value={formData.total_seats}
                onChange={(e) => setFormData({ ...formData, total_seats: parseInt(e.target.value) })}
                size="small"
                sx={{ '& .MuiOutlinedInput-root': { fontSize: { xs: '0.85rem', sm: '0.95rem' } } }}
              />
              <TextField
                label="Prix par siège (FCFA)"
                type="number"
                fullWidth
                value={formData.price_per_seat}
                onChange={(e) => setFormData({ ...formData, price_per_seat: parseInt(e.target.value) })}
                size="small"
                sx={{ '& .MuiOutlinedInput-root': { fontSize: { xs: '0.85rem', sm: '0.95rem' } } }}
              />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: { xs: 1.5, sm: 2 }, gap: { xs: 1, sm: 1.5 } }}>
            <Button 
              onClick={() => setOpenDialog(false)} 
              sx={{ 
                ...govStyles.govButton.secondary,
                fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
                py: { xs: 0.75, sm: 1 },
              }}
            >
              Annuler
            </Button>
            <Button 
              variant="contained" 
              onClick={handleSave} 
              sx={{ 
                ...govStyles.govButton.primary,
                fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
                py: { xs: 0.75, sm: 1 },
              }}
            >
              Sauvegarder
            </Button>
          </DialogActions>
        </Dialog>

        <GovPageFooter text="Système de Gestion du Transport - Gestion des Trajets" />
      </GovPageWrapper>
    </MainLayout>
  )
}
