import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, AlertCircle, CheckCircle2, Lock, ArrowRight, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, sessionExpiredNotice, clearSessionNotice } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Target path after login
  const from = location.state?.from?.pathname || '/';

  // Demo seeded roles for 1-click login
  const demoAccounts = [
    {
      role: 'WORKER',
      label: 'Worker Demo',
      email: 'worker@safetyintelligence.internal',
      password: 'Worker@2026',
      desc: 'Submit & view own safety reports',
    },
    {
      role: 'ADMIN',
      label: 'Admin Demo',
      email: 'admin@safetyintelligence.internal',
      password: 'Admin@2026',
      desc: 'Full administrative access & intelligence',
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setLoading(true);
    setErrorMessage('');
    try {
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.error?.message || err.response?.data?.detail;
      if (err.response?.status === 401) {
        setErrorMessage('Invalid credentials. Please verify your email and password.');
      } else if (err.response?.status === 403) {
        setErrorMessage('Unauthorized: Account is inactive or access is restricted.');
      } else {
        setErrorMessage(detail || 'Login failed. Please check backend connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (acc) => {
    setEmail(acc.email);
    setPassword(acc.password);
    setLoading(true);
    setErrorMessage('');
    clearSessionNotice();
    try {
      await login(acc.email, acc.password);
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.error?.message || err.response?.data?.detail;
      setErrorMessage(detail || 'Quick login failed. Ensure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-12 h-12 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-lg shadow-sm">
            SIH
          </div>
        </div>
        <h2 className="mt-4 text-center text-xl font-bold tracking-tight text-slate-900">
          Sign In to Safety Intelligence
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500">
          Role-Based Early Warning & Hazard Intelligence System
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 sm:px-10 border border-slate-200 rounded-xl shadow-sm space-y-6">
          {/* Session Expired Alert */}
          {sessionExpiredNotice && (
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-amber-600" />
              <span>Session expired. Please log in again to continue.</span>
            </div>
          )}

          {/* Error Message Alert */}
          {errorMessage && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@safetyintelligence.internal"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          {/* Seed Role Quick Login Selectors */}
          <div className="pt-4 border-t border-slate-100">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 mb-3">
              <UserCheck className="w-4 h-4 text-slate-600" />
              <span>Quick Role Switcher (Demo Users)</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {demoAccounts.map((acc) => (
                <button
                  key={acc.role}
                  type="button"
                  onClick={() => handleQuickLogin(acc)}
                  disabled={loading}
                  className="p-2.5 text-left border border-slate-200 rounded-lg hover:border-slate-400 hover:bg-slate-50 transition-colors flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-[11px] font-bold text-slate-900">{acc.role}</span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 line-clamp-1">{acc.desc}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
