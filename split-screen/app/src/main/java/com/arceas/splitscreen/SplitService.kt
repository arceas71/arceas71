package com.arceas.splitscreen

import android.accessibilityservice.AccessibilityService
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.MotionEvent
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.TextView
import android.widget.Toast

class SplitService : AccessibilityService() {

    private var bubble: TextView? = null
    private val handler = Handler(Looper.getMainLooper())

    override fun onServiceConnected() {
        instance = this
        if (Prefs.bubble(this)) showBubble()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event?.eventType != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return
        val pkg = event.packageName?.toString() ?: return
        if (pkg in PAYMENT_APPS) {
            // Payment apps refuse to run while an accessibility service is on, so switch ourselves off.
            Toast.makeText(
                this,
                "Split Screen turned itself off for payments. Re-enable it in Accessibility settings when done.",
                Toast.LENGTH_LONG
            ).show()
            disableSelf()
        }
    }

    override fun onInterrupt() {}

    override fun onUnbind(intent: android.content.Intent?): Boolean {
        hideBubble()
        instance = null
        return super.onUnbind(intent)
    }

    fun toggleSplit(closeShadeFirst: Boolean = false) {
        if (closeShadeFirst) {
            // Quick Settings shade sits on top of the app; close it, then split the app underneath.
            performGlobalAction(GLOBAL_ACTION_BACK)
            handler.postDelayed({ performGlobalAction(GLOBAL_ACTION_TOGGLE_SPLIT_SCREEN) }, 350)
        } else {
            performGlobalAction(GLOBAL_ACTION_TOGGLE_SPLIT_SCREEN)
        }
    }

    fun setBubble(on: Boolean) {
        if (on) showBubble() else hideBubble()
    }

    private fun showBubble() {
        if (bubble != null) return
        val wm = getSystemService(WINDOW_SERVICE) as WindowManager
        val size = (52 * resources.displayMetrics.density).toInt()

        val view = TextView(this).apply {
            text = "▤"
            textSize = 22f
            gravity = Gravity.CENTER
            setTextColor(Color.WHITE)
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(Color.parseColor("#CC111111"))
                setStroke(2, Color.parseColor("#88FFFFFF"))
            }
        }

        val lp = WindowManager.LayoutParams(
            size, size,
            WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 0
            y = (resources.displayMetrics.heightPixels * 0.4).toInt()
        }

        var startX = 0
        var startY = 0
        var touchX = 0f
        var touchY = 0f
        var moved = false
        view.setOnTouchListener { v, e ->
            when (e.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = lp.x; startY = lp.y
                    touchX = e.rawX; touchY = e.rawY
                    moved = false
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (e.rawX - touchX).toInt()
                    val dy = (e.rawY - touchY).toInt()
                    if (Math.abs(dx) > 12 || Math.abs(dy) > 12) moved = true
                    if (moved) {
                        lp.x = startX + dx
                        lp.y = startY + dy
                        wm.updateViewLayout(v, lp)
                    }
                }
                MotionEvent.ACTION_UP -> if (!moved) toggleSplit()
            }
            true
        }

        wm.addView(view, lp)
        bubble = view
    }

    private fun hideBubble() {
        val v = bubble ?: return
        try {
            (getSystemService(WINDOW_SERVICE) as WindowManager).removeView(v)
        } catch (_: Exception) {
        }
        bubble = null
    }

    companion object {
        // Apps that must never see an active accessibility service. Add more package names here.
        val PAYMENT_APPS = setOf(
            "com.google.android.apps.nbu.paisa.user" // Google Pay (India)
        )

        @Volatile
        var instance: SplitService? = null
    }
}
