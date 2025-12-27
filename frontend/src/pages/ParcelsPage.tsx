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
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
import { parcelService } from '../services'

interface Parcel {
  id: number
  tracking_number: string
  origin: string
  destination: string
  status: string
  weight: number
  created_at: string
  delivery_date: string | null
  recipient_name: string
  recipient_phone: string
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
    tracking_number: '',
    origin: '',
    destination: '',
    status: 'pending',
    weight: 0,
    recipient_name: '',
    recipient_phone: '',
    delivery_date: '',
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
        tracking_number: parcel.tracking_number,
        origin: parcel.origin,
        destination: parcel.destination,
        status: parcel.status,
        weight: parcel.weight,
        recipient_name: parcel.recipient_name,
        recipient_phone: parcel.recipient_phone,
        delivery_date: parcel.delivery_date || '',
      })
    } else {
      setEditingId(null)
      setFormData({
        tracking_number: `TKF-${Date.now()}`,
        origin: '',
        destination: '',
        status: 'pending',
        weight: 0,
        recipient_name: '',
        recipient_phone: '',
        delivery_date: '',
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered':
        return govStyles.colors.success
      case 'in_transit':
        return govStyles.colors.warning
      case 'pending':
        return govStyles.colors.danger
      case 'cancelled':
        return '#999'
      default:
        return govStyles.colors.primary
    }
  }

  const getStatusLabel = (status: string) => {
    const labels: { [key: string]: string } = {
      pending: 'En attente',
      in_transit: 'En transit',
      delivered: 'Livré',
      cancelled: 'Annulé',
    }
    return labels[status] || status
  }

  const filteredParcels = parcels.filter(
    (parcel) =>
      parcel.tracking_number.toLowerCase().includes(search.toLowerCase()) ||
      parcel.origin.toLowerCase().includes(search.toLowerCase()) ||
      parcel.destination.toLowerCase().includes(search.toLowerCase()) ||
      parcel.recipient_name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <GovPageWrapper maxWidth="lg">
        <GovPageHeader
          title="Suivi Colis et Livraisons"
          icon="📦"
          subtitle="Gestion complète du suivi des colis TKF"
          actions={[
            {
              label: 'Nouveau Colis',
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
              label="Rechercher (numéro/destination)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              variant="outlined"
              size="small"
              fullWidth
              sx={{ maxWidth: { md: '350px' } }}
            />
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Statut</InputLabel>
              <Select
                label="Statut"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="all">Tous</option>
                <option value="pending">En attente</option>
                <option value="in_transit">En transit</option>
                <option value="delivered">Livré</option>
                <option value="cancelled">Annulé</option>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              onClick={() => {
                setSearch('')
                setFilterStatus('all')
                loadParcels()
              }}
              sx={govStyles.govButton.secondary}
            >
              Réinitialiser
            </Button>
          </Stack>
        </Paper>

        {/* Statistiques Rapides */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderLeft: `5px solid ${govStyles.colors.success}`, ...govStyles.contentCard }}>
              <CardContent sx={{ pb: '16px !important' }}>
                <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                  Livré
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.success }}>
                  {parcels.filter((p) => p.status === 'delivered').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderLeft: `5px solid ${govStyles.colors.warning}`, ...govStyles.contentCard }}>
              <CardContent sx={{ pb: '16px !important' }}>
                <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                  En transit
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.warning }}>
                  {parcels.filter((p) => p.status === 'in_transit').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderLeft: `5px solid ${govStyles.colors.danger}`, ...govStyles.contentCard }}>
              <CardContent sx={{ pb: '16px !important' }}>
                <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                  En attente
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.danger }}>
                  {parcels.filter((p) => p.status === 'pending').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderLeft: `5px solid ${govStyles.colors.primary}`, ...govStyles.contentCard }}>
              <CardContent sx={{ pb: '16px !important' }}>
                <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.85rem' }}>
                  Total
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 700, color: govStyles.colors.primary }}>
                  {parcels.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tableau */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
            <CircularProgress sx={{ color: govStyles.colors.success }} />
          </Box>
        ) : (
          <TableContainer component={Paper} sx={govStyles.contentCard}>
            <Table sx={govStyles.table}>
              <TableHead>
                <TableRow sx={{ backgroundColor: govStyles.colors.success }}>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Numéro</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Itinéraire</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Destinataire</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="right">Poids</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredParcels.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4, color: '#999' }}>
                      Aucun colis trouvé
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredParcels.map((parcel) => (
                    <TableRow
                      key={parcel.id}
                      sx={{
                        '&:hover': { backgroundColor: '#f9f9f9' },
                        borderLeft: `4px solid ${getStatusColor(parcel.status)}`,
                      }}
                    >
                      <TableCell sx={{ fontWeight: 600, color: govStyles.colors.primary }}>
                        📦 {parcel.tracking_number}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.9rem' }}>
                        {parcel.origin} → {parcel.destination}
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {parcel.recipient_name}
                          </Typography>
                          <Typography variant="caption" sx={{ color: '#999' }}>
                            {parcel.recipient_phone}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 500 }}>
                        {parcel.weight} kg
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={getStatusLabel(parcel.status)}
                          sx={{
                            backgroundColor: `${getStatusColor(parcel.status)}20`,
                            color: getStatusColor(parcel.status),
                            fontWeight: 700,
                          }}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} justifyContent="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleOpenDialog(parcel)}
                            sx={{ color: govStyles.colors.success }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(parcel.id)}
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
          <DialogTitle sx={{ backgroundColor: govStyles.colors.success, color: 'white', fontWeight: 700 }}>
            {editingId ? '✏️ Éditer le colis' : '➕ Nouveau colis'}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Stack spacing={2}>
              <TextField
                label="Numéro de suivi"
                fullWidth
                value={formData.tracking_number}
                onChange={(e) => setFormData({ ...formData, tracking_number: e.target.value })}
              />
              <TextField
                label="Origine"
                fullWidth
                value={formData.origin}
                onChange={(e) => setFormData({ ...formData, origin: e.target.value })}
              />
              <TextField
                label="Destination"
                fullWidth
                value={formData.destination}
                onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
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
                label="Poids (kg)"
                type="number"
                fullWidth
                inputProps={{ step: '0.1', min: '0' }}
                value={formData.weight}
                onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) })}
              />
              <FormControl fullWidth>
                <InputLabel>Statut</InputLabel>
                <Select
                  label="Statut"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="pending">En attente</option>
                  <option value="in_transit">En transit</option>
                  <option value="delivered">Livré</option>
                  <option value="cancelled">Annulé</option>
                </Select>
              </FormControl>
              <TextField
                label="Date de livraison"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={formData.delivery_date}
                onChange={(e) => setFormData({ ...formData, delivery_date: e.target.value })}
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

        <GovPageFooter text="Système de Gestion du Transport - Suivi Colis et Livraisons" />
      </GovPageWrapper>
    </MainLayout>
  )
}
