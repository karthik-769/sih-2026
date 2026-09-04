import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Flame,
  ShieldCheck,
  Building2,
  Calendar,
  Layers,
  ArrowUpRight,
  PieChart,
} from 'lucide-react';
import {
  getAnalyticsKpisApi,
  getRiskTrendApi,
  getHazardTrendApi,
  getSifTrendApi,
  getDepartmentRiskApi,
} from '../services/api';

export const AnalyticsPage = () => {
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState(null);
  const [riskTrends, setRiskTrends] = useState([]);
  const [hazardTrends, setHazardTrends] = useState([]);
  const [sifTrend, setSifTrend] = useState(null);
  const [departmentRisks, setDepartmentRisks] = useState([]);
  const [trendWeeks, setTrendWeeks] = useState(4);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [kpiRes, trendRes, hazardRes, sifRes, deptRes] = await Promise.all([
          getAnalyticsKpisApi(),
          getRiskTrendApi(trendWeeks),
          getHazardTrendApi(),
          getSifTrendApi(),
          getDepartmentRiskApi(),
        ]);
        setKpis(kpiRes);
        setRiskTrends(trendRes || []);
        setHazardTrends(hazardRes || []);
        setSifTrend(sifRes);
        setDepartmentRisks(deptRes || []);
      } catch (err) {
        console.error('Failed to load safety analytics data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [trendWeeks]);

  const getRiskColor = (level) => {
    switch (level) {
      case 'CRITICAL':
        return 'text-rose-600 bg-rose-50 border-rose-200';
      case 'HIGH':
        return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'MEDIUM':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-slate-800" />
            Safety Analytics & Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Aggregated safety performance metrics, leading indicators, SIF precursor exposure, and department risk matrices.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Timeframe:</label>
          <select
            value={trendWeeks}
            onChange={(e) => setTrendWeeks(Number(e.target.value))}
            className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900"
          >
            <option value={4}>Last 4 Weeks</option>
            <option value={8}>Last 8 Weeks</option>
            <option value={12}>Last 12 Weeks</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400 text-xs">Loading safety analytics...</div>
      ) : (
        <>
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Total Safety Incidents</span>
                <Layers className="w-4 h-4 text-slate-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-2">{kpis?.total_reports || 0}</div>
              <span className="text-[11px] text-slate-500 mt-1 block">Total ingested & analyzed</span>
            </div>

            <div className="bg-white border border-rose-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-rose-600">Critical & High Risk</span>
                <Flame className="w-4 h-4 text-rose-600" />
              </div>
              <div className="text-2xl font-bold text-rose-700 mt-2">
                {(kpis?.critical_risk_count || 0) + (kpis?.high_risk_count || 0)}
              </div>
              <span className="text-[11px] text-rose-600/80 mt-1 block">
                {kpis?.critical_risk_count || 0} Critical &bull; {kpis?.high_risk_count || 0} High
              </span>
            </div>

            <div className="bg-white border border-purple-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-purple-600">SIF Precursor Rate</span>
                <TrendingUp className="w-4 h-4 text-purple-600" />
              </div>
              <div className="text-2xl font-bold text-purple-700 mt-2">
                {sifTrend?.sif_percentage ? `${sifTrend.sif_percentage}%` : '0%'}
              </div>
              <span className="text-[11px] text-purple-600/80 mt-1 block">
                {kpis?.sif_precursors_count || 0} precursors detected
              </span>
            </div>

            <div className="bg-white border border-emerald-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-emerald-700">Action Resolution</span>
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-bold text-emerald-800 mt-2">
                {kpis?.open_actions_count || 0} Open
              </div>
              <span className="text-[11px] text-rose-600 font-medium mt-1 block">
                {kpis?.overdue_actions_count || 0} Overdue Actions
              </span>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Score Trend */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Average Risk Score Trend
                  </h3>
                  <p className="text-[11px] text-slate-500">Weekly mean risk score across all reporting units</p>
                </div>
                <TrendingUp className="w-4 h-4 text-slate-500" />
              </div>

              {riskTrends.length === 0 ? (
                <div className="h-44 flex items-center justify-center text-slate-400 text-xs">No trend data available</div>
              ) : (
                <div className="space-y-3">
                  {riskTrends.map((pt, i) => {
                    const pct = Math.min(100, Math.max(5, pt.value));
                    return (
                      <div key={i} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-medium text-slate-700">{pt.label || pt.period}</span>
                          <span className="font-mono text-slate-600">
                            Score: <strong className="text-slate-900">{pt.value.toFixed(1)}</strong> ({pt.count} reports)
                          </span>
                        </div>
                        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              pt.value >= 70
                                ? 'bg-rose-500'
                                : pt.value >= 45
                                ? 'bg-amber-500'
                                : 'bg-emerald-500'
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Top Hazard Categories Distribution */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Hazard Category Breakdown
                  </h3>
                  <p className="text-[11px] text-slate-500">Frequency distribution of AI detected safety hazards</p>
                </div>
                <PieChart className="w-4 h-4 text-slate-500" />
              </div>

              {hazardTrends.length === 0 ? (
                <div className="h-44 flex items-center justify-center text-slate-400 text-xs">No hazard data available</div>
              ) : (
                <div className="space-y-3">
                  {hazardTrends.slice(0, 5).map((h, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-700">{h.hazard}</span>
                        <span className="text-slate-500 text-[11px]">
                          {h.count} incidents ({h.percentage}%)
                        </span>
                      </div>
                      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-slate-800 rounded-full"
                          style={{ width: `${Math.min(100, h.percentage)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Department Risk Comparison Matrix */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-slate-700" />
                  Department Risk Comparison Matrix
                </h3>
                <p className="text-[11px] text-slate-500">
                  Real-time exposure profiling and SIF precursor density by department
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-700 uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Department</th>
                    <th className="px-4 py-3">Total Reports</th>
                    <th className="px-4 py-3">Avg Risk Score</th>
                    <th className="px-4 py-3">SIF Precursors</th>
                    <th className="px-4 py-3">Critical Incidents</th>
                    <th className="px-4 py-3 text-right">Risk Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {departmentRisks.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                        No department risk records found.
                      </td>
                    </tr>
                  ) : (
                    departmentRisks.map((d) => (
                      <tr key={d.department_id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-3 font-semibold text-slate-900">{d.department_name}</td>
                        <td className="px-4 py-3 font-mono">{d.total_reports}</td>
                        <td className="px-4 py-3 font-mono font-medium">
                          {d.avg_risk_score ? d.avg_risk_score.toFixed(1) : '0.0'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            d.sif_count > 0 ? 'bg-purple-100 text-purple-800' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {d.sif_count}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            d.critical_count > 0 ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {d.critical_count}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${getRiskColor(d.risk_level)}`}>
                            {d.risk_level}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
export default AnalyticsPage;
