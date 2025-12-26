// src/components/ResponsiveTable.tsx
import React from 'react'
import {
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Box,
  Typography,
  useMediaQuery,
  useTheme,
  Card,
  CardContent,
  Stack,
} from '@mui/material'
import { responsiveStyles } from '../styles/responsiveStyles'

interface Column {
  key: string
  label: string
  align?: 'left' | 'right' | 'center'
  render?: (value: any, row: any) => React.ReactNode
  hidden?: boolean
}

interface ResponsiveTableProps {
  columns: Column[]
  data: any[]
  loading?: boolean
  emptyMessage?: string
  striped?: boolean
  hover?: boolean
}

export const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
  columns,
  data,
  loading = false,
  emptyMessage = 'Aucune donnée disponible',
  striped = true,
  hover = true,
}) => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

  // Version mobile: cartes
  if (isMobile) {
    return (
      <Stack spacing={2}>
        {data.length === 0 ? (
          <Box sx={responsiveStyles.flexCenter}>
            <Typography color="textSecondary">{emptyMessage}</Typography>
          </Box>
        ) : (
          data.map((row, idx) => (
            <Card key={idx} sx={responsiveStyles.card}>
              <CardContent>
                <Stack spacing={1}>
                  {columns
                    .filter((col) => !col.hidden)
                    .map((col) => (
                      <Box key={col.key} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" fontWeight={600} color="textSecondary">
                          {col.label}
                        </Typography>
                        <Typography variant="body2">
                          {col.render ? col.render(row[col.key], row) : row[col.key]}
                        </Typography>
                      </Box>
                    ))}
                </Stack>
              </CardContent>
            </Card>
          ))
        )}
      </Stack>
    )
  }

  // Version desktop: tableau
  return (
    <TableContainer component={Paper} sx={responsiveStyles.tableContainer}>
      <Table stickyHeader>
        <TableHead>
          <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
            {columns
              .filter((col) => !col.hidden)
              .map((col) => (
                <TableCell
                  key={col.key}
                  align={col.align || 'left'}
                  sx={{
                    fontWeight: 700,
                    backgroundColor: '#f5f5f5',
                    fontSize: { xs: '12px', md: '14px' },
                    color: '#666',
                  }}
                >
                  {col.label}
                </TableCell>
              ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.filter((c) => !c.hidden).length} align="center">
                <Typography color="textSecondary" sx={{ py: 3 }}>
                  {emptyMessage}
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            data.map((row, idx) => (
              <TableRow
                key={idx}
                sx={{
                  backgroundColor: striped && idx % 2 !== 0 ? '#fafafa' : '#fff',
                  '&:hover': hover ? { backgroundColor: '#f0f0f0' } : {},
                  transition: 'background-color 0.2s',
                }}
              >
                {columns
                  .filter((col) => !col.hidden)
                  .map((col) => (
                    <TableCell key={col.key} align={col.align || 'left'}>
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </TableCell>
                  ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
