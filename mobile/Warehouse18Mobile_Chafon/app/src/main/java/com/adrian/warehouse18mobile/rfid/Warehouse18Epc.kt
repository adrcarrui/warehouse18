package com.adrian.warehouse18mobile.rfid

object Warehouse18Epc {

    private const val EXPECTED_HEX_LENGTH = 24
    private const val MAGIC = 0x18

    private val classCodes = mapOf(
        0x00 to "USER",
        0x01 to "GEN",
        0x02 to "A400M",
        0x03 to "A400",
        0x04 to "235",
        0x05 to "295",
        0x06 to "MRTT",
        0x07 to "ITC",
        0x08 to "CHT",
        0x09 to "C295",
        0x0A to "DARPT",
        0x0B to "CN235"
    )

    sealed class DecodeResult {
        abstract val epc: String

        data class Valid(
            override val epc: String,
            val classCode: Int,
            val className: String,
            val objectId: Int,
            val objectCode: String,
            val tidTailHex: String,
            val hasTidTail: Boolean,
            val checksum: Int
        ) : DecodeResult()

        data class InvalidWarehouse18(
            override val epc: String,
            val reason: String
        ) : DecodeResult()

        data class External(
            override val epc: String,
            val reason: String
        ) : DecodeResult()
    }

    fun decode(rawEpc: String): DecodeResult {
        val epc = normalize(rawEpc)

        if (epc.length != EXPECTED_HEX_LENGTH) {
            return DecodeResult.External(
                epc = epc,
                reason = "EPC externo: longitud distinta de 96 bits / 24 hex"
            )
        }

        val bytes = try {
            hexToBytes(epc)
        } catch (e: IllegalArgumentException) {
            return DecodeResult.External(
                epc = epc,
                reason = "EPC externo: no es hexadecimal válido"
            )
        }

        val magic = bytes[0].toInt() and 0xFF

        if (magic != MAGIC) {
            return DecodeResult.External(
                epc = epc,
                reason = "EPC externo: no empieza por magic 18"
            )
        }

        val expectedChecksum = xor8(bytes, untilIndexExclusive = 11)
        val actualChecksum = bytes[11].toInt() and 0xFF

        if (actualChecksum != expectedChecksum) {
            return DecodeResult.InvalidWarehouse18(
                epc = epc,
                reason = "Checksum incorrecto. Esperado ${expectedChecksum.toHex2()}, leído ${actualChecksum.toHex2()}"
            )
        }

        val classCode = bytes[1].toInt() and 0xFF
        val className = classCodes[classCode]

        if (className == null) {
            return DecodeResult.InvalidWarehouse18(
                epc = epc,
                reason = "Class code desconocido: ${classCode.toHex2()}"
            )
        }

        val objectId = readObjectId(bytes)
        val tidTail = bytes.copyOfRange(5, 11)
        val tidTailHex = tidTail.joinToString("") { (it.toInt() and 0xFF).toHex2() }
        val hasTidTail = tidTail.any { (it.toInt() and 0xFF) != 0 }

        val objectCode = buildObjectCode(
            className = className,
            objectId = objectId
        )

        return DecodeResult.Valid(
            epc = epc,
            classCode = classCode,
            className = className,
            objectId = objectId,
            objectCode = objectCode,
            tidTailHex = tidTailHex,
            hasTidTail = hasTidTail,
            checksum = actualChecksum
        )
    }

    private fun normalize(value: String): String {
        return value
            .trim()
            .replace(" ", "")
            .replace("-", "")
            .uppercase()
    }

    private fun hexToBytes(hex: String): ByteArray {
        if (hex.length % 2 != 0) {
            throw IllegalArgumentException("Hex length must be even")
        }

        return ByteArray(hex.length / 2) { index ->
            val start = index * 2
            hex.substring(start, start + 2).toInt(16).toByte()
        }
    }

    private fun xor8(bytes: ByteArray, untilIndexExclusive: Int): Int {
        var checksum = 0

        for (i in 0 until untilIndexExclusive) {
            checksum = checksum xor (bytes[i].toInt() and 0xFF)
        }

        return checksum and 0xFF
    }

    private fun readObjectId(bytes: ByteArray): Int {
        val b2 = bytes[2].toInt() and 0xFF
        val b3 = bytes[3].toInt() and 0xFF
        val b4 = bytes[4].toInt() and 0xFF

        return (b2 shl 16) or (b3 shl 8) or b4
    }

    private fun buildObjectCode(className: String, objectId: Int): String {
        val padded = objectId.toString().padStart(6, '0')

        return when (className) {
            "USER" -> "USER-$padded"
            else -> "$className-$padded"
        }
    }

    private fun Int.toHex2(): String {
        return this
            .and(0xFF)
            .toString(16)
            .uppercase()
            .padStart(2, '0')
    }
}