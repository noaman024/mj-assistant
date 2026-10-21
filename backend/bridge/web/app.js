// MJ Assistant Holographic Cockpit - High-Performance Controller
// Connects Web UI to Laptop Bridge Server (Wi-Fi) and Native AndroidBridge

let activeHost = "10.35.126.235:8000";
let isLaptopOnline = false;
let screenStreamInterval = null;
let currentTab = "tab-remote";
let cameraStream = null;
let isTorchActive = false;

// 1. Initialization
document.addEventListener("DOMContentLoaded", () => {
  // Load saved IP
  if (window.AndroidBridge && typeof window.AndroidBridge.getLaptopIp === "function") {
    activeHost = window.AndroidBridge.getLaptopIp();
  } else {
    activeHost = localStorage.getItem("laptop_ip") || "10.35.126.235:8000";
  }
  document.getElementById("laptopIpInput").value = activeHost;

  setupTabs();
  setupControls();
  setupSettingsModal();
  setupScreenMirror();
  setupCamera();
  setupVoice();
  setupCallsAndWhatsApp();
  initMobileVisualizer();

  // Initial connection ping
  checkConnection();

  // Poll connection & telemetry every 3 seconds
  setInterval(checkConnection, 3000);
});

// 2. Tab Navigation & Dual Mode Switching
function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  const btnModePhone = document.getElementById("btnModePhone");
  const btnModePc = document.getElementById("btnModePc");

  function switchTab(targetId) {
    tabs.forEach((t) => {
      if (t.getAttribute("data-tab") === targetId) t.classList.add("active");
      else t.classList.remove("active");
    });

    currentTab = targetId;
    document.querySelectorAll(".tab-pane").forEach((pane) => {
      pane.classList.remove("active");
    });
    const targetPane = document.getElementById(targetId);
    if (targetPane) targetPane.classList.add("active");

    // Dual Mode pill sync
    if (targetId === "tab-pc") {
      if (btnModePc) btnModePc.classList.add("active");
      if (btnModePhone) btnModePhone.classList.remove("active");
      document.querySelectorAll(".pc-only").forEach(el => el.style.display = "flex");
    } else {
      if (btnModePhone) btnModePhone.classList.add("active");
      if (btnModePc) btnModePc.classList.remove("active");
      document.querySelectorAll(".pc-only").forEach(el => el.style.display = "none");
    }

    // Camera & Screen Streaming
    if (targetId === "tab-pc") {
      startScreenStream();
    } else {
      stopScreenStream();
    }

    if (targetId === "tab-camera") {
      initCameraStream();
    } else {
      stopCameraStream();
    }
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-tab");
      switchTab(targetId);
    });
  });

  // Dual Mode Pill buttons in Header
  if (btnModePhone) {
    btnModePhone.addEventListener("click", () => switchTab("tab-phone"));
  }
  if (btnModePc) {
    btnModePc.addEventListener("click", () => switchTab("tab-pc"));
  }
}

// 3. Connection & Telemetry
async function checkConnection() {
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");

  // Read native phone battery if available
  if (window.AndroidBridge && typeof window.AndroidBridge.getBatteryLevel === "function") {
    try {
      const pBatt = window.AndroidBridge.getBatteryLevel();
      if (pBatt > 0) {
        document.getElementById("valPhoneBatt").innerText = `${pBatt}%`;
      }
    } catch (_) {}
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1800);

    const res = await fetch(`http://${activeHost}/api/status`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      isLaptopOnline = true;
      statusDot.className = "status-dot online";
      statusText.innerText = "Online";
      const lapSync = document.getElementById("valLaptopStatus");
      if (lapSync) lapSync.innerText = "Online";

      // Update telemetry
      if (data.cpu !== undefined) document.getElementById("valCpu").innerText = `${data.cpu}%`;
      if (data.ram !== undefined) document.getElementById("valRam").innerText = `${data.ram}%`;
      if (data.battery !== undefined) document.getElementById("valBatt").innerText = `${data.battery}%`;
      return true;
    }
  } catch (e) {
    // Laptop offline or unreachable
  }

  isLaptopOnline = false;
  statusDot.className = "status-dot standalone";
  statusText.innerText = "Phone Mode";
  const lapSync = document.getElementById("valLaptopStatus");
  if (lapSync) lapSync.innerText = "Offline";
  document.getElementById("valCpu").innerText = "--%";
  document.getElementById("valRam").innerText = "--%";
  document.getElementById("valBatt").innerText = "--%";
  return false;
}

