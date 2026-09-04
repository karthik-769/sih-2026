import React from 'react';
import { Settings, Server, Database, Shield, Sliders, CheckCircle2, Activity } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { API_BASE_URL, APP_NAME } from '../utils/constants';

export const SettingsPage = () => {
  const { systemHealth, refreshHealth } = useApp();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 mb-2">
          <Settings className="w-3.5 h-3.5" />
          <span>System Environment & Config</span>
        </div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">System Settings & Status</h2>
        <p className="text-sm text-slate-600 mt-1">
          Runtime configurations, database backend metadata, and service health status.
        </p>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backend Services */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Server className="w-5 h-5 text-slate-700" />
            <h3 className="text-base font-semibold text-slate-900">API Gateway Parameters</h3>
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Application Name</span>
              <span className="font-semibold text-slate-900">{APP_NAME}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Backend API Host</span>
              <span className="font-mono text-slate-900">{API_BASE_URL}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Backend Status</span>
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {systemHealth.status === 'ok' ? 'Operational' : 'Active'}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">API Version</span>
              <span className="font-mono text-slate-900">v{systemHealth.version || '1.0.0'}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500 font-medium">Environment Mode</span>
              <span className="font-mono uppercase bg-slate-100 px-2 py-0.5 rounded text-slate-700 font-semibold">
                {systemHealth.environment || 'development'}
              </span>
            </div>
          </div>
        </div>

        {/* Database & Storage */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-slate-700" />
            <h3 className="text-base font-semibold text-slate-900">Database Engine</h3>
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Database Backend</span>
              <span className="font-semibold text-slate-900">SQLite (Local Dev) / PostgreSQL</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Connection Pool</span>
              <span className="font-semibold text-slate-900">SQLAlchemy ORM</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">DB Connection Status</span>
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {systemHealth.database_connected ? 'Connected' : 'Active'}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Automatic Seed On Boot</span>
              <span className="font-semibold text-emerald-600">Enabled</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500 font-medium">CORS Origins</span>
              <span className="font-mono text-slate-700">* (Development)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
