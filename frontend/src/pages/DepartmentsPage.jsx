import React, { useState, useEffect } from 'react';
import {
  Building2,
  Search,
  RefreshCw,
  Plus,
  Edit2,
  Trash2,
  CheckCircle2,
  BarChart2,
  X,
  AlertTriangle,
} from 'lucide-react';
import {
  getDepartments,
  createDepartmentApi,
  updateDepartmentApi,
  deleteDepartmentApi,
  getDepartmentStatsApi,
} from '../services/api';
import { useAuth } from '../context/AuthContext';

export const DepartmentsPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [statsDept, setStatsDept] = useState(null);
  const [statsData, setStatsData] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  // Form states
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [formError, setFormError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDepts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDepartments();
      setDepartments(data || []);
    } catch (err) {
      console.error('Error fetching departments:', err);
      setError(err.message || 'Failed to load departments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepts();
  }, []);

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setActionLoading(true);
    try {
      await createDepartmentApi(formData);
      setShowCreateModal(false);
      setFormData({ name: '', description: '' });
      await fetchDepts();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create department.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setActionLoading(true);
    try {
      await updateDepartmentApi(editingDept.id, {
        name: editingDept.name,
        description: editingDept.description,
      });
      setEditingDept(null);
      await fetchDepts();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to update department.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (dept) => {
    if (!window.confirm(`Are you sure you want to delete department "${dept.name}"?`)) return;
    try {
      await deleteDepartmentApi(dept.id);
      await fetchDepts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete department.');
    }
  };

  const handleOpenStats = async (dept) => {
    setStatsDept(dept);
    setStatsLoading(true);
    try {
      const data = await getDepartmentStatsApi(dept.id);
      setStatsData(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setStatsLoading(false);
    }
  };

  const filtered = departments.filter(
    (d) =>
      (d.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (d.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 mb-2">
            <Building2 className="w-3.5 h-3.5" />
            <span>Operational Structure</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Plant Departments</h2>
          <p className="text-sm text-slate-600 mt-1">
            Registered operational divisions, safety matrices, and unit incident tracking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchDepts}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {isAdmin && (
            <button
              onClick={() => {
                setFormError('');
                setShowCreateModal(true);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Department
            </button>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center gap-4 bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search departments by name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
          />
        </div>
        <div className="text-xs text-slate-500 font-medium">
          Showing <span className="font-bold text-slate-900">{filtered.length}</span> departments
        </div>
      </div>

      {/* Grid of Departments */}
      {loading ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-xl shadow-sm">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-slate-400 mb-2" />
          <p className="text-sm text-slate-500">Loading department listings...</p>
        </div>
      ) : error ? (
        <div className="p-8 bg-rose-50 border border-rose-200 rounded-xl text-center text-rose-700">
          <p className="font-semibold">Unable to load departments</p>
          <p className="text-xs mt-1">{error}</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-xl shadow-sm">
          <Building2 className="w-8 h-8 mx-auto text-slate-300 mb-2" />
          <p className="text-sm text-slate-500">No departments match your filter criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((dept) => (
            <div
              key={dept.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:border-slate-300 hover:shadow transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center font-bold text-sm">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded font-semibold">
                    ID: #{dept.id}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1">{dept.name}</h3>
                <p className="text-xs text-slate-600 mb-4 line-clamp-2">
                  {dept.description || 'No description provided for this department.'}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span className="inline-flex items-center gap-1 text-emerald-600 font-medium text-[11px]">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Active Unit
                </span>

                {isAdmin && (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleOpenStats(dept)}
                      className="p-1.5 text-slate-500 hover:text-slate-900 rounded hover:bg-slate-100"
                      title="View Department Statistics"
                    >
                      <BarChart2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => {
                        setFormError('');
                        setEditingDept({ ...dept });
                      }}
                      className="p-1.5 text-slate-500 hover:text-slate-900 rounded hover:bg-slate-100"
                      title="Edit Department"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(dept)}
                      className="p-1.5 text-slate-500 hover:text-rose-600 rounded hover:bg-rose-50"
                      title="Delete Department"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-slate-700" />
                Create Plant Department
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-5 space-y-4 text-xs">
              {formError && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
                  {formError}
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Department Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Electrical Maintenance"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  placeholder="Brief description of operations..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-2 border border-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-slate-900 text-white rounded-lg font-semibold hover:bg-slate-800 disabled:opacity-50"
                >
                  {actionLoading ? 'Creating...' : 'Create Department'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingDept && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-slate-700" />
                Edit Department #{editingDept.id}
              </h3>
              <button
                onClick={() => setEditingDept(null)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="p-5 space-y-4 text-xs">
              {formError && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
                  {formError}
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Department Name</label>
                <input
                  type="text"
                  required
                  value={editingDept.name}
                  onChange={(e) => setEditingDept({ ...editingDept, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={editingDept.description || ''}
                  onChange={(e) => setEditingDept({ ...editingDept, description: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingDept(null)}
                  className="px-3 py-2 border border-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-slate-900 text-white rounded-lg font-semibold hover:bg-slate-800 disabled:opacity-50"
                >
                  {actionLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Stats Modal */}
      {statsDept && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-slate-700" />
                Department Safety Metrics: {statsDept.name}
              </h3>
              <button
                onClick={() => {
                  setStatsDept(null);
                  setStatsData(null);
                }}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs">
              {statsLoading ? (
                <div className="text-center py-8 text-slate-400">Loading metrics...</div>
              ) : statsData ? (
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">Total Reports</span>
                    <div className="text-xl font-bold text-slate-900 mt-1">{statsData.total_reports}</div>
                  </div>
                  <div className="bg-rose-50 p-3 rounded-lg border border-rose-200">
                    <span className="text-[10px] text-rose-600 uppercase font-semibold">Critical Incidents</span>
                    <div className="text-xl font-bold text-rose-700 mt-1">{statsData.critical_risk_reports}</div>
                  </div>
                  <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                    <span className="text-[10px] text-purple-600 uppercase font-semibold">SIF Precursors</span>
                    <div className="text-xl font-bold text-purple-700 mt-1">{statsData.sif_precursors}</div>
                  </div>
                  <div className="bg-amber-50 p-3 rounded-lg border border-amber-200">
                    <span className="text-[10px] text-amber-600 uppercase font-semibold">Active Alerts</span>
                    <div className="text-xl font-bold text-amber-700 mt-1">{statsData.active_alerts}</div>
                  </div>
                  <div className="col-span-2 bg-emerald-50 p-3 rounded-lg border border-emerald-200 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-emerald-700 uppercase font-semibold">Open Corrective Actions</span>
                      <div className="text-lg font-bold text-emerald-800">{statsData.open_actions} Open</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-slate-400">No data available</div>
              )}
            </div>

            <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
              <button
                onClick={() => {
                  setStatsDept(null);
                  setStatsData(null);
                }}
                className="px-4 py-2 bg-slate-900 text-white font-semibold rounded-lg text-xs hover:bg-slate-800 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default DepartmentsPage;
