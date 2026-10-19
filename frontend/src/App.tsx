import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AuthProvider from './modules/auth/components/AuthProvider'
import ProtectedRoute from './modules/auth/components/ProtectedRoute'
import LoginPage from './modules/auth/pages/LoginPage'
import DevicesPage from './modules/admin/pages/DevicesPage'
import UsersPage from './modules/admin/pages/UsersPage'
import PatientsPage from './modules/patients/pages/PatientsPage'
import Layout from './shared/components/Layout'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<PatientsPage />} />
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
