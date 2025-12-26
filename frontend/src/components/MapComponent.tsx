import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import { Box, Paper, Typography, CircularProgress, Alert, Button, Stack } from '@mui/material'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Icônes personnalisées
const createIcon = (color: string, label: string) => {
  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        color: white;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        border: 2px solid white;
        font-size: 12px;
      ">
        ${label}
      </div>
    `,
    iconSize: [40, 40],
    className: 'custom-icon',
  })
}

interface Location {
  id: number
  name: string
  latitude: number
  longitude: number
  type: 'city' | 'trip_start' | 'trip_end' | 'stop'
  description?: string
  color?: string
}

interface MapComponentProps {
  locations: Location[]
  routes?: Array<{ start: [number, number]; end: [number, number]; color?: string }>
  zoom?: number
  center?: [number, number]
  height?: string
  loading?: boolean
  onLocationClick?: (location: Location) => void
}

// Composant pour contrôler la vue de la carte
const MapController: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap()

  useEffect(() => {
    if (map) {
      map.setView(center, zoom)
    }
  }, [center, zoom, map])

  return null
}

export const MapComponent: React.FC<MapComponentProps> = ({
  locations = [],
  routes = [],
  zoom = 7,
  center = [12.3714, -1.5197], // Burkina Faso center
  height = '600px',
  loading = false,
  onLocationClick,
}) => {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null)

  const handleLocationClick = (location: Location) => {
    setSelectedLocation(location)
    onLocationClick?.(location)
  }

  const getColor = (type: string, customColor?: string) => {
    if (customColor) return customColor
    switch (type) {
      case 'city':
        return '#007A5E' // Vert TKF
      case 'trip_start':
        return '#CE1126' // Rouge TKF
      case 'trip_end':
        return '#FFD700' // Or TKF
      case 'stop':
        return '#667eea'
      default:
        return '#666'
    }
  }

  const getLabel = (type: string) => {
    switch (type) {
      case 'city':
        return '🏙️'
      case 'trip_start':
        return '📍'
      case 'trip_end':
        return '🎯'
      case 'stop':
        return '🛑'
      default:
        return '•'
    }
  }

  return (
    <Paper sx={{ height, position: 'relative', overflow: 'hidden' }}>
      {loading && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <CircularProgress />
          <Typography>Chargement de la carte...</Typography>
        </Box>
      )}

      {locations.length === 0 && !loading && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 500,
            textAlign: 'center',
          }}
        >
          <Alert severity="info">Aucune localisation à afficher</Alert>
        </Box>
      )}

      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        {/* Couche de tuiles OpenStreetMap */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Contrôleur de la vue */}
        <MapController center={center} zoom={zoom} />

        {/* Lignes des trajets */}
        {routes.map((route, idx) => (
          <Polyline
            key={`route-${idx}`}
            positions={[route.start, route.end]}
            color={route.color || '#667eea'}
            weight={3}
            opacity={0.7}
            dashArray="5, 5"
          />
        ))}

        {/* Marqueurs des localités */}
        {locations.map((location) => (
          <Marker
            key={`marker-${location.id}`}
            position={[location.latitude, location.longitude]}
            icon={createIcon(getColor(location.type, location.color), getLabel(location.type))}
            eventHandlers={{
              click: () => handleLocationClick(location),
            }}
          >
            <Popup>
              <Box sx={{ minWidth: '200px' }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                  {location.name}
                </Typography>
                {location.description && (
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                    {location.description}
                  </Typography>
                )}
                <Typography variant="caption" color="textSecondary">
                  Lat: {location.latitude.toFixed(4)} | Lon: {location.longitude.toFixed(4)}
                </Typography>
              </Box>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Légende */}
      <Paper
        sx={{
          position: 'absolute',
          bottom: 20,
          right: 20,
          p: 2,
          zIndex: 400,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(5px)',
        }}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
          Légende
        </Typography>
        <Stack spacing={0.5}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 20,
                height: 20,
                borderRadius: '50%',
                backgroundColor: '#007A5E',
                border: '2px solid white',
              }}
            />
            <Typography variant="caption">Ville</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 20,
                height: 20,
                borderRadius: '50%',
                backgroundColor: '#CE1126',
                border: '2px solid white',
              }}
            />
            <Typography variant="caption">Départ</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 20,
                height: 20,
                borderRadius: '50%',
                backgroundColor: '#FFD700',
                border: '2px solid white',
              }}
            />
            <Typography variant="caption">Arrivée</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 20,
                height: 20,
                borderRadius: '50%',
                backgroundColor: '#667eea',
                border: '2px solid white',
              }}
            />
            <Typography variant="caption">Arrêt</Typography>
          </Box>
        </Stack>
      </Paper>

      {/* Informations du marqueur sélectionné */}
      {selectedLocation && (
        <Paper
          sx={{
            position: 'absolute',
            top: 20,
            left: 20,
            p: 2,
            zIndex: 400,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(5px)',
            minWidth: '250px',
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
              {selectedLocation.name}
            </Typography>
            <Button
              size="small"
              onClick={() => setSelectedLocation(null)}
              sx={{ minWidth: 'auto', p: 0 }}
            >
              ✕
            </Button>
          </Box>
          {selectedLocation.description && (
            <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
              {selectedLocation.description}
            </Typography>
          )}
          <Typography variant="caption" display="block">
            <strong>Latitude:</strong> {selectedLocation.latitude.toFixed(6)}
          </Typography>
          <Typography variant="caption" display="block">
            <strong>Longitude:</strong> {selectedLocation.longitude.toFixed(6)}
          </Typography>
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            <strong>Type:</strong> {selectedLocation.type}
          </Typography>
        </Paper>
      )}
    </Paper>
  )
}

export default MapComponent
