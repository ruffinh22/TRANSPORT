import React from 'react'
import {
  Box,
  Container,
  Grid,
  Typography,
  Stack,
  Divider,
  Link,
  Paper,
} from '@mui/material'
import {
  Place as PlaceIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Public as PublicIcon,
} from '@mui/icons-material'

interface GovernmentFooterProps {
  language?: 'fr' | 'en'
}

export const GovernmentFooter: React.FC<GovernmentFooterProps> = ({ language = 'fr' }) => {
  const translations = {
    fr: {
      quickLinks: 'Liens Rapides',
      services: 'Services',
      contact: 'Contact',
      legal: 'Légal',
      followUs: 'Nous Suivre',
      address: 'Ouagadougou, Burkina Faso',
      phone: '+226 25 30 00 00',
      email: 'support@transport.bf',
      website: 'www.transport.bf',
      dashboard: 'Tableau de Bord',
      tracking: 'Suivi en Temps Réel',
      reports: 'Rapports',
      settings: 'Paramètres',
      home: 'Accueil',
      about: 'À Propos',
      faq: 'FAQ',
      legal_notice: 'Mentions Légales',
      privacy: 'Politique de Confidentialité',
      terms: 'Conditions d\'Utilisation',
      accessibility: 'Accessibilité',
      cookies: 'Gestion des Cookies',
      copyright: '© 2025 Gouvernement du Burkina Faso. Tous droits réservés.',
      ministry: 'Ministère des Transports et de la Mobilité Urbaine',
      version: 'v1.0.0 - Dernière mise à jour:',
      certification: 'Certifiée conforme aux normes ISO 27001, OHADA et WCAG 2.1 AA',
      support_hours: 'Horaires d\'assistance: Lun-Ven 07:00-18:00 GMT',
      responsable: 'Portail Officiel de Gestion du Transport',
    },
    en: {
      quickLinks: 'Quick Links',
      services: 'Services',
      contact: 'Contact',
      legal: 'Legal',
      followUs: 'Follow Us',
      address: 'Ouagadougou, Burkina Faso',
      phone: '+226 25 30 00 00',
      email: 'support@transport.bf',
      website: 'www.transport.bf',
      dashboard: 'Dashboard',
      tracking: 'Real-Time Tracking',
      reports: 'Reports',
      settings: 'Settings',
      home: 'Home',
      about: 'About',
      faq: 'FAQ',
      legal_notice: 'Legal Notice',
      privacy: 'Privacy Policy',
      terms: 'Terms of Service',
      accessibility: 'Accessibility',
      cookies: 'Cookie Management',
      copyright: '© 2025 Government of Burkina Faso. All rights reserved.',
      ministry: 'Ministry of Transport and Urban Mobility',
      version: 'v1.0.0 - Last updated:',
      certification: 'Certified compliant with ISO 27001, OHADA and WCAG 2.1 AA standards',
      support_hours: 'Support hours: Mon-Fri 07:00-18:00 GMT',
      responsable: 'Official Transport Management Portal',
    },
  }

  const t = translations[language]

  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: '#1a1a1a',
        color: 'white',
        pt: 6,
        borderTop: '4px solid #CE1126',
      }}
    >
      <Container maxWidth="lg">
        {/* Main Footer Content */}
        <Grid container spacing={4} sx={{ mb: 4 }}>
          {/* Ministry Info */}
          <Grid item xs={12} sm={6} md={3}>
            <Stack spacing={2}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <Box
                  sx={{
                    width: 50,
                    height: 50,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                    color: '#FFD700',
                  }}
                >
                  ★
                </Box>
                <Stack spacing={0}>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: '#EF3B39' }}>
                    Burkina Faso
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.8 }}>
                    {t.responsable}
                  </Typography>
                </Stack>
              </Box>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                {t.ministry}
              </Typography>
            </Stack>
          </Grid>

          {/* Services */}
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, color: '#CE1126' }}>
              {t.services}
            </Typography>
            <Stack spacing={1}>
              <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85 }}>
                {t.dashboard}
              </Link>
              <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85 }}>
                {t.tracking}
              </Link>
              <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85 }}>
                {t.reports}
              </Link>
              <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85 }}>
                {t.settings}
              </Link>
            </Stack>
          </Grid>

          {/* Quick Links */}
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, color: '#007A5E' }}>
              {t.quickLinks}
            </Typography>
            <Stack spacing={1}>
              <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85 }}>
                {t.home}
              </Link>
              <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85 }}>
                {t.about}
              </Link>
              <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85 }}>
                {t.faq}
              </Link>
              <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85 }}>
                {t.contact}
              </Link>
            </Stack>
          </Grid>

          {/* Contact */}
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, color: '#CE1126' }}>
              {t.contact}
            </Typography>
            <Stack spacing={1.5}>
              <Stack direction="row" spacing={1} alignItems="flex-start">
                <PlaceIcon sx={{ fontSize: '1.2rem', mt: 0.5, flexShrink: 0 }} />
                <Box>
                  <Typography variant="caption" sx={{ opacity: 0.8, display: 'block' }}>
                    {t.address}
                  </Typography>
                </Box>
              </Stack>
              <Stack direction="row" spacing={1} alignItems="center">
                <PhoneIcon sx={{ fontSize: '1rem', flexShrink: 0 }} />
                <Link href={`tel:+22625300000`} underline="hover" sx={{ color: 'white' }}>
                  {t.phone}
                </Link>
              </Stack>
              <Stack direction="row" spacing={1} alignItems="center">
                <EmailIcon sx={{ fontSize: '1rem', flexShrink: 0 }} />
                <Link href={`mailto:${t.email}`} underline="hover" sx={{ color: 'white' }}>
                  {t.email}
                </Link>
              </Stack>
            </Stack>
          </Grid>
        </Grid>

        <Divider sx={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', my: 3 }} />

        {/* Legal Links */}
        <Box sx={{ mb: 3, pb: 3, borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ flexWrap: 'wrap' }}>
            <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85, fontSize: '0.9rem' }}>
              {t.legal_notice}
            </Link>
            <Typography sx={{ color: 'white', opacity: 0.4 }}>•</Typography>
            <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85, fontSize: '0.9rem' }}>
              {t.privacy}
            </Link>
            <Typography sx={{ color: 'white', opacity: 0.4 }}>•</Typography>
            <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85, fontSize: '0.9rem' }}>
              {t.terms}
            </Link>
            <Typography sx={{ color: 'white', opacity: 0.4 }}>•</Typography>
            <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85, fontSize: '0.9rem' }}>
              {t.accessibility}
            </Link>
            <Typography sx={{ color: 'white', opacity: 0.4 }}>•</Typography>
            <Link href="#" underline="hover" sx={{ color: 'white', opacity: 0.85, fontSize: '0.9rem' }}>
              {t.cookies}
            </Link>
          </Stack>
        </Box>

        {/* Certification Bar */}
        <Paper
          sx={{
            backgroundColor: 'rgba(206, 17, 38, 0.1)',
            border: '1px solid #CE1126',
            p: 2,
            mb: 3,
          }}
        >
          <Stack spacing={1}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                color: '#CE1126',
                textAlign: 'center',
              }}
            >
              ✓ {t.certification}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: 'white',
                opacity: 0.8,
                textAlign: 'center',
                display: 'block',
              }}
            >
              {t.support_hours}
            </Typography>
          </Stack>
        </Paper>

        {/* Bottom Footer */}
        <Box sx={{ textAlign: 'center', py: 3, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Stack spacing={1} alignItems="center">
            <Typography variant="caption" sx={{ color: 'white', opacity: 0.8 }}>
              {t.copyright}
            </Typography>
            <Typography variant="caption" sx={{ color: 'white', opacity: 0.6 }}>
              {t.version} {new Date().toLocaleDateString('fr-FR')}
            </Typography>
            <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 2 }}>
              <Link href="#" underline="none" sx={{ color: '#CE1126', opacity: 0.8, '&:hover': { opacity: 1 } }}>
                Facebook
              </Link>
              <Link href="#" underline="none" sx={{ color: '#CE1126', opacity: 0.8, '&:hover': { opacity: 1 } }}>
                Twitter
              </Link>
              <Link href="#" underline="none" sx={{ color: '#CE1126', opacity: 0.8, '&:hover': { opacity: 1 } }}>
                LinkedIn
              </Link>
            </Stack>
          </Stack>
        </Box>
      </Container>
    </Box>
  )
}
