import React from 'react';
import { Activity, ShieldCheck, Zap, AlertTriangle, Users, Flame, PackageX } from 'lucide-react';

export default function AnalyticsPanel({
  fps = 0,
  personsCount = 0,
  threatLevel = 'NORMAL',
  incidents = []
}) {
  // Aggregate stats from incidents
  const total = incidents.length;
  const fights = incidents.filter(i => i.threat_type === 'FIGHT_VIOLENCE').length;
  const falls = incidents.filter(i => i.threat_type === 'FALL_DETECTED').length;
  const abandoned = incidents.filter(i => i.threat_type === 'ABANDONED_OBJECT').length;
  const intruders = incidents.filter(i => i.threat_type === 'UNAUTHORIZED_PERSON').length;

  const getPercent = (count) => {
    if (total === 0) return 0;
    return Math.round((count / total) * 100);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
      {/* Metric 1: Persons Tracked */}
      <div className="cyber-card" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            TRACKED PERSONS
          </span>
          <Users size={18} color="var(--cyan)" />
        </div>
        <div className="font-mono" style={{ fontSize: '1.8rem', fontWeight: 700, color: '#fff' }}>
          {personsCount}
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--emerald)', marginTop: '4px' }}>
          ● Real-time YOLOv8 ByteTrack
        </div>
      </div>

      {/* Metric 2: Total Logged Incidents */}
      <div className="cyber-card" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            TOTAL INCIDENTS
          </span>
          <Activity size={18} color="var(--danger)" />
        </div>
        <div className="font-mono" style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--danger)' }}>
          {total}
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '4px' }}>
          Stored in SQLite Evidence Vault
        </div>
      </div>

      {/* Metric 3: Real-Time FPS & Hardware */}
      <div className="cyber-card" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            INFERENCE THROUGHPUT
          </span>
          <Zap size={18} color="var(--emerald)" />
        </div>
        <div className="font-mono" style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--emerald)' }}>
          {fps} <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>FPS</span>
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--cyan)', marginTop: '4px' }}>
          CPU Real-Time Multithreaded
        </div>
      </div>

      {/* Metric 4: Threat Classification Breakdown */}
      <div className="cyber-card" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            ANOMALY BREAKDOWN
          </span>
          <ShieldCheck size={18} color="var(--warning)" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
          {/* Fights */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              <span>🥊 Violent Fights</span>
              <span className="font-mono">{fights} ({getPercent(fights)}%)</span>
            </div>
            <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ width: `${getPercent(fights)}%`, height: '100%', background: 'var(--danger)' }} />
            </div>
          </div>

          {/* Falls */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              <span>🚨 Fall Accidents</span>
              <span className="font-mono">{falls} ({getPercent(falls)}%)</span>
            </div>
            <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ width: `${getPercent(falls)}%`, height: '100%', background: 'var(--warning)' }} />
            </div>
          </div>

          {/* Abandoned Luggage */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              <span>🧍 Abandoned Luggage</span>
              <span className="font-mono">{abandoned} ({getPercent(abandoned)}%)</span>
            </div>
            <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ width: `${getPercent(abandoned)}%`, height: '100%', background: 'var(--cyan)' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
