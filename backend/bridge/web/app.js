// MJ Mobile Controller PWA App Logic

let ws = null;
let audioCtx = null;
let sirenOsc = null;
let sirenInterval = null;
let isSirenActive = false;
let screenStreamInterval = null;
let cameraStream = null;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  initWebSocket();
  initBatteryMonitoring();
  setupRemoteControls();
  setupCamera();
  setupSpeechRecognition();
  setupClipboard();
});

// 1. WebSocket Bridge
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    document.getElementById("statusDot").classList.add("online");
    document.getElementById("statusText").innerText = "Online";
    console.log("[WS] Connected to MJ Hub");
    sendBatteryTelemetry();
  };

  ws.onclose = () => {
    document.getElementById("statusDot").classList.remove("online");
    document.getElementById("statusText").innerText = "Offline";
    console.log("[WS] Disconnected, reconnecting in 3s...");
    setTimeout(initWebSocket, 3000);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleServerEvent(data);
    } catch (e) {
      console.error("[WS] Parse error:", e);
    }
  };
}

function handleServerEvent(data) {
  console.log("[WS Event]", data);

  if (data.type === "ring_alert") {
    if (data.action === "start_siren") {
      startPhoneSiren();
    } else if (data.action === "stop_siren") {
      stopPhoneSiren();
    }
  } else if (data.type === "clipboard_sync") {
    const clipInput = document.getElementById("clipboardInput");
    if (clipInput) clipInput.value = data.text;
    showAssistantResponse("📋 Laptop clipboard updated");
  } else if (data.type === "new_voicemail") {
    showAssistantResponse(`📞 New Voicemail from ${data.voicemail.caller_name}: "${data.voicemail.summary}"`);
    loadVoicemails();
  } else if (data.type === "dial_call") {
    showAssistantResponse(`📞 Calling ${data.name || data.number}...`);
    window.location.href = `tel:${data.number}`;
  } else if (data.type === "telemetry_update") {
    updateLaptopTelemetry(data);
  }
}

// 2. Loud Siren / Find My Phone Alarm (Web Audio API)
function startPhoneSiren() {
  if (isSirenActive) return;
  isSirenActive = true;
  document.getElementById("sirenOverlay").style.display = "flex";

  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContext();
    
    let high = false;
    sirenInterval = setInterval(() => {
      if (!isSirenActive || !audioCtx) return;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(high ? 1760 : 880, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.7, audioCtx.currentTime);
      
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      
      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
      high = !high;
    }, 400);

    // Vibrate device if supported
    if ("vibrate" in navigator) {
      navigator.vibrate([400, 200, 400, 200, 400]);
    }
  } catch (e) {
    console.warn("AudioContext error:", e);
  }
}

function stopPhoneSiren() {
  isSirenActive = false;
  document.getElementById("sirenOverlay").style.display = "none";
  if (sirenInterval) clearInterval(sirenInterval);
  if (audioCtx) {
    try { audioCtx.close(); } catch (e) {}
    audioCtx = null;
  }
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "ring_stopped" }));
  }
}

document.getElementById("stopSirenBtn").addEventListener("click", stopPhoneSiren);

// 3. Battery Telemetry (Web Battery API)
async function initBatteryMonitoring() {
  if ("getBattery" in navigator) {
    try {
      const battery = await navigator.getBattery();
      const update = () => {
        sendBatteryTelemetry(Math.round(battery.level * 100), battery.charging);
      };
      update();
      battery.addEventListener("levelchange", update);
      battery.addEventListener("chargingchange", update);
    } catch (e) {
      console.log("Battery API not permitted:", e);
    }
  }
}

function sendBatteryTelemetry(level, isCharging) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: "phone_status",
      battery: level || null,
      charging: !!isCharging,
      device: navigator.userAgent.includes("Android") ? "Android Phone" : "Mobile Phone"
    }));
  }
}

