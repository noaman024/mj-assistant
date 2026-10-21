# MJ JARVIS Mobile Companion (React Native / Expo)

This mobile app wrapper allows **Noaman** to control MJ and interact with two-way voice directly from any Android phone or iPhone.

---

## 🚀 Quick Start with Expo Go (No Android Studio required)

1. Open your terminal in this directory:
   ```bash
   cd mobile_react_native
   npm install
   ```

2. Start the Expo development server:
   ```bash
   npx expo start
   ```

3. Scan the QR code using the **Expo Go** app on your phone (available on Google Play Store and Apple App Store).

---

## 🌐 Remote Access Options (Local Wi-Fi or Outside the House)

- **Option 1: Same Wi-Fi Network**
  - Enter your Laptop's local IP: `http://192.168.x.x:8000` in the app's `⚙️ URL` settings.
- **Option 2: Remote / Cellular Data (ngrok / Cloudflare Tunnel)**
  - On your laptop, run:
    ```bash
    ngrok http 8000
    ```
  - Copy the forwarded `https://...ngrok-free.app` URL and paste it into the mobile app's `⚙️ URL` setting.
  - You can now talk to and control MJ from anywhere in the world!

---

## 📦 Building Standalone APK

To build a standalone installable Android APK file:
```bash
npm install -g eas-cli
eas login
eas build -p android --profile preview
```
