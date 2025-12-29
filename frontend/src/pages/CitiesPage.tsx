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
  useTheme,
  useMediaQuery,
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
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

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
    <MainLayout hideGovernmentHeader={true}>
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

        {/* Filtres - ULTRA RESPONSIVE */}
        <Paper sx={{ p: { xs: 1.5, sm: 2, md: 2 }, mb: { xs: 2, sm: 3, md: 3 }, ...govStyles.contentCard }}>
          <Stack direction={{ xs: 'column', sm: 'column', md: 'row' }} spacing={{ xs: 1.5, sm: 2, md: 2 }} sx={{ alignItems: { xs: 'stretch', sm: 'stretch', md: 'center' } }}>
            <TextField
              label="Rechercher (ville/région)"
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
            <Stack direction="row" spacing={1} sx={{ width: { xs: '100%', md: 'auto' } }}>
              <Button
                variant={viewMode === 'table' ? 'contained' : 'outlined'}
                onClick={() => setViewMode('table')}
                size="small"
                fullWidth={isMobile}
                sx={viewMode === 'table' ? govStyles.govButton.primary : {}}
              >
                📊 Tableau
              </Button>
              <Button
                variant={viewMode === 'grid' ? 'contained' : 'outlined'}
                onClick={() => setViewMode('grid')}
                size="small"
                fullWidth={isMobile}
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
              fullWidth={isMobile}
            >
              Réinitialiser
            </Button>
          </Stack>
        </Paper>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
            <CircularProgress sx={{ color: govStyles.colors.success }} />
          </Box>
        ) : isMobile ? (
          /* Vue CARTES MOBILE (auto sur mobile) */
          <Box sx={{ width: '100%', px: { xs: 1, sm: 0 } }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 1, sm: 1.5, md: 2 }, margin: '0 auto', maxWidth: { xs: '90%', sm: '100%' } }}>
              {filteredCities.length === 0 ? (
                <Paper sx={{ p: 4, textAlign: 'center', color: '#999' }}>
                  Aucune ville trouvée
                </Paper>
              ) : (
                filteredCities.map((city) => (
                    <Card sx={{
                      borderLeft: `5px solid ${govStyles.colors.success}`,
                      p: { xs: 1, sm: 1.5, md: 2 },
                    backgroundColor: '#f9f9f9',
                    '&:hover': {
                      boxShadow: '0 4px 8px rgba(0, 122, 94, 0.15)',
                      backgroundColor: '#fafafa'
                    }
                  }}>
                    <Stack spacing={{ xs: 1, sm: 1.5 }}>
                      {/* Header */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: { xs: '0.85rem', sm: '0.95rem' }, color: govStyles.colors.success }}>
                            🌍 {city.name}
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.75rem', sm: '0.8rem' }, color: '#666' }}>
                            {city.region}
                          </Typography>
                        </Box>
                        <Chip
                          label={city.status === 'active' ? 'Actif' : 'Inactif'}
                          color={city.status === 'active' ? 'success' : 'default'}
                          size="small"
                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                        />
                      </Box>

                      {/* Info Grid 2x2 */}
                      <Box sx={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: { xs: 1, sm: 1.5 },
                        backgroundColor: '#fff',
                        p: { xs: 1, sm: 1.5 },
                        borderRadius: 1
                      }}>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' }, fontWeight: 600, color: '#666' }}>
                            Population
                          </Typography>
                          <Typography sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem' }, color: '#000', fontWeight: 500 }}>
                            {(city.population / 1000).toFixed(1)}k
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' }, fontWeight: 600, color: '#666' }}>
                            Couverture
                          </Typography>
                          <Typography sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem' }, color: getCoverageColor(city.coverage), fontWeight: 600 }}>
                            {city.coverage}%
                          </Typography>
                        </Box>
                      </Box>

                      {/* Progress Bar */}
                      <Box sx={{
                        width: '100%',
                        height: '6px',
                        backgroundColor: '#e0e0e0',
                        borderRadius: '3px',
                        overflow: 'hidden'
                      }}>
                        <Box
                          sx={{
                            height: '100%',
                            width: `${city.coverage}%`,
                            backgroundColor: getCoverageColor(city.coverage),
                            transition: 'width 0.3s'
                          }}
                        />
                      </Box>

                      {/* Actions */}
                      <Stack direction="row" spacing={1} sx={{ pt: 1 }}>
                        <Button
                          variant="outlined"
                          onClick={() => handleOpenDialog(city)}
                          fullWidth
                          size="small"
                          sx={{
                            fontSize: { xs: '0.75rem', sm: '0.8rem' },
                            py: { xs: 0.75, sm: 1 },
                            color: govStyles.colors.success,
                            borderColor: govStyles.colors.success,
                            '&:hover': { backgroundColor: 'rgba(0, 122, 94, 0.05)' }
                          }}
                        >
                          ✏️ Éditer
                        </Button>
                        <Button
                          variant="outlined"
                          color="error"
                          onClick={() => handleDelete(city.id)}
                          fullWidth
                          size="small"
                          sx={{
                            fontSize: { xs: '0.75rem', sm: '0.8rem' },
                            py: { xs: 0.75, sm: 1 }
                          }}
                        >
                          🗑️ Supprimer
                        </Button>
                      </Stack>
                    </Stack>
                    </Card>
                ))
              )}
            </Box>
          </Box>
        ) : viewMode === 'table' ? (
          /* Vue TABLEAU DESKTOP */
          <TableContainer component={Paper} sx={govStyles.contentCard}>
            <Table sx={govStyles.table}>
              <TableHead>
                <TableRow sx={{ backgroundColor: govStyles.colors.success }}>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Ville</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Région</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }} align="right">Population</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }} align="center">Couverture</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }} align="center">Actions</TableCell>
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
                      <TableCell sx={{ fontWeight: 600, fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>{city.name}</TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>{city.region}</TableCell>
                      <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        {city.population.toLocaleString('fr-FR')}
                      </TableCell>
                      <TableCell align="center" sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                          <Box sx={{
                            width: '100%',
                            maxWidth: '80px',
                            height: '8px',
                            backgroundColor: '#e0e0e0',
                            borderRadius: '4px',
                            overflow: 'hidden',
                          }}>
                            <Box sx={{
                              height: '100%',
                              width: `${city.coverage}%`,
                              backgroundColor: getCoverageColor(city.coverage),
                              transition: 'width 0.3s',
                            }} />
                          </Box>
                          <Typography variant="caption" sx={{ fontWeight: 700, minWidth: '35px', fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.8rem' } }}>
                            {city.coverage}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        <Chip
                          label={city.status === 'active' ? 'Actif' : 'Inactif'}
                          color={city.status === 'active' ? 'success' : 'default'}
                          size="small"
                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.8rem' } }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} justifyContent="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleOpenDialog(city)}
                            sx={{ color: govStyles.colors.success, fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' } }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(city.id)}
                            sx={{ color: govStyles.colors.danger, fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' } }}
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
          /* Vue GRILLE DESKTOP */
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' }, gap: { xs: 1.5, sm: 2, md: 3 } }}>
            {filteredCities.length === 0 ? (
              <Typography align="center" sx={{ color: '#999', py: 4, gridColumn: '1 / -1' }}>
                Aucune ville trouvée
              </Typography>
            ) : (
              filteredCities.map((city) => (
                  <Card sx={{
                    borderLeft: `5px solid ${govStyles.colors.success}`,
                    borderRadius: 2,
                    transition: 'all 0.3s',
                    '&:hover': {
                      boxShadow: 3,
                      transform: 'translateY(-2px)',
                    },
                    height: '100%',
                  }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 700, color: govStyles.colors.success, fontSize: { xs: '0.95rem', sm: '1.1rem', md: '1.25rem' } }}>
                          🌍 {city.name}
                        </Typography>
                        <Chip
                          label={city.status === 'active' ? 'Actif' : 'Inactif'}
                          color={city.status === 'active' ? 'success' : 'default'}
                          size="small"
                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.8rem' } }}
                        />
                      </Box>

                      <Typography variant="body2" sx={{ color: '#666', mb: 2, fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' } }}>
                        <strong>Région:</strong> {city.region}
                      </Typography>

                      <Typography variant="body2" sx={{ color: '#666', mb: 3, fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' } }}>
                        <strong>Population:</strong> {city.population.toLocaleString('fr-FR')}
                      </Typography>

                      {/* Barre Couverture */}
                      <Box sx={{ mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="caption" sx={{ fontWeight: 600, fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.8rem' } }}>
                            Couverture
                          </Typography>
                          <Typography variant="caption" sx={{ fontWeight: 700, color: getCoverageColor(city.coverage), fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.8rem' } }}>
                            {city.coverage}%
                          </Typography>
                        </Box>
                        <Box sx={{
                          width: '100%',
                          height: '8px',
                          backgroundColor: '#e0e0e0',
                          borderRadius: '4px',
                          overflow: 'hidden',
                        }}>
                          <Box sx={{
                            height: '100%',
                            width: `${city.coverage}%`,
                            backgroundColor: getCoverageColor(city.coverage),
                          }} />
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
                ))
              )}
            </Box>
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
