// src/components/ResponsivePageTemplate.tsx
import React from 'react'
import { Box, Container, Typography, Button, Stack } from '@mui/material'
import { responsiveStyles } from '../styles/responsiveStyles'

interface ResponsivePageTemplateProps {
  title: string
  subtitle?: string
  actions?: React.ReactNode[]
  children: React.ReactNode
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}

export const ResponsivePageTemplate: React.FC<ResponsivePageTemplateProps> = ({
  title,
  subtitle,
  actions,
  children,
  maxWidth = 'lg',
}) => {
  return (
    <Container maxWidth={maxWidth} sx={{ py: { xs: 2, md: 4 } }}>
      {/* Header Section */}
      <Box sx={responsiveStyles.headerSection}>
        <Box sx={responsiveStyles.flexBetween}>
          <Box flex={1}>
            <Typography sx={responsiveStyles.pageTitle}>{title}</Typography>
            {subtitle && <Typography sx={responsiveStyles.pageSubtitle}>{subtitle}</Typography>}
          </Box>
          {actions && actions.length > 0 && (
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={{ xs: 1, md: 2 }}
              sx={{ alignSelf: 'flex-start', ml: { xs: 0, md: 2 } }}
            >
              {actions}
            </Stack>
          )}
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={responsiveStyles.mainContainer}>{children}</Box>
    </Container>
  )
}
