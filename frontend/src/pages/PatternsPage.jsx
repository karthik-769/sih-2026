import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  TrendingUp,
  AlertTriangle,
  Flame,
  ShieldAlert,
  ChevronRight,
  Filter,
  RefreshCw,
  Search,
  Building2,
  MapPin,
  Sparkles,
  Layers,
  ArrowUpRight,
} from 'lucide-react';
import { getPatternsApi, recomputePatternsApi } from '../services/api';

export const PatternsPage = () => {
  const navigate = useNavigate();

  const [patterns, setPatterns] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);

  // Filters
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchPatterns = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 10,
        pattern_type: typeFilter || undefined,
        risk_level: severityFilter || undefined,
      };
      const res = await getPatternsApi(params);
      setPatterns(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load patterns', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatterns();
  }, [page, typeFilter, severityFilter]);

  const handleRecompute = async () => {
    setRecomputing(true);
    try {
      await recomputePatternsApi();
      await fetchPatterns();
    } catch (err) {
      console.error('Failed to recompute patterns', err);
    } finally {
      setRecomputing(false);
    }
  };

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

  const filteredPatterns = patterns.filter((p) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.title.toLowerCase().includes(q) ||
      (p.hazard_category && p.hazard_category.toLowerCase().includes(q)) ||
      (p.department_name && p.department_name.toLowerCase().includes(q)) ||
      (p.location_name && p.location_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
              Pattern Detection Engine
            </span>
            <span className="text-xs font-semibold text-slate-500">Milestone 3</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Recurring Safety Patterns</h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Automated cluster analysis across hazards, control failures, SIF precursors, and plant units to detect developing systemic risks before serious incidents occur.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleRecompute}
            disabled={recomputing}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${recomputing ? 'animate-spin' : ''}`} />
            <span>{recomputing ? 'Recomputing...' : 'Recompute Patterns'}</span>
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

        <div className="relative flex-1 max-w-xs">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search pattern title or hazard..."
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
          />
        </div>
      </div>

      {/* Patterns Grid */}
      {loading ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-xs text-slate-500">
          <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Analyzing recurring hazard patterns...
        </div>
      ) : filteredPatterns.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-xs text-slate-500 space-y-2">
          <TrendingUp className="w-8 h-8 mx-auto text-slate-400" />
          <p className="font-semibold text-slate-700">No recurring safety patterns detected for the selected criteria.</p>
          <p>Pattern engine continuously monitors safety reports for clustering hazards.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredPatterns.map((pattern) => (
            <div
              key={pattern.id}
              onClick={() => navigate(`/patterns/${pattern.id}`)}
              className="bg-white border border-slate-200 hover:border-indigo-300 rounded-xl p-5 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border ${getSeverityBadge(pattern.risk_level)}`}>
                      {pattern.risk_level} &bull; Score {pattern.risk_score}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                      {pattern.pattern_type}
                    </span>
                  </div>
                  {pattern.trend_percentage > 0 && (
                    <span className="text-[11px] font-bold text-rose-600 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded flex items-center gap-1">
                      <ArrowUpRight className="w-3 h-3" /> +{pattern.trend_percentage}%
                    </span>
                  )}
                </div>

                <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  {pattern.title}
                </h3>

                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-2.5">
                  {pattern.location_name && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" /> {pattern.location_name}
                    </span>
                  )}
                  {pattern.department_name && (
                    <span className="flex items-center gap-1">
                      <Building2 className="w-3.5 h-3.5 text-slate-400" /> {pattern.department_name}
                    </span>
                  )}
                  <span className="flex items-center gap-1 font-semibold text-slate-700">
                    <Layers className="w-3.5 h-3.5 text-slate-400" /> {pattern.frequency_count} incidents
                  </span>
                  {pattern.sif_count > 0 && (
                    <span className="flex items-center gap-1 font-bold text-rose-600">
                      <Flame className="w-3.5 h-3.5 text-rose-500" /> {pattern.sif_count} SIF Precursors
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-400 text-[11px]">
                  First: {new Date(pattern.first_detected_at).toLocaleDateString()} &bull; Last: {new Date(pattern.last_detected_at).toLocaleDateString()}
                </span>
                <span className="font-semibold text-indigo-600 flex items-center gap-1 group-hover:underline">
                  Inspect Evidence <ChevronRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
