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
    image_b64: str = None
    image: str = None
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

@app.get("/sw.js")
async def get_service_worker():
    return FileResponse(WEB_DIR / "sw.js", media_type="application/javascript")

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

    cpu_val = psutil.cpu_percent(interval=None)
    ram_val = psutil.virtual_memory().percent
    batt_val = batt_info["percent"] if batt_info else 100

    return {
        "status": "online",
        "cpu": cpu_val,
        "ram": ram_val,
        "battery": batt_val,
        "laptop": {
            "cpu": cpu_val,
            "ram": ram_val,
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
    img_data = req.image_b64 or req.image
    if not img_data:
        raise HTTPException(status_code=400, detail="Image data is required")
    result = await vision_analyzer.analyze_base64(img_data, req.prompt)
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

# --- OpenJarvis Agent Endpoints ---
class ResearchRequest(BaseModel):
    topic: str

class CodeRequest(BaseModel):
    code: str

class MemoryFactRequest(BaseModel):
    fact: str

@app.get("/api/agent/digest")
async def get_morning_digest():
    """Generates on-demand Morning Digest briefing"""
    from backend.agents.morning_digest import morning_digest
    briefing = await morning_digest.generate_briefing()
    return {"status": "success", "briefing": briefing}

@app.post("/api/agent/research")
async def run_deep_research(req: ResearchRequest):
    """Executes multi-hop Deep Research on a topic"""
    from backend.agents.deep_research import deep_research
    result = await deep_research.research(req.topic)
    return {"status": "success", "research": result}

@app.post("/api/agent/code")
async def execute_python_sandbox(req: CodeRequest):
    """Executes sandboxed Python code via CodeInterpreter"""
    from backend.tools.code_interpreter import code_interpreter
    result = code_interpreter.execute(req.code)
    return {"status": "success", "execution": result}

@app.get("/api/agent/memory")
async def get_durable_facts():
    """Returns stored durable facts about Noaman"""
    from backend.core.fact_extractor import fact_extractor
    facts = fact_extractor.get_all_facts()
    return {"status": "success", "facts": facts}

@app.post("/api/agent/memory")
async def save_durable_fact(req: MemoryFactRequest):
    """Saves a new durable fact into persistent memory"""
    from backend.core.fact_extractor import fact_extractor
    saved = fact_extractor.save_fact(req.fact)
    return {"status": "success", "saved": saved}

# --- JARVIS Universal IoT Smart Home Endpoints ---
class IoTControlRequest(BaseModel):
    device_id: str
    action: str
    value: Any = None

class IoTRegisterRequest(BaseModel):
    id: str
    name: str
    protocol: str = "rest"
    endpoints: Dict[str, str] = {}
    aliases: List[str] = []

@app.get("/api/iot/devices")
async def get_iot_devices():
    """Returns list of all registered smart home IoT devices"""
    from backend.tools.iot_controller import iot_controller
    return {"status": "success", "devices": iot_controller.list_devices()}

@app.post("/api/iot/control")
async def control_iot_device(req: IoTControlRequest):
    """Controls a smart home device via REST or MQTT"""
    from backend.tools.iot_controller import iot_controller
    res = await iot_controller.execute_action(req.device_id, req.action, req.value)
    return {"status": "success", "result": res}

@app.post("/api/iot/register")
async def register_iot_device(req: IoTRegisterRequest):
    """Registers new IoT hardware device"""
    from backend.tools.iot_controller import iot_controller
    res = iot_controller.register_device(req.model_dump())
    return {"status": "success", "result": res}

# --- JARVIS Automation Engine & Macro Endpoints ---
class MacroRequest(BaseModel):
    macro_name: str

class PowerShellRequest(BaseModel):
    script: str

@app.get("/api/automation/macros")
async def get_macros():
    """Lists available automation macros"""
    from backend.tools.automation_engine import automation_engine
    return {"status": "success", "macros": automation_engine.macros}

@app.post("/api/automation/macro")
async def run_automation_macro(req: MacroRequest):
    """Executes a multi-action automation macro"""
    from backend.tools.automation_engine import automation_engine
    res = await automation_engine.execute_macro(req.macro_name)
    return {"status": "success", "result": res}

@app.post("/api/automation/powershell")
async def run_powershell_script(req: PowerShellRequest):
    """Runs a system-level PowerShell automation script"""
    from backend.tools.automation_engine import automation_engine
    res = automation_engine.execute_powershell(req.script)
    return {"status": "success", "result": res}

# --- JARVIS Autonomous Task Scheduler Endpoints ---
class DynamicTaskRequest(BaseModel):
    task_id: str
    name: str
    interval_sec: int
    command: str

@app.get("/api/scheduler/tasks")
async def get_scheduled_tasks():
    """Lists active autonomous background tasks"""
    from backend.core.proactive_scheduler import proactive_scheduler
    return {"status": "success", "tasks": proactive_scheduler.list_tasks()}

@app.post("/api/scheduler/task")
async def add_scheduled_task(req: DynamicTaskRequest):
    """Schedules a new autonomous background task"""
    from backend.core.proactive_scheduler import proactive_scheduler
    from backend.core.orchestrator import orchestrator

    async def task_wrapper():
        return await orchestrator.process_command(req.command, source_device="scheduler")

    proactive_scheduler.register_task(
        task_id=req.task_id,
        name=req.name,
        interval_sec=req.interval_sec,
        handler=task_wrapper,
        vocal_announce=True
    )
    return {"status": "success", "message": f"Task '{req.name}' scheduled every {req.interval_sec}s."}

@app.delete("/api/scheduler/task/{task_id}")
async def delete_scheduled_task(task_id: str):
    """Deletes an autonomous background task"""
    from backend.core.proactive_scheduler import proactive_scheduler
    success = proactive_scheduler.unregister_task(task_id)
    return {"status": "success" if success else "error", "removed": success}

# --- Mobile Two-Way Audio Streaming (Edge-TTS over HTTP/WS) ---
class TTSStreamRequest(BaseModel):
    text: str

@app.post("/api/voice/tts")
async def stream_tts_audio(req: TTSStreamRequest):
    """Synthesizes speech and streams MP3 audio directly to phone browser for two-way audio"""
    import tempfile, edge_tts
    from backend.config.settings import TTS_VOICE, TTS_RATE, TTS_PITCH
    from backend.voice.hinglish_normalizer import normalize_hinglish

    spoken = normalize_hinglish(req.text)
    communicate = edge_tts.Communicate(text=spoken, voice=TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
        tmp_path = fp.name
    await communicate.save(tmp_path)
    return FileResponse(tmp_path, media_type="audio/mpeg")

@app.get("/api/voice/tts")
async def get_stream_tts_audio(text: str = ""):
    """GET version for direct HTML5 Audio(src) on mobile browsers"""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text query parameter is required")
    import tempfile, edge_tts
    from backend.config.settings import TTS_VOICE, TTS_RATE, TTS_PITCH
    from backend.voice.hinglish_normalizer import normalize_hinglish

    spoken = normalize_hinglish(text)
    communicate = edge_tts.Communicate(text=spoken, voice=TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
        tmp_path = fp.name
    await communicate.save(tmp_path)
    return FileResponse(tmp_path, media_type="audio/mpeg")

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
