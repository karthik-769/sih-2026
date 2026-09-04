import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import {
  FileText,
  Plus,
  Search,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Eye,
  AlertTriangle,
  Building2,
  MapPin,
  Clock,
  ShieldAlert,
  FileSpreadsheet,
  File,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getReportsApi, getDepartments, getLocations } from '../services/api';

export const ReportsListPage = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const batchIdParam = searchParams.get('batch_id');

  const { user } = useAuth();
  const role = user?.role || 'WORKER';

  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filter options & master data
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedLoc, setSelectedLoc] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Load master data on mount
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const [depts, locs] = await Promise.all([getDepartments(), getLocations()]);
        setDepartments(depts);
        setLocations(locs);
      } catch (err) {
        console.error('Failed to load filter dropdowns', err);
      }
    };
    loadFilters();
  }, []);

  // Fetch reports when filters or page changes
  const fetchReports = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 8,
        department_id: selectedDept || undefined,
        location_id: selectedLoc || undefined,
        incident_type: selectedType || undefined,
        import_batch_id: batchIdParam ? parseInt(batchIdParam, 10) : undefined,
        search: searchTerm.trim() || undefined,
      };
      const res = await getReportsApi(params);
      setReports(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to fetch reports', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [page, selectedDept, selectedLoc, selectedType, batchIdParam]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchReports();
  };

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

  const getPageTitle = () => {
    if (role === 'WORKER') return 'My Safety Reports';
    if (role === 'SUPERVISOR') return 'Unit Safety Incident Reports';
    return 'Site Safety Incident Registry';
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">{getPageTitle()}</h2>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
              {total} Total
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {role === 'WORKER'
              ? 'Showing all safety observations and hazard submissions authored by you.'
              : 'Plant-wide safety reporting registry with multi-attribute filtering.'}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchReports}
            title="Refresh reports"
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/submit-report"
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Submit New Report
          </Link>
        </div>
      </div>

      {/* Batch Filter Notification Banner */}
      {batchIdParam && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-indigo-900 shadow-xs">
          <div className="flex items-center gap-2">
            <span className="font-bold">Filtering by Batch #{batchIdParam}:</span>
            <span>Showing only safety reports imported in this specific batch.</span>
          </div>
          <button
            onClick={() => setSearchParams({})}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white hover:bg-indigo-100 text-indigo-700 font-semibold border border-indigo-200 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            <span>Clear Filter</span>
          </button>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search Case ID, task, or description keyword..."
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
            />
          </div>

          {/* Department Filter */}
          <select
            value={selectedDept}
            onChange={(e) => {
              setSelectedDept(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium text-slate-700"
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>

          {/* Location Filter */}
          <select
            value={selectedLoc}
            onChange={(e) => {
              setSelectedLoc(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium text-slate-700"
          >
            <option value="">All Locations</option>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>

          {/* Incident Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium text-slate-700"
          >
            <option value="">All Incident Types</option>
            <option value="UNSAFE_ACT">Unsafe Act</option>
            <option value="UNSAFE_CONDITION">Unsafe Condition</option>
            <option value="NEAR_MISS">Near Miss</option>
            <option value="SAFETY_OBSERVATION">Safety Observation</option>
          </select>

          <button
            type="submit"
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-lg transition-colors border border-slate-200"
          >
            Filter
          </button>
        </form>
      </div>

      {/* Reports Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading safety reports...
          </div>
        ) : reports.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            <ShieldAlert className="w-8 h-8 mx-auto mb-2 text-slate-400" />
            <p className="font-semibold text-slate-700">No safety reports found matching criteria</p>
            <p className="mt-1">Try adjusting your filters or search query.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                <tr>
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Source</th>
                  <th className="py-3 px-4">Reported Date</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Location</th>
                  <th className="py-3 px-4">Incident Type</th>
                  <th className="py-3 px-4">Task</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reports.map((report) => (
                  <tr
                    key={report.id}
                    onClick={() => navigate(`/reports/${report.id}`)}
                    className="hover:bg-slate-50/75 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">
                      {report.case_id}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {report.source_type && report.source_type !== 'MANUAL' ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                          {report.source_type}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px]">Direct</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                      {new Date(report.reported_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-800">
                      {report.department?.name || `Dept #${report.department_id}`}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {report.location?.name || `Loc #${report.location_id}`}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold border ${getIncidentBadge(
                          report.incident_type
                        )}`}
                      >
                        {report.incident_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-700 max-w-xs truncate font-medium">
                      {report.task}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        {report.processing_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/reports/${report.id}`);
                        }}
                        className="p-1.5 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
                        title="View Full Report Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing Page <strong className="font-semibold text-slate-900">{page}</strong> of{' '}
            <strong className="font-semibold text-slate-900">{totalPages}</strong> ({total} items)
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
