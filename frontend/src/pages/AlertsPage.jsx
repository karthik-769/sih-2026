import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Bell,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Clock,
  RefreshCw,
  Search,
  Filter,
  ChevronRight,
  ShieldAlert,
  Building2,
  MapPin,
  FileText,
} from 'lucide-react';
import { getAlertsApi } from '../services/api';

export const AlertsPage = () => {
  const navigate = useNavigate();

  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 10,
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
      };
      const res = await getAlertsApi(params);
      setAlerts(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [page, severityFilter, statusFilter]);

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-50 text-rose-700 border-rose-200 font-bold';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200 font-semibold';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  const getStatusBadge = (st) => {
    switch (st) {
      case 'NEW':
        return 'bg-rose-500 text-white font-bold animate-pulse';
      case 'ACKNOWLEDGED':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'IN_PROGRESS':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'RESOLVED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      a.title.toLowerCase().includes(q) ||
      a.description.toLowerCase().includes(q) ||
      (a.location_name && a.location_name.toLowerCase().includes(q)) ||
      (a.department_name && a.department_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded border border-rose-200">
              Early Warning Alert Engine
            </span>
            <span className="text-xs font-semibold text-slate-500">Live Active Alerts</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Early Warning Safety Alerts</h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Prioritized safety warnings generated from recurring hazard patterns, SIF spikes, control failures, and concentration trends with full data evidence.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchAlerts}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh alerts"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-500 font-medium">Severity:</span>
          {['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => {
                setSeverityFilter(sev);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
                severityFilter === sev
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              {sev === '' ? 'All Severities' : sev}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-500 font-medium">Status:</span>
          {['', 'NEW', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
                statusFilter === st
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              {st === '' ? 'All Status' : st}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Feed */}
      {loading ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-xs text-slate-500">
          <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Evaluating active early warnings...
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-xs text-slate-500 space-y-2">
          <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500" />
          <p className="font-semibold text-slate-700">No active early warnings for the selected criteria.</p>
          <p>Plant operations within normal baseline parameters.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              onClick={() => navigate(`/alerts/${alert.id}`)}
              className="bg-white border border-slate-200 hover:border-rose-300 rounded-xl p-5 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
            >
              <div className="space-y-1.5 max-w-3xl">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border ${getSeverityBadge(alert.severity)}`}>
                    {alert.severity} &bull; Score {alert.risk_score}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border ${getStatusBadge(alert.status)}`}>
                    {alert.status}
                  </span>
                  <span className="text-xs font-mono text-slate-400">{alert.alert_key}</span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 group-hover:text-rose-600 transition-colors">
                  {alert.title}
                </h3>
                <p className="text-xs text-slate-600 line-clamp-2">{alert.description}</p>

                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-1">
                  {alert.location_name && (
                    <span className="flex items-center gap-1 font-medium">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" /> {alert.location_name}
                    </span>
                  )}
                  {alert.department_name && (
                    <span className="flex items-center gap-1 font-medium">
                      <Building2 className="w-3.5 h-3.5 text-slate-400" /> {alert.department_name}
                    </span>
                  )}
                  <span className="flex items-center gap-1 font-semibold text-slate-700">
                    <FileText className="w-3.5 h-3.5 text-slate-400" /> {alert.contributing_report_ids?.length || 0} Incident Cases
                  </span>
                  <span className="text-slate-400 text-[11px]">
                    {new Date(alert.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-xs font-semibold text-rose-600 group-hover:underline flex items-center gap-1">
                  <span>Review Evidence</span>
                  <ChevronRight className="w-4 h-4" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
