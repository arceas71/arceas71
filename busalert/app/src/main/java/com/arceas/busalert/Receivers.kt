package com.arceas.busalert

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class AlarmReceiver : BroadcastReceiver() {
    override fun onReceive(ctx: Context, intent: Intent) {
        // Chain the next alarm first so the schedule never breaks.
        Scheduler.scheduleNext(ctx)
        val id = intent.getIntExtra("route", 0)
        val svc = BusService.instance
        if (svc == null) {
            Notifier.post(
                ctx,
                "Bus Alert is switched off",
                "Turn on Bus Alert in Settings > Accessibility so it can check Chennai One.",
                1
            )
        } else {
            svc.startRun(id)
        }
    }
}

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(ctx: Context, intent: Intent) {
        Scheduler.scheduleNext(ctx)
    }
}
