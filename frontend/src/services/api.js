import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request Interceptor: Attach JWT Bearer Token if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Catch 401 Session Expired
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (localStorage.getItem('auth_token')) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        window.dispatchEvent(new CustomEvent('session-expired'));
      }
    }
    return Promise.reject(error);
  }
);

// Health APIs
export const checkHealth = async () => {
  const response = await apiClient.get('/api/health');
  return response.data;
};

export const checkHealthDetails = async () => {
  const response = await apiClient.get('/api/v1/health/details');
  return response.data;
};

// Auth APIs
export const loginApi = async (email, password) => {
  const response = await apiClient.post('/api/auth/login', { email, password });
  return response.data;
};

export const registerApi = async (name, email, password, role = 'WORKER') => {
  const response = await apiClient.post('/api/auth/register', { name, email, password, role });
  return response.data;
};

export const getMeApi = async () => {
  const response = await apiClient.get('/api/auth/me');
  return response.data;
};

// User Management APIs (Admin Only)
export const getUsersApi = async (params = {}) => {
  const response = await apiClient.get('/api/users', { params });
  return response.data;
};

export const createUserApi = async (userData) => {
  const response = await apiClient.post('/api/users', userData);
  return response.data;
};

export const getUserByIdApi = async (userId) => {
  const response = await apiClient.get(`/api/users/${userId}`);
  return response.data;
};

export const updateUserApi = async (userId, userData) => {
  const response = await apiClient.put(`/api/users/${userId}`, userData);
  return response.data;
};

export const updateUserStatusApi = async (userId, isActive) => {
  const response = await apiClient.patch(`/api/users/${userId}/status`, { is_active: isActive });
  return response.data;
};

export const resetUserPasswordApi = async (userId, newPassword) => {
  const response = await apiClient.post(`/api/users/${userId}/reset-password`, { new_password: newPassword });
  return response.data;
};

// Master Data & Department Management APIs
export const getDepartments = async () => {
  const response = await apiClient.get('/api/departments');
  return response.data;
};

export const createDepartmentApi = async (departmentData) => {
  const response = await apiClient.post('/api/departments', departmentData);
  return response.data;
};

export const updateDepartmentApi = async (departmentId, departmentData) => {
  const response = await apiClient.put(`/api/departments/${departmentId}`, departmentData);
  return response.data;
};

export const deleteDepartmentApi = async (departmentId) => {
  const response = await apiClient.delete(`/api/departments/${departmentId}`);
  return response.data;
};

export const getDepartmentStatsApi = async (departmentId) => {
  const response = await apiClient.get(`/api/departments/${departmentId}/stats`);
  return response.data;
};

export const getLocations = async () => {
  const response = await apiClient.get('/api/locations');
  return response.data;
};

// Safety Reports APIs
export const createReportApi = async (reportData) => {
  const response = await apiClient.post('/api/reports', reportData);
  return response.data;
};

export const getReportsApi = async (params = {}) => {
  const response = await apiClient.get('/api/reports', { params });
  return response.data;
};

export const getReportByIdApi = async (reportId) => {
  const response = await apiClient.get(`/api/reports/${reportId}`);
  return response.data;
};

export const updateReportApi = async (reportId, reportData) => {
  const response = await apiClient.put(`/api/reports/${reportId}`, reportData);
  return response.data;
};

// AI Safety Intelligence APIs
export const triggerReportAnalysisApi = async (reportId) => {
  const response = await apiClient.post(`/api/reports/${reportId}/analyze`);
  return response.data;
};

export const getReportAnalysisApi = async (reportId) => {
  const response = await apiClient.get(`/api/reports/${reportId}/analysis`);
  return response.data;
};

export const getSimilarIncidentsApi = async (reportId) => {
  const response = await apiClient.get(`/api/reports/${reportId}/similar`);
  return response.data;
};

// Bulk Safety Report Import APIs
export const uploadImportFileApi = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/api/imports/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000,
  });
  return response.data;
};

export const confirmImportBatchApi = async (batchId, duplicateStrategy = 'SKIP', selectedRowIndices = null) => {
  const response = await apiClient.post(`/api/imports/${batchId}/confirm`, {
    duplicate_strategy: duplicateStrategy,
    selected_row_indices: selectedRowIndices,
  });
  return response.data;
};

export const getImportProgressApi = async (batchId) => {
  const response = await apiClient.get(`/api/imports/${batchId}/progress`);
  return response.data;
};

export const getImportBatchesApi = async (params = {}) => {
  const response = await apiClient.get('/api/imports', { params });
  return response.data;
};

export const getImportBatchByIdApi = async (batchId) => {
  const response = await apiClient.get(`/api/imports/${batchId}`);
  return response.data;
};

