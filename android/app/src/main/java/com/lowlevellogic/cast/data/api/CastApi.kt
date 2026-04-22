package com.lowlevellogic.cast.data.api

import com.lowlevellogic.cast.data.models.Opportunity
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.Path
import retrofit2.http.Query

interface CastApi {
    @GET("opportunities/pending")
    suspend fun getPending(@Query("user_id") userId: String): List<Opportunity>

    @PATCH("opportunities/{id}/approve")
    suspend fun approve(
        @Path("id") id: String,
        @Query("user_id") userId: String,
    ): Opportunity

    @PATCH("opportunities/{id}/reject")
    suspend fun reject(
        @Path("id") id: String,
        @Query("user_id") userId: String,
    ): Opportunity
}
