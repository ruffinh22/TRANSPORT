import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Container,
  Grid,
  Typography,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
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
  Tab,
  Tabs,
  Alert,
  CircularProgress,
  IconButton,
  Badge,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Done as DoneIcon,
  LocalShipping as ShippingIcon,
  Payment as PaymentIcon,
  Receipt as ReceiptIcon,
  Notifications as NotificationsIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

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
      id={`guichetier-tabpanel-${index}`}
      aria-labelledby={`guichetier-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

interface Parcel {
  id: string;
  trackingNumber: string;
  sender: string;
  receiver: string;
  weight: number;
  destination: string;
  status: 'PENDING' | 'IN_TRANSIT' | 'DELIVERED' | 'RETURNED';
  createdAt: string;
  deliveryDate?: string;
}

interface Ticket {
  id: string;
  ticketNumber: string;
  subject: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
  createdAt: string;
  client: string;
}

interface Notification {
  id: string;
  type: 'parcel' | 'payment' | 'ticket' | 'system';
  message: string;
  read: boolean;
  createdAt: string;
}

export const GuichetierDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openParcelDialog, setOpenParcelDialog] = useState(false);
  const [openTicketDialog, setOpenTicketDialog] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  // Form states
  const [parcelForm, setParcelForm] = useState({
    sender: '',
    receiver: '',
    weight: '',
    destination: '',
    description: '',
  });

  const [ticketForm, setTicketForm] = useState({
    subject: '',
    priority: 'MEDIUM',
    description: '',
    client: '',
  });

  // Mock data
  const stats = [
    {
      title: 'Colis en Attente',
      value: '12',
      color: '#FFD700',
      icon: ShippingIcon,
    },
    {
      title: 'Tickets Ouverts',
      value: '5',
      color: '#CE1126',
      icon: ReceiptIcon,
    },
    {
      title: 'Paiements Pendants',
      value: '8',
      color: '#003D66',
      icon: PaymentIcon,
    },
    {
      title: 'Notifications',
      value: String(notifications.length),
      color: '#007A5E',
      icon: NotificationsIcon,
    },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      // Mock data
      const mockParcels: Parcel[] = [
        {
          id: '1',
          trackingNumber: 'TRK-2024-001',
          sender: 'Company A',
          receiver: 'John Doe',
          weight: 2.5,
          destination: 'Yaoundé',
          status: 'PENDING',
          createdAt: new Date().toISOString(),
        },
        {
          id: '2',
          trackingNumber: 'TRK-2024-002',
          sender: 'Company B',
          receiver: 'Jane Smith',
          weight: 5.0,
          destination: 'Douala',
          status: 'IN_TRANSIT',
          createdAt: new Date(Date.now() - 86400000).toISOString(),
          deliveryDate: new Date(Date.now() + 86400000).toISOString(),
        },
      ];

      const mockTickets: Ticket[] = [
        {
          id: '1',
          ticketNumber: 'TICK-2024-001',
          subject: 'Colis endommagé',
          priority: 'HIGH',
          status: 'OPEN',
          createdAt: new Date().toISOString(),
          client: 'customer@example.com',
        },
      ];

      const mockNotifications: Notification[] = [
        {
          id: '1',
          type: 'parcel',
          message: 'Nouveau colis arrivé - TRK-2024-003',
          read: false,
          createdAt: new Date().toISOString(),
        },
        {
          id: '2',
          type: 'payment',
          message: 'Paiement reçu de Client X',
          read: true,
          createdAt: new Date(Date.now() - 3600000).toISOString(),
        },
      ];

      setParcels(mockParcels);
      setTickets(mockTickets);
      setNotifications(mockNotifications);
    } catch (err) {
      setError('Erreur lors du chargement des données');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddParcel = async () => {
    if (!parcelForm.sender || !parcelForm.receiver || !parcelForm.destination) {
      setError('Veuillez remplir tous les champs requis');
      return;
    }

    setLoading(true);
    try {
      // TODO: Implémenter authService.createParcel(parcelForm)
      console.log('Creating parcel:', parcelForm);
      setParcelForm({
        sender: '',
        receiver: '',
        weight: '',
        destination: '',
        description: '',
      });
      setOpenParcelDialog(false);
      await loadData();
    } catch (err) {
      setError('Erreur lors de la création du colis');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTicket = async () => {
    if (!ticketForm.subject || !ticketForm.client) {
      setError('Veuillez remplir tous les champs requis');
      return;
    }

    setLoading(true);
    try {
      // TODO: Implémenter authService.createTicket(ticketForm)
      console.log('Creating ticket:', ticketForm);
      setTicketForm({
        subject: '',
        priority: 'MEDIUM',
        description: '',
        client: '',
      });
      setOpenTicketDialog(false);
      await loadData();
    } catch (err) {
      setError('Erreur lors de la création du ticket');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateParcelStatus = async (parcelId: string, newStatus: string) => {
    setLoading(true);
    try {
      // TODO: Implémenter authService.updateParcelStatus(parcelId, newStatus)
      console.log('Updating parcel status:', parcelId, newStatus);
      await loadData();
    } catch (err) {
      setError('Erreur lors de la mise à jour du colis');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkNotificationAsRead = (notificationId: string) => {
    setNotifications(
      notifications.map((n) =>
        n.id === notificationId ? { ...n, read: true } : n
      )
    );
  };

  const unreadNotifications = notifications.filter((n) => !n.read).length;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return '#FFD700';
      case 'IN_TRANSIT':
        return '#007A5E';
      case 'DELIVERED':
        return '#007A5E';
      case 'RETURNED':
        return '#CE1126';
      default:
        return '#003D66';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'LOW':
        return 'info';
      case 'MEDIUM':
        return 'warning';
      case 'HIGH':
        return 'error';
      case 'URGENT':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#003D66' }}>
            Tableau de Bord Guichetier
          </Typography>
          <IconButton
            color="inherit"
            onClick={() => setShowNotifications(!showNotifications)}
            sx={{ position: 'relative' }}
          >
            <Badge badgeContent={unreadNotifications} color="error">
              <NotificationsIcon sx={{ fontSize: 28, color: '#003D66' }} />
            </Badge>
          </IconButton>
        </Box>
        <Divider sx={{ mt: 2 }} />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card sx={{ boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography color="textSecondary" sx={{ fontSize: '0.875rem', mb: 1 }}>
                        {stat.title}
                      </Typography>
                      <Typography variant="h5" sx={{ color: stat.color, fontWeight: 'bold' }}>
                        {stat.value}
                      </Typography>
                    </Box>
                    <Icon sx={{ fontSize: 40, color: stat.color, opacity: 0.5 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Notifications Panel */}
      {showNotifications && (
        <Card sx={{ mb: 4, borderLeft: `4px solid #007A5E` }}>
          <CardHeader
            title="Notifications"
            action={
              <IconButton
                size="small"
                onClick={() => setShowNotifications(false)}
              >
                <CloseIcon />
              </IconButton>
            }
          />
          <CardContent>
            {notifications.length === 0 ? (
              <Typography color="textSecondary">Aucune notification</Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {notifications.map((notif) => (
                  <Box
                    key={notif.id}
                    sx={{
                      p: 2,
                      backgroundColor: notif.read ? '#f5f5f5' : '#e3f2fd',
                      borderRadius: 1,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Box>
                      <Typography
                        sx={{
                          fontWeight: notif.read ? 'normal' : 'bold',
                          fontSize: '0.9rem',
                        }}
                      >
                        {notif.message}
                      </Typography>
                      <Typography sx={{ fontSize: '0.75rem', color: 'textSecondary' }}>
                        {new Date(notif.createdAt).toLocaleString('fr-FR')}
                      </Typography>
                    </Box>
                    {!notif.read && (
                      <IconButton
                        size="small"
                        onClick={() => handleMarkNotificationAsRead(notif.id)}
                      >
                        <DoneIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Card>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          aria-label="guichetier-tabs"
          sx={{
            borderBottom: '1px solid #ddd',
            '& .MuiTab-root': {
              textTransform: 'none',
              fontSize: '1rem',
            },
            '& .Mui-selected': {
              color: '#003D66',
              fontWeight: 'bold',
            },
          }}
        >
          <Tab label="Colis" id="guichetier-tab-0" />
          <Tab label="Tickets" id="guichetier-tab-1" />
          <Tab label="Paiements" id="guichetier-tab-2" />
        </Tabs>

        {/* Tab 0: Parcels */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 3 }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpenParcelDialog(true)}
              sx={{
                backgroundColor: '#007A5E',
                '&:hover': { backgroundColor: '#005c47' },
                mb: 3,
              }}
            >
              Nouveau Colis
            </Button>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>Numéro de Suivi</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Expéditeur</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Destinataire</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }} align="right">
                        Poids (kg)
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Destination</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }} align="center">
                        Statut
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }} align="center">
                        Actions
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {parcels.map((parcel) => (
                      <TableRow key={parcel.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                        <TableCell>{parcel.trackingNumber}</TableCell>
                        <TableCell>{parcel.sender}</TableCell>
                        <TableCell>{parcel.receiver}</TableCell>
                        <TableCell align="right">{parcel.weight}</TableCell>
                        <TableCell>{parcel.destination}</TableCell>
                        <TableCell align="center">
                          <Chip
                            label={parcel.status}
                            size="small"
                            sx={{
                              backgroundColor: getStatusColor(parcel.status),
                              color: parcel.status === 'PENDING' ? 'black' : 'white',
                            }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => handleUpdateParcelStatus(parcel.id, 'IN_TRANSIT')}
                            title="Marquer en transit"
                            sx={{ color: '#007A5E' }}
                          >
                            <ShippingIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleUpdateParcelStatus(parcel.id, 'DELIVERED')}
                            title="Marquer livré"
                            sx={{ color: '#007A5E' }}
                          >
                            <DoneIcon fontSize="small" />
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

        {/* Tab 1: Tickets */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 3 }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpenTicketDialog(true)}
              sx={{
                backgroundColor: '#CE1126',
                '&:hover': { backgroundColor: '#a00d1b' },
                mb: 3,
              }}
            >
              Nouveau Ticket
            </Button>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>Numéro Ticket</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Sujet</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Client</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }} align="center">
                        Priorité
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }} align="center">
                        Statut
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tickets.map((ticket) => (
                      <TableRow key={ticket.id} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                        <TableCell>{ticket.ticketNumber}</TableCell>
                        <TableCell>{ticket.subject}</TableCell>
                        <TableCell>{ticket.client}</TableCell>
                        <TableCell align="center">
                          <Chip
                            label={ticket.priority}
                            size="small"
                            color={getPriorityColor(ticket.priority)}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={ticket.status}
                            size="small"
                            variant="outlined"
                            color={ticket.status === 'OPEN' ? 'error' : 'success'}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </TabPanel>

        {/* Tab 2: Payments */}
        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" sx={{ mb: 2 }}>
                Module de gestion des paiements à venir
              </Typography>
              <LinearProgress sx={{ backgroundColor: '#ddd', height: 8 }} />
            </CardContent>
          </Card>
        </TabPanel>
      </Card>

      {/* Add Parcel Dialog */}
      <Dialog open={openParcelDialog} onClose={() => setOpenParcelDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ backgroundColor: '#003D66', color: 'white', fontWeight: 'bold' }}>
          Ajouter un Nouveau Colis
        </DialogTitle>
        <DialogContent sx={{ pt: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Expéditeur"
            fullWidth
            value={parcelForm.sender}
            onChange={(e) => setParcelForm({ ...parcelForm, sender: e.target.value })}
            disabled={loading}
          />
          <TextField
            label="Destinataire"
            fullWidth
            value={parcelForm.receiver}
            onChange={(e) => setParcelForm({ ...parcelForm, receiver: e.target.value })}
            disabled={loading}
          />
          <TextField
            label="Poids (kg)"
            type="number"
            fullWidth
            value={parcelForm.weight}
            onChange={(e) => setParcelForm({ ...parcelForm, weight: e.target.value })}
            disabled={loading}
          />
          <TextField
            label="Destination"
            fullWidth
            value={parcelForm.destination}
            onChange={(e) => setParcelForm({ ...parcelForm, destination: e.target.value })}
            disabled={loading}
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={parcelForm.description}
            onChange={(e) => setParcelForm({ ...parcelForm, description: e.target.value })}
            disabled={loading}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setOpenParcelDialog(false)} disabled={loading}>
            Annuler
          </Button>
          <Button
            onClick={handleAddParcel}
            variant="contained"
            disabled={loading}
            sx={{
              backgroundColor: '#007A5E',
              '&:hover': { backgroundColor: '#005c47' },
            }}
          >
            {loading ? <CircularProgress size={24} /> : 'Ajouter'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Ticket Dialog */}
      <Dialog open={openTicketDialog} onClose={() => setOpenTicketDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ backgroundColor: '#CE1126', color: 'white', fontWeight: 'bold' }}>
          Créer un Nouveau Ticket
        </DialogTitle>
        <DialogContent sx={{ pt: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Sujet"
            fullWidth
            value={ticketForm.subject}
            onChange={(e) => setTicketForm({ ...ticketForm, subject: e.target.value })}
            disabled={loading}
          />
          <TextField
            label="Email Client"
            type="email"
            fullWidth
            value={ticketForm.client}
            onChange={(e) => setTicketForm({ ...ticketForm, client: e.target.value })}
            disabled={loading}
          />
          <FormControl fullWidth>
            <InputLabel>Priorité</InputLabel>
            <Select
              value={ticketForm.priority}
              onChange={(e) => setTicketForm({ ...ticketForm, priority: e.target.value })}
              disabled={loading}
              label="Priorité"
            >
              <MenuItem value="LOW">Basse</MenuItem>
              <MenuItem value="MEDIUM">Moyenne</MenuItem>
              <MenuItem value="HIGH">Haute</MenuItem>
              <MenuItem value="URGENT">Urgente</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={ticketForm.description}
            onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })}
            disabled={loading}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setOpenTicketDialog(false)} disabled={loading}>
            Annuler
          </Button>
          <Button
            onClick={handleAddTicket}
            variant="contained"
            disabled={loading}
            sx={{
              backgroundColor: '#CE1126',
              '&:hover': { backgroundColor: '#a00d1b' },
            }}
          >
            {loading ? <CircularProgress size={24} /> : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default GuichetierDashboard;
