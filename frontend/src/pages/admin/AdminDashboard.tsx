import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Container,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tab,
  Tabs,
  Alert,
  CircularProgress,
  Grid,
  Typography,
  Divider,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Visibility as ViewIcon,
  Lock as LockIcon,
  CheckCircle as ApproveIcon,
} from '@mui/icons-material';
import userManagementService from '../../services/userManagementService';

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
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  roles: string[];
  isActive: boolean;
  emailVerified: boolean;
  phoneVerified: boolean;
  lastLogin?: string;
  createdAt: string;
}

interface StatCard {
  title: string;
  value: number;
  color: string;
}

export const AdminDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    roleDistribution: {} as Record<string, number>,
  });

  // Form states
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    roles: [] as string[],
    isActive: true,
    password: '',
  });

  const roles = ['ADMIN', 'COMPTABLE', 'GUICHETIER', 'CHAUFFEUR', 'CONTROLEUR', 'GESTIONNAIRE_COURRIER', 'MANAGER'];

  // Load users
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await userManagementService.getAllUsers();
      setUsers(response);
      calculateStats(response);
    } catch (err) {
      setError('Erreur lors du chargement des utilisateurs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (userList: User[]) => {
    const roleDistribution: Record<string, number> = {};
    let activeCount = 0;

    userList.forEach((user) => {
      if (user.isActive) activeCount++;
      user.roles.forEach((role) => {
        roleDistribution[role] = (roleDistribution[role] || 0) + 1;
      });
    });

    setStats({
      totalUsers: userList.length,
      activeUsers: activeCount,
      roleDistribution,
    });
  };

  const handleOpenDialog = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        phone: user.phone || '',
        roles: user.roles,
        isActive: user.isActive,
        password: '',
      });
    } else {
      setEditingUser(null);
      setFormData({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        roles: [],
        isActive: true,
        password: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingUser(null);
  };

  const handleSaveUser = async () => {
    if (!formData.firstName || !formData.lastName || !formData.email || formData.roles.length === 0) {
      setError('Veuillez remplir tous les champs requis');
      return;
    }

    setLoading(true);
    setError('');

    try {
      if (editingUser) {
        // Update existing user
        await userManagementService.updateUser(editingUser.id, {
          firstName: formData.firstName,
          lastName: formData.lastName,
          phone: formData.phone,
          roles: formData.roles,
          isActive: formData.isActive,
        });
      } else {
        // Create new user
        await userManagementService.createUser({
          firstName: formData.firstName,
          lastName: formData.lastName,
          email: formData.email,
          phone: formData.phone,
          roles: formData.roles,
          password: formData.password,
        });
      }

      // Reload users
      await loadUsers();
      handleCloseDialog();
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la sauvegarde de l\'utilisateur');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      await userManagementService.deleteUser(userId);
      await loadUsers();
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la suppression de l\'utilisateur');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    setLoading(true);
    setError('');

    try {
      await userManagementService.deactivateUser(userId);
      await loadUsers();
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la désactivation de l\'utilisateur');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (userId: string) => {
    if (!window.confirm('Envoyer un email de réinitialisation de mot de passe ?')) {
      return;
    }

    setLoading(true);
    try {
      await userManagementService.adminResetUserPassword(userId);
      alert('Email de réinitialisation envoyé avec succès');
      setError('');
    } catch (err: any) {
      setError(err.message || 'Erreur lors de l\'envoi de l\'email');
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(
    (user) =>
      user.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const statCards: StatCard[] = [
    {
      title: 'Total Utilisateurs',
      value: stats.totalUsers,
      color: '#003D66',
    },
    {
      title: 'Utilisateurs Actifs',
      value: stats.activeUsers,
      color: '#007A5E',
    },
    {
      title: 'Total Rôles',
      value: Object.keys(stats.roleDistribution).length,
      color: '#CE1126',
    },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#003D66', mb: 2 }}>
          Tableau de Bord Administration
        </Typography>
        <Divider />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card sx={{ boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom sx={{ fontSize: '0.875rem' }}>
                  {stat.title}
                </Typography>
                <Typography variant="h4" sx={{ color: stat.color, fontWeight: 'bold' }}>
                  {stat.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Tabs */}
      <Card>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          aria-label="admin-tabs"
          sx={{
            borderBottom: '1px solid #ddd',
            '& .MuiTab-root': {
              textTransform: 'none',
              fontSize: '1rem',
              minWidth: '120px',
            },
            '& .Mui-selected': {
              color: '#003D66',
              fontWeight: 'bold',
            },
          }}
        >
          <Tab label="Gestion Utilisateurs" id="admin-tab-0" />
          <Tab label="Distribution Rôles" id="admin-tab-1" />
          <Tab label="Audit & Logs" id="admin-tab-2" />
          <Tab label="Paramètres" id="admin-tab-3" />
        </Tabs>

        {/* Tab 0: Users Management */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
              <TextField
                placeholder="Rechercher un utilisateur..."
                variant="outlined"
                size="small"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                sx={{ flex: '1 1 250px', minWidth: '250px' }}
              />
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
                sx={{
                  backgroundColor: '#007A5E',
                  '&:hover': { backgroundColor: '#005c47' },
                }}
              >
                Nouvel Utilisateur
              </Button>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>Nom</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Email</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Téléphone</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Rôles</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }} align="center">
                        Statut
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }} align="center">
                        Actions
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredUsers.map((user) => (
                      <TableRow key={user.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                        <TableCell>
                          {user.firstName} {user.lastName}
                        </TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>{user.phone || '-'}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {user.roles.map((role) => (
                              <Chip
                                key={role}
                                label={role}
                                size="small"
                                sx={{
                                  backgroundColor: '#003D66',
                                  color: 'white',
                                  fontWeight: '500',
                                }}
                              />
                            ))}
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={user.isActive ? 'Actif' : 'Inactif'}
                            color={user.isActive ? 'success' : 'default'}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenDialog(user)}
                            title="Modifier"
                            sx={{ color: '#007A5E' }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleResetPassword(user.id)}
                            title="Réinitialiser MDP"
                            sx={{ color: '#CE1126' }}
                          >
                            <LockIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeactivateUser(user.id)}
                            title={user.isActive ? 'Désactiver' : 'Activer'}
                            sx={{ color: '#FFD700' }}
                          >
                            <ApproveIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteUser(user.id)}
                            title="Supprimer"
                            sx={{ color: '#CE1126' }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </TabPanel>

        {/* Tab 1: Role Distribution */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {Object.entries(stats.roleDistribution).map(([role, count]) => (
              <Grid item xs={12} sm={6} md={4} key={role}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      {role}
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#003D66', fontWeight: 'bold' }}>
                      {count} utilisateur(s)
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Tab 2: Audit & Logs */}
        <TabPanel value={tabValue} index={2}>
          <Typography color="textSecondary">
            Les logs d'audit seront disponibles dans une prochaine version
          </Typography>
        </TabPanel>

        {/* Tab 3: Settings */}
        <TabPanel value={tabValue} index={3}>
          <Typography color="textSecondary">
            Les paramètres de configuration seront disponibles dans une prochaine version
          </Typography>
        </TabPanel>
      </Card>

      {/* User Edit/Create Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ backgroundColor: '#003D66', color: 'white', fontWeight: 'bold' }}>
          {editingUser ? 'Modifier Utilisateur' : 'Créer Nouvel Utilisateur'}
        </DialogTitle>
        <DialogContent sx={{ pt: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Prénom"
            fullWidth
            value={formData.firstName}
            onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
            disabled={loading}
          />
          <TextField
            label="Nom"
            fullWidth
            value={formData.lastName}
            onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
            disabled={loading}
          />
          <TextField
            label="Email"
            type="email"
            fullWidth
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            disabled={loading || !!editingUser}
          />
          <TextField
            label="Téléphone"
            fullWidth
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            disabled={loading}
          />

          {!editingUser && (
            <TextField
              label="Mot de passe initial"
              type="password"
              fullWidth
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              disabled={loading}
              helperText="Laisser vide pour générer automatiquement"
            />
          )}

          <FormControl fullWidth>
            <InputLabel>Rôles</InputLabel>
            <Select
              multiple
              value={formData.roles}
              onChange={(e) => setFormData({ ...formData, roles: e.target.value as string[] })}
              disabled={loading}
              label="Rôles"
            >
              {roles.map((role) => (
                <MenuItem key={role} value={role}>
                  {role}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Statut</InputLabel>
            <Select
              value={formData.isActive ? 'actif' : 'inactif'}
              onChange={(e) => setFormData({ ...formData, isActive: e.target.value === 'actif' })}
              disabled={loading}
              label="Statut"
            >
              <MenuItem value="actif">Actif</MenuItem>
              <MenuItem value="inactif">Inactif</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseDialog} disabled={loading}>
            Annuler
          </Button>
          <Button
            onClick={handleSaveUser}
            variant="contained"
            disabled={loading}
            sx={{
              backgroundColor: '#007A5E',
              '&:hover': { backgroundColor: '#005c47' },
            }}
          >
            {loading ? <CircularProgress size={24} /> : 'Sauvegarder'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminDashboard;
