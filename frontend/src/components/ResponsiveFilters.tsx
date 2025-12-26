// src/components/ResponsiveFilters.tsx
import React from 'react'
import { Box, TextField, Button, Stack, Collapse, IconButton, useMediaQuery, useTheme } from '@mui/material'
import { FilterList as FilterIcon, Close as CloseIcon } from '@mui/icons-material'
import { responsiveStyles } from '../styles/responsiveStyles'

interface FilterField {
  name: string
  label: string
  type?: 'text' | 'select' | 'date' | 'number'
  options?: { label: string; value: any }[]
  value: any
  onChange: (value: any) => void
}

interface ResponsiveFiltersProps {
  fields: FilterField[]
  onApply?: () => void
  onReset?: () => void
  children?: React.ReactNode
}

export const ResponsiveFilters: React.FC<ResponsiveFiltersProps> = ({
  fields,
  onApply,
  onReset,
  children,
}) => {
  const [open, setOpen] = React.useState(false)
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

  return (
    <Box sx={responsiveStyles.filterSection}>
      {isMobile && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <CloseIcon /> : <FilterIcon />}
          </IconButton>
          <span style={{ fontSize: '14px', fontWeight: 500 }}>Filtres</span>
        </Box>
      )}

      <Collapse in={!isMobile || open} sx={{ width: '100%' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={{ xs: 1, md: 2 }} sx={{ width: '100%', flexWrap: 'wrap' }}>
          {fields.map((field) => (
            <TextField
              key={field.name}
              label={field.label}
              type={field.type || 'text'}
              value={field.value}
              onChange={(e) => field.onChange(e.target.value)}
              size="small"
              variant="outlined"
              sx={{ flex: { xs: '1 1 100%', sm: '1 1 auto', md: 'auto' }, minWidth: '150px' }}
            />
          ))}

          {children}

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ ml: 'auto' }}>
            {onApply && (
              <Button variant="contained" size="small" onClick={onApply}>
                Appliquer
              </Button>
            )}
            {onReset && (
              <Button variant="outlined" size="small" onClick={onReset}>
                Réinitialiser
              </Button>
            )}
          </Stack>
        </Stack>
      </Collapse>
    </Box>
  )
}