// 4. Command Dispatching
async function dispatchCommand(query) {
  if (!query || !query.trim()) return;
  const cleanCmd = query.trim();

  showAssistantResponse(`Soch rahi hu...`);
  const label = document.getElementById("hudVoiceLabel");
  if (label) label.innerText = "EXECUTING...";

  // Haptic feedback
  if (window.AndroidBridge && typeof window.AndroidBridge.vibrate === "function") {
    window.AndroidBridge.vibrate(30);
  }

  if (isLaptopOnline) {
    try {
      const res = await fetch(`http://${activeHost}/api/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: cleanCmd, source: "phone_cockpit" })
      });
      const data = await res.json();
      const reply = data.response || "Command executed on Laptop.";
      showAssistantResponse(reply);
      speakResponse(reply);
      if (label) label.innerText = "JARVIS CORE ONLINE";
      return;
    } catch (e) {
      console.warn("Laptop command failed, falling back to local bridge:", e);
    }
  }

  // Standalone Phone Mode fallback
  if (window.AndroidBridge && typeof window.AndroidBridge.dispatchLocalCommand === "function") {
    const localReply = window.AndroidBridge.dispatchLocalCommand(cleanCmd);
    showAssistantResponse(localReply);
    speakResponse(localReply);
  } else {
    const fallback = `Laptop offline hai Noaman. Main phone standalone mode me hu.`;
    showAssistantResponse(fallback);
    speakResponse(fallback);
  }
  if (label) label.innerText = "JARVIS CORE ONLINE";
}

function speakResponse(text) {
  if (!text || !text.trim()) return;
  if (isLaptopOnline) {
    playMobileTTS(text);
  } else if (window.AndroidBridge && typeof window.AndroidBridge.speakNative === "function") {
    setCoreActive(true);
    window.AndroidBridge.speakNative(text);
    setTimeout(() => setCoreActive(false), Math.min(Math.max(text.length * 80, 2000), 7000));
  }
}

function showAssistantResponse(text) {
  const el = document.getElementById("responseText");
  if (el) {
    el.innerText = text;
  }
}

// 5. Controls Setup
function setupControls() {
  // --- Phone Device Superpowers (Tab Phone) ---
  const btnPhoneTorch = document.getElementById("btnPhoneTorchAction");
  if (btnPhoneTorch) {
    btnPhoneTorch.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.toggleTorch === "function") {
        isTorchActive = !isTorchActive;
        window.AndroidBridge.toggleTorch(isTorchActive);
        const lbl = document.getElementById("torchLabel");
        if (lbl) lbl.innerText = isTorchActive ? "Torch On" : "Torch Off";
        if (isTorchActive) btnPhoneTorch.classList.add("torch-on");
        else btnPhoneTorch.classList.remove("torch-on");
        const reply = isTorchActive ? "Flashlight on kar di hai Noaman!" : "Flashlight off kar di hai.";
        showAssistantResponse(reply);
        speakResponse(reply);
      }
    });
  }

  const btnPhoneVolUp = document.getElementById("btnPhoneVolUpAction");
  if (btnPhoneVolUp) {
    btnPhoneVolUp.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.volumeUp === "function") {
        const v = window.AndroidBridge.volumeUp();
        const reply = `Media volume ${v} percent kar diya hai Noaman.`;
        showAssistantResponse(reply);
        speakResponse(reply);
      }
    });
  }

  const btnPhoneVolDown = document.getElementById("btnPhoneVolDownAction");
  if (btnPhoneVolDown) {
    btnPhoneVolDown.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.volumeDown === "function") {
        const v = window.AndroidBridge.volumeDown();
        const reply = `Media volume ${v} percent kar diya hai Noaman.`;
        showAssistantResponse(reply);
        speakResponse(reply);
      }
    });
  }

  const btnPhoneMute = document.getElementById("btnPhoneMuteAction");
  if (btnPhoneMute) {
    btnPhoneMute.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.mute === "function") {
        window.AndroidBridge.mute();
        const reply = "Phone silent mode me set kar diya hai Noaman.";
        showAssistantResponse(reply);
        speakResponse(reply);
      }
    });
  }

  const btnPhoneWifi = document.getElementById("btnPhoneWifiAction");
  if (btnPhoneWifi) {
    btnPhoneWifi.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.openWifiSettings === "function") {
        window.AndroidBridge.openWifiSettings();
        const reply = "Wi-Fi settings open kar di hain Noaman.";
        showAssistantResponse(reply);
        speakResponse(reply);
      }
    });
  }

  const btnPhoneBluetooth = document.getElementById("btnPhoneBluetoothAction");
  if (btnPhoneBluetooth) {
    btnPhoneBluetooth.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.openBluetoothSettings === "function") {
        window.AndroidBridge.openBluetoothSettings();
        const reply = "Bluetooth settings open kar di hain Noaman.";
        showAssistantResponse(reply);
        speakResponse(reply);
      }
    });
  }

  const btnPhoneCamera = document.getElementById("btnPhoneCameraAction");
  if (btnPhoneCamera) {
    btnPhoneCamera.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.launchApp === "function") {
        window.AndroidBridge.launchApp("camera");
        const reply = "Camera open kar rahi hu Noaman!";
        showAssistantResponse(reply);
        speakResponse(reply);
      }
    });
  }

  const btnPhoneBattery = document.getElementById("btnPhoneBatteryAction");
  if (btnPhoneBattery) {
    btnPhoneBattery.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.getBatteryLevel === "function") {
        const b = window.AndroidBridge.getBatteryLevel();
        const reply = `Phone battery level ${b} percent hai Noaman.`;
        showAssistantResponse(reply);
        speakResponse(reply);
      }
    });
  }

  // --- Phone Quick Apps Launcher ---
  document.querySelectorAll(".app-tile[data-phone-app]").forEach((tile) => {
    tile.addEventListener("click", () => {
      const app = tile.getAttribute("data-phone-app");
      if (window.AndroidBridge && typeof window.AndroidBridge.launchApp === "function") {
        window.AndroidBridge.launchApp(app);
        const reply = `${app.toUpperCase()} open kar rahi hu Noaman!`;
        showAssistantResponse(reply);
        speakResponse(reply);
      } else {
        dispatchCommand(`${app} open karo`);
      }
    });
  });

  const btnQuickDialer = document.getElementById("btnQuickDialer");
  if (btnQuickDialer) {
    btnQuickDialer.addEventListener("click", () => {
      const callsTab = document.getElementById("tabCallsBtn");
      if (callsTab) callsTab.click();
    });
  }

  // --- Voice Prompt Suggestions Chips ---
  document.querySelectorAll(".prompt-chip[data-query]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      document.getElementById("chatInput").value = q;
      dispatchCommand(q);
    });
  });

  // --- PC Remote Buttons (Tab PC) ---
  document.querySelectorAll(".btn-ctrl[data-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.getAttribute("data-action");
      dispatchCommand(action);
    });
  });

  // PC App Launcher Tiles
  document.querySelectorAll(".app-tile[data-app]").forEach((tile) => {
    tile.addEventListener("click", () => {
      const app = tile.getAttribute("data-app");
      dispatchCommand(`open ${app}`);
    });
  });

  // Chat Send button
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");

  const submitChat = () => {
    const text = chatInput.value.trim();
    if (text) {
      dispatchCommand(text);
      chatInput.value = "";
    }
  };

  sendBtn.addEventListener("click", submitChat);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") submitChat();
  });

  // Clipboard sync
  const sendClipBtn = document.getElementById("sendClipBtn");
  if (sendClipBtn) {
    sendClipBtn.addEventListener("click", async () => {
      const text = document.getElementById("clipboardInput").value;
      if (!text) return;
      if (isLaptopOnline) {
        try {
          await fetch(`http://${activeHost}/api/clipboard`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
          });
          showAssistantResponse("📋 Laptop clipboard updated!");
        } catch (_) {
          showAssistantResponse("Clipboard sync me error aaya.");
        }
      } else {
        showAssistantResponse("Laptop offline hai Noaman.");
      }
    });
  }

  // Siren Test
  const btnFindMyPhone = document.getElementById("btnFindMyPhone");
  if (btnFindMyPhone) {
    btnFindMyPhone.addEventListener("click", () => {
      document.getElementById("sirenOverlay").style.display = "flex";
      if (window.AndroidBridge && typeof window.AndroidBridge.vibrate === "function") {
        window.AndroidBridge.vibrate(1000);
      }
    });
  }

  const stopSirenBtn = document.getElementById("stopSirenBtn");
  if (stopSirenBtn) {
    stopSirenBtn.addEventListener("click", () => {
      document.getElementById("sirenOverlay").style.display = "none";
    });
  }

  // Flashlight button
  const btnToggleTorch = document.getElementById("btnToggleTorch");
  if (btnToggleTorch) {
    btnToggleTorch.addEventListener("click", () => {
      if (window.AndroidBridge && typeof window.AndroidBridge.toggleTorch === "function") {
        isTorchActive = !isTorchActive;
        window.AndroidBridge.toggleTorch(isTorchActive);
        btnToggleTorch.innerText = isTorchActive ? "🔦 Off" : "🔦 Torch";
        showAssistantResponse(isTorchActive ? "Flashlight on kar di." : "Flashlight off kar di.");
      }
    });
  }
}

