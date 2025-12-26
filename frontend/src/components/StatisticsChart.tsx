import React from 'react'
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
import { Box, Card, CardContent, Typography, Paper, Grid } from '@mui/material'

const COLORS = ['#CE1126', '#007A5E', '#FFD700', '#667eea', '#f093fb', '#4facfe', '#fa709a', '#fee140']

interface ChartDataPoint {
  name: string
  [key: string]: string | number
}

interface StatisticsChartProps {
  data: ChartDataPoint[]
  type: 'line' | 'bar' | 'pie' | 'area'
  title: string
  dataKeys: string[]
  height?: number
  xAxisKey?: string
  colors?: string[]
}

export const StatisticsChart: React.FC<StatisticsChartProps> = ({
  data,
  type,
  title,
  dataKeys,
  height = 300,
  xAxisKey = 'name',
  colors = COLORS,
}) => {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="textSecondary">Aucune donnée disponible</Typography>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
          {title}
        </Typography>
        <ResponsiveContainer width="100%" height={height}>
          {type === 'line' && (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xAxisKey} />
              <YAxis />
              <Tooltip
                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', borderRadius: '8px' }}
                formatter={(value) => (typeof value === 'number' ? value.toLocaleString() : value)}
              />
              <Legend />
              {dataKeys.map((key, idx) => (
                <Line
                  key={`line-${key}`}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[idx % colors.length]}
                  strokeWidth={2}
                  dot={{ fill: colors[idx % colors.length], r: 4 }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          )}

          {type === 'bar' && (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xAxisKey} />
              <YAxis />
              <Tooltip
                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', borderRadius: '8px' }}
                formatter={(value) => (typeof value === 'number' ? value.toLocaleString() : value)}
              />
              <Legend />
              {dataKeys.map((key, idx) => (
                <Bar key={`bar-${key}`} dataKey={key} fill={colors[idx % colors.length]} />
              ))}
            </BarChart>
          )}

          {type === 'area' && (
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={colors[0]} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={colors[0]} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xAxisKey} />
              <YAxis />
              <Tooltip
                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', borderRadius: '8px' }}
                formatter={(value) => (typeof value === 'number' ? value.toLocaleString() : value)}
              />
              <Legend />
              {dataKeys.map((key, idx) => (
                <Area
                  key={`area-${key}`}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[idx % colors.length]}
                  fill={idx === 0 ? 'url(#colorGradient)' : colors[idx % colors.length]}
                  fillOpacity={0.6}
                />
              ))}
            </AreaChart>
          )}

          {type === 'pie' && (
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey={dataKeys[0] || 'value'}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => (typeof value === 'number' ? value.toLocaleString() : value)}
              />
              <Legend />
            </PieChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

interface DashboardChartsProps {
  tripData?: ChartDataPoint[]
  revenueData?: ChartDataPoint[]
  employeeData?: ChartDataPoint[]
  cityData?: ChartDataPoint[]
}

export const DashboardCharts: React.FC<DashboardChartsProps> = ({
  tripData = [],
  revenueData = [],
  employeeData = [],
  cityData = [],
}) => {
  return (
    <Grid container spacing={3}>
      {tripData.length > 0 && (
        <Grid item xs={12} md={6}>
          <StatisticsChart
            data={tripData}
            type="line"
            title="Trajets par jour"
            dataKeys={['completed', 'pending', 'cancelled']}
            height={300}
          />
        </Grid>
      )}

      {revenueData.length > 0 && (
        <Grid item xs={12} md={6}>
          <StatisticsChart
            data={revenueData}
            type="area"
            title="Chiffre d'affaires"
            dataKeys={['revenue']}
            height={300}
          />
        </Grid>
      )}

      {employeeData.length > 0 && (
        <Grid item xs={12} md={6}>
          <StatisticsChart
            data={employeeData}
            type="bar"
            title="Employés par département"
            dataKeys={['count']}
            height={300}
          />
        </Grid>
      )}

      {cityData.length > 0 && (
        <Grid item xs={12} md={6}>
          <StatisticsChart
            data={cityData}
            type="pie"
            title="Répartition par région"
            dataKeys={['count']}
            height={300}
          />
        </Grid>
      )}
    </Grid>
  )
}

export default StatisticsChart
