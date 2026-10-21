// MJ Desktop Cockpit JavaScript Engine v6.0

let ws = null;
let audioCtx = null;
let analyser = null;
let currentStageState = "STANDBY";
let micRecognition = null;
let isMicListening = false;

// Customization states
let currentVisMode = localStorage.getItem("mj_vis_mode") || "ribbon";
let sfxMuted = localStorage.getItem("mj_sfx_muted") === "true";

document.addEventListener("DOMContentLoaded", () => {
  initThemes();
  initHudClock();
  initSfx();
  initVisualizer();
  initScratchpad();
  initWebSocket();
  initTelemetry();
  initCommandHandlers();
  initSpeechRecognition();
  initPhonePairing();
  loadDeskVoicemails();

  // Play sci-fi startup chime on initial user interaction or launch
  window.addEventListener("pointerdown", () => {
    ensureAudioCtx();
  }, { once: true });
});

/* ==========================================================================
   1. THEME ENGINE (Black & White Stealth Luxury + 4 Matching Palettes)
   ========================================================================== */
function initThemes() {
  const savedTheme = localStorage.getItem("mj_cockpit_theme") || "jarvis";
  applyTheme(savedTheme);

  document.querySelectorAll("[data-theme-pick]").forEach(btn => {
    btn.addEventListener("click", () => {
      const theme = btn.dataset.themePick;
      applyTheme(theme);
      playClickChirp();
    });
  });
}

function applyTheme(themeName) {
  document.documentElement.setAttribute("data-theme", themeName);
  localStorage.setItem("mj_cockpit_theme", themeName);

  document.querySelectorAll("[data-theme-pick]").forEach(btn => {
    if (btn.dataset.themePick === themeName) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
}

/* ==========================================================================
   2. HUD LIVE DIGITAL CLOCK & DATE
   ========================================================================== */
function initHudClock() {
  const timeEl = document.getElementById("hudClockTime");
  const dateEl = document.getElementById("hudClockDate");
  if (!timeEl || !dateEl) return;

  function update() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    const seconds = String(now.getSeconds()).padStart(2, "0");
    timeEl.innerText = `${hours}:${minutes}:${seconds}`;

    const days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
    const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    dateEl.innerText = `${days[now.getDay()]}, ${now.getDate()} ${months[now.getMonth()]}`;
  }

  update();
  setInterval(update, 1000);
}

/* ==========================================================================
   3. PROCEDURAL SCI-FI WEB AUDIO SFX (100% Offline & Instant)
   ========================================================================== */
function ensureAudioCtx() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume();
  }
}

function initSfx() {
  const toggleBtn = document.getElementById("hudSfxToggle");
  const iconEl = document.getElementById("sfxIcon");
  const labelEl = document.getElementById("sfxLabel");

  function updateUI() {
    if (iconEl) iconEl.innerText = sfxMuted ? "🔇" : "🔊";
    if (labelEl) labelEl.innerText = sfxMuted ? "MUTED" : "SFX";
    if (toggleBtn) {
      toggleBtn.style.opacity = sfxMuted ? "0.6" : "1";
    }
  }
  updateUI();

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      sfxMuted = !sfxMuted;
      localStorage.setItem("mj_sfx_muted", sfxMuted ? "true" : "false");
      updateUI();
      if (!sfxMuted) playClickChirp();
    });
  }

  // Attach hover sound to cyber buttons & tiles
  document.querySelectorAll(".btn-cyber, .app-cube, .theme-btn, .vis-mode-btn, .btn-dock-mic, .btn-dock-send").forEach(el => {
    el.addEventListener("mouseenter", () => {
      playHoverTick();
    });
  });
}

function playHoverTick() {
  if (sfxMuted) return;
  try {
    ensureAudioCtx();
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(1400, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1800, audioCtx.currentTime + 0.015);

    gain.gain.setValueAtTime(0.018, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.015);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.016);
  } catch (e) {}
}

function playClickChirp() {
  if (sfxMuted) return;
  try {
    ensureAudioCtx();
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(750, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1600, audioCtx.currentTime + 0.05);

    gain.gain.setValueAtTime(0.045, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.05);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.052);
  } catch (e) {}
}

