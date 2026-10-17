import io
import base64
import logging
from PIL import Image
from backend.core.llm_engine import llm
from backend.config.settings import GEMINI_MODEL, USER_NAME, ASSISTANT_NAME

logger = logging.getLogger("MJ.Vision")

class VisionAnalyzer:
    def __init__(self):
        pass

    async def analyze_image_bytes(self, image_bytes: bytes, prompt: str = None) -> str:
        """Analyzes an image using Gemini Multimodal Vision"""
        default_prompt = (
            f"You are {ASSISTANT_NAME}, {USER_NAME}'s AI assistant. "
            f"Answer concisely in natural Hinglish or Hindi. Describe what you see in this image or answer {USER_NAME}'s query."
        )
        user_prompt = prompt or default_prompt

        if llm.gemini_client:
            try:
                from google.genai import types
                image = Image.open(io.BytesIO(image_bytes))
                response = llm.gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[user_prompt, image]
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini vision error: {e}")
                return f"Vision processing me issue aayi: {e}"

        return "Gemini Vision client available nahi hai ya image process nahi ho saki."

    async def analyze_base64(self, b64_string: str, prompt: str = None) -> str:
        """Decodes base64 image (from phone camera) and analyzes it"""
        try:
            if "," in b64_string:
                b64_string = b64_string.split(",", 1)[1]
            image_bytes = base64.b64decode(b64_string)
            return await self.analyze_image_bytes(image_bytes, prompt)
        except Exception as e:
            logger.error(f"Base64 image decode error: {e}")
            return f"Image format decode nahi ho paya: {e}"

vision_analyzer = VisionAnalyzer()
