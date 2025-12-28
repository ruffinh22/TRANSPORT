import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { Provider } from 'react-redux'
import { store } from './store'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { TripsPage } from './pages/TripsPage'
import { TicketsPage } from './pages/TicketsPage'
import { ParcelsPage } from './pages/ParcelsPage'
import { PaymentsPage } from './pages/PaymentsPage'
import { EmployeesPage } from './pages/EmployeesPage'
import { CitiesPage } from './pages/CitiesPage'
import ReportsPage from './pages/ReportsPage'
import SettingsPage from './pages/SettingsPage'
import { LandingPage } from './pages/LandingPage'
import { UserProfilePage } from './pages/UserProfilePage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { governmentTheme } from './theme/governmentTheme'
import { NotificationProvider } from './services/NotificationService'
import LoginPage from './pages/LoginPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ProfilePage from './pages/ProfilePage'
import DashboardRouter from './pages/DashboardRouter'
import RoleBasedRoute from './components/RoleBasedRoute'
import AccessDenied from './components/AccessDenied'

const AppContent: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/" element={<LandingPage />} />
      <Route path="/access-denied" element={<AccessDenied />} />
      
      {/* Legacy Login Route */}
      <Route path="/login-legacy" element={<Login />} />
      
      {/* Protected Routes - Dashboard Router (role-based) */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardRouter />
          </ProtectedRoute>
        }
      />
      
      {/* Protected Routes - User Profile */}
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      
      {/* Protected Routes - Legacy Dashboard */}
      <Route
        path="/dashboard-legacy"
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
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      {/* Catch-all - Redirect to login */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={governmentTheme}>
        <NotificationProvider>
          <BrowserRouter>
            <AppContent />
          </BrowserRouter>
        </NotificationProvider>
      </ThemeProvider>
    </Provider>
  )
}

export default App
