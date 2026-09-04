import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  UploadCloud,
  FileSpreadsheet,
  FileText,
  File,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Clock,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Info,
  Check,
  X,
  Layers,
  ShieldCheck,
  ShieldAlert,
  Flame,
  ChevronRight,
  Filter,
  Search,
  Download,
} from 'lucide-react';
import { uploadImportFileApi, confirmImportBatchApi, getImportProgressApi } from '../services/api';

export const BulkImportPage = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Flow steps: 'UPLOAD' -> 'PREVIEW' -> 'PROCESSING' -> 'DONE'
  const [step, setStep] = useState('UPLOAD');

  // Upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  // Preview state
  const [previewData, setPreviewData] = useState(null);
  const [duplicateStrategy, setDuplicateStrategy] = useState('SKIP');
  const [statusFilter, setStatusFilter] = useState('ALL'); // ALL, VALID, WARNING, ERROR, DUPLICATE
  const [searchQuery, setSearchQuery] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState('');

  // Processing & Progress state
  const [confirmResult, setConfirmResult] = useState(null);
  const [progressData, setProgressData] = useState(null);
  const [polling, setPolling] = useState(false);

  // Handle Drag and Drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file) => {
    setUploadError('');
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.xlsx', '.xls', '.csv', '.pdf'].includes(ext)) {
      setUploadError(`Invalid file format '${ext}'. Please upload an Excel (.xlsx), CSV (.csv), or PDF (.pdf) file.`);
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setUploadError(`File exceeds the maximum upload limit of 25 MB.`);
      return;
    }
    setSelectedFile(file);
  };

  // Upload & Parse
  const handleUploadAndParse = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setUploadError('');
    try {
      const res = await uploadImportFileApi(selectedFile);
      setPreviewData(res);
      setStep('PREVIEW');
    } catch (err) {
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Failed to parse file. Please verify file integrity.';
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  // Confirm Import
  const handleConfirmImport = async () => {
    if (!previewData) return;
    setConfirming(true);
    setConfirmError('');
    try {
      const res = await confirmImportBatchApi(previewData.batch_id, duplicateStrategy);
      setConfirmResult(res);
      setStep('PROCESSING');
      setPolling(true);
    } catch (err) {
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Failed to confirm import batch.';
      setConfirmError(msg);
    } finally {
      setConfirming(false);
    }
  };

  // Poll Background AI Progress
  useEffect(() => {
    let intervalId = null;
    if (polling && previewData?.batch_id) {
      const pollProgress = async () => {
        try {
          const prog = await getImportProgressApi(previewData.batch_id);
          setProgressData(prog);
          if (prog.is_finished) {
            setPolling(false);
            setStep('DONE');
          }
        } catch (err) {
          console.error('Error polling import progress', err);
        }
      };

      // Poll immediately then every 1.5s
      pollProgress();
      intervalId = setInterval(pollProgress, 1500);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [polling, previewData?.batch_id]);

  // Reset to Upload Step
  const handleReset = () => {
    setStep('UPLOAD');
    setSelectedFile(null);
    setPreviewData(null);
    setProgressData(null);
    setConfirmResult(null);
    setUploadError('');
    setConfirmError('');
    setStatusFilter('ALL');
    setSearchQuery('');
  };

  // Filter Preview Rows
  const getFilteredRows = () => {
    if (!previewData?.rows) return [];
    return previewData.rows.filter((row) => {
      // Status filter
      if (statusFilter === 'VALID' && row.validation_status !== 'VALID') return false;
      if (statusFilter === 'WARNING' && row.validation_status !== 'WARNING') return false;
      if (statusFilter === 'ERROR' && row.validation_status !== 'ERROR') return false;
      if (statusFilter === 'DUPLICATE' && !row.is_duplicate) return false;

      // Search filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchCase = (row.case_id || '').toLowerCase().includes(q);
        const matchDesc = (row.description || '').toLowerCase().includes(q);
        const matchTask = (row.task || '').toLowerCase().includes(q);
        const matchDept = (row.department_name || '').toLowerCase().includes(q);
        if (!matchCase && !matchDesc && !matchTask && !matchDept) return false;
      }

      return true;
    });
  };

  const getFormatIcon = (fileType) => {
    switch (fileType) {
      case 'EXCEL':
        return <FileSpreadsheet className="w-5 h-5 text-emerald-600" />;
      case 'CSV':
        return <FileText className="w-5 h-5 text-blue-600" />;
      case 'PDF':
        return <File className="w-5 h-5 text-rose-600" />;
      default:
        return <File className="w-5 h-5 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-6xl mx-auto">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
              Bulk Data Ingestion & AI Pipeline
            </span>
            <span className="text-xs font-semibold text-slate-500">Milestone 2.5</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Bulk Safety Report Import</h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Upload historical safety incident records from Excel (.xlsx), CSV (.csv), or PDF (.pdf). Imported records are normalized, validated, and automatically processed through the AI Safety Intelligence Pipeline.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/import-history"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-semibold text-slate-700 transition-colors"
          >
            <Clock className="w-4 h-4 text-slate-500" />
            <span>Import History</span>
          </Link>
        </div>
      </div>

      {/* STEP 1: FILE UPLOAD ZONE */}
      {step === 'UPLOAD' && (
        <div className="space-y-6">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer ${
              dragOver
                ? 'border-indigo-500 bg-indigo-50/50 scale-[1.01]'
                : selectedFile
                ? 'border-slate-400 bg-slate-50/70'
                : 'border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv,.pdf"
              onChange={handleFileChange}
              className="hidden"
            />

            <div className="max-w-md mx-auto space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto border border-indigo-200 shadow-sm">
                <UploadCloud className="w-8 h-8" />
              </div>

              <div>
                <h3 className="text-base font-bold text-slate-900">
                  {selectedFile ? selectedFile.name : 'Choose a file or drag & drop here'}
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  {selectedFile
                    ? `${(selectedFile.size / 1024).toFixed(1)} KB &bull; Click or drag to replace`
                    : 'Supports Excel (.xlsx), CSV (.csv), and structured PDF (.pdf) up to 25 MB'}
                </p>
              </div>

              {/* Supported Format Badges */}
              <div className="flex items-center justify-center gap-3 pt-2">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-medium">
                  <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                  Excel (.xlsx)
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-blue-50 text-blue-800 border border-blue-200 text-xs font-medium">
                  <FileText className="w-3.5 h-3.5 text-blue-600" />
                  CSV (.csv)
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-rose-50 text-rose-800 border border-rose-200 text-xs font-medium">
                  <File className="w-3.5 h-3.5 text-rose-600" />
                  PDF (.pdf)
                </span>
              </div>
            </div>
          </div>

          {uploadError && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Action Footer */}
          <div className="flex justify-end gap-3">
            <button
              onClick={handleUploadAndParse}
              disabled={!selectedFile || uploading}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white rounded-xl text-xs font-semibold transition-all shadow-sm"
            >
              {uploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Parsing & Validating File...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Upload & Generate Preview</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: INTERACTIVE PREVIEW & VALIDATION INSPECTOR */}
      {step === 'PREVIEW' && previewData && (
        <div className="space-y-6">
          {/* File Meta Header */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center border border-slate-200">
                {getFormatIcon(previewData.file_type)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900">{previewData.filename}</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    {previewData.batch_id}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  {(previewData.file_size_bytes / 1024).toFixed(1)} KB &bull; {previewData.total_records} records extracted
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleReset}
                className="px-3 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg text-xs font-medium transition-colors"
              >
                Change File
              </button>
            </div>
          </div>

          {/* Validation Metrics KPI Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <button
              onClick={() => setStatusFilter('ALL')}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                statusFilter === 'ALL'
                  ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                  : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700'
              }`}
            >
              <div className="text-[10px] font-bold uppercase tracking-wider opacity-70">Total Rows</div>
              <div className="text-xl font-extrabold mt-0.5">{previewData.total_records}</div>
            </button>

            <button
              onClick={() => setStatusFilter('VALID')}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                statusFilter === 'VALID'
                  ? 'bg-emerald-700 text-white border-emerald-700 shadow-sm'
                  : 'bg-white hover:bg-emerald-50/50 border-emerald-200 text-emerald-800'
              }`}
            >
              <div className="text-[10px] font-bold uppercase tracking-wider opacity-70 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Valid
              </div>
              <div className="text-xl font-extrabold mt-0.5">{previewData.valid_records}</div>
            </button>

            <button
              onClick={() => setStatusFilter('WARNING')}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                statusFilter === 'WARNING'
                  ? 'bg-amber-600 text-white border-amber-600 shadow-sm'
                  : 'bg-white hover:bg-amber-50/50 border-amber-200 text-amber-800'
              }`}
            >
              <div className="text-[10px] font-bold uppercase tracking-wider opacity-70 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Warnings
              </div>
              <div className="text-xl font-extrabold mt-0.5">{previewData.warning_records}</div>
            </button>

            <button
              onClick={() => setStatusFilter('ERROR')}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                statusFilter === 'ERROR'
                  ? 'bg-rose-700 text-white border-rose-700 shadow-sm'
                  : 'bg-white hover:bg-rose-50/50 border-rose-200 text-rose-800'
              }`}
            >
              <div className="text-[10px] font-bold uppercase tracking-wider opacity-70 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" /> Errors
              </div>
              <div className="text-xl font-extrabold mt-0.5">{previewData.error_records}</div>
            </button>

            <button
              onClick={() => setStatusFilter('DUPLICATE')}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                statusFilter === 'DUPLICATE'
                  ? 'bg-indigo-700 text-white border-indigo-700 shadow-sm'
                  : 'bg-white hover:bg-indigo-50/50 border-indigo-200 text-indigo-800'
              }`}
            >
              <div className="text-[10px] font-bold uppercase tracking-wider opacity-70">Duplicates</div>
              <div className="text-xl font-extrabold mt-0.5">{previewData.duplicate_records}</div>
            </button>
          </div>

          {/* Duplicate Strategy & Import Configuration */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              <span>Duplicate Case ID Policy</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <label
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  duplicateStrategy === 'SKIP'
                    ? 'bg-white border-indigo-500 shadow-xs'
                    : 'bg-slate-100/70 border-slate-200 text-slate-600'
                }`}
              >
                <input
                  type="radio"
                  name="dup_policy"
                  value="SKIP"
                  checked={duplicateStrategy === 'SKIP'}
                  onChange={() => setDuplicateStrategy('SKIP')}
                  className="mt-0.5 text-indigo-600 focus:ring-indigo-500"
                />
                <div>
                  <span className="font-bold text-slate-900 block">Skip Duplicates (Recommended)</span>
                  <span className="text-[11px] text-slate-500">
                    Existing database reports remain untouched. Duplicate rows in the upload are omitted.
                  </span>
                </div>
              </label>

              <label
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  duplicateStrategy === 'REPLACE'
                    ? 'bg-white border-indigo-500 shadow-xs'
                    : 'bg-slate-100/70 border-slate-200 text-slate-600'
                }`}
              >
                <input
                  type="radio"
                  name="dup_policy"
                  value="REPLACE"
                  checked={duplicateStrategy === 'REPLACE'}
                  onChange={() => setDuplicateStrategy('REPLACE')}
                  className="mt-0.5 text-indigo-600 focus:ring-indigo-500"
                />
                <div>
                  <span className="font-bold text-slate-900 block">Overwrite / Replace Existing Reports</span>
                  <span className="text-[11px] text-slate-500">
                    Overwrites existing matching Case ID reports with new details and re-runs AI intelligence.
                  </span>
                </div>
              </label>
            </div>
          </div>

          {/* Search and Table Filters Bar */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search preview rows by Case ID, task, or description..."
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
              />
            </div>

            <div className="text-xs text-slate-500 font-medium">
              Showing <strong className="text-slate-900">{getFilteredRows().length}</strong> of{' '}
              <strong className="text-slate-900">{previewData.total_records}</strong> rows
            </div>
          </div>

          {/* Extracted Preview Table */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                  <tr>
                    <th className="py-3 px-3">#</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3">Case ID</th>
                    <th className="py-3 px-3">Department</th>
                    <th className="py-3 px-3">Location</th>
                    <th className="py-3 px-3">Type</th>
                    <th className="py-3 px-3">Task</th>
                    <th className="py-3 px-3">Description Narrative</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {getFilteredRows().length === 0 ? (
                    <tr>
                      <td colSpan="8" className="p-8 text-center text-slate-500">
                        No rows found matching current filter.
                      </td>
                    </tr>
                  ) : (
                    getFilteredRows().map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-3 font-mono text-slate-400 text-[11px]">
                          {row.page_number ? `p.${row.page_number}` : `r.${row.row_number}`}
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          {row.validation_status === 'VALID' ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3" /> Valid
                            </span>
                          ) : row.validation_status === 'WARNING' ? (
                            <span
                              title={row.validation_messages.join(', ')}
                              className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 cursor-help"
                            >
                              <AlertTriangle className="w-3 h-3" /> Warning
                            </span>
                          ) : (
                            <span
                              title={row.validation_messages.join(', ')}
                              className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 cursor-help"
                            >
                              <AlertCircle className="w-3 h-3" /> Error
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 font-mono font-bold text-slate-900 whitespace-nowrap">
                          {row.case_id || <span className="text-slate-400 font-normal italic">Auto-generate</span>}
                          {row.is_duplicate && (
                            <span className="ml-1.5 text-[9px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200 px-1 py-0.2 rounded">
                              Duplicate
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 font-medium text-slate-800">{row.department_name}</td>
                        <td className="py-3 px-3 text-slate-600">{row.location_name}</td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                            {row.incident_type}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-medium text-slate-800 max-w-xs truncate">{row.task}</td>
                        <td className="py-3 px-3 text-slate-600 max-w-sm truncate" title={row.description}>
                          {row.description}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {confirmError && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{confirmError}</span>
            </div>
          )}

          {/* Action Footer */}
          <div className="flex items-center justify-between pt-2">
            <button
              onClick={handleReset}
              className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
            >
              Cancel Import
            </button>

            <button
              onClick={handleConfirmImport}
              disabled={confirming || previewData.total_records === previewData.error_records}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-xl text-xs font-semibold transition-all shadow-sm"
            >
              {confirming ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Ingesting Reports...</span>
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>
                    Confirm & Ingest {previewData.total_records - previewData.error_records} Safety Reports
                  </span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: LIVE BACKGROUND AI PIPELINE PROCESSING */}
      {(step === 'PROCESSING' || step === 'DONE') && (
        <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm text-center space-y-6 max-w-2xl mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto border border-indigo-200 shadow-sm">
            {step === 'DONE' ? (
              <CheckCircle2 className="w-9 h-9 text-emerald-600" />
            ) : (
              <Sparkles className="w-8 h-8 animate-spin" />
            )}
          </div>

          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {step === 'DONE' ? 'Batch Ingestion & AI Intelligence Complete' : 'AI Safety Intelligence Processing'}
            </h2>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              {progressData?.message ||
                'Executing hazard classification, SIF precursor detection, causal explanations, and risk calculations in background.'}
            </p>
          </div>

          {/* Real-time Progress Bar */}
          <div className="space-y-2 max-w-md mx-auto">
            <div className="flex justify-between text-xs font-semibold text-slate-700">
              <span>AI Pipeline Progress</span>
              <span>{progressData ? `${progressData.progress_percentage}%` : 'Starting...'}</span>
            </div>
            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
              <div
                className="h-full bg-indigo-600 transition-all duration-500 rounded-full"
                style={{ width: `${progressData?.progress_percentage || 5}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-500">
              <span>
                Completed: <strong>{progressData?.ai_completed_records || 0}</strong>
              </span>
              <span>
                Failed: <strong>{progressData?.ai_failed_records || 0}</strong>
              </span>
              <span>
                Total: <strong>{progressData?.imported_records || 0}</strong>
              </span>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
            <button
              onClick={() => navigate('/reports')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
            >
              <span>View Incidents in Registry</span>
              <ChevronRight className="w-4 h-4" />
            </button>

            <button
              onClick={handleReset}
              className="w-full sm:w-auto px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
            >
              Import Another File
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
