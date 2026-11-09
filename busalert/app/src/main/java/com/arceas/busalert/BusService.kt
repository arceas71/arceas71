package com.arceas.busalert

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.graphics.Rect
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import java.text.DateFormat
import java.util.Date

/**
 * Opens Chennai One, drives its screens (search stop, pick suggestion, press search)
 * and reads the resulting bus list from the screen, then posts a notification.
 */
class BusService : AccessibilityService() {

    companion object {
        @Volatile
        var instance: BusService? = null

        private val TIME = Regex(
            """(\d+\s*(min|mins|minutes|hr|hrs)\b)|(\b\d{1,2}:\d{2}\b)|\b(ETA|arriving|due)\b""",
            RegexOption.IGNORE_CASE
        )
        private val BUSNO = Regex("""^[0-9]{1,3}[A-Za-z]{0,3}$""")
        private val DISMISS = listOf(
            "Allow", "While using the app", "Only this time", "OK", "Okay",
            "Skip", "Got it", "Later", "Not now", "No thanks", "Maybe later"
        )
        private val NAV = listOf(
            "Bus", "Buses", "Bus Tracking", "Live Bus", "Track Bus", "Search Bus",
            "Find Bus", "Bus Stop", "Stop", "Route", "Search", "Where to",
            "Go", "Find", "Next", "Submit", "Show"
        )
    }

    private class N(val info: AccessibilityNodeInfo, val text: String, val editable: Boolean)

    private val h = Handler(Looper.getMainLooper())
    private var running = false
    private var route: Route? = null
    private var steps = 0
    private var wake: PowerManager.WakeLock? = null
    private val clicked = HashMap<String, Int>()
    private val setCount = HashMap<Int, Int>()
    private var fieldsDone = 0
    private var pending: String? = null
    private var pendingTries = 0
    private var okStreak = 0
    private var lastLines: List<String> = emptyList()

    override fun onServiceConnected() {
        instance = this
        Scheduler.scheduleNext(this)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    override fun onInterrupt() {}

    override fun onUnbind(intent: Intent?): Boolean {
        instance = null
        return super.onUnbind(intent)
    }

    fun startRun(id: Int) {
        if (running) return
        val r = Config.routes(this).firstOrNull { it.id == id } ?: return
        val launch = packageManager.getLaunchIntentForPackage(Config.pkg(this))
        if (launch == null) {
            Notifier.post(
                this, "Chennai One not found",
                "Couldn't find an installed app with package ${Config.pkg(this)}. " +
                    "Fix the package name inside Bus Alert.", 2
            )
            return
        }
        running = true
        route = r
        steps = 0
        clicked.clear()
        setCount.clear()
        fieldsDone = 0
        pending = null
        pendingTries = 0
        okStreak = 0
        lastLines = emptyList()

        @Suppress("DEPRECATION")
        val w = (getSystemService(POWER_SERVICE) as PowerManager).newWakeLock(
            PowerManager.SCREEN_BRIGHT_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP,
            "busalert:run"
        )
        w.acquire(90_000L)
        wake = w

        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        try {
            startActivity(launch)
        } catch (e: Exception) {
            finish(false, "Couldn't open Chennai One: ${e.message}", emptyList())
            return
        }
        next(3500)
    }

    private fun next(ms: Long = 1200) {
        h.postDelayed({ step() }, ms)
    }

    private fun walk(n: AccessibilityNodeInfo?, out: MutableList<N>, depth: Int) {
        if (n == null || depth > 40) return
        if (n.isVisibleToUser) {
            val t = n.text?.toString()?.trim() ?: ""
            val cd = n.contentDescription?.toString()?.trim() ?: ""
            val label = if (t.isNotEmpty()) t else cd
            if (label.isNotEmpty() || n.isEditable) out.add(N(n, label, n.isEditable))
        }
        for (i in 0 until n.childCount) walk(n.getChild(i), out, depth + 1)
    }

    private fun click(n: AccessibilityNodeInfo): Boolean {
        var c: AccessibilityNodeInfo? = n
        while (c != null) {
            if (c.isClickable && c.performAction(AccessibilityNodeInfo.ACTION_CLICK)) return true
            c = c.parent
        }
        val b = Rect()
        n.getBoundsInScreen(b)
        val p = Path()
        p.moveTo(b.exactCenterX(), b.exactCenterY())
        val g = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(p, 0, 60))
            .build()
        return dispatchGesture(g, null, null)
    }