function playStateSound(state) {
  if (sfxMuted) return;
  try {
    ensureAudioCtx();
    if (!audioCtx) return;
    const freqs = {
      "LISTENING": [440, 880],
      "THINKING": [600, 750],
      "SPEAKING": [520, 650, 780]
    };
    const seq = freqs[state];
    if (!seq) return;

    seq.forEach((freq, idx) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      const startT = audioCtx.currentTime + idx * 0.06;

      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, startT);
      gain.gain.setValueAtTime(0.03, startT);
      gain.gain.exponentialRampToValueAtTime(0.0001, startT + 0.05);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start(startT);
      osc.stop(startT + 0.055);
    });
  } catch (e) {}
}

/* ==========================================================================
   4. MULTI-STYLE AUDIO FREQUENCY VISUALIZER (Ribbon, Reactor, Spectrum)
   ========================================================================== */
function initVisualizer() {
  const canvas = document.getElementById("audioVisualizer");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Mode Switcher Buttons
  document.querySelectorAll("[data-vis]").forEach(btn => {
    if (btn.dataset.vis === currentVisMode) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }

    btn.addEventListener("click", () => {
      currentVisMode = btn.dataset.vis;
      localStorage.setItem("mj_vis_mode", currentVisMode);
      document.querySelectorAll("[data-vis]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      playClickChirp();
    });
  });

  let phase = 0;
  const numBars = 36;
  const peakValues = new Array(numBars).fill(0);

  function renderFrame() {
    requestAnimationFrame(renderFrame);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const width = canvas.width;
    const height = canvas.height;
    const centerY = height / 2;

    const accentColor = getComputedStyle(document.documentElement).getPropertyValue("--cyan").trim() || "#ffffff";
    const subColor = getComputedStyle(document.documentElement).getPropertyValue("--magenta").trim() || "#a1a1aa";

    // MODE 1: HARMONIC SINE RIBBON
    if (currentVisMode === "ribbon") {
      ctx.lineWidth = 2.5;
      const grad = ctx.createLinearGradient(0, 0, width, 0);
      grad.addColorStop(0, "rgba(255, 255, 255, 0.08)");
      grad.addColorStop(0.5, accentColor);
      grad.addColorStop(1, subColor);

      ctx.strokeStyle = grad;
      ctx.beginPath();

      const freq = currentStageState === "SPEAKING" ? 0.035 : (currentStageState === "LISTENING" ? 0.045 : 0.02);
      const amp = currentStageState === "SPEAKING" ? 22 : (currentStageState === "LISTENING" ? 18 : 9);

      for (let x = 0; x < width; x++) {
        const envelope = Math.sin((x / width) * Math.PI);
        const y = centerY + Math.sin(x * freq + phase) * amp * envelope;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Secondary Harmonic Line
      ctx.lineWidth = 1.2;
      ctx.strokeStyle = subColor;
      ctx.beginPath();
      for (let x = 0; x < width; x++) {
        const envelope = Math.sin((x / width) * Math.PI);
        const y = centerY - Math.sin(x * freq * 1.3 - phase * 0.9) * (amp * 0.65) * envelope;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      phase += currentStageState === "SPEAKING" ? 0.12 : (currentStageState === "LISTENING" ? 0.09 : 0.04);
    }

    // MODE 2: ARC REACTOR CORE VISUALIZER
    else if (currentVisMode === "reactor") {
      const centerX = width / 2;
      const numRays = 32;
      const baseRadius = 18;
      const maxSpike = currentStageState === "SPEAKING" ? 28 : (currentStageState === "LISTENING" ? 22 : 12);

      // Rotating dashed ring
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(phase * 0.3);

      ctx.strokeStyle = accentColor;
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.arc(0, 0, baseRadius + 4, 0, Math.PI * 2);
      ctx.stroke();

      // Energy spikes radiating outward
      ctx.setLineDash([]);
      for (let i = 0; i < numRays; i++) {
        const angle = (i / numRays) * Math.PI * 2;
        const spikeLen = Math.abs(Math.sin(i * 1.5 + phase * 2)) * maxSpike + 4;
        const r1 = baseRadius + 6;
        const r2 = r1 + spikeLen;

        const x1 = Math.cos(angle) * r1;
        const y1 = Math.sin(angle) * r1;
        const x2 = Math.cos(angle) * r2;
        const y2 = Math.sin(angle) * r2;

        ctx.strokeStyle = i % 2 === 0 ? accentColor : subColor;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }

      ctx.restore();
      phase += currentStageState === "SPEAKING" ? 0.09 : 0.04;
    }

    // MODE 3: FREQUENCY SPECTRUM BARS
    else if (currentVisMode === "spectrum") {
      const barSpacing = width / numBars;
      const barWidth = barSpacing * 0.65;

      for (let i = 0; i < numBars; i++) {
        const factor = Math.sin((i / numBars) * Math.PI);
        let targetHeight = 0;

        if (currentStageState === "SPEAKING") {
          targetHeight = (Math.sin(i * 0.4 + phase * 1.8) * 0.5 + 0.5) * (height * 0.8) * factor + 5;
        } else if (currentStageState === "LISTENING") {
          targetHeight = (Math.cos(i * 0.6 - phase * 2.2) * 0.5 + 0.5) * (height * 0.75) * factor + 4;
        } else {
          targetHeight = (Math.sin(i * 0.3 + phase * 0.8) * 0.5 + 0.5) * (height * 0.35) * factor + 3;
        }

        // Peak decay smoothing
        if (targetHeight > peakValues[i]) {
          peakValues[i] = targetHeight;
        } else {
          peakValues[i] = Math.max(0, peakValues[i] - 1.2);
        }

        const x = i * barSpacing + (barSpacing - barWidth) / 2;
        const barH = targetHeight;
        const y = height - barH;

        // Gradient bar
        const grad = ctx.createLinearGradient(0, height, 0, y);
        grad.addColorStop(0, "rgba(255, 255, 255, 0.15)");
        grad.addColorStop(1, accentColor);

        ctx.fillStyle = grad;
        ctx.fillRect(x, y, barWidth, barH);

        // Peak cap
        ctx.fillStyle = subColor;
        ctx.fillRect(x, height - peakValues[i] - 2, barWidth, 2);
      }

      phase += currentStageState === "SPEAKING" ? 0.14 : 0.06;
    }
  }

  renderFrame();
}

/* ==========================================================================
   5. INTERACTIVE ASSISTANT STATE CONTROLLER
   ========================================================================== */
function setAssistantState(state, text) {
  currentStageState = state;
  const pill = document.getElementById("stageStatePill");
  playStateSound(state);

  const states = {
    "STANDBY": { color: "var(--cyan)", label: "● STANDBY / READY" },
    "LISTENING": { color: "#ef4444", label: "🎙️ LISTENING..." },
    "THINKING": { color: "var(--purple)", label: "⚡ THINKING / REASONING..." },
    "SPEAKING": { color: "var(--cyan)", label: "🌸 MJ SPEAKING..." }
  };

  const current = states[state] || states["STANDBY"];
  if (pill) {
    pill.style.color = current.color;
    pill.style.borderColor = current.color;
    pill.innerHTML = `<span>${text || current.label}</span>`;
  }
}

/* ==========================================================================
   6. QUICK SCRATCHPAD / STICKY NOTES ENGINE
   ========================================================================== */
function initScratchpad() {
  const pad = document.getElementById("deskScratchpad");
  const status = document.getElementById("scratchpadStatus");
  const clearBtn = document.getElementById("btnClearScratchpad");
  if (!pad) return;

  pad.value = localStorage.getItem("mj_scratchpad") || "";

  pad.addEventListener("input", () => {
    localStorage.setItem("mj_scratchpad", pad.value);
    if (status) {
      status.innerText = "✓ Saved";
      status.style.color = "var(--cyan)";
    }
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (confirm("Notes clear karni hain Noaman?")) {
        pad.value = "";
        localStorage.removeItem("mj_scratchpad");
        playClickChirp();
        if (status) status.innerText = "Cleared";
      }
    });
  }
}

/* ==========================================================================
   7. WEBSOCKET REAL-TIME BRIDGE
   ========================================================================== */
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    const dot = document.getElementById("hudStatusDot");
    const txt = document.getElementById("hudStatusText");
    if (dot) dot.style.background = "var(--cyan)";
    if (txt) txt.innerText = "SYSTEM ONLINE";
    console.log("[WS] Desktop Cockpit connected to MJ Hub");
  };

  ws.onclose = () => {
    const dot = document.getElementById("hudStatusDot");
    const txt = document.getElementById("hudStatusText");
    if (dot) dot.style.background = "#ef4444";
    if (txt) txt.innerText = "RECONNECTING...";
    setTimeout(initWebSocket, 3000);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWsEvent(data);
    } catch (e) {
      console.error("[WS] Parse error:", e);
    }
  };
}

