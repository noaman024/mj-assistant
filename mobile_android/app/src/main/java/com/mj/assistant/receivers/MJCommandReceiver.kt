package com.mj.assistant.receivers

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.mj.assistant.MainActivity
import com.mj.assistant.tools.DeviceController

class MJCommandReceiver : BroadcastReceiver() {

    private val TAG = "MJ.CommandReceiver"

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        Log.i(TAG, "Broadcast received: $action")

        val deviceController = DeviceController(context)

        when (action) {
            "com.mj.assistant.TRIGGER_WAKE" -> {
                val launchIntent = Intent(context, MainActivity::class.java).apply {
                    this.action = "com.mj.assistant.TRIGGER_WAKE"
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
                }
                context.startActivity(launchIntent)
            }

            "com.mj.assistant.EXECUTE_COMMAND" -> {
                val cmd = intent.getStringExtra("query") ?: intent.getStringExtra("command") ?: ""
                val targetApp = intent.getStringExtra("app")
                val volume = intent.getIntExtra("volume", -1)
                val torch = intent.getBooleanExtra("torch", false)

                if (targetApp != null) {
                    deviceController.launchApp(targetApp)
                } else if (volume != -1) {
                    deviceController.setVolume(volume)
                } else if (intent.hasExtra("torch")) {
                    deviceController.setTorch(torch)
                } else if (cmd.isNotEmpty()) {
                    // Forward generic query to MainActivity WebView
                    val launchIntent = Intent(context, MainActivity::class.java).apply {
                        this.action = "com.mj.assistant.EXECUTE_COMMAND"
                        putExtra("query", cmd)
                        flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
                    }
                    context.startActivity(launchIntent)
                }
            }
        }
    }
}
