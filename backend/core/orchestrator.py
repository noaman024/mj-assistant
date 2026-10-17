import re
import logging
from backend.core.llm_engine import llm
from backend.voice.tts import tts
from backend.tools.app_launcher import app_launcher, KNOWN_APPS
from backend.config.settings import USER_NAME, ASSISTANT_NAME

from backend.core.learning_engine import learning_engine
from backend.core.nlp_engine import nlp_engine, NLPResult

from backend.tools.system_control import system_control
from backend.tools.browser_controller import browser_control
from backend.tools.contact_manager import contact_manager
from backend.tools.messaging import message_automator
from backend.bridge.phone_hub import phone_hub
from backend.tools.call_manager import call_manager
from backend.core.diagnostics import diagnostics_engine
from backend.core.security import security_vault
from backend.tools.autonomous_executor import autonomous_executor
from backend.core.skill_learner import skill_learner
from backend.tools.vision_analyzer import vision_analyzer
from backend.tools.compression_manager import compression_manager

logger = logging.getLogger("MJ.Orchestrator")


class AssistantOrchestrator:
    def __init__(self):
        self.last_nlp_result: NLPResult = None

    async def process_command(self, query: str, source_device: str = "laptop") -> str:
        """Processes voice or text command from Noaman using NLP (NLU + NER + Sentiment)"""
        query_clean = query.strip()
        if not query_clean:
            return ""

        query_lower = query_clean.lower()
        logger.info(f"Processing command from {USER_NAME}: '{query_clean}' (Source: {source_device})")

        # 0-Wake. Instant Wake Word Acknowledgment & Stripping
        clean_wake = re.sub(r"[^\w\s]", "", query_lower).strip()
        wake_greetings = [
            "hey mj", "mj", "hello mj", "hi mj", "suno mj", "arre mj", "arey mj", "oye mj",
            "hey mg", "mg", "hello mg", "hi mg", "suno mg",
            "hey m j", "m j", "hello m j",
            "hey emjay", "emjay", "m jay", "hey m.j.", "m.j.",
            "एमजे", "एम जे", "हे एमजे", "हे एम जे",
            "hey jarvis", "jarvis", "hello jarvis"
        ]
        if clean_wake in wake_greetings:
            responses = [
                f"Haan {USER_NAME}! Sun rahi hu, kahiye kya karna hai?",
                f"Yes {USER_NAME}, main active hu! Boliye kya help karu?",
                f"Haan {USER_NAME}, bolo! Main bilkul ready hu."
            ]
            import random
            greeting_res = random.choice(responses)
            await tts.speak(greeting_res)
            return greeting_res

        # If wake word is a prefix of a command (e.g. "hey mj volume badhao")
        for wg in sorted(wake_greetings, key=len, reverse=True):
            if query_lower.startswith(wg):
                remainder = query_lower[len(wg):].strip(" ,.-:!?")
                if remainder:
                    query_clean = remainder
                    query_lower = remainder
                break

        # 0a. Security Vault Passcode Challenge Response
        if security_vault.awaiting_passcode_for:
            success, auth_msg = security_vault.authenticate(query_clean)
            await tts.speak(auth_msg)
            return auth_msg

        # 0b. Awaiting WhatsApp Message Content Flow
        if message_automator.awaiting_message_for:
            recipient = message_automator.awaiting_message_for
            success, prompt_msg, _ = message_automator.prepare_whatsapp_message(recipient, query_clean)
            await tts.speak(prompt_msg)
            return prompt_msg

        # 0c. Pending Message Confirmation Flow
        if message_automator.pending_message:
            if any(w in query_lower for w in ["haan", "bhej do", "send", "yes", "ha", "theek hai"]):
                res = message_automator.send_whatsapp()
                await tts.speak(res)
                return res
            elif any(w in query_lower for w in ["nahi", "cancel", "mat bhejo", "no", "rehnde"]):
                message_automator.pending_message = None
                res = "Theek hai, message cancel kar diya gaya hai."
                await tts.speak(res)
                return res

        # -------------------------------------------------------------
        # NLP PARSING (Natural Language Processing & Intent Classification)
        # -------------------------------------------------------------
        nlp_res = await nlp_engine.parse(query_clean)
        self.last_nlp_result = nlp_res
        logger.info(f"[NLP Brain] Parsed: Intent={nlp_res.intent} (Conf={nlp_res.confidence:.2f}, Sentiment={nlp_res.sentiment}, Source={nlp_res.source})")

        # Empathy prefix for negative/frustrated sentiment
        empathy_prefix = ""
        if nlp_res.sentiment == "frustrated":
            empathy_prefix = "Arre Noaman pareshan mat ho, "
        elif nlp_res.sentiment == "tired":
            empathy_prefix = "Haan Noaman, thoda rest bhi le lo. "

        # 1. System Controls Intent
        if nlp_res.intent == "SYSTEM_CONTROL":
            action = nlp_res.entities.action
            if action == "volume_up":
                res = system_control.volume_up()
            elif action == "volume_down":
                res = system_control.volume_down()
            elif action == "mute":
                res = system_control.mute()
            elif action == "lock":
                res = system_control.lock_pc()
            elif action == "sleep":
                res = system_control.sleep_pc()
            elif action == "minimize":
                res = system_control.minimize_all()
            elif action == "screenshot":
                _, res = system_control.take_screenshot()
            elif action == "battery":
                res = system_control.get_system_stats()
            else:
                res = system_control.get_system_stats()
            
            final_res = f"{empathy_prefix}{res}" if empathy_prefix else res
            await tts.speak(final_res)
            return final_res

        # 2. App Launch Intent
        if nlp_res.intent == "APP_LAUNCH" and nlp_res.entities.app_name:
            target = nlp_res.entities.target_device or source_device
            res = app_launcher.launch(nlp_res.entities.app_name, target=target)
            final_res = f"{empathy_prefix}{res}" if empathy_prefix else res
            await tts.speak(final_res)
            return final_res

        # 3. Communication Intent (Calling, WhatsApp, Contacts)
        if nlp_res.intent == "COMMUNICATION":
            action = nlp_res.entities.action
            if action == "call":
                target = nlp_res.entities.contact_name or query_clean
                res = await call_manager.dial_contact(target)
            elif action == "send_whatsapp":
                res_recipient = nlp_res.entities.contact_name
                res_msg = nlp_res.entities.message_text or ""
                _, res, _ = message_automator.prepare_whatsapp_message(res_recipient, res_msg)
            elif action == "save_contact":
                res = contact_manager.add_contact(nlp_res.entities.contact_name, nlp_res.entities.phone_number)
            elif action == "lookup_contact":
                contact = contact_manager.find_contact(nlp_res.entities.contact_name)
                if contact and contact.get("phone"):
                    res = f"{contact['name']} ka number {contact['phone']} hai."
                elif contact:
                    res = f"{contact['name']} contact list me hai par number save nahi hai."
                else:
                    res = f"{nlp_res.entities.contact_name} ka contact nahi mila."
            else:
                res = await call_manager.dial_contact(query_clean)

            await tts.speak(res)
            return res

        # 4. Storage Optimization & ZIP Vault Intent
        if nlp_res.intent == "STORAGE_OPTIMIZE":
            action = nlp_res.entities.action
            if action == "zip_data":
                res = compression_manager.create_data_backup()
            elif action == "extract_zip":
                res = compression_manager.extract_archive()
            elif action == "inspect_zip":
                res = compression_manager.list_archive_contents()
            elif action == "clean_storage":
                res = compression_manager.auto_optimize_storage()
            else:
                res = compression_manager.create_data_backup()
            await tts.speak(res)
            return res

        # 5. Diagnostics & Self-Healing Intent
        if nlp_res.intent == "DIAGNOSTICS":
            action = nlp_res.entities.action
            if action == "apply_fix":
                opt = nlp_res.entities.option_number or 1
                pending = list(diagnostics_engine.pending_fixes.keys())
                if pending:
                    res = diagnostics_engine.apply_solution(pending[0], opt)
                else:
                    res = "Koi pending issue nahi mila Noaman."
            else:
                res = diagnostics_engine.get_spoken_advisory_report()
            await tts.speak(res)
            return res

        # 6. Vision Screen Analysis Intent
        if nlp_res.intent == "VISION_ANALYZE":
            filepath, _ = system_control.take_screenshot()
            try:
                with open(filepath, "rb") as fp:
                    img_bytes = fp.read()
                res = await vision_analyzer.analyze_image_bytes(img_bytes, prompt=query_clean)
            except Exception as e:
                res = f"Screen analyze karte waqt issue aaya: {e}"
            await tts.speak(res)
            return res

        # 7. Media Playback & Web Search Intent
        if nlp_res.intent == "MEDIA_CONTROL":
            action = nlp_res.entities.action
            if action == "play_pause":
                res = browser_control.media_play_pause()
            elif action == "next":
                res = browser_control.media_next()
            elif action == "youtube_search" and nlp_res.entities.query:
                res = browser_control.youtube_play(nlp_res.entities.query)
            elif action == "google_search" and nlp_res.entities.query:
                res = browser_control.google_search(nlp_res.entities.query)
            else:
                res = browser_control.media_play_pause()
            await tts.speak(res)
            return res

        # 8. Cross-Device Phone Controls Intent
        if nlp_res.intent == "CROSS_DEVICE":
            action = nlp_res.entities.action
            if action == "find_phone":
                _, res = await phone_hub.ring_phone()
            elif action == "stop_ring":
                _, res = await phone_hub.stop_ring()
            elif action == "phone_battery":
                res = phone_hub.get_phone_battery_report()
            else:
                _, res = await phone_hub.ring_phone()
            await tts.speak(res)
            return res

        # 9. Call Screening & Voicemails Intent
        if nlp_res.intent == "CALL_SCREENING":
            from backend.call_screening import call_screener
            action = nlp_res.entities.action
            if action == "mark_read":
                call_screener.mark_all_as_read()
                res = "Saare voicemails read mark kar diye gaye hain."
            else:
                res = call_screener.get_summary_report()
            await tts.speak(res)
            return res

        # 10. Dynamic Skills Intent
        if nlp_res.intent == "SKILL_LEARN":
            action = nlp_res.entities.action
            if action == "teach_skill":
                s_name = nlp_res.entities.skill_name or "custom_task"
                s_desc = nlp_res.entities.skill_desc or query_clean
                res = await skill_learner.learn_skill(s_name, s_desc, s_desc)
            else:
                res = skill_learner.list_learned_skills()
            await tts.speak(res)
            return res

        # 11. Autonomous Tasks Intent
        if nlp_res.intent == "AUTONOMOUS_TASK":
            res = await autonomous_executor.execute_task(query_clean)
            await tts.speak(res)
            return res

        # 12. Check if query matches a previously learned dynamic skill
        matched_skill_name, _ = skill_learner.find_matching_skill(query_clean)
        if matched_skill_name:
            logger.info(f"Triggering dynamically learned skill: {matched_skill_name}")
            res = skill_learner.execute_skill(matched_skill_name)
            await tts.speak(res)
            return res

        # 13. Continuous Learning Check: Did Noaman teach a fact, rule, alias, or preference?
        did_learn, ack_msg = learning_engine.analyze_and_learn(query_clean)
        if did_learn and ack_msg:
            await tts.speak(ack_msg)
            return ack_msg

        # 14. File Creation Intent
        if "file banao" in query_lower or "create file" in query_lower or "note banao" in query_lower:
            from backend.tools.file_manager import file_manager
            filename = re.sub(r"\b(file|banao|create|note|par|desktop|pe|karo)\b", "", query_lower).strip()
            filename = filename or "mj_notes"
            res = file_manager.create_text_file(filename, content=f"Created by MJ for {USER_NAME}.\n")
            await tts.speak(res)
            return res

        # 15. General AI Conversation, Reasoning & Companionship
        response = await llm.generate_response(query_clean)
        await tts.speak(response)
        return response


# Global instance
orchestrator = AssistantOrchestrator()
