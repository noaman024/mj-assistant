import json
import logging
from datetime import datetime
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger("MJ.PhoneHub")

class PhoneHub:
    """Manages real-time WebSocket communication and state synchronization between Phone and Laptop"""

    def __init__(self):
        self.active_websockets: Set[WebSocket] = set()
        self.phone_status = {
            "connected": False,
            "battery_percent": None,
            "is_charging": False,
            "device_name": "Mobile Device",
            "last_seen": None,
            "is_ringing": False
        }
        self.clipboard_content = ""

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.add(websocket)
        self.phone_status["connected"] = True
        self.phone_status["last_seen"] = datetime.now().isoformat()
        logger.info(f"Phone connected via WebSocket. Total clients: {len(self.active_websockets)}")
        
        # Send initial handshake with current state
        await websocket.send_json({
            "type": "handshake",
            "status": "connected",
            "message": "Connected to MJ Desktop Hub",
            "clipboard": self.clipboard_content
        })

    def disconnect(self, websocket: WebSocket):
        self.active_websockets.discard(websocket)
        if len(self.active_websockets) == 0:
            self.phone_status["connected"] = False
            self.phone_status["is_ringing"] = False
        logger.info(f"Phone disconnected. Remaining clients: {len(self.active_websockets)}")

    async def broadcast(self, message: dict):
        """Broadcasts JSON payload to all connected phone clients"""
        if not self.active_websockets:
            logger.debug(f"No connected phones to receive broadcast: {message.get('type')}")
            return False

        disconnected = set()
        for ws in self.active_websockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending to WebSocket client: {e}")
                disconnected.add(ws)

        for ws in disconnected:
            self.disconnect(ws)
        return True

    async def ring_phone(self) -> tuple[bool, str]:
        """Triggers loud siren on connected phone ('Find My Phone')"""
        self.phone_status["is_ringing"] = True
        sent = await self.broadcast({
            "type": "ring_alert",
            "action": "start_siren",
            "message": "MJ FIND MY PHONE: Loud Ringing Activated!"
        })
        if sent:
            return True, "Noaman, maine aapke phone par loud alarm bajana shuru kar diya hai."
        else:
            return False, "Phone abhi Wi-Fi controller se connected nahi hai. Kripya phone browser me MJ controller open rakhein."

    async def stop_ring(self) -> tuple[bool, str]:
        """Stops the siren on connected phone"""
        self.phone_status["is_ringing"] = False
        await self.broadcast({
            "type": "ring_alert",
            "action": "stop_siren"
        })
        return True, "Phone ka alarm band kar diya gaya hai."

    def update_phone_telemetry(self, battery: int = None, charging: bool = False, device: str = None):
        """Updates battery and device status received from phone PWA"""
        if battery is not None:
            self.phone_status["battery_percent"] = battery
        self.phone_status["is_charging"] = charging
        if device:
            self.phone_status["device_name"] = device
        self.phone_status["last_seen"] = datetime.now().isoformat()
        self.phone_status["connected"] = True

    def get_phone_battery_report(self) -> str:
        """Returns natural language phone battery status"""
        if not self.phone_status["connected"] or self.phone_status["battery_percent"] is None:
            return "Phone abhi MJ Wi-Fi controller se connect nahi hai, isliye battery status uplabdh nahi hai."

        batt = self.phone_status["battery_percent"]
        charging = "charger laga hua hai" if self.phone_status["is_charging"] else "battery par chal raha hai"
        return f"Noaman, aapke phone ki battery {batt}% hai aur {charging}."

    async def sync_clipboard(self, text: str, source: str = "laptop"):
        """Synchronizes clipboard across laptop and phone"""
        self.clipboard_content = text
        if source == "laptop":
            await self.broadcast({
                "type": "clipboard_sync",
                "text": text
            })
        return f"Clipboard text sync ho gaya: '{text[:40]}...'"

phone_hub = PhoneHub()
