import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'

interface ChartDataPoint {
  name: string
  value: number
  [key: string]: any
}

interface AdvancedChartsProps {
  data: ChartDataPoint[]
  title?: string
  subtitle?: string
}

const COLORS = ['#CE1126', '#007A5E', '#FFD700', '#667eea', '#764ba2', '#f093fb', '#f5576c']

/**
 * Graphique en courbe
 */
export const LineChartComponent: React.FC<{
  data: ChartDataPoint[]
  dataKey: string
  title: string
  color?: string
}> = ({ data, dataKey, title, color = '#CE1126' }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
        {title}
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: `2px solid ${color}`,
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={{ fill: color }} />
        </LineChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>
)

/**
 * Graphique en barres
 */
export const BarChartComponent: React.FC<{
  data: ChartDataPoint[]
  dataKey: string
  title: string
  color?: string
}> = ({ data, dataKey, title, color = '#007A5E' }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
        {title}
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: `2px solid ${color}`,
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Bar dataKey={dataKey} fill={color} radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>
)

/**
 * Graphique en camembert
 */
export const PieChartComponent: React.FC<{
  data: ChartDataPoint[]
  dataKey: string
  title: string
}> = ({ data, dataKey, title }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
        {title}
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey={dataKey}
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '2px solid #CE1126',
              borderRadius: '8px',
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>
)

/**
 * Graphique en aire (Area Chart)
 */
export const AreaChartComponent: React.FC<{
  data: ChartDataPoint[]
  dataKey: string
  title: string
  color?: string
}> = ({ data, dataKey, title, color = '#667eea' }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
        {title}
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: `2px solid ${color}`,
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Area type="monotone" dataKey={dataKey} fill={color} stroke={color} fillOpacity={0.3} />
        </AreaChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>
)

/**
 * Tableau de bord complet avec plusieurs graphiques
 */
export const AdvancedDashboard: React.FC<AdvancedChartsProps> = ({
  data,
  title = 'Tableau de bord analytique',
  subtitle = 'Analyse détaillée des performances',
}) => {
  const [chartType, setChartType] = React.useState<'line' | 'bar' | 'pie' | 'area'>('line')

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 700, color: '#CE1126' }}>
                {title}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            </Box>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Type de graphique</InputLabel>
              <Select
                value={chartType}
                label="Type de graphique"
                onChange={(e) => setChartType(e.target.value as any)}
              >
                <MenuItem value="line">Courbe</MenuItem>
                <MenuItem value="bar">Barres</MenuItem>
                <MenuItem value="area">Aire</MenuItem>
                <MenuItem value="pie">Camembert</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          {chartType === 'line' && (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '2px solid #CE1126',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line type="monotone" dataKey="value" stroke="#CE1126" strokeWidth={2} dot={{ fill: '#CE1126' }} />
              </LineChart>
            </ResponsiveContainer>
          )}

          {chartType === 'bar' && (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '2px solid #007A5E',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar dataKey="value" fill="#007A5E" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}

          {chartType === 'area' && (
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '2px solid #667eea',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Area type="monotone" dataKey="value" fill="#667eea" stroke="#667eea" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          )}

          {chartType === 'pie' && (
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                  label
                >
                  {data.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '2px solid #CE1126',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}

export default {
  LineChartComponent,
  BarChartComponent,
  PieChartComponent,
  AreaChartComponent,
  AdvancedDashboard,
}
