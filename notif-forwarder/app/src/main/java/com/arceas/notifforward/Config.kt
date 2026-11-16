package com.arceas.notifforward

object Config {
    const val PREFS = "notif_forwarder"
    const val KEY_TOPIC = "topic"

    const val LAPTOP_PAGE = "https://arceas71.github.io/y.html"

    // Apps whose notifications get forwarded.
    val PACKAGES = setOf(
        "com.instagram.android",
        "com.instagram.lite"
    )
}
