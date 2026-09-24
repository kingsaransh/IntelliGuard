import React, { useState, useEffect } from 'react';
import { X, Download, Eye, CheckCircle2, ShieldAlert, Filter, Search } from 'lucide-react';
import { api } from '../services/api';

export default function IncidentLogModal({ isOpen, onClose, selectedIncident, onClearSelectedIncident }) {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [threatFilter, setThreatFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [activeEvidence, setActiveEvidence] = useState(null);

  useEffect(() => {
    if (selectedIncident) {
      setActiveEvidence(selectedIncident);
    }
  }, [selectedIncident]);

  useEffect(() => {
    if (isOpen) {
      fetchIncidents();
    }
  }, [isOpen, threatFilter, severityFilter]);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const data = await api.getIncidents(100, threatFilter, severityFilter);
      setIncidents(data);
    } catch (err) {
      console.error("Error fetching incidents", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (id, newStatus) => {
    try {
      await api.updateIncidentStatus(id, newStatus);
      fetchIncidents();
      if (activeEvidence && activeEvidence.id === id) {
        setActiveEvidence(prev => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      console.error("Error updating incident status", err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '1050px' }}>
        {/* Modal Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-dim)',
          background: 'rgba(10, 16, 28, 0.95)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert size={22} color="var(--danger)" />
            <h2 className="font-display" style={{ fontSize: '1.2rem', color: '#fff' }}>
              INTELLIGUARD INCIDENT EVIDENCE VAULT
            </h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <a
              href={api.getExportIncidentsUrl()}
              download
              className="btn btn-secondary"
              style={{ fontSize: '0.78rem' }}
            >
              <Download size={14} />
              <span>EXPORT CSV</span>
            </a>
            <button
              id="btn-close-incidents"
              className="btn btn-secondary"
              onClick={onClose}
              style={{ padding: '6px' }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Filters Bar */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 20px',
          background: 'rgba(14, 22, 38, 0.6)',
          borderBottom: '1px solid var(--border-dim)',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Filter size={16} color="var(--cyan)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Threat:</span>
            <select
              className="cyber-input"
              value={threatFilter}
              onChange={e => setThreatFilter(e.target.value)}
              style={{ width: 'auto', padding: '4px 10px', fontSize: '0.8rem' }}
            >
              <option value="ALL">All Anomalies</option>
              <option value="FIGHT_VIOLENCE">Fight / Violence</option>
              <option value="FALL_DETECTED">Fall / Emergency</option>
              <option value="ABANDONED_OBJECT">Abandoned Luggage</option>
              <option value="UNAUTHORIZED_PERSON">Unauthorized Face</option>
            </select>

            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '8px' }}>Severity:</span>
            <select
              className="cyber-input"
              value={severityFilter}
              onChange={e => setSeverityFilter(e.target.value)}
              style={{ width: 'auto', padding: '4px 10px', fontSize: '0.8rem' }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
            </select>
          </div>

          <span className="font-mono" style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
            RECORDS: {incidents.length}
          </span>
        </div>

        {/* Main Body: Table + Side Evidence Viewer */}
        <div style={{ display: 'grid', gridTemplateColumns: activeEvidence ? '1.2fr 1fr' : '1fr', gap: '16px', padding: '20px' }}>
          {/* Incidents Table */}
          <div style={{ overflowX: 'auto', maxHeight: '520px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-dim)', color: 'var(--text-dim)' }}>
                  <th style={{ padding: '8px 10px' }}>ID</th>
                  <th style={{ padding: '8px 10px' }}>TIMESTAMP</th>
                  <th style={{ padding: '8px 10px' }}>THREAT</th>
                  <th style={{ padding: '8px 10px' }}>SEV</th>
                  <th style={{ padding: '8px 10px' }}>CONF</th>
                  <th style={{ padding: '8px 10px' }}>STATUS</th>
                  <th style={{ padding: '8px 10px' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {incidents.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-dim)' }}>
                      No incidents matching current filters.
                    </td>
                  </tr>
                ) : (
                  incidents.map(inc => (
                    <tr
                      key={inc.id}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        background: activeEvidence?.id === inc.id ? 'rgba(0, 240, 255, 0.08)' : 'transparent',
                        cursor: 'pointer'
                      }}
                      onClick={() => setActiveEvidence(inc)}
                    >
                      <td className="font-mono" style={{ padding: '8px 10px', color: 'var(--cyan)' }}>#{inc.id}</td>
                      <td className="font-mono" style={{ padding: '8px 10px', color: 'var(--text-secondary)' }}>
                        {inc.timestamp.split(' ')[1] || inc.timestamp}
                      </td>
                      <td style={{ padding: '8px 10px', fontWeight: 600, color: '#fff' }}>
                        {inc.threat_type.replace('_', ' ')}
                      </td>
                      <td style={{ padding: '8px 10px' }}>
                        <span className={`badge ${inc.severity === 'CRITICAL' ? 'badge-critical' : (inc.severity === 'HIGH' ? 'badge-high' : 'badge-medium')}`}>
                          {inc.severity}
                        </span>
                      </td>
                      <td className="font-mono" style={{ padding: '8px 10px', color: 'var(--text-primary)' }}>
                        {Math.round(inc.confidence * 100)}%
                      </td>
                      <td style={{ padding: '8px 10px' }}>
                        <span style={{
                          color: inc.status === 'RESOLVED' ? 'var(--emerald)' : (inc.status === 'ACKNOWLEDGED' ? 'var(--cyan)' : 'var(--warning)'),
                          fontWeight: 600,
                          fontSize: '0.75rem'
                        }}>
                          {inc.status}
                        </span>
                      </td>
                      <td style={{ padding: '8px 10px' }}>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <button
                            className="btn btn-secondary"
                            onClick={(e) => { e.stopPropagation(); setActiveEvidence(inc); }}
                            style={{ padding: '2px 6px', fontSize: '0.7rem' }}
                          >
                            <Eye size={12} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Evidence Inspector Side Panel */}
          {activeEvidence && (
            <div className="cyber-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h3 className="font-display" style={{ fontSize: '0.95rem', color: 'var(--cyan)' }}>
                  EVIDENCE SNAPSHOT #{activeEvidence.id}
                </h3>
                <button
                  className="btn btn-secondary"
                  onClick={() => setActiveEvidence(null)}
                  style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                >
                  CLOSE PREVIEW
                </button>
              </div>

              {activeEvidence.screenshot_path ? (
                <div style={{ borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-bright)' }}>
                  <img
                    src={api.getScreenshotUrl(activeEvidence.screenshot_path)}
                    alt="Evidence Screenshot"
                    style={{ width: '100%', height: 'auto', display: 'block' }}
                  />
                </div>
              ) : (
                <div style={{ padding: '40px', textAlign: 'center', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', color: 'var(--text-dim)' }}>
                  No screenshot evidence captured.
                </div>
              )}

              {/* Threat Details */}
              <div style={{ fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div><strong style={{ color: 'var(--text-secondary)' }}>Type:</strong> <span style={{ color: '#fff' }}>{activeEvidence.threat_type}</span></div>
                <div><strong style={{ color: 'var(--text-secondary)' }}>Timestamp:</strong> <span className="font-mono">{activeEvidence.timestamp}</span></div>
                <div><strong style={{ color: 'var(--text-secondary)' }}>Camera:</strong> <span className="font-mono">{activeEvidence.camera_id}</span></div>
                <div><strong style={{ color: 'var(--text-secondary)' }}>Confidence:</strong> <span className="font-mono" style={{ color: 'var(--cyan)' }}>{Math.round(activeEvidence.confidence * 100)}%</span></div>
                <div><strong style={{ color: 'var(--text-secondary)' }}>Details:</strong> <span style={{ color: 'var(--text-primary)' }}>{activeEvidence.description}</span></div>
              </div>

              {/* Status Update Buttons */}
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => handleUpdateStatus(activeEvidence.id, 'ACKNOWLEDGED')}
                  style={{ flex: 1, fontSize: '0.75rem', justifyContent: 'center' }}
                >
                  ACKNOWLEDGE
                </button>
                <button
                  className="btn btn-success"
                  onClick={() => handleUpdateStatus(activeEvidence.id, 'RESOLVED')}
                  style={{ flex: 1, fontSize: '0.75rem', justifyContent: 'center' }}
                >
                  RESOLVE
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
