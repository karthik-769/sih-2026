import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  TrendingUp,
  AlertTriangle,
  Flame,
  ShieldAlert,
  CheckCircle2,
  FileSpreadsheet,
  Building2,
  ChevronRight,
  RefreshCw,
  Plus,
  Layers,
  FileText,
  Clock,
  ExternalLink,
  BrainCircuit,
  AlertCircle,
  Users,
  ShieldCheck,
} from 'lucide-react';
import {
  getAnalyticsKpisApi,
  getRiskTrendApi,
  getHazardTrendApi,
  getSifTrendApi,
  getAlertsApi,
  getPatternsApi,
  getReportsApi,
  getCorrectiveActionsApi,
} from '../services/api';
import { useAuth } from '../context/AuthContext';

export const DashboardPlaceholder = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const role = user?.role || 'WORKER';
  const isAdmin = role === 'ADMIN';

  // Admin state
  const [kpis, setKpis] = useState(null);
  const [trends, setTrends] = useState([]);
  const [hazards, setHazards] = useState([]);
  const [sifData, setSifData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [patterns, setPatterns] = useState([]);

  // Worker state
  const [workerReports, setWorkerReports] = useState([]);
  const [workerActions, setWorkerActions] = useState([]);

  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        const [kpiRes, trendRes, hazRes, sifRes, alertsRes, patternsRes] = await Promise.all([
          getAnalyticsKpisApi().catch(() => null),
          getRiskTrendApi(4).catch(() => []),
          getHazardTrendApi().catch(() => []),
          getSifTrendApi().catch(() => null),
          getAlertsApi({ page: 1, page_size: 4 }).catch(() => ({ items: [] })),
          getPatternsApi({ page: 1, page_size: 4 }).catch(() => ({ items: [] })),
        ]);

        setKpis(kpiRes);
        setTrends(trendRes || []);
        setHazards(hazRes || []);
        setSifData(sifRes);
        setAlerts(alertsRes?.items || []);
        setPatterns(patternsRes?.items || []);
      } else {
        // Worker-specific personal queries
        const [reportsRes, actionsRes] = await Promise.all([
          getReportsApi({ page: 1, page_size: 10 }).catch(() => ({ items: [] })),
          getCorrectiveActionsApi({ page: 1, page_size: 10 }).catch(() => ({ items: [] })),
        ]);

        setWorkerReports(reportsRes?.items || []);
        setWorkerActions(actionsRes?.items || []);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [isAdmin]);

  const getSeverityBadge = (level) => {
    switch (level) {
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

  const getRiskBadge = (level) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'LOW':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  // -------------------------------------------------------------
  // WORKER VIEW
  // -------------------------------------------------------------
  if (!isAdmin) {
    const totalReports = workerReports.length;
    const analyzedReports = workerReports.filter((r) => r.ai_analysis).length;
    const openActions = workerActions.filter((a) => a.status !== 'RESOLVED' && a.status !== 'CLOSED').length;

    return (
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Top Header */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded border border-slate-200">
                Worker Safety Portal
              </span>
              <span className="text-xs font-semibold text-slate-500">Personal Dashboard</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Welcome, {user?.name || 'Worker'}
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Submit observations, track automated AI hazard evaluations for your reports, and monitor personal safety resolutions.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchDashboardData}
              className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
              title="Refresh Dashboard"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => navigate('/submit-report')}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Submit Safety Report</span>
            </button>
          </div>
        </div>

        {/* Worker Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>My Submitted Reports</span>
              <FileText className="w-4 h-4 text-slate-600" />
            </div>
            <div className="text-2xl font-extrabold text-slate-900">{totalReports}</div>
            <div className="text-[11px] text-slate-500">Reports submitted by your account</div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-700 font-medium">
              <span>AI Evaluated Incidents</span>
              <BrainCircuit className="w-4 h-4 text-slate-600" />
            </div>
            <div className="text-2xl font-extrabold text-slate-900">{analyzedReports}</div>
            <div className="text-[11px] text-slate-500">Automated classification & risk scores</div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-xs text-emerald-700 font-medium">
              <span>Related Actions</span>
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-extrabold text-emerald-700">{openActions}</div>
            <div className="text-[11px] text-slate-500">Corrective actions on your reports</div>
          </div>
        </div>

        {/* Recent Submitted Reports Table */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <FileText className="w-4 h-4 text-slate-700" />
              My Recent Safety Reports
            </h3>
            <Link
              to="/reports"
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 flex items-center gap-1"
            >
              <span>View All Reports</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-700 uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Case ID</th>
                  <th className="px-4 py-3">Task & Department</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">AI Risk Level</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {workerReports.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                      You have not submitted any safety reports yet.
                    </td>
                  </tr>
                ) : (
                  workerReports.map((report) => {
                    const ai = report.ai_analysis;
                    return (
                      <tr key={report.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-3 font-mono font-bold text-slate-900">{report.case_id}</td>
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-900">{report.task}</div>
                          <div className="text-[10px] text-slate-400">{report.department?.name || 'Department'}</div>
                        </td>
                        <td className="px-4 py-3 font-medium text-[11px]">{report.incident_type}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                            {report.processing_status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {ai ? (
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${getRiskBadge(
                                ai.risk_level
                              )}`}
                            >
                              {ai.risk_level} ({ai.risk_score?.toFixed(0)})
                            </span>
                          ) : (
                            <span className="text-slate-400 italic text-[11px]">Pending AI</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Link
                            to={`/reports/${report.id}`}
                            className="px-2.5 py-1 text-[11px] font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
                          >
                            View Details
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // ADMIN VIEW
  // -------------------------------------------------------------
  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Welcome & KPI Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-800 bg-slate-100 px-2.5 py-0.5 rounded border border-slate-200">
              Admin Safety Intelligence Center
            </span>
            <span className="text-xs font-semibold text-slate-500">Enterprise AI Engine</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Welcome back, {user?.name || 'Administrator'}
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Real-time proactive safety intelligence, systemic pattern recognition, early warning indicators, and corrective workflows.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchDashboardData}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh command center"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => navigate('/submit-report')}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Submit Report</span>
          </button>
        </div>
      </div>

      {/* Top 4 KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Safety Reports */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Safety Reports</span>
            <FileText className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900">
            {kpis ? kpis.total_reports : '—'}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between">
            <span>
              Critical: <strong className="text-rose-600">{kpis?.critical_risk_count || 0}</strong>
            </span>
            <span>
              High: <strong className="text-amber-600">{kpis?.high_risk_count || 0}</strong>
            </span>
          </div>
        </div>

        {/* SIF Precursors */}
        <div className="bg-white border border-rose-200 rounded-xl p-4 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs text-rose-700 font-semibold">
            <span>SIF Precursors</span>
            <Flame className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-extrabold text-rose-700">
            {kpis ? kpis.sif_precursors_count : '—'}
          </div>
          <div className="text-[11px] text-rose-600 font-medium">
            {sifData?.sif_percentage || 0}% of analyzed incident cases
          </div>
        </div>

        {/* Active Early Warnings */}
        <div
          className="bg-white border border-amber-200 rounded-xl p-4 shadow-sm space-y-2 cursor-pointer hover:border-amber-300 transition-colors"
          onClick={() => navigate('/alerts')}
        >
          <div className="flex items-center justify-between text-xs text-amber-800 font-semibold">
            <span>Active Early Warnings</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-extrabold text-amber-700">
            {kpis ? kpis.active_alerts_count : '—'}
          </div>
          <div className="text-[11px] text-slate-700 font-semibold flex items-center gap-0.5">
            <span>Inspect Alerts</span>
            <ChevronRight className="w-3 h-3" />
          </div>
        </div>

        {/* Open Corrective Actions */}
        <div
          className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2 cursor-pointer hover:border-slate-400 transition-colors"
          onClick={() => navigate('/corrective-actions')}
        >
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Open Corrective Actions</span>
            <CheckCircle2 className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900">
            {kpis ? kpis.open_actions_count : '—'}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between">
            {kpis?.overdue_actions_count > 0 ? (
              <span className="text-rose-600 font-bold flex items-center gap-1">
                <AlertCircle className="w-3 h-3" /> {kpis.overdue_actions_count} Overdue
              </span>
            ) : (
              <span className="text-emerald-600 font-semibold">0 Overdue Actions</span>
            )}
            <span className="text-slate-700 font-semibold">View All</span>
          </div>
        </div>
      </div>

      {/* Main Command Center Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Risk Trends & Early Warning Feed */}
        <div className="lg:col-span-2 space-y-6">
          {/* Risk Trend Weekly Trajectory */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">4-Week Plant Risk Trajectory</h3>
                <p className="text-xs text-slate-500">Average NLP & ML calculated risk score index</p>
              </div>
              <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                Weekly Index
              </span>
            </div>

            <div className="grid grid-cols-4 gap-2 pt-2">
              {trends.map((t, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center space-y-1">
                  <div className="text-[11px] font-semibold text-slate-500">{t.label}</div>
                  <div className="text-lg font-extrabold text-slate-900">{t.value}</div>
                  <div className="text-[10px] text-slate-400">
                    {t.count} reports &bull; {t.sif_count} SIFs
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Early Warning Alerts Stream */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                <h3 className="text-sm font-bold text-slate-900">Active Early Warning Alerts</h3>
              </div>
              <Link
                to="/alerts"
                className="text-xs font-semibold text-slate-700 hover:underline flex items-center gap-1"
              >
                <span>View All Alerts</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {alerts.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-4 text-center">
                No active early warnings currently detected.
              </p>
            ) : (
              <div className="space-y-2.5">
                {alerts.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => navigate(`/alerts/${a.id}`)}
                    className="p-3.5 bg-slate-50/75 hover:bg-slate-100/75 border border-slate-200 rounded-xl cursor-pointer transition-all flex items-start justify-between gap-3 group"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.2 rounded text-[10px] uppercase tracking-wider border ${getSeverityBadge(
                            a.severity
                          )}`}
                        >
                          {a.severity} &bull; Score {a.risk_score}
                        </span>
                        <span className="text-[11px] font-bold text-slate-900 group-hover:text-rose-600 transition-colors">
                          {a.title}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 line-clamp-1">{a.description}</p>
                    </div>

                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-900 group-hover:translate-x-0.5 transition-all flex-shrink-0 mt-1" />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top Recurring Hazards Distribution */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Hazard Category Recurrence Distribution</h3>
            <div className="space-y-3">
              {hazards.map((h, idx) => (
                <div key={idx} className="space-y-1 text-xs">
                  <div className="flex items-center justify-between font-medium">
                    <span className="text-slate-800 font-bold">{h.hazard}</span>
                    <span className="text-slate-500">
                      <strong>{h.count}</strong> incidents ({h.percentage}%)
                      {h.sif_count > 0 && <span className="text-rose-600 font-bold"> &bull; {h.sif_count} SIFs</span>}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${h.sif_count > 0 ? 'bg-rose-500' : 'bg-slate-800'}`}
                      style={{ width: `${Math.min(h.percentage * 1.5, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 1 Col: Quick Launchpad & Patterns */}
        <div className="space-y-6">
          {/* Quick Action Navigation Launchpad */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Administration Launchpad
            </h3>
            <div className="grid grid-cols-1 gap-2 text-xs font-semibold">
              <button
                onClick={() => navigate('/ai-analysis')}
                className="w-full py-2.5 px-3 bg-slate-50 hover:bg-slate-100 text-slate-800 rounded-xl text-left flex items-center justify-between transition-colors border border-slate-200"
              >
                <span className="flex items-center gap-2">
                  <BrainCircuit className="w-4 h-4 text-slate-700" />
                  <span>AI Safety Intelligence</span>
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </button>

              <button
                onClick={() => navigate('/analytics')}
                className="w-full py-2.5 px-3 bg-slate-50 hover:bg-slate-100 text-slate-800 rounded-xl text-left flex items-center justify-between transition-colors border border-slate-200"
              >
                <span className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-slate-700" />
                  <span>Safety Analytics</span>
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </button>

              <button
                onClick={() => navigate('/bulk-import')}
                className="w-full py-2.5 px-3 bg-slate-50 hover:bg-slate-100 text-slate-800 rounded-xl text-left flex items-center justify-between transition-colors border border-slate-200"
              >
                <span className="flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-slate-700" />
                  <span>Bulk Safety Report Importer</span>
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </button>

              <button
                onClick={() => navigate('/reports-export')}
                className="w-full py-2.5 px-3 bg-slate-50 hover:bg-slate-100 text-slate-800 rounded-xl text-left flex items-center justify-between transition-colors border border-slate-200"
              >
                <span className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-700" />
                  <span>Export Data</span>
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </button>

              <button
                onClick={() => navigate('/users')}
                className="w-full py-2.5 px-3 bg-slate-50 hover:bg-slate-100 text-slate-800 rounded-xl text-left flex items-center justify-between transition-colors border border-slate-200"
              >
                <span className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-slate-700" />
                  <span>Manage Users</span>
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </button>

              <button
                onClick={() => navigate('/departments')}
                className="w-full py-2.5 px-3 bg-slate-50 hover:bg-slate-100 text-slate-800 rounded-xl text-left flex items-center justify-between transition-colors border border-slate-200"
              >
                <span className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-slate-700" />
                  <span>Plant Departments</span>
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </button>
            </div>
          </div>

          {/* Recurring Patterns Summary */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-slate-700" />
                <h3 className="text-sm font-bold text-slate-900">Systemic Safety Patterns</h3>
              </div>
              <Link
                to="/patterns"
                className="text-xs font-semibold text-slate-700 hover:underline flex items-center gap-1"
              >
                <span>View All</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-2.5">
              {patterns.map((p) => (
                <div
                  key={p.id}
                  onClick={() => navigate(`/patterns/${p.id}`)}
                  className="p-3 bg-slate-50 rounded-xl border border-slate-200 hover:border-slate-300 transition-colors cursor-pointer space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-900 truncate">{p.title}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] uppercase font-bold border ${getSeverityBadge(
                        p.risk_level
                      )}`}
                    >
                      {p.risk_level}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center justify-between">
                    <span>{p.frequency_count} incidents in cluster</span>
                    {p.trend_percentage > 0 && (
                      <span className="text-rose-600 font-bold">+{p.trend_percentage}% trend</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default DashboardPlaceholder;
