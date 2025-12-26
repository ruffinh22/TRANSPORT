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
  LinearProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  LocalShipping as TrackIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
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
  const [seedLoading, setSeedLoading] = useState(false)

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
      setParcels(response.data.results || response.data)
    } catch (error) {
      console.error('Erreur:', error)
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

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingId(null)
  }

  const handleSaveParcel = async () => {
    try {
      if (editingId) {
        await parcelService.update(editingId, formData)
      } else {
        await parcelService.create(formData)
      }
      handleCloseDialog()
      loadParcels()
    } catch (error) {
      console.error('Erreur:', error)
    }
  }

  const handleDeleteParcel = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await parcelService.delete(id)
        loadParcels()
      } catch (error) {
        console.error('Erreur:', error)
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'warning'
      case 'in_transit': return 'info'
      case 'delivered': return 'success'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  const getStatusProgress = (status: string) => {
    switch (status) {
      case 'pending': return 25
      case 'in_transit': return 65
      case 'delivered': return 100
      default: return 0
    }
  }

  const handleSeedParcels = async () => {
    setSeedLoading(true)
    try {
      await parcelService.seed()
      loadParcels()
      alert('✅ Colis générés avec succès!')
    } catch (error) {
      console.error('Erreur:', error)
      alert('❌ Erreur lors de la génération des colis')
    }
    setSeedLoading(false)
  }

  const filteredParcels = parcels.filter(parcel =>
    parcel.tracking_number.toLowerCase().includes(search.toLowerCase()) ||
    parcel.sender_name.toLowerCase().includes(search.toLowerCase()) ||
    parcel.recipient_name.toLowerCase().includes(search.toLowerCase())
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
            Gestion des Colis
          </Typography>
        </Box>

        {/* Stats Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Total colis
                </Typography>
                <Typography variant="h4">{parcels.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  En transit
                </Typography>
                <Typography variant="h4">
                  {parcels.filter(p => p.status === 'in_transit').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Livrés
                </Typography>
                <Typography variant="h4">
                  {parcels.filter(p => p.status === 'delivered').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Poids total
                </Typography>
                <Typography variant="h4">
                  {parcels.reduce((sum, p) => sum + p.weight, 0)} kg
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Card sx={{ mb: 3, p: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              label="Rechercher (suivi, expéditeur, destinataire)"
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
                <option value="pending">En attente</option>
                <option value="in_transit">En transit</option>
                <option value="delivered">Livré</option>
                <option value="cancelled">Annulé</option>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
              sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
            >
              Ajouter colis
            </Button>
            <Button
              variant="outlined"
              color="success"
              onClick={handleSeedParcels}
              disabled={seedLoading}
            >
              {seedLoading ? '⏳ Génération...' : '🌱 Seed'}
            </Button>
          </Stack>
        </Card>

        {/* Parcels Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead sx={{ backgroundColor: '#f5f6fa' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Suivi</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Expéditeur → Destinataire</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Poids</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Prix</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Progression</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredParcels.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography color="textSecondary">Aucun colis trouvé</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredParcels.map((parcel) => (
                  <TableRow key={parcel.id} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace' }}>
                        {parcel.tracking_number}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {parcel.sender_name} → {parcel.recipient_name}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{parcel.weight} kg</TableCell>
                    <TableCell align="right">{parcel.price.toLocaleString()} CFA</TableCell>
                    <TableCell>
                      <Box sx={{ width: '100%' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ flex: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={getStatusProgress(parcel.status)}
                              sx={{ height: 6, borderRadius: 3 }}
                            />
                          </Box>
                          <Chip
                            label={parcel.status}
                            size="small"
                            color={getStatusColor(parcel.status) as any}
                            variant="outlined"
                          />
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={0.5} justifyContent="center">
                        <Button
                          size="small"
                          startIcon={<TrackIcon />}
                          onClick={() => console.log('Track', parcel.id)}
                        />
                        <Button
                          size="small"
                          startIcon={<EditIcon />}
                          onClick={() => handleOpenDialog(parcel)}
                        />
                        <Button
                          size="small"
                          color="error"
                          startIcon={<DeleteIcon />}
                          onClick={() => handleDeleteParcel(parcel.id)}
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
          {editingId ? 'Éditer colis' : 'Ajouter un colis'}
        </DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            label="Nom expéditeur"
            variant="outlined"
            value={formData.sender_name}
            onChange={(e) => setFormData({ ...formData, sender_name: e.target.value })}
            fullWidth
          />
          <TextField
            label="Téléphone expéditeur"
            variant="outlined"
            value={formData.sender_phone}
            onChange={(e) => setFormData({ ...formData, sender_phone: e.target.value })}
            fullWidth
          />
          <TextField
            label="Nom destinataire"
            variant="outlined"
            value={formData.recipient_name}
            onChange={(e) => setFormData({ ...formData, recipient_name: e.target.value })}
            fullWidth
          />
          <TextField
            label="Téléphone destinataire"
            variant="outlined"
            value={formData.recipient_phone}
            onChange={(e) => setFormData({ ...formData, recipient_phone: e.target.value })}
            fullWidth
          />
          <TextField
            label="Description"
            variant="outlined"
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            fullWidth
          />
          <TextField
            label="Poids (kg)"
            type="number"
            variant="outlined"
            value={formData.weight}
            onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) })}
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
          <FormControl fullWidth>
            <InputLabel>Statut</InputLabel>
            <Select
              value={formData.status}
              label="Statut"
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            >
              <option value="pending">En attente</option>
              <option value="in_transit">En transit</option>
              <option value="delivered">Livré</option>
              <option value="cancelled">Annulé</option>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Annuler</Button>
          <Button onClick={handleSaveParcel} variant="contained">
            {editingId ? 'Mettre à jour' : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  )
}
