import os
import time
import logging
from backend.config.settings import USER_NAME

logger = logging.getLogger("MJ.Security")

DEFAULT_SECRET_PASSCODE = os.getenv("SECRET_PASSCODE", "jarvis").strip().lower()

class SecurityVault:
    """Manages secret passphrase authentication and protection for private actions & data"""

    def __init__(self):
        self.secret_passcode = DEFAULT_SECRET_PASSCODE
        self.authenticated_until = 0.0
        self.awaiting_passcode_for = None  # Action pending authentication

    def is_unlocked(self) -> bool:
        """Returns True if vault is currently unlocked within session timeout"""
        return time.time() < self.authenticated_until

    def authenticate(self, spoken_word: str) -> tuple[bool, str]:
        """Validates spoken passphrase from user"""
        clean_input = spoken_word.strip().lower()

        # Check match with configured secret passcode
        if self.secret_passcode in clean_input or clean_input in self.secret_passcode:
            self.authenticated_until = time.time() + 300  # 5 minutes session window
            pending = self.awaiting_passcode_for
            self.awaiting_passcode_for = None
            logger.info("Security Vault: Access Granted via secret passphrase.")
            return True, f"Access Granted Noaman! Vault unlock ho gaya hai. Ab aap '{pending or 'protected actions'}' access kar sakte hain."
        else:
            logger.warning(f"Security Vault: Invalid secret passphrase attempt: '{spoken_word}'")
            return False, "Access Denied Noaman! Secret passphrase match nahi hua."

    def challenge_action(self, action_name: str) -> tuple[bool, str]:
        """Checks if action is permitted or requires secret passcode challenge"""
        if self.is_unlocked():
            return True, ""

        self.awaiting_passcode_for = action_name
        return False, f"Noaman, yeh action private aur protected hai. Kripya authentication ke liye apna Secret Word boliye."

    def lock_vault(self) -> str:
        """Manually locks the privacy vault immediately"""
        self.authenticated_until = 0.0
        self.awaiting_passcode_for = None
        return "Privacy Vault lock kar diya gaya hai Noaman. Saari private files aur actions protected hain."

# Global instance
security_vault = SecurityVault()
