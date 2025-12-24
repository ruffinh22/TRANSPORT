import React, { useState } from 'react'
import {
  Box,
  Container,
  Stack,
  Typography,
  Button,
  Menu,
  MenuItem,
  Divider,
  Paper,
} from '@mui/material'
import {
  Language as LanguageIcon,
  Info as InfoIcon,
  Help as HelpIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
} from '@mui/icons-material'

interface GovernmentHeaderProps {
  language?: 'fr' | 'en'
  onLanguageChange?: (lang: 'fr' | 'en') => void
}

export const GovernmentHeader: React.FC<GovernmentHeaderProps> = ({
  language = 'fr',
  onLanguageChange,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [langAnchor, setLangAnchor] = useState<null | HTMLElement>(null)

  const handleInfoOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleInfoClose = () => {
    setAnchorEl(null)
  }

  const handleLangOpen = (event: React.MouseEvent<HTMLElement>) => {
    setLangAnchor(event.currentTarget)
  }

  const handleLangClose = () => {
    setLangAnchor(null)
  }

  const handleLanguageChange = (lang: 'fr' | 'en') => {
    if (onLanguageChange) {
      onLanguageChange(lang)
    }
    handleLangClose()
  }

  const translations = {
    fr: {
      motto: 'Unité - Progrès - Travail',
      country: 'République du Burkina Faso',
      ministry: 'Ministère des Transports et de la Mobilité Urbaine',
      portal: 'Portail de Gestion Intégrée du Transport',
      support: 'Support & Aide',
      about: 'À propos',
      contact: 'Contact',
      email: 'support@transport.bf',
      phone: '+226 25 30 00 00',
      hours: 'Lun-Ven: 07:00-18:00',
      legal: 'Mentions légales',
      privacy: 'Politique de confidentialité',
      accessibility: 'Accessibilité',
      lang: 'Langue',
    },
    en: {
      motto: 'Unity - Progress - Labor',
      country: 'Republic of Burkina Faso',
      ministry: 'Ministry of Transport and Urban Mobility',
      portal: 'Integrated Transport Management Portal',
      support: 'Support & Help',
      about: 'About',
      contact: 'Contact',
      email: 'support@transport.bf',
      phone: '+226 25 30 00 00',
      hours: 'Mon-Fri: 07:00-18:00',
      legal: 'Legal Notice',
      privacy: 'Privacy Policy',
      accessibility: 'Accessibility',
      lang: 'Language',
    },
  }

  const t = translations[language]

  return (
    <Box sx={{ backgroundColor: '#ffffff' }}>
      {/* Top Info Bar */}
      <Box
        sx={{
          background: 'linear-gradient(90deg, #1a1a1a 0%, #333333 100%)',
          color: 'white',
          py: 1,
          borderBottom: '2px solid #CE1126',
        }}
      >
        <Container maxWidth="lg">
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            justifyContent="space-between"
            alignItems="center"
            sx={{ fontSize: '0.85rem' }}
          >
            <Stack direction="row" spacing={3}>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <PhoneIcon sx={{ fontSize: '0.9rem' }} />
                <Typography variant="caption">{t.phone}</Typography>
              </Stack>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <EmailIcon sx={{ fontSize: '0.9rem' }} />
                <Typography variant="caption">{t.email}</Typography>
              </Stack>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                {t.hours}
              </Typography>
            </Stack>
            <Stack direction="row" spacing={1}>
              <Button
                size="small"
                startIcon={<LanguageIcon sx={{ fontSize: '1rem' }} />}
                onClick={handleLangOpen}
                sx={{
                  color: 'white',
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.1)' },
                }}
              >
                {language.toUpperCase()}
              </Button>
              <Menu
                anchorEl={langAnchor}
                open={Boolean(langAnchor)}
                onClose={handleLangClose}
              >
                <MenuItem
                  onClick={() => handleLanguageChange('fr')}
                  selected={language === 'fr'}
                >
                  Français 🇧🇫
                </MenuItem>
                <MenuItem
                  onClick={() => handleLanguageChange('en')}
                  selected={language === 'en'}
                >
                  English 🇬🇧
                </MenuItem>
              </Menu>
            </Stack>
          </Stack>
        </Container>
      </Box>

      {/* Official Seal & Title Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
          py: 3,
          borderBottom: '3px solid #CE1126',
        }}
      >
        <Container maxWidth="lg">
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems="center" justifyContent="space-between">
            {/* Left: Coat of Arms & Country Info */}
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              sx={{ flex: { xs: 1, md: 'initial' } }}
            >
              {/* Coat of Arms Placeholder */}
              <Box
                sx={{
                  width: 60,
                  height: 60,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFD700',
                  fontWeight: 700,
                  fontSize: '1.8rem',
                }}
              >
                ★
              </Box>

              {/* Country & Ministry Info */}
              <Stack spacing={0.5}>
                <Typography
                  variant="overline"
                  sx={{
                    fontWeight: 700,
                    letterSpacing: '2px',
                    color: '#CE1126',
                    fontSize: '0.75rem',
                  }}
                >
                  {t.country}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 600,
                    color: '#1a1a1a',
                  }}
                >
                  {t.ministry}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: '#007A5E',
                    fontStyle: 'italic',
                  }}
                >
                  {t.motto}
                </Typography>
              </Stack>
            </Stack>

            {/* Center: Portal Title */}
            <Stack alignItems="center" spacing={1} sx={{ flex: 1 }}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  textAlign: 'center',
                }}
              >
                {t.portal}
              </Typography>
              <Box
                sx={{
                  width: 80,
                  height: '2px',
                  background: 'linear-gradient(90deg, #CE1126 0%, #007A5E 100%)',
                }}
              />
              <Typography
                variant="caption"
                sx={{
                  color: '#666',
                  fontWeight: 500,
                  textAlign: 'center',
                }}
              >
                Système Officiel du Gouvernement
              </Typography>
            </Stack>

            {/* Right: Help & Legal Links */}
            <Stack direction="row" spacing={1}>
              <Button
                size="small"
                startIcon={<HelpIcon />}
                onClick={handleInfoOpen}
                sx={{
                  color: '#007A5E',
                  borderColor: '#007A5E',
                }}
                variant="outlined"
              >
                {t.support}
              </Button>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleInfoClose}
              >
                <MenuItem>{t.about}</MenuItem>
                <MenuItem>{t.contact}</MenuItem>
                <Divider />
                <MenuItem>{t.legal}</MenuItem>
                <MenuItem>{t.privacy}</MenuItem>
                <MenuItem>{t.accessibility}</MenuItem>
              </Menu>
            </Stack>
          </Stack>
        </Container>
      </Box>
      <Box
        sx={{
          background: '#f0f0f0',
          borderBottom: '1px solid #e0e0e0',
          py: 1.5,
        }}
      >
        <Container maxWidth="lg">
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={2}
            alignItems="center"
            justifyContent="space-between"
            sx={{ fontSize: '0.8rem' }}
          >
            <Stack direction="row" spacing={2} alignItems="center">
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  color: '#CE1126',
                  fontWeight: 600,
                }}
              >
                ✓ ISO 27001
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  color: '#CE1126',
                  fontWeight: 600,
                }}
              >
                ✓ OHADA Compliant
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  color: '#CE1126',
                  fontWeight: 600,
                }}
              >
                ✓ WCAG 2.1 AA
              </Box>
            </Stack>
            <Typography variant="caption" sx={{ color: '#666', fontStyle: 'italic' }}>
              Plateforme Officielle • Données Sécurisées • Audit Gouvernemental Complet
            </Typography>
          </Stack>
        </Container>
      </Box>
    </Box>
  )
}
