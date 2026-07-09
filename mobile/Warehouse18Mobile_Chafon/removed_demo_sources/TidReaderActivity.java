package com.UHF.scanlable;

import com.adrian.chafonscanner.R;
import com.rfid.trans.ReadTag;
import com.rfid.trans.ReaderParameter;
import com.rfid.trans.TagCallback;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import java.util.Locale;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class TidReaderActivity extends AppCompatActivity {

    private TextView txtStatus;
    private TextView txtTid;
    private TextView txtLog;
    private Button btnReadTid;
    private Button btnClear;
    private ScrollView scrollLog;

    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private static final byte TID_BANK = 0x02;
    private static final int START_WORD = 0;
    private static final byte WORD_COUNT = 6;
    private static final String PASSWORD = "00000000";

    private volatile boolean isConnected = false;
    private volatile String lastEpc = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_tid_reader);

        scrollLog = findViewById(R.id.scrollLog);
        txtStatus = findViewById(R.id.txtStatus);
        txtTid = findViewById(R.id.txtTid);
        txtLog = findViewById(R.id.txtLog);
        btnReadTid = findViewById(R.id.btnReadTid);
        btnClear = findViewById(R.id.btnClear);

        btnReadTid.setOnClickListener(v -> readTidAsync());

        btnClear.setOnClickListener(v -> {
            txtTid.setText("-");
            txtStatus.setText("Estado: esperando lectura...");
            txtLog.setText("");
            lastEpc = null;
        });

        appendLog("Pantalla TID iniciada.");
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        try {
            Reader.rrlib.StopRead();
        } catch (Exception ignored) {
        }

        try {
            Reader.rrlib.DisConnect();
        } catch (Exception ignored) {
        }

        try {
            OtgUtils.setPOGOPINEnable(false);
        } catch (Exception ignored) {
        }

        isConnected = false;
    }

    private void readTidAsync() {
        btnReadTid.setEnabled(false);
        txtStatus.setText("Estado: leyendo EPC + TID...");
        appendLog("================================");
        appendLog("Iniciando lectura EPC + TID...");

        new Thread(() -> {
            try {
                if (!connectReader()) {
                    showFailure("No se pudo conectar con el lector RFID.");
                    return;
                }

                String epc = readSingleEpc();

                if (epc == null || epc.trim().isEmpty()) {
                    showFailure("No se ha leído EPC. Acerca una sola etiqueta.");
                    return;
                }

                appendLog("EPC leído: " + epc);

                String tid = readTidUsingEpc(epc);

                if (tid == null || tid.trim().isEmpty() || isOnlyZeros(tid)) {
                    appendLog("TID vacío.");
                    appendLog("Posibles causas:");
                    appendLog("1) La etiqueta está lejos.");
                    appendLog("2) Hay varias etiquetas cerca.");
                    appendLog("3) La etiqueta no permite leer ese bloque TID.");
                    appendLog("4) Hay que ajustar longitud de lectura.");
                    showFailure("No se ha leído ningún TID.");
                    return;
                }

                String finalTid = tid.toUpperCase(Locale.ROOT);

                mainHandler.post(() -> {
                    txtTid.setText(finalTid);
                    txtStatus.setText("Estado: TID leído correctamente");
                    appendLog("TID leído: " + finalTid);
                    btnReadTid.setEnabled(true);
                });

            } catch (Exception e) {
                mainHandler.post(() -> {
                    txtStatus.setText("Estado: error leyendo TID");
                    appendLog("ERROR: " + e.getClass().getSimpleName());
                    appendLog("MENSAJE: " + e.getMessage());
                    btnReadTid.setEnabled(true);
                });
            }
        }).start();
    }

    private boolean connectReader() {
        if (isConnected) {
            appendLog("Lector ya conectado.");
            return true;
        }

        try {
            appendLog("Activando POGO PIN...");
            OtgUtils.setPOGOPINEnable(true);

            appendLog("Conectando a /dev/ttyHSL0 a 57600...");
            int result = Reader.rrlib.Connect("/dev/ttyHSL0", 57600, 1);
            appendLog("Resultado conexión 57600: " + result);

            if (result != 0) {
                appendLog("Probando conexión a 115200...");
                result = Reader.rrlib.Connect("/dev/ttyHSL0", 115200, 1);
                appendLog("Resultado conexión 115200: " + result);
            }

            isConnected = result == 0;

            if (isConnected) {
                appendLog("Lector RFID conectado.");
                initRfid();
            } else {
                appendLog("No se pudo conectar al lector RFID.");
            }

            return isConnected;

        } catch (Exception e) {
            appendLog("Error conectando lector: " + e.getMessage());
            isConnected = false;
            return false;
        }
    }

    private void initRfid() {
        try {
            int readerType = Reader.rrlib.GetReaderType();
            ReaderParameter param = Reader.rrlib.GetInventoryPatameter();

            appendLog("ReaderType: " + readerType);

            if (readerType == 0x21
                    || readerType == 0x28
                    || readerType == 0x23
                    || readerType == 0x37
                    || readerType == 0x36) {
                param.Session = 1;
            } else if (readerType == 0x70
                    || readerType == 0x71
                    || readerType == 0x31) {
                param.Session = 254;
            } else if (readerType == 0x61
                    || readerType == 0x63
                    || readerType == 0x65
                    || readerType == 0x66) {
                param.Session = 1;
            } else {
                param.Session = 0;
            }

            Reader.rrlib.SetInventoryPatameter(param);
            appendLog("Parámetros RFID inicializados. Session=" + param.Session);

        } catch (Exception e) {
            appendLog("No se pudieron inicializar parámetros RFID: " + e.getMessage());
        }
    }

    private String readSingleEpc() {
        try {
            appendLog("Iniciando inventario para obtener EPC...");

            CountDownLatch latch = new CountDownLatch(1);
            final String[] scannedEpc = new String[]{null};

            Reader.rrlib.SetCallBack(new TagCallback() {
                @Override
                public void tagCallback(ReadTag tag) {
                    if (tag == null) {
                        return;
                    }

                    String epc = tag.epcId;

                    if (epc != null) {
                        epc = epc.trim().toUpperCase(Locale.ROOT);
                    }

                    if (epc != null && !epc.isEmpty() && scannedEpc[0] == null) {
                        scannedEpc[0] = epc;
                        lastEpc = epc;
                        appendLog("Callback EPC: " + epc);
                        latch.countDown();
                    }
                }

                @Override
                public void StopReadCallBack() {
                    appendLog("StopReadCallBack recibido.");
                }
            });

            int startResult = Reader.rrlib.StartRead();
            appendLog("StartRead resultado: " + startResult);

            if (startResult != 0) {
                return null;
            }

            latch.await(1200, TimeUnit.MILLISECONDS);

            try {
                Reader.rrlib.StopRead();
                appendLog("StopRead ejecutado.");
            } catch (Exception e) {
                appendLog("Error en StopRead: " + e.getMessage());
            }

            if (scannedEpc[0] == null || scannedEpc[0].isEmpty()) {
                appendLog("No se recibió EPC por callback.");
            }

            return scannedEpc[0];

        } catch (Exception e) {
            appendLog("Error leyendo EPC: " + e.getMessage());

            try {
                Reader.rrlib.StopRead();
            } catch (Exception ignored) {
            }

            return null;
        }
    }

    private String readTidUsingEpc(String epc) {
        try {
            appendLog("Leyendo TID usando EPC...");
            appendLog("EPC usado: " + epc);
            appendLog("MemBank: 02 = TID");
            appendLog("WordPtr: " + START_WORD);
            appendLog("WordCount: " + WORD_COUNT);

            /*
             * Firma del SDK:
             * ReadData_G2(String EPC, byte Mem, int WordPtr, byte Num, String Password)
             *
             * Es más limpia que ExtReadData_G2 porque el SDK se encarga
             * de convertir el EPC internamente. Milagro menor, pero milagro.
             */
            String result = Reader.rrlib.ReadData_G2(
                    epc,
                    TID_BANK,
                    START_WORD,
                    WORD_COUNT,
                    PASSWORD
            );

            appendLog("Resultado ReadData_G2 String: " + String.valueOf(result));

            if (result == null) {
                return "";
            }

            result = result.trim().toUpperCase(Locale.ROOT);

            /*
             * Algunos SDKs devuelven texto de error o vacío.
             */
            if (result.equals("NULL") || result.equals("ERROR") || result.equals("FAIL")) {
                return "";
            }

            return result;

        } catch (Exception e) {
            appendLog("Error leyendo TID con EPC: " + e.getMessage());
            return "";
        }
    }

    private void showFailure(String message) {
        mainHandler.post(() -> {
            txtStatus.setText("Estado: " + message);
            appendLog(message);
            btnReadTid.setEnabled(true);
        });
    }

    private boolean isOnlyZeros(String value) {
        if (value == null) {
            return true;
        }

        String clean = value.trim().replace(" ", "");

        if (clean.isEmpty()) {
            return true;
        }

        for (int i = 0; i < clean.length(); i++) {
            if (clean.charAt(i) != '0') {
                return false;
            }
        }

        return true;
    }

    private void appendLog(String message) {
        mainHandler.post(() -> {
            if (txtLog != null) {
                txtLog.append(message + "\n");

                if (scrollLog != null) {
                    scrollLog.post(() -> scrollLog.fullScroll(ScrollView.FOCUS_DOWN));
                }
            }
        });
    }
}