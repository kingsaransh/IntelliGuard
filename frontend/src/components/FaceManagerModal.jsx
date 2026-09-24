import React, { useState, useEffect } from 'react';
import { X, UserPlus, Trash2, ShieldCheck, Camera, Upload, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function FaceManagerModal({ isOpen, onClose }) {
  const [faces, setFaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [role, setRole] = useState('Security Staff');
  const [department, setDepartment] = useState('Surveillance Unit');
  const [selectedImageBase64, setSelectedImageBase64] = useState(null);
  const [statusMsg, setStatusMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadFaces();
    }
  }, [isOpen]);

  const loadFaces = async () => {
    setLoading(true);
    try {
      const data = await api.getAuthorizedFaces();
      setFaces(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setSelectedImageBase64(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleCaptureFromStream = () => {
    const img = document.getElementById('live-stream-img');
    if (!img) {
      setStatusMsg("No active video feed found to capture.");
      return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth || 960;
    canvas.height = img.naturalHeight || 540;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg');
    setSelectedImageBase64(dataUrl);
    setStatusMsg("Captured frame from live stream. Fill in name and submit.");
  };

  const handleEnrollSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setStatusMsg("Please enter person name.");
      return;
    }
    if (!selectedImageBase64) {
      setStatusMsg("Please upload a photo or capture from live feed.");
      return;
    }

    setIsSubmitting(true);
    setStatusMsg("Extracting 128-d face embedding...");
    try {
      const res = await api.enrollFaceBase64(name, role, department, selectedImageBase64);
      if (res.status === 'success') {
        setStatusMsg(`Enrolled ${name} successfully!`);
        setName('');
        setSelectedImageBase64(null);
        loadFaces();
      } else {
        setStatusMsg(res.detail || "Enrollment failed.");
      }
    } catch (err) {
      setStatusMsg("Error communicating with facial recognition server.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteFace = async (faceId) => {
    if (!confirm("Revoke authorization for this person?")) return;
    try {
      await api.deleteFace(faceId);
      loadFaces();
    } catch (err) {
      console.error(err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '900px' }}>
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
            <ShieldCheck size={22} color="var(--cyan)" />
            <h2 className="font-display" style={{ fontSize: '1.2rem', color: '#fff' }}>
              AUTHORIZED FACIAL ACCESS ROSTER
            </h2>
          </div>
          <button id="btn-close-faces" className="btn btn-secondary" onClick={onClose} style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        {/* Content Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '20px', padding: '20px' }}>
          {/* Left: Enroll Form */}
          <div className="cyber-card" style={{ padding: '16px' }}>
            <h3 className="font-display" style={{ fontSize: '0.95rem', color: 'var(--cyan)', marginBottom: '12px' }}>
              ENROLL AUTHORIZED INDIVIDUAL
            </h3>

            <form onSubmit={handleEnrollSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  FULL NAME
                </label>
                <input
                  id="input-face-name"
                  type="text"
                  className="cyber-input"
                  placeholder="e.g. Officer Alex Vance"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  SECURITY CLEARANCE ROLE
                </label>
                <select
                  id="select-face-role"
                  className="cyber-input"
                  value={role}
                  onChange={e => setRole(e.target.value)}
                >
                  <option value="Security Staff">Security Officer</option>
                  <option value="Executive / Admin">Executive / Admin</option>
                  <option value="Authorized Staff">Authorized Staff</option>
                  <option value="Approved Visitor">Approved Visitor</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  DEPARTMENT / UNIT
                </label>
                <input
                  type="text"
                  className="cyber-input"
                  placeholder="e.g. Security Division"
                  value={department}
                  onChange={e => setDepartment(e.target.value)}
                />
              </div>

              {/* Photo Options */}
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  PORTRAIT IMAGE
                </label>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                  <label className="btn btn-secondary" style={{ flex: 1, fontSize: '0.75rem', justifyContent: 'center' }}>
                    <Upload size={14} />
                    <span>UPLOAD</span>
                    <input type="file" accept="image/*" onChange={handleFileSelect} style={{ display: 'none' }} />
                  </label>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleCaptureFromStream}
                    style={{ flex: 1, fontSize: '0.75rem', justifyContent: 'center' }}
                  >
                    <Camera size={14} />
                    <span>FROM FEED</span>
                  </button>
                </div>

                {selectedImageBase64 && (
                  <div style={{ textAlign: 'center', marginTop: '6px' }}>
                    <img
                      src={selectedImageBase64}
                      alt="Selected Preview"
                      style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '6px', border: '1px solid var(--cyan)' }}
                    />
                  </div>
                )}
              </div>

              {statusMsg && (
                <div style={{ fontSize: '0.78rem', color: statusMsg.includes('success') ? 'var(--emerald)' : 'var(--warning)', padding: '6px', background: 'rgba(0,0,0,0.3)', borderRadius: '4px' }}>
                  {statusMsg}
                </div>
              )}

              <button
                id="btn-submit-face"
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting}
                style={{ marginTop: '8px', justifyContent: 'center' }}
              >
                <UserPlus size={16} />
                <span>{isSubmitting ? 'PROCESSING EMBEDDING...' : 'SAVE & AUTHORIZE'}</span>
              </button>
            </form>
          </div>

          {/* Right: Enrolled Faces Roster */}
          <div className="cyber-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column' }}>
            <h3 className="font-display" style={{ fontSize: '0.95rem', color: 'var(--cyan)', marginBottom: '12px' }}>
              ENROLLED PERSONNEL ({faces.length})
            </h3>

            <div style={{ overflowY: 'auto', maxHeight: '420px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {faces.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-dim)' }}>
                  No authorized personnel registered yet.
                </div>
              ) : (
                faces.map(f => (
                  <div
                    key={f.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px',
                      background: 'rgba(12, 18, 30, 0.7)',
                      border: '1px solid var(--border-dim)',
                      borderRadius: '6px'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>{f.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--cyan)' }}>{f.role} • {f.department || 'General'}</div>
                      <div className="font-mono" style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                        ID #{f.id} • 128-d Embedding Active
                      </div>
                    </div>

                    <button
                      className="btn btn-secondary"
                      onClick={() => handleDeleteFace(f.id)}
                      style={{ padding: '6px', color: 'var(--danger)' }}
                      title="Revoke Clearance"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
