import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Calendar,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ShieldCheck,
  Building2,
  RefreshCw,
  FileSpreadsheet,
  Layers,
  Users,
  UploadCloud,
  BrainCircuit,
} from 'lucide-react';
import { getReportSummaryApi, downloadReportApi, getDepartments } from '../services/api';

export const ReportsExportPage = () => {
  const [dataset, setDataset] = useState('REPORTS');
  const [reportType, setReportType] = useState('WEEKLY');
  const [timeframeDays, setTimeframeDays] = useState(30);
  const [departmentId, setDepartmentId] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  // Master data
  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    const loadMaster = async () => {
      try {
        const d = await getDepartments();
        setDepartments(d || []);
      } catch (err) {
        console.error('Failed to load departments', err);
      }
    };
    loadMaster();
  }, []);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await getReportSummaryApi({
        report_type: reportType,
        timeframe_days: timeframeDays,
        department_id: departmentId || undefined,
      });
      setSummary(res);
    } catch (err) {
      console.error('Failed to load summary', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [reportType, timeframeDays, departmentId]);

  const handleExport = async (format) => {
    setExporting(true);
    try {
      const data = await downloadReportApi({
        dataset,
        report_type: reportType,
        format,
        timeframe_days: timeframeDays,
        department_id: departmentId || undefined,
        severity: severity || undefined,
        status: status || undefined,
        role: roleFilter || undefined,
      });

      const blob = new Blob([data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `safety_${dataset.toLowerCase()}_${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download report', err);
      alert('Failed to export dataset. Please check your filter parameters.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-800 bg-slate-100 px-2.5 py-0.5 rounded border border-slate-200">
              Safety Intelligence Export Engine
            </span>
            <span className="text-xs font-semibold text-slate-500">Multi-Dataset Export</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Export Safety Intelligence Data</h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Export genuine system records, AI hazard classifications, corrective workflows, early warning alerts, users, and audit batches in CSV, Excel (.xlsx), and PDF formats.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => handleExport('xlsx')}
            disabled={exporting}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Excel (.xlsx)</span>
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-700 hover:bg-rose-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <FileText className="w-4 h-4" />
            <span>PDF (.pdf)</span>
          </button>
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Configuration Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Export Parameters</h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="font-semibold text-slate-700 block mb-1">Target Dataset</label>
            <select
              value={dataset}
              onChange={(e) => setDataset(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
            >
              <option value="REPORTS">Safety Incident Reports</option>
              <option value="AI">AI Intelligence & SIF Risk</option>
              <option value="ACTIONS">Corrective Actions</option>
              <option value="ALERTS">Early Warning Alerts</option>
              <option value="USERS">Provisioned System Users</option>
              <option value="IMPORTS">Import Batches History</option>
              <option value="SUMMARY">Executive Summary</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">Timeframe Scope</label>
            <select
              value={timeframeDays}
              onChange={(e) => setTimeframeDays(parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
            >
              <option value={7}>Last 7 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={60}>Last 60 Days</option>
              <option value={90}>Last 90 Days</option>
              <option value={365}>Past 1 Year</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">Department Filter</label>
            <select
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">Report Category</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
            >
              <option value="WEEKLY">Weekly Risk Assessment</option>
              <option value="DAILY">Daily Safety Snapshot</option>
              <option value="MONTHLY">Monthly HSE Performance</option>
              <option value="HIGH_RISK">High-Risk Incidents Audit</option>
              <option value="SIF_PRECURSOR">SIF Precursor Deep-Dive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Live Report Preview */}
      {loading ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-xs text-slate-500">
          <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Compiling executive report preview...
        </div>
      ) : summary ? (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-slate-900">{summary.report_title}</h2>
            <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
              <span>
                Timeframe: <strong>{summary.timeframe}</strong>
              </span>
              &bull;
              <span>
                Generated: <strong>{new Date(summary.generated_at).toLocaleString()}</strong>
              </span>
            </div>
          </div>

          {/* Key Metrics Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <div className="text-slate-500">Safety Reports</div>
              <div className="text-xl font-extrabold text-slate-900 mt-0.5">{summary.total_reports}</div>
            </div>
            <div className="p-3.5 bg-rose-50 rounded-xl border border-rose-200">
              <div className="text-rose-700 font-semibold">SIF Precursors</div>
              <div className="text-xl font-extrabold text-rose-700 mt-0.5">{summary.sif_precursors_count}</div>
            </div>
            <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200">
              <div className="text-amber-700 font-semibold">Active Early Warnings</div>
              <div className="text-xl font-extrabold text-amber-700 mt-0.5">{summary.active_alerts_count}</div>
            </div>
            <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200">
              <div className="text-emerald-700 font-semibold">Open Actions</div>
              <div className="text-xl font-extrabold text-emerald-800 mt-0.5">
                {summary.open_actions_count}{' '}
                <span className="text-xs text-rose-600 font-bold">({summary.overdue_actions_count} overdue)</span>
              </div>
            </div>
          </div>

          {/* Risk Distribution Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            <div className="space-y-3">
              <h4 className="font-bold text-slate-800">Risk Severity Breakdown</h4>
              <div className="space-y-2">
                {Object.entries(summary.risk_distribution || {}).map(([lvl, cnt]) => (
                  <div
                    key={lvl}
                    className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-200"
                  >
                    <span className="font-bold text-slate-800">{lvl}</span>
                    <span className="font-mono font-bold text-slate-900">{cnt} reports</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-slate-800">Top Hazard Concentrations</h4>
              <div className="space-y-2">
                {(summary.top_hazards || []).map((h, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-200"
                  >
                    <span className="font-semibold text-slate-800">{h.hazard}</span>
                    <span className="font-mono font-bold text-slate-900">{h.count} incidents</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Strategic Recommendations */}
          <div className="space-y-3 pt-2">
            <h4 className="font-bold text-slate-800 flex items-center gap-2 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Key Preventive Recommendations</span>
            </h4>
            <ul className="space-y-2 text-xs text-slate-700">
              {(summary.key_recommendations || []).map((rec, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2 bg-emerald-50/50 border border-emerald-100 p-3 rounded-lg"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
};
export default ReportsExportPage;
