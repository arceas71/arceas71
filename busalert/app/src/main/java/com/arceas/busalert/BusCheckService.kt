package com.arceas.busalert

import android.annotation.SuppressLint
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.ServiceCompat
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * Runs while a route's time window is open: every INTERVAL_MS it asks the accessibility
 * service to open Chennai One, search the route, read the times, then posts a notification.
 */
class BusCheckService : Service() {

    companion object {
        const val EXTRA_ROUTE = "route"
        const val EXTRA_ONCE = "once"
        private const val FG_ID = 1
        @Volatile private var generation = 0
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val route = Config.byId(intent?.getIntExtra(EXTRA_ROUTE, 1) ?: 1)
        val once = intent?.getBooleanExtra(EXTRA_ONCE, false) ?: false

        ServiceCompat.startForeground(
            this, FG_ID,
            Notifier.serviceNotification(this, "Checking buses: ${route.title}"),
            if (Build.VERSION.SDK_INT >= 34) ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE else 0
        )

        val myGen = ++generation
        Thread {
            try {
                do {
                    runOne(route)
                    if (once) break
                    var waited = 0L
                    while (waited < Config.INTERVAL_MS && generation == myGen) {
                        Thread.sleep(5_000)
                        waited += 5_000
                    }
                } while (generation == myGen && Scheduler.inWindow(route))
            } catch (_: InterruptedException) {
            } finally {
                if (generation == myGen) stopSelf()
            }
        }.start()

        return START_NOT_STICKY
    }

    @SuppressLint("WakelockTimeout")
    @Suppress("DEPRECATION")
    private fun runOne(route: Route) {
        val pm = getSystemService(PowerManager::class.java)
        val wl = pm.newWakeLock(
            PowerManager.SCREEN_BRIGHT_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP,
            "busalert:check"
        )
        wl.acquire(Config.JOB_TIMEOUT_MS + 20_000)
        try {
            val svc = BusAccessibilityService.instance
            val time = SimpleDateFormat("hh:mm a", Locale.getDefault()).format(Date())
            if (svc == null) {
                val msg = "Accessibility service is off. Turn on \"Bus Alert\" in Accessibility settings."
                Prefs.saveLast(this, "$time  ${route.title}\n$msg")
                Notifier.alert(this, route.id * 100, route.title, msg)
                return
            }

            val latch = CountDownLatch(1)
            var result: CheckResult? = null
            svc.startJob(route) {
                result = it
                latch.countDown()
            }
            latch.await(Config.JOB_TIMEOUT_MS + 15_000, TimeUnit.MILLISECONDS)
            val r = result ?: CheckResult(false, emptyList(), "No response from Chennai One")

            val body = if (r.ok) {
                "Next buses (checked $time):\n" + r.lines.joinToString("\n")
            } else {
                "Couldn't read bus times at $time. Chennai One showed:\n" + r.raw.take(400)
            }
            Prefs.saveLast(this, "$time  ${route.title}\n$body")
            Notifier.alert(this, route.id * 100, route.title, body)
        } finally {
            if (wl.isHeld) wl.release()
        }
    }
}
