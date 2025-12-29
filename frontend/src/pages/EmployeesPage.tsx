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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
} from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
import { employeeService } from '../services'

interface Employee {
  id: number
  first_name: string
  last_name: string
  email: string
  phone: string
  role: string
  status: string
  hire_date: string
  department: string
}

export const EmployeesPage: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table')

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    role: 'driver',
    status: 'active',
    hire_date: '',
    department: '',
  })

  useEffect(() => {
    loadEmployees()
  }, [filterStatus])

  const loadEmployees = async () => {
    setLoading(true)
    try {
      const params = filterStatus !== 'all' ? { status: filterStatus } : {}
      const response = await employeeService.list(params)
      
      // Extraire les données de manière sûre
      let data: Employee[] = []
      if (response.data && Array.isArray(response.data)) {
        data = response.data
      } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
        data = response.data.results
      }
      
      setEmployees(data)
      setError(null)
    } catch (err) {
      setError('Erreur au chargement des employés')
      console.error(err)
      setEmployees([])
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
        hire_date: employee.hire_date,
        department: employee.department,
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
        hire_date: '',
        department: '',
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

  const getRoleLabel = (role: string) => {
    const roles: { [key: string]: string } = {
      admin: 'Administrateur',
      manager: 'Gestionnaire',
      driver: 'Conducteur',
      staff: 'Personnel',
    }
    return roles[role] || role
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return govStyles.colors.danger
      case 'manager':
        return govStyles.colors.primary
      case 'driver':
        return govStyles.colors.success
      default:
        return govStyles.colors.neutral
    }
  }

  const filteredEmployees = employees.filter(
    (emp) =>
      emp.first_name.toLowerCase().includes(search.toLowerCase()) ||
      emp.last_name.toLowerCase().includes(search.toLowerCase()) ||
      emp.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <MainLayout hideGovernmentHeader={true}>
      <GovPageWrapper maxWidth="lg">
        <GovPageHeader
          title="Gestion Ressources Humaines"
          icon="👥"
          subtitle="Gestion des employés et équipes TKF"
          actions={[
            {
              label: 'Nouvel Employé',
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
              label="Rechercher (nom/email)"
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
                <MenuItem value="active">Actif</MenuItem>
                <MenuItem value="inactive">Inactif</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              onClick={() => {
                setSearch('')
                setFilterStatus('all')
                loadEmployees()
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
            <Grid container spacing={{ xs: 1, sm: 1.5, md: 2 }} sx={{ margin: '0 auto', maxWidth: { xs: '90%', sm: '100%' } }}>
              {filteredEmployees.length === 0 ? (
                <Grid item xs={12}>
                  <Paper sx={{ p: 4, textAlign: 'center', color: '#999' }}>
                    Aucun employé trouvé
                  </Paper>
                </Grid>
              ) : (
                filteredEmployees.map((emp) => (
                  <Grid item xs={12} key={emp.id}>
                    <Card sx={{
                      p: { xs: 1, sm: 1.5, md: 2 },
                    borderLeft: `4px solid ${getRoleColor(emp.role)}`,
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
                            👤 {emp.first_name} {emp.last_name}
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.75rem', sm: '0.8rem' }, color: '#666' }}>
                            {emp.email}
                          </Typography>
                        </Box>
                        <Chip
                          label={emp.status === 'active' ? 'Actif' : 'Inactif'}
                          color={emp.status === 'active' ? 'success' : 'default'}
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
                            Rôle
                          </Typography>
                          <Typography sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem' }, color: '#000' }}>
                            {getRoleLabel(emp.role)}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' }, fontWeight: 600, color: '#666' }}>
                            Téléphone
                          </Typography>
                          <Typography sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem' }, color: '#000' }}>
                            {emp.phone}
                          </Typography>
                        </Box>
                      </Box>

                      {/* Actions */}
                      <Stack direction="row" spacing={1} sx={{ pt: 1 }}>
                        <Button
                          variant="outlined"
                          onClick={() => handleOpenDialog(emp)}
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
                          onClick={() => handleDelete(emp.id)}
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
                </Grid>
              ))
            )}
          </Grid>
          </Box>
        ) : (
          // TABLE DESKTOP RESPONSIVE
          <TableContainer component={Paper} sx={govStyles.contentCard}>
            <Table sx={govStyles.table}>
              <TableHead>
                <TableRow sx={{ backgroundColor: govStyles.colors.primary }}>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Nom</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Email</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Téléphone</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Rôle</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }}>Statut</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 700, textTransform: 'uppercase', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.85rem' } }} align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredEmployees.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4, color: '#999' }}>
                      Aucun employé trouvé
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredEmployees.map((emp) => (
                    <TableRow key={emp.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                      <TableCell sx={{ fontWeight: 500, fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        {emp.first_name} {emp.last_name}
                      </TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>{emp.email}</TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>{emp.phone}</TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        <Chip
                          label={getRoleLabel(emp.role)}
                          sx={{
                            backgroundColor: `${getRoleColor(emp.role)}20`,
                            color: getRoleColor(emp.role),
                            fontWeight: 600,
                            fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.8rem' }
                          }}
                          size="small"
                        />
                      </TableCell>
                      <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' } }}>
                        <Chip
                          label={emp.status === 'active' ? 'Actif' : 'Inactif'}
                          color={emp.status === 'active' ? 'success' : 'default'}
                          size="small"
                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.8rem' } }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} justifyContent="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleOpenDialog(emp)}
                            sx={{ color: govStyles.colors.primary, fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' } }}
                          >
                            ✏️
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleDelete(emp.id)}
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
            {editingId ? '✏️ Éditer l\'employé' : '➕ Nouvel employé'}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Stack spacing={2}>
              <TextField
                label="Prénom"
                fullWidth
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              />
              <TextField
                label="Nom"
                fullWidth
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              />
              <TextField
                label="Email"
                type="email"
                fullWidth
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
              <TextField
                label="Téléphone"
                fullWidth
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
              <FormControl fullWidth>
                <InputLabel>Rôle</InputLabel>
                <Select
                  label="Rôle"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="admin">Administrateur</option>
                  <option value="manager">Gestionnaire</option>
                  <option value="driver">Conducteur</option>
                  <option value="staff">Personnel</option>
                </Select>
              </FormControl>
              <TextField
                label="Département"
                fullWidth
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              />
              <TextField
                label="Date d'embauche"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={formData.hire_date}
                onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
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

        <GovPageFooter text="Système de Gestion du Transport - Gestion Ressources Humaines" />
      </GovPageWrapper>
    </MainLayout>
  )
}
