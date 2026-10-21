package com.mj.assistant.tools

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.hardware.camera2.CameraManager
import android.media.AudioManager
import android.net.wifi.WifiManager
import android.os.Build
import android.net.Uri
import android.provider.MediaStore
import android.provider.Settings
import android.widget.Toast

class DeviceController(private val context: Context) {

    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
    private var isTorchActive = false

    private val knownAppPackages = mapOf(
        "whatsapp" to "com.whatsapp",
        "youtube" to "com.google.android.youtube",
        "yt" to "com.google.android.youtube",
        "chrome" to "com.android.chrome",
        "browser" to "com.android.chrome",
        "spotify" to "com.spotify.music",
        "maps" to "com.google.android.apps.maps",
        "instagram" to "com.instagram.android",
        "telegram" to "org.telegram.messenger",
        "gmail" to "com.google.android.gm",
        "calculator" to "com.google.android.calculator",
        "camera" to "camera_intent",
        "settings" to "settings_intent",
        "photos" to "com.google.android.apps.photos",
        "gallery" to "com.google.android.apps.photos",
        "files" to "com.google.android.documentsui",
        "clock" to "com.google.android.deskclock",
        "playstore" to "com.android.vending",
        "store" to "com.android.vending",
        "phonepe" to "com.phonepe.app",
        "gpay" to "com.google.android.apps.nbu.paisa.user",
        "paytm" to "net.one97.paytm"
    )

    fun launchApp(appNameOrPackage: String): Boolean {
        val query = appNameOrPackage.lowercase().trim()
        val pkg = knownAppPackages[query] ?: query

        // 1. Try launching by explicit package name if not a virtual intent
        val pm: PackageManager = context.packageManager
        if (!pkg.endsWith("_intent")) {
            val launchIntent = pm.getLaunchIntentForPackage(pkg)
            if (launchIntent != null) {
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                context.startActivity(launchIntent)
                return true
            }
        }

        // 2. Specific fallback for YouTube (Uri scheme ensures it opens even without package visibility)
        if (query.contains("youtube") || query == "yt" || pkg.contains("youtube")) {
            try {
                val ytIntent = Intent(Intent.ACTION_VIEW, Uri.parse("vnd.youtube:")).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                context.startActivity(ytIntent)
                return true
            } catch (_: Exception) {
                try {
                    val webIntent = Intent(Intent.ACTION_VIEW, Uri.parse("https://www.youtube.com")).apply {
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    context.startActivity(webIntent)
                    return true
                } catch (_: Exception) {}
            }
        }

        // 3. Fallbacks for system intent actions
        if (query.contains("camera") || pkg == "camera_intent") {
            return try {
                val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                context.startActivity(intent)
                true
            } catch (_: Exception) { false }
        }

        if (query.contains("setting") || pkg == "settings_intent") {
            return try {
                val intent = Intent(Settings.ACTION_SETTINGS).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                context.startActivity(intent)
                true
            } catch (_: Exception) { false }
        }

        // 4. Try scanning all installed applications by name / label
        try {
            val apps = pm.getInstalledApplications(PackageManager.GET_META_DATA)
            for (app in apps) {
                val label = pm.getApplicationLabel(app).toString().lowercase()
                if (label.contains(query) || app.packageName.lowercase().contains(query)) {
                    val intent = pm.getLaunchIntentForPackage(app.packageName)
                    if (intent != null) {
                        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        context.startActivity(intent)
                        return true
                    }
                }
            }
        } catch (_: Exception) {}

        return false
    }

    fun setTorch(enable: Boolean): Boolean {
        return try {
            val cameraId = cameraManager.cameraIdList.firstOrNull() ?: return false
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                cameraManager.setTorchMode(cameraId, enable)
                isTorchActive = enable
                true
            } else {
                false
            }
        } catch (e: Exception) {
            false
        }
    }

    fun isTorchOn(): Boolean = isTorchActive

    fun volumeUp(): Int {
        audioManager.adjustStreamVolume(
            AudioManager.STREAM_MUSIC,
            AudioManager.ADJUST_RAISE,
            AudioManager.FLAG_SHOW_UI
        )
        return getVolumePercent()
    }

    fun volumeDown(): Int {
        audioManager.adjustStreamVolume(
            AudioManager.STREAM_MUSIC,
            AudioManager.ADJUST_LOWER,
            AudioManager.FLAG_SHOW_UI
        )
        return getVolumePercent()
    }

    fun setVolume(percent: Int): Int {
        val maxVol = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
        val target = ((percent.coerceIn(0, 100) / 100.0) * maxVol).toInt()
        audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, target, AudioManager.FLAG_SHOW_UI)
        return getVolumePercent()
    }

    fun muteVolume(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, AudioManager.FLAG_SHOW_UI)
        } else {
            @Suppress("DEPRECATION")
            audioManager.setStreamMute(AudioManager.STREAM_MUSIC, true)
        }
        return true
    }

    fun unmuteVolume(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, AudioManager.FLAG_SHOW_UI)
        } else {
            @Suppress("DEPRECATION")
            audioManager.setStreamMute(AudioManager.STREAM_MUSIC, false)
        }
        return true
    }

    fun getVolumePercent(): Int {
        val current = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC)
        val max = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
        return if (max > 0) ((current.toFloat() / max.toFloat()) * 100).toInt() else 0
    }

    fun openWifiSettings(): Boolean {
        return try {
            val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                Intent(Settings.Panel.ACTION_WIFI).apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }
            } else {
                Intent(Settings.ACTION_WIFI_SETTINGS).apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }
            }
            context.startActivity(intent)
            true
        } catch (e: Exception) {
            false
        }
    }

    fun openBluetoothSettings(): Boolean {
        return try {
            val intent = Intent(Settings.ACTION_BLUETOOTH_SETTINGS).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(intent)
            true
        } catch (e: Exception) {
            false
        }
    }
}
