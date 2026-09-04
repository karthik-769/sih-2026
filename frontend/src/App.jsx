import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppShell } from './layouts/AppShell';

import { DashboardPlaceholder } from './pages/DashboardPlaceholder';
import { LoginPage } from './pages/LoginPage';
import { SubmitReportPage } from './pages/SubmitReportPage';
import { ReportsListPage } from './pages/ReportsListPage';
import { ReportDetailsPage } from './pages/ReportDetailsPage';
import { AiAnalysisPage } from './pages/AiAnalysisPage';
import { AlertsPage } from './pages/AlertsPage';
import { AlertDetailsPage } from './pages/AlertDetailsPage';
import { PatternsPage } from './pages/PatternsPage';
import { PatternDetailsPage } from './pages/PatternDetailsPage';
import { CorrectiveActionsPage } from './pages/CorrectiveActionsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { BulkImportPage } from './pages/BulkImportPage';
import { ImportHistoryPage } from './pages/ImportHistoryPage';
import { ReportsExportPage } from './pages/ReportsExportPage';
import { UsersPage } from './pages/UsersPage';
import { DepartmentsPage } from './pages/DepartmentsPage';
import { AuditLogsPage } from './pages/AuditLogsPage';

export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Authentication Route */}
            <Route path="/login" element={<LoginPage />} />

            {/* Authenticated Application Shell */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              {/* Dashboard */}
              <Route index element={<DashboardPlaceholder />} />

              {/* Worker & Admin Accessible Routes */}
              <Route path="submit-report" element={<SubmitReportPage />} />
              <Route path="reports/new" element={<SubmitReportPage />} />
              <Route path="reports" element={<ReportsListPage />} />
              <Route path="reports/:id" element={<ReportDetailsPage />} />
              <Route path="my-reports" element={<Navigate to="/reports" replace />} />

              {/* Admin Only Routes */}
              <Route
                path="ai-analysis"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <AiAnalysisPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="alerts"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <AlertsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="alerts/:id"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <AlertDetailsPage />
                  </ProtectedRoute>
                }
              />
              <Route path="early-warnings" element={<Navigate to="/alerts" replace />} />

              <Route
                path="patterns"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <PatternsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="patterns/:id"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <PatternDetailsPage />
                  </ProtectedRoute>
                }
              />

              <Route
                path="corrective-actions"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <CorrectiveActionsPage />
                  </ProtectedRoute>
                }
              />

              <Route
                path="analytics"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <AnalyticsPage />
                  </ProtectedRoute>
                }
              />

              <Route
                path="bulk-import"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <BulkImportPage />
                  </ProtectedRoute>
                }
              />
              <Route path="import-reports" element={<Navigate to="/bulk-import" replace />} />
              <Route
                path="import-history"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <ImportHistoryPage />
                  </ProtectedRoute>
                }
              />

              <Route
                path="reports-export"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <ReportsExportPage />
                  </ProtectedRoute>
                }
              />
              <Route path="reporting/export" element={<Navigate to="/reports-export" replace />} />

              <Route
                path="users"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <UsersPage />
                  </ProtectedRoute>
                }
              />
              <Route path="users-management" element={<Navigate to="/users" replace />} />

              <Route
                path="departments"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <DepartmentsPage />
                  </ProtectedRoute>
                }
              />
              <Route path="departments-view" element={<Navigate to="/departments" replace />} />

              <Route
                path="audit-logs"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <AuditLogsPage />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </AuthProvider>
  );
}
