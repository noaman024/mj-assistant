# 📱 MJ Mobile Assistant: Smart Dual-Mode Android Application

This is the native Android application for **MJ Assistant**, designed specifically for **Noaman**.

It implements the **Smart Dual-Mode (Option 1 + Option 3)** architecture:
- **Mode 1: Standalone Phone Mode (Laptop OFF / Travel):** Direct 4G/5G AI, calling, and WhatsApp without laptop dependency.
- **Mode 2: Jarvis Laptop Bridge Mode (Laptop ON):** Automatic Wi-Fi handshake, remote laptop control, and telemetry sync.

---

## 🚀 Key Features Built-In

1. **Direct Phone Calling (`CALL_PHONE`):**
   - Connects calls instantly without requiring the user to press the green dialer button.
2. **Zero-Touch WhatsApp Automation (`AccessibilityService`):**
   - Automatically navigates to the contact chat, fills the text box, and triggers the Send button hands-free.
3. **24/7 Background Wake Word (`ForegroundService` + `WakeLock`):**
   - Listens for commands even when the screen is locked or in your pocket.
4. **Holographic Cyberpunk Cockpit UI (Jetpack Compose):**
   - Pulsing animated audio orb, live mode status badge, quick action chips, and command terminal.
5. **Hinglish Pronunciation Normalizer:**
   - Built-in phonetic cleaner ensuring natural speech (Noaman -> "नोमान", RAM -> "रैम", CPU -> "सी.पी.यू.").

---

## 🛠️ How to Open & Build the APK

### Method 1: Using Android Studio (Recommended)
1. Open **Android Studio**.
2. Click **File > Open** and select the folder:
   ```text
   c:\Users\sabir\antigravity\assistant\mobile\android
   ```
3. Android Studio will automatically sync the Gradle project.
4. Connect your Android phone with **USB Debugging** enabled.
5. Click the green **Run (▶)** button, or click:
   **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
6. The generated `app-debug.apk` will be in `app/build/outputs/apk/debug/`.

### Method 2: Building via Command Line (Gradle)
In terminal inside `mobile/android`:
```bash
gradlew assembleDebug
```

---

## ⚙️ Initial Setup & Permissions on Phone

When you open the app for the first time:
1. **Grant Runtime Permissions:**
   - Microphone (`RECORD_AUDIO`)
   - Phone Calls (`CALL_PHONE`)
   - Contacts (`READ_CONTACTS`)
2. **Enable WhatsApp Automation:**
   - Go to your phone's **Settings > Accessibility**.
   - Find **MJ Assistant** under Downloaded Apps/Services.
   - Turn it **ON**.

---

## 📡 Dual-Mode Operation

- **Ghar par (Laptop ON hai):**
  - App Wi-Fi par laptop ko auto-detect karegi.
  - Header me green status aayega: `● JARVIS BRIDGE (Laptop: 192.168.x.x)`.
  - Tum phone se laptop par gana chala sakte ho, diagnostics run kar sakte ho, ya laptop lock kar sakte ho.
- **Bahar / Laptop OFF hai:**
  - Header me cyan status aayega: `● STANDALONE PHONE MODE (Direct 4G/5G AI)`.
  - Phone par call lagana, WhatsApp bhejna, torch jalana, aur AI se baatein karna 100% normal chalega!
