import React, { useRef, useEffect } from 'react'
import {
  Box,
  Pagination,
  PaginationItem,
  Stack,
  Typography,
  CircularProgress,
  Paper,
} from '@mui/material'
import { NavigateBefore as PrevIcon, NavigateNext as NextIcon } from '@mui/icons-material'

interface PaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
  loading?: boolean
  variant?: 'pagination' | 'infinite-scroll'
  onLoadMore?: () => void
}

/**
 * Composant de pagination avec navigation
 */
export const AdvancedPagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  loading = false,
  variant = 'pagination',
}) => {
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  if (variant === 'infinite-scroll') {
    return null // Géré par le composant InfiniteScroll
  }

  return (
    <Paper sx={{ p: 2, mt: 3 }}>
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            Affichage {startItem} à {endItem} sur {totalItems} éléments
          </Typography>
          {loading && <CircularProgress size={24} />}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(_, page) => onPageChange(page)}
            renderItem={(item) => (
              <PaginationItem
                {...item}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: '#CE1126',
                    color: 'white',
                  },
                  '&:hover': {
                    backgroundColor: 'rgba(206, 17, 38, 0.1)',
                  },
                }}
              />
            )}
          />
        </Box>
      </Stack>
    </Paper>
  )
}

/**
 * Composant Infinite Scroll
 */
export const InfiniteScroll: React.FC<{
  children: React.ReactNode
  onLoadMore: () => void
  hasMore: boolean
  loading: boolean
  threshold?: number
}> = ({ children, onLoadMore, hasMore, loading, threshold = 200 }) => {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          onLoadMore()
        }
      },
      { rootMargin: `${threshold}px` }
    )

    const element = scrollRef.current
    if (element) {
      observer.observe(element)
    }

    return () => {
      if (element) {
        observer.unobserve(element)
      }
    }
  }, [hasMore, loading, onLoadMore, threshold])

  return (
    <Box>
      {children}
      {hasMore && (
        <Box
          ref={scrollRef}
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            py: 4,
          }}
        >
          {loading ? (
            <CircularProgress size={32} />
          ) : (
            <Typography color="textSecondary">Défilez pour charger plus...</Typography>
          )}
        </Box>
      )}
    </Box>
  )
}

/**
 * Sélecteur d'éléments par page
 */
export const ItemsPerPageSelector: React.FC<{
  value: number
  onChange: (value: number) => void
  options?: number[]
}> = ({ value, onChange, options = [10, 25, 50, 100] }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <Typography variant="body2">Éléments par page:</Typography>
    <Stack direction="row" spacing={1}>
      {options.map((option) => (
        <Box
          key={option}
          onClick={() => onChange(option)}
          sx={{
            px: 2,
            py: 1,
            border: `2px solid ${value === option ? '#CE1126' : '#ddd'}`,
            borderRadius: '4px',
            cursor: 'pointer',
            backgroundColor: value === option ? 'rgba(206, 17, 38, 0.1)' : 'transparent',
            color: value === option ? '#CE1126' : '#666',
            fontWeight: value === option ? 700 : 400,
            transition: 'all 0.3s',
            '&:hover': {
              borderColor: '#CE1126',
              backgroundColor: 'rgba(206, 17, 38, 0.05)',
            },
          }}
        >
          {option}
        </Box>
      ))}
    </Stack>
  </Box>
)

/**
 * Composant combiné de pagination avec options
 */
export const PaginationWithControls: React.FC<PaginationProps & { onItemsPerPageChange?: (count: number) => void }> = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  onItemsPerPageChange,
  loading = false,
}) => {
  return (
    <Stack spacing={2} sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {onItemsPerPageChange && (
          <ItemsPerPageSelector value={itemsPerPage} onChange={onItemsPerPageChange} />
        )}
        <Typography variant="body2" color="textSecondary">
          {loading ? 'Chargement...' : `Total: ${totalItems} éléments`}
        </Typography>
      </Box>

      <AdvancedPagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={totalItems}
        itemsPerPage={itemsPerPage}
        onPageChange={onPageChange}
        loading={loading}
      />
    </Stack>
  )
}

export default {
  AdvancedPagination,
  InfiniteScroll,
  ItemsPerPageSelector,
  PaginationWithControls,
}
