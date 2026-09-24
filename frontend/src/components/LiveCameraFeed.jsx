import React, { useState, useRef } from 'react';
import { Maximize, Minimize, Camera, RefreshCw, Eye, EyeOff, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export default function LiveCameraFeed({
  cameraId = 'cam-1',
  fps = 0,
  personsCount = 0,
  modulesActive = {},
  onModuleToggle
}) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const containerRef = useRef(null);
  const streamUrl = `${api.getVideoFeedUrl()}?t=${isRefreshing ? Date.now() : ''}`;

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(err => console.error(err));
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const handleRefreshStream = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 300);
  };

  const captureSnapshot = () => {
    const img = document.getElementById('live-stream-img');
    if (!img) return;
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth || 960;
    canvas.height = img.naturalHeight || 540;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    const link = document.createElement('a');
    link.download = `intelliguard_snapshot_${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  return (
    <div
      ref={containerRef}
      className="cyber-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        background: '#04070d'
      }}
    >
      {/* Top Feed Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 14px',
        background: 'rgba(10, 16, 28, 0.95)',
        borderBottom: '1px solid var(--border-dim)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="font-mono" style={{ color: 'var(--cyan)', fontSize: '0.85rem', fontWeight: 600 }}>
            SURVEILLANCE FEED: {cameraId.toUpperCase()}
          </span>
          <span className="badge badge-medium">
            AI PROCESSING 30 FPS
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            id="btn-refresh-feed"
            className="btn btn-secondary"
            onClick={handleRefreshStream}
            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
            title="Reload Video Stream"
          >
            <RefreshCw size={14} className={isRefreshing ? "spin" : ""} />
          </button>
          <button
            id="btn-snapshot"
            className="btn btn-secondary"
            onClick={captureSnapshot}
            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
            title="Download Instant Snapshot"
          >
            <Camera size={14} />
            <span>SNAPSHOT</span>
          </button>
          <button
            id="btn-fullscreen"
            className="btn btn-secondary"
            onClick={toggleFullscreen}
            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
          >
            {isFullscreen ? <Minimize size={14} /> : <Maximize size={14} />}
          </button>
        </div>
      </div>

      {/* Main Video Viewport */}
      <div style={{
        position: 'relative',
        width: '100%',
        aspectRatio: '16/9',
        backgroundColor: '#020408',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <img
          id="live-stream-img"
          src={streamUrl}
          alt="IntelliGuard Surveillance Stream"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain'
          }}
          onError={(e) => {
            // Graceful reconnect retry
            setTimeout(() => {
              if (e.target) e.target.src = `${api.getVideoFeedUrl()}?retry=${Date.now()}`;
            }, 2000);
          }}
        />

        {/* Scanline & Lens Vignette */}
        <div className="scanline-overlay" />

        {/* Corner Reticles */}
        <div style={{
          position: 'absolute',
          top: 12,
          left: 12,
          width: 20,
          height: 20,
          borderTop: '2px solid var(--cyan)',
          borderLeft: '2px solid var(--cyan)',
          pointerEvents: 'none'
        }} />
        <div style={{
          position: 'absolute',
          top: 12,
          right: 12,
          width: 20,
          height: 20,
          borderTop: '2px solid var(--cyan)',
          borderRight: '2px solid var(--cyan)',
          pointerEvents: 'none'
        }} />
        <div style={{
          position: 'absolute',
          bottom: 12,
          left: 12,
          width: 20,
          height: 20,
          borderBottom: '2px solid var(--cyan)',
          borderLeft: '2px solid var(--cyan)',
          pointerEvents: 'none'
        }} />
        <div style={{
          position: 'absolute',
          bottom: 12,
          right: 12,
          width: 20,
          height: 20,
          borderBottom: '2px solid var(--cyan)',
          borderRight: '2px solid var(--cyan)',
          pointerEvents: 'none'
        }} />
      </div>

      {/* Bottom Detection Modules Control Bar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 14px',
        background: 'rgba(10, 16, 28, 0.95)',
        borderTop: '1px solid var(--border-dim)',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600 }}>AI PIPELINE:</span>
          
          <button
            className={`badge ${modulesActive.fight_detection !== false ? 'badge-critical' : 'badge-secondary'}`}
            onClick={() => onModuleToggle('fight_detection', !modulesActive.fight_detection)}
            style={{ cursor: 'pointer', background: modulesActive.fight_detection !== false ? 'rgba(255,51,102,0.2)' : 'rgba(255,255,255,0.05)' }}
          >
            🥊 FIGHT/VIOLENCE (CNN-LSTM)
          </button>

          <button
            className={`badge ${modulesActive.fall_detection !== false ? 'badge-high' : 'badge-secondary'}`}
            onClick={() => onModuleToggle('fall_detection', !modulesActive.fall_detection)}
            style={{ cursor: 'pointer', background: modulesActive.fall_detection !== false ? 'rgba(255,170,0,0.2)' : 'rgba(255,255,255,0.05)' }}
          >
            🚨 FALL COLLAPSE
          </button>

          <button
            className={`badge ${modulesActive.abandoned_detection !== false ? 'badge-medium' : 'badge-secondary'}`}
            onClick={() => onModuleToggle('abandoned_detection', !modulesActive.abandoned_detection)}
            style={{ cursor: 'pointer', background: modulesActive.abandoned_detection !== false ? 'rgba(0,240,255,0.2)' : 'rgba(255,255,255,0.05)' }}
          >
            🧍 ABANDONED BAGS
          </button>

          <button
            className={`badge ${modulesActive.face_recognition !== false ? 'badge-success' : 'badge-secondary'}`}
            onClick={() => onModuleToggle('face_recognition', !modulesActive.face_recognition)}
            style={{ cursor: 'pointer', background: modulesActive.face_recognition !== false ? 'rgba(0,255,157,0.2)' : 'rgba(255,255,255,0.05)' }}
          >
            🔐 FACE ACCESS
          </button>
        </div>

        <div className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          DETECTIONS: <span style={{ color: 'var(--emerald)', fontWeight: 700 }}>{personsCount} PERSONS</span> | REAL-TIME FPS: <span style={{ color: 'var(--cyan)' }}>{fps}</span>
        </div>
      </div>
    </div>
  );
}
