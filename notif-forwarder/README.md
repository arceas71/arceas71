# Notif Forwarder

Android app that forwards Instagram notifications to your laptop as desktop notifications.

Flow: phone app -> https://ntfy.sh (private random topic) -> `y.html` open in a laptop browser tab -> desktop notification.

## Setup

1. Install the APK (GitHub: Actions > latest "Build Notif Forwarder APK" run > `notif-forwarder-debug-apk`).
2. Open the app. A random secret topic is generated for you.
3. Tap "Grant notification access" and enable Notif Forwarder. On Android 13+, if the toggle is greyed out: long-press the app icon > App info > three dots > Allow restricted settings.
4. Tap "Disable battery optimization" and allow it so Android doesn't kill the listener.
5. On the laptop, open the link shown in the app (`https://arceas71.github.io/y.html#<topic>`), click the blank page once, and allow notifications. Keep that tab open.
6. Tap "Send test notification" in the app.

The page needs GitHub Pages enabled for this repo (Settings > Pages > deploy from `main`, root).

Anyone who knows the topic can read your forwarded notifications, so don't share the link. Edit `Config.PACKAGES` to forward other apps.
