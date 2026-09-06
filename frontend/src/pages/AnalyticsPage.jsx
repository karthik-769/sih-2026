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
  Shield,
  ShieldAlert,
  Activity,
  MapPin,
  Filter,
  RefreshCw,
} from 'lucide-react';
import {
  getAnalyticsKpisApi,
  getRiskTrendApi,
  getHazardTrendApi,
  getSifTrendApi,
  getDepartmentRiskApi,
  getSifDensityApi,
  getActivityAnalyticsApi,
  getLifeSavingRulesAnalyticsApi,
  getBarrierFailuresAnalyticsApi,
  getTrendsAnalyticsApi,
  getLocations,
  getDepartments,
} from '../services/api';

export const AnalyticsPage = () => {
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState(null);
  const [riskTrends, setRiskTrends] = useState([]);
  const [hazardTrends, setHazardTrends] = useState([]);
  const [sifTrend, setSifTrend] = useState(null);
  const [departmentRisks, setDepartmentRisks] = useState([]);
  const [sifDensity, setSifDensity] = useState(null);
  const [activityAnalytics, setActivityAnalytics] = useState([]);
  const [lsrAnalytics, setLsrAnalytics] = useState([]);
  const [barrierAnalytics, setBarrierAnalytics] = useState([]);
  const [comparativeTrends, setComparativeTrends] = useState(null);

  // Filters
  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('');
  const [trendDays, setTrendDays] = useState(30);

  const fetchData = async () => {
    setLoading(true);
    try {
      const filterParams = {};
      if (selectedLocation) filterParams.location_id = selectedLocation;
      if (selectedDepartment) filterParams.department_id = selectedDepartment;

      const [
        kpiRes,
        trendRes,
        hazardRes,
        sifRes,
        deptRes,
        sifDensRes,
        actRes,
        lsrRes,
        barRes,
        compTrendRes,
      ] = await Promise.all([
        getAnalyticsKpisApi(filterParams).catch(() => null),
        getRiskTrendApi(Math.round(trendDays / 7)).catch(() => []),
        getHazardTrendApi().catch(() => []),
        getSifTrendApi().catch(() => null),
        getDepartmentRiskApi().catch(() => []),
        getSifDensityApi(filterParams).catch(() => null),
        getActivityAnalyticsApi(filterParams).catch(() => []),
        getLifeSavingRulesAnalyticsApi(filterParams).catch(() => []),
        getBarrierFailuresAnalyticsApi(filterParams).catch(() => []),
        getTrendsAnalyticsApi(filterParams).catch(() => null),
      ]);

      setKpis(kpiRes);
      setRiskTrends(trendRes || []);
      setHazardTrends(hazardRes || []);
      setSifTrend(sifRes);
      setDepartmentRisks(deptRes || []);
      setSifDensity(sifDensRes);
      setActivityAnalytics(actRes || []);
      setLsrAnalytics(lsrRes || []);
      setBarrierAnalytics(barRes || []);
      setComparativeTrends(compTrendRes);
    } catch (err) {
      console.error('Failed to load safety analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getLocations().then(setLocations).catch(() => {});
    getDepartments().then(setDepartments).catch(() => {});
  }, []);

  useEffect(() => {
    fetchData();
  }, [selectedLocation, selectedDepartment, trendDays]);

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
            Safety Analytics & SIF Precursor Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Proactive leading indicators, SIF precursor density metrics, IOGP Life-Saving Rules compliance, and barrier failure recurrence.
          </p>
        </div>

        {/* Multi-Dimensional Filter Bar */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 shadow-xs">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="bg-transparent text-slate-700 focus:outline-none"
            >
              <option value="">All Locations / Sites</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 shadow-xs">
            <Building2 className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="bg-transparent text-slate-700 focus:outline-none"
            >
              <option value="">All Departments</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 shadow-xs">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={trendDays}
              onChange={(e) => setTrendDays(Number(e.target.value))}
              className="bg-transparent text-slate-700 focus:outline-none font-medium"
            >
              <option value={7}>Last 7 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
            </select>
          </div>

          <button
            onClick={fetchData}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors bg-white shadow-xs"
            title="Refresh analytics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400 text-xs">
          <div className="w-8 h-8 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          Loading advanced safety analytics...
        </div>
      ) : (
        <>
          {/* Top 4 KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Total Safety Incidents</span>
                <Layers className="w-4 h-4 text-slate-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-2">{kpis?.total_reports || 0}</div>
              <span className="text-[11px] text-slate-500 mt-1 block">In scope reports</span>
            </div>

            <div className="bg-white border border-rose-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-rose-600">SIF Precursors</span>
                <Flame className="w-4 h-4 text-rose-600" />
              </div>
              <div className="text-2xl font-bold text-rose-700 mt-2">
                {sifDensity ? sifDensity.total_sif_precursors : (kpis?.sif_precursors_count || 0)}
              </div>
              <span className="text-[11px] text-rose-600/80 mt-1 block">
                High-energy + worker exposure
              </span>
            </div>

            <div className="bg-white border border-purple-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-purple-600">SIF Precursor Density</span>
                <TrendingUp className="w-4 h-4 text-purple-600" />
              </div>
              <div className="text-2xl font-bold text-purple-700 mt-2">
                {sifDensity ? `${sifDensity.overall_density}%` : '0.0%'}
              </div>
              <span className="text-[11px] text-purple-600/80 mt-1 block font-mono">
                Formula: (SIF / Total) &times; 100
              </span>
            </div>

            <div className="bg-white border border-emerald-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-emerald-700">Open Actions</span>
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-bold text-emerald-800 mt-2">
                {kpis?.open_actions_count || 0}
              </div>
              <span className="text-[11px] text-rose-600 font-medium mt-1 block">
                {kpis?.overdue_actions_count || 0} Overdue Actions
              </span>
            </div>
          </div>

          {/* SIF Density Comparison by Location */}
          {sifDensity?.by_location && sifDensity.by_location.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-indigo-600" />
                    SIF Precursor Density by Field / Site Location
                  </h3>
                  <p className="text-[11px] text-slate-500">Calculated percentage of SIF exposure per operating facility</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {sifDensity.by_location.map((loc, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-slate-900 truncate">{loc.location_name}</span>
                      <span className="text-xs font-black font-mono text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                        {loc.density}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>{loc.total_reports} reports</span>
                      <span className="text-rose-600 font-bold">{loc.sif_count} SIF Precursors</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-purple-600"
                        style={{ width: `${Math.min(loc.density * 2, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SIF Density by Operational Activity */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-slate-700" />
              Operational Activity Breakdown & SIF Density
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-700 uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Operational Activity</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Total Reports</th>
                    <th className="px-4 py-3">SIF Precursors</th>
                    <th className="px-4 py-3 text-right">SIF Density %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activityAnalytics.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                        No activity records found.
                      </td>
                    </tr>
                  ) : (
                    activityAnalytics.map((act, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-3 font-bold text-slate-900">{act.activity}</td>
                        <td className="px-4 py-3 text-slate-500">{act.category}</td>
                        <td className="px-4 py-3 font-mono">{act.count}</td>
                        <td className="px-4 py-3 font-bold text-rose-600">{act.sif_count}</td>
                        <td className="px-4 py-3 text-right font-mono font-bold text-purple-700">
                          {act.sif_density}%
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* IOGP Life-Saving Rules & Top Barrier Failures */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Life-Saving Rules Breakdown */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Shield className="w-4 h-4 text-indigo-600" />
                  IOGP Life-Saving Rules Mapping
                </h3>
              </div>

              <div className="space-y-3">
                {lsrAnalytics.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No Life-Saving Rules data available.</p>
                ) : (
                  lsrAnalytics.map((lsr, idx) => (
                    <div key={idx} className="space-y-1 text-xs">
                      <div className="flex items-center justify-between font-medium">
                        <span className="font-bold text-slate-900">{lsr.rule}</span>
                        <span className="text-slate-500">
                          <strong>{lsr.count}</strong> reports &bull; <strong className="text-rose-600">{lsr.sif_count} SIFs</strong>
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden flex">
                        <div
                          className="bg-indigo-600 h-full rounded-full"
                          style={{ width: `${Math.min(lsr.percentage * 2, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Top Recurring Barrier Failures */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-600" />
                  Top Recurring Barrier Failures
                </h3>
              </div>

              <div className="space-y-2.5">
                {barrierAnalytics.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No barrier failure records available.</p>
                ) : (
                  barrierAnalytics.map((b, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-bold text-slate-900">{b.barrier_name}</div>
                        <div className="text-[10px] text-slate-500">
                          Hierarchy: <span className="font-semibold text-slate-700">{b.hierarchy_level}</span>
                        </div>
                      </div>
                      <span className="text-xs font-mono font-bold text-rose-700 bg-rose-50 px-2.5 py-1 rounded border border-rose-200">
                        {b.failure_count} Failures
                      </span>
                    </div>
                  ))
                )}
              </div>
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
