import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BrainCircuit,
  AlertTriangle,
  Flame,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { getReportsApi, triggerReportAnalysisApi } from '../services/api';

export const AiAnalysisPage = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzingId, setAnalyzingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [sifOnly, setSifOnly] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await getReportsApi({ page: 1, page_size: 50 });
      setReports(res.items || []);
    } catch (err) {
      console.error('Failed to load reports for AI analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleReanalyze = async (reportId) => {
    setAnalyzingId(reportId);
    try {
      await triggerReportAnalysisApi(reportId);
      await fetchReports();
    } catch (err) {
      console.error('Failed to trigger AI re-run:', err);
    } finally {
      setAnalyzingId(null);
    }
  };

  const filteredReports = reports.filter((r) => {
    const ai = r.ai_analysis;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchCase = r.case_id?.toLowerCase().includes(q);
      const matchDesc = r.description?.toLowerCase().includes(q);
      const matchTask = r.task?.toLowerCase().includes(q);
      if (!matchCase && !matchDesc && !matchTask) return false;
    }
    if (riskFilter && ai?.risk_level !== riskFilter) return false;
    if (sifOnly && !ai?.sif_precursor && !ai?.sif_detected) return false;
    return true;
  });

  const totalAnalyzed = reports.filter((r) => r.ai_analysis).length;
  const criticalCount = reports.filter((r) => r.ai_analysis?.risk_level === 'CRITICAL').length;
  const highCount = reports.filter((r) => r.ai_analysis?.risk_level === 'HIGH').length;
  const sifCount = reports.filter((r) => r.ai_analysis?.sif_precursor || r.ai_analysis?.sif_detected).length;

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-slate-800" />
            AI Safety Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time automated incident classification, hazard detection, SIF precursor evaluation, and root cause analysis.
          </p>
        </div>
        <button
          onClick={fetchReports}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Intelligence
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">AI Analyzed Reports</span>
            <BrainCircuit className="w-4 h-4 text-slate-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{totalAnalyzed}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">Across all ingested incidents</span>
        </div>

        <div className="bg-white border border-rose-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-rose-600">Critical Risk Incidents</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-700 mt-2">{criticalCount}</div>
          <span className="text-[11px] text-rose-600/80 mt-1 block">Score &ge; 75.0</span>
        </div>

        <div className="bg-white border border-amber-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-amber-600">High Risk Incidents</span>
            <Flame className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-700 mt-2">{highCount}</div>
          <span className="text-[11px] text-amber-600/80 mt-1 block">Score 50.0 - 74.9</span>
        </div>

        <div className="bg-white border border-purple-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-purple-600">SIF Precursors Detected</span>
            <TrendingUp className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-purple-700 mt-2">{sifCount}</div>
          <span className="text-[11px] text-purple-600/80 mt-1 block">Severe injury potential</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Case ID, task, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900"
          >
            <option value="">All Risk Levels</option>
            <option value="CRITICAL">Critical Risk</option>
            <option value="HIGH">High Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
          </select>

          <button
            onClick={() => setSifOnly(!sifOnly)}
            className={`px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
              sifOnly
                ? 'bg-purple-50 text-purple-700 border-purple-300 font-semibold'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            SIF Precursors Only
          </button>
        </div>
      </div>

      {/* Report Cards Grid */}
      {loading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading AI safety intelligence...</div>
      ) : filteredReports.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500 text-xs">
          No reports matched your search or filter criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredReports.map((report) => {
            const ai = report.ai_analysis;
            const isSif = ai?.sif_precursor || ai?.sif_detected;

            return (
              <div
                key={report.id}
                className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:border-slate-300 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  {/* Top Bar */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-slate-900">{report.case_id}</span>
                        {ai && (
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${getRiskBadge(
                              ai.risk_level
                            )}`}
                          >
                            {ai.risk_level} ({ai.risk_score?.toFixed(0)})
                          </span>
                        )}
                        {isSif && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-200">
                            SIF PRECURSOR
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1">
                        {report.task} &bull; {report.department?.name || 'Department'}
                      </div>
                    </div>

                    <Link
                      to={`/reports/${report.id}`}
                      className="text-slate-400 hover:text-slate-900 p-1 transition-colors"
                      title="View Report Details"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Link>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-slate-700 line-clamp-2 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    {report.description}
                  </p>

                  {/* AI Insights */}
                  {ai ? (
                    <div className="space-y-2 pt-1">
                      {ai.explanation && (
                        <div className="text-[11px] text-slate-600 bg-amber-50/50 p-2 rounded border border-amber-100">
                          <span className="font-semibold text-slate-800">AI Assessment: </span>
                          {ai.explanation}
                        </div>
                      )}

                      {/* Hazards and Controls */}
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {(ai.hazards || []).slice(0, 3).map((h, i) => (
                          <span
                            key={i}
                            className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium"
                          >
                            {h.hazard_type || h.category}
                          </span>
                        ))}
                        {(ai.failed_controls || []).slice(0, 2).map((fc, i) => (
                          <span
                            key={i}
                            className="text-[10px] bg-rose-50 text-rose-700 border border-rose-100 px-2 py-0.5 rounded"
                          >
                            Failed Control: {fc.failed_control}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-[11px] text-slate-400 italic py-2">
                      Report submitted. Ready for AI evaluation.
                    </div>
                  )}
                </div>

                {/* Footer Buttons */}
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-400">
                    Status: <strong className="text-slate-600">{report.processing_status}</strong>
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleReanalyze(report.id)}
                      disabled={analyzingId === report.id}
                      className="px-2.5 py-1 text-[11px] font-semibold text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-1"
                    >
                      <RefreshCw className={`w-3 h-3 ${analyzingId === report.id ? 'animate-spin' : ''}`} />
                      {analyzingId === report.id ? 'Re-analyzing...' : 'Re-run AI'}
                    </button>
                    <Link
                      to={`/reports/${report.id}`}
                      className="px-3 py-1 text-[11px] font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
                    >
                      Inspect
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
export default AiAnalysisPage;
