package com.mj.assistant

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.mj.assistant.bridge.DualModeBridge
import com.mj.assistant.services.MJForegroundService
import com.mj.assistant.tools.DirectCallManager
import kotlinx.coroutines.launch
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private lateinit var bridge: DualModeBridge
    private lateinit var callManager: DirectCallManager
    private var speechRecognizer: SpeechRecognizer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        bridge = DualModeBridge(this)
        callManager = DirectCallManager(this)

        // 1. Start 24/7 Background Service
        startBackgroundService()

        // 2. Initialize UI Hooks
        val txtStatus = findViewById<TextView>(R.id.txtConnectionStatus)
        val txtResponse = findViewById<TextView>(R.id.txtAssistantResponse)
        val editInput = findViewById<EditText>(R.id.editCommand)
        val btnSend = findViewById<Button>(R.id.btnSend)
        val btnMic = findViewById<Button>(R.id.btnMic)

        // Check Laptop connection
        lifecycleScope.launch {
            val connected = bridge.checkLaptopConnection()
            txtStatus.text = if (connected) "🟢 LAPTOP BRIDGE ONLINE" else "🔵 STANDALONE PHONE MODE"
        }

        btnSend.setOnClickListener {
            val cmd = editInput.text.toString().trim()
            if (cmd.isNotEmpty()) {
                txtResponse.text = "Thinking..."
                lifecycleScope.launch {
                    val reply = bridge.dispatchCommand(cmd)
                    txtResponse.text = reply
                }
                editInput.setText("")
            }
        }

        btnMic.setOnClickListener {
            startVoiceListening(txtResponse)
        }
    }

    private fun startBackgroundService() {
        val serviceIntent = Intent(this, MJForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }

    private fun startVoiceListening(displayView: TextView) {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            Toast.makeText(this, "Speech recognition not available", Toast.LENGTH_SHORT).show()
            return
        }

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN")
        }

        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                displayView.text = "🎙️ Sun rahi hu Noaman... Boliye"
            }
            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val spoken = matches?.firstOrNull() ?: ""
                if (spoken.isNotEmpty()) {
                    displayView.text = "You: $spoken"
                    lifecycleScope.launch {
                        val reply = bridge.dispatchCommand(spoken)
                        displayView.text = reply
                    }
                }
            }
            override fun onError(error: Int) {
                displayView.text = "Voice error: $error"
            }
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}
            override fun onPartialResults(partialResults: Bundle?) {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })

        speechRecognizer?.startListening(intent)
    }

    override fun onDestroy() {
        super.onDestroy()
        speechRecognizer?.destroy()
    }
}
