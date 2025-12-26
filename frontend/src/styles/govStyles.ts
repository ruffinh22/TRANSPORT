// Styles Gouvernementaux Centralisés pour toutes les pages TKF

export const govStyles = {
  // Couleurs Officielles
  colors: {
    primary: '#003D66', // Bleu Gouvernemental
    danger: '#CE1126', // Rouge Burkina
    success: '#007A5E', // Vert Responsabilité
    warning: '#FFD700', // Or Prestige
    neutral: '#666666', // Texte principal
    light: '#f5f5f5', // Fond clair
    border: '#ddd', // Bordures
  },

  // En-tête de Page Gouvernementale
  pageHeader: {
    borderBottom: '3px solid #003D66',
    paddingBottom: 3,
    marginBottom: 4,
  },

  pageTitle: {
    fontSize: { xs: '1.5rem', md: '2rem' },
    fontWeight: 700,
    color: '#003D66',
    marginBottom: 0.5,
  },

  pageSubtitle: {
    fontSize: '0.95rem',
    color: '#666',
  },

  // Boutons Gouvernementaux
  govButton: {
    primary: {
      backgroundColor: '#003D66',
      color: '#ffffff',
      textTransform: 'uppercase',
      fontWeight: 600,
      fontSize: '0.875rem',
      padding: '12px 16px',
      borderRadius: '6px',
      border: '2px solid #003D66',
      transition: 'all 0.3s ease',
      '&:hover': {
        backgroundColor: '#002A47',
        boxShadow: '0 4px 12px rgba(0, 61, 102, 0.15)',
        transform: 'translateY(-1px)',
      },
    },
    secondary: {
      backgroundColor: '#E8E8E8',
      color: '#003D66',
      textTransform: 'uppercase',
      fontWeight: 600,
      fontSize: '0.875rem',
      padding: '12px 16px',
      borderRadius: '6px',
      border: '2px solid #999',
      transition: 'all 0.3s ease',
      '&:hover': {
        backgroundColor: '#D3D3D3',
        boxShadow: '0 4px 12px rgba(0, 61, 102, 0.15)',
        transform: 'translateY(-1px)',
      },
    },
    danger: {
      backgroundColor: '#CE1126',
      color: '#ffffff',
      textTransform: 'uppercase',
      fontWeight: 600,
      fontSize: '0.875rem',
      padding: '12px 16px',
      borderRadius: '6px',
      border: '2px solid #CE1126',
      transition: 'all 0.3s ease',
      '&:hover': {
        backgroundColor: '#9B0B1D',
        boxShadow: '0 4px 12px rgba(206, 17, 38, 0.15)',
        transform: 'translateY(-1px)',
      },
    },
  },

  // Cartes Statistiques
  statCard: (color: string) => ({
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    border: `2px solid ${color}`,
    borderRadius: '8px',
    backgroundColor: '#ffffff',
    boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
    '&:hover': {
      boxShadow: '0 8px 24px rgba(0, 61, 102, 0.15)',
      transform: 'translateY(-2px)',
      borderColor: color,
    },
    position: 'relative',
    overflow: 'hidden',

    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '4px',
      backgroundColor: color,
    },
  }),

  // Cartes de Contenu
  contentCard: {
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0, 61, 102, 0.08)',
    border: '1px solid #e0e0e0',
    backgroundColor: '#ffffff',
    transition: 'all 0.3s ease',
    '&:hover': {
      boxShadow: '0 4px 16px rgba(0, 61, 102, 0.12)',
    },
  },

  // Tableau Gouvernemental
  table: {
    '& thead': {
      backgroundColor: '#003D66',
      '& th': {
        color: '#ffffff',
        fontWeight: 700,
        textTransform: 'uppercase',
        fontSize: '0.85rem',
        letterSpacing: '0.5px',
        padding: '16px',
        borderBottom: '2px solid #002A47',
      },
    },
    '& tbody': {
      '& tr': {
        borderBottom: '1px solid #e0e0e0',
        transition: 'all 0.2s ease',
        '&:hover': {
          backgroundColor: '#f9f9f9',
        },
        '& td': {
          padding: '16px',
        },
      },
    },
  },

  // Pied de Page Gouvernemental
  footer: {
    marginTop: 6,
    paddingTop: 3,
    borderTop: '2px solid #ddd',
    textAlign: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: '8px',
    padding: 3,
  },

  // Espacement Standard
  spacing: {
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4,
  },

  // Icônes Gouvernementales
  icon: {
    primary: { fontSize: 28, color: '#003D66' },
    danger: { fontSize: 28, color: '#CE1126' },
    success: { fontSize: 28, color: '#007A5E' },
    warning: { fontSize: 28, color: '#FFD700' },
  },

  // Chargement
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '400px',
    flexDirection: 'column',
    gap: 2,
  },

  // Erreur
  error: {
    backgroundColor: '#FFEBEE',
    borderLeft: '4px solid #CE1126',
    padding: 2,
    borderRadius: '4px',
    marginBottom: 2,
  },
}

// Fonction utilitaire pour créer des cartes statistiques
export const createStatCard = (color: string) => ({
  ...govStyles.statCard(color),
  padding: 3,
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
  gap: 2,
})
