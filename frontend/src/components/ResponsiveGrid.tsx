// src/components/ResponsiveGrid.tsx
import React from 'react'
import { Grid, Box, SxProps, Theme } from '@mui/material'

interface ResponsiveGridProps {
  children: React.ReactNode
  itemXs?: number
  itemSm?: number
  itemMd?: number
  itemLg?: number
  spacing?: number
  sx?: SxProps<Theme>
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  itemXs = 12,
  itemSm = 6,
  itemMd = 4,
  itemLg = 3,
  spacing = 2,
  sx,
}) => {
  return (
    <Grid
      container
      spacing={{ xs: 1, sm: spacing, md: spacing }}
      sx={sx}
    >
      {React.Children.map(children, (child) => (
        <Grid
          item
          xs={itemXs}
          sm={itemSm}
          md={itemMd}
          lg={itemLg}
        >
          {child}
        </Grid>
      ))}
    </Grid>
  )
}

// Composant pour grilles de statistiques (3 colonnes desktop)
export const StatsGrid: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ResponsiveGrid itemXs={12} itemSm={6} itemMd={4} itemLg={4} spacing={3}>
    {children}
  </ResponsiveGrid>
)

// Composant pour grilles de cartes (2 colonnes desktop)
export const CardGrid: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ResponsiveGrid itemXs={12} itemSm={6} itemMd={6} itemLg={6} spacing={2}>
    {children}
  </ResponsiveGrid>
)

// Composant pour grilles de détails (4 colonnes desktop)
export const DetailGrid: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ResponsiveGrid itemXs={12} itemSm={6} itemMd={3} itemLg={3} spacing={2}>
    {children}
  </ResponsiveGrid>
)
