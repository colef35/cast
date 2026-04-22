package com.lowlevellogic.cast.data.models

import com.google.gson.annotations.SerializedName

data class Stats(
    val opportunities: OpportunityStats,
    val subscribers: SubscriberStats,
)

data class OpportunityStats(
    val total: Int,
    @SerializedName("last_24h") val last24h: Int,
    @SerializedName("last_7d") val last7d: Int,
    @SerializedName("by_channel") val byChannel: Map<String, Int>,
    val pending: Int,
    val sent: Int,
)

data class SubscriberStats(
    @SerializedName("total_active") val totalActive: Int,
    @SerializedName("by_plan") val byPlan: Map<String, Int>,
)
