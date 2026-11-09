package com.arceas.busalert

import android.content.Context

data class Route(
    val id: Int,
    val from: String,
    val to: String,
    val startMin: Int, // minutes after midnight
    val endMin: Int
)

object Config {
    // Package id of the Chennai One app (editable inside the app if it differs).
    const val DEFAULT_PKG = "in.mobility.cumta"
    const val INTERVAL_MIN = 5

    private fun p(c: Context) = c.getSharedPreferences("busalert", Context.MODE_PRIVATE)

    fun pkg(c: Context): String = p(c).getString("pkg", DEFAULT_PKG) ?: DEFAULT_PKG

    fun routes(c: Context): List<Route> {
        val s = p(c)
        return listOf(
            Route(
                0,
                s.getString("r0from", "Ramapuram MIOT") ?: "Ramapuram MIOT",
                s.getString("r0to", "Karayanchavadi") ?: "Karayanchavadi",
                5 * 60, 6 * 60
            ),
            Route(
                1,
                s.getString("r1from", "Karayanchavadi") ?: "Karayanchavadi",
                s.getString("r1to", "Avadi") ?: "Avadi",
                6 * 60, 7 * 60
            )
        )
    }

    fun get(c: Context, key: String, def: String): String = p(c).getString(key, def) ?: def

    fun save(c: Context, values: Map<String, String>) {
        val e = p(c).edit()
        for ((k, v) in values) e.putString(k, v.trim())
        e.apply()
    }

    fun setLast(c: Context, text: String) = p(c).edit().putString("last", text).apply()
    fun last(c: Context): String = p(c).getString("last", "No check has run yet.") ?: ""
}
