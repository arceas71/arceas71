package com.arceas.notifforward

import android.app.Notification
import android.content.ComponentName
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import java.util.concurrent.Executors

class ForwarderService : NotificationListenerService() {

    private val executor = Executors.newSingleThreadExecutor()
    private val lastSent = LinkedHashMap<String, String>()

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (sbn.packageName !in Config.PACKAGES) return

        val n = sbn.notification
        if (n.flags and Notification.FLAG_GROUP_SUMMARY != 0) return

        val extras = n.extras
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = (extras.getCharSequence(Notification.EXTRA_BIG_TEXT)
            ?: extras.getCharSequence(Notification.EXTRA_TEXT))?.toString().orEmpty()
        if (title.isBlank() && text.isBlank()) return

        val topic = getSharedPreferences(Config.PREFS, MODE_PRIVATE)
            .getString(Config.KEY_TOPIC, "").orEmpty()
        if (topic.isBlank()) return

        // Instagram re-posts the same notification on updates; skip exact repeats.
        val fingerprint = "$title|$text"
        synchronized(lastSent) {
            if (lastSent[sbn.key] == fingerprint) return
            lastSent[sbn.key] = fingerprint
            if (lastSent.size > 200) {
                lastSent.remove(lastSent.keys.first())
            }
        }

        val heading = title.ifBlank { "Instagram" }
        val body = text.ifBlank { " " }

        executor.execute {
            var attempt = 0
            while (attempt < 3) {
                if (Ntfy.send(topic, heading, body) == null) break
                attempt++
                try {
                    Thread.sleep(2000L * attempt)
                } catch (e: InterruptedException) {
                    break
                }
            }
        }
    }

    override fun onListenerDisconnected() {
        requestRebind(ComponentName(this, ForwarderService::class.java))
    }

    override fun onDestroy() {
        executor.shutdown()
        super.onDestroy()
    }
}
