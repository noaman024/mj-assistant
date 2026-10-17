package com.mj.assistant.bridge

import android.content.Context
import android.content.Intent
import android.hardware.camera2.CameraManager
import android.os.BatteryManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.Toast
import com.mj.assistant.MainActivity
import com.mj.assistant.tools.DirectCallManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * JavaScript Bridge exposed as `window.AndroidBridge` inside WebView.
 * Connects the Futuristic Holographic Cockpit directly to Native Android Superpowers.
 */
class AndroidBridge(
    private val activity: MainActivity,
    private val webView: WebView
) {
    private val prefs = activity.getSharedPreferences("mj_prefs", Context.MODE_PRIVATE)
    private val callManager = DirectCallManager(activity)
    private var isTorchOn = false

    @JavascriptInterface
    fun getLaptopIp(): String {
        return prefs.getString("laptop_ip", "10.35.126.235:8000") ?: "10.35.126.235:8000"
    }

    @JavascriptInterface
    fun setLaptopIp(ip: String) {
        val cleanIp = ip.trim().removePrefix("http://").removePrefix("https://").trimEnd('/')
        prefs.edit().putString("laptop_ip", cleanIp).apply()
        showToast("Laptop IP saved: $cleanIp")
    }

    @JavascriptInterface
    fun makeCall(phoneNumber: String): Boolean {
        vibrate(50)
        return callManager.callNumber(phoneNumber)
    }

    @JavascriptInterface
    fun sendWhatsApp(phoneNumber: String, message: String): Boolean {
        vibrate(50)
        return callManager.sendWhatsApp(phoneNumber, message)
    }

    @JavascriptInterface
    fun startVoiceRecognition() {
        activity.runOnUiThread {
            activity.startVoiceListening()
        }
    }

    @JavascriptInterface
    fun toggleTorch(enable: Boolean): Boolean {
        return try {
            val cameraManager = activity.getSystemService(Context.CAMERA_SERVICE) as CameraManager
            val cameraId = cameraManager.cameraIdList[0]
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                cameraManager.setTorchMode(cameraId, enable)
                isTorchOn = enable
                vibrate(40)
                true
            } else {
                false
            }
        } catch (e: Exception) {
            false
        }
    }

    @JavascriptInterface
    fun isTorchActive(): Boolean {
        return isTorchOn
    }

    @JavascriptInterface
    fun getBatteryLevel(): Int {
        val bm = activity.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        return bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }

    @JavascriptInterface
    fun showToast(message: String) {
        activity.runOnUiThread {
            Toast.makeText(activity, message, Toast.LENGTH_SHORT).show()
        }
    }

    @JavascriptInterface
    fun vibrate(durationMs: Long) {
        try {
            val vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                vibrator.vibrate(durationMs)
            }
        } catch (_: Exception) {}
    }

    @JavascriptInterface
    fun dispatchLocalCommand(query: String): String {
        val q = query.lowercase().trim()
        return when {
            q.contains("battery") -> {
                val batt = getBatteryLevel()
                "Phone battery level $batt percent hai Noaman."
            }
            q.contains("torch on") || q.contains("flashlight on") -> {
                toggleTorch(true)
                "Torch on kar di hai Noaman!"
            }
            q.contains("torch off") || q.contains("flashlight off") -> {
                toggleTorch(false)
                "Torch off kar di hai."
            }
            q.contains("call") -> {
                "Calling feature active hai Noaman. Number dial kijiye ya Calls tab use kijiye."
            }
            q.contains("kaise ho") || q.contains("kya haal") -> {
                "Main bilkul theek hu Noaman! Aap bataiye, main aapki kya help kar sakti hu?"
            }
            else -> {
                "Sun rahi hu Noaman! Laptop abhi connect nahi hua hai, to main phone mode me operate kar rahi hu."
            }
        }
    }
}
