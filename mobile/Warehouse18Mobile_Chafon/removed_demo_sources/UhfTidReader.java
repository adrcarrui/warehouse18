package com.UHF.scanlable;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Locale;

public class UhfTidReader {

    private static final String[] READER_CLASS_CANDIDATES = new String[]{
            "com.UHF.scanlable.Reader",
            "com.uhf.scanlable.Reader",
            "com.handheld.uhfr.Reader",
            "com.example.tidreader.Reader"
    };

    private static final String[] READER_FIELD_CANDIDATES = new String[]{
            "rrlib",
            "mReader",
            "reader",
            "uhfReader",
            "rfidReader"
    };

    private static final int TID_BANK = 2;
    private static final int START_WORD = 0;
    private static final int WORD_COUNT = 6;

    private final LogSink log;

    public UhfTidReader(LogSink log) {
        this.log = log;
    }

    public TidResult readTid() {
        try {
            Object reader = findReaderObject();
            if (reader == null) {
                return TidResult.fail("No se encontró el objeto del SDK. Copia Reader.java/librerías de la demo original.");
            }

            Class<?> sdkClass = reader instanceof Class ? (Class<?>) reader : reader.getClass();
            Object invokeTarget = reader instanceof Class ? null : reader;

            Method method = findReadDataMethod(sdkClass);
            if (method == null) {
                return TidResult.fail("No se encontró método ReadData_G2/readData compatible. Pulsa 'Ver métodos SDK'.");
            }

            log("Método candidato: " + methodToString(method));
            TidResult direct = tryInvokeKnownSignature(invokeTarget, method);
            if (direct != null) return direct;

            return TidResult.fail("El método existe, pero esta firma aún no está soportada: " + methodToString(method));
        } catch (Throwable t) {
            return TidResult.fail(t.getClass().getSimpleName() + ": " + safe(t.getMessage()));
        }
    }

    public String describeAvailableSdkMethods() {
        StringBuilder sb = new StringBuilder();

        try {
            Object reader = findReaderObject();
            if (reader == null) {
                sb.append("No se ha encontrado Reader/rrlib.\n");
                sb.append("Solución: copia las clases y librerías del SDK original dentro de este proyecto o usa la versión drop-in sobre tu app demo.\n");
                return sb.toString();
            }

            Class<?> clazz = reader instanceof Class ? (Class<?>) reader : reader.getClass();
            sb.append("Objeto SDK encontrado: ").append(clazz.getName()).append("\n");
            sb.append("Métodos que parecen útiles:\n");

            for (Method m : clazz.getMethods()) {
                String name = m.getName().toLowerCase(Locale.ROOT);
                if (name.contains("read") || name.contains("inventory") || name.contains("tid") || name.contains("g2")) {
                    sb.append(" - ").append(methodToString(m)).append("\n");
                }
            }

        } catch (Throwable t) {
            sb.append("Error listando métodos: ").append(t.getClass().getSimpleName()).append(": ").append(safe(t.getMessage())).append("\n");
        }

        return sb.toString();
    }

    private Object findReaderObject() {
        for (String className : READER_CLASS_CANDIDATES) {
            try {
                Class<?> readerClass = Class.forName(className);
                log("Clase Reader encontrada: " + className);

                for (String fieldName : READER_FIELD_CANDIDATES) {
                    try {
                        Field field = readerClass.getDeclaredField(fieldName);
                        field.setAccessible(true);
                        Object value = field.get(null);
                        if (value != null) {
                            log("Campo SDK encontrado: " + className + "." + fieldName);
                            return value;
                        }
                    } catch (Throwable ignored) {
                    }
                }

                // Si la clase Reader expone métodos estáticos, devolvemos su Class para inspección.
                return readerClass;

            } catch (Throwable ignored) {
            }
        }

        return null;
    }

