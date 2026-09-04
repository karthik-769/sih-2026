import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  Plus,
  RefreshCw,
  Search,
  Filter,
  UserCheck,
  Building2,
  MapPin,
  Calendar,
  X,
  Check,
  AlertCircle,
} from 'lucide-react';
import { getCorrectiveActionsApi, createCorrectiveActionApi, updateCorrectiveActionApi, getDepartments, getLocations } from '../services/api';

export const CorrectiveActionsPage = () => {
  const [actions, setActions] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Master data
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);

  // Create Modal state
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [recommendedAction, setRecommendedAction] = useState('');
  const [priority, setPriority] = useState('HIGH');
  const [dueDate, setDueDate] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [locationId, setLocationId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');

  const fetchActions = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 10,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      };
      const res = await getCorrectiveActionsApi(params);
      setActions(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load corrective actions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadMaster = async () => {
      try {
        const [d, l] = await Promise.all([getDepartments(), getLocations()]);
        setDepartments(d);
        setLocations(l);
      } catch (err) {
        console.error('Master data load failed', err);
      }
    };
    loadMaster();
  }, []);

  useEffect(() => {
    fetchActions();
  }, [page, statusFilter, priorityFilter]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setModalError('');
    try {
      await createCorrectiveActionApi({
        title,
        description,
        recommended_action: recommendedAction,
        priority,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        department_id: departmentId ? parseInt(departmentId, 10) : null,
        location_id: locationId ? parseInt(locationId, 10) : null,
      });
      setShowModal(false);
      setTitle('');
      setDescription('');
      setRecommendedAction('');
      setDueDate('');
      await fetchActions();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to create action.';
      setModalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateStatus = async (actionId, newStatus) => {
    try {
      await updateCorrectiveActionApi(actionId, { status: newStatus });
      await fetchActions();
    } catch (err) {
      console.error('Failed to update status', err);
    }
  };

  const getPriorityBadge = (p) => {
    switch (p) {
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

  const getStatusBadge = (st, isOverdue) => {
    if (isOverdue || st === 'OVERDUE') {
      return 'bg-rose-600 text-white font-bold animate-pulse';
    }
    switch (st) {
      case 'RESOLVED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'IN_PROGRESS':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'ASSIGNED':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const overdueCount = actions.filter((a) => a.is_overdue || a.status === 'OVERDUE').length;

  const filteredActions = actions.filter((a) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      a.action_number.toLowerCase().includes(q) ||
      a.title.toLowerCase().includes(q) ||
      a.description.toLowerCase().includes(q) ||
      (a.assignee_name && a.assignee_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
              Preventive & Corrective Action System
            </span>
            <span className="text-xs font-semibold text-slate-500">{total} Actions Logged</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Corrective Action Management</h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Track, assign, and enforce deadline accountability on preventive actions generated from high-risk alerts and safety patterns.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Action</span>
          </button>
        </div>
      </div>

      {/* Overdue Warning Notification Banner */}
      {overdueCount > 0 && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-center justify-between text-xs text-rose-900 shadow-xs">
          <div className="flex items-center gap-2 font-semibold">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <span>
              {overdueCount} corrective action(s) have exceeded their due deadline and require immediate escalation!
            </span>
          </div>
          <button
            onClick={() => {
              setStatusFilter('OVERDUE');
              setPage(1);
            }}
            className="px-3 py-1 bg-rose-600 text-white font-bold rounded-lg hover:bg-rose-700 transition-colors"
          >
            View Overdue
          </button>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-500 font-medium">Status:</span>
          {['', 'OPEN', 'ASSIGNED', 'IN_PROGRESS', 'OVERDUE', 'RESOLVED'].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
                statusFilter === st
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              {st === '' ? 'All Status' : st}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-500 font-medium">Priority:</span>
          {['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => (
            <button
              key={p}
              onClick={() => {
                setPriorityFilter(p);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
                priorityFilter === p
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              {p === '' ? 'All Priorities' : p}
            </button>
          ))}
        </div>
      </div>

      {/* Actions Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading corrective actions...
          </div>
        ) : filteredActions.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 space-y-2">
            <CheckCircle2 className="w-8 h-8 mx-auto text-slate-400" />
            <p className="font-semibold text-slate-700">No corrective actions found matching filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                <tr>
                  <th className="py-3 px-4">Action #</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Action Item & Measure</th>
                  <th className="py-3 px-4">Location / Dept</th>
                  <th className="py-3 px-4">Assignee</th>
                  <th className="py-3 px-4">Due Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Workflow</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredActions.map((act) => (
                  <tr key={act.id} className="hover:bg-slate-50/75 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900 whitespace-nowrap">
                      {act.action_number}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border ${getPriorityBadge(act.priority)}`}>
                        {act.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4 max-w-sm">
                      <div className="font-bold text-slate-900">{act.title}</div>
                      <div className="text-slate-600 truncate mt-0.5">{act.recommended_action}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                      <div>{act.location_name || 'Plant-wide'}</div>
                      <div className="text-slate-400 text-[11px]">{act.department_name || 'Operations'}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-700 whitespace-nowrap">
                      {act.assignee_name || <span className="text-slate-400 italic">Unassigned</span>}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {act.due_date ? (
                        <span className={act.is_overdue ? 'text-rose-600 font-bold' : 'text-slate-600'}>
                          {new Date(act.due_date).toLocaleDateString()}
                        </span>
                      ) : (
                        <span className="text-slate-400">None</span>
                      )}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border ${getStatusBadge(act.status, act.is_overdue)}`}>
                        {act.is_overdue ? 'OVERDUE' : act.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      {act.status !== 'RESOLVED' ? (
                        <div className="flex items-center justify-end gap-1.5">
                          {act.status !== 'IN_PROGRESS' && (
                            <button
                              onClick={() => handleUpdateStatus(act.id, 'IN_PROGRESS')}
                              className="px-2 py-1 rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-semibold text-[11px] transition-colors"
                            >
                              In Progress
                            </button>
                          )}
                          <button
                            onClick={() => handleUpdateStatus(act.id, 'RESOLVED')}
                            className="px-2 py-1 rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold text-[11px] transition-colors"
                          >
                            Resolve
                          </button>
                        </div>
                      ) : (
                        <span className="text-emerald-600 font-semibold text-[11px] flex items-center justify-end gap-1">
                          <Check className="w-3.5 h-3.5" /> Resolved
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900">Create Corrective Action</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Action Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Calibrate atmospheric testing monitors in Unit C"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Issue Description</label>
                <textarea
                  rows={2}
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe hazard condition and why action is required..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Mandatory Preventive Measure</label>
                <textarea
                  rows={2}
                  required
                  value={recommendedAction}
                  onChange={(e) => setRecommendedAction(e.target.value)}
                  placeholder="Specific task to be completed..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Department</label>
                  <select
                    value={departmentId}
                    onChange={(e) => setDepartmentId(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
                  >
                    <option value="">Plant-wide / General</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Location</label>
                  <select
                    value={locationId}
                    onChange={(e) => setLocationId(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
                  >
                    <option value="">All Locations</option>
                    {locations.map((l) => (
                      <option key={l.id} value={l.id}>{l.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white font-medium"
                  >
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Due Date</label>
                  <input
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:outline-none"
                  />
                </div>
              </div>

              {modalError && (
                <p className="text-rose-600 text-[11px] font-medium">{modalError}</p>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg font-semibold shadow-sm"
                >
                  {submitting ? 'Creating...' : 'Create Action'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
