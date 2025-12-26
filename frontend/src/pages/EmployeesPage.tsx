import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Paper,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../hooks';
import { api } from '../services/api';

interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: string;
  hire_date: string;
  salary: number;
  status: string;
  city: string;
  document_id: string;
  avatar?: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`employee-tabpanel-${index}`}
      aria-labelledby={`employee-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const EmployeesPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [filteredEmployees, setFilteredEmployees] = useState<Employee[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    on_leave: 0,
    drivers: 0,
    receivers: 0,
    cashiers: 0,
    controllers: 0,
    mail_agents: 0,
  });

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    role: 'driver',
    hire_date: new Date().toISOString().split('T')[0],
    salary: 0,
    status: 'active',
    city: '',
    document_id: '',
  });

  const roles = [
    { value: 'driver', label: 'Chauffeur' },
    { value: 'receiver', label: 'Receveur' },
    { value: 'cashier', label: 'Guichetier' },
    { value: 'controller', label: 'Contrôleur' },
    { value: 'mail_agent', label: 'Agent Courrier' },
    { value: 'admin', label: 'Administrateur' },
  ];

  const statuses = [
    { value: 'active', label: 'Actif' },
    { value: 'on_leave', label: 'En congé' },
    { value: 'suspended', label: 'Suspendu' },
    { value: 'retired', label: 'Retraité' },
  ];

  // Chargement des employés
  useEffect(() => {
    fetchEmployees();
  }, []);

  // Filtrage
  useEffect(() => {
    let filtered = employees;

    if (searchTerm) {
      filtered = filtered.filter(
        (emp) =>
          emp.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          emp.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          emp.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
          emp.phone.includes(searchTerm)
      );
    }

    if (selectedRole) {
      filtered = filtered.filter((emp) => emp.role === selectedRole);
    }

    if (selectedStatus) {
      filtered = filtered.filter((emp) => emp.status === selectedStatus);
    }

    setFilteredEmployees(filtered);
  }, [employees, searchTerm, selectedRole, selectedStatus]);

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      // Simuler l'appel API
      const mockEmployees: Employee[] = [
        {
          id: 1,
          first_name: 'Amadou',
          last_name: 'Diallo',
          email: 'amadou.diallo@tkf.com',
          phone: '+226 70 00 00 01',
          role: 'driver',
          hire_date: '2023-01-15',
          salary: 450000,
          status: 'active',
          city: 'Ouagadougou',
          document_id: 'ID001',
        },
        {
          id: 2,
          first_name: 'Fatoumata',
          last_name: 'Sow',
          email: 'fatoumata.sow@tkf.com',
          phone: '+226 70 00 00 02',
          role: 'receiver',
          hire_date: '2023-02-20',
          salary: 300000,
          status: 'active',
          city: 'Bobo-Dioulasso',
          document_id: 'ID002',
        },
        {
          id: 3,
          first_name: 'Ibrahim',
          last_name: 'Traore',
          email: 'ibrahim.traore@tkf.com',
          phone: '+226 70 00 00 03',
          role: 'cashier',
          hire_date: '2023-03-10',
          salary: 350000,
          status: 'active',
          city: 'Ouagadougou',
          document_id: 'ID003',
        },
        {
          id: 4,
          first_name: 'Marie',
          last_name: 'Dubois',
          email: 'marie.dubois@tkf.com',
          phone: '+226 70 00 00 04',
          role: 'controller',
          hire_date: '2023-04-05',
          salary: 320000,
          status: 'on_leave',
          city: 'Koudougou',
          document_id: 'ID004',
        },
        {
          id: 5,
          first_name: 'Ousmane',
          last_name: 'Ba',
          email: 'ousmane.ba@tkf.com',
          phone: '+226 70 00 00 05',
          role: 'mail_agent',
          hire_date: '2023-05-12',
          salary: 280000,
          status: 'active',
          city: 'Ouagadougou',
          document_id: 'ID005',
        },
      ];

      setEmployees(mockEmployees);

      // Calculer les stats
      const newStats = {
        total: mockEmployees.length,
        active: mockEmployees.filter((e) => e.status === 'active').length,
        on_leave: mockEmployees.filter((e) => e.status === 'on_leave').length,
        drivers: mockEmployees.filter((e) => e.role === 'driver').length,
        receivers: mockEmployees.filter((e) => e.role === 'receiver').length,
        cashiers: mockEmployees.filter((e) => e.role === 'cashier').length,
        controllers: mockEmployees.filter((e) => e.role === 'controller').length,
        mail_agents: mockEmployees.filter((e) => e.role === 'mail_agent').length,
      };
      setStats(newStats);
    } catch (err) {
      setError('Erreur lors du chargement des employés');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (employee?: Employee) => {
    if (employee) {
      setEditingEmployee(employee);
      setFormData({
        first_name: employee.first_name,
        last_name: employee.last_name,
        email: employee.email,
        phone: employee.phone,
        role: employee.role,
        hire_date: employee.hire_date,
        salary: employee.salary,
        status: employee.status,
        city: employee.city,
        document_id: employee.document_id,
      });
    } else {
      setEditingEmployee(null);
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        role: 'driver',
        hire_date: new Date().toISOString().split('T')[0],
        salary: 0,
        status: 'active',
        city: '',
        document_id: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingEmployee(null);
  };

  const handleSaveEmployee = async () => {
    try {
      if (editingEmployee) {
        // Mise à jour
        setEmployees(
          employees.map((emp) =>
            emp.id === editingEmployee.id
              ? { ...emp, ...formData }
              : emp
          )
        );
      } else {
        // Création
        const newEmployee: Employee = {
          id: Math.max(...employees.map((e) => e.id), 0) + 1,
          ...formData,
        };
        setEmployees([...employees, newEmployee]);
      }
      handleCloseDialog();
    } catch (err) {
      setError('Erreur lors de la sauvegarde');
    }
  };

  const handleDeleteEmployee = (id: number) => {
    setEmployees(employees.filter((emp) => emp.id !== id));
  };

  const getRoleLabel = (role: string) => {
    return roles.find((r) => r.value === role)?.label || role;
  };

  const getStatusLabel = (status: string) => {
    const statusMap: { [key: string]: { label: string; color: any } } = {
      active: { label: 'Actif', color: 'success' },
      on_leave: { label: 'En congé', color: 'warning' },
      suspended: { label: 'Suspendu', color: 'error' },
      retired: { label: 'Retraité', color: 'default' },
    };
    return statusMap[status] || { label: status, color: 'default' };
  };

  const handleExportPDF = () => {
    alert('Export PDF en cours de développement...');
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => window.history.back()}
          variant="outlined"
          size="small"
        >
          Retour
        </Button>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#CE1126' }}>
          ★ Gestion du Personnel TKF
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Statistiques */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #A00E1A 100%)', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Total</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ background: 'linear-gradient(135deg, #007A5E 0%, #004D3A 100%)', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Actifs</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.active}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Chauffeurs</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.drivers}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #FF69B4 100%)', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Guichetiers</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.cashiers}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ background: 'linear-gradient(135deg, #007A5E 0%, #20B2AA 100%)', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">Agents Courrier</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.mail_agents}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ background: 'linear-gradient(135deg, #FF6B6B 0%, #FF8C00 100%)', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6">En congé</Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {stats.on_leave}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Barre de filtre et actions */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              placeholder="Chercher par nom, email..."
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'gray' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Rôle</InputLabel>
              <Select
                value={selectedRole}
                label="Rôle"
                onChange={(e) => setSelectedRole(e.target.value)}
              >
                <MenuItem value="">Tous les rôles</MenuItem>
                {roles.map((role) => (
                  <MenuItem key={role.value} value={role.value}>
                    {role.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Statut</InputLabel>
              <Select
                value={selectedStatus}
                label="Statut"
                onChange={(e) => setSelectedStatus(e.target.value)}
              >
                <MenuItem value="">Tous les statuts</MenuItem>
                {statuses.map((status) => (
                  <MenuItem key={status.value} value={status.value}>
                    {status.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              fullWidth
              onClick={handleExportPDF}
            >
              Exporter PDF
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              fullWidth
              sx={{
                background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)',
              }}
              onClick={() => handleOpenDialog()}
            >
              Ajouter Employé
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Tableau des employés */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead sx={{ backgroundColor: '#CE1126' }}>
            <TableRow>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Employé</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Contact</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Rôle</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Ville</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Salaire</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Statut</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="center">
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredEmployees.map((employee) => (
              <TableRow key={employee.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)' }}>
                      {employee.first_name[0]}{employee.last_name[0]}
                    </Avatar>
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {employee.first_name} {employee.last_name}
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'gray' }}>
                        ID: {employee.document_id}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{employee.email}</Typography>
                  <Typography variant="caption" sx={{ color: 'gray' }}>
                    {employee.phone}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={getRoleLabel(employee.role)}
                    size="small"
                    sx={{
                      background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
                      color: 'white',
                    }}
                  />
                </TableCell>
                <TableCell>{employee.city}</TableCell>
                <TableCell sx={{ fontWeight: 'bold', color: '#CE1126' }}>
                  {employee.salary.toLocaleString()} FCFA
                </TableCell>
                <TableCell>
                  <Chip
                    label={getStatusLabel(employee.status).label}
                    size="small"
                    color={getStatusLabel(employee.status).color}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Voir détails">
                    <IconButton size="small" color="info">
                      <VisibilityIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Modifier">
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => handleOpenDialog(employee)}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Supprimer">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteEmployee(employee.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog d'ajout/modification */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)', color: 'white' }}>
          {editingEmployee ? 'Modifier Employé' : 'Ajouter un Nouvel Employé'}
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Stack spacing={2}>
            <TextField
              fullWidth
              label="Prénom"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Nom"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <TextField
              fullWidth
              label="Téléphone"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Rôle</InputLabel>
              <Select
                value={formData.role}
                label="Rôle"
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              >
                {roles.map((role) => (
                  <MenuItem key={role.value} value={role.value}>
                    {role.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Ville"
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
            />
            <TextField
              fullWidth
              label="Salaire mensuel (FCFA)"
              type="number"
              value={formData.salary}
              onChange={(e) => setFormData({ ...formData, salary: parseInt(e.target.value) })}
            />
            <TextField
              fullWidth
              label="Date d'embauche"
              type="date"
              InputLabelProps={{ shrink: true }}
              value={formData.hire_date}
              onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
            />
            <TextField
              fullWidth
              label="Numéro document d'identité"
              value={formData.document_id}
              onChange={(e) => setFormData({ ...formData, document_id: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Statut</InputLabel>
              <Select
                value={formData.status}
                label="Statut"
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              >
                {statuses.map((status) => (
                  <MenuItem key={status.value} value={status.value}>
                    {status.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseDialog}>Annuler</Button>
          <Button
            variant="contained"
            onClick={handleSaveEmployee}
            sx={{ background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)' }}
          >
            Enregistrer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EmployeesPage;
