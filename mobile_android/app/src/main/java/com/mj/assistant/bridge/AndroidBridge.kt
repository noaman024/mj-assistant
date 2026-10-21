package com.mj.assistant.bridge

import android.content.Context
import android.os.BatteryManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.Toast
import com.mj.assistant.MainActivity
import com.mj.assistant.tools.AudioStreamManager
import com.mj.assistant.tools.DeviceController
import com.mj.assistant.tools.DirectCallManager

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
    private val deviceController = DeviceController(activity)
    private val audioStreamManager = AudioStreamManager(activity)

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
    fun launchApp(appNameOrPackage: String): Boolean {
        vibrate(40)
        return deviceController.launchApp(appNameOrPackage)
    }

    @JavascriptInterface
    fun toggleTorch(enable: Boolean): Boolean {
        vibrate(40)
        return deviceController.setTorch(enable)
    }

    @JavascriptInterface
    fun isTorchActive(): Boolean {
        return deviceController.isTorchOn()
    }

    @JavascriptInterface
    fun volumeUp(): Int {
        vibrate(30)
        return deviceController.volumeUp()
    }

    @JavascriptInterface
    fun volumeDown(): Int {
        vibrate(30)
        return deviceController.volumeDown()
    }

    @JavascriptInterface
    fun setVolume(percent: Int): Int {
        vibrate(30)
        return deviceController.setVolume(percent)
    }

    @JavascriptInterface
    fun mute(): Boolean {
        vibrate(30)
        return deviceController.muteVolume()
    }

    @JavascriptInterface
    fun unmute(): Boolean {
        vibrate(30)
        return deviceController.unmuteVolume()
    }

    @JavascriptInterface
    fun getVolume(): Int {
        return deviceController.getVolumePercent()
    }

    @JavascriptInterface
    fun openBluetoothSettings(): Boolean {
        vibrate(30)
        return deviceController.openBluetoothSettings()
    }

    @JavascriptInterface
    fun openWifiSettings(): Boolean {
        vibrate(30)
        return deviceController.openWifiSettings()
    }

    @JavascriptInterface
    fun playTTSAudio(url: String) {
        activity.runOnUiThread {
            audioStreamManager.playTTSStream(url) {
                activity.runOnUiThread {
                    webView.evaluateJavascript("window.onAudioStreamFinished && window.onAudioStreamFinished();", null)
                }
            }
        }
    }

    @JavascriptInterface
    fun stopTTSAudio() {
        audioStreamManager.stopAudio()
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
            q.contains("volume up") || q.contains("awaz badhao") -> {
                val v = volumeUp()
                "Media volume $v percent kar diya hai."
            }
            q.contains("volume down") || q.contains("awaz kam") -> {
                val v = volumeDown()
                "Media volume $v percent kar diya hai."
            }
            q.contains("mute") -> {
                mute()
                "Phone mute kar diya hai."
            }
            q.contains("unmute") -> {
                unmute()
                "Phone unmute kar diya hai."
            }
            q.contains("bluetooth") -> {
                openBluetoothSettings()
                "Bluetooth settings open kar di hain Noaman."
            }
            q.contains("wifi") || q.contains("wi-fi") -> {
                openWifiSettings()
                "Wi-Fi panel open kar diya hai Noaman."
            }
            q.startsWith("open ") || q.startsWith("launch ") -> {
                val target = q.removePrefix("open ").removePrefix("launch ").trim()
                if (launchApp(target)) {
                    "$target open kar rahi hu Noaman!"
                } else {
                    "$target app install nahi mila Noaman."
                }
            }
            q.contains("call") -> {
                "Calling feature active hai Noaman. Number dial kijiye ya Calls tab use kijiye."
            }
            q.contains("kaise ho") || q.contains("kya haal") -> {
                "Main bilkul theek hu Noaman! Aap bataiye, main aapki kya help kar sakti hu?"
            }
            else -> {
                "Sun rahi hu Noaman! Laptop se offline hu, par saare phone controls bilkul ready hain."
            }
        }
    }
}
