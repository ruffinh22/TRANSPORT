import React, { useState } from 'react'
import {
  Box,
  Paper,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Grid,
  DatePicker,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
} from '@mui/icons-material'

export interface FilterConfig {
  id: string
  label: string
  type: 'text' | 'select' | 'date' | 'number' | 'multiselect'
  options?: { label: string; value: any }[]
  value?: any
  multiple?: boolean
}

interface AdvancedFilterProps {
  filters: FilterConfig[]
  onFilterChange: (filters: FilterConfig[]) => void
  onReset: () => void
  title?: string
}

/**
 * Composant de filtres avancés réutilisable
 */
export const AdvancedFilter: React.FC<AdvancedFilterProps> = ({
  filters,
  onFilterChange,
  onReset,
  title = 'Filtres avancés',
}) => {
  const [activeFilters, setActiveFilters] = useState<FilterConfig[]>(filters)

  const handleFilterChange = (filterId: string, value: any) => {
    const updated = activeFilters.map((f) =>
      f.id === filterId ? { ...f, value } : f
    )
    setActiveFilters(updated)
    onFilterChange(updated)
  }

  const handleReset = () => {
    const reset = activeFilters.map((f) => ({ ...f, value: undefined }))
    setActiveFilters(reset)
    onReset()
  }

  const activeCount = activeFilters.filter((f) => f.value !== undefined).length

  return (
    <Paper sx={{ mb: 3 }}>
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <FilterIcon sx={{ mr: 1 }} />
          <Typography variant="h6" sx={{ flex: 1 }}>
            {title}
          </Typography>
          {activeCount > 0 && (
            <Chip
              label={`${activeCount} filtre${activeCount > 1 ? 's' : ''} actif${activeCount > 1 ? 's' : ''}`}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            <Grid container spacing={2}>
              {activeFilters.map((filter) => (
                <Grid item xs={12} sm={6} md={4} key={filter.id}>
                  {filter.type === 'text' && (
                    <TextField
                      fullWidth
                      label={filter.label}
                      variant="outlined"
                      size="small"
                      value={filter.value || ''}
                      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                      placeholder={`Entrez ${filter.label.toLowerCase()}`}
                    />
                  )}

                  {filter.type === 'number' && (
                    <TextField
                      fullWidth
                      label={filter.label}
                      variant="outlined"
                      size="small"
                      type="number"
                      value={filter.value || ''}
                      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                    />
                  )}

                  {filter.type === 'select' && (
                    <FormControl fullWidth size="small">
                      <InputLabel>{filter.label}</InputLabel>
                      <Select
                        value={filter.value || ''}
                        label={filter.label}
                        onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                      >
                        <MenuItem value="">
                          <em>Tous</em>
                        </MenuItem>
                        {filter.options?.map((opt) => (
                          <MenuItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}

                  {filter.type === 'date' && (
                    <TextField
                      fullWidth
                      label={filter.label}
                      variant="outlined"
                      size="small"
                      type="date"
                      value={filter.value || ''}
                      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                      InputLabelProps={{ shrink: true }}
                    />
                  )}

                  {filter.type === 'multiselect' && (
                    <FormControl fullWidth size="small">
                      <InputLabel>{filter.label}</InputLabel>
                      <Select
                        multiple
                        value={filter.value || []}
                        label={filter.label}
                        onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                      >
                        {filter.options?.map((opt) => (
                          <MenuItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                </Grid>
              ))}
            </Grid>

            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button
                startIcon={<ClearIcon />}
                variant="outlined"
                onClick={handleReset}
                disabled={activeCount === 0}
              >
                Réinitialiser
              </Button>
              <Button variant="contained" color="primary">
                Appliquer
              </Button>
            </Box>
          </Stack>
        </AccordionDetails>
      </Accordion>
    </Paper>
  )
}

/**
 * Composant de filtres rapides (tags)
 */
export const QuickFilters: React.FC<{
  filters: { label: string; value: string; active: boolean }[]
  onChange: (value: string) => void
}> = ({ filters, onChange }) => (
  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
    {filters.map((filter) => (
      <Chip
        key={filter.value}
        label={filter.label}
        onClick={() => onChange(filter.value)}
        variant={filter.active ? 'filled' : 'outlined'}
        color={filter.active ? 'primary' : 'default'}
        sx={{ cursor: 'pointer' }}
      />
    ))}
  </Box>
)

/**
 * Barre de recherche avec suggestions
 */
export const SearchBar: React.FC<{
  onSearch: (query: string) => void
  placeholder?: string
  suggestions?: string[]
}> = ({ onSearch, placeholder = 'Rechercher...', suggestions = [] }) => {
  const [value, setValue] = React.useState('')
  const [openSuggestions, setOpenSuggestions] = React.useState(false)

  return (
    <Box sx={{ position: 'relative', mb: 2 }}>
      <TextField
        fullWidth
        variant="outlined"
        placeholder={placeholder}
        value={value}
        onChange={(e) => {
          setValue(e.target.value)
          onSearch(e.target.value)
          setOpenSuggestions(e.target.value.length > 0 && suggestions.length > 0)
        }}
        onFocus={() => setOpenSuggestions(value.length > 0 && suggestions.length > 0)}
        onBlur={() => setTimeout(() => setOpenSuggestions(false), 200)}
      />
      {openSuggestions && suggestions.length > 0 && (
        <Paper
          sx={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 10,
            maxHeight: 200,
            overflowY: 'auto',
          }}
        >
          {suggestions
            .filter((s) => s.toLowerCase().includes(value.toLowerCase()))
            .map((suggestion) => (
              <Box
                key={suggestion}
                sx={{
                  p: 1.5,
                  cursor: 'pointer',
                  '&:hover': { backgroundColor: '#f5f5f5' },
                }}
                onClick={() => {
                  setValue(suggestion)
                  onSearch(suggestion)
                  setOpenSuggestions(false)
                }}
              >
                {suggestion}
              </Box>
            ))}
        </Paper>
      )}
    </Box>
  )
}

export default {
  AdvancedFilter,
  QuickFilters,
  SearchBar,
}
