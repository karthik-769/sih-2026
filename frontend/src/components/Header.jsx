import React from 'react';
import { Menu, RefreshCw, CheckCircle2, AlertCircle, HelpCircle, LogOut, User } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';

export const Header = () => {
  const { sidebarOpen, setSidebarOpen, systemHealth, refreshHealth } = useApp();
  const { user, logout } = useAuth();

  const getStatusBadge = () => {
    if (systemHealth.status === 'checking') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
          <HelpCircle className="w-3.5 h-3.5 animate-spin" />
          Connecting...
        </span>
      );
    }
    if (systemHealth.status === 'ok') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          API Online
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
        <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
        Offline
      </span>
    );
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'SAFETY_OFFICER':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'SUPERVISOR':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-200 transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-slate-900 text-white flex items-center justify-center font-bold text-sm tracking-wide">
            SIH
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-900 tracking-tight leading-tight">
              Safety Intelligence & Early Warning
            </h1>
            <p className="text-[11px] text-slate-500 leading-none">
              SIH26165 &bull; Authenticated Workspace
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {getStatusBadge()}

        <button
          onClick={refreshHealth}
          title="Refresh connection status"
          className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        <div className="h-4 w-px bg-slate-200 mx-1" />

        {user && (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center text-xs font-semibold">
                {getInitials(user.name)}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-xs font-semibold text-slate-900 leading-tight">{user.name}</p>
                <span
                  className={`inline-block text-[10px] font-semibold px-1.5 py-0.2 rounded border ${getRoleBadgeColor(
                    user.role
                  )}`}
                >
                  {user.role === 'ADMIN' ? 'SAFETY OFFICER' : user.role}
                </span>
              </div>
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
