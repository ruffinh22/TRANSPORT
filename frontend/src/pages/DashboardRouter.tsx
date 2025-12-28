import React from 'react';
import { Box, Container, Typography, Divider, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Dashboard } from './Dashboard';
import AdminDashboard from './admin/AdminDashboard';
import ComptableDashboard from './comptable/ComptableDashboard';
import GuichetierDashboard from './guichetier/GuichetierDashboard';
import ChauffeurDashboard from './chauffeur/ChauffeurDashboard';

export const DashboardRouter: React.FC = () => {
  const navigate = useNavigate();
  
  // Récupérer l'utilisateur depuis localStorage pour éviter dépendance Redux
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;
  const roles = user?.roles || [];

  // Determine which dashboard to show based on role priority
  const getDashboard = () => {
    if (roles.includes('ADMIN')) {
      // Pour ADMIN: afficher le Dashboard avec les onglets intégrés
      return <Dashboard />;
    } else if (roles.includes('COMPTABLE')) {
      return <ComptableDashboard />;
    } else if (roles.includes('GUICHETIER')) {
      return <GuichetierDashboard />;
    } else if (roles.includes('CHAUFFEUR')) {
      return <ChauffeurDashboard />;
    } else {
      return <DefaultDashboard />;
    }
  };

  const getRoleName = (): string => {
    if (roles.includes('ADMIN')) return 'Administrateur';
    if (roles.includes('COMPTABLE')) return 'Comptable';
    if (roles.includes('GUICHETIER')) return 'Guichetier';
    if (roles.includes('CHAUFFEUR')) return 'Chauffeur';
    if (roles.includes('CONTROLEUR')) return 'Contrôleur';
    if (roles.includes('GESTIONNAIRE_COURRIER')) return 'Gestionnaire de Courrier';
    if (roles.includes('MANAGER')) return 'Manager';
    return 'Utilisateur';
  };

  return (
    <Box>
      {/* Dashboard Content */}

      {/* Dashboard Content */}
      {getDashboard()}
    </Box>
  );
};

/**
 * Default Dashboard for users without specific roles
 * Provides links to available features
 */
const DefaultDashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#003D66', mb: 2 }}>
          Bienvenue dans TKF Transport
        </Typography>
        <Divider sx={{ my: 3 }} />

        <Typography color="textSecondary" sx={{ mb: 4, fontSize: '1.1rem' }}>
          Votre compte ne dispose pas encore d'un rôle spécifique. Veuillez contacter l'administrateur pour être assigné à un rôle.
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            onClick={() => navigate('/profile')}
            sx={{
              backgroundColor: '#003D66',
              '&:hover': { backgroundColor: '#002244' },
            }}
          >
            Consulter Mon Profil
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/')}
            sx={{ borderColor: '#007A5E', color: '#007A5E' }}
          >
            Retour à l'Accueil
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default DashboardRouter;
