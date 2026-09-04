import React, { useState, useEffect } from 'react';
import { MapPin, Search, RefreshCw, Compass, ExternalLink, CheckCircle2, Globe } from 'lucide-react';
import { getLocations } from '../services/api';

export const LocationsPage = () => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);

  const fetchLocs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLocations();
      setLocations(data || []);
    } catch (err) {
      console.error('Error fetching locations:', err);
      setError(err.message || 'Failed to load locations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLocs();
  }, []);

  const filtered = locations.filter((l) =>
    (l.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 mb-2">
            <Compass className="w-3.5 h-3.5" />
            <span>GIS & Physical Zones</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Plant Physical Locations</h2>
          <p className="text-sm text-slate-600 mt-1">
            Registered operational sites, machinery bays, warehouses, and geo-coordinates.
          </p>
        </div>
        <button
          onClick={fetchLocs}
          disabled={loading}
          className="self-start sm:self-center inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center gap-4 bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search plant locations, sectors, or bays..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
          />
        </div>
        <div className="text-xs text-slate-500 font-medium">
          Showing <span className="font-bold text-slate-900">{filtered.length}</span> locations
        </div>
      </div>

      {/* Grid of Locations */}
      {loading ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-xl shadow-sm">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-slate-400 mb-2" />
          <p className="text-sm text-slate-500">Loading location coordinates...</p>
        </div>
      ) : error ? (
        <div className="p-8 bg-rose-50 border border-rose-200 rounded-xl text-center text-rose-700">
          <p className="font-semibold">Unable to load plant locations</p>
          <p className="text-xs mt-1">{error}</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-xl shadow-sm">
          <MapPin className="w-8 h-8 mx-auto text-slate-300 mb-2" />
          <p className="text-sm text-slate-500">No plant locations match your filter criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((loc) => (
            <div
              key={loc.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:border-slate-300 hover:shadow transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm">
                    <MapPin className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded font-semibold">
                    ID: #{loc.id}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1">{loc.name}</h3>
                <p className="text-xs text-slate-600 mb-4 line-clamp-2">
                  {loc.description || 'General plant site area.'}
                </p>
              </div>

              <div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs font-mono text-slate-700 flex items-center justify-between mb-3">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-sans font-semibold">GPS Coordinates</span>
                    <span>{loc.latitude ? loc.latitude.toFixed(4) : '28.6139'}, {loc.longitude ? loc.longitude.toFixed(4) : '77.2090'}</span>
                  </div>
                  <a
                    href={`https://www.google.com/maps?q=${loc.latitude || 28.6139},${loc.longitude || 77.2090}`}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
                    title="View in Maps"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Monitored Zone
                  </span>
                  <span className="font-mono text-[11px]">
                    {loc.created_at ? new Date(loc.created_at).toLocaleDateString() : 'Active'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
