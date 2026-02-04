package com.opencode.client.data.api

import com.opencode.client.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface OpenCodeApiService {

    @GET("remote/health")
    suspend fun health(): Response<HealthResponse>

    @GET("remote/workspace")
    suspend fun getWorkspace(): Response<WorkspaceResponse>

    @POST("remote/execute")
    suspend fun execute(
        @Body request: RemoteCommandRequest,
        @Header("Authorization") authorization: String? = null
    ): Response<RemoteCommandResponse>

    @GET("remote/commands")
    suspend fun getCommands(): Response<CommandsListResponse>
}
