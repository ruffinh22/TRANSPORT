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
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
import { cityService } from '../services'

interface City {
  id: number
  name: string
  region: string
  population: number
  status: string
  coverage: number
  created_at: string
}

export const CitiesPage: React.FC = () => {
  const [cities, setCities] = useState<City[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table')

  const [formData, setFormData] = useState({
    name: '',
    region: '',
    population: 0,
    status: 'active',
    coverage: 0,
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
      console.error(err)
    }
    setLoading(false)
  }

  const handleOpenDialog = (city?: City) => {
    if (city) {
      setEditingId(city.id)
      setFormData({
        name: city.name,
        region: city.region,
        population: city.population,
        status: city.status,
        coverage: city.coverage,
      })
    } else {
      setEditingId(null)
      setFormData({
        name: '',
        region: '',
        population: 0,
        status: 'active',
        coverage: 0,
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

  const getCoverageColor = (coverage: number) => {
    if (coverage >= 80) return govStyles.colors.success
    if (coverage >= 50) return govStyles.colors.warning
    return govStyles.colors.danger
  }

  const filteredCities = cities.filter(
    (city) =>
      city.name.toLowerCase().includes(search.toLowerCase()) ||
      city.region.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <GovPageWrapper maxWidth="lg">
        <GovPageHeader
          title="Villes et Couverture"
          icon="🌍"
          subtitle="Gestion de la couverture géographique TKF"
          actions={[
            {
              label: 'Nouvelle Ville',
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
              label="Rechercher (ville/région)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              variant="outlined"
              size="small"
              fullWidth
              sx={{ maxWidth: { md: '300px' } }}
            />
            <Stack direction="row" spacing={1}>
              <Button
                variant={viewMode === 'table' ? 'contained' : 'outlined'}
                onClick={() => setViewMode('table')}
                size="small"
                sx={viewMode === 'table' ? govStyles.govButton.primary : {}}
              >
                📊 Tableau
              </Button>
              <Button
                variant={viewMode === 'grid' ? 'contained' : 'outlined'}
                onClick={() => setViewMode('grid')}
                size="small"
                sx={viewMode === 'grid' ? govStyles.govButton.primary : {}}
              >
                📋 Cartes
              </Button>
            </Stack>
            <Button
              variant="contained"
              onClick={() => {
                setSearch('')
                loadCities()
              }}
              sx={govStyles.govButton.secondary}
            >
              Réinitialiser
            </Button>
          </Stack>
        </Paper>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
            <CircularProgress sx={{ color: govStyles.colors.success }} />
          </Box>
        ) : viewMode === 'table' ? (
          /* Vue Tableau */
          <TableContainer component={Paper} sx={govStyles.contentCard}>
            <Table sx={govStyles.table}>
              <TableHead>
                <TableRow sx={{ backgroundColor: govStyles.colors.success }}>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Ville</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Région</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="right">Population</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Couverture</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredCities.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4, color: '#999' }}>
                      Aucune ville trouvée
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredCities.map((city) => (
                    <TableRow key={city.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' }, borderLeft: `4px solid ${govStyles.colors.success}` }}>
                      <TableCell sx={{ fontWeight: 600 }}>{city.name}</TableCell>
                      <TableCell>{city.region}</TableCell>
                      <TableCell align="right">
                        {city.population.toLocaleString('fr-FR')}
                      </TableCell>
                      <TableCell align="center">
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 1,
                          }}
                        >
                          <Box
                            sx={{
                              width: '100%',
                              maxWidth: '80px',
                              height: '8px',
                              backgroundColor: '#e0e0e0',
                              borderRadius: '4px',
                              overflow: 'hidden',
                            }}
                          >
                            <Box
                              sx={{
                                height: '100%',
                                width: `${city.coverage}%`,
                                backgroundColor: getCoverageColor(city.coverage),
                                transition: 'width 0.3s',
                              }}
                            />
                          </Box>
                          <Typography variant="caption" sx={{ fontWeight: 700, minWidth: '35px' }}>
                            {city.coverage}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={city.status === 'active' ? 'Active' : 'Inactive'}
                          color={city.status === 'active' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} justifyContent="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleOpenDialog(city)}
                            sx={{ color: govStyles.colors.success }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(city.id)}
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
        ) : (
          /* Vue Grille */
          <Grid container spacing={3}>
            {filteredCities.length === 0 ? (
              <Grid item xs={12}>
                <Typography align="center" sx={{ color: '#999', py: 4 }}>
                  Aucune ville trouvée
                </Typography>
              </Grid>
            ) : (
              filteredCities.map((city) => (
                <Grid item xs={12} sm={6} md={4} key={city.id}>
                  <Card
                    sx={{
                      borderLeft: `5px solid ${govStyles.colors.success}`,
                      borderRadius: 2,
                      transition: 'all 0.3s',
                      '&:hover': {
                        boxShadow: 3,
                        transform: 'translateY(-2px)',
                      },
                      height: '100%',
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 700, color: govStyles.colors.success }}>
                          🌍 {city.name}
                        </Typography>
                        <Chip
                          label={city.status === 'active' ? 'Active' : 'Inactive'}
                          color={city.status === 'active' ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>

                      <Typography variant="body2" sx={{ color: '#666', mb: 2 }}>
                        <strong>Région:</strong> {city.region}
                      </Typography>

                      <Typography variant="body2" sx={{ color: '#666', mb: 3 }}>
                        <strong>Population:</strong> {city.population.toLocaleString('fr-FR')}
                      </Typography>

                      {/* Barre Couverture */}
                      <Box sx={{ mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="caption" sx={{ fontWeight: 600 }}>
                            Couverture
                          </Typography>
                          <Typography variant="caption" sx={{ fontWeight: 700, color: getCoverageColor(city.coverage) }}>
                            {city.coverage}%
                          </Typography>
                        </Box>
                        <Box
                          sx={{
                            width: '100%',
                            height: '8px',
                            backgroundColor: '#e0e0e0',
                            borderRadius: '4px',
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              height: '100%',
                              width: `${city.coverage}%`,
                              backgroundColor: getCoverageColor(city.coverage),
                            }}
                          />
                        </Box>
                      </Box>

                      {/* Actions */}
                      <Stack direction="row" spacing={1} justifyContent="flex-end">
                        <Button
                          size="small"
                          variant="contained"
                          onClick={() => handleOpenDialog(city)}
                          sx={govStyles.govButton.primary}
                        >
                          ✏️ Éditer
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleDelete(city.id)}
                          sx={{
                            borderColor: govStyles.colors.danger,
                            color: govStyles.colors.danger,
                            '&:hover': {
                              backgroundColor: `${govStyles.colors.danger}10`,
                            },
                          }}
                        >
                          🗑️
                        </Button>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        )}

        {/* Dialog Form */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle sx={{ backgroundColor: govStyles.colors.success, color: 'white', fontWeight: 700 }}>
            {editingId ? '✏️ Éditer la ville' : '➕ Nouvelle ville'}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Stack spacing={2}>
              <TextField
                label="Nom de la ville"
                fullWidth
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
              <TextField
                label="Région"
                fullWidth
                value={formData.region}
                onChange={(e) => setFormData({ ...formData, region: e.target.value })}
              />
              <TextField
                label="Population"
                type="number"
                fullWidth
                value={formData.population}
                onChange={(e) => setFormData({ ...formData, population: parseInt(e.target.value) })}
              />
              <TextField
                label="Couverture (%)"
                type="number"
                fullWidth
                inputProps={{ min: 0, max: 100 }}
                value={formData.coverage}
                onChange={(e) => setFormData({ ...formData, coverage: parseInt(e.target.value) })}
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

        <GovPageFooter text="Système de Gestion du Transport - Couverture Géographique" />
      </GovPageWrapper>
    </MainLayout>
  )
}
