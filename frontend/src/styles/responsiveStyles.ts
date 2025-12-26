// src/styles/responsiveStyles.ts
import { SxProps, Theme } from '@mui/material/styles'

// Breakpoints personnalisés (MUI default)
export const breakpoints = {
  xs: 0,
  sm: 600,
  md: 960,
  lg: 1280,
  xl: 1920,
}

// Styles réutilisables
export const responsiveStyles = {
  // Container principal
  mainContainer: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    py: { xs: 2, sm: 3, md: 4 },
    px: { xs: 1, sm: 2, md: 3 },
  } as SxProps<Theme>,

  // Card responsive
  card: {
    borderRadius: { xs: 8, md: 12 },
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    p: { xs: 2, sm: 3, md: 4 },
    mb: { xs: 2, sm: 3, md: 4 },
    transition: 'all 0.3s ease',
    '&:hover': {
      boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
    },
  } as SxProps<Theme>,

  // Header responsive
  headerSection: {
    py: { xs: 3, sm: 4, md: 5 },
    px: { xs: 2, sm: 3, md: 4 },
    backgroundColor: '#fff',
    borderBottom: '1px solid #e0e0e0',
    mb: { xs: 2, sm: 3, md: 4 },
  } as SxProps<Theme>,

  // Titre principal
  pageTitle: {
    fontSize: { xs: '24px', sm: '28px', md: '32px', lg: '36px' },
    fontWeight: 700,
    color: '#1a1a1a',
    mb: { xs: 1, md: 2 },
  } as SxProps<Theme>,

  // Sous-titre
  pageSubtitle: {
    fontSize: { xs: '12px', sm: '13px', md: '14px' },
    color: '#666',
    mb: { xs: 2, md: 3 },
  } as SxProps<Theme>,

  // Grid responsive
  gridContainer: {
    spacing: { xs: 1, sm: 2, md: 3 },
  } as SxProps<Theme>,

  // Tableau responsive
  tableContainer: {
    overflowX: 'auto',
    '& table': {
      minWidth: { xs: '100%', md: '100%' },
    },
    '& th, & td': {
      fontSize: { xs: '12px', sm: '13px', md: '14px' },
      p: { xs: 1, sm: 1.5, md: 2 },
    },
  } as SxProps<Theme>,

  // Boutons responsifs
  buttonPrimary: {
    py: { xs: 1, md: 1.5 },
    px: { xs: 2, md: 3 },
    fontSize: { xs: '12px', md: '14px' },
    textTransform: 'none',
    borderRadius: '6px',
    fontWeight: 600,
  } as SxProps<Theme>,

  // Inputs responsifs
  inputField: {
    '& .MuiInputBase-input': {
      fontSize: { xs: '14px', md: '15px' },
      py: { xs: 1, md: 1.25 },
    },
  } as SxProps<Theme>,

  // Flex center responsive
  flexCenter: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '200px',
  } as SxProps<Theme>,

  // Flex between
  flexBetween: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: { xs: 'flex-start', md: 'center' },
    flexDirection: { xs: 'column', md: 'row' },
    gap: { xs: 2, md: 3 },
  } as SxProps<Theme>,

  // Badge responsive
  badge: {
    px: { xs: 1, md: 1.5 },
    py: { xs: 0.5, md: 0.75 },
    fontSize: { xs: '10px', md: '12px' },
    borderRadius: '4px',
  } as SxProps<Theme>,

  // Modal responsive
  modal: {
    '& .MuiPaper-root': {
      width: { xs: '90%', sm: '80%', md: '600px' },
      maxWidth: '90vw',
    },
  } as SxProps<Theme>,

  // Drawer responsive
  drawer: {
    '& .MuiDrawer-paper': {
      width: { xs: '100%', sm: '300px' },
      maxWidth: '100vw',
    },
  } as SxProps<Theme>,

  // Pagination responsive
  pagination: {
    mt: { xs: 2, md: 3 },
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: { xs: 1, md: 2 },
    '& .MuiPaginationItem-root': {
      fontSize: { xs: '12px', md: '14px' },
    },
  } as SxProps<Theme>,

  // Filter section responsive
  filterSection: {
    p: { xs: 2, sm: 3, md: 3 },
    backgroundColor: '#fafafa',
    borderRadius: { xs: 6, md: 8 },
    mb: { xs: 2, md: 3 },
    display: 'flex',
    flexDirection: { xs: 'column', sm: 'row' },
    gap: { xs: 1.5, md: 2 },
    flexWrap: 'wrap',
  } as SxProps<Theme>,

  // Stats card
  statsCard: {
    p: { xs: 2, sm: 2.5, md: 3 },
    backgroundColor: '#fff',
    borderRadius: { xs: 8, md: 12 },
    border: '1px solid #e0e0e0',
    textAlign: 'center',
    transition: 'all 0.3s ease',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
    },
  } as SxProps<Theme>,

  // Action buttons group
  actionButtons: {
    display: 'flex',
    gap: { xs: 1, md: 2 },
    flexDirection: { xs: 'column', sm: 'row' },
    mt: { xs: 2, md: 3 },
  } as SxProps<Theme>,
}

// Hooks para media queries
export const useResponsive = () => {
  return {
    isMobile: `@media (max-width: ${breakpoints.sm}px)`,
    isTablet: `@media (min-width: ${breakpoints.sm}px) and (max-width: ${breakpoints.md}px)`,
    isDesktop: `@media (min-width: ${breakpoints.md}px)`,
  }
}
