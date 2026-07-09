package com.adrian.warehouse18mobile

import android.content.Context
import android.util.Log
import java.lang.reflect.InvocationHandler
import java.lang.reflect.Method
import java.lang.reflect.Proxy
import java.util.Locale
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Adapter for the Chafon / CF-H906-style SDK included in this project.
 *
 * The uploaded project includes rfiddrive-release.aar, whose useful runtime class is:
 *   com.rfid.trans.ReaderHelp
 *
 * The previous version only searched for RSCJA/Speedata-style classes, so the app showed:
 * "Chafon RFID SDK not found" even though the SDK was already inside app/libs.
 * Because apparently SDK naming consistency was too much civilization for one industry.
 */
class ChafonRfidController(
    private val context: Context
) : RfidController {

    @Volatile
    private var reader: Any? = null

    @Volatile
    private var listener: RfidController.Listener? = null

    private val inventoryRunning = AtomicBoolean(false)
    private var callbackProxy: Any? = null

    override val isConnected: Boolean
        get() = reader != null && runCatching {
            val current = reader ?: return@runCatching false
            val result = invokeFirst(
                target = current,
                candidates = listOf(MethodCall("isConnect")),
                required = false
            )
            result !is Boolean || result
        }.getOrDefault(reader != null)

    override fun setListener(listener: RfidController.Listener?) {
        this.listener = listener
    }

    override fun connect() {
        if (reader != null && isConnected) return

        enablePogoPin(true)
        Thread.sleep(700L)

        val instance = findReaderHelpInstance()
            ?: throw RuntimeException(
                "Chafon RFID SDK not found. Expected com.rfid.trans.ReaderHelp from rfiddrive-release.aar in app/libs."
            )

        // Clean any half-open session left by a previous inventory/search attempt.
        runCatching { invokeFirst(instance, listOf(MethodCall("StopRead")), required = false) }
        runCatching { invokeFirst(instance, listOf(MethodCall("DisConnect")), required = false) }
        Thread.sleep(250L)

        var connectionResult = connectSerial(instance)

        if (!connectionResult.connected) {
            // One retry with a full power toggle. This helps when Locate starts right after barcode scan
            // and the device has not released the scanner/serial path yet. Because apparently waiting
            // one second is now embedded engineering.
            enablePogoPin(false)
            Thread.sleep(450L)
            enablePogoPin(true)
            Thread.sleep(900L)
            runCatching { invokeFirst(instance, listOf(MethodCall("DisConnect")), required = false) }
            connectionResult = connectSerial(instance)
        }

        if (!connectionResult.connected) {
            reader = null
            enablePogoPin(false)
            throw RuntimeException(
                "Could not connect to Chafon RFID module. ${connectionResult.message}"
            )
        }

        reader = instance

        runCatching { invokeFirst(instance, listOf(MethodCall("SetLogSwitch", 0)), required = false) }
        initInventoryParameters(instance)
        trySetPower(instance, 30)
    }

    override fun disconnect() {
        stopInventory()

        val target = reader
        if (target != null) {
            runCatching {
                invokeFirst(
                    target = target,
                    candidates = listOf(MethodCall("DisConnect"), MethodCall("disconnect"), MethodCall("close")),
                    required = false
                )
            }
        }

        callbackProxy = null
        reader = null
        enablePogoPin(false)
    }

    override fun startInventory() {
        val target = reader ?: throw RuntimeException("Chafon RFID reader is not connected.")

        if (inventoryRunning.getAndSet(true)) return

        installTagCallback(target)

        val result = invokeFirst(
            target = target,
            candidates = listOf(
                MethodCall("StartRead"),
                MethodCall("startRead"),
                MethodCall("startInventory")
            )
        )

        if (result is Number && result.toInt() != 0) {
            inventoryRunning.set(false)
            throw RuntimeException("Chafon StartRead failed with code ${result.toInt()}.")
        }

        if (result is Boolean && !result) {
            inventoryRunning.set(false)
            throw RuntimeException("Chafon StartRead returned false.")
        }
    }

    override fun stopInventory() {
        inventoryRunning.set(false)

        val target = reader ?: return
        runCatching {
            invokeFirst(
                target = target,
                candidates = listOf(
                    MethodCall("StopRead"),
                    MethodCall("stopRead"),
                    MethodCall("stopInventory")
                ),
                required = false
            )
        }
    }

    override fun readTid(epc: String): String {
        val target = reader ?: throw RuntimeException("Chafon RFID reader is not connected.")
        val cleanEpc = normalizeHex(epc)

        val result = invokeFirst(
            target = target,
            candidates = listOf(
                // rfiddrive-release.aar / ReaderHelp:
                // ReadData_G2(String EPC, byte Mem, int WordPtr, byte Num, String Password)
                MethodCall("ReadData_G2", cleanEpc, 2, 0, 6, "00000000"),
                MethodCall("ReadData_G2", cleanEpc, 2, 0, 8, "00000000"),
                MethodCall("ReadData_G2", cleanEpc, 2, 0, 4, "00000000"),
                MethodCall("ReadDataByTID", cleanEpc, 2, 0, 6, hexToBytes("00000000")),
                // Generic fallbacks, for other firmware builds.
                MethodCall("readData", "00000000", 2, 0, 6, cleanEpc),
                MethodCall("readData", "00000000", 2, 0, 8, cleanEpc),
                MethodCall("readTID", cleanEpc),
                MethodCall("readTid", cleanEpc)
            )
        )

        val tid = normalizeHex(extractText(result))
        if (tid.equals("NULL", ignoreCase = true) || tid.equals("ERROR", ignoreCase = true) || tid.equals("FAIL", ignoreCase = true)) {
            return ""
        }
        return tid
    }

    override fun writeEpc(currentEpc: String, newEpc: String) {
        val target = reader ?: throw RuntimeException("Chafon RFID reader is not connected.")
        val cleanCurrent = normalizeHex(currentEpc)
        val cleanNew = normalizeHex(newEpc)

        if (cleanNew.isBlank() || cleanNew.length % 4 != 0) {
            throw RuntimeException("New EPC must be hex and word-aligned: $cleanNew")
        }

        // Keep only one tag close to the antenna. Some Chafon SDK calls write the nearest tag.
        val result = invokeFirst(
            target = target,
            candidates = listOf(
                // ReaderHelp: WriteEPC_G2(String EPC, String Password)
                MethodCall("WriteEPC_G2", cleanNew, "00000000"),
                // ReaderHelp: WriteData_G2(String EPC, String data, byte mem, int wordPtr, String password)
                MethodCall("WriteData_G2", cleanCurrent, cleanNew, 1, 2, "00000000"),
                // Generic fallbacks.
                MethodCall("writeEPC", "00000000", cleanNew),
                MethodCall("writeEpc", "00000000", cleanNew),
                MethodCall("writeData", "00000000", 1, 2, cleanNew, cleanCurrent)
            )
        )

        if (result is Number && result.toInt() != 0) {
            throw RuntimeException("Chafon write EPC failed with code ${result.toInt()}.")
        }

        if (result is Boolean && !result) {
            throw RuntimeException("Chafon write EPC returned false.")
        }

        val text = extractText(result).lowercase(Locale.ROOT)
        if (text.contains("fail") || text.contains("error")) {
            throw RuntimeException("Chafon write EPC failed: $text")
        }
    }

    private fun findReaderHelpInstance(): Any? {
        // The demo wrapper included in the uploaded project exposes Reader.rrlib.
        runCatching {
            val wrapperClass = Class.forName("com.UHF.scanlable.Reader")
            val field = wrapperClass.getDeclaredField("rrlib")
            field.isAccessible = true
            val value = field.get(null)
            if (value != null) return value
        }

        // Direct SDK class from rfiddrive-release.aar.
        return runCatching {
            Class.forName("com.rfid.trans.ReaderHelp").getDeclaredConstructor().newInstance()
        }.getOrNull()
    }

    private fun connectSerial(target: Any): SerialConnectResult {
        if (runCatching {
                invokeFirst(target, listOf(MethodCall("isConnect")), required = false) as? Boolean
            }.getOrNull() == true
        ) {
            return SerialConnectResult(true, "Already connected")
        }

        val ports = listOf(
            "/dev/ttyHSL0",
            "/dev/ttyS4",
            "/dev/ttyHS1",
            "/dev/ttyHSL1",
            "/dev/ttyHSL2",
            "/dev/ttyS3",
            "/dev/ttyS2",
            "/dev/ttyS1",
            "/dev/ttyMT1",
            "/dev/ttyMT0"
        )
        val baudRates = listOf(57600, 115200)

        val attempts = mutableListOf<String>()
        for (port in ports) {
            for (baud in baudRates) {
                val attemptLabel = "$port@$baud"
                val result = runCatching {
                    invokeFirst(target, listOf(MethodCall("Connect", port, baud, 1)))
                }.fold(
                    onSuccess = { it },
                    onFailure = { error ->
                        attempts.add("$attemptLabel=${error.cause?.message ?: error.message ?: error.javaClass.simpleName}")
                        null
                    }
                )

                if (result is Number) {
                    attempts.add("$attemptLabel=${result.toInt()}")
                    if (result.toInt() == 0) {
                        Log.d(TAG, "Connected Chafon RFID on $port at $baud")
                        return SerialConnectResult(true, "Connected on $attemptLabel")
                    }
                } else if (result is Boolean) {
                    attempts.add("$attemptLabel=$result")
                    if (result) {
                        Log.d(TAG, "Connected Chafon RFID on $port at $baud")
                        return SerialConnectResult(true, "Connected on $attemptLabel")
                    }
                } else if (result != null) {
                    attempts.add("$attemptLabel=$result")
                }
            }
        }

        val message = "Tried ${attempts.joinToString(", ").take(500)}"
        Log.e(TAG, "Chafon serial connection failed. $message")
        return SerialConnectResult(false, message)
    }

    private fun initInventoryParameters(target: Any) {
        runCatching {
            val readerType = (invokeFirst(target, listOf(MethodCall("GetReaderType")), required = false) as? Number)?.toInt()
            val params = invokeFirst(target, listOf(MethodCall("GetInventoryPatameter")), required = false)
                ?: return@runCatching

            val session = when (readerType) {
                0x21, 0x28, 0x23, 0x37, 0x36 -> 1
                0x70, 0x71, 0x31 -> 254
                0x61, 0x63, 0x65, 0x66 -> 1
                else -> 0
            }

            setFieldIfExists(params, "Session", session)
            setFieldIfExists(params, "ScanTime", 10)
            setFieldIfExists(params, "QValue", 4)
            setFieldIfExists(params, "Antenna", 1)

            invokeFirst(target, listOf(MethodCall("SetInventoryPatameter", params)), required = false)
            Log.d(TAG, "Chafon inventory params initialized. ReaderType=$readerType Session=$session")
        }.onFailure {
            Log.d(TAG, "Chafon inventory init ignored: ${it.message}")
        }
    }

    private fun trySetPower(target: Any, power: Int) {
        runCatching {
            invokeFirst(
                target = target,
                candidates = listOf(
                    MethodCall("SetRfPower", power),
                    MethodCall("SetWritePower", power),
                    MethodCall("setPower", power),
                    MethodCall("setOutputPower", power)
                ),
                required = false
            )
        }.onFailure {
            Log.d(TAG, "Chafon set power ignored: ${it.message}")
        }
    }

    private fun installTagCallback(target: Any) {
        val callbackClass = runCatching { Class.forName("com.rfid.trans.TagCallback") }.getOrNull()
            ?: return

        val proxy = Proxy.newProxyInstance(
            callbackClass.classLoader,
            arrayOf(callbackClass),
            InvocationHandler { _, method, args ->
                when (method.name) {
                    "tagCallback" -> {
                        val rawTag = args?.firstOrNull()
                        val tag = parseTagObject(rawTag)
                        if (tag != null && tag.epc.isNotBlank() && inventoryRunning.get()) {
                            listener?.onTagRead(tag)
                        }
                        null
                    }

                    "StopReadCallBack" -> null
                    else -> null
                }
            }
        )

        invokeFirst(target, listOf(MethodCall("SetCallBack", proxy)), required = false)
        callbackProxy = proxy
    }

    private fun parseTagObject(raw: Any?): RfidTag? {
        if (raw == null) return null

        if (raw is RfidTag) return raw
        if (raw is String) return parseTagString(raw)

        val epc = normalizeHex(
            readMemberText(raw, "epcId", "EPC", "epc", "getEPC", "getEpc", "getEPCString", "getEpcString")
        )

        if (epc.isBlank()) {
            return parseTagString(raw.toString())
        }

        val tid = normalizeHex(
            readMemberText(raw, "memId", "tid", "TID", "getTID", "getTid")
        ).takeIf { it.isNotBlank() }

        val rssi = readMemberText(raw, "rssi", "RSSI", "getRssi", "getRSSI")
            .toIntOrNull()

        return RfidTag(
            epc = epc,
            rssi = rssi,
            tid = tid
        )
    }

    private fun parseTagString(value: String): RfidTag? {
        val tokens = Regex("[0-9A-Fa-f]{8,}")
            .findAll(value)
            .map { it.value.uppercase(Locale.ROOT) }
            .toList()

        val epc = tokens.firstOrNull { it.length % 4 == 0 } ?: return null
        val rssi = Regex("RSSI[^-0-9]*(-?\\d+)", RegexOption.IGNORE_CASE)
            .find(value)
            ?.groupValues
            ?.getOrNull(1)
            ?.toIntOrNull()

        return RfidTag(epc = epc, rssi = rssi)
    }

    private fun enablePogoPin(enable: Boolean) {
        runCatching {
            val clazz = Class.forName("com.UHF.scanlable.OtgUtils")
            val method = clazz.methods.firstOrNull { it.name == "setPOGOPINEnable" && it.parameterCount == 1 }
            method?.invoke(null, enable)
        }.onFailure {
            Log.d(TAG, "POGO pin control ignored: ${it.message}")
        }

        // Secondary SDK helper. It exists in some rfiddrive builds.
        runCatching {
            val clazz = Class.forName("com.rfid.trans.OtgUtils")
            val method = clazz.methods.firstOrNull { it.name == "set53GPIOEnabled" && it.parameterCount == 1 }
            method?.invoke(null, enable)
        }
    }

    private fun setFieldIfExists(target: Any, fieldName: String, value: Int) {
        runCatching {
            val field = target.javaClass.fields.firstOrNull { it.name == fieldName }
                ?: target.javaClass.declaredFields.firstOrNull { it.name == fieldName }
                ?: return
            field.isAccessible = true
            when (field.type) {
                java.lang.Integer.TYPE, java.lang.Integer::class.java -> field.set(target, value)
                java.lang.Byte.TYPE, java.lang.Byte::class.java -> field.set(target, value.toByte())
                java.lang.Short.TYPE, java.lang.Short::class.java -> field.set(target, value.toShort())
                else -> field.set(target, value)
            }
        }
    }

    private fun invokeFirst(
        target: Any,
        candidates: List<MethodCall>,
        required: Boolean = true
    ): Any? {
        val errors = mutableListOf<String>()

        for (candidate in candidates) {
            try {
                val method = findCompatibleMethod(
                    target = target,
                    name = candidate.name,
                    args = candidate.args
                ) ?: continue

                method.isAccessible = true
                return method.invoke(target, *coerceArgs(method, candidate.args))
            } catch (ex: Exception) {
                errors.add("${candidate.name}(${candidate.args.size}): ${ex.cause?.message ?: ex.message}")
            }
        }

        if (required) {
            throw NoSuchMethodException(
                "No compatible Chafon SDK method found. Tried: ${errors.ifEmpty { candidates.map { it.name } }.joinToString("; ")}"
            )
        }

        return null
    }

    private fun findCompatibleMethod(target: Any, name: String, args: Array<out Any?>): Method? {
        return target.javaClass.methods.firstOrNull { method ->
            method.name == name && method.parameterTypes.size == args.size && canCoerce(method.parameterTypes, args)
        }
    }

    private fun canCoerce(parameterTypes: Array<Class<*>>, args: Array<out Any?>): Boolean {
        return parameterTypes.indices.all { index ->
            val arg = args[index] ?: return@all !parameterTypes[index].isPrimitive
            val type = wrapPrimitive(parameterTypes[index])

            when {
                type.isAssignableFrom(arg.javaClass) -> true
                type == java.lang.Integer::class.java && arg is Number -> true
                type == java.lang.Long::class.java && arg is Number -> true
                type == java.lang.Short::class.java && arg is Number -> true
                type == java.lang.Byte::class.java && arg is Number -> true
                type == java.lang.Boolean::class.java && arg is Boolean -> true
                type == String::class.java -> true
                type.isArray && arg.javaClass.isArray -> true
                else -> false
            }
        }
    }

    private fun coerceArgs(method: Method, args: Array<out Any?>): Array<Any?> {
        return method.parameterTypes.mapIndexed { index, rawType ->
            val type = wrapPrimitive(rawType)
            val arg = args[index]

            when {
                arg == null -> null
                type == java.lang.Integer::class.java && arg is Number -> arg.toInt()
                type == java.lang.Long::class.java && arg is Number -> arg.toLong()
                type == java.lang.Short::class.java && arg is Number -> arg.toShort()
                type == java.lang.Byte::class.java && arg is Number -> arg.toByte()
                type == String::class.java -> arg.toString()
                else -> arg
            }
        }.toTypedArray()
    }

    private fun wrapPrimitive(type: Class<*>): Class<*> {
        return when (type) {
            java.lang.Integer.TYPE -> java.lang.Integer::class.java
            java.lang.Long.TYPE -> java.lang.Long::class.java
            java.lang.Short.TYPE -> java.lang.Short::class.java
            java.lang.Byte.TYPE -> java.lang.Byte::class.java
            java.lang.Boolean.TYPE -> java.lang.Boolean::class.java
            java.lang.Float.TYPE -> java.lang.Float::class.java
            java.lang.Double.TYPE -> java.lang.Double::class.java
            else -> type
        }
    }

    private fun readMemberText(target: Any, vararg names: String): String {
        for (name in names) {
            try {
                val method = target.javaClass.methods.firstOrNull { it.name == name && it.parameterCount == 0 }
                val value = method?.invoke(target)
                if (value != null) return value.toString()
            } catch (_: Exception) {
            }

            try {
                val field = target.javaClass.fields.firstOrNull { it.name == name }
                    ?: target.javaClass.declaredFields.firstOrNull { it.name == name }
                field?.isAccessible = true
                val value = field?.get(target)
                if (value != null) return value.toString()
            } catch (_: Exception) {
            }
        }

        return ""
    }

    private fun extractText(value: Any?): String {
        if (value == null) return ""

        if (value is ByteArray) {
            return value.joinToString("") { each -> "%02X".format(each.toInt() and 0xFF) }
        }

        val direct = value.toString().trim()
        if (direct.isNotBlank() && direct != value.javaClass.name) {
            return direct
        }

        return readMemberText(value, "getData", "getResult", "getTID", "getTid", "data", "result", "tid", "TID")
    }

    private fun normalizeHex(value: String): String {
        return value
            .trim()
            .replace(" ", "")
            .replace(":", "")
            .replace("-", "")
            .uppercase(Locale.ROOT)
    }

    private fun hexToBytes(hex: String): ByteArray {
        val clean = normalizeHex(hex)
        return ByteArray(clean.length / 2) { index ->
            clean.substring(index * 2, index * 2 + 2).toInt(16).toByte()
        }
    }

    private data class SerialConnectResult(
        val connected: Boolean,
        val message: String
    )

    private class MethodCall(
        val name: String,
        vararg val args: Any?
    )

    companion object {
        private const val TAG = "ChafonRfidController"
    }
}