// 4. Tab Navigation
function setupTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add("active");

      // Handle screen stream polling toggle
      if (btn.dataset.tab === "tab-screen") {
        startScreenStream();
      } else {
        stopScreenStream();
      }

      // Handle camera preview toggle
      if (btn.dataset.tab === "tab-camera") {
        startCameraStream();
      } else {
        stopCameraStream();
      }
    });
  });
}

// 5. Remote Controls & Commands
function setupRemoteControls() {
  // Volume controls
  document.querySelectorAll("[data-action]").forEach(el => {
    el.addEventListener("click", () => {
      const action = el.dataset.action;
      executeCommand(action);
    });
  });

  // App Launchers
  document.querySelectorAll("[data-app]").forEach(el => {
    el.addEventListener("click", () => {
      const app = el.dataset.app;
      executeCommand(`open ${app}`);
    });
  });

  // Chat input
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");

  const send = () => {
    const text = chatInput.value.trim();
    if (!text) return;
    executeCommand(text);
    chatInput.value = "";
  };

  sendBtn.addEventListener("click", send);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") send();
  });
}

async function executeCommand(query) {
  showAssistantResponse(`⏳ Executing: "${query}"...`);
  try {
    const res = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, source: "phone" })
    });
    const data = await res.json();
    showAssistantResponse(data.response || "Command executed.");
  } catch (e) {
    showAssistantResponse(`⚠️ Error: ${e.message}`);
  }
}

function showAssistantResponse(text) {
  const el = document.getElementById("responseBar");
  if (el) el.innerText = text;
}

// 6. Live Screen Stream
function startScreenStream() {
  const img = document.getElementById("screenImage");
  if (!img) return;
  stopScreenStream();

  const update = () => {
    img.src = `/api/screen/snapshot?t=${Date.now()}`;
  };
  update();
  screenStreamInterval = setInterval(update, 1200);
}

function stopScreenStream() {
  if (screenStreamInterval) {
    clearInterval(screenStreamInterval);
    screenStreamInterval = null;
  }
}

// 7. AI Camera Eye
async function startCameraStream() {
  const video = document.getElementById("cameraVideo");
  if (!video || cameraStream) return;

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
      audio: false
    });
    video.srcObject = cameraStream;
  } catch (e) {
    console.error("Camera access error:", e);
    document.getElementById("visionResult").innerText = "Camera access denied or unavailable: " + e.message;
  }
}

function stopCameraStream() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }
}

function setupCamera() {
  const analyzeBtn = document.getElementById("analyzeCameraBtn");
  if (!analyzeBtn) return;

  analyzeBtn.addEventListener("click", async () => {
    const video = document.getElementById("cameraVideo");
    const resultEl = document.getElementById("visionResult");
    if (!video || !cameraStream) {
      resultEl.innerText = "Camera active nahi hai.";
      return;
    }

    resultEl.innerText = "🔍 MJ analyzing what's in front of your camera...";

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const b64 = canvas.toDataURL("image/jpeg", 0.7);

    try {
      const res = await fetch("/api/vision/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_b64: b64, prompt: "Is photo me kya dikh raha hai? Hindi/Hinglish me short me batao." })
      });
      const data = await res.json();
      resultEl.innerText = data.analysis || "No response received.";
    } catch (e) {
      resultEl.innerText = "Vision analysis error: " + e.message;
    }
  });
}

// 8. Speech Recognition (Push-to-Talk)
function setupSpeechRecognition() {
  const micBtn = document.getElementById("micBtn");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    micBtn.title = "Speech recognition not supported on this browser";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "hi-IN";
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    micBtn.classList.add("recording");
    showAssistantResponse("🎙️ Listening... Boliye");
  };

  recognition.onend = () => {
    micBtn.classList.remove("recording");
  };

  recognition.onresult = (event) => {
    const spoken = event.results[0][0].transcript;
    document.getElementById("chatInput").value = spoken;
    executeCommand(spoken);
  };

  recognition.onerror = (e) => {
    micBtn.classList.remove("recording");
    showAssistantResponse("Mic error: " + e.error);
  };

  micBtn.addEventListener("click", () => {
    try {
      recognition.start();
    } catch (e) {
      recognition.stop();
    }
  });
}

