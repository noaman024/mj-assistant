package com.mj.assistant.bridge

import android.content.Context
import android.net.wifi.WifiManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

class LaptopDiscovery(private val context: Context) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(1200, TimeUnit.MILLISECONDS)
        .readTimeout(1500, TimeUnit.MILLISECONDS)
        .build()

    var activeLaptopIp: String? = null
        private set

    /**
     * Checks if laptop is online on local Wi-Fi network
     */
    suspend fun checkLaptopReachability(preferredIp: String? = null): Boolean = withContext(Dispatchers.IO) {
        // 1. Try preferred IP if configured
        if (!preferredIp.isNullOrBlank()) {
            if (testIp(preferredIp)) {
                activeLaptopIp = preferredIp
                return@withContext true
            }
        }

        // 2. Try last known active IP
        activeLaptopIp?.let {
            if (testIp(it)) return@withContext true
        }

        // 3. Scan local subnet based on phone's current Wi-Fi IP
        val subnetBase = getSubnetBase() ?: return@withContext false
        for (lastOctet in listOf(1, 2, 100, 101, 102, 105, 110, 150)) {
            val candidateIp = "$subnetBase.$lastOctet"
            if (testIp(candidateIp)) {
                activeLaptopIp = candidateIp
                return@withContext true
            }
        }

        activeLaptopIp = null
        false
    }

    private fun testIp(ip: String): Boolean {
        return try {
            val request = Request.Builder()
                .url("http://$ip:8000/api/status")
                .get()
                .build()
            val response = client.newCall(request).execute()
            response.isSuccessful && (response.body?.string()?.contains("laptop") == true)
        } catch (e: Exception) {
            false
        }
    }

    private fun getSubnetBase(): String? {
        val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
            ?: return null
        val ipAddress = wifiManager.connectionInfo.ipAddress
        if (ipAddress == 0) return null

        val ipString = String.format(
            "%d.%d.%d.%d",
            ipAddress and 0xff,
            ipAddress shr 8 and 0xff,
            ipAddress shr 16 and 0xff,
            ipAddress shr 24 and 0xff
        )
        val parts = ipString.split(".")
        return if (parts.size == 4) "${parts[0]}.${parts[1]}.${parts[2]}" else null
    }
}
