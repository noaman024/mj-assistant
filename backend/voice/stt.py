import time
import re
import logging
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from backend.config.settings import WAKE_WORDS

logger = logging.getLogger("MJ.STT")

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.2  # 200ms
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

# Comprehensive phonetic regex patterns for "Hey MJ" and "MJ" across Indian English and Hindi STT
WAKE_PATTERNS = [
    r"\b(?:hey|hi|hello|suno|arre|arey|oye)?\s*(?:mj|mg|m\s*j|m\.j\.|emjay|m\s*jay|एम\s*जे|एमजे)\b",
    r"\b(?:hey|hi|hello)?\s*jarvis\b"
]
COMPILED_WAKE = [re.compile(p, re.IGNORECASE) for p in WAKE_PATTERNS]

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.sample_rate = SAMPLE_RATE
        self.silence_threshold = 120  # Sensitive AC RMS threshold
        self.silence_limit = 0.55     # Seconds of silence to conclude speech (optimized for fast conversational response)

    def calibrate_noise(self, duration: float = 0.5):
        """Calibrates microphone for ambient room noise with AC zero-mean filtering"""
        try:
            recording = sd.rec(int(duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='int16')
            sd.wait()
            audio_float = recording.astype(np.float32).flatten()
            # Calculate true AC energy without DC bias
            ac_rms = np.sqrt(np.mean((audio_float - np.mean(audio_float)) ** 2))
            # Adaptive threshold: ambient AC + 40% margin, bounded between 100 and 400
            self.silence_threshold = max(min(ac_rms * 1.4, 400), 100)
            logger.info(f"Calibrated noise threshold: {self.silence_threshold:.1f} (ambient: {ac_rms:.1f})")
        except Exception as e:
            logger.warning(f"Noise calibration error: {e}")
            self.silence_threshold = 120

    def listen_command(self, timeout: float = 8.0) -> str:
        """
        Listens to the microphone using sounddevice with a pre-speech ring buffer.
        Detects when user starts speaking and stops after pause.
        """
        recorded_chunks = []
        is_speaking = False
        silence_start = None
        start_time = time.time()
        prev_chunks = []
        max_prev = 2  # Keep ~400ms prior to voice detection so first syllable is never lost

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16') as stream:
                while True:
                    if not is_speaking and (time.time() - start_time > timeout):
                        return ""

                    data, _ = stream.read(CHUNK_SIZE)
                    audio_float = data.astype(np.float32).flatten()
                    # True AC RMS calculation
                    rms = np.sqrt(np.mean((audio_float - np.mean(audio_float)) ** 2))

                    if rms > self.silence_threshold:
                        if not is_speaking:
                            is_speaking = True
                            # Prepend pre-speech buffer so words like "Hey" or "MJ" aren't clipped
                            for prev in prev_chunks:
                                recorded_chunks.append(prev)
                        recorded_chunks.append(data.tobytes())
                        silence_start = None
                    elif is_speaking:
                        recorded_chunks.append(data.tobytes())
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > self.silence_limit:
                            break
                    else:
                        prev_chunks.append(data.tobytes())
                        if len(prev_chunks) > max_prev:
                            prev_chunks.pop(0)

            if not recorded_chunks:
                return ""

            # Combine all recorded chunks into AudioData
            audio_bytes = b"".join(recorded_chunks)
            audio_data = sr.AudioData(audio_bytes, self.sample_rate, 2)

            # Try en-IN first (recognizes Indian Hinglish and English)
            try:
                text = self.recognizer.recognize_google(audio_data, language="en-IN")
                if text:
                    logger.info(f"Recognized Speech (en-IN): '{text}'")
                    return text
            except sr.UnknownValueError:
                pass

            # Fallback to hi-IN (pure Hindi)
            try:
                text = self.recognizer.recognize_google(audio_data, language="hi-IN")
                if text:
                    logger.info(f"Recognized Speech (hi-IN): '{text}'")
                    return text
            except Exception:
                return ""

        except Exception as e:
            logger.error(f"Error recording from microphone: {e}")
            return ""

    def is_wake_word(self, text: str) -> bool:
        """Check if spoken phrase contains the wake word (including all phonetic variations)"""
        if not text:
            return False
        t_lower = text.lower().strip()
        for pattern in COMPILED_WAKE:
            if pattern.search(t_lower):
                return True
        return False

# Global instance
stt = SpeechToText()

