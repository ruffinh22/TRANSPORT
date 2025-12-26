import React from 'react'
import {
  AppBar,
  Toolbar,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Avatar,
  Tooltip,
  Badge,
  Typography,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
// Notification services - optional imports
// import { useNotification } from '../../services/NotificationService'
// import { useWebSocketNotifications } from '../../services/WebSocketService'

interface EnhancedHeaderProps {
  onMenuClick?: () => void
  userInitials?: string
}

/**
 * En-tête amélioré avec notifications et menu utilisateur
 */
export const EnhancedHeader: React.FC<EnhancedHeaderProps> = ({
  onMenuClick,
  userInitials = 'JD',
}) => {
  const navigate = useNavigate()
  const { notifications } = useNotification()
  const { isConnected } = useWebSocketNotifications('')
  
  const [anchorElUser, setAnchorElUser] = React.useState<null | HTMLElement>(null)
  const [anchorElNotif, setAnchorElNotif] = React.useState<null | HTMLElement>(null)

  const handleOpenUserMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElUser(event.currentTarget)
  }

  const handleCloseUserMenu = () => {
    setAnchorElUser(null)
  }

  const handleOpenNotifications = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElNotif(event.currentTarget)
  }

  const handleCloseNotifications = () => {
    setAnchorElNotif(null)
  }

  const handleProfileClick = () => {
    navigate('/profile')
    handleCloseUserMenu()
  }

  const handleSettingsClick = () => {
    navigate('/settings')
    handleCloseUserMenu()
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
    handleCloseUserMenu()
  }

  return (
    <AppBar position="sticky" sx={{ backgroundColor: '#CE1126' }}>
      <Toolbar>
        {/* Menu mobile */}
        <IconButton
          size="large"
          edge="start"
          color="inherit"
          aria-label="menu"
          sx={{ mr: 2, display: { xs: 'flex', md: 'none' } }}
          onClick={onMenuClick}
        >
          <MenuIcon />
        </IconButton>

        {/* Titre */}
        <Typography
          variant="h6"
          sx={{
            flexGrow: 1,
            fontWeight: 'bold',
            display: { xs: 'none', sm: 'block' },
          }}
        >
          TKF Transport
        </Typography>

        {/* Statut de connexion WebSocket */}
        <Box sx={{ mr: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: isConnected ? '#4caf50' : '#f44336',
            }}
          />
          <Typography variant="caption" sx={{ display: { xs: 'none', sm: 'block' } }}>
            {isConnected ? 'Connecté' : 'Déconnecté'}
          </Typography>
        </Box>

        {/* Notifications */}
        <Tooltip title="Notifications">
          <IconButton
            color="inherit"
            onClick={handleOpenNotifications}
            sx={{ mr: 1 }}
          >
            <Badge badgeContent={notifications.length} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Tooltip>

        {/* Menu utilisateur */}
        <Tooltip title="Compte">
          <IconButton onClick={handleOpenUserMenu} sx={{ p: 0 }}>
            <Avatar sx={{ bgcolor: '#007A5E', width: 32, height: 32 }}>
              {userInitials}
            </Avatar>
          </IconButton>
        </Tooltip>

        {/* Menu utilisateur dropdown */}
        <Menu
          sx={{ mt: '45px' }}
          anchorEl={anchorElUser}
          anchorOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          keepMounted
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(anchorElUser)}
          onClose={handleCloseUserMenu}
        >
          <MenuItem onClick={handleProfileClick}>
            <PersonIcon sx={{ mr: 1 }} />
            Mon Profil
          </MenuItem>
          <MenuItem onClick={handleSettingsClick}>
            <SettingsIcon sx={{ mr: 1 }} />
            Paramètres
          </MenuItem>
          <MenuItem onClick={handleLogout}>
            <LogoutIcon sx={{ mr: 1 }} />
            Déconnexion
          </MenuItem>
        </Menu>

        {/* Menu notifications dropdown */}
        <Menu
          sx={{ mt: '45px' }}
          anchorEl={anchorElNotif}
          anchorOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          keepMounted
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(anchorElNotif)}
          onClose={handleCloseNotifications}
        >
          {notifications.length === 0 ? (
            <MenuItem disabled>Aucune notification</MenuItem>
          ) : (
            notifications.map((notif) => (
              <MenuItem key={notif.id} onClick={handleCloseNotifications}>
                <Box>
                  {notif.title && (
                    <Typography variant="subtitle2">{notif.title}</Typography>
                  )}
                  <Typography variant="body2" color="textSecondary">
                    {notif.message}
                  </Typography>
                </Box>
              </MenuItem>
            ))
          )}
        </Menu>
      </Toolbar>
    </AppBar>
  )
}

export default EnhancedHeader
