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
    <MainLayout>
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

        {/* Filtres */}
        <Paper sx={{ p: 2, mb: 3, ...govStyles.contentCard }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="Rechercher (référence)"
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
                <option value="completed">Complété</option>
                <option value="pending">En attente</option>
                <option value="failed">Échoué</option>
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
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Référence</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="right">Montant</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Méthode</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Date</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }}>Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase' }} align="center">Actions</TableCell>
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
                      <TableCell sx={{ fontWeight: 500 }}>{payment.reference}</TableCell>
                      <TableCell align="right">
                        <Typography sx={{ fontWeight: 600, color: govStyles.colors.primary }}>
                          {payment.amount.toLocaleString('fr-FR')} CFA
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={payment.method === 'cash' ? 'Espèces' : payment.method === 'card' ? 'Carte' : 'Virement'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{new Date(payment.created_at).toLocaleDateString('fr-FR')}</TableCell>
                      <TableCell>
                        <Chip
                          label={getStatusLabel(payment.status)}
                          sx={{
                            backgroundColor: `${getStatusColor(payment.status)}20`,
                            color: getStatusColor(payment.status),
                            fontWeight: 600,
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
                            sx={{ color: govStyles.colors.primary }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(payment.id)}
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
