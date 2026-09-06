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
  Shield,
  Check,
  Edit3,
  ArrowDown,
  Skull,
  FileCheck,
  Award,
  Target,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  getReportByIdApi,
  getReportAnalysisApi,
  getSimilarIncidentsApi,
  triggerReportAnalysisApi,
  updateReportApi,
  reviewReportAnalysisApi,
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

  // HSE Review Modal State
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewAction, setReviewAction] = useState('CONFIRM'); // 'CONFIRM' or 'OVERRIDE'
  const [reviewSifLevel, setReviewSifLevel] = useState('HIGH');
  const [reviewLsr, setReviewLsr] = useState('');
  const [reviewRiskScore, setReviewRiskScore] = useState(85);
  const [reviewComment, setReviewComment] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState('');

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

      // Load AI analysis
      try {
        const aiData = await getReportAnalysisApi(reportId);
        setAnalysis(aiData);
        if (aiData) {
          setReviewSifLevel(aiData.sif_level || 'HIGH');
          setReviewLsr(aiData.life_saving_rule || '');
          setReviewRiskScore(Math.round(aiData.risk_score || 75));
        }
      } catch (aiErr) {
        setAnalysis(null);
      }

      // Load similar incidents
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
        const aiData = await getReportAnalysisApi(report.id);
        setAnalysis(aiData);
      }

      const updatedReport = await getReportByIdApi(report.id);
      setReport(updatedReport);

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

  const handleHseReviewSubmit = async (e) => {
    e.preventDefault();
    setReviewSubmitting(true);
    try {
      const payload = {
        action: reviewAction,
        comment: reviewComment,
        sif_level: reviewAction === 'OVERRIDE' ? reviewSifLevel : undefined,
        life_saving_rule: reviewAction === 'OVERRIDE' ? reviewLsr : undefined,
        risk_score: reviewAction === 'OVERRIDE' ? Number(reviewRiskScore) : undefined,
      };

      const updated = await reviewReportAnalysisApi(report.id, payload);
      setAnalysis(updated);
      setShowReviewModal(false);
      setReviewSuccessMsg(`Review recorded: AI analysis marked as ${updated.review_status}.`);
      setTimeout(() => setReviewSuccessMsg(''), 5000);
    } catch (err) {
      alert('Failed to submit HSE review: ' + (err.response?.data?.detail || err.message));
    } finally {
      setReviewSubmitting(false);
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

  const getSifLevelColor = (level) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-rose-600 text-white';
      case 'HIGH':
        return 'bg-orange-600 text-white';
      case 'MEDIUM':
        return 'bg-amber-500 text-white';
      default:
        return 'bg-slate-500 text-white';
    }
  };

  // Extract key evidence variables for the reasoning chain
  const topHazard = analysis?.hazards?.[0]?.hazard_type || analysis?.hazards?.[0]?.category || 'High-Energy Operational Hazard';
  const topBarrier = analysis?.failed_barriers?.[0]?.barrier_name || analysis?.control_failures?.[0]?.failed_control || 'Primary Physical/Procedure Barrier';
  const barrierLevel = analysis?.failed_barriers?.[0]?.hierarchy_level || 'ADMINISTRATIVE';
  const exposureText = `${analysis?.worker_exposure?.proximity_level || 'DIRECT'} Proximity (${analysis?.worker_exposure?.exposure_rating || 'HIGH'} Exposure)`;
  const potentialConsequenceText = analysis?.potential_consequence || 'Fatal / Severe Acute Trauma';
  const lsrText = analysis?.life_saving_rule || 'Energy Isolation / Confined Space';
  const sifLevelText = analysis?.sif_level || (analysis?.sif_precursor ? 'CRITICAL' : 'NONE');

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

        <div className="flex flex-wrap items-center gap-2.5">
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

          {isAdmin && analysis && (
            <button
              onClick={() => setShowReviewModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold transition-all shadow-sm"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>HSE Review ({analysis.review_status || 'PENDING'})</span>
            </button>
          )}

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

      {reviewSuccessMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
          <span>{reviewSuccessMsg}</span>
        </div>
      )}

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

      {/* ========================================================================= */}
      {/* 1. REPORT INFORMATION (Raw Source of Truth) */}
      {/* ========================================================================= */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 bg-slate-50/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
                1. Report Information
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
              <span>Location / Site</span>
            </div>
            <p className="font-semibold text-slate-900">{report.location?.name || report.site || 'N/A'}</p>
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
              <Activity className="w-3 h-3" />
              <span>Operational Activity</span>
            </div>
            <p className="font-semibold text-slate-900">{report.activity || report.task}</p>
          </div>
        </div>

        {/* Verbatim Description */}
        <div className="p-5 space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-slate-700" />
            <span>Verbatim Narrative Description (Preserved Raw Source)</span>
          </h3>
          <div className="p-3.5 bg-slate-50/80 border border-slate-200 rounded-lg text-xs leading-relaxed font-mono whitespace-pre-wrap text-slate-900">
            {report.description}
          </div>
        </div>
      </div>

      {analysis ? (
        <div className="space-y-6">
          {/* ========================================================================= */}
          {/* 2. AI SIF ASSESSMENT (Hero Card) */}
          {/* ========================================================================= */}
          <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-slate-800">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 px-2.5 py-0.5 rounded-full">
                    2. AI SIF Precursor Assessment
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Engine v{analysis.analysis_version || '2.0.0'}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <div
                    className={`px-3 py-1.5 rounded-xl text-sm font-black tracking-wide border flex items-center gap-2 ${
                      analysis.sif_precursor || analysis.sif_detected
                        ? 'bg-rose-500/20 border-rose-400 text-rose-200 animate-pulse'
                        : 'bg-emerald-500/20 border-emerald-400 text-emerald-200'
                    }`}
                  >
                    <Flame className="w-4 h-4" />
                    SIF Precursor: {analysis.sif_precursor || analysis.sif_detected ? 'YES' : 'NO'}
                  </div>

                  <span className={`text-xs font-bold px-3 py-1 rounded-lg ${getSifLevelColor(analysis.sif_level)}`}>
                    SIF Potential: {analysis.sif_level || 'NONE'}
                  </span>

                  {analysis.fatality_potential && (
                    <span className="text-xs font-bold px-3 py-1 rounded-lg bg-rose-900/80 text-rose-200 border border-rose-600 flex items-center gap-1.5">
                      <Skull className="w-3.5 h-3.5" />
                      Fatality Potential
                    </span>
                  )}
                </div>

                {analysis.sif_categories && analysis.sif_categories.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-[11px] text-slate-400">Precursor Categories:</span>
                    {analysis.sif_categories.map((cat, idx) => (
                      <span
                        key={idx}
                        className="bg-rose-950/60 text-rose-300 border border-rose-800/80 px-2.5 py-0.5 rounded-md text-[11px] font-semibold"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Quantitative Risk Score Meter */}
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
                    Assessed Operational Risk
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
                  <div className="text-[10px] text-slate-400">Deterministic Multi-Factor Score</div>
                </div>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* 3. WHY FLAGGED (6-STAGE VISUAL CAUSAL REASONING CHAIN) */}
          {/* ========================================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-indigo-600" />
                <div>
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                    3. Why Was This Report Flagged? (Causal Reasoning Chain)
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Step-by-step causal evidence connecting high-energy hazards and failed barriers to worst-case consequence.
                  </p>
                </div>
              </div>
              <span className="text-xs font-bold text-indigo-800 bg-indigo-50 border border-indigo-200 px-2.5 py-1 rounded-lg">
                Explainable AI Chain
              </span>
            </div>

            {/* Visual Reasoning Chain Nodes */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
              {/* Node 1: HAZARD */}
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl border border-slate-200 shadow-2xs">
                <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-800 font-bold flex items-center justify-center flex-shrink-0 text-xs">
                  ⚠
                </div>
                <div className="flex-1 text-xs">
                  <div className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                    Stage 1: High-Energy Hazard Identified
                  </div>
                  <p className="text-slate-700 font-semibold">{topHazard}</p>
                </div>
              </div>

              <div className="flex justify-center text-slate-400">
                <ArrowDown className="w-4 h-4 animate-bounce" />
              </div>

              {/* Node 2: BARRIER FAILURE */}
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl border border-rose-200 shadow-2xs">
                <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-800 font-bold flex items-center justify-center flex-shrink-0 text-xs">
                  🚫
                </div>
                <div className="flex-1 text-xs">
                  <div className="font-bold text-rose-900 uppercase tracking-wider text-[11px]">
                    Stage 2: Critical Barrier / Safeguard Failure
                  </div>
                  <p className="text-rose-800 font-semibold">
                    {topBarrier} <span className="text-[10px] font-normal text-slate-500">({barrierLevel})</span>
                  </p>
                </div>
              </div>

              <div className="flex justify-center text-slate-400">
                <ArrowDown className="w-4 h-4 animate-bounce" />
              </div>

              {/* Node 3: WORKER EXPOSURE */}
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl border border-blue-200 shadow-2xs">
                <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-800 font-bold flex items-center justify-center flex-shrink-0 text-xs">
                  👷
                </div>
                <div className="flex-1 text-xs">
                  <div className="font-bold text-blue-900 uppercase tracking-wider text-[11px]">
                    Stage 3: Worker Exposure & Line-of-Fire Proximity
                  </div>
                  <p className="text-blue-800 font-semibold">{exposureText}</p>
                </div>
              </div>

              <div className="flex justify-center text-slate-400">
                <ArrowDown className="w-4 h-4 animate-bounce" />
              </div>

              {/* Node 4: POTENTIAL CONSEQUENCE */}
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl border border-purple-200 shadow-2xs">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-800 font-bold flex items-center justify-center flex-shrink-0 text-xs">
                  ☠
                </div>
                <div className="flex-1 text-xs">
                  <div className="font-bold text-purple-900 uppercase tracking-wider text-[11px]">
                    Stage 4: Worst-Case Credible Potential Consequence
                  </div>
                  <p className="text-purple-800 font-semibold">{potentialConsequenceText}</p>
                </div>
              </div>

              <div className="flex justify-center text-slate-400">
                <ArrowDown className="w-4 h-4 animate-bounce" />
              </div>

              {/* Node 5: IOGP LIFE-SAVING RULE */}
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl border border-indigo-200 shadow-2xs">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-800 font-bold flex items-center justify-center flex-shrink-0 text-xs">
                  📋
                </div>
                <div className="flex-1 text-xs">
                  <div className="font-bold text-indigo-900 uppercase tracking-wider text-[11px]">
                    Stage 5: Applicable IOGP Life-Saving Rule
                  </div>
                  <p className="text-indigo-800 font-semibold">{lsrText}</p>
                </div>
              </div>

              <div className="flex justify-center text-slate-400">
                <ArrowDown className="w-4 h-4 animate-bounce" />
              </div>

              {/* Node 6: SIF POTENTIAL CONCLUSION */}
              <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-rose-50 to-purple-50 rounded-xl border border-rose-300 shadow-xs">
                <div className="w-8 h-8 rounded-lg bg-rose-600 text-white font-black flex items-center justify-center flex-shrink-0 text-xs">
                  🔴
                </div>
                <div className="flex-1 text-xs">
                  <div className="font-bold text-rose-900 uppercase tracking-wider text-[11px]">
                    Stage 6: SIF Precursor Determination
                  </div>
                  <p className="text-rose-900 font-extrabold text-sm">
                    {sifLevelText} SIF Potential Precursor Flagged
                  </p>
                </div>
              </div>
            </div>

            {/* Narrative Explanation Summary */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 leading-relaxed">
              <span className="font-bold text-slate-900 block mb-1">Causal Synthesis:</span>
              {analysis.sif_reasoning || analysis.explanation}
            </div>
          </div>

          {/* ========================================================================= */}
          {/* 4 & 5. HAZARDS & BARRIER FAILURES */}
          {/* ========================================================================= */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 4. HAZARDS */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <span>4. Detected Hazards ({analysis.hazards?.length || 0})</span>
              </h3>

              <div className="space-y-2">
                {analysis.hazards && analysis.hazards.length > 0 ? (
                  analysis.hazards.map((h, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-amber-200 bg-amber-50/40 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-900">{h.hazard_type || h.category}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                          {h.category || 'HAZARD'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600">{h.description || 'High-energy industrial risk factor.'}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic">No specific critical hazards detected.</p>
                )}
              </div>
            </div>

            {/* 5. BARRIER FAILURES */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-rose-500" />
                <span>5. Failed / Absent Barriers ({analysis.failed_barriers?.length || analysis.control_failures?.length || 0})</span>
              </h3>

              <div className="space-y-2">
                {(analysis.failed_barriers || analysis.control_failures)?.length > 0 ? (
                  (analysis.failed_barriers || analysis.control_failures).map((b, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-rose-200 bg-rose-50/40 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-rose-900">{b.barrier_name || b.failed_control}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800">
                          {b.hierarchy_level || 'CONTROL'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600">{b.description}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic">No critical barrier breakdown detected.</p>
                )}
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* 6. WORKER EXPOSURE */}
          {/* ========================================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <span>6. Worker Proximity & Exposure Assessment</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-[10px] text-slate-500 font-semibold block uppercase">Proximity Level</span>
                <span className="text-sm font-bold text-slate-900">
                  {analysis.worker_exposure?.proximity_level || 'DIRECT'}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">Worker inside active hazard radius</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-[10px] text-slate-500 font-semibold block uppercase">Exposure Rating</span>
                <span className="text-sm font-bold text-slate-900">
                  {analysis.worker_exposure?.exposure_rating || 'HIGH'}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">Direct contact or unmitigated line-of-fire</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-[10px] text-slate-500 font-semibold block uppercase">Observed Role</span>
                <span className="text-sm font-bold text-slate-900">{report.job_role}</span>
                <span className="text-[10px] text-slate-500 block mt-0.5">Involved operational personnel</span>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* 7 & 8. ACTUAL CONSEQUENCE vs POTENTIAL CONSEQUENCE */}
          {/* ========================================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <span>7 & 8. Actual Consequence vs Worst-Case Credible Potential</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* 7. Actual Recorded Consequence */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  7. Actual Recorded Outcome (Immediate)
                </div>
                <div className="text-sm font-bold text-slate-900">
                  {analysis.actual_consequence || report.actual_consequence || 'No injury (Near-miss)'}
                </div>
                <p className="text-[11px] text-slate-500">
                  The immediate physical consequence observed at the time of reporting.
                </p>
              </div>

              {/* 8. Worst-Case Potential Consequence */}
              <div className="p-4 bg-rose-50/70 rounded-xl border border-rose-200 space-y-1.5">
                <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-rose-800">
                  <span>8. Worst-Case Potential Outcome</span>
                  {analysis.fatality_potential && (
                    <span className="px-2 py-0.5 rounded bg-rose-600 text-white font-black text-[10px]">
                      FATALITY POTENTIAL
                    </span>
                  )}
                </div>
                <div className="text-sm font-bold text-rose-900">
                  {analysis.potential_consequence || report.potential_consequence || 'Severe Acute Trauma / Fatality'}
                </div>
                <p className="text-[11px] text-rose-700/80">
                  Severity: <strong className="font-semibold">{analysis.potential_consequence_severity || 'FATAL_POTENTIAL'}</strong>
                </p>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* 9. IOGP LIFE-SAVING RULE */}
          {/* ========================================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Shield className="w-4 h-4 text-indigo-600" />
              <span>9. IOGP Life-Saving Rule Verification</span>
            </h3>

            {analysis.life_saving_rule ? (
              <div className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-200 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-indigo-900 text-sm flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-indigo-600" />
                    {analysis.life_saving_rule}
                  </span>
                  {analysis.life_saving_rule_confidence && (
                    <span className="text-[10px] font-bold bg-indigo-200 text-indigo-900 px-2 py-0.5 rounded">
                      {Math.round(analysis.life_saving_rule_confidence * 100)}% Match Confidence
                    </span>
                  )}
                </div>
                {analysis.life_saving_rule_evidence && (
                  <p className="text-[11px] text-indigo-800 font-mono">
                    Evidence: "{analysis.life_saving_rule_evidence}"
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No specific IOGP Life-Saving Rule mapped.</p>
            )}
          </div>

          {/* ========================================================================= */}
          {/* 10. EVIDENCE SNIPPETS */}
          {/* ========================================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Quote className="w-4 h-4 text-amber-600" />
              <span>10. Verbatim Narrative Evidence Snippets</span>
            </h3>

            {(analysis.evidence_snippets?.length > 0 || analysis.highlighted_evidence?.length > 0) ? (
              <div className="flex flex-wrap gap-2">
                {(analysis.evidence_snippets || analysis.highlighted_evidence).map((snip, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-900 border border-amber-300/80 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold shadow-2xs"
                  >
                    <Quote className="w-3 h-3 text-amber-600" />
                    "{snip}"
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">Full narrative utilized for contextual analysis.</p>
            )}
          </div>

          {/* ========================================================================= */}
          {/* 11. QUANTITATIVE RISK SCORE */}
          {/* ========================================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Target className="w-4 h-4 text-slate-700" />
                <span>11. Quantitative Operational Risk Index (0-100)</span>
              </span>
              <span className="text-xs font-mono font-bold text-slate-900">
                Score: {Math.round(analysis.risk_score)} / 100 ({analysis.risk_level})
              </span>
            </h3>

            <p className="text-xs text-slate-600">
              Assesses overall operational severity and probability based on energy density, worker proximity, barrier failure, and historical frequency.
            </p>

            {analysis.model_metadata?.scoring_breakdown && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                {Object.entries(analysis.model_metadata.scoring_breakdown).map(([k, v], idx) => (
                  <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-[10px] text-slate-500 block truncate">{k.replace(/_/g, ' ')}</span>
                    <span className="font-bold text-slate-900">+{v} pts</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ========================================================================= */}
          {/* 12. RECOMMENDATIONS (Hierarchy of Controls) */}
          {/* ========================================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>12. Prioritized Preventive Recommendations (Hierarchy of Controls)</span>
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

          {/* ========================================================================= */}
          {/* 13. SIMILAR REPORTS */}
          {/* ========================================================================= */}
          {similarData && (
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2 text-indigo-700">
                  <Link2 className="w-4 h-4" />
                  <h3 className="text-xs font-bold uppercase tracking-wide text-slate-900">
                    13. Semantic Similar Historical Incidents
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

          {/* ========================================================================= */}
          {/* 14. HSE REVIEW (Human-in-the-Loop) */}
          {/* ========================================================================= */}
          <div className="bg-indigo-50/50 border border-indigo-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-indigo-100 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-700" />
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wide text-indigo-950">
                    14. HSE Professional Review & Audit Trail (Human-in-the-Loop)
                  </h3>
                  <p className="text-[11px] text-indigo-700/80">
                    AI assists HSE professionals; it does not replace HSE judgment.
                  </p>
                </div>
              </div>

              {isAdmin && (
                <button
                  onClick={() => setShowReviewModal(true)}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs"
                >
                  Record HSE Decision
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 bg-white rounded-xl border border-indigo-100">
                <span className="text-[10px] text-slate-500 font-semibold block uppercase">Review Status</span>
                <span className="text-sm font-bold text-indigo-900">{analysis.review_status || 'PENDING'}</span>
              </div>

              <div className="p-3 bg-white rounded-xl border border-indigo-100">
                <span className="text-[10px] text-slate-500 font-semibold block uppercase">Reviewed By</span>
                <span className="text-sm font-bold text-slate-900">{analysis.reviewed_by_name || 'Awaiting Review'}</span>
              </div>

              <div className="p-3 bg-white rounded-xl border border-indigo-100">
                <span className="text-[10px] text-slate-500 font-semibold block uppercase">Review Timestamp</span>
                <span className="text-xs font-semibold text-slate-700">
                  {analysis.reviewed_at ? new Date(analysis.reviewed_at).toLocaleString() : 'Not Yet Reviewed'}
                </span>
              </div>
            </div>

            {analysis.review_comment && (
              <div className="p-3.5 bg-white rounded-xl border border-indigo-100 text-xs">
                <span className="font-bold text-indigo-950 block mb-1">Auditor Comments:</span>
                <p className="text-slate-700 leading-relaxed font-mono text-[11px]">{analysis.review_comment}</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Empty / Pending AI Analysis State */
        <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto border border-indigo-200">
            <Cpu className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900">AI Safety Intelligence Pending</h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            Execute the AI processing pipeline to classify hazards, extract operational activities, map IOGP Life-Saving Rules, detect SIF precursors, and compute risk scores.
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

      {/* HSE Review / Override Modal */}
      {showReviewModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 flex flex-col">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-indigo-600" />
                <span>HSE Intelligence Review — {report.case_id}</span>
              </h3>
              <button onClick={() => setShowReviewModal(false)} className="text-slate-400 hover:text-slate-700 p-1">
                ✕
              </button>
            </div>

            <form onSubmit={handleHseReviewSubmit} className="p-5 space-y-4 text-xs">
              <div className="space-y-1">
                <label className="block font-semibold text-slate-700">Review Action</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setReviewAction('CONFIRM')}
                    className={`py-2 px-3 rounded-lg border font-semibold flex items-center justify-center gap-1.5 transition-all ${
                      reviewAction === 'CONFIRM'
                        ? 'bg-emerald-50 border-emerald-300 text-emerald-800 font-bold'
                        : 'bg-white border-slate-200 text-slate-600'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" />
                    Confirm AI Decision
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewAction('OVERRIDE')}
                    className={`py-2 px-3 rounded-lg border font-semibold flex items-center justify-center gap-1.5 transition-all ${
                      reviewAction === 'OVERRIDE'
                        ? 'bg-amber-50 border-amber-300 text-amber-800 font-bold'
                        : 'bg-white border-slate-200 text-slate-600'
                    }`}
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    Override AI Decision
                  </button>
                </div>
              </div>

              {reviewAction === 'OVERRIDE' && (
                <div className="p-3 bg-amber-50/60 rounded-xl border border-amber-200 space-y-3">
                  <div>
                    <label className="block font-semibold text-amber-900 mb-1">Override SIF Level</label>
                    <select
                      value={reviewSifLevel}
                      onChange={(e) => setReviewSifLevel(e.target.value)}
                      className="w-full px-3 py-1.5 border border-amber-300 rounded-lg bg-white font-semibold text-xs"
                    >
                      <option value="CRITICAL">CRITICAL</option>
                      <option value="HIGH">HIGH</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="NONE">NONE</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-amber-900 mb-1">Override Life-Saving Rule</label>
                    <input
                      type="text"
                      value={reviewLsr}
                      onChange={(e) => setReviewLsr(e.target.value)}
                      placeholder="e.g., Energy Isolation, Confined Space"
                      className="w-full px-3 py-1.5 border border-amber-300 rounded-lg bg-white text-xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-amber-900 mb-1">Override Risk Score (0-100)</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={reviewRiskScore}
                      onChange={(e) => setReviewRiskScore(e.target.value)}
                      className="w-full px-3 py-1.5 border border-amber-300 rounded-lg bg-white font-mono text-xs"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Auditor / HSE Review Comments</label>
                <textarea
                  rows={3}
                  required
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder="Provide rationale for review action (audit logged)..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowReviewModal(false)}
                  className="px-3 py-2 border border-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reviewSubmitting}
                  className="px-4 py-2 bg-slate-900 text-white rounded-lg font-semibold hover:bg-slate-800 disabled:opacity-50"
                >
                  {reviewSubmitting ? 'Recording Audit Review...' : 'Save HSE Review'}
                </button>
              </div>
            </form>
          </div>
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

export default ReportDetailsPage;