    private fun step() {
        if (!running) return
        val r = route ?: return
        steps++
        if (steps > 45) {
            finish(false, "Gave up after $steps steps.", lastLines)
            return
        }
        val root = rootInActiveWindow
        val pkgName = root?.packageName?.toString() ?: ""
        val inTarget = pkgName == Config.pkg(this)
        val isPerm = pkgName.contains("permission") || pkgName.contains("packageinstaller")
        if (root == null || (!inTarget && !isPerm)) {
            next()
            return
        }

        val nodes = ArrayList<N>()
        walk(root, nodes, 0)
        val lines = nodes.map { it.text }.filter { it.isNotEmpty() }.distinct()
        if (inTarget) lastLines = lines

        // 1. Are we looking at results? Require it on two consecutive looks so the list has loaded.
        if (inTarget) {
            val timeish = lines.count { TIME.containsMatchIn(it) }
            val hasEditable = nodes.any { it.editable }
            val looksFinal = timeish >= 1 && ((fieldsDone >= 1 && !hasEditable) || steps >= 14)
            if (looksFinal) okStreak++ else okStreak = 0
            if (okStreak >= 2) {
                finish(true, null, lines)
                return
            }
        }

        // 2. Dismiss popups and permission dialogs.
        for (n in nodes) {
            if (n.editable) continue
            val d = DISMISS.firstOrNull { it.equals(n.text, true) } ?: continue
            val cnt = clicked[d] ?: 0
            if (cnt < 3 && click(n.info)) {
                clicked[d] = cnt + 1
                next()
                return
            }
        }
        if (!inTarget) {
            next()
            return
        }

        // 3. Pick the suggestion for the text we just typed.
        val pend = pending
        if (pend != null) {
            val cand = nodes.firstOrNull {
                !it.editable && it.text.length < 120 && it.text.contains(pend, true)
            }
            if (cand != null && click(cand.info)) {
                fieldsDone++
                pending = null
                next()
                return
            }
            pendingTries++
            if (pendingTries > 3) {
                pending = null
                fieldsDone++
            }
        }

        // 4. Fill text fields (from first, then to).
        val eds = nodes.filter { it.editable }
        if (eds.isNotEmpty() && pending == null) {
            val wants = listOf(r.from, r.to)
            for ((i, ed) in eds.withIndex()) {
                val want = if (eds.size == 1) wants[minOf(fieldsDone, 1)] else wants[minOf(i, 1)]
                if (ed.text.contains(want, true)) continue
                val key = i * 10 + fieldsDone
                val used = setCount[key] ?: 0
                if (used >= 2) continue
                val args = Bundle()
                args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, want)
                ed.info.performAction(AccessibilityNodeInfo.ACTION_FOCUS)
                ed.info.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
                setCount[key] = used + 1
                pending = want
                pendingTries = 0
                next()
                return
            }
        }

        // 5. Navigate: press the next sensible button.
        for (label in NAV) {
            val n = nodes.firstOrNull { !it.editable && it.text.equals(label, true) } ?: continue
            val cnt = clicked[label] ?: 0
            if (cnt < 2 && click(n.info)) {
                clicked[label] = cnt + 1
                next()
                return
            }
        }
        next()
    }

    private fun finish(ok: Boolean, msg: String?, lines: List<String>) {
        val r = route
        running = false
        h.removeCallbacksAndMessages(null)
        try {
            wake?.release()
        } catch (_: Exception) {
        }
        if (r != null) {
            val title: String
            val body: String
            if (ok) {
                val rel = lines.filter {
                    it.contains(r.to, true) || it.contains(r.from, true) ||
                        TIME.containsMatchIn(it) || BUSNO.matches(it)
                }
                val use = (if (rel.isEmpty()) lines else rel).take(14)
                title = "Bus: ${r.from} to ${r.to}"
                body = use.joinToString("\n")
            } else {
                title = "Couldn't read buses: ${r.from} to ${r.to}"
                body = (msg ?: "") + "\nScreen: " + lines.take(12).joinToString(" | ")
            }
            val stamp = DateFormat.getTimeInstance(DateFormat.SHORT).format(Date())
            Config.setLast(this, "$stamp\n$title\n$body")
            Notifier.post(this, title, body, 10 + r.id, r.id)
        }
        h.postDelayed({ performGlobalAction(GLOBAL_ACTION_HOME) }, 600)
    }
}
