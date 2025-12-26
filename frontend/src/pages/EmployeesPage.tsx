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
