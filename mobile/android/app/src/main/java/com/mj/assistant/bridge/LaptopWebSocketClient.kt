package com.mj.assistant.bridge

import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

class LaptopWebSocketClient {

    private val client = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()
    private var webSocket: WebSocket? = null
    var isConnected = false
        private set

    suspend fun executeRemoteCommand(laptopIp: String, query: String): String = withContext(Dispatchers.IO) {
        try {
            val url = "http://$laptopIp:8000/api/command"
            val payload = JsonObject().apply {
                addProperty("query", query)
                addProperty("source", "mobile_app")
            }
            val requestBody = gson.toJson(payload).toRequestBody("application/json".toMediaType())
            val request = Request.Builder().url(url).post(requestBody).build()

            val response = client.newCall(request).execute()
            val bodyString = response.body?.string() ?: ""

            if (response.isSuccessful) {
                val json = gson.fromJson(bodyString, JsonObject::class.java)
                json.get("response")?.asString ?: "Command executed on Laptop Noaman."
            } else {
                "Laptop command error: HTTP ${response.code}"
            }
        } catch (e: Exception) {
            "Laptop se communicate karte waqt error: ${e.message}"
        }
    }

    fun connectWebSocket(laptopIp: String, onMessageReceived: (String) -> Unit) {
        val request = Request.Builder()
            .url("ws://$laptopIp:8001/ws/phone")
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(ws: WebSocket, response: Response) {
                isConnected = true
            }

            override fun onMessage(ws: WebSocket, text: String) {
                onMessageReceived(text)
            }

            override fun onClosed(ws: WebSocket, code: Int, reason: String) {
                isConnected = false
            }

            override fun onFailure(ws: WebSocket, t: Throwable, response: Response?) {
                isConnected = false
            }
        })
    }

    fun disconnect() {
        webSocket?.close(1000, "App closed")
        isConnected = false
    }
}
