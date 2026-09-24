const API_BASE = window.location.origin.includes('5173')
  ? 'http://localhost:8000'
  : window.location.origin;

export const api = {
  // Incidents
  async getIncidents(limit = 50, threatType = 'ALL', severity = 'ALL') {
    const res = await fetch(`${API_BASE}/api/incidents?limit=${limit}&threat_type=${threatType}&severity=${severity}`);
    return res.json();
  },

  async updateIncidentStatus(id, status) {
    const res = await fetch(`${API_BASE}/api/incidents/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    return res.json();
  },

  getExportIncidentsUrl() {
    return `${API_BASE}/api/incidents/export`;
  },

  getScreenshotUrl(relativeOrFilename) {
    if (!relativeOrFilename) return '';
    if (relativeOrFilename.startsWith('http')) return relativeOrFilename;
    if (relativeOrFilename.startsWith('/api/')) return `${API_BASE}${relativeOrFilename}`;
    return `${API_BASE}/api/incidents/screenshot/${relativeOrFilename}`;
  },

  // Cameras
  async getCameras() {
    const res = await fetch(`${API_BASE}/api/cameras`);
    return res.json();
  },

  async switchCamera(cameraId, sourceType, sourceUrl) {
    const res = await fetch(`${API_BASE}/api/cameras/switch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        camera_id: cameraId,
        source_type: sourceType,
        source_url: sourceUrl
      })
    });
    return res.json();
  },

  async uploadVideo(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/api/cameras/upload_video`, {
      method: 'POST',
      body: formData
    });
    return res.json();
  },

  // Faces
  async getAuthorizedFaces() {
    const res = await fetch(`${API_BASE}/api/faces`);
    return res.json();
  },

  async enrollFaceBase64(name, role, department, imageBase64) {
    const res = await fetch(`${API_BASE}/api/faces/enroll_base64`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        role,
        department,
        image_base64: imageBase64
      })
    });
    return res.json();
  },

  async deleteFace(faceId) {
    const res = await fetch(`${API_BASE}/api/faces/${faceId}`, {
      method: 'DELETE'
    });
    return res.json();
  },

  // System
  async getSystemStatus() {
    const res = await fetch(`${API_BASE}/api/system/status`);
    return res.json();
  },

  async toggleModule(moduleName, enabled) {
    const res = await fetch(`${API_BASE}/api/system/toggle_module`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module_name: moduleName, enabled })
    });
    return res.json();
  },

  async triggerTestAlert(threatType, severity) {
    const res = await fetch(`${API_BASE}/api/system/test_alert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ threat_type: threatType, severity })
    });
    return res.json();
  },

  // Stream URL
  getVideoFeedUrl() {
    return `${API_BASE}/api/stream/video_feed`;
  },

  // WebSocket connection helper
  createWebSocket(onMessage, onError) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.origin.includes('5173')
      ? 'localhost:8000'
      : window.location.host;
    
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/api/stream/ws`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (err) {
        console.error("WS Parse Error", err);
      }
    };
    if (onError) ws.onerror = onError;
    return ws;
  }
};
