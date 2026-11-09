package com.arceas.busalert

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import java.util.Calendar

object Scheduler {

    /** Next scheduled check strictly after now: (epoch millis, route id). */
    fun computeNext(ctx: Context): Pair<Long, Int>? {
        val nowMs = System.currentTimeMillis()
        var best = Long.MAX_VALUE
        var bestRoute = -1
        for (dayOffset in 0..1) {
            for (r in Config.routes(ctx)) {
                var m = r.startMin
                while (m < r.endMin) {
                    val c = Calendar.getInstance()
                    c.set(Calendar.HOUR_OF_DAY, m / 60)
                    c.set(Calendar.MINUTE, m % 60)
                    c.set(Calendar.SECOND, 0)
                    c.set(Calendar.MILLISECOND, 0)
                    c.add(Calendar.DAY_OF_YEAR, dayOffset)
                    val t = c.timeInMillis
                    if (t > nowMs + 1000 && t < best) {
                        best = t
                        bestRoute = r.id
                    }
                    m += Config.INTERVAL_MIN
                }
            }
        }
        return if (bestRoute < 0) null else Pair(best, bestRoute)
    }

    fun scheduleNext(ctx: Context) {
        val next = computeNext(ctx) ?: return
        val am = ctx.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val intent = Intent(ctx, AlarmReceiver::class.java).putExtra("route", next.second)
        val pi = PendingIntent.getBroadcast(
            ctx, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        try {
            if (Build.VERSION.SDK_INT >= 31 && !am.canScheduleExactAlarms()) {
                am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next.first, pi)
            } else {
                am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next.first, pi)
            }
        } catch (e: SecurityException) {
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next.first, pi)
        }
    }
}
