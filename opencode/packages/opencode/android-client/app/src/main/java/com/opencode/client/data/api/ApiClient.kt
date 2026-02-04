package com.opencode.client.data.api

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.opencode.client.data.model.ConnectionConfig
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    private const val DEFAULT_TIMEOUT = 30L

    private var _apiService: OpenCodeApiService? = null
    private var _baseUrl: String = "http://localhost:4096/"
    private var _connectionConfig: ConnectionConfig? = null

    val apiService: OpenCodeApiService
        get() = _apiService ?: createApiService()

    val baseUrl: String
        get() = _baseUrl

    fun setBaseUrl(url: String) {
        _baseUrl = url
        _apiService = null // Force recreation
    }

    fun setConnectionConfig(config: ConnectionConfig) {
        _connectionConfig = config
        setBaseUrl(config.serverUrl)
        _apiService = null // Force recreation
    }

    private fun createGson(): Gson {
        return GsonBuilder()
            .setLenient()
            .create()
    }

    private fun createOkHttpClient(): OkHttpClient {
        val builder = OkHttpClient.Builder()
            .connectTimeout(DEFAULT_TIMEOUT, TimeUnit.SECONDS)
            .readTimeout(DEFAULT_TIMEOUT, TimeUnit.SECONDS)
            .writeTimeout(DEFAULT_TIMEOUT, TimeUnit.SECONDS)

        // Add logging
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        builder.addInterceptor(loggingInterceptor)

        // Add auth header if available
        _connectionConfig?.let { config ->
            builder.addInterceptor { chain ->
                val original = chain.request()
                val requestBuilder = original.newBuilder()

                config.getAuthHeaders()["Authorization"]?.let { auth ->
                    requestBuilder.header("Authorization", auth)
                }

                chain.proceed(requestBuilder.build())
            }
        }

        return builder.build()
    }

    private fun createApiService(): OpenCodeApiService {
        val retrofit = Retrofit.Builder()
            .baseUrl(_baseUrl.removeSuffix("/") + "/")
            .client(createOkHttpClient())
            .addConverterFactory(GsonConverterFactory.create(createGson()))
            .build()

        return retrofit.create(OpenCodeApiService::class.java).also {
            _apiService = it
        }
    }

    fun reset() {
        _apiService = null
        _connectionConfig = null
        _baseUrl = "http://localhost:4096/"
    }
}
