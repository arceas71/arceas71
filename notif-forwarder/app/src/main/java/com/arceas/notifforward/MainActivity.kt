package com.arceas.notifforward

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.provider.Settings
import android.text.InputType
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import java.util.UUID
import kotlin.concurrent.thread

class MainActivity : Activity() {

    private lateinit var topicInput: EditText
    private lateinit var link: TextView
    private lateinit var status: TextView

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    private fun label(text: String) = TextView(this).apply {
        this.text = text
        setTextColor(Color.parseColor("#9A9A9A"))
        textSize = 12f
        setPadding(0, dp(16), 0, dp(4))
    }

    private fun button(text: String, onClick: () -> Unit) = Button(this).apply {
        this.text = text
        isAllCaps = false
        setOnClickListener { onClick() }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val prefs = getSharedPreferences(Config.PREFS, MODE_PRIVATE)

        // The topic acts as a password, so generate a random one on first launch.
        var topic = prefs.getString(Config.KEY_TOPIC, "").orEmpty()
        if (topic.isBlank()) {
            topic = "nf-" + UUID.randomUUID().toString().replace("-", "").take(20)
            prefs.edit().putString(Config.KEY_TOPIC, topic).apply()
        }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(40), dp(20), dp(20))
            setBackgroundColor(Color.BLACK)
        }

        val title = TextView(this).apply {
            text = "Notif Forwarder"
            setTextColor(Color.WHITE)
            textSize = 24f
        }
        val sub = TextView(this).apply {
            text = "Instagram notifications → laptop"
            setTextColor(Color.parseColor("#9A9A9A"))
            textSize = 14f
        }

        topicInput = EditText(this).apply {
            setText(topic)
            setTextColor(Color.WHITE)
            setSingleLine(true)
            inputType = InputType.TYPE_CLASS_TEXT
        }

        link = TextView(this).apply {
            setTextColor(Color.WHITE)
            textSize = 14f
            setTextIsSelectable(true)
            setPadding(0, dp(8), 0, 0)
        }

        status = TextView(this).apply {
            setTextColor(Color.WHITE)
            textSize = 14f
            setPadding(0, dp(16), 0, 0)
        }

        root.addView(title)
        root.addView(sub)
        root.addView(label("Topic (keep it secret, it works like a password)"))
        root.addView(topicInput)
        root.addView(button("Save") { save() })
        root.addView(label("Open this link on the laptop and click the page once"))
        root.addView(link)
        root.addView(button("Send test notification") { sendTest() })
        root.addView(button("1. Grant notification access") {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        })
        root.addView(button("2. Disable battery optimization") {
            startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
        })
        root.addView(status)

        setContentView(ScrollView(this).apply {
            setBackgroundColor(Color.BLACK)
            addView(root)
        })
        refreshStatus()
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
    }

    private fun currentTopic() = topicInput.text.toString().trim()

    private fun save() {
        val t = currentTopic()
        if (t.isEmpty()) {
            refreshStatus("Topic can't be empty.")
            return
        }
        getSharedPreferences(Config.PREFS, MODE_PRIVATE).edit()
            .putString(Config.KEY_TOPIC, t)
            .apply()
        refreshStatus("Saved.")
    }

    private fun sendTest() {
        save()
        val t = currentTopic()
        if (t.isEmpty()) return
        refreshStatus("Sending test...")
        thread {
            val err = Ntfy.send(t, "Notif Forwarder", "Test notification: it works")
            runOnUiThread {
                refreshStatus(if (err == null) "Test sent. Check the laptop." else "Failed: $err")
            }
        }
    }

    private fun listenerEnabled(): Boolean {
        val enabled = Settings.Secure.getString(contentResolver, "enabled_notification_listeners")
        return enabled?.contains(packageName) == true
    }

    private fun refreshStatus(extra: String? = null) {
        link.text = Config.LAPTOP_PAGE + "#" + currentTopic()
        val access = if (listenerEnabled()) "Notification access: ON" else "Notification access: OFF"
        status.text = if (extra == null) access else "$access\n$extra"
    }
}
