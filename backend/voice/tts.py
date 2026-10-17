import asyncio
import os
import tempfile
import logging
from pathlib import Path
import edge_tts
import sounddevice as sd
import av
import numpy as np
import pyttsx3
from backend.config.settings import (
    TTS_VOICE,
    TTS_RATE,
    TTS_PITCH,
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    ELEVENLABS_MODEL_ID,
)

logger = logging.getLogger("MJ.TTS")

class TextToSpeech:
    def __init__(self):
        self.voice = TTS_VOICE
        self.rate = TTS_RATE
        self.pitch = TTS_PITCH
        self.elevenlabs_api_key = ELEVENLABS_API_KEY
        self.elevenlabs_voice_id = ELEVENLABS_VOICE_ID
        self.elevenlabs_model_id = ELEVENLABS_MODEL_ID
        self._offline_engine = None

    def _get_offline_engine(self):
        if self._offline_engine is None:
            try:
                self._offline_engine = pyttsx3.init()
                # Ensure a female voice is selected, never male David/Admin
                voices = self._offline_engine.getProperty('voices')
                for v in voices:
                    name_lower = v.name.lower()
                    if any(fem in name_lower for fem in ["zira", "hazel", "heera", "kalpana", "female"]):
                        self._offline_engine.setProperty('voice', v.id)
                        logger.info(f"Selected female offline TTS voice: {v.name}")
                        break
                self._offline_engine.setProperty('rate', 175)
            except Exception as e:
                logger.error(f"Failed to init pyttsx3: {e}")
        return self._offline_engine

    async def speak(self, text: str):
        """Asynchronous speak"""
        await self.speak_async(text)

    def speak_sync(self, text: str):
        """Synchronous speak wrapper"""
        try:
            loop = asyncio.get_running_loop()
            import threading
            threading.Thread(target=lambda: asyncio.run(self.speak_async(text)), daemon=True).start()
        except RuntimeError:
            asyncio.run(self.speak_async(text))

    async def _speak_elevenlabs(self, text: str) -> bool:
        """Synthesize speech using ElevenLabs API (Swati S voice)"""
        # Reload key in case updated at runtime in .env
        api_key = self.elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY", "").strip()
        if not api_key:
            return False

        try:
            import httpx
            logger.info(f"Synthesizing voice via ElevenLabs [Voice ID: {self.elevenlabs_voice_id}]...")
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key,
            }
            payload = {
                "text": text,
                "model_id": self.elevenlabs_model_id,
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.85,
                    "style": 0.35,
                    "use_speaker_boost": True,
                },
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                        temp_filename = fp.name
                        fp.write(resp.content)
                    self._play_audio_file(temp_filename)
                    try:
                        os.remove(temp_filename)
                    except Exception:
                        pass
                    return True
                else:
                    logger.warning(f"ElevenLabs TTS returned HTTP {resp.status_code}: {resp.text[:120]}")
                    return False
        except Exception as e:
            logger.warning(f"ElevenLabs synthesis error ({e}). Falling back...")
            return False

    async def speak_async(self, text: str):
        """Synthesize and play speech asynchronously with multi-tier fallback"""
        if not text.strip():
            return

        logger.info(f"Speaking: '{text}'")

        # Phonetically optimize Hinglish pronunciation
        from backend.voice.hinglish_normalizer import normalize_hinglish
        spoken_text = normalize_hinglish(text)

        # Tier 1: Try ElevenLabs (Swati S) if API Key is configured
        if self.elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY", "").strip():
            success = await self._speak_elevenlabs(spoken_text)
            if success:
                return

        # Tier 2: Free Unlimited Edge-TTS Fallback
        try:
            communicate = edge_tts.Communicate(
                text=spoken_text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
            )
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_filename = fp.name

            await communicate.save(temp_filename)
            self._play_audio_file(temp_filename)

            try:
                os.remove(temp_filename)
            except Exception:
                pass
            return
        except Exception as e:
            logger.warning(f"Edge-TTS failed ({e}). Falling back to offline voice.")
            self._speak_offline(spoken_text)

    def _play_audio_file(self, filepath: str):
        container = av.open(filepath)
        stream = container.streams.audio[0]
        sample_rate = stream.rate

        audio_frames = []
        for frame in container.decode(stream):
            # Convert frame to numpy float32
            arr = frame.to_ndarray()
            # If stereo, average or reshape
            if arr.ndim == 2:
                arr = arr.T
            audio_frames.append(arr)

        if audio_frames:
            data = np.concatenate(audio_frames, axis=0)
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32768.0
            sd.play(data, samplerate=sample_rate)
            sd.wait()

    def _speak_offline(self, text: str):
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            for v in speaker.GetVoices():
                desc = v.GetDescription().lower()
                if any(fem in desc for fem in ["zira", "hazel", "heera", "female"]):
                    speaker.Voice = v
                    break
            speaker.Rate = 1
            speaker.Speak(text)
        except Exception as e:
            logger.warning(f"SAPI voice error ({e}). Trying pyttsx3...")
            try:
                engine = self._get_offline_engine()
                if engine:
                    engine.say(text)
                    engine.runAndWait()
            except Exception as e2:
                logger.error(f"Offline TTS failed: {e2}")

# Global instance
tts = TextToSpeech()
