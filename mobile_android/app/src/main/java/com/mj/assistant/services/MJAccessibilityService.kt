package com.mj.assistant.services

import android.accessibilityservice.AccessibilityService
import android.os.Bundle
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/**
 * Superpower: Zero-Touch Automated WhatsApp Messaging
 * When MJ triggers a WhatsApp deep link, this service automatically locates
 * the text input and clicks the Send button without requiring manual screen touches.
 */
class MJAccessibilityService : AccessibilityService() {

    companion object {
        var pendingMessageText: String? = null
        var shouldAutoSend: Boolean = false
        private const val TAG = "MJ.Accessibility"
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (!shouldAutoSend || pendingMessageText == null) return
        val rootNode = rootInActiveWindow ?: return

        // 1. Search for WhatsApp Send Button (contentDescription: "Send" or "भेजें")
        val sendNode = findSendButton(rootNode)

        if (sendNode != null) {
            Log.i(TAG, "Found WhatsApp Send button! Simulating automated click...")
            sendNode.performAction(AccessibilityNodeInfo.ACTION_CLICK)

            // Reset state after dispatch
            shouldAutoSend = false
            pendingMessageText = null

            // Automatically navigate back to MJ Cockpit
            performGlobalAction(GLOBAL_ACTION_BACK)
        }
    }

    private fun findSendButton(node: AccessibilityNodeInfo): AccessibilityNodeInfo? {
        val desc = node.contentDescription?.toString()?.lowercase() ?: ""
        val text = node.text?.toString()?.lowercase() ?: ""

        if (desc.contains("send") || desc.contains("भेजें") || text.contains("send") || text.contains("भेजें")) {
            if (node.isClickable) return node
        }

        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            val found = findSendButton(child)
            if (found != null) return found
        }
        return null
    }

    override fun onInterrupt() {
        Log.w(TAG, "Accessibility Service interrupted")
    }
}
