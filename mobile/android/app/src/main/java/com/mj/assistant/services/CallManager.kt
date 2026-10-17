package com.mj.assistant.services

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.ContactsContract
import androidx.core.content.ContextCompat

class CallManager(private val context: Context) {

    /**
     * Resolves contact name or direct number and triggers immediate phone call
     */
    fun dial(query: String): String {
        val clean = query.trim()
        val phoneNumber = if (clean.matches(Regex("^[0-9+\\s-]+$"))) {
            clean.replace(" ", "").replace("-", "")
        } else {
            findContactNumber(clean)
        }

        if (phoneNumber == null) {
            return "Noaman, '$clean' ka number contact list me nahi mila."
        }

        return makeDirectCall(phoneNumber, clean)
    }

    private fun makeDirectCall(number: String, contactName: String): String {
        val hasPermission = ContextCompat.checkSelfPermission(
            context,
            android.Manifest.permission.CALL_PHONE
        ) == PackageManager.PERMISSION_GRANTED

        return if (hasPermission) {
            val callIntent = Intent(Intent.ACTION_CALL).apply {
                data = Uri.parse("tel:$number")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            try {
                context.startActivity(callIntent)
                "$contactName ($number) ko direct call lagayi ja rahi hai Noaman."
            } catch (e: Exception) {
                "Call lagane me error aaya: ${e.message}"
            }
        } else {
            // Fallback to dialer if CALL_PHONE permission not yet granted
            val dialIntent = Intent(Intent.ACTION_DIAL).apply {
                data = Uri.parse("tel:$number")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(dialIntent)
            "CALL_PHONE permission required hai Noaman. Dialer open kar diya hai."
        }
    }

    private fun findContactNumber(name: String): String? {
        val resolver = context.contentResolver
        val cursor = resolver.query(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
            arrayOf(
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                ContactsContract.CommonDataKinds.Phone.NUMBER
            ),
            "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?",
            arrayOf("%$name%"),
            null
        )

        cursor?.use {
            if (it.moveToFirst()) {
                val numIdx = it.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER)
                if (numIdx >= 0) {
                    val rawNum = it.getString(numIdx)
                    return rawNum.replace(" ", "").replace("-", "")
                }
            }
        }
        return null
    }
}
