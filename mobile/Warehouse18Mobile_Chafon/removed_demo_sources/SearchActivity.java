package com.UHF.scanlable;

import android.os.Bundle;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.Button;
import com.adrian.chafonscanner.R;
import androidx.appcompat.app.AppCompatActivity;

public class SearchActivity extends AppCompatActivity {

    private Warehouse18WebSocketClient wsClient;
    private TextView txtReceivedEpc;
    private TextView txtConnectionStatus;

    private static final String SERVER_IP = "192.168.137.1";
    private static final String DEVICE_ID = "pistol-01";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_search);

        txtReceivedEpc = findViewById(R.id.txtReceivedEpc);
        txtConnectionStatus = findViewById(R.id.txtConnectionStatus);

        connectToWarehouse18();
    }

    private void connectToWarehouse18() {
        wsClient = new Warehouse18WebSocketClient(new Warehouse18WebSocketClient.Listener() {

            @Override
            public void onConnected() {
                runOnUiThread(() -> {
                    txtConnectionStatus.setText("Connected to Warehouse18");
                    Toast.makeText(
                            SearchActivity.this,
                            "Connected",
                            Toast.LENGTH_SHORT
                    ).show();
                });
            }

            @Override
            public void onDisconnected() {
                runOnUiThread(() -> {
                    txtConnectionStatus.setText("Disconnected");
                    Toast.makeText(
                            SearchActivity.this,
                            "Disconnected",
                            Toast.LENGTH_SHORT
                    ).show();
                });
            }

            @Override
            public void onError(String message) {
                runOnUiThread(() -> {
                    txtConnectionStatus.setText("Error: " + message);
                    Toast.makeText(
                            SearchActivity.this,
                            "Error: " + message,
                            Toast.LENGTH_LONG
                    ).show();
                });
            }

            @Override
            public void onTargetEpcReceived(String epc, String mode, String itemKey) {
                runOnUiThread(() -> {
                    txtReceivedEpc.setText(epc);

                    Toast.makeText(
                            SearchActivity.this,
                            "EPC recibido",
                            Toast.LENGTH_SHORT
                    ).show();
                });
            }
        });

        wsClient.connect(SERVER_IP, DEVICE_ID);
    }
    private void reconnectToWarehouse18() {
        if (wsClient != null) {
            wsClient.disconnect();
        }

        txtConnectionStatus.setText("Reconnecting...");
        connectToWarehouse18();
    }
    @Override
    protected void onDestroy() {
        super.onDestroy();

        if (wsClient != null) {
            wsClient.disconnect();
        }
    }
}