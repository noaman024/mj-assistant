package com.mj.assistant.services

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.core.app.NotificationCompat
import com.mj.assistant.MainActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.math.sqrt

class MJForegroundService : Service() {

    private var wakeLock: PowerManager.WakeLock? = null
    private val CHANNEL_ID = "mj_foreground_channel"
    private val NOTIF_ID = 1001
    private val TAG = "MJ.ForegroundService"

    private var listenerJob: Job? = null
    private var isListeningWakeWord = false

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()

        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "MJAssistant::ContinuousListening")
        wakeLock?.acquire(24 * 60 * 60 * 1000L) // 24 hours keep-alive

        val notification = buildForegroundNotification()
        startForeground(NOTIF_ID, notification)

        startWakeWordListener()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "MJ Assistant 24/7 Engine",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps MJ wake-word engine and remote bridge alive"
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    private fun buildForegroundNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("⚡ MJ JARVIS Mobile Active")
            .setContentText("Always-on: Say 'Hey MJ' to activate voice commands")
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    @SuppressLint("MissingPermission")
    private fun startWakeWordListener() {
        if (isListeningWakeWord) return
        isListeningWakeWord = true

        val sampleRate = 16000
        val bufferSize = AudioRecord.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT
        )

        listenerJob = CoroutineScope(Dispatchers.IO).launch {
            var audioRecord: AudioRecord? = null
            try {
                audioRecord = AudioRecord(
                    MediaRecorder.AudioSource.MIC,
                    sampleRate,
                    AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    bufferSize
                )

                if (audioRecord.state != AudioRecord.STATE_INITIALIZED) {
                    Log.w(TAG, "AudioRecord could not initialize for wake-word.")
                    return@launch
                }

                audioRecord.startRecording()
                val audioBuffer = ShortArray(bufferSize / 2)
                var consecutiveSpeechFrames = 0

                while (isActive && isListeningWakeWord) {
                    val readSize = audioRecord.read(audioBuffer, 0, audioBuffer.size)
                    if (readSize > 0) {
                        // Compute RMS energy
                        var sum = 0.0
                        for (i in 0 until readSize) {
                            sum += audioBuffer[i] * audioBuffer[i]
                        }
                        val rms = sqrt(sum / readSize)

                        // If energy indicates speech bursts (e.g. "Hey MJ")
                        if (rms > 1200) {
                            consecutiveSpeechFrames++
                            if (consecutiveSpeechFrames >= 4) { // Sustained speech phrase detected
                                consecutiveSpeechFrames = 0
                                onWakeWordTriggered()
                            }
                        } else {
                            if (consecutiveSpeechFrames > 0) consecutiveSpeechFrames--
                        }
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Wake word listener error: $e")
            } finally {
                try {
                    audioRecord?.stop()
                    audioRecord?.release()
                } catch (_: Exception) {}
            }
        }
    }

    private fun onWakeWordTriggered() {
        Log.info(TAG, "Wake word triggered! Waking up MJ...")
        val wakeIntent = Intent(this, MainActivity::class.java).apply {
            action = "com.mj.assistant.TRIGGER_WAKE"
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        startActivity(wakeIntent)

        val broadcast = Intent("com.mj.assistant.TRIGGER_WAKE")
        sendBroadcast(broadcast)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        isListeningWakeWord = false
        listenerJob?.cancel()
        if (wakeLock?.isHeld == true) {
            wakeLock?.release()
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
