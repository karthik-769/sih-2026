import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FilePlus,
  FileText,
  BrainCircuit,
  Bell,
  AlertTriangle,
  ShieldCheck,
  TrendingUp,
  UploadCloud,
  Clock,
  Download,
  Building2,
  ShieldAlert,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';

export const Sidebar = () => {
  const { sidebarOpen } = useApp();
  const { user } = useAuth();
  const role = user?.role || 'WORKER';
  const isAdmin = role === 'ADMIN';

  // Worker navigation items
  const workerNavItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      to: '/submit-report',
      label: 'Submit Report',
      icon: FilePlus,
      badge: 'New',
    },
    {
      to: '/reports',
      label: 'My Reports',
      icon: FileText,
    },
  ];

  // Safety Officer / Admin navigation items
  const adminNavItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      to: '/reports',
      label: 'All Reports',
      icon: FileText,
    },
    {
      to: '/ai-analysis',
      label: 'AI Model Evaluation',
      icon: BrainCircuit,
      badge: 'AI',
    },
    {
      to: '/alerts',
      label: 'Early Warnings',
      icon: Bell,
      badge: 'Live',
    },
    {
      to: '/patterns',
      label: 'Patterns',
      icon: AlertTriangle,
    },
    {
      to: '/corrective-actions',
      label: 'Corrective Actions',
      icon: ShieldCheck,
    },
    {
      to: '/analytics',
      label: 'Analytics',
      icon: TrendingUp,
    },
    {
      to: '/bulk-import',
      label: 'Bulk Upload',
      icon: UploadCloud,
    },
    {
      to: '/import-history',
      label: 'Import History',
      icon: Clock,
    },
    {
      to: '/reports-export',
      label: 'Export Data',
      icon: Download,
    },
    {
      to: '/departments',
      label: 'Departments',
      icon: Building2,
    },
    {
      to: '/audit-logs',
      label: 'Audit Logs',
      icon: ShieldAlert,
    },
  ];

  const visibleNavItems = isAdmin ? adminNavItems : workerNavItems;

  return (
    <aside
      className={`fixed lg:static inset-y-0 left-0 z-20 flex-shrink-0 bg-white border-r border-slate-200 transition-all duration-200 ease-in-out flex flex-col justify-between ${
        sidebarOpen ? 'w-64 translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-20'
      }`}
    >
      <div className="p-4 flex flex-col gap-4 overflow-y-auto max-h-[calc(100vh-80px)]">
        <div className="px-2 flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-800 font-semibold text-xs uppercase tracking-wider text-slate-400">
            <ShieldAlert className="w-4 h-4 text-slate-700" />
            {sidebarOpen && <span>{isAdmin ? 'Safety Officer Console' : 'Worker Portal'}</span>}
          </div>
          {sidebarOpen && (
            <span
              className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${
                isAdmin
                  ? 'bg-purple-100 text-purple-800 border-purple-200'
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}
            >
              {role === 'ADMIN' ? 'SAFETY OFFICER' : role}
            </span>
          )}
        </div>

        <nav className="space-y-1">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-900 text-white font-semibold shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                    {sidebarOpen && (
                      <div className="flex items-center justify-between w-full">
                        <span>{item.label}</span>
                        {item.badge && (
                          <span
                            className={`text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded ${
                              isActive
                                ? 'bg-slate-800 text-slate-200 border border-slate-700'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}
                          >
                            {item.badge}
                          </span>
                        )}
                      </div>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {sidebarOpen && (
        <div className="p-3 border-t border-slate-100 bg-slate-50/50 m-3 rounded-lg border">
          <div className="flex items-center gap-2 text-xs text-slate-700 font-semibold mb-0.5">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-700" />
            <span>2-Role RBAC Active</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">
            {isAdmin
              ? 'Authorized for full safety intelligence, early warnings, and oversight.'
              : 'Authorized for report submissions and personal tracking.'}
          </p>
        </div>
      )}
    </aside>
  );
};
export default Sidebar;
