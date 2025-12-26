// src/components/ResponsiveForm.tsx
/**
 * Formulaire responsive avec validation
 */

import React from 'react'
import {
  Box,
  TextField,
  Button,
  Stack,
  FormControlLabel,
  Checkbox,
  Select,
  FormControl,
  InputLabel,
  FormHelperText,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material'
import { responsiveStyles } from '../styles/responsiveStyles'

export interface FormField {
  name: string
  label: string
  type?: 'text' | 'email' | 'password' | 'number' | 'textarea' | 'select' | 'checkbox' | 'date'
  value: any
  onChange: (value: any) => void
  options?: { label: string; value: any }[]
  error?: string
  required?: boolean
  disabled?: boolean
  helperText?: string
  multiline?: boolean
  rows?: number
  fullWidth?: boolean
  xs?: number
  sm?: number
  md?: number
}

interface ResponsiveFormProps {
  fields: FormField[]
  onSubmit: () => void
  onCancel?: () => void
  loading?: boolean
  error?: string
  success?: string
  submitLabel?: string
  cancelLabel?: string
  columns?: number
}

export const ResponsiveForm: React.FC<ResponsiveFormProps> = ({
  fields,
  onSubmit,
  onCancel,
  loading = false,
  error,
  success,
  submitLabel = 'Soumettre',
  cancelLabel = 'Annuler',
  columns = 2,
}) => {
  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Grid container spacing={{ xs: 1, md: 2 }}>
        {fields.map((field) => (
          <Grid
            item
            xs={field.xs || 12}
            sm={field.sm || (12 / columns)}
            md={field.md || (12 / columns)}
            key={field.name}
          >
            {field.type === 'checkbox' ? (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={field.value}
                    onChange={(e) => field.onChange(e.target.checked)}
                    disabled={field.disabled}
                  />
                }
                label={field.label}
              />
            ) : field.type === 'select' ? (
              <FormControl fullWidth error={!!field.error}>
                <InputLabel>{field.label}</InputLabel>
                <Select
                  value={field.value}
                  onChange={(e) => field.onChange(e.target.value)}
                  label={field.label}
                  disabled={field.disabled}
                  size="small"
                >
                  {field.options?.map((opt) => (
                    <optio key={opt.value} value={opt.value}>
                      {opt.label}
                    </optio>
                  ))}
                </Select>
                {field.error && <FormHelperText>{field.error}</FormHelperText>}
              </FormControl>
            ) : (
              <TextField
                fullWidth
                label={field.label}
                type={field.type || 'text'}
                value={field.value}
                onChange={(e) => field.onChange(e.target.value)}
                error={!!field.error}
                helperText={field.error || field.helperText}
                required={field.required}
                disabled={field.disabled}
                multiline={field.multiline || field.type === 'textarea'}
                rows={field.rows || 3}
                size="small"
                variant="outlined"
                sx={responsiveStyles.inputField}
              />
            )}
          </Grid>
        ))}
      </Grid>

      {/* Actions */}
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        sx={{ mt: { xs: 2, md: 3 }, justifyContent: 'flex-end' }}
      >
        {onCancel && (
          <Button
            variant="outlined"
            onClick={onCancel}
            disabled={loading}
            fullWidth={{ xs: true, sm: false }}
          >
            {cancelLabel}
          </Button>
        )}
        <Button
          variant="contained"
          onClick={onSubmit}
          disabled={loading}
          fullWidth={{ xs: true, sm: false }}
          endIcon={loading && <CircularProgress size={20} />}
        >
          {submitLabel}
        </Button>
      </Stack>
    </Box>
  )
}