export const getImportBatchReportsApi = async (batchId, params = {}) => {
  const response = await apiClient.get(`/api/imports/${batchId}/reports`, { params });
  return response.data;
};

// Milestone 3: Pattern Detection APIs
export const getPatternsApi = async (params = {}) => {
  const response = await apiClient.get('/api/patterns', { params });
  return response.data;
};

export const getPatternByIdApi = async (patternId) => {
  const response = await apiClient.get(`/api/patterns/${patternId}`);
  return response.data;
};

export const recomputePatternsApi = async () => {
  const response = await apiClient.post('/api/patterns/recompute');
  return response.data;
};

// Milestone 3: Early Warning Alert APIs
export const getAlertsApi = async (params = {}) => {
  const response = await apiClient.get('/api/alerts', { params });
  return response.data;
};

export const getAlertByIdApi = async (alertId) => {
  const response = await apiClient.get(`/api/alerts/${alertId}`);
  return response.data;
};

export const updateAlertApi = async (alertId, data) => {
  const response = await apiClient.patch(`/api/alerts/${alertId}`, data);
  return response.data;
};

// Milestone 3: Corrective Action APIs
export const getCorrectiveActionsApi = async (params = {}) => {
  const response = await apiClient.get('/api/corrective-actions', { params });
  return response.data;
};

export const createCorrectiveActionApi = async (data) => {
  const response = await apiClient.post('/api/corrective-actions', data);
  return response.data;
};

export const getCorrectiveActionByIdApi = async (actionId) => {
  const response = await apiClient.get(`/api/corrective-actions/${actionId}`);
  return response.data;
};

export const updateCorrectiveActionApi = async (actionId, data) => {
  const response = await apiClient.patch(`/api/corrective-actions/${actionId}`, data);
  return response.data;
};

// Milestone 3: Advanced Safety Analytics APIs
export const getAnalyticsKpisApi = async () => {
  const response = await apiClient.get('/api/analytics/kpis');
  return response.data;
};

export const getRiskTrendApi = async (weeks = 4) => {
  const response = await apiClient.get('/api/analytics/risk-trend', { params: { weeks } });
  return response.data;
};

export const getHazardTrendApi = async () => {
  const response = await apiClient.get('/api/analytics/hazard-trend');
  return response.data;
};

export const getSifTrendApi = async () => {
  const response = await apiClient.get('/api/analytics/sif-trend');
  return response.data;
};

export const getDepartmentRiskApi = async () => {
  const response = await apiClient.get('/api/analytics/departments');
  return response.data;
};

export const getLocationRiskApi = async () => {
  const response = await apiClient.get('/api/analytics/locations');
  return response.data;
};

export const getTopRiskAreasApi = async () => {
  const response = await apiClient.get('/api/analytics/top-risk-areas');
  return response.data;
};

export const getRiskMapApi = async () => {
  const response = await apiClient.get('/api/analytics/risk-map');
  return response.data;
};

// Milestone 3: Safety Reporting & Export APIs
export const getReportSummaryApi = async (params = {}) => {
  const response = await apiClient.get('/api/reporting/summary', { params });
  return response.data;
};

export const exportReportUrl = (options = {}) => {
  const {
    dataset = 'REPORTS',
    reportType = 'WEEKLY',
    format = 'xlsx',
    timeframeDays = 30,
    departmentId,
    severity,
    status,
    role,
  } = typeof options === 'string' ? { reportType: options } : options;

  const token = localStorage.getItem('auth_token');
  const query = new URLSearchParams({
    dataset,
    report_type: reportType,
    export_format: format,
    timeframe_days: String(timeframeDays),
  });
  if (departmentId) query.append('department_id', String(departmentId));
  if (severity) query.append('severity', severity);
  if (status) query.append('status', status);
  if (role) query.append('role', role);
  if (token) query.append('token', token);

  return `${API_BASE_URL}/api/reporting/export?${query.toString()}`;
};

export const downloadReportApi = async (options = {}) => {
  const params = typeof options === 'string'
    ? { report_type: options, export_format: 'xlsx', timeframe_days: 30 }
    : {
        dataset: options.dataset || 'REPORTS',
        report_type: options.reportType || options.report_type || 'WEEKLY',
        export_format: options.format || options.export_format || 'xlsx',
        timeframe_days: options.timeframeDays || options.timeframe_days || 30,
        department_id: options.departmentId || options.department_id,
        severity: options.severity,
        status: options.status,
        role: options.role,
      };

  const response = await apiClient.get('/api/reporting/export', {
    params,
    responseType: 'blob',
  });
  return response.data;
};

// Audit Logs APIs (Admin Only)
export const getAuditLogsApi = async (params = {}) => {
  const response = await apiClient.get('/api/audit-logs', { params });
  return response.data;
};

export default apiClient;


