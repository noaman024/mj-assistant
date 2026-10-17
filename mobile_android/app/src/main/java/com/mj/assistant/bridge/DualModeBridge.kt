package com.mj.assistant.bridge

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

/**
 * The Auto-Switching Dual Mode Engine:
 * - If Laptop Wi-Fi is reachable (e.g. 10.35.126.235:8000) -> Executes on Laptop via Bridge
 * - If outside on 4G/5G or Laptop is off -> Executes locally / via Standalone Gemini Client
 */
class DualModeBridge(private val context: Context) {

    private val TAG = "MJ.DualMode"
    var laptopIp: String = "10.35.126.235"
    var laptopPort: Int = 8000
    var isLaptopConnected: Boolean = false

    suspend fun checkLaptopConnection(): Boolean = withContext(Dispatchers.IO) {
        try {
            val url = URL("http://$laptopIp:$laptopPort/api/status")
            val connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 1500
            connection.readTimeout = 1500
            connection.requestMethod = "GET"
            val code = connection.responseCode
            isLaptopConnected = (code == 200)
            connection.disconnect()
            isLaptopConnected
        } catch (e: Exception) {
            isLaptopConnected = false
            false
        }
    }

    suspend fun dispatchCommand(query: String): String = withContext(Dispatchers.IO) {
        val isConnected = checkLaptopConnection()

        if (isConnected) {
            // MODE 1: Send to Laptop Server with NLP routing
            try {
                val url = URL("http://$laptopIp:$laptopPort/api/command")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                conn.connectTimeout = 4000
                conn.readTimeout = 6000

                val payload = JSONObject().apply {
                    put("query", query)
                    put("source", "phone_native_apk")
                }

                val writer = OutputStreamWriter(conn.outputStream)
                writer.write(payload.toString())
                writer.flush()
                writer.close()

                val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                conn.disconnect()

                val json = JSONObject(responseStr)
                json.optString("response", "Command executed on Laptop.")
            } catch (e: Exception) {
                Log.e(TAG, "Bridge error: ${e.message}")
                "Laptop se connect karne me dikkat aayi. Standalone mode me try kar rahi hu."
            }
        } else {
            // MODE 2: Standalone Phone execution
            "Laptop offline hai Noaman. Main phone standalone mode me hu."
        }
    }
}