// 6. Native Calls & WhatsApp
function setupCallsAndWhatsApp() {
  const btnDirectCall = document.getElementById("btnDirectCall");
  const phoneCallInput = document.getElementById("phoneCallInput");

  btnDirectCall.addEventListener("click", () => {
    const phone = phoneCallInput.value.trim();
    if (!phone) {
      showAssistantResponse("Kripya ek valid phone number enter karein Noaman.");
      return;
    }

    if (window.AndroidBridge && typeof window.AndroidBridge.makeCall === "function") {
      showAssistantResponse(`Direct call connect ho rahi hai: ${phone}...`);
      window.AndroidBridge.makeCall(phone);
    } else {
      window.location.href = `tel:${phone}`;
    }
  });

  const btnSendWhatsApp = document.getElementById("btnSendWhatsApp");
  const whatsappNumberInput = document.getElementById("whatsappNumberInput");
  const whatsappMessageInput = document.getElementById("whatsappMessageInput");

  btnSendWhatsApp.addEventListener("click", () => {
    const phone = whatsappNumberInput.value.trim();
    const msg = whatsappMessageInput.value.trim();

    if (!phone || !msg) {
      showAssistantResponse("Phone number aur message dono zaroori hain Noaman.");
      return;
    }

    if (window.AndroidBridge && typeof window.AndroidBridge.sendWhatsApp === "function") {
      showAssistantResponse(`WhatsApp auto-send dispatch ho raha hai...`);
      window.AndroidBridge.sendWhatsApp(phone, msg);
    } else {
      window.open(`https://api.whatsapp.com/send?phone=${phone}&text=${encodeURIComponent(msg)}`);
    }
  });
}

