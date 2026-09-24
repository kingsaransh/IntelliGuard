import React, { useState, useEffect } from 'react';
import { Shield, ShieldAlert, ShieldCheck, Volume2, VolumeX, History, Users, Camera, BellRing } from 'lucide-react';
import { soundAlert } from '../utils/audioAlert';

export default function Navbar({
  threatLevel = 'NORMAL',
  activeThreatCount = 0,
  onOpenIncidents,
  onOpenFaces,
  onOpenCameras,
  onTriggerTestAlert
}) {
  const [timeStr, setTimeStr] = useState('');
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-US', { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleMute = () => {
    const muted = soundAlert.toggleMute();
    setIsMuted(muted);
  };

  const isCritical = threatLevel === 'CRITICAL';
  const isHigh = threatLevel === 'HIGH';

  return (
    <header className="navbar-container" style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 24px',
      background: 'rgba(8, 12, 22, 0.92)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-dim)',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      {/* Brand & Threat Level */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(0, 240, 255, 0.1)',
          padding: '6px 14px',
          borderRadius: '8px',
          border: '1px solid rgba(0, 240, 255, 0.3)'
        }}>
          <Shield style={{ color: 'var(--cyan)', width: 22, height: 22 }} />
          <div>
            <span className="font-display" style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>
              INTELLI<span style={{ color: 'var(--cyan)' }}>GUARD</span>
            </span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', display: 'block', letterSpacing: '1px' }}>
              DEEP LEARNING SOC v2.0
            </span>
          </div>
        </div>

        {/* Threat Status Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '6px',
          background: isCritical ? 'rgba(255, 51, 102, 0.18)' : (isHigh ? 'rgba(255, 170, 0, 0.18)' : 'rgba(0, 255, 157, 0.12)'),
          border: `1px solid ${isCritical ? 'var(--danger)' : (isHigh ? 'var(--warning)' : 'var(--emerald)')}`
        }}>
          <span className={`indicator-dot ${isCritical ? 'dot-danger' : (isHigh ? 'dot-warning' : 'dot-normal')}`}></span>
          <span className="font-mono" style={{
            fontSize: '0.8rem',
            fontWeight: 700,
            color: isCritical ? 'var(--danger)' : (isHigh ? 'var(--warning)' : 'var(--emerald)')
          }}>
            DEFCON STATUS: {threatLevel} {activeThreatCount > 0 ? `(${activeThreatCount} ACTIVE)` : ''}
          </span>
        </div>
      </div>

      {/* Clock & Action Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Time code */}
        <div className="font-mono" style={{
          background: 'rgba(14, 20, 32, 0.8)',
          border: '1px solid var(--border-dim)',
          padding: '6px 12px',
          borderRadius: '6px',
          color: 'var(--cyan)',
          fontSize: '0.85rem'
        }}>
          SEC-TIME: {timeStr}
        </div>

        {/* Audio Mute Toggle */}
        <button
          id="btn-mute-toggle"
          className="btn btn-secondary"
          onClick={handleToggleMute}
          title={isMuted ? "Unmute Alarm Chimes" : "Mute Alarm Chimes"}
        >
          {isMuted ? <VolumeX size={16} color="var(--danger)" /> : <Volume2 size={16} color="var(--cyan)" />}
          <span>{isMuted ? 'MUTED' : 'AUDIO ON'}</span>
        </button>

        {/* Quick Modals */}
        <button
          id="btn-open-incidents"
          className="btn btn-secondary"
          onClick={onOpenIncidents}
        >
          <History size={16} />
          <span>INCIDENT VAULT</span>
        </button>

        <button
          id="btn-open-faces"
          className="btn btn-secondary"
          onClick={onOpenFaces}
        >
          <Users size={16} />
          <span>FACE ACCESS</span>
        </button>

        <button
          id="btn-open-cameras"
          className="btn btn-secondary"
          onClick={onOpenCameras}
        >
          <Camera size={16} />
          <span>CAM FEED</span>
        </button>

        <button
          id="btn-trigger-test"
          className="btn btn-danger"
          onClick={onTriggerTestAlert}
          title="Trigger a simulated alarm to test audio and emergency dispatch"
        >
          <BellRing size={16} />
          <span>TEST ALARM</span>
        </button>
      </div>
    </header>
  );
}
