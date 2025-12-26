// src/components/ResponsiveAppBar.tsx
/**
 * App Bar responsive avec menu collapsible sur mobile
 */

import React from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Box,
  useMediaQuery,
  useTheme,
  Avatar,
  Stack,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  AccountCircle as AccountIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material'

interface NavItem {
  label: string
  path: string
  icon?: React.ReactNode
}

interface ResponsiveAppBarProps {
  title: string
  navItems?: NavItem[]
  onNavigate?: (path: string) => void
  userInitials?: string
  userName?: string
  onLogout?: () => void
}

export const ResponsiveAppBar: React.FC<ResponsiveAppBarProps> = ({
  title,
  navItems = [],
  onNavigate,
  userInitials = 'U',
  userName = 'Utilisateur',
  onLogout,
}) => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)
  const [userMenuOpen, setUserMenuOpen] = React.useState(false)
  const [userMenuAnchor, setUserMenuAnchor] = React.useState<null | HTMLElement>(null)

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget)
    setUserMenuOpen(true)
  }

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null)
    setUserMenuOpen(false)
  }

  return (
    <>
      <AppBar position="sticky" sx={{ backgroundColor: '#CE1126', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 1, md: 3 } }}>
          {/* Logo/Title */}
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              fontSize: { xs: '16px', md: '20px' },
              cursor: 'pointer',
            }}
          >
            {title}
          </Typography>

          {/* Desktop Navigation */}
          {!isMobile && (
            <Stack direction="row" spacing={2}>
              {navItems.map((item) => (
                <Button
                  key={item.path}
                  color="inherit"
                  onClick={() => onNavigate?.(item.path)}
                  sx={{ textTransform: 'none', fontSize: '14px' }}
                >
                  {item.label}
                </Button>
              ))}
            </Stack>
          )}

          {/* User Menu + Mobile Menu */}
          <Stack direction="row" spacing={1} alignItems="center">
            {/* User Avatar */}
            <IconButton
              onClick={handleUserMenuOpen}
              sx={{ color: 'white' }}
              size="small"
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  backgroundColor: 'rgba(255,255,255,0.3)',
                  fontSize: '12px',
                }}
              >
                {userInitials}
              </Avatar>
            </IconButton>

            {/* Mobile Menu Icon */}
            {isMobile && (
              <IconButton
                color="inherit"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                size="small"
              >
                {mobileMenuOpen ? <CloseIcon /> : <MenuIcon />}
              </IconButton>
            )}
          </Stack>
        </Toolbar>

        {/* Mobile Navigation */}
        {isMobile && mobileMenuOpen && (
          <Box sx={{ backgroundColor: 'rgba(0,0,0,0.1)', px: 2, py: 1 }}>
            {navItems.map((item) => (
              <Button
                key={item.path}
                fullWidth
                color="inherit"
                onClick={() => {
                  onNavigate?.(item.path)
                  setMobileMenuOpen(false)
                }}
                sx={{ justifyContent: 'flex-start', textTransform: 'none', py: 1 }}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        )}
      </AppBar>

      {/* User Menu */}
      <Menu
        anchorEl={userMenuAnchor}
        open={userMenuOpen}
        onClose={handleUserMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem disabled>
          <Typography variant="caption">{userName}</Typography>
        </MenuItem>
        <MenuItem onClick={() => { onNavigate?.('/profile'); handleUserMenuClose() }}>
          <AccountIcon sx={{ mr: 1 }} /> Profil
        </MenuItem>
        <MenuItem onClick={() => { onLogout?.(); handleUserMenuClose() }}>
          <LogoutIcon sx={{ mr: 1 }} /> Déconnexion
        </MenuItem>
      </Menu>
    </>
  )
}
