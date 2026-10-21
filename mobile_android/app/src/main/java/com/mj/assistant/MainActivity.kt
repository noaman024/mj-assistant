package com.mj.assistant

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.mj.assistant.bridge.AndroidBridge
import com.mj.assistant.services.MJForegroundService

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var bridge: AndroidBridge
    private var speechRecognizer: SpeechRecognizer? = null

    private val PERMISSIONS_REQUEST_CODE = 101

    private val requiredPermissions: Array<String>
        get() {
            val list = mutableListOf(
                Manifest.permission.RECORD_AUDIO,
                Manifest.permission.CALL_PHONE,
                Manifest.permission.CAMERA
            )
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                list.add(Manifest.permission.BLUETOOTH_CONNECT)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                list.add(Manifest.permission.POST_NOTIFICATIONS)
            }
            return list.toTypedArray()
        }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        checkAndRequestPermissions()
        startBackgroundService()

        webView = findViewById(R.id.webViewCockpit)
        setupWebView()

        handleIncomingIntent(intent)

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    finish()
                }
            }
        })
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncomingIntent(intent)
    }

    private fun handleIncomingIntent(intent: Intent?) {
        if (intent == null) return

        // 1. Deep Link (e.g. mj://command?query=...)
        val data: Uri? = intent.data
        if (data != null && (data.scheme == "mj" || data.scheme == "https")) {
            val query = data.getQueryParameter("query") ?: data.getQueryParameter("cmd")
            if (!query.isNullOrEmpty()) {
                val escaped = escapeJs(query)
                webView.postDelayed({
                    evalJs("window.dispatchCommand && window.dispatchCommand('$escaped');")
                }, 1200)
                return
            }
        }

        // 2. Broadcast / Wake Action
        if (intent.action == "com.mj.assistant.TRIGGER_WAKE") {
            webView.postDelayed({
                startVoiceListening()
            }, 800)
        } else if (intent.action == "com.mj.assistant.EXECUTE_COMMAND") {
            val query = intent.getStringExtra("query")
            if (!query.isNullOrEmpty()) {
                val escaped = escapeJs(query)
                webView.postDelayed({
                    evalJs("window.dispatchCommand && window.dispatchCommand('$escaped');")
                }, 1200)
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        settings.databaseEnabled = true
        settings.mediaPlaybackRequiresUserGesture = false
        settings.cacheMode = WebSettings.LOAD_DEFAULT

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        }

        bridge = AndroidBridge(this, webView)
        webView.addJavascriptInterface(bridge, "AndroidBridge")

        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest?) {
                request?.grant(request.resources)
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
            }
        }

        webView.loadUrl("file:///android_asset/www/index.html")
    }

    private fun checkAndRequestPermissions() {
        val missingPermissions = requiredPermissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missingPermissions.toTypedArray(), PERMISSIONS_REQUEST_CODE)
        }
    }

    private fun startBackgroundService() {
        try {
            val serviceIntent = Intent(this, MJForegroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent)
            } else {
                startService(serviceIntent)
            }
        } catch (_: Exception) {}
    }

    fun startVoiceListening() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            Toast.makeText(this, "Speech recognition not available", Toast.LENGTH_SHORT).show()
            return
        }

        runOnUiThread {
            speechRecognizer?.destroy()
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)

            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-IN")
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            }

            speechRecognizer?.setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) {
                    bridge.vibrate(30)
                    evalJs("window.onSpeechStatus && window.onSpeechStatus('listening');")
                }

                override fun onRmsChanged(rmsdB: Float) {
                    // Normalize -2dB to 10dB into 0 to 100 percentage for UI Visualizer
                    val normalized = ((rmsdB + 2.0f) / 12.0f * 100.0f).coerceIn(0.0f, 100.0f).toInt()
                    evalJs("window.onMicAmplitude && window.onMicAmplitude($normalized);")
                }

                override fun onResults(results: Bundle?) {
                    val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    val spoken = matches?.firstOrNull() ?: ""
                    evalJs("window.onMicAmplitude && window.onMicAmplitude(0);")
                    if (spoken.isNotEmpty()) {
                        val escaped = escapeJs(spoken)
                        evalJs("window.onNativeVoiceResult && window.onNativeVoiceResult('$escaped');")
                    } else {
                        evalJs("window.onSpeechStatus && window.onSpeechStatus('idle');")
                    }
                }

                override fun onError(error: Int) {
                    evalJs("window.onMicAmplitude && window.onMicAmplitude(0);")
                    evalJs("window.onSpeechStatus && window.onSpeechStatus('idle');")
                }

                override fun onBeginningOfSpeech() {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onEndOfSpeech() {
                    evalJs("window.onMicAmplitude && window.onMicAmplitude(0);")
                }
                override fun onPartialResults(partialResults: Bundle?) {}
                override fun onEvent(eventType: Int, params: Bundle?) {}
            })

            speechRecognizer?.startListening(intent)
        }
    }

    private fun escapeJs(str: String): String {
        return str.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\"", "\\\"")
            .replace("\n", " ")
    }

    private fun evalJs(script: String) {
        runOnUiThread {
            webView.evaluateJavascript(script, null)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        speechRecognizer?.destroy()
    }
}
