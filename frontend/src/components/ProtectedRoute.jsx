import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { ShieldAlert, LogIn, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center space-y-2">
          <div className="w-8 h-8 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500 font-medium">Verifying authorization...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role authorization
  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 max-w-lg mx-auto mt-12 text-center shadow-sm">
        <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-4 border border-rose-200">
          <Lock className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">Access Unauthorized</h3>
        <p className="text-xs text-slate-600 mb-4 leading-relaxed">
          Your current role (<strong className="font-semibold text-slate-900">{user?.role}</strong>) does not have permission to access this module.
          Requires: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">{allowedRoles.join(', ')}</code>.
        </p>
        <div className="pt-4 border-t border-slate-100 flex justify-center gap-3">
          <a
            href="/"
            className="px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-lg hover:bg-slate-800 transition-colors"
          >
            Return to Allowed Overview
          </a>
        </div>
      </div>
    );
  }

  return children;
};
