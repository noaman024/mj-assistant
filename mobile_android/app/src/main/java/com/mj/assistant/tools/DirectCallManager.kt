package com.mj.assistant.tools

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.util.Log
import androidx.core.content.ContextCompat

/**
 * Superpower: Direct Phone Calling
 * Bypasses the dialer confirmation screen and places direct phone calls
 * using android.permission.CALL_PHONE.
 */
class DirectCallManager(private val context: Context) {

    private val TAG = "MJ.DirectCall"

    fun callNumber(phoneNumber: String): Boolean {
        val cleanNumber = phoneNumber.replace(Regex("[^0-9+]"), "")
        if (cleanNumber.isEmpty()) return false

        val hasPermission = ContextCompat.checkSelfPermission(
            context,
            android.Manifest.permission.CALL_PHONE
        ) == PackageManager.PERMISSION_GRANTED

        return if (hasPermission) {
            val callIntent = Intent(Intent.ACTION_CALL).apply {
                data = Uri.parse("tel:$cleanNumber")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(callIntent)
            Log.i(TAG, "Direct call placed to: $cleanNumber")
            true
        } else {
            // Fallback to standard DIAL intent if permission not yet granted
            val dialIntent = Intent(Intent.ACTION_DIAL).apply {
                data = Uri.parse("tel:$cleanNumber")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(dialIntent)
            Log.w(TAG, "CALL_PHONE permission missing, opened dialer.")
            false
        }
    }

    fun sendWhatsApp(phoneNumber: String, message: String): Boolean {
        return try {
            val cleanNumber = phoneNumber.replace(Regex("[^0-9+]"), "").removePrefix("+")
            MJAccessibilityService.pendingMessageText = message
            MJAccessibilityService.shouldAutoSend = true
            val encodedMsg = java.net.URLEncoder.encode(message, "UTF-8")
            val uri = Uri.parse("https://api.whatsapp.com/send?phone=$cleanNumber&text=$encodedMsg")
            val intent = Intent(Intent.ACTION_VIEW, uri).apply {
                setPackage("com.whatsapp")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
            true
        } catch (e: Exception) {
            Log.e(TAG, "WhatsApp dispatch error: ${e.message}")
            false
        }
    }
}