// 9. Clipboard Sync
function setupClipboard() {
  const sendClipBtn = document.getElementById("sendClipBtn");
  const clipInput = document.getElementById("clipboardInput");

  if (!sendClipBtn || !clipInput) return;

  sendClipBtn.addEventListener("click", async () => {
    const text = clipInput.value.trim();
    if (!text) return;
    try {
      const res = await fetch("/api/clipboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
      });
      const data = await res.json();
      showAssistantResponse(data.message || "Clipboard sent to laptop");
    } catch (e) {
      showAssistantResponse("Clipboard error: " + e.message);
    }
  });
}

// 10. Telemetry updates
async function fetchTelemetry() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    if (data.laptop) {
      const elCpu = document.getElementById("valCpu");
      const elRam = document.getElementById("valRam");
      const elBatt = document.getElementById("valBatt");
      if (elCpu) elCpu.innerText = data.laptop.cpu + "%";
      if (elRam) elRam.innerText = data.laptop.ram + "%";
      if (elBatt) elBatt.innerText = data.laptop.battery ? (data.laptop.battery.percent + "%") : "N/A";
    }
  } catch (e) {}
}

setInterval(fetchTelemetry, 3000);
fetchTelemetry();

// 11. Voicemail Management
async function loadVoicemails() {
  const listEl = document.getElementById("voicemailsList");
  if (!listEl) return;
  try {
    const res = await fetch("/api/call/voicemails");
    const data = await res.json();
    const vms = data.voicemails || [];
    if (vms.length === 0) {
      listEl.innerHTML = '<p style="font-size:12px; color:var(--text-muted);">Koi nayi voicemail nahi hai. All clear!</p>';
      return;
    }
    listEl.innerHTML = vms.map(vm => {
      const urgentColor = vm.urgency === "URGENT" ? "var(--pink)" : "var(--cyan)";
      return `
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:12px; display:flex; flex-direction:column; gap:6px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:14px; color:#fff;">👤 ${vm.caller_name}</strong>
            <span style="font-size:10px; font-weight:700; color:${urgentColor}; border:1px solid ${urgentColor}; padding:2px 6px; border-radius:6px;">${vm.urgency}</span>
          </div>
          <span style="font-size:11px; color:var(--text-muted);">${vm.timestamp} | ${vm.phone_number}</span>
          <p style="font-size:13px; color:var(--text-main); margin-top:2px;">"${vm.summary}"</p>
          <p style="font-size:11px; color:var(--text-muted); font-style:italic;">Transcript: "${vm.transcript}"</p>
          ${vm.audio_url ? `<audio controls src="${vm.audio_url}" style="width:100%; height:32px; margin-top:6px;"></audio>` : ''}
        </div>
      `;
    }).join("");
  } catch (e) {
    listEl.innerHTML = `<p style="font-size:12px; color:var(--pink);">Error loading: ${e.message}</p>`;
  }
}

// Voicemail simulation & clear buttons
document.addEventListener("DOMContentLoaded", () => {
  loadVoicemails();

  const simBtn = document.getElementById("btnSimulateCall");
  if (simBtn) {
    simBtn.addEventListener("click", async () => {
      showAssistantResponse("⏳ Simulating incoming call & voicemail...");
      try {
        const res = await fetch("/api/call/voicemail", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            caller_name: "Rahul",
            phone_number: "+919876543210",
            transcript: "Bhai jaldi college aja, practical exam shuru hone wali hai!"
          })
        });
        const data = await res.json();
        showAssistantResponse(`✅ Voicemail processed from ${data.voicemail.caller_name}`);
        loadVoicemails();
      } catch (e) {
        showAssistantResponse("Error: " + e.message);
      }
    });
  }

  const clearBtn = document.getElementById("btnClearVmBtn");
  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      await fetch("/api/call/voicemails/read", { method: "POST" });
      loadVoicemails();
      showAssistantResponse("Voicemails marked as read.");
    });
  }
});
