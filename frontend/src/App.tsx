import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { Provider } from 'react-redux'
import { store } from './store'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { TripsPage } from './pages/TripsPage'
import { TicketsPage } from './pages/TicketsPage'
import { ParcelsPage } from './pages/ParcelsPage'
import { PaymentsPage } from './pages/PaymentsPage'
import EmployeesPage from './pages/EmployeesPage'
import { CitiesPage } from './pages/CitiesPage'
import ReportsPage from './pages/ReportsPage'
import { LandingPage } from './pages/LandingPage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { governmentTheme } from './theme/governmentTheme'

const AppContent: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<LandingPage />} />
      
      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/trips"
        element={
          <ProtectedRoute>
            <TripsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tickets"
        element={
          <ProtectedRoute>
            <TicketsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/parcels"
        element={
          <ProtectedRoute>
            <ParcelsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/payments"
        element={
          <ProtectedRoute>
            <PaymentsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/employees"
        element={
          <ProtectedRoute>
            <EmployeesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cities"
        element={
          <ProtectedRoute>
            <CitiesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={governmentTheme}>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  )
}

export default App
