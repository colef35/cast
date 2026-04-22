package com.lowlevellogic.cast.data.models

import com.google.gson.annotations.SerializedName

data class Opportunity(
    val id: String,
    @SerializedName("product_id") val productId: String,
    val channel: String,
    @SerializedName("source_url") val sourceUrl: String,
    @SerializedName("source_title") val sourceTitle: String,
    @SerializedName("source_body") val sourceBody: String,
    @SerializedName("relevance_score") val relevanceScore: Float,
    @SerializedName("roi_score") val roiScore: Float,
    val draft: String?,
    val status: String,
    @SerializedName("created_at") val createdAt: String,
)
