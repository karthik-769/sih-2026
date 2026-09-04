export const APP_NAME = import.meta.env.VITE_APP_TITLE || 'Safety Intelligence & Early Warning System';
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '');

export const NAV_ITEMS = [
  { label: 'Overview', path: '/', icon: 'LayoutDashboard', active: true },
  { label: 'Incidents & Observations', path: '/incidents', icon: 'FileText', badge: 'Next' },
  { label: 'SIF Intelligence', path: '/sif-detection', icon: 'AlertTriangle', badge: 'Future' },
  { label: 'Early Warnings', path: '/warnings', icon: 'Bell', badge: 'Future' },
  { label: 'Action Tracker', path: '/actions', icon: 'CheckSquare', badge: 'Future' },
  { label: 'System Settings', path: '/settings', icon: 'Settings', badge: 'Future' },
];
