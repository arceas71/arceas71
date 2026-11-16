package com.arceas.notifforward

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

object Ntfy {
    /** Publishes a message to an ntfy.sh topic. Returns null on success, or a short error string. */
    fun send(topic: String, title: String, message: String): String? {
        var conn: HttpURLConnection? = null
        return try {
            conn = URL("https://ntfy.sh/").openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.connectTimeout = 10_000
            conn.readTimeout = 10_000
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            val body = JSONObject()
                .put("topic", topic)
                .put("title", title.take(200))
                .put("message", message.take(3500))
                .toString()
            conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            val code = conn.responseCode
            if (code in 200..299) {
                null
            } else {
                val err = conn.errorStream?.bufferedReader()?.readText().orEmpty()
                "HTTP $code ${err.take(200)}"
            }
        } catch (e: Exception) {
            e.message ?: e.javaClass.simpleName
        } finally {
            conn?.disconnect()
        }
    }
}
