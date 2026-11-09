package com.arceas.busalert

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent

object Notifier {
    private const val CH = "bus_alerts"

    fun post(ctx: Context, title: String, body: String, id: Int, routeId: Int = -1) {
        val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        nm.createNotificationChannel(
            NotificationChannel(CH, "Bus alerts", NotificationManager.IMPORTANCE_HIGH)
        )
        val open = PendingIntent.getActivity(
            ctx, 0, Intent(ctx, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val b = Notification.Builder(ctx, CH)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body.lines().firstOrNull() ?: "")
            .setStyle(Notification.BigTextStyle().bigText(body))
            .setContentIntent(open)
            .setAutoCancel(true)
        if (routeId >= 0) {
            val again = PendingIntent.getBroadcast(
                ctx, 100 + routeId,
                Intent(ctx, AlarmReceiver::class.java).putExtra("route", routeId),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            @Suppress("DEPRECATION")
            b.addAction(android.R.drawable.ic_menu_rotate, "Check again", again)
        }
        nm.notify(id, b.build())
    }
}
