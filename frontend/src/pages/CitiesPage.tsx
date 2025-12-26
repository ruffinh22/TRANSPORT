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
  Alert,
  CircularProgress,
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { ResponsivePageTemplate, ResponsiveTable, ResponsiveFilters } from '../components'
import { responsiveStyles } from '../styles/responsiveStyles'
import { cityService } from '../services'

interface City {
  id: number
  name: string
  region: string
  country: string
  latitude: number
  longitude: number
  created_at: string
}

export const CitiesPage: React.FC = () => {
  const [cities, setCities] = useState<City[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    name: '',
    region: '',
    country: 'Burkina Faso',
    latitude: 0,
    longitude: 0,
  })

  useEffect(() => {
    loadCities()
  }, [])

  const loadCities = async () => {
    setLoading(true)
    try {
      const response = await cityService.list()
      setCities(response.data.results || response.data || [])
      setError(null)
    } catch (err) {
      setError('Erreur au chargement des villes')
    }
    setLoading(false)
  }

  const handleOpenDialog = (city?: City) => {
    if (city) {
      setEditingId(city.id)
      setFormData({
        name: city.name,
        region: city.region,
        country: city.country,
        latitude: city.latitude,
        longitude: city.longitude,
      })
    } else {
      setEditingId(null)
      setFormData({
        name: '',
        region: '',
        country: 'Burkina Faso',
        latitude: 0,
        longitude: 0,
      })
    }
    setOpenDialog(true)
  }

  const handleSave = async () => {
    try {
      if (editingId) {
        await cityService.update(editingId, formData)
      } else {
        await cityService.create(formData)
      }
      await loadCities()
      setOpenDialog(false)
    } catch (err) {
      setError('Erreur lors de la sauvegarde')
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await cityService.delete(id)
        await loadCities()
      } catch (err) {
        setError('Erreur lors de la suppression')
      }
    }
  }

  const filteredCities = cities.filter((c) => c.name.toLowerCase().includes(search.toLowerCase()))

  return (
    <MainLayout>
      <ResponsivePageTemplate
        title="Gestion des Villes"
        subtitle="Consultez et gérez les villes desservies"
        actions={[
          <Button key="add" variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
            Ajouter Ville
          </Button>,
        ]}
      >
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <ResponsiveFilters
          fields={[
            { name: 'search', label: 'Recherche', value: search, onChange: setSearch },
          ]}
          onApply={() => loadCities()}
          onReset={() => setSearch('')}
        />

        {loading ? (
          <Box sx={responsiveStyles.flexCenter}>
            <CircularProgress />
          </Box>
        ) : (
          <ResponsiveTable
            columns={[
              { key: 'name', label: 'Ville' },
              { key: 'region', label: 'Région' },
              { key: 'country', label: 'Pays' },
              {
                key: 'actions',
                label: 'Actions',
                render: (_, row) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" variant="text" onClick={() => handleOpenDialog(row)}>✏️</Button>
                    <Button size="small" variant="text" color="error" onClick={() => handleDelete(row.id)}>🗑️</Button>
                  </Stack>
                ),
              },
            ]}
            data={filteredCities}
            emptyMessage="Aucune ville trouvée"
          />
        )}

        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>{editingId ? 'Éditer' : 'Ajouter ville'}</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <Stack spacing={2}>
              <TextField label="Nom" fullWidth value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
              <TextField label="Région" fullWidth value={formData.region} onChange={(e) => setFormData({ ...formData, region: e.target.value })} />
              <TextField label="Pays" fullWidth value={formData.country} onChange={(e) => setFormData({ ...formData, country: e.target.value })} />
              <TextField label="Latitude" type="number" fullWidth value={formData.latitude} onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })} />
              <TextField label="Longitude" type="number" fullWidth value={formData.longitude} onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })} />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Annuler</Button>
            <Button variant="contained" onClick={handleSave}>Sauvegarder</Button>
          </DialogActions>
        </Dialog>
      </ResponsivePageTemplate>
    </MainLayout>
  )
}