    private Method findReadDataMethod(Class<?> clazz) {
        Method best = null;

        for (Method method : clazz.getMethods()) {
            String name = method.getName().toLowerCase(Locale.ROOT);
            if (name.equals("readdata_g2")) {
                return method;
            }
            if (name.contains("readdata") && name.contains("g2")) {
                best = method;
            }
        }

        if (best != null) return best;

        for (Method method : clazz.getMethods()) {
            String name = method.getName().toLowerCase(Locale.ROOT);
            if (name.contains("read") && name.contains("data")) {
                best = method;
            }
        }

        return best;
    }

    private TidResult tryInvokeKnownSignature(Object reader, Method method) throws Exception {
        Class<?>[] types = method.getParameterTypes();
        String signature = methodToString(method);

        // Firma habitual EPCC1-G2 con 14 parámetros y FrmHandle al final.
        // ReadData_G2(byte[] ComAdr, byte[] EPC, byte ENum, byte Mem, byte WordPtr, byte Num,
        //             byte[] Password, byte MaskMem, byte[] MaskAdr, byte MaskLen, byte[] MaskData,
        //             byte[] Data, int[] Errorcode, int FrmHandle)
        if (types.length == 14) {
            byte[] comAdr = new byte[]{(byte) 0xFF};
            byte[] epc = new byte[0];
            byte eNum = 0;
            byte mem = (byte) TID_BANK;
            byte wordPtr = (byte) START_WORD;
            byte num = (byte) WORD_COUNT;
            byte[] password = hexToBytes("00000000");
            byte maskMem = 0;
            byte[] maskAdr = new byte[]{0x00, 0x00};
            byte maskLen = 0;
            byte[] maskData = new byte[0];
            byte[] data = new byte[WORD_COUNT * 2];
            int[] errorCode = new int[]{0};
            int frameHandle = findFrameHandle();

            Object ret = method.invoke(reader, comAdr, epc, eNum, mem, wordPtr, num, password,
                    maskMem, maskAdr, maskLen, maskData, data, errorCode, frameHandle);

            String tid = bytesToHex(data);
            log("Retorno SDK: " + String.valueOf(ret) + ", ErrorCode: " + errorCode[0] + ", FrmHandle: " + frameHandle);

            if (looksLikeEmpty(tid)) {
                return TidResult.fail("Lectura vacía. Revisa antena, distancia, etiqueta o firma del método.", signature);
            }
            return TidResult.ok(tid, signature);
        }

        // Variante sin FrmHandle.
        if (types.length == 13) {
            byte[] comAdr = new byte[]{(byte) 0xFF};
            byte[] epc = new byte[0];
            byte eNum = 0;
            byte mem = (byte) TID_BANK;
            byte wordPtr = (byte) START_WORD;
            byte num = (byte) WORD_COUNT;
            byte[] password = hexToBytes("00000000");
            byte maskMem = 0;
            byte[] maskAdr = new byte[]{0x00, 0x00};
            byte maskLen = 0;
            byte[] maskData = new byte[0];
            byte[] data = new byte[WORD_COUNT * 2];
            int[] errorCode = new int[]{0};

            Object ret = method.invoke(reader, comAdr, epc, eNum, mem, wordPtr, num, password,
                    maskMem, maskAdr, maskLen, maskData, data, errorCode);

            String tid = bytesToHex(data);
            log("Retorno SDK: " + String.valueOf(ret) + ", ErrorCode: " + errorCode[0]);

            if (looksLikeEmpty(tid)) {
                return TidResult.fail("Lectura vacía. Revisa antena, distancia, etiqueta o firma del método.", signature);
            }
            return TidResult.ok(tid, signature);
        }

        // Variante frecuente en SDKs tipo readData(String pwd, int bank, int ptr, int count)
        if (types.length == 4
                && types[0] == String.class
                && isIntLike(types[1])
                && isIntLike(types[2])
                && isIntLike(types[3])) {
            Object ret = method.invoke(reader, "00000000", TID_BANK, START_WORD, WORD_COUNT);
            String tid = normalizeReturnedTid(ret);
            if (tid.length() > 0) return TidResult.ok(tid, signature);
            return TidResult.fail("El método devolvió vacío: " + String.valueOf(ret), signature);
        }

        // Variante con filtro: readData(String pwd, int bank, int ptr, int count, String filter, int filterBank, int filterPtr, boolean filter)
        if (types.length == 8
                && types[0] == String.class
                && isIntLike(types[1])
                && isIntLike(types[2])
                && isIntLike(types[3])
                && types[4] == String.class
                && isIntLike(types[5])
                && isIntLike(types[6])
                && types[7] == boolean.class) {
            Object ret = method.invoke(reader, "00000000", TID_BANK, START_WORD, WORD_COUNT, "", 1, 32, false);
            String tid = normalizeReturnedTid(ret);
            if (tid.length() > 0) return TidResult.ok(tid, signature);
            return TidResult.fail("El método devolvió vacío: " + String.valueOf(ret), signature);
        }

        return null;
    }

