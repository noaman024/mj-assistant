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
    fun reloadInterface() {
        activity.runOnUiThread {
            webView.reload()
        }
    }

    @JavascriptInterface
    fun loadLiveServer() {
        val host = getLaptopIp()
        activity.runOnUiThread {
            webView.loadUrl("http://$host/")
        }
    }

    @JavascriptInterface
    fun loadOfflineAsset() {
        activity.runOnUiThread {
            webView.loadUrl("file:///android_asset/www/index.html")
        }
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
    fun speakNative(text: String) {
        activity.speak(text)
    }

    @JavascriptInterface
    fun dispatchLocalCommand(query: String): String {
        val q = query.lowercase().trim()
        val reply = parseAndExecuteLocal(q)

        activity.runOnUiThread {
            try {
                Toast.makeText(activity, reply, Toast.LENGTH_SHORT).show()
            } catch (_: Exception) {}
        }
        activity.speak(reply)
        return reply
    }

    private fun parseAndExecuteLocal(q: String): String {
        // 1. YouTube Commands (English + Hindi / Hinglish)
        if (q.contains("youtube") || q.contains("yt") || q.contains("yu tube") || q.contains("yutube")) {
            deviceController.launchApp("youtube")
            return "YouTube open kar rahi hu Noaman!"
        }

        // 2. WhatsApp Commands
        if (q.contains("whatsapp") || q.contains("wa ") || q.endsWith(" wa")) {
            if (q.contains("message") || q.contains("bhejo") || q.contains("send")) {
                return "WhatsApp message bhejne ke liye Calls tab me number aur message enter karein Noaman."
            }
            deviceController.launchApp("whatsapp")
            return "WhatsApp open kar rahi hu Noaman!"
        }

        // 3. Torch / Flashlight
        if (q.contains("torch") || q.contains("flashlight") || q.contains("falsh")) {
            return if (q.contains("off") || q.contains("band") || q.contains("bujhao") || q.contains("roko")) {
                toggleTorch(false)
                "Torch off kar di hai Noaman."
            } else {
                toggleTorch(true)
                "Torch on kar di hai Noaman!"
            }
        }

        // 4. Volume Up / Badhao
        if (q.contains("volume up") || q.contains("awaz badhao") || q.contains("aawaz badhao") ||
            q.contains("sound badhao") || q.contains("tez karo") || q.contains("volume badha")) {
            val v = volumeUp()
            return "Media volume $v percent kar diya hai Noaman."
        }

        // 5. Volume Down / Kam karo
        if (q.contains("volume down") || q.contains("awaz kam") || q.contains("aawaz kam") ||
            q.contains("sound kam") || q.contains("dheema") || q.contains("volume ghata")) {
            val v = volumeDown()
            return "Media volume $v percent kar diya hai Noaman."
        }

        // 6. Mute / Silent
        if (q.contains("mute") || q.contains("silent") || q.contains("shant")) {
            mute()
            return "Phone silent kar diya hai Noaman."
        }

        // 7. Unmute
        if (q.contains("unmute") || q.contains("silent hatao")) {
            unmute()
            return "Phone unmute kar diya hai Noaman."
        }

        // 8. Bluetooth
        if (q.contains("bluetooth")) {
            openBluetoothSettings()
            return "Bluetooth settings open kar di hain Noaman."
        }

        // 9. Wi-Fi
        if (q.contains("wifi") || q.contains("wi-fi")) {
            openWifiSettings()
            return "Wi-Fi settings open kar di hain Noaman."
        }

        // 10. Camera
        if (q.contains("camera") || q.contains("photo") || q.contains("selfie")) {
            deviceController.launchApp("camera")
            return "Camera open kar rahi hu Noaman!"
        }

        // 11. Chrome / Browser
        if (q.contains("chrome") || q.contains("browser") || q.contains("google")) {
            deviceController.launchApp("chrome")
            return "Chrome browser open kar rahi hu Noaman!"
        }

        // 12. Music / Spotify
        if (q.contains("spotify") || q.contains("music") || q.contains("gana")) {
            deviceController.launchApp("spotify")
            return "Music player open kar rahi hu Noaman!"
        }

        // 13. Calculator
        if (q.contains("calculator") || q.contains("hisab")) {
            deviceController.launchApp("calculator")
            return "Calculator open kar rahi hu Noaman!"
        }

        // 14. Settings
        if (q.contains("setting")) {
            deviceController.launchApp("settings")
            return "Settings open kar rahi hu Noaman!"
        }

        // 15. Battery
        if (q.contains("battery") || q.contains("charge") || q.contains("charging") || q.contains("batt")) {
            val batt = getBatteryLevel()
            return "Phone battery level $batt percent hai Noaman."
        }

        // 16. General App Launcher (Strip filler words)
        if (q.contains("open") || q.contains("kholo") || q.contains("chalao") ||
            q.contains("launch") || q.contains("start")) {
            var target = q
            val stopWords = listOf(
                "open", "kholo", "chalao", "launch", "start", "karo", "kar", "do", "de",
                "phone", "me", "mein", "ke", "andar", "anda", "app", "application", "please", "zara", "ko"
            )
            for (sw in stopWords) {
                target = target.replace(Regex("\\b$sw\\b"), " ")
            }
            target = target.trim()
            if (target.isNotEmpty() && deviceController.launchApp(target)) {
                return "$target open kar rahi hu Noaman!"
            }
        }

        // 17. Conversational queries
        if (q.contains("kaise ho") || q.contains("kaisi ho") || q.contains("kya haal") || q.contains("kya chal raha")) {
            return "Main bilkul theek hu Noaman! Aap bataiye, main aapki kya help kar sakti hu?"
        }
        if (q.contains("hi") || q.contains("hey") || q.contains("hello") || q.contains("mj")) {
            return "Haan Noaman, sun rahi hu! Boliye kya madat karu?"
        }
        if (q.contains("shukriya") || q.contains("thanks") || q.contains("thank you")) {
            return "Always welcome Noaman! Main hamesha aapke sath hu."
        }
        if (q.contains("kya kar sakti ho") || q.contains("help") || q.contains("features")) {
            return "Main phone me YouTube, WhatsApp, Torch, Volume control aur apps launch kar sakti hu Noaman!"
        }

        return "Sun rahi hu Noaman! Laptop se offline hu, par saare phone controls bilkul ready hain."
    }
}
