import React from 'react';
import { Box, Container, Typography, Divider, Button } from '@mui/material';
import { useAppSelector } from '../hooks/redux';
import AdminDashboard from './admin/AdminDashboard';
import ComptableDashboard from './comptable/ComptableDashboard';
import GuichetierDashboard from './guichetier/GuichetierDashboard';
import ChauffeurDashboard from './chauffeur/ChauffeurDashboard';
import { useNavigate } from 'react-router-dom';

export const DashboardRouter: React.FC = () => {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth?.user);
  const roles = user?.roles || [];

  // Determine which dashboard to show based on role priority
  // ADMIN is the highest priority
  const getDashboard = () => {
    if (roles.includes('ADMIN')) {
      return <AdminDashboard />;
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
      {/* Role Badge */}
      <Box
        sx={{
          backgroundColor: '#f5f5f5',
          py: 2,
          px: 3,
          borderBottom: '2px solid #ddd',
          mb: 2,
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography sx={{ fontSize: '0.875rem', color: 'textSecondary' }}>
                Rôle Actuel:
              </Typography>
              <Typography sx={{ fontWeight: 'bold', color: '#003D66', fontSize: '1.1rem' }}>
                {getRoleName()}
              </Typography>
            </Box>
            {roles.length > 1 && (
              <Box>
                <Typography sx={{ fontSize: '0.875rem', color: 'textSecondary', mb: 1 }}>
                  Vous avez accès à {roles.length} rôle(s):
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {roles.map((role) => (
                    <Typography
                      key={role}
                      sx={{
                        fontSize: '0.75rem',
                        backgroundColor: '#007A5E',
                        color: 'white',
                        px: 1.5,
                        py: 0.5,
                        borderRadius: 1,
                        fontWeight: '500',
                      }}
                    >
                      {role}
                    </Typography>
                  ))}
                </Box>
              </Box>
            )}
          </Box>
        </Container>
      </Box>

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
