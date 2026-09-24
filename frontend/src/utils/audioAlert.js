class SoundAlertManager {
  constructor() {
    this.audioCtx = null;
    this.isMuted = false;
    this.volume = 1.0; // Default to maximum 100% volume
  }

  _initContext() {
    if (!this.audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.audioCtx = new AudioContextClass();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    return this.isMuted;
  }

  setVolume(vol) {
    this.volume = Math.max(0.0, Math.min(1.0, vol));
  }

  playCriticalAlarm() {
    if (this.isMuted) return;
    try {
      this._initContext();
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;

      // Dynamics Compressor to maximize acoustic loudness and punch without clipping distortion
      const compressor = this.audioCtx.createDynamicsCompressor();
      compressor.threshold.setValueAtTime(-4, now);
      compressor.knee.setValueAtTime(12, now);
      compressor.ratio.setValueAtTime(10, now);
      compressor.attack.setValueAtTime(0.002, now);
      compressor.release.setValueAtTime(0.12, now);
      compressor.connect(this.audioCtx.destination);

      // Play 3 loud, high-impact siren pulses (total duration ~1.1s)
      const pulses = [
        { start: now + 0.00, dur: 0.28, startFreq: 1050, endFreq: 1650 },
        { start: now + 0.36, dur: 0.28, startFreq: 1050, endFreq: 1650 },
        { start: now + 0.72, dur: 0.34, startFreq: 1100, endFreq: 1750 }
      ];

      pulses.forEach(({ start, dur, startFreq, endFreq }) => {
        const osc1 = this.audioCtx.createOscillator();
        const osc2 = this.audioCtx.createOscillator();
        const gainNode = this.audioCtx.createGain();

        // Sawtooth + Square wave for sharp acoustic penetration in the 1kHz - 1.8kHz range
        osc1.type = 'sawtooth';
        osc2.type = 'square';

        osc1.frequency.setValueAtTime(startFreq, start);
        osc1.frequency.exponentialRampToValueAtTime(endFreq, start + dur * 0.75);
        osc1.frequency.linearRampToValueAtTime(endFreq - 200, start + dur);

        osc2.frequency.setValueAtTime(startFreq * 0.75, start);
        osc2.frequency.exponentialRampToValueAtTime(endFreq * 0.8, start + dur * 0.75);
        osc2.frequency.linearRampToValueAtTime((endFreq - 200) * 0.75, start + dur);

        // High volume ceiling (0.95)
        const peakGain = 0.95 * this.volume;
        gainNode.gain.setValueAtTime(0.01, start);
        gainNode.gain.linearRampToValueAtTime(peakGain, start + 0.02);
        gainNode.gain.setValueAtTime(peakGain, start + dur * 0.8);
        gainNode.gain.exponentialRampToValueAtTime(0.001, start + dur);

        osc1.connect(gainNode);
        osc2.connect(gainNode);
        gainNode.connect(compressor);

        osc1.start(start);
        osc2.start(start);
        osc1.stop(start + dur);
        osc2.stop(start + dur);
      });
    } catch (e) {
      console.warn("Audio alert error:", e);
    }
  }

  playWarningChime() {
    if (this.isMuted) return;
    try {
      this._initContext();
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;

      const compressor = this.audioCtx.createDynamicsCompressor();
      compressor.threshold.setValueAtTime(-6, now);
      compressor.connect(this.audioCtx.destination);

      // High-volume dual ping (E5 and A5)
      const notes = [
        { freq: 659.25, start: now, dur: 0.18 },
        { freq: 880.00, start: now + 0.16, dur: 0.32 }
      ];

      notes.forEach(({ freq, start, dur }) => {
        const osc1 = this.audioCtx.createOscillator();
        const osc2 = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();

        osc1.type = 'sawtooth';
        osc1.frequency.setValueAtTime(freq, start);

        osc2.type = 'triangle';
        osc2.frequency.setValueAtTime(freq * 1.5, start);

        const peakGain = 0.85 * this.volume;
        gain.gain.setValueAtTime(0.01, start);
        gain.gain.linearRampToValueAtTime(peakGain, start + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, start + dur);

        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(compressor);

        osc1.start(start);
        osc2.start(start);
        osc1.stop(start + dur);
        osc2.stop(start + dur);
      });
    } catch (e) {
      console.warn("Audio chime error:", e);
    }
  }

  playSuccessChime() {
    if (this.isMuted) return;
    try {
      this._initContext();
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;
      const notes = [
        { freq: 523.25, time: now },
        { freq: 659.25, time: now + 0.10 },
        { freq: 783.99, time: now + 0.20 }
      ];

      notes.forEach(({ freq, time }) => {
        const osc = this.audioCtx.createOscillator();
        const gainNode = this.audioCtx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, time);

        const peakGain = 0.70 * this.volume;
        gainNode.gain.setValueAtTime(0.01, time);
        gainNode.gain.linearRampToValueAtTime(peakGain, time + 0.02);
        gainNode.gain.exponentialRampToValueAtTime(0.001, time + 0.35);

        osc.connect(gainNode);
        gainNode.connect(this.audioCtx.destination);

        osc.start(time);
        osc.stop(time + 0.35);
      });
    } catch (e) {
      console.warn("Audio chime error:", e);
    }
  }
}

export const soundAlert = new SoundAlertManager();
