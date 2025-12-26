import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  Stack,
  Typography,
  CircularProgress,
} from '@mui/material'
import {
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
  MoreHoriz as InfiniteIcon,
} from '@mui/icons-material'

export interface PaginationConfig {
  currentPage: number
  pageSize: number
  totalItems: number
  totalPages: number
  hasNextPage: boolean
  hasPreviousPage: boolean
}

export interface PaginationComponentProps {
  config: PaginationConfig
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
  isLoading?: boolean
  pageSizeOptions?: number[]
  mode?: 'pagination' | 'infinite-scroll'
  onLoadMore?: () => void
}

/**
 * Composant de pagination réutilisable
 * Supporte pagination classique et infinite scroll
 */
export const PaginationComponent: React.FC<PaginationComponentProps> = ({
  config,
  onPageChange,
  onPageSizeChange,
  isLoading = false,
  pageSizeOptions = [10, 25, 50, 100],
  mode = 'pagination',
  onLoadMore,
}) => {
  const [pageSize, setPageSize] = useState(config.pageSize)

  useEffect(() => {
    setPageSize(config.pageSize)
  }, [config.pageSize])

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize)
    onPageSizeChange(newSize)
    onPageChange(1) // Revenir à la page 1
  }

  const handleLoadMore = () => {
    if (onLoadMore && !isLoading) {
      onLoadMore()
    }
  }

  if (mode === 'infinite-scroll') {
    return (
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        {isLoading ? (
          <CircularProgress />
        ) : (
          config.hasNextPage && (
            <Button
              variant="contained"
              startIcon={<InfiniteIcon />}
              onClick={handleLoadMore}
              fullWidth
              sx={{ maxWidth: 300 }}
            >
              Charger plus ({config.totalItems} résultats)
            </Button>
          )
        )}
      </Box>
    )
  }

  // Mode pagination classique
  return (
    <Card sx={{ mt: 3, p: 2, backgroundColor: '#f9f9f9' }}>
      <Stack spacing={2}>
        {/* Résumé de la pagination */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            Affichage{' '}
            <strong>
              {Math.min((config.currentPage - 1) * config.pageSize + 1, config.totalItems)}
            </strong>{' '}
            à{' '}
            <strong>
              {Math.min(config.currentPage * config.pageSize, config.totalItems)}
            </strong>{' '}
            de <strong>{config.totalItems}</strong> résultats
          </Typography>

          {/* Sélecteur de taille de page */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Résultats par page</InputLabel>
            <Select
              value={pageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              label="Résultats par page"
            >
              {pageSizeOptions.map((option) => (
                <MenuItem key={option} value={option}>
                  {option} par page
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* Contrôles de pagination */}
        <Grid container spacing={2} alignItems="center" justifyContent="space-between">
          {/* Boutons précédent/suivant */}
          <Grid item>
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<PrevIcon />}
                onClick={() => onPageChange(config.currentPage - 1)}
                disabled={!config.hasPreviousPage || isLoading}
              >
                Précédent
              </Button>
              <Button
                variant="outlined"
                size="small"
                endIcon={<NextIcon />}
                onClick={() => onPageChange(config.currentPage + 1)}
                disabled={!config.hasNextPage || isLoading}
              >
                Suivant
              </Button>
            </Stack>
          </Grid>

          {/* Pagination numérotée */}
          <Grid item>
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              {isLoading ? (
                <CircularProgress size={24} />
              ) : (
                <Pagination
                  count={config.totalPages}
                  page={config.currentPage}
                  onChange={(_, page) => onPageChange(page)}
                  color="primary"
                  size="medium"
                  showFirstButton
                  showLastButton
                  variant="outlined"
                />
              )}
            </Box>
          </Grid>

          {/* Info pages */}
          <Grid item>
            <Typography variant="body2" sx={{ color: 'text.secondary', whiteSpace: 'nowrap' }}>
              Page <strong>{config.currentPage}</strong> sur <strong>{config.totalPages}</strong>
            </Typography>
          </Grid>
        </Grid>

        {/* Barre de progression optionnelle */}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 1 }}>
            <CircularProgress size={32} />
          </Box>
        )}
      </Stack>
    </Card>
  )
}

/**
 * Hook personnalisé pour gérer la pagination
 */
export const usePagination = (initialPageSize: number = 10) => {
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [totalItems, setTotalItems] = useState(0)
  const [isLoading, setIsLoading] = useState(false)

  const totalPages = Math.ceil(totalItems / pageSize)
  const hasNextPage = currentPage < totalPages
  const hasPreviousPage = currentPage > 1

  const config: PaginationConfig = {
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    hasNextPage,
    hasPreviousPage,
  }

  const reset = () => {
    setCurrentPage(1)
    setPageSize(initialPageSize)
    setTotalItems(0)
  }

  return {
    config,
    setCurrentPage,
    setPageSize,
    setTotalItems,
    setIsLoading,
    isLoading,
    reset,
  }
}

export default PaginationComponent
