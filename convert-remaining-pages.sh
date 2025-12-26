#!/bin/bash

# Convertir toutes les pages restantes

PAGES_DIR="/home/lidruf/TRANSPORT/frontend/src/pages"

# PaymentsPage
cat > "$PAGES_DIR/PaymentsPage.tsx" << 'EOF'
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
EOF

echo "✅ PaymentsPage"

# EmployeesPage
cat > "$PAGES_DIR/EmployeesPage.tsx" << 'EOF'
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
import { employeeService } from '../services'

interface Employee {
  id: number
  first_name: string
  last_name: string
  email: string
  phone: string
  role: string
  status: string
  created_at: string
}

export const EmployeesPage: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    role: 'driver',
    status: 'active',
  })

  useEffect(() => {
    loadEmployees()
  }, [filterStatus])

  const loadEmployees = async () => {
    setLoading(true)
    try {
      const params = filterStatus !== 'all' ? { status: filterStatus } : {}
      const response = await employeeService.list(params)
      setEmployees(response.data.results || response.data || [])
      setError(null)
    } catch (err) {
      setError('Erreur au chargement des employés')
    }
    setLoading(false)
  }

  const handleOpenDialog = (employee?: Employee) => {
    if (employee) {
      setEditingId(employee.id)
      setFormData({
        first_name: employee.first_name,
        last_name: employee.last_name,
        email: employee.email,
        phone: employee.phone,
        role: employee.role,
        status: employee.status,
      })
    } else {
      setEditingId(null)
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        role: 'driver',
        status: 'active',
      })
    }
    setOpenDialog(true)
  }

  const handleSave = async () => {
    try {
      if (editingId) {
        await employeeService.update(editingId, formData)
      } else {
        await employeeService.create(formData)
      }
      await loadEmployees()
      setOpenDialog(false)
    } catch (err) {
      setError('Erreur lors de la sauvegarde')
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Êtes-vous sûr?')) {
      try {
        await employeeService.delete(id)
        await loadEmployees()
      } catch (err) {
        setError('Erreur lors de la suppression')
      }
    }
  }

  const filteredEmployees = employees.filter(
    (e) => e.first_name.toLowerCase().includes(search.toLowerCase()) || e.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout>
      <ResponsivePageTemplate
        title="Gestion des Employés"
        subtitle="Consultez et gérez votre équipe"
        actions={[
          <Button key="add" variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
            Ajouter Employé
          </Button>,
        ]}
      >
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <ResponsiveFilters
          fields={[
            { name: 'search', label: 'Nom/Email', value: search, onChange: setSearch },
            {
              name: 'status',
              label: 'Statut',
              value: filterStatus,
              onChange: setFilterStatus,
              options: [
                { label: 'Tous', value: 'all' },
                { label: 'Actifs', value: 'active' },
                { label: 'Inactifs', value: 'inactive' },
              ],
            },
          ]}
          onApply={() => loadEmployees()}
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
              { key: 'first_name', label: 'Prénom' },
              { key: 'last_name', label: 'Nom' },
              { key: 'email', label: 'Email' },
              { key: 'phone', label: 'Téléphone' },
              { key: 'role', label: 'Rôle' },
              {
                key: 'status',
                label: 'Statut',
                render: (val) => <Chip label={val} color={val === 'active' ? 'success' : 'default'} size="small" />,
              },
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
            data={filteredEmployees}
            emptyMessage="Aucun employé trouvé"
          />
        )}

        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>{editingId ? 'Éditer' : 'Ajouter employé'}</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <Stack spacing={2}>
              <TextField label="Prénom" fullWidth value={formData.first_name} onChange={(e) => setFormData({ ...formData, first_name: e.target.value })} />
              <TextField label="Nom" fullWidth value={formData.last_name} onChange={(e) => setFormData({ ...formData, last_name: e.target.value })} />
              <TextField label="Email" type="email" fullWidth value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
              <TextField label="Téléphone" fullWidth value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} />
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
EOF

echo "✅ EmployeesPage"

# CitiesPage
cat > "$PAGES_DIR/CitiesPage.tsx" << 'EOF'
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
EOF

echo "✅ CitiesPage"

echo ""
echo "🎉 Toutes les pages restantes sont maintenant TOTALEMENT RESPONSIVE!"
