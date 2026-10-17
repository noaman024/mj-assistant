package com.mj.assistant.core

import android.content.Context
import com.mj.assistant.bridge.LaptopDiscovery
import com.mj.assistant.bridge.LaptopWebSocketClient
import com.mj.assistant.services.CallManager
import com.mj.assistant.services.MJAccessibilityService
import com.mj.assistant.services.PhoneHardwareController
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

enum class AssistantMode {
    STANDALONE_PHONE,
    JARVIS_LAPTOP_BRIDGE
}

class DualModeManager(
    private val context: Context,
    geminiApiKey: String,
    preferredLaptopIp: String? = null
) {
    val discovery = LaptopDiscovery(context)
    val laptopClient = LaptopWebSocketClient()
    val geminiClient = GeminiMobileClient(geminiApiKey)
    val callManager = CallManager(context)
    val hardware = PhoneHardwareController(context)

    private val _currentMode = MutableStateFlow(AssistantMode.STANDALONE_PHONE)
    val currentMode: StateFlow<AssistantMode> = _currentMode

    var preferredIp: String? = preferredLaptopIp

    suspend fun refreshConnectionState(): AssistantMode {
        val reachable = discovery.checkLaptopReachability(preferredIp)
        _currentMode.value = if (reachable) {
            AssistantMode.JARVIS_LAPTOP_BRIDGE
        } else {
            AssistantMode.STANDALONE_PHONE
        }
        return _currentMode.value
    }

    suspend fun processCommand(query: String): String {
        val q = query.trim().lowercase()
        if (q.isBlank()) return ""

        // 1. Phone Calling Commands (Always execute locally on Phone)
        if (q.contains("call karo") || q.contains("call lagao") || q.startsWith("call ") || q.contains("dial karo")) {
            val contactCandidate = q.replace("call karo", "")
                .replace("call lagao", "")
                .replace("call", "")
                .replace("ko", "")
                .trim()
            return callManager.dial(contactCandidate)
        }

        // 2. WhatsApp Messaging Commands (Always execute locally on Phone via Accessibility)
        if (q.contains("whatsapp") && (q.contains("bhejo") || q.contains("message") || q.contains("bolo"))) {
            val parts = query.split(Regex("(?i)ko|ki|message|bolo|bhejo"), 3)
            val recipient = if (parts.isNotEmpty()) parts[0].replace("whatsapp", "", true).trim() else "Rahul"
            val messageText = if (parts.size > 1) parts.last().trim() else "Meeting me hu"
            MJAccessibilityService.sendWhatsAppMessage(context, recipient, messageText)
            return "Noaman, $recipient ko WhatsApp par '$messageText' send kiya ja raha hai."
        }

        // 3. Native Phone Hardware Commands
        if (q.contains("torch") || q.contains("flashlight")) {
            val enable = !q.contains("band") && !q.contains("off")
            return hardware.toggleTorch(enable)
        }
        if (q.contains("volume badhao") || q.contains("volume up")) {
            return hardware.volumeUp()
        }
        if (q.contains("volume kam") || q.contains("volume down")) {
            return hardware.volumeDown()
        }
        if (q.contains("phone battery") || q.contains("phone charge")) {
            return hardware.getBatteryStatus()
        }

        // 4. Laptop Specific Intent (YouTube, Diagnostics, Laptop Lock, Desktop Files)
        val isLaptopIntent = q.contains("laptop") || q.contains("computer") || q.contains("pc") ||
                q.contains("desktop") || q.contains("diagnostics") || q.contains("youtube")

        refreshConnectionState()

        if (_currentMode.value == AssistantMode.JARVIS_LAPTOP_BRIDGE) {
            val ip = discovery.activeLaptopIp
            if (ip != null) {
                return laptopClient.executeRemoteCommand(ip, query)
            }
        } else if (isLaptopIntent) {
            return "Noaman, laptop abhi offline hai. Par main aapke phone ke saare kaam kar sakti hu!"
        }

        // 5. Standalone AI Reasoning Fallback (Runs direct via Gemini API on 4G/5G)
        return geminiClient.generateResponse(query)
    }
}
