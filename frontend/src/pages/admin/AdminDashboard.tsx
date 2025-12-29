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
  Stack,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Visibility as ViewIcon,
  Lock as LockIcon,
  CheckCircle as ApproveIcon,
  People as PeopleIcon,
  AssignmentInd as RoleIcon,
  VerifiedUser as VerifiedIcon,
} from '@mui/icons-material';
import userManagementService from '../../services/userManagementService';
import { MainLayout } from '../../components/MainLayout';

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

export const AdminDashboardContent: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.down('lg'));
  
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
      console.error('Failed to fetch users, using test data:', err);
      
      // Use test data for development/testing
      const testUsers: User[] = [
        {
          id: '1',
          firstName: 'Client',
          lastName: 'User',
          email: 'client@transport.local',
          phone: undefined,
          roles: ['CLIENT'],
          isActive: true,
          emailVerified: true,
          phoneVerified: false,
          lastLogin: new Date().toISOString(),
          createdAt: new Date().toISOString(),
        },
        {
          id: '2',
          firstName: 'Chauffeur',
          lastName: 'User',
          email: 'chauffeur@transport.local',
          phone: undefined,
          roles: ['CHAUFFEUR'],
          isActive: true,
          emailVerified: true,
          phoneVerified: false,
          lastLogin: new Date().toISOString(),
          createdAt: new Date().toISOString(),
        },
        {
          id: '3',
          firstName: 'Guichetier',
          lastName: 'User',
          email: 'guichetier@transport.local',
          phone: undefined,
          roles: ['GUICHETIER'],
          isActive: true,
          emailVerified: true,
          phoneVerified: false,
          lastLogin: new Date().toISOString(),
          createdAt: new Date().toISOString(),
        },
        {
          id: '4',
          firstName: 'Comptable',
          lastName: 'User',
          email: 'comptable@transport.local',
          phone: undefined,
          roles: ['COMPTABLE'],
          isActive: true,
          emailVerified: true,
          phoneVerified: false,
          lastLogin: new Date().toISOString(),
          createdAt: new Date().toISOString(),
        },
        {
          id: '5',
          firstName: 'Admin',
          lastName: 'User',
          email: 'admin@transport.local',
          phone: undefined,
          roles: ['ADMIN'],
          isActive: true,
          emailVerified: true,
          phoneVerified: false,
          lastLogin: new Date().toISOString(),
          createdAt: new Date().toISOString(),
        },
      ];
      setUsers(testUsers);
      calculateStats(testUsers);
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
        await userManagementService.updateUser(editingUser.id, {
          firstName: formData.firstName,
          lastName: formData.lastName,
          phone: formData.phone,
          roles: formData.roles,
          isActive: formData.isActive,
        });
      } else {
        await userManagementService.createUser({
          firstName: formData.firstName,
          lastName: formData.lastName,
          email: formData.email,
          phone: formData.phone,
          roles: formData.roles,
          password: formData.password,
        });
      }

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

  // Composant Carte Stat Gouvernementale - RESPONSIVE
  const GovStatCard = ({
    title,
    value,
    icon: Icon,
    onClick,
    color = '#003D66',
  }: {
    title: string
    value: number | string
    icon: any
    onClick?: () => void
    color?: string
  }) => (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        border: `2px solid ${color}`,
        borderRadius: { xs: '6px', sm: '8px', md: '8px' },
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
        '&:hover': onClick
          ? {
              boxShadow: '0 8px 24px rgba(0, 61, 102, 0.15)',
              transform: 'translateY(-2px)',
              borderColor: color,
            }
          : {},
        position: 'relative',
        overflow: 'hidden',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
      onClick={onClick}
    >
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          backgroundColor: color,
        }}
      />

      <CardContent sx={{ p: { xs: '12px', sm: '16px', md: '20px' }, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: { xs: 1, md: 2 } }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography
              variant="body2"
              sx={{
                fontSize: { xs: '0.6rem', sm: '0.75rem', md: '0.85rem' },
                fontWeight: 700,
                color: '#666',
                textTransform: 'uppercase',
                letterSpacing: '0.3px',
                mb: { xs: 0.5, sm: 0.75 },
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 800,
                color: color,
                fontSize: { xs: '1rem', sm: '1.3rem', md: '1.8rem' },
                lineHeight: 1.1,
                wordBreak: 'break-word',
              }}
            >
              {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
            </Typography>
          </Box>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: { xs: 36, sm: 44, md: 56 },
              height: { xs: 36, sm: 44, md: 56 },
              borderRadius: '6px',
              backgroundColor: `${color}15`,
              flexShrink: 0,
              minWidth: { xs: 36, sm: 44, md: 56 },
            }}
          >
            <Icon sx={{ fontSize: { xs: 18, sm: 22, md: 28 }, color: color }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 1.5, sm: 2, md: 4 } }}>
      {/* En-tête - Masqué sur mobile */}
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 }, display: { xs: 'none', md: 'block' } }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#003D66', mb: { xs: 0.5, sm: 1 }, fontSize: { xs: '1.3rem', sm: '1.8rem', md: '2.2rem' } }}>
          Tableau de Bord Administration
        </Typography>
        <Typography variant="body2" sx={{ color: '#666', fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.9rem' } }}>
          Administrateur • Gestion du Transport
        </Typography>
        <Divider sx={{ mt: { xs: 1, sm: 1.5 } }} />
      </Box>

        {/* Stats Cards - GRID RESPONSIVE */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { 
            xs: '1fr', 
            sm: '1fr 1fr', 
            md: '1fr 1fr 1fr' 
          }, 
          gap: { xs: 1.5, sm: 2, md: 2.5 },
          mb: { xs: 2.5, sm: 3, md: 4 }
        }}>
          <GovStatCard
            title="Total Utilisateurs"
            value={stats.totalUsers}
            icon={PeopleIcon}
            color="#003D66"
          />
          <GovStatCard
            title="Utilisateurs Actifs"
            value={stats.activeUsers}
            icon={VerifiedIcon}
            color="#007A5E"
          />
          <GovStatCard
            title="Total Rôles"
            value={Object.keys(stats.roleDistribution).length}
            icon={RoleIcon}
            color="#CE1126"
          />
        </Box>

        {/* Tabs - ULTRA RESPONSIVE */}
        <Card sx={{ borderRadius: { xs: '6px', md: '8px' }, boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)' }}>
          <Tabs
            value={tabValue}
            onChange={(e, newValue) => setTabValue(newValue)}
            aria-label="admin-tabs"
            variant={isMobile ? "fullWidth" : "standard"}
            sx={{
              borderBottom: '2px solid #ddd',
              minHeight: { xs: '44px', sm: '48px', md: '56px' },
              '& .MuiTab-root': {
                textTransform: 'none',
                fontSize: { xs: '0.65rem', sm: '0.8rem', md: '0.95rem' },
                fontWeight: 600,
                padding: { xs: '6px 8px', sm: '8px 12px', md: '12px 20px' },
                minWidth: { xs: 'auto', sm: '120px', md: '160px' },
                minHeight: { xs: '44px', sm: '48px', md: '56px' },
                color: '#666',
                transition: 'all 0.3s ease',
                '&:hover': {
                  color: '#003D66',
                  backgroundColor: 'rgba(0, 61, 102, 0.05)',
                },
              },
              '& .Mui-selected': {
                color: '#003D66',
                fontWeight: 700,
                backgroundColor: 'rgba(0, 61, 102, 0.05)',
              },
              '& .MuiTabs-indicator': {
                height: { xs: '3px', md: '4px' },
                backgroundColor: '#003D66',
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
            <Box sx={{ p: { xs: 1, sm: 1.5, md: 2 }, pt: { xs: 1.5, sm: 2, md: 3 } }}>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={{ xs: 1, sm: 1.5, md: 2 }} sx={{ alignItems: { md: 'center' }, mb: { xs: 2, sm: 2.5, md: 3 } }}>
                <TextField
                  placeholder="Rechercher un utilisateur..."
                  variant="outlined"
                  size="small"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  sx={{ flex: '1 1 100%', minWidth: '100%', maxWidth: { md: '300px' } }}
                />
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => handleOpenDialog()}
                  fullWidth={isMobile}
                  sx={{
                    backgroundColor: '#007A5E',
                    '&:hover': { backgroundColor: '#005c47' },
                  }}
                >
                  Nouvel Utilisateur
                </Button>
              </Stack>

              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : isMobile ? (
                <Box sx={{ width: '100%', px: { xs: 1, sm: 0 } }}>
                  <Box sx={{ margin: '0 auto', maxWidth: { xs: '90%', sm: '100%' }, display: 'flex', flexDirection: 'column', gap: { xs: 1, sm: 1.5, md: 2 } }}>
                    {filteredUsers.length === 0 ? (
                      <Paper sx={{ p: 4, textAlign: 'center', color: '#999' }}>
                        Aucun utilisateur trouvé
                      </Paper>
                    ) : (
                      filteredUsers.map((user) => (
                        <Card key={user.id} sx={{
                          p: { xs: 0.75, sm: 1.5, md: 2 },
                          borderLeft: '4px solid #003D66',
                          backgroundColor: '#f9f9f9',
                          '&:hover': {
                            boxShadow: '0 4px 8px rgba(0, 61, 102, 0.15)',
                            backgroundColor: '#fafafa'
                          }
                        }}>
                          <Stack spacing={{ xs: 0.75, sm: 1.5 }}>
                            {/* Header */}
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 0.75 }}>
                              <Box>
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: { xs: '0.8rem', sm: '0.95rem' }, color: '#003D66' }}>
                                  {user.firstName} {user.lastName}
                                </Typography>
                                <Typography variant="caption" sx={{ fontSize: { xs: '0.7rem', sm: '0.8rem' }, color: '#666' }}>
                                  {user.email}
                                </Typography>
                              </Box>
                              <Chip
                                label={user.isActive ? 'Actif' : 'Inactif'}
                                color={user.isActive ? 'success' : 'default'}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' }, height: { xs: '20px', sm: 'auto' } }}
                              />
                            </Box>

                            {/* Info Grid */}
                            <Box sx={{
                              display: 'grid',
                              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                              gap: { xs: 0.75, sm: 1.5 },
                              backgroundColor: '#fff',
                              p: { xs: 0.75, sm: 1.5 },
                              borderRadius: 1
                            }}>
                              <Box>
                                <Typography variant="caption" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, fontWeight: 600, color: '#666', display: 'block', mb: 0.25 }}>
                                  Téléphone
                                </Typography>
                                <Typography sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem' }, color: '#000', fontWeight: 500 }}>
                                  {user.phone || '-'}
                                </Typography>
                              </Box>
                              <Box>
                                <Typography variant="caption" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, fontWeight: 600, color: '#666', display: 'block', mb: 0.25 }}>
                                  Rôles
                                </Typography>
                                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                  {user.roles.slice(0, 2).map((role) => (
                                    <Chip
                                      key={role}
                                      label={role}
                                      size="small"
                                      sx={{
                                        backgroundColor: '#003D66',
                                        color: 'white',
                                        fontWeight: '500',
                                        fontSize: { xs: '0.6rem', sm: '0.75rem' },
                                        height: { xs: '20px', sm: 'auto' }
                                      }}
                                    />
                                  ))}
                                  {user.roles.length > 2 && (
                                    <Chip
                                      label={`+${user.roles.length - 2}`}
                                      size="small"
                                      sx={{
                                        backgroundColor: '#f0f0f0',
                                        color: '#003D66',
                                        fontWeight: '500',
                                        fontSize: { xs: '0.6rem', sm: '0.75rem' },
                                        height: { xs: '20px', sm: 'auto' }
                                      }}
                                    />
                                  )}
                                </Box>
                              </Box>
                            </Box>

                            {/* Actions */}
                            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={{ xs: 0.75, sm: 1 }} sx={{ pt: 0.5 }}>
                              <Button
                                variant="outlined"
                                onClick={() => handleOpenDialog(user)}
                                fullWidth
                                size="small"
                                sx={{
                                  fontSize: { xs: '0.7rem', sm: '0.8rem' },
                                  py: { xs: 0.5, sm: 1 },
                                  color: '#007A5E',
                                  borderColor: '#007A5E',
                                  '&:hover': { backgroundColor: 'rgba(0, 122, 94, 0.05)' }
                                }}
                              >
                                ✏️ Éditer
                              </Button>
                              <Button
                                variant="outlined"
                                color="error"
                                onClick={() => handleResetPassword(user.id)}
                                fullWidth
                                size="small"
                                sx={{
                                  fontSize: { xs: '0.7rem', sm: '0.8rem' },
                                  py: { xs: 0.5, sm: 1 }
                                }}
                              >
                                🔑 MDP
                              </Button>
                            </Stack>
                          </Stack>
                        </Card>
                      ))
                    )}
                  </Box>
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
            <Box sx={{ p: { xs: 1, sm: 1.5, md: 2 }, pt: { xs: 1.5, sm: 2, md: 3 } }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' }, gap: 3 }}>
                {Object.entries(stats.roleDistribution).map(([role, count]) => (
                  <Card key={role}>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        {role}
                      </Typography>
                      <Typography variant="h5" sx={{ color: '#003D66', fontWeight: 'bold' }}>
                        {count} utilisateur(s)
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </Box>
          </TabPanel>

          {/* Tab 2: Audit & Logs */}
          <TabPanel value={tabValue} index={2}>
            <Box sx={{ p: { xs: 1, sm: 1.5, md: 2 }, pt: { xs: 1.5, sm: 2, md: 3 } }}>
              <Typography color="textSecondary">
                Les logs d'audit seront disponibles dans une prochaine version
              </Typography>
            </Box>
          </TabPanel>

          {/* Tab 3: Settings */}
          <TabPanel value={tabValue} index={3}>
            <Box sx={{ p: { xs: 1, sm: 1.5, md: 2 }, pt: { xs: 1.5, sm: 2, md: 3 } }}>
              <Typography color="textSecondary">
                Les paramètres de configuration seront disponibles dans une prochaine version
              </Typography>
            </Box>
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

// Composant wrapper avec MainLayout pour usage standalone
export const AdminDashboard: React.FC = () => {
  return (
    <MainLayout hideGovernmentHeader={true}>
      <AdminDashboardContent />
    </MainLayout>
  );
};

export default AdminDashboard;
