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
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { ResponsivePageTemplate, ResponsiveTable, ResponsiveFilters } from '../components'
import { responsiveStyles } from '../styles/responsiveStyles'
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

  const filteredPayments = payments.filter(
    (p) => p.reference.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <ResponsivePageTemplate
        title="Gestion des Paiements"
        subtitle="Consultez et gérez tous vos paiements"
        actions={[
          <Button key="add" variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
            Nouveau Paiement
          </Button>,
        ]}
      >
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <ResponsiveFilters
          fields={[
            { name: 'search', label: 'Référence', value: search, onChange: setSearch },
            {
              name: 'status',
              label: 'Statut',
              value: filterStatus,
              onChange: setFilterStatus,
              options: [
                { label: 'Tous', value: 'all' },
                { label: 'En attente', value: 'pending' },
                { label: 'Complété', value: 'completed' },
                { label: 'Échoué', value: 'failed' },
              ],
            },
          ]}
          onApply={() => loadPayments()}
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
              { key: 'reference', label: 'Référence' },
              { key: 'amount', label: 'Montant (FCFA)' },
              { key: 'method', label: 'Méthode' },
              {
                key: 'status',
                label: 'Statut',
                render: (val) => (
                  <Chip label={val} color={val === 'completed' ? 'success' : 'warning'} size="small" />
                ),
              },
              { key: 'created_at', label: 'Date' },
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
            data={filteredPayments}
            emptyMessage="Aucun paiement trouvé"
          />
        )}

        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>{editingId ? 'Éditer' : 'Nouveau paiement'}</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <Stack spacing={2}>
              <TextField label="Référence" fullWidth value={formData.reference} onChange={(e) => setFormData({ ...formData, reference: e.target.value })} />
              <TextField label="Montant (FCFA)" type="number" fullWidth value={formData.amount} onChange={(e) => setFormData({ ...formData, amount: parseInt(e.target.value) })} />
              <TextField label="Description" multiline rows={2} fullWidth value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
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