    private int findFrameHandle() {
        for (String className : READER_CLASS_CANDIDATES) {
            try {
                Class<?> readerClass = Class.forName(className);
                String[] names = new String[]{"FrmHandle", "frmHandle", "mFrmHandle", "handle", "mHandler"};
                for (String name : names) {
                    try {
                        Field f = readerClass.getDeclaredField(name);
                        f.setAccessible(true);
                        Object value = f.get(null);
                        if (value instanceof Integer) return (Integer) value;
                        if (value instanceof int[]) {
                            int[] arr = (int[]) value;
                            if (arr.length > 0) return arr[0];
                        }
                    } catch (Throwable ignored) {
                    }
                }
            } catch (Throwable ignored) {
            }
        }
        return 0;
    }

    private String normalizeReturnedTid(Object ret) {
        if (ret == null) return "";

        if (ret instanceof byte[]) {
            return bytesToHex((byte[]) ret);
        }

        String value = String.valueOf(ret).trim();
        value = value.replace(" ", "").replace("\n", "").replace("\r", "");

        if (value.equalsIgnoreCase("null")) return "";
        return value.toUpperCase(Locale.ROOT);
    }

    private boolean isIntLike(Class<?> c) {
        return c == int.class || c == Integer.class || c == byte.class || c == Byte.class || c == short.class || c == Short.class;
    }

    private boolean looksLikeEmpty(String hex) {
        if (hex == null || hex.length() == 0) return true;
        for (int i = 0; i < hex.length(); i++) {
            if (hex.charAt(i) != '0') return false;
        }
        return true;
    }

    private String methodToString(Method method) {
        StringBuilder sb = new StringBuilder();
        sb.append(method.getName()).append("(");
        Class<?>[] params = method.getParameterTypes();
        for (int i = 0; i < params.length; i++) {
            if (i > 0) sb.append(", ");
            sb.append(params[i].getSimpleName());
        }
        sb.append(")");
        return sb.toString();
    }

    private static byte[] hexToBytes(String hex) {
        hex = hex.replace(" ", "").trim();
        if (hex.length() % 2 != 0) hex = "0" + hex;
        byte[] out = new byte[hex.length() / 2];
        for (int i = 0; i < out.length; i++) {
            out[i] = (byte) Integer.parseInt(hex.substring(i * 2, i * 2 + 2), 16);
        }
        return out;
    }

    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) sb.append(String.format(Locale.ROOT, "%02X", b));
        return sb.toString();
    }

    private void log(String message) {
        if (log != null) log.write(message);
    }

    private String safe(String value) {
        return value == null ? "sin mensaje" : value;
    }

    public interface LogSink {
        void write(String message);
    }

    public static class TidResult {
        public final boolean success;
        public final String tid;
        public final String message;
        public final String methodUsed;

        private TidResult(boolean success, String tid, String message, String methodUsed) {
            this.success = success;
            this.tid = tid;
            this.message = message;
            this.methodUsed = methodUsed;
        }

        public static TidResult ok(String tid, String methodUsed) {
            return new TidResult(true, tid, "OK", methodUsed);
        }

        public static TidResult fail(String message) {
            return new TidResult(false, "", message, null);
        }

        public static TidResult fail(String message, String methodUsed) {
            return new TidResult(false, "", message, methodUsed);
        }
    }
}
