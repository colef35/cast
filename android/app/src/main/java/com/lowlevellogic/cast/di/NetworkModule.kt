package com.lowlevellogic.cast.di

import com.lowlevellogic.cast.data.api.CastApi
import com.lowlevellogic.cast.data.prefs.UserPrefs
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideRetrofit(prefs: UserPrefs): Retrofit = Retrofit.Builder()
        .baseUrl(prefs.apiUrl.trimEnd('/') + "/")
        .client(OkHttpClient.Builder().build())
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    @Provides
    @Singleton
    fun provideCastApi(retrofit: Retrofit): CastApi = retrofit.create(CastApi::class.java)
}
