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
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Receipt as ReceiptIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { paymentService } from '../services'

interface Payment {
  id: number
  trip: number
  ticket: number
  parcel?: number
  amount: number
  payment_method: string
  status: string
  transaction_id: string
  created_at: string
}

export const PaymentsPage: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterMethod, setFilterMethod] = useState('all')

  const [formData, setFormData] = useState({
    trip: 1,
    ticket: 1,
    parcel: undefined,
    amount: 5000,
    payment_method: 'cash',
    status: 'completed',
  })

  useEffect(() => {
    loadPayments()
  }, [filterStatus, filterMethod])

  const loadPayments = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (filterStatus !== 'all') params.status = filterStatus
      if (filterMethod !== 'all') params.payment_method = filterMethod
      const response = await paymentService.list(params)
      setPayments(response.data.results || response.data)
    } catch (error) {
      console.error('Erreur:', error)
    }
    setLoading(false)
  }

  const handleOpenDialog = (payment?: Payment) => {
    if (payment) {
      setEditingId(payment.id)
      setFormData({
        trip: payment.trip,
        ticket: payment.ticket,
        parcel: payment.parcel,
        amount: payment.amount,
        payment_method: payment.payment_method,
        status: payment.status,
      })
    } else {
      setEditingId(null)
      setFormData({
        trip: 1,
        ticket: 1,
        parcel: undefined,
        amount: 5000,
        payment_method: 'cash',
        status: 'completed',
      })
    }
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingId(null)
  }

  const handleSavePayment = async () => {
    try {
      if (editingId) {
        await paymentService.update(editingId, formData)
      } else {
        await paymentService.create(formData)
      }
      handleCloseDialog()
      loadPayments()
    } catch (error) {
      console.error('Erreur:', error)
    }
  }

  const handleDeletePayment = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await paymentService.delete(id)
        loadPayments()
      } catch (error) {
        console.error('Erreur:', error)
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'pending': return 'warning'
      case 'failed': return 'error'
      case 'refunded': return 'info'
      default: return 'default'
    }
  }

  const filteredPayments = payments.filter(payment =>
    payment.transaction_id.toLowerCase().includes(search.toLowerCase())
  )

  const totalAmount = filteredPayments.reduce((sum, p) => sum + p.amount, 0)
  const completedAmount = filteredPayments
    .filter(p => p.status === 'completed')
    .reduce((sum, p) => sum + p.amount, 0)

  return (
    <MainLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
          Gestion des Paiements
        </Typography>

        {/* Stats Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Total paiements
                </Typography>
                <Typography variant="h4">{payments.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Montant total
                </Typography>
                <Typography variant="h4">
                  {totalAmount.toLocaleString()} CFA
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Complétés
                </Typography>
                <Typography variant="h4">
                  {payments.filter(p => p.status === 'completed').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
              <CardContent>
                <Typography color="inherit" gutterBottom variant="overline">
                  Montant complété
                </Typography>
                <Typography variant="h4">
                  {completedAmount.toLocaleString()} CFA
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Card sx={{ mb: 3, p: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              label="Rechercher transaction"
              variant="outlined"
              size="small"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ flex: 1 }}
            />
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Statut</InputLabel>
              <Select
                value={filterStatus}
                label="Statut"
                onChange={(e) => setFilterStatus(e.target.value)}
                size="small"
              >
                <option value="all">Tous</option>
                <option value="completed">Complétés</option>
                <option value="pending">En attente</option>
                <option value="failed">Échoués</option>
                <option value="refunded">Remboursés</option>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Méthode</InputLabel>
              <Select
                value={filterMethod}
                label="Méthode"
                onChange={(e) => setFilterMethod(e.target.value)}
                size="small"
              >
                <option value="all">Tous</option>
                <option value="cash">Espèces</option>
                <option value="card">Carte</option>
                <option value="mobile">Mobile</option>
                <option value="bank">Banque</option>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
              sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
            >
              Ajouter paiement
            </Button>
          </Stack>
        </Card>

        {/* Payments Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead sx={{ backgroundColor: '#f5f6fa' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>ID Transaction</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Montant</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Méthode</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Statut</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredPayments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography color="textSecondary">Aucun paiement trouvé</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredPayments.map((payment) => (
                  <TableRow key={payment.id} hover>
                    <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                      {payment.transaction_id}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>
                      {payment.amount.toLocaleString()} CFA
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={payment.payment_method}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={payment.status}
                        size="small"
                        color={getStatusColor(payment.status) as any}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(payment.created_at).toLocaleDateString('fr-FR')}
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={0.5} justifyContent="center">
                        <Button
                          size="small"
                          startIcon={<ReceiptIcon />}
                          onClick={() => console.log('Receipt', payment.id)}
                        />
                        <Button
                          size="small"
                          startIcon={<EditIcon />}
                          onClick={() => handleOpenDialog(payment)}
                        />
                        <Button
                          size="small"
                          color="error"
                          startIcon={<DeleteIcon />}
                          onClick={() => handleDeletePayment(payment.id)}
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
          {editingId ? 'Éditer paiement' : 'Ajouter un paiement'}
        </DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            label="Montant"
            type="number"
            variant="outlined"
            value={formData.amount}
            onChange={(e) => setFormData({ ...formData, amount: parseInt(e.target.value) })}
            fullWidth
          />
          <FormControl fullWidth>
            <InputLabel>Méthode de paiement</InputLabel>
            <Select
              value={formData.payment_method}
              label="Méthode de paiement"
              onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
            >
              <option value="cash">Espèces</option>
              <option value="card">Carte</option>
              <option value="mobile">Mobile</option>
              <option value="bank">Banque</option>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Statut</InputLabel>
            <Select
              value={formData.status}
              label="Statut"
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            >
              <option value="completed">Complété</option>
              <option value="pending">En attente</option>
              <option value="failed">Échoué</option>
              <option value="refunded">Remboursé</option>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Annuler</Button>
          <Button onClick={handleSavePayment} variant="contained">
            {editingId ? 'Mettre à jour' : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  )
}
