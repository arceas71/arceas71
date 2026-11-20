package com.arceas.splitscreen

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView

class MainActivity : Activity() {

    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val d = resources.displayMetrics.density
        fun dp(v: Int) = (v * d).toInt()

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0A0A0A"))
            setPadding(dp(24), dp(48), dp(24), dp(24))
        }

        fun label(t: String, size: Float, color: String, bottom: Int = 12) = TextView(this).apply {
            text = t
            textSize = size
            setTextColor(Color.parseColor(color))
            setPadding(0, 0, 0, dp(bottom))
        }

        fun button(t: String, onClick: () -> Unit) = Button(this).apply {
            text = t
            isAllCaps = false
            setOnClickListener { onClick() }
        }

        root.addView(label("Split Screen", 28f, "#FFFFFF", 4))
        root.addView(label("Toggle split-screen on any app: floating button or Quick Settings tile.", 14f, "#AAAAAA", 20))

        status = label("", 16f, "#FFFFFF", 16)
        root.addView(status)

        root.addView(button("1. Enable accessibility service") {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        })

        root.addView(Switch(this).apply {
            text = "Floating split button"
            setTextColor(Color.WHITE)
            isChecked = Prefs.bubble(this@MainActivity)
            setPadding(0, dp(16), 0, dp(16))
            setOnCheckedChangeListener { _, on ->
                Prefs.setBubble(this@MainActivity, on)
                SplitService.instance?.setBubble(on)
            }
        })

        root.addView(button("Toggle split screen now") {
            SplitService.instance?.toggleSplit()
        })

        root.addView(button("Open developer options (force resizable)") {
            try {
                startActivity(Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS))
            } catch (_: Exception) {
                startActivity(Intent(Settings.ACTION_DEVICE_INFO_SETTINGS))
            }
        })

        root.addView(label(
            "Tips\n" +
                "• Add the tile: swipe down twice, tap the pencil/edit icon, drag \"Split screen\" in.\n" +
                "• Open the app you want first, then tap the button or tile; pick the second app from recents.\n" +
                "• If an app refuses to split: Developer options > Force activities to be resizable, then reboot.\n" +
                "• If Enable is greyed out: App info > ⋮ > Allow restricted settings.",
            13f, "#888888", 0
        ).apply { setPadding(0, dp(20), 0, 0) })

        setContentView(root)
    }

    override fun onResume() {
        super.onResume()
        val on = SplitService.instance != null
        status.text = if (on) "● Service running" else "○ Service off — enable it below"
        status.setTextColor(Color.parseColor(if (on) "#7CFC9A" else "#FF7A7A"))
    }
}