// 7. Screen Mirroring
function setupScreenMirror() {
  const screenImg = document.getElementById("screenImage");
  const btnRefresh = document.getElementById("btnRefreshScreen");
  const btnSnap = document.getElementById("btnSnapScreen");
  const btnToggle = document.getElementById("btnToggleScreenStream");

  const refreshScreen = () => {
    if (!isLaptopOnline) {
      screenImg.alt = "Laptop offline. Connect on same Wi-Fi to mirror screen.";
      return;
    }
    screenImg.src = `http://${activeHost}/api/screen/snapshot?t=${Date.now()}`;
  };

  btnRefresh.addEventListener("click", refreshScreen);
  btnSnap.addEventListener("click", () => {
    dispatchCommand("screenshot");
    setTimeout(refreshScreen, 1000);
  });

  let streaming = true;
  btnToggle.addEventListener("click", () => {
    streaming = !streaming;
    btnToggle.innerText = streaming ? "⏸️ Pause Stream" : "▶️ Resume Stream";
    if (streaming) startScreenStream();
    else stopScreenStream();
  });
}

function startScreenStream() {
  stopScreenStream();
  if (isLaptopOnline) {
    const screenImg = document.getElementById("screenImage");
    screenImg.src = `http://${activeHost}/api/screen/snapshot?t=${Date.now()}`;
    screenStreamInterval = setInterval(() => {
      if (currentTab === "tab-screen" && isLaptopOnline) {
        screenImg.src = `http://${activeHost}/api/screen/snapshot?t=${Date.now()}`;
      }
    }, 1400);
  }
}

function stopScreenStream() {
  if (screenStreamInterval) {
    clearInterval(screenStreamInterval);
    screenStreamInterval = null;
  }
}

