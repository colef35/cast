package com.lowlevellogic.cast.data.prefs

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UserPrefs @Inject constructor(@ApplicationContext private val context: Context) {

    private val prefs = context.getSharedPreferences("cast_prefs", Context.MODE_PRIVATE)

    var userId: String
        get() = prefs.getString("user_id", null) ?: UUID.randomUUID().toString().also { userId = it }
        set(value) = prefs.edit().putString("user_id", value).apply()

    var productId: String
        get() = prefs.getString("product_id", "") ?: ""
        set(value) = prefs.edit().putString("product_id", value).apply()

    var apiUrl: String
        get() = prefs.getString("api_url", "https://cast-production-e73f.up.railway.app") ?: "https://cast-production-e73f.up.railway.app"
        set(value) = prefs.edit().putString("api_url", value).apply()
}