function handleWsEvent(data) {
  if (data.type === "new_voicemail") {
    appendAssistantBubble(`📞 Nayi Voicemail: ${data.voicemail.caller_name} - "${data.voicemail.summary}"`);
    loadDeskVoicemails();
  } else if (data.type === "command_result") {
    appendAssistantBubble(data.response);
    setAssistantState("SPEAKING");
    setTimeout(() => setAssistantState("STANDBY"), 3500);
  }
}

/* ==========================================================================
   8. COMMAND DISPATCHER & DECK MESSAGES
   ========================================================================== */
function initCommandHandlers() {
  const input = document.getElementById("deskCmdInput");
  const sendBtn = document.getElementById("btnDeskSend");

  const send = () => {
    const text = input.value.trim();
    if (!text) return;
    playClickChirp();
    dispatchCommand(text);
    input.value = "";
  };

  if (sendBtn) sendBtn.addEventListener("click", send);
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") send();
    });
  }

  // System Action Buttons
  document.querySelectorAll("[data-action]").forEach(el => {
    el.addEventListener("click", () => {
      playClickChirp();
      dispatchCommand(el.dataset.action);
    });
  });

  // App Launcher Buttons
  document.querySelectorAll("[data-app]").forEach(el => {
    el.addEventListener("click", () => {
      playClickChirp();
      dispatchCommand(`open ${el.dataset.app}`);
    });
  });

  // Center Sphere Listening Toggle
  const core = document.getElementById("coreSphere");
  if (core) {
    core.addEventListener("click", () => {
      playClickChirp();
      toggleMicListening();
    });
  }

  // Clear Voicemails
  const clearVm = document.getElementById("btnDeskClearVm");
  if (clearVm) {
    clearVm.addEventListener("click", async () => {
      playClickChirp();
      await fetch("/api/call/voicemails/read", { method: "POST" });
      loadDeskVoicemails();
    });
  }
}

