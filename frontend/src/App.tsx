import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import DevicesPage from './modules/admin/pages/DevicesPage'
import UsersPage from './modules/admin/pages/UsersPage'
import AuthProvider from './modules/auth/components/AuthProvider'
import ProtectedRoute from './modules/auth/components/ProtectedRoute'
import ChangePasswordPage from './modules/auth/pages/ChangePasswordPage'
import ForgotPasswordPage from './modules/auth/pages/ForgotPasswordPage'
import LoginPage from './modules/auth/pages/LoginPage'
import DashboardPage from './modules/dashboard/pages/DashboardPage'
import LandingPage from './modules/landing/pages/LandingPage'
import PatientAlertsPage from './modules/measurements/pages/PatientAlertsPage'
import PatientAnalysisPage from './modules/measurements/pages/PatientAnalysisPage'
import PatientEpisodesPage from './modules/measurements/pages/PatientEpisodesPage'
import PatientHistoryPage from './modules/measurements/pages/PatientHistoryPage'
import PatientMonitorPage from './modules/measurements/pages/PatientMonitorPage'
import PatientTraceabilityPage from './modules/measurements/pages/PatientTraceabilityPage'
import PatientsPage from './modules/patients/pages/PatientsPage'
import Layout from './shared/components/Layout'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/change-password" element={<ChangePasswordPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="patients" element={<PatientsPage />} />
            <Route path="patients/:code" element={<PatientHistoryPage />} />
            <Route path="patients/:code/monitor" element={<PatientMonitorPage />} />
            <Route path="patients/:code/analisis" element={<PatientAnalysisPage />} />
            <Route path="patients/:code/trazabilidad" element={<PatientTraceabilityPage />} />
            <Route path="patients/:code/episodios" element={<PatientEpisodesPage />} />
            <Route path="patients/:code/alertas" element={<PatientAlertsPage />} />
            <Route
              path="admin/devices"
              element={
                <ProtectedRoute roles={['admin', 'viewer']}>
                  <DevicesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/users"
              element={
                <ProtectedRoute roles={['admin']}>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
