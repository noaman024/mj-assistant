package com.mj.assistant.core

import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

class GeminiMobileClient(private val apiKey: String) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()
    private val endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    private val systemInstruction = """
        You are MJ, a smart, ultra-responsive personal AI assistant for Noaman.
        Always address Noaman by his name (Noaman).
        Interaction Style:
        - Speak naturally in Hinglish, Hindi, or English.
        - Direct, helpful, concise, confident.
        - Never use 'Namaste' or formal heavy words. Simple, casual and natural (e.g. 'Hey Noaman', 'Haan Noaman', 'Theek hai Noaman').
        - Do not use forced slang or fake banter.
    """.trimIndent()

    suspend fun generateResponse(prompt: String): String = withContext(Dispatchers.IO) {
        if (apiKey.isBlank()) {
            return@withContext "Noaman, mobile app me Gemini API Key configure nahi hai."
        }

        try {
            val url = "$endpoint?key=$apiKey"
            val jsonPayload = buildPayload(prompt)
            val requestBody = jsonPayload.toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""

            if (!response.isSuccessful) {
                return@withContext "AI service me thodi dikkat aayi Noaman: HTTP ${response.code}"
            }

            parseResponseText(responseBody)
        } catch (e: Exception) {
            "Network error Noaman: ${e.localizedMessage ?: "Connection failed"}"
        }
    }

    private fun buildPayload(prompt: String): String {
        val root = JsonObject()

        // System Instruction
        val sysInst = JsonObject()
        val sysParts = com.google.gson.JsonArray()
        val sysPartObj = JsonObject()
        sysPartObj.addProperty("text", systemInstruction)
        sysParts.add(sysPartObj)
        sysInst.add("parts", sysParts)
        root.add("systemInstruction", sysInst)

        // Contents
        val contents = com.google.gson.JsonArray()
        val contentObj = JsonObject()
        contentObj.addProperty("role", "user")
        val parts = com.google.gson.JsonArray()
        val partObj = JsonObject()
        partObj.addProperty("text", prompt)
        parts.add(partObj)
        contentObj.add("parts", parts)
        contents.add(contentObj)
        root.add("contents", contents)

        return gson.toJson(root)
    }

    private fun parseResponseText(responseJson: String): String {
        return try {
            val root = gson.fromJson(responseJson, JsonObject::class.java)
            val candidates = root.getAsJsonArray("candidates")
            if (candidates != null && candidates.size() > 0) {
                val first = candidates[0].asJsonObject
                val content = first.getAsJsonObject("content")
                val parts = content.getAsJsonArray("parts")
                if (parts != null && parts.size() > 0) {
                    return parts[0].asJsonObject.get("text").asString.trim()
                }
            }
            "Mujhe response samajh nahi aaya Noaman."
        } catch (e: Exception) {
            "Response parse karte waqt error: ${e.message}"
        }
    }
}
