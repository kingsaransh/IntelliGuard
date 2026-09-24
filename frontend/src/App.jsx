import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import LiveCameraFeed from './components/LiveCameraFeed';
import ThreatAlertFeed from './components/ThreatAlertFeed';
import AnalyticsPanel from './components/AnalyticsPanel';
import IncidentLogModal from './components/IncidentLogModal';
import FaceManagerModal from './components/FaceManagerModal';
import CameraSettingsModal from './components/CameraSettingsModal';

import { api } from './services/api';
import { soundAlert } from './utils/audioAlert';

export default function App() {
  // Live Telemetry State
  const [telemetry, setTelemetry] = useState({
    camera_id: 'cam-1',
    fps: 28.5,
    persons_detected: 0,
    active_threats_count: 0,
    active_threats: [],
    threat_level: 'NORMAL',
    modules_active: {
      person_tracking: true,
      fight_detection: true,
      fall_detection: true,
      abandoned_detection: true,
      face_recognition: true
    }
  });

  // Recent Incidents list for radar & analytics
  const [recentIncidents, setRecentIncidents] = useState([]);
  
  // Modals state
  const [isIncidentsOpen, setIsIncidentsOpen] = useState(false);
  const [isFacesOpen, setIsFacesOpen] = useState(false);
  const [isCamerasOpen, setIsCamerasOpen] = useState(false);
  const [selectedIncidentForEvidence, setSelectedIncidentForEvidence] = useState(null);

  const prevThreatCountRef = useRef(0);

  // Poll recent incidents & establish live WebSocket
  const loadRecentIncidents = async () => {
    try {
      const data = await api.getIncidents(15);
      setRecentIncidents(data);
    } catch (err) {
      console.error("Error loading incidents", err);
    }
  };

  useEffect(() => {
    loadRecentIncidents();
    const interval = setInterval(loadRecentIncidents, 4000);
    return () => clearInterval(interval);
  }, []);

  // Live WebSocket Telemetry Loop
  useEffect(() => {
    let ws = null;
    const connectWS = () => {
      ws = api.createWebSocket(
        (data) => {
          setTelemetry(prev => ({
            ...prev,
            ...data
          }));

          // Check if new critical threats arrived
          const currentCount = data.active_threats_count || 0;
          if (currentCount > prevThreatCountRef.current) {
            // New threat detected! Play alarm sound
            if (data.threat_level === 'CRITICAL') {
              soundAlert.playCriticalAlarm();
            } else if (data.threat_level === 'HIGH') {
              soundAlert.playWarningChime();
            }
            loadRecentIncidents();
          }
          prevThreatCountRef.current = currentCount;
        },
        (err) => {
          console.warn("WebSocket disconnected, reconnecting in 3s...", err);
          setTimeout(connectWS, 3000);
        }
      );
    };

    connectWS();
    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Handle module toggles (Fight, Fall, Bag, Face)
  const handleModuleToggle = async (moduleName, enabled) => {
    try {
      await api.toggleModule(moduleName, enabled);
      setTelemetry(prev => ({
        ...prev,
        modules_active: {
          ...prev.modules_active,
          [moduleName]: enabled
        }
      }));
    } catch (err) {
      console.error("Error toggling module", err);
    }
  };

  // Trigger test alarm
  const handleTriggerTestAlert = async () => {
    soundAlert.playCriticalAlarm();
    try {
      await api.triggerTestAlert('FIGHT_VIOLENCE', 'CRITICAL');
      loadRecentIncidents();
    } catch (err) {
      console.error("Error triggering test alert", err);
    }
  };

  // Acknowledge alert
  const handleAcknowledgeAlert = async (id) => {
    if (!id) return;
    try {
      await api.updateIncidentStatus(id, 'ACKNOWLEDGED');
      loadRecentIncidents();
      soundAlert.playSuccessChime();
    } catch (err) {
      console.error(err);
    }
  };

  // Evidence inspector trigger
  const handleSelectIncident = (incident) => {
    setSelectedIncidentForEvidence(incident);
    setIsIncidentsOpen(true);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
      {/* Top Navbar */}
      <Navbar
        threatLevel={telemetry.threat_level}
        activeThreatCount={telemetry.active_threats_count}
        onOpenIncidents={() => setIsIncidentsOpen(true)}
        onOpenFaces={() => setIsFacesOpen(true)}
        onOpenCameras={() => setIsCamerasOpen(true)}
        onTriggerTestAlert={handleTriggerTestAlert}
      />

      {/* Main SOC Dashboard Body */}
      <main style={{
        flex: 1,
        padding: '16px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        maxWidth: '1700px',
        width: '100%',
        margin: '0 auto'
      }}>
        {/* Top Grid: Camera Viewport (Left 70%) & Threat Radar Feed (Right 30%) */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 2fr) minmax(320px, 1fr)',
          gap: '16px',
          alignItems: 'stretch'
        }}>
          <LiveCameraFeed
            cameraId={telemetry.camera_id}
            fps={telemetry.fps}
            personsCount={telemetry.persons_detected}
            modulesActive={telemetry.modules_active}
            onModuleToggle={handleModuleToggle}
          />

          <ThreatAlertFeed
            alerts={recentIncidents}
            onSelectIncident={handleSelectIncident}
            onAcknowledgeAlert={handleAcknowledgeAlert}
          />
        </div>

        {/* Bottom Section: Analytics & Performance Metrics */}
        <AnalyticsPanel
          fps={telemetry.fps}
          personsCount={telemetry.persons_detected}
          threatLevel={telemetry.threat_level}
          incidents={recentIncidents}
        />
      </main>

      {/* Modals */}
      <IncidentLogModal
        isOpen={isIncidentsOpen}
        onClose={() => {
          setIsIncidentsOpen(false);
          setSelectedIncidentForEvidence(null);
        }}
        selectedIncident={selectedIncidentForEvidence}
      />

      <FaceManagerModal
        isOpen={isFacesOpen}
        onClose={() => setIsFacesOpen(false)}
      />

      <CameraSettingsModal
        isOpen={isCamerasOpen}
        onClose={() => setIsCamerasOpen(false)}
        activeCameraId={telemetry.camera_id}
        onCameraSwitched={(newCamId) => {
          setTelemetry(prev => ({ ...prev, camera_id: newCamId }));
        }}
      />
    </div>
  );
}
