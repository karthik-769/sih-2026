import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  TrendingUp,
  AlertTriangle,
  Flame,
  ShieldCheck,
  Building2,
  MapPin,
  ChevronLeft,
  ChevronRight,
  Clock,
  Sparkles,
  FileText,
  CheckCircle2,
  ExternalLink,
  Shield,
  ShieldAlert,
  Activity,
  PlusCircle,
} from 'lucide-react';
import { getPatternByIdApi } from '../services/api';

export const PatternDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [pattern, setPattern] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadPattern = async () => {
      setLoading(true);
      try {
        const res = await getPatternByIdApi(id);
        setPattern(res);
      } catch (err) {
        setError('Failed to load pattern details.');
      } finally {
        setLoading(false);
      }
    };
    loadPattern();
  }, [id]);

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

  if (loading) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-xs text-slate-500 max-w-4xl mx-auto">
        <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        Loading pattern intelligence...
      </div>
    );
  }

  if (error || !pattern) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center max-w-md mx-auto space-y-4">
        <p className="text-xs text-rose-600 font-semibold">{error || 'Pattern not found'}</p>
        <button
          onClick={() => navigate('/patterns')}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold"
        >
          Back to Patterns
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Back & Action Buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/patterns')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to Patterns Registry</span>
        </button>

        <button
          onClick={() => navigate('/corrective-actions', { state: { patternId: pattern.id, title: pattern.title } })}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Create Corrective Action</span>
        </button>
      </div>

      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`px-2.5 py-1 rounded text-xs uppercase tracking-wider border ${getSeverityBadge(pattern.risk_level)}`}>
              {pattern.risk_level} RISK &bull; Score {pattern.risk_score} / 100
            </span>
            <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              {pattern.pattern_key}
            </span>
            {pattern.sif_density > 0 && (
              <span className="text-xs font-bold font-mono text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded border border-purple-200">
                {pattern.sif_density}% SIF Precursor Density
              </span>
            )}
          </div>

          <div className="text-xs text-slate-500">
            Detected: <strong>{new Date(pattern.first_detected_at).toLocaleDateString()}</strong> &bull; Updated:{' '}
            <strong>{new Date(pattern.last_detected_at).toLocaleDateString()}</strong>
          </div>
        </div>

        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">{pattern.title}</h1>
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 mt-2">
            {pattern.location_name && (
              <span className="flex items-center gap-1.5 font-medium">
                <MapPin className="w-4 h-4 text-slate-400" /> {pattern.location_name}
              </span>
            )}
            {pattern.department_name && (
              <span className="flex items-center gap-1.5 font-medium">
                <Building2 className="w-4 h-4 text-slate-400" /> {pattern.department_name}
              </span>
            )}
            {pattern.activity && (
              <span className="flex items-center gap-1.5 font-semibold text-slate-800">
                <Activity className="w-4 h-4 text-indigo-500" /> {pattern.activity}
              </span>
            )}
            {pattern.life_saving_rule && (
              <span className="flex items-center gap-1.5 font-semibold text-indigo-700">
                <Shield className="w-4 h-4 text-indigo-600" /> LSR: {pattern.life_saving_rule}
              </span>
            )}
            <span className="flex items-center gap-1.5 font-semibold text-slate-900">
              <FileText className="w-4 h-4 text-slate-400" /> {pattern.frequency_count} Incidents in Cluster
            </span>
            {pattern.sif_count > 0 && (
              <span className="flex items-center gap-1.5 font-bold text-rose-600">
                <Flame className="w-4 h-4 text-rose-500" /> {pattern.sif_count} SIF Precursors
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Explainable Factor Scoring Breakdown */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900">Explainable Risk Scoring Breakdown</h3>
          </div>
          <span className="text-xs font-mono text-slate-500">
            Pattern Risk Score: <strong>{pattern.risk_score}</strong> / 100
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          {Object.entries(pattern.scoring_factors || {}).map(([factor, pts]) => (
            <div key={factor} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-slate-500 capitalize">{factor.replace(/_/g, ' ')}</div>
              <div className="text-lg font-extrabold text-slate-900 mt-0.5">+{pts} pts</div>
            </div>
          ))}
        </div>
      </div>

      {/* Synthesized Preventive Recommendations */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Strategic Preventive Recommendations</span>
        </h3>
        <ul className="space-y-2 text-xs text-slate-700">
          {(pattern.recommendations || []).map((rec, idx) => (
            <li key={idx} className="flex items-start gap-2 bg-emerald-50/50 border border-emerald-100 p-3 rounded-lg">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Contributing Incidents Evidence */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900">Contributing Incidents & Evidence</h3>
          <span className="text-xs text-slate-500 font-semibold">{pattern.contributing_reports?.length || 0} Reports</span>
        </div>

        <div className="divide-y divide-slate-100">
          {(pattern.contributing_reports || []).map((rep) => (
            <div key={rep.id} className="py-3 flex items-start justify-between gap-4">
              <div className="space-y-1 max-w-2xl">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs text-slate-900">{rep.case_id}</span>
                  <span className="text-[10px] px-2 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    {rep.incident_type}
                  </span>
                  <span className="text-xs text-slate-500">
                    {rep.department_name} &bull; {rep.location_name}
                  </span>
                </div>
                <p className="text-xs text-slate-700 font-mono text-[11px]">{rep.description}</p>
              </div>

              <Link
                to={`/reports/${rep.id}`}
                className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:underline flex-shrink-0"
              >
                <span>View Report</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PatternDetailsPage;
