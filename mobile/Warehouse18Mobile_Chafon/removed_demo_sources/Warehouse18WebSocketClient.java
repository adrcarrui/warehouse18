package com.UHF.scanlable;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import org.json.JSONObject;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

public class Warehouse18WebSocketClient {

    private static final String TAG = "Warehouse18WS";

    private final OkHttpClient client;
    private WebSocket webSocket;
    private Listener listener;

    public interface Listener {
        void onConnected();
        void onDisconnected();
        void onError(String message);
        void onTargetEpcReceived(String epc, String mode, String itemKey);
    }

    public Warehouse18WebSocketClient(Listener listener) {
        this.listener = listener;
        this.client = new OkHttpClient();
    }

    public void connect(String serverIp, String deviceId) {
        String url = "ws://" + serverIp + ":8000/api/rfid/pistol/ws/" + deviceId;

        Request request = new Request.Builder()
                .url(url)
                .build();

        webSocket = client.newWebSocket(request, new WebSocketListener() {

            @Override
            public void onOpen(@NonNull WebSocket webSocket, @NonNull Response response) {
                Log.d(TAG, "Connected");
                if (listener != null) listener.onConnected();
            }

            @Override
            public void onMessage(@NonNull WebSocket webSocket, @NonNull String text) {
                Log.d(TAG, "Received: " + text);

                try {
                    JSONObject json = new JSONObject(text);
                    String type = json.optString("type", "");

                    if ("target_epc".equals(type)) {
                        String epc = json.optString("epc", "");
                        String mode = json.optString("mode", "search");
                        String itemKey = json.optString("itemKey", "");

                        if (listener != null) {
                            listener.onTargetEpcReceived(epc, mode, itemKey);
                        }
                    }

                } catch (Exception e) {
                    Log.e(TAG, "Invalid message", e);
                    if (listener != null) listener.onError("Invalid message");
                }
            }

            @Override
            public void onFailure(@NonNull WebSocket webSocket, @NonNull Throwable t, @Nullable Response response) {
                Log.e(TAG, "WS Error", t);
                if (listener != null) listener.onError(t.getMessage());
            }

            @Override
            public void onClosed(@NonNull WebSocket webSocket, int code, @NonNull String reason) {
                Log.d(TAG, "Closed");
                if (listener != null) listener.onDisconnected();
            }
        });
    }

    public void disconnect() {
        if (webSocket != null) {
            webSocket.close(1000, "Closed");
            webSocket = null;
        }
    }
}