async function dispatchCommand(query) {
  appendUserBubble(query);
  setAssistantState("THINKING");

  try {
    const res = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, source: "desktop_cockpit" })
    });
    const data = await res.json();
    if (data.nlp) {
      updateNlpTelemetry(data.nlp);
    }
    appendAssistantBubble(data.response || "Command executed.", data.nlp);
    setAssistantState("SPEAKING");
    setTimeout(() => setAssistantState("STANDBY"), 3000);
  } catch (e) {
    appendAssistantBubble(`Error: ${e.message}`);
    setAssistantState("STANDBY");
  }
}

function updateNlpTelemetry(nlp) {
  const elParser = document.getElementById("nlpActiveParser");
  const elIntent = document.getElementById("nlpLastIntent");
  const elSent = document.getElementById("nlpSentiment");

  if (elParser) elParser.innerText = `${nlp.source} (${nlp.latency_ms || 0}ms)`;
  if (elIntent) elIntent.innerText = `${nlp.intent} (${Math.round(nlp.confidence * 100)}%)`;
  if (elSent) elSent.innerText = `${nlp.sentiment.toUpperCase()}`;
}

function appendUserBubble(text) {
  const deck = document.getElementById("conversationDeck");
  if (!deck) return;

  const bubble = document.createElement("div");
  bubble.className = "speech-bubble user";
  bubble.innerHTML = `
    <div class="speech-meta">
      <span>👤 Commander Noaman</span>
      <span>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
    </div>
    <p>${escapeHtml(text)}</p>
  `;
  deck.appendChild(bubble);
  deck.scrollTop = deck.scrollHeight;
}

function appendAssistantBubble(text, nlp = null) {
  const deck = document.getElementById("conversationDeck");
  if (!deck) return;

  const nlpBadge = nlp ? `
    <div class="speech-nlp-meta">
      <span>⚡ NLU: <strong class="speech-nlp-badge">${escapeHtml(nlp.intent)}</strong> (${Math.round(nlp.confidence * 100)}% conf • ${nlp.latency_ms}ms) • Tone: ${escapeHtml(nlp.sentiment)}</span>
    </div>
  ` : '';

  const bubble = document.createElement("div");
  bubble.className = "speech-bubble assistant";
  bubble.innerHTML = `
    <div class="speech-meta">
      <span>🌸 MJ Personal Assistant</span>
      <span>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
    </div>
    <p>${escapeHtml(text)}</p>
    ${nlpBadge}
  `;
  deck.appendChild(bubble);
  deck.scrollTop = deck.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

/* ==========================================================================
   9. SPEECH RECOGNITION & PUSH-TO-TALK MIC
   ========================================================================== */
function initSpeechRecognition() {
  const micBtn = document.getElementById("btnDeskMic");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    if (micBtn) micBtn.title = "Browser SpeechRecognition not supported";
    return;
  }

  micRecognition = new SpeechRecognition();
  micRecognition.lang = "hi-IN";
  micRecognition.continuous = false;
  micRecognition.interimResults = false;

  micRecognition.onstart = () => {
    isMicListening = true;
    if (micBtn) micBtn.classList.add("listening");
    setAssistantState("LISTENING", "🎙️ SUN RAHI HU... BOLIYE");
  };

  micRecognition.onend = () => {
    isMicListening = false;
    if (micBtn) micBtn.classList.remove("listening");
    if (currentStageState === "LISTENING") {
      setAssistantState("STANDBY");
    }
  };

  micRecognition.onresult = (event) => {
    const spoken = event.results[0][0].transcript;
    document.getElementById("deskCmdInput").value = spoken;
    dispatchCommand(spoken);
  };

  if (micBtn) {
    micBtn.addEventListener("click", () => {
      playClickChirp();
      toggleMicListening();
    });
  }
}

