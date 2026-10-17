# Project Discussion & Requirements Summary

**Date:** 10–11 October 2026  
**User:** Noaman  
**Assistant Name:** **MJ** (Personal AI Assistant)  

---

## 1. Project Identity & Reference
* **Official Name:** **MJ**
* **Reference Project (Base):** MYRAA Assistant
* **Google Drive Link:** `https://drive.google.com/drive/folders/1VmV3MyZDhWkPeN_AiPPZBcx5kBhWXieU?usp=drive_link`
* **Architecture Overview:**
  - **Frontend:** React + Dynamic Audio/Screen Visualizers + Memory Dashboard (Branded as **MJ**).
  - **Backend Server:** Node.js/TypeScript + WebSockets + Gemini Multimodal Live API.
  - **Desktop Agent:** Python FastAPI (`desktop_agent/`) with 40+ system tools (Volume, Brightness, Playwright browser automation, Screenshots/OCR, App launchers).
  - **Packaging:** Windows Electron standalone application.
* **Goal:** Build & customize **MJ** with personalized features, wake-word ("Hey MJ"), and custom styling.

---

## 2. Core Planned Features & Workflows

### A. Cross-Device Ecosystem (Phone ↔ Laptop)
* **Phone Controls Laptop:**
  - Voice/text commands from phone to control laptop volume, sleep/shutdown, launch apps.
  - Live screen mirroring/surveillance view on phone.
* **Bidirectional App & Software Launcher (Laptop + Phone Dono Par):**
  - **Laptop par apps:** Kisi bhi device se command dekar PC par software/apps/games kholna (*Chrome, VS Code, Photoshop, Games*).
  - **Phone par apps:** Kisi bhi device se command dekar Phone par apps kholna (*WhatsApp, YouTube, Instagram, Camera, Phone Settings*).
  - Smart Routing: Voice me agar device mention kiya (*"phone me"* ya *"laptop me"*), toh exact usi device par open hoga.
* **Laptop Controls Phone:**
  - "Find My Phone" (ring even if silent).
  - Phone battery and notification checks on laptop.
  - Wireless clipboard and file sync.
  - Phone camera feed as AI live visual input.
* **Implementation Modes:** Local Wi-Fi Web App (PWA) / Private Telegram Bot Bridge.

### B. Hands-Free Voice Messaging
* Send WhatsApp/SMS messages via voice while busy working on the laptop (e.g., *"Rahul ko WhatsApp par bolo ki 10 minute me call karta hun"*).
* Direct WhatsApp Web / deep-link automation.
* Contact memory persistence in `memories.json`.
* Optional voice confirmation before sending.

### C. AI Call Screening & Smart Voicemail
* **Use Case:** Missed calls while sleeping or attending college lectures.
* **Workflow:**
  1. Phone rings 3–4 times; if unanswered, AI picks up.
  2. Greets caller politely in Hindi/English: *"Noaman abhi college lecture me hain aur call attend nahi kar sakte. Kya aapka koi zaroori message hai?"*
  3. Records and transcribes caller's spoken message.
  4. Delivers an instant summary card (Caller details, Timestamp, Message summary, Audio recording clip) to laptop and phone.

---

## 3. Status & Next Steps
* Discussion saved for long-term reference.
* Ready to start project scaffolding and implementation whenever needed.
