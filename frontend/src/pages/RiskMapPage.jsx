import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import {
  MapPin,
  AlertTriangle,
  Flame,
  ShieldCheck,
  RefreshCw,
  Building2,
  FileText,
  Clock,
  Layers,
} from 'lucide-react';
import { getRiskMapApi } from '../services/api';

// Create custom colored circle marker icons
const createMapIcon = (riskLevel) => {
  let color = '#10b981'; // Green
  if (riskLevel === 'CRITICAL') color = '#e11d48'; // Red
  else if (riskLevel === 'HIGH') color = '#ea580c'; // Orange
  else if (riskLevel === 'MEDIUM') color = '#d97706'; // Amber

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="34" height="34">
      <circle cx="12" cy="12" r="10" fill="${color}" stroke="#ffffff" stroke-width="2.5" />
      <circle cx="12" cy="12" r="4" fill="#ffffff" />
    </svg>
  `;
  return L.divIcon({
    html: svg,
    className: 'custom-leaflet-marker',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -17],
  });
};

export const RiskMapPage = () => {
  const [markers, setMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState(null);

  const fetchRiskMap = async () => {
    setLoading(true);
    try {
      const res = await getRiskMapApi();
      setMarkers(res);
      if (res.length > 0) {
        setSelectedLocation(res[0]);
      }
    } catch (err) {
      console.error('Failed to load risk map markers', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskMap();
  }, []);

  const getSeverityBadge = (level) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-rose-50 text-rose-700 border-rose-200 font-bold';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200 font-semibold';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
  };

  const centerPosition = markers.length > 0
    ? [markers[0].latitude, markers[0].longitude]
    : [19.0760, 72.8777];

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
              Geo-Spatial Safety Intelligence
            </span>
            <span className="text-xs font-semibold text-slate-500">Live Plant Risk Telemetry</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Plant Safety Risk Map</h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Interactive geo-spatial risk mapping across operational plant units, high-risk concentrations, and open corrective actions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchRiskMap}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh map telemetry"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Map + Side Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive Leaflet Map (2 Cols) */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden min-h-[480px] relative z-0">
          {loading ? (
            <div className="h-[480px] flex items-center justify-center text-xs text-slate-500">
              <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Loading plant coordinates...
            </div>
          ) : (
            <MapContainer
              center={centerPosition}
              zoom={13}
              scrollWheelZoom={false}
              className="h-[480px] w-full z-0"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {markers.map((m) => (
                <Marker
                  key={m.location_id}
                  position={[m.latitude, m.longitude]}
                  icon={createMapIcon(m.risk_level)}
                  eventHandlers={{
                    click: () => setSelectedLocation(m),
                  }}
                >
                  <Popup>
                    <div className="p-1 space-y-1.5 text-xs">
                      <div className="font-bold text-slate-900 text-sm">{m.location_name}</div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${getSeverityBadge(m.risk_level)}`}>
                          {m.risk_level} &bull; Score {m.risk_score}
                        </span>
                      </div>
                      <div className="text-slate-600 pt-1">
                        <div>Total Reports: <strong>{m.total_reports}</strong></div>
                        <div>SIF Precursors: <strong className="text-rose-600">{m.sif_precursors}</strong></div>
                        <div>Open Actions: <strong>{m.open_corrective_actions}</strong></div>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          )}
        </div>

        {/* Selected Unit Details Panel (1 Col) */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
              <h3 className="text-sm font-bold text-slate-900">Unit Risk Profile</h3>
              {selectedLocation && (
                <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${getSeverityBadge(selectedLocation.risk_level)}`}>
                  {selectedLocation.risk_level}
                </span>
              )}
            </div>

            {selectedLocation ? (
              <div className="space-y-4 text-xs">
                <div>
                  <h4 className="text-base font-bold text-slate-900">{selectedLocation.location_name}</h4>
                  <p className="text-slate-500 font-mono text-[11px] mt-0.5">
                    Coordinates: {selectedLocation.latitude?.toFixed(4)}, {selectedLocation.longitude?.toFixed(4)}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="text-slate-500">Risk Score</div>
                    <div className="text-lg font-extrabold text-slate-900">{selectedLocation.risk_score} / 100</div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="text-slate-500">Total Reports</div>
                    <div className="text-lg font-extrabold text-slate-900">{selectedLocation.total_reports}</div>
                  </div>
                  <div className="p-3 bg-rose-50 rounded-lg border border-rose-200">
                    <div className="text-rose-600 font-semibold">SIF Precursors</div>
                    <div className="text-lg font-extrabold text-rose-700">{selectedLocation.sif_precursors}</div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="text-slate-500">Open Actions</div>
                    <div className="text-lg font-extrabold text-slate-900">{selectedLocation.open_corrective_actions}</div>
                  </div>
                </div>

                <div>
                  <h5 className="font-bold text-slate-800 mb-1.5">Main Hazards Identified</h5>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedLocation.top_hazards?.map((h, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] border border-slate-200">
                        {h}
                      </span>
                    ))}
                  </div>
                </div>

                {selectedLocation.recent_alerts?.length > 0 && (
                  <div>
                    <h5 className="font-bold text-slate-800 mb-1.5">Active Early Warnings</h5>
                    <ul className="space-y-1 text-[11px] text-rose-700">
                      {selectedLocation.recent_alerts.map((al, idx) => (
                        <li key={idx} className="bg-rose-50 border border-rose-200 p-2 rounded">
                          {al}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500">Click a pin on the map to inspect unit safety telemetry.</p>
            )}
          </div>

          <div className="border-t border-slate-100 pt-3 text-[11px] text-slate-400">
            * Coordinates mapped to operational site layouts.
          </div>
        </div>
      </div>
    </div>
  );
};
