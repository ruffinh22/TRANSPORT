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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  useTheme,
  useMediaQuery,
  Grid,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
import { paymentService } from '../services'

interface Payment {
  id: number
  reference: string
  amount: number
  method: string
  status: string
  created_at: string
  description: string
}

export const PaymentsPage: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    reference: '',
    amount: 0,
    method: 'cash',
    status: 'pending',
    description: '',
  })

  useEffect(() => {
    loadPayments()
  }, [filterStatus])

  const loadPayments = async () => {
    setLoading(true)
    try {
      const params = filterStatus !== 'all' ? { status: filterStatus } : {}
      const response = await paymentService.list(params)
      setPayments(response.data.results || response.data || [])
      setError(null)
    } catch (err) {
      setError('Erreur au chargement des paiements')
      console.error(err)
    }
    setLoading(false)
  }

  const handleOpenDialog = (payment?: Payment) => {
    if (payment) {
      setEditingId(payment.id)
      setFormData({
        reference: payment.reference,
        amount: payment.amount,
        method: payment.method,
        status: payment.status,
        description: payment.description,
      })
    } else {
      setEditingId(null)
      setFormData({
        reference: '',
        amount: 0,
        method: 'cash',
        status: 'pending',
        description: '',
      })
    }
    setOpenDialog(true)
  }

  const handleSave = async () => {
    try {
      if (editingId) {
        await paymentService.update(editingId, formData)
      } else {
        await paymentService.create(formData)
      }
      await loadPayments()
      setOpenDialog(false)
    } catch (err) {
      setError('Erreur lors de la sauvegarde')
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await paymentService.delete(id)
        await loadPayments()
      } catch (err) {
        setError('Erreur lors de la suppression')
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return govStyles.colors.success // Vert
      case 'pending':
        return govStyles.colors.warning // Or
      case 'failed':
        return govStyles.colors.danger // Rouge
      default:
        return govStyles.colors.neutral
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Complété'
      case 'pending':
        return 'En attente'
      case 'failed':
        return 'Échoué'
      default:
        return status
    }
  }

  const filteredPayments = payments.filter(
    (payment) =>
      payment.reference.toLowerCase().includes(search.toLowerCase()) ||
      payment.description.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout hideGovernmentHeader={true}>
      <GovPageWrapper maxWidth="lg">
        <GovPageHeader
          title="Gestion des Paiements"
          icon="💳"
          subtitle="Suivi des transactions et paiements"
          actions={[
            {
              label: 'Nouveau Paiement',
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
              label="Rechercher (référence)"
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
                <MenuItem value="completed">Complété</MenuItem>
                <MenuItem value="pending">En attente</MenuItem>
                <MenuItem value="failed">Échoué</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              onClick={() => {
                setSearch('')
                setFilterStatus('all')
                loadPayments()
              }}
              sx={govStyles.govButton.secondary}
              fullWidth={isMobile}
            >
              Réinitialiser
            </Button>
          </Stack>
        </Paper>

        {/* LAYOUT RESPONSIVE - CARDS MOBILE / TABLE DESKTOP */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
            <CircularProgress sx={{ color: govStyles.colors.primary }} />
          </Box>
        ) : isMobile ? (
          <Box sx={{ width: '100%', px: { xs: 1, sm: 0 } }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 1, sm: 1.5, md: 2 }, margin: '0 auto', maxWidth: { xs: '90%', sm: '100%' } }}>
              {filteredPayments.length === 0 ? (
                <Paper sx={{ p: 4, textAlign: 'center', color: '#999' }}>
                  Aucun paiement trouvé
                </Paper>
              ) : (
                filteredPayments.map((payment) => (
                  <Card key={payment.id} sx={{
                    p: { xs: 1, sm: 1.5, md: 2 },
                    borderLeft: '4px solid #003D66',
                    backgroundColor: '#f9f9f9',
                    '&:hover': {
                      boxShadow: '0 4px 8px rgba(0, 61, 102, 0.15)',
                      backgroundColor: '#fafafa'
                    }
                  }}>
                    <Stack spacing={{ xs: 1, sm: 1.5 }}>
                      {/* Header */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: { xs: '0.85rem', sm: '0.95rem' }, color: govStyles.colors.primary }}>
                            💳 {payment.reference}
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.75rem', sm: '0.8rem' }, color: '#666' }}>
                            {new Date(payment.created_at).toLocaleDateString('fr-FR')}
                          </Typography>
                        </Box>
                        <Chip
                          label={getStatusLabel(payment.status)}
                          sx={{
                            backgroundColor: `${getStatusColor(payment.status)}20`,
                            color: getStatusColor(payment.status),
                            fontWeight: 700,
                            fontSize: { xs: '0.65rem', sm: '0.75rem' },
                            height: 'auto',
                            padding: '2px 8px'
                          }}
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
                            Montant
                          </Typography>
                          <Typography sx={{ fontSize: { xs: '0.8rem', sm: '0.85rem' }, color: govStyles.colors.primary, fontWeight: 600 }}>
                            {payment.amount.toLocaleString('fr-FR')} CFA
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' }, fontWeight: 600, color: '#666' }}>
                            Méthode
                          </Typography>
                          <Typography sx={{ fontSize: { xs: '0.8rem', sm: '0.85rem' }, color: '#000' }}>
                            {payment.method === 'cash' ? 'Espèces' : payment.method === 'card' ? 'Carte' : 'Virement'}
                          </Typography>
                        </Box>
                      </Box>

                      {/* Actions */}
                      <Stack direction="row" spacing={1} sx={{ pt: 1 }}>
                        <Button
                          variant="outlined"
                          onClick={() => handleOpenDialog(payment)}
                          fullWidth
                          size="small"
                          sx={{
                            fontSize: { xs: '0.75rem', sm: '0.8rem' },
                            py: { xs: 0.75, sm: 1 },
                            color: govStyles.colors.primary,
                            borderColor: govStyles.colors.primary,
                            '&:hover': { backgroundColor: 'rgba(0, 61, 102, 0.05)' }
                          }}
                        >
                          ✏️ Éditer
                        </Button>
                        <Button
                          variant="outlined"
                          color="error"
                          onClick={() => handleDelete(payment.id)}
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
        ) : (
          // TABLE DESKTOP RESPONSIVE
          <TableContainer component={Paper} sx={govStyles.contentCard}>
            <Table sx={govStyles.table}>
              <TableHead>
                <TableRow sx={{ backgroundColor: govStyles.colors.primary }}>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Référence</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }} align="right">Montant</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Méthode</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Date</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }} align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPayments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4, color: '#999' }}>
                      Aucun paiement trouvé
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredPayments.map((payment) => (
                    <TableRow key={payment.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                      <TableCell sx={{ fontWeight: 500, fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>{payment.reference}</TableCell>
                      <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        <Typography sx={{ fontWeight: 600, color: govStyles.colors.primary }}>
                          {payment.amount.toLocaleString('fr-FR')} CFA
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        <Chip
                          label={payment.method === 'cash' ? 'Espèces' : payment.method === 'card' ? 'Carte' : 'Virement'}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.8rem' } }}
                        />
                      </TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>{new Date(payment.created_at).toLocaleDateString('fr-FR')}</TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        <Chip
                          label={getStatusLabel(payment.status)}
                          sx={{
                            backgroundColor: `${getStatusColor(payment.status)}20`,
                            color: getStatusColor(payment.status),
                            fontWeight: 600,
                            fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.8rem' }
                          }}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} justifyContent="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleOpenDialog(payment)}
                            sx={{ color: govStyles.colors.primary, fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' } }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(payment.id)}
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
        )}

        {/* Dialog Form */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle sx={{ backgroundColor: govStyles.colors.primary, color: 'white', fontWeight: 700 }}>
            {editingId ? '✏️ Éditer le paiement' : '➕ Nouveau paiement'}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Stack spacing={2}>
              <TextField
                label="Référence"
                fullWidth
                value={formData.reference}
                onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                variant="outlined"
              />
              <TextField
                label="Montant (FCFA)"
                type="number"
                fullWidth
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
              />
              <FormControl fullWidth>
                <InputLabel>Méthode</InputLabel>
                <Select
                  label="Méthode"
                  value={formData.method}
                  onChange={(e) => setFormData({ ...formData, method: e.target.value })}
                >
                  <option value="cash">Espèces</option>
                  <option value="card">Carte</option>
                  <option value="transfer">Virement</option>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Statut</InputLabel>
                <Select
                  label="Statut"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="pending">En attente</option>
                  <option value="completed">Complété</option>
                  <option value="failed">Échoué</option>
                </Select>
              </FormControl>
              <TextField
                label="Description"
                fullWidth
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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

        <GovPageFooter text="Système de Gestion du Transport - Gestion des Paiements" />
      </GovPageWrapper>
    </MainLayout>
  )
}
