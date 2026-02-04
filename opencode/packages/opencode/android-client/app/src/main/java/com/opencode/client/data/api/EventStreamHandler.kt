package com.opencode.client.data.api

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonSyntaxException
import com.opencode.client.data.model.ConnectionConfig
import com.opencode.client.data.model.ServerEvent
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.receiveAsFlow
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class EventStreamHandler(private val config: ConnectionConfig) {

    private val TAG = "EventStreamHandler"
    private val gson = Gson()

    private val _eventChannel = Channel<ServerEvent>(Channel.BUFFERED)
    val eventFlow: Flow<ServerEvent> = _eventChannel.receiveAsFlow()

    private var eventSource: EventSource? = null
    private var client: OkHttpClient? = null

    fun connect() {
        val url = buildEventUrl()

        client = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(0, TimeUnit.SECONDS) // Disable read timeout for SSE
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()

        val request = Request.Builder()
            .url(url)
            .build()

        eventSource = EventSources.createFactory(client!!)
            .newEventSource(request, object : EventSourceListener() {
                override fun onOpen(eventSource: EventSource, response: Response) {
                    Log.d(TAG, "SSE connection opened")
                }

                override fun onEvent(
                    eventSource: EventSource,
                    id: String?,
                    type: String?,
                    data: String
                ) {
                    try {
                        val json = JSONObject(data)
                        val eventType = json.optString("type")
                        val properties = json.optJSONObject("properties")?.let { props ->
                            val map = mutableMapOf<String, Any>()
                            props.keys().forEach { key ->
                                map[key] = props.get(key).toString()
                            }
                            map
                        }

                        val event = ServerEvent(eventType, properties)
                        _eventChannel.trySend(event)
                        Log.d(TAG, "Event received: $eventType")
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to parse event: $data", e)
                    }
                }

                override fun onClosed(eventSource: EventSource) {
                    Log.d(TAG, "SSE connection closed")
                    _eventChannel.close()
                }

                override fun onFailure(
                    eventSource: EventSource,
                    t: Throwable?,
                    response: Response?
                ) {
                    Log.e(TAG, "SSE connection failed", t)
                    _eventChannel.close(t)
                }
            })
    }

    private fun buildEventUrl(): String {
        val baseUrl = config.serverUrl.removeSuffix("/")
        val auth = config.getAuthHeaders()["Authorization"]
        val authParam = auth?.removePrefix("Basic ")
            ?.let { "?auth=$it" } ?: ""
        return "$baseUrl/event$authParam"
    }

    fun disconnect() {
        eventSource?.cancel()
        eventSource = null
        client?.dispatcher?.executorService?.shutdown()
        client = null
    }

    fun isConnected(): Boolean {
        return eventSource != null
    }
}
