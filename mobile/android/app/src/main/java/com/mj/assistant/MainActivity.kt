package com.mj.assistant

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.mj.assistant.core.AssistantMode
import com.mj.assistant.core.DualModeManager
import com.mj.assistant.core.VoiceEngine
import com.mj.assistant.services.BackgroundWakeService
import com.mj.assistant.ui.screens.ChatMessage
import com.mj.assistant.ui.screens.CockpitScreen
import com.mj.assistant.ui.theme.MJTheme
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private lateinit var dualModeManager: DualModeManager
    private lateinit var voiceEngine: VoiceEngine

    // Dynamic state
    private val messages = mutableStateListOf<ChatMessage>()
    private var isListening by mutableStateOf(false)

    // Permission launcher
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        // Permissions handled
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request vital Jarvis permissions
        requestRequiredPermissions()

        // Initialize Dual-Mode Manager
        val geminiApiKey = "" // Enter your Gemini API Key or load from local secure storage
        dualModeManager = DualModeManager(this, geminiApiKey)

        // Initialize Voice Engine
        voiceEngine = VoiceEngine(this) { spokenQuery ->
            handleUserCommand(spokenQuery)
        }

        // Start 24/7 Background Wake Service
        try {
            val serviceIntent = Intent(this, BackgroundWakeService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent)
            } else {
                startService(serviceIntent)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        // Periodic network probe for laptop connectivity (every 10s)
        lifecycleScope.launch {
            while (true) {
                dualModeManager.refreshConnectionState()
                delay(10000)
            }
        }

        // Welcome message
        messages.add(
            ChatMessage(
                sender = "MJ",
                text = "Hey Noaman! MJ Mobile Cockpit online hai. Boliye ya type kijiye, main ready hu.",
                isUser = false
            )
        )

        setContent {
            MJTheme {
                val currentMode by dualModeManager.currentMode.collectAsState()
                val laptopIp = dualModeManager.discovery.activeLaptopIp

                CockpitScreen(
                    currentMode = currentMode,
                    laptopIp = laptopIp,
                    chatMessages = messages,
                    isListening = isListening,
                    onMicClick = {
                        if (isListening) {
                            voiceEngine.stopListening()
                            isListening = false
                        } else {
                            voiceEngine.startListening()
                            isListening = true
                        }
                    },
                    onSendCommand = { cmd ->
                        handleUserCommand(cmd)
                    }
                )
            }
        }
    }

    private fun handleUserCommand(cmd: String) {
        if (cmd.isBlank()) return
        messages.add(ChatMessage("Noaman", cmd, isUser = true))

        lifecycleScope.launch {
            val response = dualModeManager.processCommand(cmd)
            messages.add(ChatMessage("MJ", response, isUser = false))
            voiceEngine.speak(response)
        }
    }

    private fun requestRequiredPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.CALL_PHONE,
            Manifest.permission.READ_CONTACTS
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val needed = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (needed.isNotEmpty()) {
            requestPermissionLauncher.launch(needed.toTypedArray())
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        voiceEngine.destroy()
        dualModeManager.laptopClient.disconnect()
    }
}
