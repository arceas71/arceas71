package com.arceas.busalert

import android.Manifest
import android.app.Activity
import android.app.AlarmManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.text.format.DateFormat
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import java.util.Date

class MainActivity : Activity() {

    private lateinit var status: TextView
    private lateinit var last: TextView
    private val fields = LinkedHashMap<String, EditText>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val sv = ScrollView(this)
        sv.setBackgroundColor(Color.BLACK)
        val col = LinearLayout(this)
        col.orientation = LinearLayout.VERTICAL
        col.setPadding(48, 80, 48, 80)
        sv.addView(col)
        setContentView(sv)

        col.addView(text("BUS ALERT", 28f, Color.WHITE, true))
        col.addView(text("Checks Chennai One and notifies you.", 14f, Color.LTGRAY, false))
        status = text("", 14f, Color.WHITE, false)
        status.setPadding(0, 32, 0, 32)
        col.addView(status)

        col.addView(text("Route 1 (5:00 - 6:00 AM, every ${Config.INTERVAL_MIN} min)", 14f, Color.LTGRAY, false))
        col.addView(field("From", "r0from", "Ramapuram MIOT"))
        col.addView(field("To", "r0to", "Karayanchavadi"))
        col.addView(text("Route 2 (6:00 - 7:00 AM, every ${Config.INTERVAL_MIN} min)", 14f, Color.LTGRAY, false))
        col.addView(field("From", "r1from", "Karayanchavadi"))
        col.addView(field("To", "r1to", "Avadi"))
        col.addView(text("Chennai One package id", 14f, Color.LTGRAY, false))
        col.addView(field("Package", "pkg", Config.DEFAULT_PKG))

        col.addView(button("Save stops") {
            val m = HashMap<String, String>()
            for ((k, v) in fields) m[k] = v.text.toString()
            Config.save(this, m)
            Scheduler.scheduleNext(this)
            toast("Saved")
            refresh()
        })

        col.addView(text("Setup (do each once)", 16f, Color.WHITE, true).also { it.setPadding(0, 40, 0, 8) })
        col.addView(button("1. Turn on Bus Alert in Accessibility") {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        })
        col.addView(button("2. Allow notifications") {
            if (Build.VERSION.SDK_INT >= 33) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
            } else toast("Already allowed")
        })
        col.addView(button("3. Allow exact alarms") {
            if (Build.VERSION.SDK_INT >= 31) {
                startActivity(
                    Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:$packageName"))
                )
            } else toast("Not needed on this Android version")
        })
        col.addView(button("4. Disable battery optimisation") {
            startActivity(
                Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName"))
            )
        })
        col.addView(button("5. Start schedule") {
            Scheduler.scheduleNext(this)
            toast("Schedule on")
            refresh()
        })

        col.addView(text("Test now", 16f, Color.WHITE, true).also { it.setPadding(0, 40, 0, 8) })
        col.addView(button("Check route 1 now") { runNow(0) })
        col.addView(button("Check route 2 now") { runNow(1) })

        col.addView(text("Last result", 16f, Color.WHITE, true).also { it.setPadding(0, 40, 0, 8) })
        last = text("", 13f, Color.LTGRAY, false)
        col.addView(last)
    }

    override fun onResume() {
        super.onResume()
        refresh()
    }

    private fun runNow(id: Int) {
        val svc = BusService.instance
        if (svc == null) {
            toast("Turn on Bus Alert in Accessibility first")
        } else {
            toast("Opening Chennai One...")
            svc.startRun(id)
        }
    }

    private fun refresh() {
        val acc = Settings.Secure.getString(contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: ""
        val accOn = acc.contains(packageName) && BusService.instance != null
        val notifOn = Build.VERSION.SDK_INT < 33 ||
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
        val exactOn = Build.VERSION.SDK_INT < 31 ||
            (getSystemService(Context.ALARM_SERVICE) as AlarmManager).canScheduleExactAlarms()
        val next = Scheduler.computeNext(this)
        val nextText = if (next == null) "none"
        else DateFormat.format("EEE h:mm a", Date(next.first)).toString()
        status.text = "Accessibility: ${if (accOn) "ON" else "OFF"}\n" +
            "Notifications: ${if (notifOn) "ON" else "OFF"}\n" +
            "Exact alarms: ${if (exactOn) "ON" else "OFF"}\n" +
            "Next check: $nextText"
        last.text = Config.last(this)
    }

    private fun toast(s: String) = Toast.makeText(this, s, Toast.LENGTH_SHORT).show()

    private fun text(s: String, size: Float, color: Int, bold: Boolean): TextView {
        val t = TextView(this)
        t.text = s
        t.textSize = size
        t.setTextColor(color)
        if (bold) t.setTypeface(t.typeface, android.graphics.Typeface.BOLD)
        t.setPadding(0, 16, 0, 4)
        return t
    }

    private fun field(label: String, key: String, def: String): View {
        val e = EditText(this)
        e.hint = label
        e.setText(Config.get(this, key, def))
        e.setTextColor(Color.WHITE)
        e.setHintTextColor(Color.GRAY)
        e.setSingleLine(true)
        fields[key] = e
        return e
    }

    private fun button(label: String, onClick: () -> Unit): Button {
        val b = Button(this)
        b.text = label
        b.isAllCaps = false
        b.setOnClickListener { onClick() }
        return b
    }
}
