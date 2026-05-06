import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { useAuth } from "@/hooks/use-auth"
import { I18nProvider } from "@/lib/i18n"
import Layout from "@/components/Layout"
import LoginPage from "@/pages/LoginPage"
import DashboardPage from "@/pages/DashboardPage"
import BusinessProcessesPage from "@/pages/BusinessProcessesPage"
import AssetsPage from "@/pages/AssetsPage"
import CatalogPage from "@/pages/CatalogPage"
import MappingsPage from "@/pages/MappingsPage"
import ImplementationPlanPage from "@/pages/ImplementationPlanPage"
import RisksPage from "@/pages/RisksPage"
import EvidencesPage from "@/pages/EvidencesPage"
import AuditViewPage from "@/pages/AuditViewPage"
import AdminPage from "@/pages/AdminPage"
import TerminologyPage from "@/pages/TerminologyPage"

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <I18nProvider>
      <BrowserRouter>
        <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/processes"
          element={
            <ProtectedRoute>
              <BusinessProcessesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/assets"
          element={
            <ProtectedRoute>
              <AssetsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/catalog"
          element={
            <ProtectedRoute>
              <CatalogPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mappings"
          element={
            <ProtectedRoute>
              <MappingsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/implementation-plan"
          element={
            <ProtectedRoute>
              <ImplementationPlanPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/risks"
          element={
            <ProtectedRoute>
              <RisksPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/evidences"
          element={
            <ProtectedRoute>
              <EvidencesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit"
          element={
            <ProtectedRoute>
              <AuditViewPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/terminology"
          element={
            <ProtectedRoute>
              <TerminologyPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Routes>
      </BrowserRouter>
    </I18nProvider>
  )
}