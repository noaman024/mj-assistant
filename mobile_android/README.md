# 📱 MJ Assistant - JARVIS Mobile APK Project

This Android project transforms **Noaman's** smartphone into a native, autonomous JARVIS mobile terminal connected to the local MJ Assistant backend.

---

## 🌟 5 Core JARVIS Mobile Superpowers

### 1. 📱 Native Android Device Control & Intents (`DeviceController.kt`)
- **Open Any App:** Voice triggers like *"Open WhatsApp"*, *"Open YouTube"*, *"Open Spotify"*, *"Open Chrome"*, *"Camera"* launch target apps instantly via Android Intents.
- **Hardware Toggles:** Voice control to turn on/off the flashlight (`CameraManager`), open Bluetooth settings panel, and toggle Wi-Fi panel.
- **Volume & Media Actuation:** Dynamic adjustment (`volume up`, `volume down`, `set volume to 80%`, `mute`, `unmute`) directly via `AudioManager`.

### 2. 👂 24/7 Background Service & Always-On Wake Word (`MJForegroundService.kt`)
- **Foreground Service with Persistent Notification:** Keeps the app alive in memory even when minimized or phone screen is turned off.
- **Low-Power Wake-Word Detection:** Listens on a dedicated 16000Hz PCM audio stream. When speech energy patterns detect *"Hey MJ"* or *"MJ"*, the service automatically wakes up the screen and triggers hands-free listening.

### 3. 🎙️ Continuous Native Audio Streaming & Media Ducking (`AudioStreamManager.kt`)
- **Audio Ducking:** Automatically requests transient audio focus (`AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK`) when MJ starts speaking, smoothly lowering any playing music/YouTube video in the background.
- **RMS Audio Amplitude Hook:** `MainActivity.kt`'s SpeechRecognizer computes live microphone RMS decibels (`onRmsChanged`) and streams normalized 0–100 amplitude directly to the WebView visualizer in real time.
- **Smooth TTS Audio Player:** Streams synthesized Edge-TTS responses over HTTP/WebSocket without cutting off words.

### 4. ⚛️ Mobile JARVIS Sci-Fi UI/UX
- **Arc Reactor Energy Core:** Glowing neon cyan (`#00f0ff`) and electric orange (`#ff7700`) concentric rotating HUD rings.
- **Responsive Waveform Visualizer:** Harmonic sine-wave visualizer canvas that pulses and expands dynamically when Noaman speaks or when MJ responds.

### 5. ⚡ Deep Linking & Push Automation Hooks (`MJCommandReceiver.kt`)
- **Deep Links:** Support for `mj://command?query=<command>` and `https://mj.assistant/command?query=<command>`.
- **Autonomous Broadcast Receiver:** `MJCommandReceiver` listens for `com.mj.assistant.EXECUTE_COMMAND` broadcasts, allowing the PC backend to push tasks to the phone (e.g., ring phone, toggle torch, adjust volume, launch apps) even when the app is in the background.

---

## 🛠️ How to Build the APK

### Method 1: Local Android Studio Build
1. Open **Android Studio**.
2. Select **Open** and choose this directory:
   `c:\Users\sabir\antigravity\assistant\mobile_android`
3. Wait for Gradle sync to finish.
4. Select **Build** > **Build Bundle(s) / APK(s)** > **Build APK(s)**.
5. Locate the generated `app-debug.apk` in `app/build/outputs/apk/debug/` and install it on your phone!

### Method 2: GitHub Actions Automated Cloud Build
1. Run `push_to_github.bat` from the root directory.
2. Go to your repository's **Actions** tab on GitHub.
3. Select **Build MJ Native Android APK** and click **Run workflow**.
4. Download the compiled `MJ-Assistant-Debug-APK` directly to your phone and install!