function toggleMicListening() {
  if (!micRecognition) return;
  if (isMicListening) {
    micRecognition.stop();
  } else {
    try {
      micRecognition.start();
    } catch (e) {
      micRecognition.stop();
    }
  }
}

/* ==========================================================================
   10. TELEMETRY MONITORING
   ========================================================================== */
async function initTelemetry() {
  async function poll() {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();

      if (data.laptop) {
        const elCpu = document.getElementById("hudCpu");
        const elRam = document.getElementById("hudRam");
        const elBatt = document.getElementById("hudBatt");

        if (elCpu) elCpu.innerText = data.laptop.cpu + "%";
        if (elRam) elRam.innerText = data.laptop.ram + "%";
        if (elBatt) elBatt.innerText = data.laptop.battery ? (data.laptop.battery.percent + "%") : "N/A";
      }

      if (data.phone) {
        const phoneDev = document.getElementById("phoneDeviceName");
        const phoneBatt = document.getElementById("phoneBattVal");
        if (phoneDev) phoneDev.innerText = data.phone.connected ? (data.phone.device_name || "Connected") : "Standby";
        if (phoneBatt) phoneBatt.innerText = data.phone.battery_percent !== null ? (data.phone.battery_percent + "%") : "Standby";
      }
    } catch (e) {}
  }

  poll();
  setInterval(poll, 2500);
}

/* ==========================================================================
   11. VOICEMAILS FEED
   ========================================================================== */
async function loadDeskVoicemails() {
  const listEl = document.getElementById("deskVoicemailsList");
  if (!listEl) return;

  try {
    const res = await fetch("/api/call/voicemails");
    const data = await res.json();
    const vms = data.voicemails || [];

    if (vms.length === 0) {
      listEl.innerHTML = '<p style="font-size:12px; color:var(--text-muted);">No new voicemails. All clear!</p>';
      return;
    }

    listEl.innerHTML = vms.slice(0, 5).map(vm => {
      const tagClass = vm.urgency === "URGENT" ? "urgent" : "normal";
      return `
        <div class="vm-item">
          <div class="vm-item-header">
            <span class="vm-caller">👤 ${escapeHtml(vm.caller_name)}</span>
            <span class="vm-tag ${tagClass}">${vm.urgency}</span>
          </div>
          <p class="vm-summary">"${escapeHtml(vm.summary)}"</p>
          <span class="vm-time">${escapeHtml(vm.timestamp)}</span>
          ${vm.audio_url ? `<audio controls src="${vm.audio_url}" style="width:100%; height:24px; margin-top:4px;"></audio>` : ''}
        </div>
      `;
    }).join("");
  } catch (e) {
    listEl.innerHTML = `<p style="font-size:12px; color:var(--text-muted);">Voicemails unavailable.</p>`;
  }
}

/* ==========================================================================
   12. PHONE PAIRING & DYNAMIC QR ENGINE
   ========================================================================== */
async function initPhonePairing() {
  const btn = document.getElementById("btnShowPhoneQr");
  const box = document.getElementById("phoneQrBox");
  const qrImg = document.getElementById("phoneQrImg");
  const link = document.getElementById("phoneUrlLink");
  if (!btn || !box) return;

  btn.addEventListener("click", async () => {
    playClickChirp();
    if (box.style.display === "none" || !box.style.display) {
      box.style.display = "flex";
      try {
        const res = await fetch("/api/network/info");
        const data = await res.json();
        if (data.phone_url) {
          if (link) {
            link.innerText = data.phone_url;
            link.href = data.phone_url;
          }
          if (qrImg) qrImg.src = data.qr_url;
        }
      } catch (e) {
        if (link) link.innerText = window.location.origin;
      }
    } else {
      box.style.display = "none";
    }
  });
}
