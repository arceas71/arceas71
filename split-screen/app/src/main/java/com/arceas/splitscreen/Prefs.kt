package com.arceas.splitscreen

import android.content.Context

object Prefs {
    private fun p(c: Context) = c.getSharedPreferences("split", Context.MODE_PRIVATE)

    fun bubble(c: Context): Boolean = p(c).getBoolean("bubble", true)

    fun setBubble(c: Context, on: Boolean) {
        p(c).edit().putBoolean("bubble", on).apply()
    }
}
