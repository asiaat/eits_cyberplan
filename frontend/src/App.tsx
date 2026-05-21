import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { useAuth } from "@/hooks/use-auth"
import { I18nProvider } from "@/lib/i18n"
import { AlertProvider } from "@/contexts/AlertContext"
import Layout from "@/components/Layout"
import LoginPage from "@/pages/LoginPage"
import SelectOrgPage from "@/pages/SelectOrgPage"
import DashboardPage from "@/pages/DashboardPage"
import BusinessProcessesPage from "@/pages/BusinessProcessesPage"
import AssetsPage from "@/pages/AssetsPage"
import TargetsPage from "@/pages/TargetsPage"
import CatalogPage from "@/pages/CatalogPage"
import MappingsPage from "@/pages/MappingsPage"
import ImplementationPlanPage from "@/pages/ImplementationPlanPage"
import RisksPage from "@/pages/RisksPage"
import EvidencesPage from "@/pages/EvidencesPage"
import AuditViewPage from "@/pages/AuditViewPage"
import AdminPage from "@/pages/AdminPage"
import TerminologyPage from "@/pages/TerminologyPage"
import OrganizationPage from "@/pages/OrganizationPage"
import SupportPeoplePage from "@/pages/SupportPeoplePage"
import AlertsPage from "@/pages/AlertsPage"
import SettingsPage from "@/pages/SettingsPage"
import ProtectionModePage from "@/pages/ProtectionModePage"

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading, selectedOrgId } = useAuth()
  
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  if (!selectedOrgId) {
    return <Navigate to="/select-org" replace />
  }
  
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <I18nProvider>
      <AlertProvider>
        <div className="scanlines">
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/select-org" element={<SelectOrgPage />} />
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
                path="/targets"
                element={
                  <ProtectedRoute>
                    <TargetsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/protection-mode"
                element={
                  <ProtectedRoute>
                    <ProtectionModePage />
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
                path="/organization"
                element={
                  <ProtectedRoute>
                    <OrganizationPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/support/people"
                element={
                  <ProtectedRoute>
                    <SupportPeoplePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/alerts"
                element={
                  <ProtectedRoute>
                    <AlertsPage />
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
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <SettingsPage />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </BrowserRouter>
        </div>
      </AlertProvider>
    </I18nProvider>
  )
}