// 8. Phone Camera AI Eye
function setupCamera() {
  const analyzeBtn = document.getElementById("analyzeCameraBtn");
  analyzeBtn.addEventListener("click", () => {
    const video = document.getElementById("cameraVideo");
    const canvas = document.getElementById("cameraCanvas");
    const resultBox = document.getElementById("visionResult");

    if (!video.videoWidth) {
      resultBox.innerText = "Camera feed abhi ready nahi hai.";
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    resultBox.innerText = "🔍 Image analyze ho rahi hai...";
    showAssistantResponse("Image dekh rahi hu Noaman...");

    // Send frame to server if online
    if (isLaptopOnline) {
      const dataUrl = canvas.toDataURL("image/jpeg", 0.7);
      fetch(`http://${activeHost}/api/vision/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: dataUrl })
      })
      .then(res => res.json())
      .then(data => {
        const text = data.analysis || "Analysis complete.";
        resultBox.innerText = text;
        showAssistantResponse(text);
      })
      .catch(() => {
        resultBox.innerText = "Camera frame capture ho gaya hai. Local recognition active hai.";
      });
    } else {
      setTimeout(() => {
        resultBox.innerText = "Image captured! Standalone mode me basic visual sensing ready hai.";
      }, 800);
    }
  });
}

function initCameraStream() {
  const video = document.getElementById("cameraVideo");
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
      .then((stream) => {
        cameraStream = stream;
        video.srcObject = stream;
      })
      .catch((err) => {
        console.warn("Camera access warning:", err);
      });
  }
}

function stopCameraStream() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
}

// 9. Voice, Speech & JARVIS Reactive Visualizer Engine
let currentAmplitude = 0;
let visualizerAnimationId = null;

function playMobileTTS(text) {
  if (!text || !text.trim() || !isLaptopOnline) return;
  const audioUrl = `http://${activeHost}/api/voice/tts?text=${encodeURIComponent(text)}`;

  if (window.AndroidBridge && typeof window.AndroidBridge.playTTSAudio === "function") {
    // Native MediaPlayer with Media Ducking!
    setCoreActive(true);
    window.AndroidBridge.playTTSAudio(audioUrl);
  } else {
    // Web Audio fallback
    try {
      const audio = new Audio(audioUrl);
      setCoreActive(true);
      audio.onended = () => setCoreActive(false);
      audio.onerror = () => setCoreActive(false);
      audio.play().catch(() => setCoreActive(false));
    } catch (_) {
      setCoreActive(false);
    }
  }
}

function setCoreActive(isActive) {
  const core = document.getElementById("btnCoreVoice");
  const label = document.getElementById("hudVoiceLabel");
  if (core) {
    if (isActive) core.classList.add("active-pulse");
    else core.classList.remove("active-pulse");
  }
  if (label) {
    label.innerText = isActive ? "MJ SPEAKING / ACTIVE" : "JARVIS CORE ONLINE";
  }
}

function initMobileVisualizer() {
  const canvas = document.getElementById("mobileVisualizerCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let phase = 0;

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const w = canvas.width;
    const h = canvas.height;
    const midY = h / 2;

    // Draw baseline
    ctx.beginPath();
    ctx.strokeStyle = "rgba(0, 240, 255, 0.15)";
    ctx.lineWidth = 1;
    ctx.moveTo(0, midY);
    ctx.lineTo(w, midY);
    ctx.stroke();

    // Responsive sine waveform based on currentAmplitude (0-100)
    const amp = Math.max(currentAmplitude * 0.35, 3.0);

    // Cyan Harmonic Wave
    ctx.beginPath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = currentAmplitude > 20 ? "#ff7700" : "#00f0ff";
    ctx.shadowBlur = 10;
    ctx.shadowColor = currentAmplitude > 20 ? "#ff7700" : "#00f0ff";

    for (let x = 0; x < w; x++) {
      const normX = x / w;
      const envelope = Math.sin(normX * Math.PI); // Pin edges to zero
      const y = midY + Math.sin(normX * 10 + phase) * amp * envelope;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    phase += 0.08 + (currentAmplitude * 0.002);
    visualizerAnimationId = requestAnimationFrame(draw);
  }

  draw();
}

function setupVoice() {
  const micBtn = document.getElementById("micBtn");
  const btnCoreVoice = document.getElementById("btnCoreVoice");

  const triggerListening = () => {
    if (window.AndroidBridge && typeof window.AndroidBridge.startVoiceRecognition === "function") {
      window.AndroidBridge.startVoiceRecognition();
    } else {
      showAssistantResponse("Native voice recognition available inside the Android APK.");
    }
  };

  micBtn.addEventListener("click", triggerListening);
  if (btnCoreVoice) {
    btnCoreVoice.addEventListener("click", triggerListening);
  }

  // Global callbacks called by MainActivity.kt
  window.onSpeechStatus = function(status) {
    const mic = document.getElementById("micBtn");
    const core = document.getElementById("btnCoreVoice");
    const label = document.getElementById("hudVoiceLabel");

    if (status === "listening") {
      mic.classList.add("listening");
      if (core) core.classList.add("active-pulse");
      if (label) label.innerText = "LISTENING...";
      showAssistantResponse("🎙️ Sun rahi hu Noaman... Boliye");
    } else {
      mic.classList.remove("listening");
      if (core) core.classList.remove("active-pulse");
      if (label) label.innerText = "JARVIS CORE ONLINE";
      currentAmplitude = 0;
    }
  };

  window.onMicAmplitude = function(percent) {
    currentAmplitude = percent;
  };

  window.onNativeVoiceResult = function(spokenText) {
    const mic = document.getElementById("micBtn");
    const core = document.getElementById("btnCoreVoice");
    const label = document.getElementById("hudVoiceLabel");
    mic.classList.remove("listening");
    if (core) core.classList.remove("active-pulse");
    if (label) label.innerText = "JARVIS CORE ONLINE";
    currentAmplitude = 0;

    if (spokenText) {
      document.getElementById("chatInput").value = spokenText;
      dispatchCommand(spokenText);
    }
  };

  window.onAudioStreamFinished = function() {
    setCoreActive(false);
  };

  window.dispatchDeepLinkCommand = function(cmd) {
    if (cmd) {
      document.getElementById("chatInput").value = cmd;
      dispatchCommand(cmd);
    }
  };
}

// 10. Settings Modal
function setupSettingsModal() {
  const modal = document.getElementById("settingsModal");
  const btnSettings = document.getElementById("btnSettings");
  const statusBadge = document.getElementById("statusBadge");
  const btnClose = document.getElementById("btnCloseModal");
  const btnSave = document.getElementById("btnSaveIp");
  const btnPing = document.getElementById("btnTestPing");
  const ipInput = document.getElementById("laptopIpInput");
  const statusBox = document.getElementById("modalStatusBox");

  const openModal = () => {
    ipInput.value = activeHost;
    statusBox.innerText = `Current target: ${activeHost} (${isLaptopOnline ? "Online" : "Offline"})`;
    modal.classList.add("active");
  };

  btnSettings.addEventListener("click", openModal);
  statusBadge.addEventListener("click", openModal);
  btnClose.addEventListener("click", () => modal.classList.remove("active"));

  btnSave.addEventListener("click", () => {
    const val = ipInput.value.trim();
    if (val) {
      activeHost = val;
      localStorage.setItem("laptop_ip", val);
      if (window.AndroidBridge && typeof window.AndroidBridge.setLaptopIp === "function") {
        window.AndroidBridge.setLaptopIp(val);
      }
      statusBox.innerText = `Saved! Testing connection to ${val}...`;
      checkConnection().then((online) => {
        statusBox.innerText = online ? `🟢 Connected to ${val} successfully!` : `⚠️ Could not reach ${val}. Check Wi-Fi & laptop server.`;
      });
    }
  });

  btnPing.addEventListener("click", async () => {
    const val = ipInput.value.trim() || activeHost;
    statusBox.innerText = `Pinging ${val}...`;
    const start = Date.now();
    try {
      const res = await fetch(`http://${val}/api/status`);
      const latency = Date.now() - start;
      if (res.ok) {
        statusBox.innerText = `🟢 Ping 200 OK (${latency}ms). Connected!`;
      } else {
        statusBox.innerText = `⚠️ HTTP ${res.status} returned from ${val}.`;
      }
    } catch (e) {
      statusBox.innerText = `❌ Unreachable (${Date.now() - start}ms). Ensure Laptop server is running on port 8000.`;
    }
  });

  const btnReload = document.getElementById("btnSyncReload");
  if (btnReload) {
    btnReload.addEventListener("click", () => {
      statusBox.innerText = "🔄 Reloading interface...";
      if (window.AndroidBridge && typeof window.AndroidBridge.reloadInterface === "function") {
        window.AndroidBridge.reloadInterface();
      } else {
        window.location.reload();
      }
    });
  }

  const btnLive = document.getElementById("btnLiveServer");
  if (btnLive) {
    btnLive.addEventListener("click", () => {
      statusBox.innerText = `🌐 Connecting to live server at http://${activeHost}/...`;
      if (window.AndroidBridge && typeof window.AndroidBridge.loadLiveServer === "function") {
        window.AndroidBridge.loadLiveServer();
      } else {
        window.location.href = `http://${activeHost}/`;
      }
    });
  }
}
