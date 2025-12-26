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
