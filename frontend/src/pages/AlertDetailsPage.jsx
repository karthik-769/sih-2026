import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Bell,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Building2,
  MapPin,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  FileText,
  Plus,
  ExternalLink,
  ShieldCheck,
  Check,
  X,
} from 'lucide-react';
import { getAlertByIdApi, updateAlertApi, createCorrectiveActionApi } from '../services/api';

export const AlertDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Action Modal state
  const [showActionModal, setShowActionModal] = useState(false);
  const [actionTitle, setActionTitle] = useState('');
  const [actionDesc, setActionDesc] = useState('');
  const [actionRec, setActionRec] = useState('');
  const [actionPriority, setActionPriority] = useState('HIGH');
  const [actionDueDate, setActionDueDate] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);
  const [actionError, setActionError] = useState('');

  const loadAlert = async () => {
    setLoading(true);
    try {
      const res = await getAlertByIdApi(id);
      setAlert(res);
      if (res.recommended_actions?.length > 0) {
        setActionRec(res.recommended_actions[0]);
      }
      setActionTitle(`Corrective Action: ${res.title}`);
      setActionDesc(`Address early warning alert evidence: ${res.description}`);
    } catch (err) {
      setError('Failed to load alert details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlert();
  }, [id]);

  const handleStatusUpdate = async (newStatus) => {
    try {
      await updateAlertApi(id, { status: newStatus });
      await loadAlert();
    } catch (err) {
      console.error('Failed to update alert status', err);
    }
  };

  const handleCreateAction = async (e) => {
    e.preventDefault();
    setSubmittingAction(true);
    setActionError('');
    try {
      await createCorrectiveActionApi({
        alert_id: alert.id,
        pattern_id: alert.pattern_id,
        title: actionTitle,
        description: actionDesc,
        recommended_action: actionRec,
        priority: actionPriority,
        department_id: alert.department_id,
        location_id: alert.location_id,
        due_date: actionDueDate ? new Date(actionDueDate).toISOString() : null,
      });
      setShowActionModal(false);
      await loadAlert();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to create corrective action.';
      setActionError(msg);
    } finally {
      setSubmittingAction(false);
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
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
        Loading alert intelligence...
      </div>
    );
  }

  if (error || !alert) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center max-w-md mx-auto space-y-4">
        <p className="text-xs text-rose-600 font-semibold">{error || 'Alert not found'}</p>
        <button
          onClick={() => navigate('/alerts')}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold"
        >
          Back to Alerts
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Back Button */}
      <div>
        <button
          onClick={() => navigate('/alerts')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to Early Warning Alerts</span>
        </button>
      </div>

      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1 rounded text-xs uppercase tracking-wider border ${getSeverityBadge(alert.severity)}`}>
              {alert.severity} SEVERITY &bull; Risk Score {alert.risk_score} / 100
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              {alert.status}
            </span>
            <span className="text-xs font-mono text-slate-400">{alert.alert_key}</span>
          </div>

          <div className="flex items-center gap-2">
            {alert.status === 'NEW' && (
              <button
                onClick={() => handleStatusUpdate('ACKNOWLEDGED')}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition-colors"
              >
                Acknowledge Alert
              </button>
            )}
            {alert.status !== 'RESOLVED' && alert.status !== 'DISMISSED' && (
              <button
                onClick={() => handleStatusUpdate('RESOLVED')}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors"
              >
                Mark Resolved
              </button>
            )}
            <button
              onClick={() => setShowActionModal(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Corrective Action</span>
            </button>
          </div>
        </div>

        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">{alert.title}</h1>
          <p className="text-xs text-slate-600 mt-1">{alert.description}</p>
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mt-3">
            {alert.location_name && (
              <span className="flex items-center gap-1 font-medium">
                <MapPin className="w-4 h-4 text-slate-400" /> {alert.location_name}
              </span>
            )}
            {alert.department_name && (
              <span className="flex items-center gap-1 font-medium">
                <Building2 className="w-4 h-4 text-slate-400" /> {alert.department_name}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4 text-slate-400" /> {new Date(alert.created_at).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Why This Alert Was Generated: Evidence Section */}
      <div className="bg-white border border-rose-200 rounded-xl p-6 shadow-sm space-y-3">
        <div className="flex items-center gap-2 text-rose-700 font-bold text-sm">
          <ShieldAlert className="w-4 h-4" />
          <span>Why This Alert Was Generated (Data-Backed Evidence)</span>
        </div>
        <ul className="space-y-2 text-xs text-slate-800">
          {(alert.explanation_evidence || []).map((bullet, idx) => (
            <li key={idx} className="flex items-start gap-2 bg-rose-50/50 border border-rose-100 p-3 rounded-lg">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-600 flex-shrink-0 mt-1.5" />
              <span className="font-medium">{bullet}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Recommended Preventive Actions */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Recommended Preventive Actions</span>
        </h3>
        <ul className="space-y-2 text-xs text-slate-700">
          {(alert.recommended_actions || []).map((rec, idx) => (
            <li key={idx} className="flex items-start gap-2 bg-emerald-50/50 border border-emerald-100 p-3 rounded-lg">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Linked Corrective Actions */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900">Corrective Actions Created</h3>
          <button
            onClick={() => setShowActionModal(true)}
            className="text-xs font-semibold text-indigo-600 hover:underline flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" /> New Action
          </button>
        </div>

        {alert.corrective_actions?.length === 0 ? (
          <p className="text-xs text-slate-500 italic">
            No corrective actions have been assigned to this alert yet. Click "Create Corrective Action" to assign tasks.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {alert.corrective_actions.map((act) => (
              <div key={act.id} className="py-3 flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-900">{act.action_number}</span>
                    <span className="font-bold px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {act.priority}
                    </span>
                    <span className="px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                      {act.status}
                    </span>
                  </div>
                  <p className="text-slate-800 font-medium mt-1">{act.title}</p>
                </div>

                <div className="text-right text-slate-500">
                  <div>Assignee: <strong className="text-slate-800">{act.assignee_name || 'Unassigned'}</strong></div>
                  {act.due_date && <div>Due: {new Date(act.due_date).toLocaleDateString()}</div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Contributing Reports */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Contributing Incident Reports</h3>
        <div className="divide-y divide-slate-100">
          {(alert.contributing_reports || []).map((rep) => (
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
                <p className="text-xs text-slate-700">{rep.description}</p>
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

      {/* Create Corrective Action Modal */}
      {showActionModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900">Create Corrective Action</h3>
              <button onClick={() => setShowActionModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateAction} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Action Title</label>
                <input
                  type="text"
                  required
                  value={actionTitle}
                  onChange={(e) => setActionTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Description</label>
                <textarea
                  rows={2}
                  required
                  value={actionDesc}
                  onChange={(e) => setActionDesc(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Mandatory Preventive Measure</label>
                <textarea
                  rows={2}
                  required
                  value={actionRec}
                  onChange={(e) => setActionRec(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Priority</label>
                  <select
                    value={actionPriority}
                    onChange={(e) => setActionPriority(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
                  >
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Due Deadline</label>
                  <input
                    type="date"
                    value={actionDueDate}
                    onChange={(e) => setActionDueDate(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
                  />
                </div>
              </div>

              {actionError && (
                <p className="text-rose-600 text-[11px] font-medium">{actionError}</p>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowActionModal(false)}
                  className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingAction}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg font-semibold shadow-sm"
                >
                  {submittingAction ? 'Creating...' : 'Assign Action'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
