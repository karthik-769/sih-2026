import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  CheckCircle2,
  AlertCircle,
  Paperclip,
  ArrowRight,
  Info,
  Clock,
  Building2,
  MapPin,
  Briefcase,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getDepartments, getLocations, createReportApi } from '../services/api';

export const SubmitReportPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loadingData, setLoadingData] = useState(true);

  // Form State
  const [caseId, setCaseId] = useState('');
  const [jobRole, setJobRole] = useState(user?.name ? `${user.role} - Field Specialist` : 'Operator');
  const [departmentId, setDepartmentId] = useState('');
  const [locationId, setLocationId] = useState('');
  const [task, setTask] = useState('');
  const [incidentType, setIncidentType] = useState('UNSAFE_CONDITION');
  const [reportedAt, setReportedAt] = useState(() => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  });
  const [description, setDescription] = useState('');
  const [attachmentName, setAttachmentName] = useState('');

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successReport, setSuccessReport] = useState(null);

  useEffect(() => {
    const loadMasterData = async () => {
      setLoadingData(true);
      try {
        const [depts, locs] = await Promise.all([getDepartments(), getLocations()]);
        setDepartments(depts);
        setLocations(locs);
        if (depts.length > 0) setDepartmentId(depts[0].id);
        if (locs.length > 0) setLocationId(locs[0].id);
      } catch (err) {
        setErrorMessage('Failed to load departments and locations.');
      } finally {
        setLoadingData(false);
      }
    };
    loadMasterData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // Client-side validations
    if (!jobRole.trim()) {
      setErrorMessage('Please specify your job role or title.');
      return;
    }
    if (!departmentId) {
      setErrorMessage('Please select a department.');
      return;
    }
    if (!locationId) {
      setErrorMessage('Please select a plant location/unit.');
      return;
    }
    if (!task.trim()) {
      setErrorMessage('Please describe the work task being performed.');
      return;
    }
    if (!description.trim() || description.trim().length < 10) {
      setErrorMessage('Description must be at least 10 characters describing the event.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        job_role: jobRole.trim(),
        department_id: parseInt(departmentId),
        location_id: parseInt(locationId),
        task: task.trim(),
        incident_type: incidentType,
        description: description.trim(),
        case_id: caseId.trim() || null,
        reported_at: reportedAt ? new Date(reportedAt).toISOString() : null,
      };

      const result = await createReportApi(payload);
      setSuccessReport(result);
    } catch (err) {
      const detail = err.response?.data?.error?.message || err.response?.data?.detail;
      setErrorMessage(detail || 'Failed to submit report. Please check required fields.');
    } finally {
      setSubmitting(false);
    }
  };

  if (successReport) {
    return (
      <div className="max-w-2xl mx-auto mt-8">
        <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm text-center space-y-5">
          <div className="w-14 h-14 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-200">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div>
            <h2 className="text-xl font-bold text-slate-900">Safety Report Submitted Successfully</h2>
            <p className="text-xs text-slate-500 mt-1">
              Your report has been stored securely with initial status <span className="font-semibold text-slate-700">SUBMITTED</span>.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-left space-y-2 text-xs">
            <div className="flex justify-between border-b border-slate-200/60 pb-2">
              <span className="text-slate-500">Assigned Case ID:</span>
              <strong className="font-mono text-slate-900 font-bold">{successReport.case_id}</strong>
            </div>
            <div className="flex justify-between border-b border-slate-200/60 pb-2">
              <span className="text-slate-500">Incident Category:</span>
              <span className="font-semibold text-slate-800">{successReport.incident_type}</span>
            </div>
            <div className="flex justify-between border-b border-slate-200/60 pb-2">
              <span className="text-slate-500">Department:</span>
              <span className="text-slate-800">{successReport.department?.name || 'Assigned'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Location:</span>
              <span className="text-slate-800">{successReport.location?.name || 'Assigned'}</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row justify-center gap-3 pt-2">
            <button
              onClick={() => navigate(`/reports/${successReport.id}`)}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition-colors"
            >
              View Report Details
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                setSuccessReport(null);
                setDescription('');
                setTask('');
                setCaseId('');
              }}
              className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors border border-slate-200"
            >
              Submit Another Report
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Submit Safety Report</h2>
            <p className="text-xs text-slate-500">
              Record safety observations, near misses, unsafe acts, and physical workplace hazards.
            </p>
          </div>
        </div>

        {/* Worker Guidance Box */}
        <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
          <p>
            <strong>Worker UX Principle:</strong> Simply describe what happened in your own words.
            You do not need to classify hazards, calculate risk scores, or determine SIF potential—these will be handled automatically in future intelligence steps.
          </p>
        </div>
      </div>

      {/* Submission Form */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 shadow-sm">
        {errorMessage && (
          <div className="mb-6 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Row 1: Case ID & Incident Type */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Case ID <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <input
                type="text"
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                placeholder="Auto-generated if blank (e.g. CASE-2026-XXXX)"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Incident Classification <span className="text-rose-500">*</span>
              </label>
              <select
                value={incidentType}
                onChange={(e) => setIncidentType(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
              >
                <option value="UNSAFE_ACT">Unsafe Act (Behavioral)</option>
                <option value="UNSAFE_CONDITION">Unsafe Condition (Physical / Environmental)</option>
                <option value="NEAR_MISS">Near Miss (Potential Injury / Damage)</option>
                <option value="SAFETY_OBSERVATION">Safety Observation (Proactive Catch)</option>
              </select>
            </div>
          </div>

          {/* Row 2: Department & Location */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Department <span className="text-rose-500">*</span>
              </label>
              <select
                required
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
                disabled={loadingData}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white"
              >
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Plant Location / Unit <span className="text-rose-500">*</span>
              </label>
              <select
                required
                value={locationId}
                onChange={(e) => setLocationId(e.target.value)}
                disabled={loadingData}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white"
              >
                {locations.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name} {l.description ? `(${l.description.slice(0, 30)}...)` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Row 3: Job Role & Task */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Job Role / Designation <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={jobRole}
                onChange={(e) => setJobRole(e.target.value)}
                placeholder="e.g. Millwright, Electrician, Operator"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Specific Work Task <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={task}
                onChange={(e) => setTask(e.target.value)}
                placeholder="e.g. Conveyor Roller Replacement, Transformer Bay Check"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none transition-colors"
              />
            </div>
          </div>

          {/* Row 4: Event Date/Time */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Observation Date & Time <span className="text-rose-500">*</span>
            </label>
            <input
              type="datetime-local"
              required
              value={reportedAt}
              onChange={(e) => setReportedAt(e.target.value)}
              className="w-full sm:w-1/2 px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none transition-colors bg-white font-mono"
            />
          </div>

          {/* Row 5: Description */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700">
                Event Description <span className="text-rose-500">*</span>
              </label>
              <span className="text-[11px] text-slate-400 font-mono">
                {description.length} / 3000 chars (min 10)
              </span>
            </div>
            <textarea
              required
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe factually what occurred, conditions present, tools involved, and immediate actions taken..."
              className="w-full px-3 py-2.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none transition-colors leading-relaxed"
            />
          </div>

          {/* Optional Attachment Placeholder */}
          <div className="pt-2">
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Attachment <span className="text-slate-400 font-normal">(Optional Placeholder)</span>
            </label>
            <div className="border border-dashed border-slate-300 rounded-lg p-3 text-center bg-slate-50/50 hover:bg-slate-50 transition-colors">
              <div className="flex items-center justify-center gap-2 text-xs text-slate-600">
                <Paperclip className="w-4 h-4 text-slate-400" />
                <span>
                  {attachmentName ? (
                    <strong className="text-slate-900">{attachmentName}</strong>
                  ) : (
                    'Attach photo, work permit, or diagram (Simulated upload)'
                  )}
                </span>
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setAttachmentName(e.target.files[0].name);
                    }
                  }}
                />
                <label
                  htmlFor="file-upload"
                  className="ml-2 text-slate-900 underline font-medium cursor-pointer"
                >
                  Browse
                </label>
              </div>
            </div>
          </div>

          {/* Submit Action */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/reports')}
              className="px-4 py-2.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || loadingData}
              className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 disabled:opacity-50"
            >
              {submitting ? 'Submitting Report...' : 'Submit Safety Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
