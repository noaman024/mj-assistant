import os
import socket
import logging
from pathlib import Path
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config.settings import API_PORT, USER_NAME, ASSISTANT_NAME
from backend.tools.system_control import system_control
from backend.tools.vision_analyzer import vision_analyzer
from backend.bridge.phone_hub import phone_hub

logger = logging.getLogger("MJ.BridgeServer")

WEB_DIR = Path(__file__).parent / "web"

app = FastAPI(title="MJ Cross-Device Bridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static web files
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

class CommandRequest(BaseModel):
    query: str
    source: str = "phone"

class ClipboardRequest(BaseModel):
    text: str

class VisionRequest(BaseModel):
    image_b64: str
    prompt: str = None

@app.get("/")
async def get_index():
    return FileResponse(WEB_DIR / "index.html")

@app.get("/desktop")
async def get_desktop():
    """Serves the Futuristic Holographic Desktop Cockpit UI"""
    return FileResponse(WEB_DIR / "desktop.html")

@app.get("/manifest.json")
async def get_manifest():
    return FileResponse(WEB_DIR / "manifest.json")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.get("/api/network/info")
async def get_network_info():
    ip = get_local_ip()
    port = API_PORT
    phone_url = f"http://{ip}:{port}"
    return {
        "local_ip": ip,
        "port": port,
        "phone_url": phone_url,
        "qr_url": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={phone_url}"
    }

@app.get("/api/status")
async def get_status():
    """Returns combined status of Laptop and connected Phone"""
    battery = psutil.sensors_battery()
    batt_info = None
    if battery:
        batt_info = {
            "percent": battery.percent,
            "plugged": battery.power_plugged
        }

    return {
        "laptop": {
            "cpu": psutil.cpu_percent(interval=None),
            "ram": psutil.virtual_memory().percent,
            "battery": batt_info,
            "user": USER_NAME
        },
        "phone": phone_hub.phone_status
    }

@app.post("/api/command")
async def handle_remote_command(req: CommandRequest):
    """Executes a command originating from the desktop or phone on the laptop with NLP telemetry"""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Command from {req.source}: '{req.query}'")
    from backend.core.orchestrator import orchestrator
    response_text = await orchestrator.process_command(req.query, source_device=req.source)
    nlp_data = None
    if orchestrator.last_nlp_result:
        nlp_data = orchestrator.last_nlp_result.model_dump()

    return {
        "status": "success",
        "query": req.query,
        "response": response_text,
        "nlp": nlp_data
    }

@app.post("/api/nlp/analyze")
async def analyze_nlp_query(req: CommandRequest):
    """Direct NLP inspection endpoint returning Intent, Entities, Sentiment and Latency"""
    from backend.core.nlp_engine import nlp_engine
    res = await nlp_engine.parse(req.query)
    return {
        "status": "success",
        "nlp": res.model_dump()
    }

@app.get("/api/screen/snapshot")
async def get_screen_snapshot():
    """High-speed JPEG capture for real-time mobile screen mirroring"""
    try:
        jpeg_bytes = system_control.get_screen_jpeg_bytes(max_width=960, quality=55)
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    except Exception as e:
        logger.error(f"Error capturing screen snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clipboard")
async def handle_clipboard_sync(req: ClipboardRequest):
    """Syncs clipboard between devices"""
    text = req.text
    try:
        import pyperclip
        pyperclip.copy(text)
    except Exception:
        pass

    msg = await phone_hub.sync_clipboard(text, source="phone")
    return {"status": "success", "message": msg}

@app.post("/api/vision/analyze")
async def handle_vision_analysis(req: VisionRequest):
    """Multimodal vision analysis of photo captured by phone camera"""
    result = await vision_analyzer.analyze_base64(req.image_b64, req.prompt)
    return {
        "status": "success",
        "analysis": result
    }

@app.post("/api/ring")
async def trigger_find_my_phone():
    """Triggers loud siren on connected phone"""
    success, message = await phone_hub.ring_phone()
    return {"success": success, "message": message}

@app.post("/api/ring/stop")
async def stop_phone_ring():
    """Stops the siren on phone"""
    success, message = await phone_hub.stop_ring()
    return {"success": success, "message": message}

# --- Phase 5: AI Call Screening & Smart Voicemail APIs ---
class VoicemailRequest(BaseModel):
    phone_number: str
    transcript: str
    caller_name: str = None
    audio_b64: str = None

@app.get("/api/call/voicemails")
async def get_voicemails():
    """Returns list of all screened voicemails"""
    from backend.call_screening import call_screener
    return {
        "voicemails": call_screener.voicemails,
        "unread_count": len(call_screener.get_unread_voicemails())
    }

@app.post("/api/call/voicemails/read")
async def mark_voicemails_read():
    from backend.call_screening import call_screener
    call_screener.mark_all_as_read()
    return {"status": "success", "message": "All voicemails marked as read"}

@app.post("/api/call/voicemail")
async def receive_voicemail(req: VoicemailRequest):
    """Processes new voicemail left by caller"""
    from backend.call_screening import call_screener
    audio_bytes = None
    if req.audio_b64:
        import base64
        try:
            audio_bytes = base64.b64decode(req.audio_b64)
        except Exception:
            pass

    entry = await call_screener.process_incoming_voicemail(
        phone_number=req.phone_number,
        transcript=req.transcript,
        audio_bytes=audio_bytes,
        caller_name=req.caller_name
    )
    return {"status": "success", "voicemail": entry}

@app.get("/api/call/audio/{filename}")
async def get_voicemail_audio(filename: str):
    from backend.call_screening import VOICEMAILS_AUDIO_DIR
    audio_path = VOICEMAILS_AUDIO_DIR / filename
    if audio_path.exists():
        return FileResponse(audio_path, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="Audio file not found")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await phone_hub.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            if event_type == "phone_status":
                phone_hub.update_phone_telemetry(
                    battery=data.get("battery"),
                    charging=data.get("charging", False),
                    device=data.get("device")
                )

            elif event_type == "ring_stopped":
                phone_hub.phone_status["is_ringing"] = False

            elif event_type == "command":
                cmd = data.get("query", "")
                if cmd:
                    from backend.core.orchestrator import orchestrator
                    resp = await orchestrator.process_command(cmd, source_device="phone")
                    await websocket.send_json({
                        "type": "command_result",
                        "response": resp
                    })

    except WebSocketDisconnect:
        phone_hub.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        phone_hub.disconnect(websocket)

@app.get("/api/phone/sync/contacts")
async def get_synced_contacts():
    from backend.tools.contact_manager import contact_manager
    return {"status": "success", "contacts": contact_manager.contacts}

@app.post("/api/phone/sync/contacts")
async def save_synced_contacts(req: dict):
    from backend.tools.contact_manager import contact_manager
    new_contacts = req.get("contacts", [])
    count = 0
    for c in new_contacts:
        if c.get("name") and c.get("phone"):
            contact_manager.add_contact(c["name"], c["phone"])
            count += 1
    return {"status": "success", "synced": count, "total": len(contact_manager.contacts)}

@app.get("/api/phone/sync/memories")
async def get_synced_memories():
    from backend.core.memory import memory
    return {"status": "success", "memories": memory.memories}

def get_local_ip() -> str:
    """Detects active local Wi-Fi IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_connection_banner(port: int = 8000):
    ip = get_local_ip()
    print("\n" + "=" * 65)
    print(f"📱  MJ CROSS-DEVICE CONTROLLER ACTIVE  📱")
    print("=" * 65)
    print(f"👉 Laptop Local URL: http://localhost:{port}")
    print(f"👉 Phone Wi-Fi URL:  http://{ip}:{port}")
    print("=" * 65)
    print(f"Apne phone ke browser me 'http://{ip}:{port}' kholein.")
    print("Saare remote controls, camera vision, aur screen mirror chalu hain!")
    print("=" * 65 + "\n")
