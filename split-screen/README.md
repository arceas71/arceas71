# Split Screen

Small Android app that toggles split-screen mode on any app. Built for the Realme Narzo N53 (Realme UI, Android 13) but works on any Android 7+ phone.

Two ways to trigger it: a draggable floating button, or a Quick Settings tile.

## Install

Download `SplitScreen.apk` from the latest GitHub Release (or Actions > "Build Split Screen APK" > `split-screen-debug-apk`).

## Setup

1. Open the app and tap "Enable accessibility service", then turn on Split Screen. If it is greyed out: App info > three dots > Allow restricted settings.
2. Open any app, tap the floating button (or the tile), then pick a second app from recents.
3. Add the tile: swipe down twice > edit icon > drag "Split screen" in.

If an app won't split: Developer options > Force activities to be resizable, then reboot.

The accessibility service is only used to call Android's own toggle-split-screen action. It does not read or store screen content.
