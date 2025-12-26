import React from 'react'
import { Box, Container, Typography, Button } from '@mui/material'
import { govStyles } from '../styles/govStyles'

interface GovPageHeaderProps {
  title: string
  subtitle?: string
  icon?: string
  actions?: Array<{
    label: string
    icon: React.ReactNode
    onClick: () => void
    variant?: 'primary' | 'secondary' | 'danger'
  }>
}

export const GovPageHeader: React.FC<GovPageHeaderProps> = ({ title, subtitle, icon, actions }) => (
  <Box sx={govStyles.pageHeader}>
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
      <Box sx={{ flex: 1 }}>
        <Typography variant="h4" sx={govStyles.pageTitle}>
          {icon} {title}
        </Typography>
        {subtitle && <Typography sx={govStyles.pageSubtitle}>{subtitle}</Typography>}
      </Box>
      {actions && actions.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, flexDirection: { xs: 'column', sm: 'row' } }}>
          {actions.map((action, idx) => (
            <Button
              key={idx}
              startIcon={action.icon}
              onClick={action.onClick}
              variant="contained"
              sx={govStyles.govButton[action.variant || 'primary']}
            >
              {action.label}
            </Button>
          ))}
        </Box>
      )}
    </Box>
  </Box>
)

interface GovPageWrapperProps {
  children: React.ReactNode
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}

export const GovPageWrapper: React.FC<GovPageWrapperProps> = ({ children, maxWidth = 'lg' }) => (
  <Container maxWidth={maxWidth} sx={{ py: { xs: 2, md: 4 } }}>
    {children}
  </Container>
)

interface GovPageFooterProps {
  text: string
}

export const GovPageFooter: React.FC<GovPageFooterProps> = ({ text }) => (
  <Box sx={govStyles.footer}>
    <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
      🏛️ <strong>TKF - Transporteur Kendrick Faso</strong> | {text}
    </Typography>
    <Typography variant="caption" sx={{ color: '#999', mt: 1 }}>
      © 2024-2025 • République du Burkina Faso • Tous droits réservés
    </Typography>
  </Box>
)
