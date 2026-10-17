package com.mj.assistant.services

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import java.net.URLEncoder

class MJAccessibilityService : AccessibilityService() {

    companion object {
        private const val TAG = "MJ.Accessibility"
        private var pendingMessage: String? = null
        private var pendingRecipientNumber: String? = null
        private var isAutomating = false

        fun sendWhatsAppMessage(context: Context, phoneNumber: String, message: String) {
            val cleanNumber = phoneNumber.replace("+", "").replace(" ", "").replace("-", "")
            val internationalNumber = if (cleanNumber.length == 10) "91$cleanNumber" else cleanNumber

            pendingRecipientNumber = internationalNumber
            pendingMessage = message
            isAutomating = true

            val encoded = URLEncoder.encode(message, "UTF-8")
            val url = "https://api.whatsapp.com/send?phone=$internationalNumber&text=$encoded"
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                setPackage("com.whatsapp")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }

            try {
                context.startActivity(intent)
            } catch (e: Exception) {
                Log.e(TAG, "Could not open WhatsApp: ${e.message}")
                isAutomating = false
            }
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (!isAutomating || event == null) return

        val pkgName = event.packageName?.toString() ?: ""
        if (pkgName != "com.whatsapp" && pkgName != "com.whatsapp.w4b") return

        val rootNode = rootInActiveWindow ?: return

        // Delay slightly for UI animation
        Handler(Looper.getMainLooper()).postDelayed({
            findAndClickSendButton(rootNode)
        }, 600)
    }

    private fun findAndClickSendButton(rootNode: AccessibilityNodeInfo) {
        if (!isAutomating) return

        // Search 1: By WhatsApp Send Button resource ID
        val sendNodes = rootNode.findAccessibilityNodeInfosByViewId("com.whatsapp:id/send")
        if (sendNodes != null && sendNodes.isNotEmpty()) {
            for (node in sendNodes) {
                if (node.isClickable) {
                    node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                    Log.i(TAG, "WhatsApp message sent via resource ID.")
                    finishAutomation()
                    return
                }
            }
        }

        // Search 2: By content description ("Send" / "भेजें")
        val contentDescs = listOf("Send", "भेजें", "send")
        for (desc in contentDescs) {
            val nodes = rootNode.findAccessibilityNodeInfosByText(desc)
            if (nodes != null) {
                for (node in nodes) {
                    if (node.isClickable) {
                        node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                        Log.i(TAG, "WhatsApp message sent via description '$desc'.")
                        finishAutomation()
                        return
                    }
                }
            }
        }
    }

    private fun finishAutomation() {
        isAutomating = false
        pendingMessage = null
        pendingRecipientNumber = null

        // Return back to MJ App after 800ms
        Handler(Looper.getMainLooper()).postDelayed({
            performGlobalAction(GLOBAL_ACTION_BACK)
        }, 800)
    }

    override fun onInterrupt() {
        Log.w(TAG, "Accessibility Service Interrupted.")
        isAutomating = false
    }
}
