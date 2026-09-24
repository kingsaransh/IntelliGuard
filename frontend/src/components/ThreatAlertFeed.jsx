import React from 'react';
import { AlertCircle, ShieldAlert, CheckCircle2, Eye, Flame, UserX, AlertTriangle, PackageX } from 'lucide-react';
import { api } from '../services/api';

export default function ThreatAlertFeed({
  alerts = [],
  onSelectIncident,
  onAcknowledgeAlert
}) {
  const getThreatIcon = (type) => {
    switch (type) {
      case 'FIGHT_VIOLENCE':
        return <Flame size={18} color="#ff3366" />;
      case 'FALL_DETECTED':
        return <AlertTriangle size={18} color="#ffaa00" />;
      case 'ABANDONED_OBJECT':
        return <PackageX size={18} color="#00f0ff" />;
      case 'UNAUTHORIZED_PERSON':
        return <UserX size={18} color="#a855f7" />;
      default:
        return <AlertCircle size={18} color="#ff3366" />;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return <span className="badge badge-critical">CRITICAL</span>;
      case 'HIGH':
        return <span className="badge badge-high">HIGH</span>;
      default:
        return <span className="badge badge-medium">MEDIUM</span>;
    }
  };

  return (
    <div className="cyber-card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Feed Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-dim)',
        background: 'rgba(12, 18, 30, 0.95)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={18} color="var(--danger)" />
          <h3 className="font-display" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
            ACTIVE THREAT RADAR
          </h3>
        </div>
        <span className="badge badge-critical" style={{ fontSize: '0.7rem' }}>
          LIVE FEED ({alerts.length})
        </span>
      </div>

      {/* Alerts Scrollable List */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        maxHeight: '480px'
      }}>
        {alerts.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px 20px',
            color: 'var(--text-dim)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '10px'
          }}>
            <CheckCircle2 size={36} color="var(--emerald)" style={{ opacity: 0.8 }} />
            <div className="font-display" style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
              ALL SECTORS SECURE
            </div>
            <p style={{ fontSize: '0.78rem' }}>
              No active anomalies or hazardous incidents detected in monitored feeds.
            </p>
          </div>
        ) : (
          alerts.map((alert) => {
            const isCritical = alert.severity === 'CRITICAL';
            return (
              <div
                key={`${alert.id || alert.timestamp}-${alert.threat_type}`}
                style={{
                  background: isCritical ? 'rgba(35, 12, 22, 0.7)' : 'rgba(18, 26, 44, 0.7)',
                  border: `1px solid ${isCritical ? 'rgba(255, 51, 102, 0.4)' : 'rgba(0, 240, 255, 0.2)'}`,
                  borderRadius: '8px',
                  padding: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  boxShadow: isCritical ? '0 0 15px rgba(255, 51, 102, 0.15)' : 'none',
                  transition: 'transform 0.15s ease'
                }}
              >
                {/* Header row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getThreatIcon(alert.threat_type)}
                    <span className="font-display" style={{ fontWeight: 700, fontSize: '0.88rem', color: '#fff' }}>
                      {alert.threat_type.replace('_', ' ')}
                    </span>
                  </div>
                  {getSeverityBadge(alert.severity)}
                </div>

                {/* Description */}
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {alert.description || 'Abnormal activity identified by deep learning network'}
                </p>

                {/* Metadata & Actions */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingTop: '6px',
                  borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                  fontSize: '0.75rem'
                }}>
                  <div className="font-mono" style={{ color: 'var(--text-dim)' }}>
                    <span>CONF: {Math.round(alert.confidence * 100)}%</span>
                    <span style={{ margin: '0 6px' }}>•</span>
                    <span>{alert.timestamp ? alert.timestamp.split(' ')[1] || alert.timestamp : 'NOW'}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {alert.screenshot_path && (
                      <button
                        className="btn btn-secondary"
                        onClick={() => onSelectIncident(alert)}
                        style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                        title="Inspect Evidence Screenshot"
                      >
                        <Eye size={12} />
                        <span>EVIDENCE</span>
                      </button>
                    )}
                    <button
                      className="btn btn-secondary"
                      onClick={() => onAcknowledgeAlert(alert.id)}
                      style={{ padding: '3px 8px', fontSize: '0.72rem', color: 'var(--emerald)' }}
                      title="Acknowledge Threat"
                    >
                      <CheckCircle2 size={12} />
                      <span>ACK</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
