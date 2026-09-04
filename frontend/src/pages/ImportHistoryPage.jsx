import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FileSpreadsheet,
  FileText,
  File,
  Clock,
  RefreshCw,
  Plus,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Search,
  Filter,
} from 'lucide-react';
import { getImportBatchesApi } from '../services/api';

export const ImportHistoryPage = () => {
  const navigate = useNavigate();

  const [batches, setBatches] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [fileTypeFilter, setFileTypeFilter] = useState('');

  const fetchBatches = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 10,
        file_type: fileTypeFilter || undefined,
      };
      const res = await getImportBatchesApi(params);
      setBatches(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load import batches', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, [page, fileTypeFilter]);

  const getFormatIcon = (fileType) => {
    switch (fileType) {
      case 'EXCEL':
        return <FileSpreadsheet className="w-4 h-4 text-emerald-600" />;
      case 'CSV':
        return <FileText className="w-4 h-4 text-blue-600" />;
      case 'PDF':
        return <File className="w-4 h-4 text-rose-600" />;
      default:
        return <File className="w-4 h-4 text-slate-600" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'COMPLETED_WITH_ERRORS':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'ANALYZING':
      case 'IMPORTING':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200 animate-pulse';
      case 'FAILED':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Bulk Import Audit History</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
              {total} Batches
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Complete audit trail of all bulk historical file ingestion batches and background AI intelligence progress.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchBatches}
            title="Refresh"
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/import-reports"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Bulk Import
          </Link>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-slate-500 font-medium">Format:</span>
          {['', 'EXCEL', 'CSV', 'PDF'].map((fmt) => (
            <button
              key={fmt}
              onClick={() => {
                setFileTypeFilter(fmt);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
                fileTypeFilter === fmt
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              {fmt === '' ? 'All Formats' : fmt}
            </button>
          ))}
        </div>

        <div className="text-slate-500">
          Page <strong>{page}</strong> of <strong>{totalPages}</strong>
        </div>
      </div>

      {/* Batches Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading import audit logs...
          </div>
        ) : batches.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 space-y-2">
            <Clock className="w-8 h-8 mx-auto text-slate-400" />
            <p className="font-semibold text-slate-700">No import batches found</p>
            <p>Upload safety reports in bulk from Excel, CSV, or PDF to populate this audit registry.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                <tr>
                  <th className="py-3 px-4">Batch ID</th>
                  <th className="py-3 px-4">Source File</th>
                  <th className="py-3 px-4">Uploader</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-center">Total</th>
                  <th className="py-3 px-4 text-center">Imported</th>
                  <th className="py-3 px-4 text-center">Duplicates</th>
                  <th className="py-3 px-4 text-center">AI Completed</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {batches.map((batch) => (
                  <tr key={batch.id} className="hover:bg-slate-50/75 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">{batch.batch_id}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {getFormatIcon(batch.file_type)}
                        <span className="font-medium text-slate-800">{batch.filename}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-600">{batch.uploader_name || 'System'}</td>
                    <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                      {new Date(batch.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-slate-900">{batch.total_records}</td>
                    <td className="py-3 px-4 text-center font-semibold text-emerald-700">{batch.imported_records}</td>
                    <td className="py-3 px-4 text-center text-slate-500">{batch.duplicate_records}</td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-indigo-700">
                      {batch.ai_completed_records} / {batch.imported_records}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold border ${getStatusBadge(batch.status)}`}>
                        {batch.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/reports?batch_id=${batch.id}`}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 hover:underline"
                      >
                        <span>View Reports</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>
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
            <strong className="font-semibold text-slate-900">{totalPages}</strong>
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
