package com.mj.assistant.services

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.hardware.camera2.CameraManager
import android.media.AudioManager
import android.os.BatteryManager

class PhoneHardwareController(private val context: Context) {

    private val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private var isTorchOn = false

    fun toggleTorch(enable: Boolean? = null): String {
        return try {
            val cameraId = cameraManager.cameraIdList[0]
            val newState = enable ?: !isTorchOn
            cameraManager.setTorchMode(cameraId, newState)
            isTorchOn = newState
            if (isTorchOn) "Flashlight on kar di hai Noaman." else "Flashlight band kar di hai Noaman."
        } catch (e: Exception) {
            "Flashlight control karte waqt error: ${e.message}"
        }
    }

    fun volumeUp(): String {
        audioManager.adjustVolume(AudioManager.ADJUST_RAISE, AudioManager.FLAG_SHOW_UI)
        return "Phone ka volume badha diya hai Noaman."
    }

    fun volumeDown(): String {
        audioManager.adjustVolume(AudioManager.ADJUST_LOWER, AudioManager.FLAG_SHOW_UI)
        return "Phone ka volume kam kar diya hai Noaman."
    }

    fun getBatteryStatus(): String {
        val ifilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        val batteryStatus = context.registerReceiver(null, ifilter)
        val level = batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryStatus?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        val batteryPct = if (level != -1 && scale != -1) (level * 100 / scale.toFloat()).toInt() else 0

        val status = batteryStatus?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                status == BatteryManager.BATTERY_STATUS_FULL

        val state = if (isCharging) "charging ho rahi hai" else "battery par hai"
        return "Noaman, phone ki battery $batteryPct% hai aur $state."
    }
}
