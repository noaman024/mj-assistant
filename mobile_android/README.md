# 📱 MJ Assistant - Full Native Android Application

## 🌟 Superpowers Included in Native APK
1. **24/7 Background Foreground Service (`MJForegroundService.kt`)**:
   - Uses `PARTIAL_WAKE_LOCK` to keep listening for *"Hey MJ"* even when the phone screen is completely locked and turned off in your pocket.
2. **Zero-Touch WhatsApp Auto-Send (`MJAccessibilityService.kt`)**:
   - Automatically opens WhatsApp, inputs message text, and clicks the Send button without manual tapping.
3. **Direct Calling (`DirectCallManager.kt`)**:
   - Uses `CALL_PHONE` permission to place calls instantly without confirmation dialogs.
4. **Dual-Mode Engine (`DualModeBridge.kt`)**:
   - **Mode 1 (Wi-Fi Bridge):** When your laptop is ON, phone controls laptop apps (CapCut, Blender, Volume, Lock PC).
   - **Mode 2 (4G/5G Standalone):** When you are outside, phone acts as an independent portable AI assistant.

---

## 🛠️ How to Build the APK

### Method 1: Build in Android Studio (Local PC)
1. Download & open **Android Studio**.
2. Select **Open** and choose the `mobile_android` directory:
   `c:\Users\sabir\antigravity\assistant\mobile_android`
3. Wait for Gradle sync to complete.
4. Go to **Build** menu > **Build Bundle(s) / APK(s)** > **Build APK(s)**.
5. Once compiled, click **locate** to get `app-debug.apk`.
6. Transfer `app-debug.apk` to your phone via USB or WhatsApp, tap on it, and select **Install**!

### Method 2: Automated Cloud Build (Zero Setup on PC)
We have included a GitHub Actions workflow in `.github/workflows/build_apk.yml`:
1. Push this project to GitHub.
2. Go to the **Actions** tab on your GitHub repository.
3. Select **Build MJ Native Android APK** and click **Run workflow**.
4. In under two minutes, GitHub compiles the APK and provides a direct download link under **Artifacts** (`MJ-Assistant-Debug-APK`).
5. Download directly to your phone and install!
