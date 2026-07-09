package com.adrian.warehouse18mobile

data class RfidTag(
    val epc: String,
    val rssi: Int? = null,
    val tid: String? = null
)

interface RfidController {
    val isConnected: Boolean

    fun setListener(listener: Listener?)
    fun connect()
    fun disconnect()
    fun startInventory()
    fun stopInventory()
    fun readTid(epc: String): String
    fun writeEpc(currentEpc: String, newEpc: String)

    interface Listener {
        fun onTagRead(tag: RfidTag)
        fun onTriggerPressed()
        fun onTriggerReleased()
    }
}
