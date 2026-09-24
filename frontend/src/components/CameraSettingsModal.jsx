import React, { useState, useEffect } from 'react';
import { X, Camera, Play, Video, Upload, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export default function CameraSettingsModal({ isOpen, onClose, activeCameraId, onCameraSwitched }) {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadCameras();
    }
  }, [isOpen]);

  const loadCameras = async () => {
    setLoading(true);
    try {
      const data = await api.getCameras();
      setCameras(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSwitch = async (camId, sourceType, sourceUrl) => {
    setStatusMsg(`Switching feed to ${camId}...`);
    try {
      const res = await api.switchCamera(camId, sourceType, sourceUrl);
      if (res.status === 'success') {
        setStatusMsg(`Active camera set to ${camId} (${sourceType})`);
        loadCameras();
        if (onCameraSwitched) onCameraSwitched(camId);
      }
    } catch (err) {
      setStatusMsg("Failed to switch camera.");
    }
  };

  const handleVideoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setStatusMsg(`Uploading surveillance file ${file.name}...`);
    try {
      const res = await api.uploadVideo(file);
      if (res.status === 'success') {
        setStatusMsg(`Uploaded ${file.name}. AI Pipeline running inference!`);
        if (onCameraSwitched) onCameraSwitched('cam-uploaded');
        loadCameras();
      }
    } catch (err) {
      setStatusMsg("Upload failed. Make sure video format is MP4/AVI.");
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '750px' }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-dim)',
          background: 'rgba(10, 16, 28, 0.95)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Camera size={22} color="var(--cyan)" />
            <h2 className="font-display" style={{ fontSize: '1.2rem', color: '#fff' }}>
              SURVEILLANCE INPUT CHANNELS
            </h2>
          </div>
          <button id="btn-close-cams" className="btn btn-secondary" onClick={onClose} style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        {/* Channels List */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {statusMsg && (
            <div style={{ padding: '10px 14px', background: 'rgba(0, 240, 255, 0.1)', border: '1px solid var(--cyan)', borderRadius: '6px', fontSize: '0.85rem', color: 'var(--cyan)' }}>
              {statusMsg}
            </div>
          )}

          {/* Quick Presets */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            {/* Preset 1: Synthetic Threat Demo */}
            <div
              className="cyber-card"
              style={{
                padding: '14px',
                cursor: 'pointer',
                borderColor: activeCameraId === 'cam-1' ? 'var(--cyan)' : 'var(--border-dim)',
                boxShadow: activeCameraId === 'cam-1' ? '0 0 15px var(--cyan-glow)' : 'none'
              }}
              onClick={() => handleSwitch('cam-1', 'demo', 'demo')}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="badge badge-medium">OUT-OF-BOX DEMO</span>
                {activeCameraId === 'cam-1' && <CheckCircle2 size={16} color="var(--cyan)" />}
              </div>
              <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>Sector Alpha Simulator</div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Simulates real-time CCTV scenarios: fights, falls, luggage abandonment, and face checkpoints.
              </p>
            </div>

            {/* Preset 2: Physical Webcam 0 */}
            <div
              className="cyber-card"
              style={{
                padding: '14px',
                cursor: 'pointer',
                borderColor: activeCameraId === 'cam-2' ? 'var(--cyan)' : 'var(--border-dim)',
                boxShadow: activeCameraId === 'cam-2' ? '0 0 15px var(--cyan-glow)' : 'none'
              }}
              onClick={() => handleSwitch('cam-2', 'webcam', '0')}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="badge badge-success">LIVE HARDWARE</span>
                {activeCameraId === 'cam-2' && <CheckCircle2 size={16} color="var(--emerald)" />}
              </div>
              <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>Physical Webcam (0)</div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Streams directly from your integrated laptop camera or connected USB webcam.
              </p>
            </div>

            {/* Preset 3: Upload Video */}
            <div
              className="cyber-card"
              style={{
                padding: '14px',
                cursor: 'pointer',
                borderColor: activeCameraId === 'cam-uploaded' ? 'var(--cyan)' : 'var(--border-dim)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="badge badge-high">FILE INPUT</span>
                {activeCameraId === 'cam-uploaded' && <CheckCircle2 size={16} color="var(--warning)" />}
              </div>
              <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>Upload CCTV Video</div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px', marginBottom: '8px' }}>
                Analyze any MP4 or AVI footage with the deep learning pipeline.
              </p>
              <label className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center', fontSize: '0.75rem' }}>
                <Upload size={14} />
                <span>{isUploading ? 'UPLOADING...' : 'CHOOSE VIDEO'}</span>
                <input type="file" accept="video/*" onChange={handleVideoUpload} style={{ display: 'none' }} disabled={isUploading} />
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
