package com.arceas.splitscreen

import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

class SplitTile : TileService() {

    override fun onStartListening() {
        qsTile?.apply {
            state = if (SplitService.instance != null) Tile.STATE_INACTIVE else Tile.STATE_UNAVAILABLE
            updateTile()
        }
    }

    @Suppress("DEPRECATION")
    override fun onClick() {
        val svc = SplitService.instance
        if (svc != null) {
            svc.toggleSplit(closeShadeFirst = true)
        } else {
            val intent = Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            if (Build.VERSION.SDK_INT >= 34) {
                startActivityAndCollapse(
                    PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE)
                )
            } else {
                startActivityAndCollapse(intent)
            }
        }
    }
}
