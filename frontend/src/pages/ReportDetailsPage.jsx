import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Building2,
  MapPin,
  Briefcase,
  AlertCircle,
  FileText,
  User,
  ShieldCheck,
  ShieldAlert,
  Cpu,
  Clock,
  Zap,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Flame,
  Activity,
  Layers,
  Sparkles,
  Link2,
  ChevronRight,
  Info,
  Quote,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  getReportByIdApi,
  getReportAnalysisApi,
  getSimilarIncidentsApi,
  triggerReportAnalysisApi,
  updateReportApi,
  getDepartments,
  getLocations,
} from '../services/api';

export const ReportDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  const [report, setReport] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [similarData, setSimilarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [analysisError, setAnalysisError] = useState('');

  // Edit Modal State (Admin Only)
  const [showEditModal, setShowEditModal] = useState(false);
  const [editFormData, setEditFormData] = useState({
    task: '',
    incident_type: 'UNSAFE_ACT',
    job_role: '',
    department_id: '',
    location_id: '',
    description: '',
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState('');
  const [departmentsList, setDepartmentsList] = useState([]);
  const [locationsList, setLocationsList] = useState([]);

  const loadAllReportData = async (reportId) => {
    setLoading(true);
    setErrorMessage('');
    try {
      const rep = await getReportByIdApi(reportId);
      setReport(rep);
      setEditFormData({
        task: rep.task || '',
        incident_type: rep.incident_type || 'UNSAFE_ACT',
        job_role: rep.job_role || '',
        department_id: rep.department?.id || rep.department_id || '',
        location_id: rep.location?.id || rep.location_id || '',
        description: rep.description || '',
      });

      // Attempt loading AI analysis
      try {
        const aiData = await getReportAnalysisApi(reportId);
        setAnalysis(aiData);
      } catch (aiErr) {
        setAnalysis(null);
      }

      // Attempt loading similar incidents
      try {
        const simRes = await getSimilarIncidentsApi(reportId);
        setSimilarData(simRes);
      } catch (simErr) {
        setSimilarData(null);
      }
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail;
      setErrorMessage(msg || 'Failed to load safety report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllReportData(id);
    if (isAdmin) {
      getDepartments().then(setDepartmentsList).catch(() => {});
      getLocations().then(setLocationsList).catch(() => {});
    }
  }, [id, isAdmin]);

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setEditError('');
    setEditLoading(true);
    try {
      await updateReportApi(report.id, editFormData);
      setShowEditModal(false);
      await loadAllReportData(report.id);
    } catch (err) {
      setEditError(err.response?.data?.detail || err.response?.data?.error?.message || 'Failed to update report.');
    } finally {
      setEditLoading(false);
    }
  };

  const handleTriggerAnalysis = async () => {
    if (!report) return;
    setAnalyzing(true);
    setAnalysisError('');
    try {
      const res = await triggerReportAnalysisApi(report.id);
      if (res.analysis) {
        setAnalysis(res.analysis);
      } else {
        // Refresh analysis
        const aiData = await getReportAnalysisApi(report.id);
        setAnalysis(aiData);
      }

      // Refresh report status
      const updatedReport = await getReportByIdApi(report.id);
      setReport(updatedReport);

      // Refresh similar incidents
      const simRes = await getSimilarIncidentsApi(report.id);
      setSimilarData(simRes);
    } catch (err) {
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message;
      setAnalysisError(msg || 'AI analysis failed to process. Please retry.');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-xs text-slate-500">
        <div className="w-8 h-8 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading safety intelligence & report details...
      </div>
    );
  }

  if (errorMessage || !report) {
    return (
      <div className="max-w-xl mx-auto mt-12 bg-white border border-slate-200 rounded-xl p-8 shadow-sm text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto border border-rose-200">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-900">Unable to Open Report</h3>
        <p className="text-xs text-slate-600">{errorMessage || 'Report not found.'}</p>
        <button
          onClick={() => navigate('/reports')}
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Reports
        </button>
      </div>
    );
  }

  const getIncidentBadge = (type) => {
    switch (type) {
      case 'UNSAFE_ACT':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'UNSAFE_CONDITION':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'NEAR_MISS':
        return 'bg-rose-50 text-rose-700 border-rose-200 font-bold';
      case 'SAFETY_OBSERVATION':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getRiskScoreColor = (score, level) => {
    if (level === 'CRITICAL' || score >= 75) return { bg: 'bg-rose-500', text: 'text-rose-700', border: 'border-rose-200', light: 'bg-rose-50' };
    if (level === 'HIGH' || score >= 50) return { bg: 'bg-orange-500', text: 'text-orange-700', border: 'border-orange-200', light: 'bg-orange-50' };
    if (level === 'MEDIUM' || score >= 25) return { bg: 'bg-amber-500', text: 'text-amber-700', border: 'border-amber-200', light: 'bg-amber-50' };
    return { bg: 'bg-emerald-500', text: 'text-emerald-700', border: 'border-emerald-200', light: 'bg-emerald-50' };
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Top Navigation & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/reports')}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Incident Registry
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
            ID: #{report.id}
          </span>
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${
              report.processing_status === 'ANALYZED'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : report.processing_status === 'ANALYZING'
                ? 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse'
                : report.processing_status === 'FAILED'
                ? 'bg-rose-50 text-rose-700 border-rose-200'
                : 'bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            Status: {report.processing_status}
          </span>

          {isAdmin && (
            <button
              onClick={() => {
                setEditError('');
                setShowEditModal(true);
              }}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold transition-all shadow-sm"
            >
              <span>Edit Report</span>
            </button>
          )}

          <button
            onClick={handleTriggerAnalysis}
            disabled={analyzing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
            {analyzing ? 'Running AI Pipeline...' : analysis ? 'Re-run AI Analysis' : 'Run AI Analysis'}
          </button>
        </div>
      </div>

      {analysisError && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{analysisError}</span>
          </div>
          <button
            onClick={handleTriggerAnalysis}
            className="underline font-semibold text-rose-800 hover:text-rose-950 ml-3"
          >
            Retry
          </button>
        </div>
      )}

      {/* SECTION 1: ORIGINAL WORKER SAFETY REPORT */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {/* Title Header */}
        <div className="p-5 border-b border-slate-200 bg-slate-50/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
                Original Safety Report
              </span>
              <h2 className="text-lg font-bold font-mono text-slate-900">{report.case_id}</h2>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${getIncidentBadge(report.incident_type)}`}>
                {report.incident_type}
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Task: <strong className="text-slate-800 font-medium">{report.task}</strong>
            </p>
          </div>

          <div className="text-left sm:text-right text-xs text-slate-500 space-y-0.5">
            <div className="flex items-center sm:justify-end gap-1.5 font-medium text-slate-700">
              <Calendar className="w-3.5 h-3.5" />
              {new Date(report.reported_at).toLocaleString()}
            </div>
            <div>
              Reported by: <span className="font-semibold text-slate-800">{report.reporter?.name || 'Worker'}</span> ({report.job_role})
            </div>
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 border-b border-slate-100 bg-white text-xs">
          <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
            <div className="text-slate-400 flex items-center gap-1 mb-0.5 text-[11px]">
              <Building2 className="w-3 h-3" />
              <span>Department</span>
            </div>
            <p className="font-semibold text-slate-900">{report.department?.name || 'N/A'}</p>
          </div>

          <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
            <div className="text-slate-400 flex items-center gap-1 mb-0.5 text-[11px]">
              <MapPin className="w-3 h-3" />
              <span>Plant Location</span>
            </div>
            <p className="font-semibold text-slate-900">{report.location?.name || 'N/A'}</p>
          </div>

          <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
            <div className="text-slate-400 flex items-center gap-1 mb-0.5 text-[11px]">
              <Briefcase className="w-3 h-3" />
              <span>Job Role</span>
            </div>
            <p className="font-semibold text-slate-900">{report.job_role}</p>
          </div>

          <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
            <div className="text-slate-400 flex items-center gap-1 mb-0.5 text-[11px]">
              <Clock className="w-3 h-3" />
              <span>Logged Time</span>
            </div>
            <p className="font-semibold text-slate-900">{new Date(report.created_at).toLocaleTimeString()}</p>
          </div>
        </div>

        {/* Verbatim Description */}
        <div className="p-5 space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-slate-700" />
            <span>Verbatim Description (Source of Truth - Preserved Unedited)</span>
          </h3>
          <div className="p-3.5 bg-slate-50/80 border border-slate-200 rounded-lg text-xs leading-relaxed font-mono whitespace-pre-wrap text-slate-900">
            {report.description}
          </div>
        </div>
      </div>

      {/* SECTION 2: AI SAFETY INTELLIGENCE & SIF ANALYSIS */}
      {analysis ? (
        <div className="space-y-6">
          {/* SIF & Risk Hero Banner */}
          <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-slate-800">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              {/* Left: SIF Status */}
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 border border-indigo-400/30 text-indigo-200">
                  <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                  <span>AI Safety Intelligence Engine v{analysis.analysis_version || '1.0.0'}</span>
                </div>

                <div className="flex items-center gap-3">
                  <div
                    className={`px-3 py-1 rounded-lg text-sm font-black tracking-wide border flex items-center gap-1.5 ${
                      analysis.sif_precursor || analysis.sif_detected
                        ? 'bg-rose-500/20 border-rose-400 text-rose-200 animate-pulse'
                        : 'bg-emerald-500/20 border-emerald-400 text-emerald-200'
                    }`}
                  >
                    <Flame className="w-4 h-4" />
                    SIF Precursor: {analysis.sif_precursor || analysis.sif_detected ? 'YES' : 'NO'}
                  </div>

                  <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    SIF Level: {analysis.sif_level || 'NONE'}
                  </span>
                </div>

                {/* SIF Categories Tags */}
                {analysis.sif_categories && analysis.sif_categories.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-[11px] text-slate-400">Precursor Categories:</span>
                    {analysis.sif_categories.map((cat, idx) => (
                      <span
                        key={idx}
                        className="bg-rose-950/60 text-rose-300 border border-rose-800/80 px-2 py-0.5 rounded text-[11px] font-semibold"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Right: Quantitative Risk Score Meter */}
              <div className="flex items-center gap-4 bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 min-w-[240px]">
                <div className="relative w-16 h-16 flex items-center justify-center">
                  <svg className="w-16 h-16 transform -rotate-90">
                    <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="6" className="text-slate-700" fill="transparent" />
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="currentColor"
                      strokeWidth="6"
                      strokeDasharray="175"
                      strokeDashoffset={175 - (175 * Math.min(analysis.risk_score, 100)) / 100}
                      strokeLinecap="round"
                      className={
                        analysis.risk_level === 'CRITICAL'
                          ? 'text-rose-500'
                          : analysis.risk_level === 'HIGH'
                          ? 'text-orange-500'
                          : analysis.risk_level === 'MEDIUM'
                          ? 'text-amber-500'
                          : 'text-emerald-500'
                      }
                      fill="transparent"
                    />
                  </svg>
                  <span className="absolute text-sm font-black font-mono">
                    {Math.round(analysis.risk_score)}
                  </span>
                </div>

                <div>
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Risk Assessment
                  </div>
                  <div className="text-base font-black tracking-tight flex items-center gap-1.5">
                    <span
                      className={
                        analysis.risk_level === 'CRITICAL'
                          ? 'text-rose-400'
                          : analysis.risk_level === 'HIGH'
                          ? 'text-orange-400'
                          : analysis.risk_level === 'MEDIUM'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {analysis.risk_level}
                    </span>
                    <span className="text-xs font-normal text-slate-400 font-mono">/ 100</span>
                  </div>
                  <div className="text-[10px] text-slate-400">Explainable Multi-Factor Score</div>
                </div>
              </div>
            </div>
          </div>

          {/* Explanation & Highlighted Evidence Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-indigo-700">
              <Zap className="w-4 h-4" />
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Why is this report dangerous? (Causal AI Explanation)
              </h3>
            </div>

            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed bg-slate-50 border border-slate-200 p-4 rounded-xl">
              {analysis.explanation || 'Detailed causal breakdown generated based on detected hazards and control barriers.'}
            </p>

            {/* Highlighted Verbatim Evidence */}
            {analysis.highlighted_evidence && analysis.highlighted_evidence.length > 0 && (
              <div className="space-y-2 pt-1">
                <div className="text-[11px] font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                  <Quote className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Highlighted Evidence Extracted from Report</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {analysis.highlighted_evidence.map((phrase, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 bg-amber-50 text-amber-900 border border-amber-300/80 px-2.5 py-1 rounded-lg text-xs font-mono font-medium shadow-xs"
                    >
                      "{phrase}"
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Grid: Hazards Detected & Control Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Hazards Detected */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-orange-500" />
                  <span>Detected Hazards ({analysis.hazards?.length || 0})</span>
                </h3>
              </div>

              <div className="space-y-2.5">
                {analysis.hazards && analysis.hazards.length > 0 ? (
                  analysis.hazards.map((h, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-slate-900">{h.hazard_type || h.category}</span>
                        {h.confidence && (
                          <span className="text-[10px] font-semibold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">
                            {Math.round(h.confidence * 100)}% Confidence
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-600 leading-normal">{h.description}</p>
                      {h.keywords_matched && h.keywords_matched.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {h.keywords_matched.map((kw, kIdx) => (
                            <span key={kIdx} className="bg-slate-200/80 text-slate-700 px-1.5 py-0.2 rounded text-[10px]">
                              {kw}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic">No acute hazards identified.</p>
                )}
              </div>
            </div>

            {/* Control Failures & Worker Exposure */}
            <div className="space-y-4">
              {/* Control Failures */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-rose-500" />
                  <span>Missing / Failed Critical Controls ({analysis.control_failures?.length || 0})</span>
                </h3>

                <div className="space-y-2">
                  {analysis.control_failures && analysis.control_failures.length > 0 ? (
                    analysis.control_failures.map((cf, idx) => (
                      <div key={idx} className="p-2.5 rounded-lg border border-rose-100 bg-rose-50/40 text-xs space-y-0.5">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-rose-900">{cf.failed_control}</span>
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-800">
                            {cf.hierarchy_level || 'CONTROL'}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-600">{cf.description}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 italic">No critical control failures detected.</p>
                  )}
                </div>
              </div>

              {/* Worker Exposure Card */}
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-blue-500" />
                  <span>Worker Exposure & Proximity</span>
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <span className="text-[10px] text-slate-500 block">Proximity</span>
                    <span className="font-bold text-slate-800">{analysis.worker_exposure?.proximity_level || 'DIRECT'}</span>
                  </div>
                  <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <span className="text-[10px] text-slate-500 block">Exposure Rating</span>
                    <span className="font-bold text-slate-800">{analysis.worker_exposure?.exposure_rating || 'MODERATE'}</span>
                  </div>
                </div>
                {analysis.worker_exposure?.exposed_hazard && (
                  <p className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded border border-slate-100">
                    <strong className="text-slate-800 font-medium">Exposed Vectors:</strong> {analysis.worker_exposure.exposed_hazard}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Actionable Preventive Recommendations */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Prioritized Preventive Recommendations (Hierarchy of Controls)</span>
            </h3>

            <div className="space-y-3">
              {analysis.recommendations && analysis.recommendations.length > 0 ? (
                analysis.recommendations.map((rec, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/60 flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                      {rec.priority || idx + 1}
                    </div>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">{rec.action_title}</span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                          {rec.hierarchy_level}
                        </span>
                      </div>
                      <p className="text-slate-600 leading-relaxed text-[11px]">{rec.action_description}</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 italic">Standard procedure compliance recommended.</p>
              )}
            </div>
          </div>

          {/* Semantic Similar Incident Search */}
          {similarData && (
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2 text-indigo-700">
                  <Link2 className="w-4 h-4" />
                  <h3 className="text-xs font-bold uppercase tracking-wide text-slate-900">
                    Semantic Similar Historical Incidents
                  </h3>
                </div>
                <div className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 text-indigo-800 border border-indigo-200">
                  {similarData.summary_text}
                </div>
              </div>

              <div className="space-y-2.5">
                {similarData.similar_reports && similarData.similar_reports.length > 0 ? (
                  similarData.similar_reports.map((sim, idx) => (
                    <Link
                      key={idx}
                      to={`/reports/${sim.report_id}`}
                      className="block p-3 rounded-lg border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all text-xs"
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold font-mono text-slate-900">{sim.case_id}</span>
                          <span className="text-[10px] font-semibold text-slate-500">
                            {sim.department} • {sim.location}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              sim.risk_level === 'CRITICAL'
                                ? 'bg-rose-100 text-rose-800'
                                : sim.risk_level === 'HIGH'
                                ? 'bg-orange-100 text-orange-800'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {sim.risk_level}
                          </span>
                          <span className="text-[11px] font-mono font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                            {Math.round(sim.similarity_score * 100)}% Match
                          </span>
                          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                        </div>
                      </div>
                      <p className="text-[11px] text-slate-600 line-clamp-1">{sim.description}</p>
                    </Link>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic">No semantically similar historical incidents found.</p>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Empty / Pending AI Analysis State */
        <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto border border-indigo-200">
            <Cpu className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900">AI Safety Intelligence Pending</h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            Execute the AI processing pipeline to classify hazards, detect SIF precursors, compute multi-factor risk scores, and find historical semantic matches.
          </p>
          <button
            onClick={handleTriggerAnalysis}
            disabled={analyzing}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
          >
            <Sparkles className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
            {analyzing ? 'Processing AI Pipeline...' : 'Run AI Analysis Now'}
          </button>
        </div>
      )}

      {/* Admin Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 max-h-[90vh] flex flex-col">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">
                Edit Safety Report {report.case_id}
              </h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="p-5 space-y-4 text-xs overflow-y-auto">
              {editError && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
                  {editError}
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Task Name</label>
                <input
                  type="text"
                  required
                  value={editFormData.task}
                  onChange={(e) => setEditFormData({ ...editFormData, task: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Incident Type</label>
                  <select
                    value={editFormData.incident_type}
                    onChange={(e) => setEditFormData({ ...editFormData, incident_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
                  >
                    <option value="UNSAFE_ACT">UNSAFE_ACT</option>
                    <option value="UNSAFE_CONDITION">UNSAFE_CONDITION</option>
                    <option value="NEAR_MISS">NEAR_MISS</option>
                    <option value="SAFETY_OBSERVATION">SAFETY_OBSERVATION</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Job Role</label>
                  <input
                    type="text"
                    required
                    value={editFormData.job_role}
                    onChange={(e) => setEditFormData({ ...editFormData, job_role: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Department</label>
                  <select
                    value={editFormData.department_id}
                    onChange={(e) => setEditFormData({ ...editFormData, department_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
                  >
                    <option value="">Select Department</option>
                    {departmentsList.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Location</label>
                  <select
                    value={editFormData.location_id}
                    onChange={(e) => setEditFormData({ ...editFormData, location_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
                  >
                    <option value="">Select Location</option>
                    {locationsList.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={4}
                  required
                  value={editFormData.description}
                  onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono text-[11px]"
                />
              </div>

              <p className="text-[11px] text-slate-500 italic">
                * Note: Saving will automatically re-run the AI classification & risk computation pipeline with the updated narrative.
              </p>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-3 py-2 border border-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editLoading}
                  className="px-4 py-2 bg-slate-900 text-white rounded-lg font-semibold hover:bg-slate-800 disabled:opacity-50"
                >
                  {editLoading ? 'Saving & Re-analyzing...' : 'Save & Re-run AI'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
