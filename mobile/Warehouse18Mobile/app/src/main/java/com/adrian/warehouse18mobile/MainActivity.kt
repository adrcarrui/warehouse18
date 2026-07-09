package com.adrian.warehouse18mobile

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.provider.Settings as AndroidSettings
import android.util.Log
import android.media.AudioManager
import android.media.ToneGenerator
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.LinearProgressIndicator
import androidx.activity.OnBackPressedCallback
import androidx.core.content.ContextCompat as AndroidXContextCompat
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.Image
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.annotation.DrawableRes
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Icon
import androidx.compose.ui.res.painterResource
import androidx.compose.foundation.layout.Box
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.graphicsLayer
import com.zebra.rfid.api3.ENUM_TRANSPORT
import com.zebra.rfid.api3.HANDHELD_TRIGGER_EVENT_TYPE
import com.zebra.rfid.api3.RFIDReader
import com.zebra.rfid.api3.Readers
import com.zebra.rfid.api3.RfidEventsListener
import com.zebra.rfid.api3.RfidReadEvents
import com.zebra.rfid.api3.RfidStatusEvents
import com.zebra.rfid.api3.STATUS_EVENT_TYPE
import com.zebra.rfid.api3.TagData
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.Locale
import kotlin.concurrent.thread

import com.zebra.rfid.api3.MEMORY_BANK
import com.zebra.rfid.api3.TagAccess

private const val TAG = "Warehouse18Mobile"

// PC running FastAPI.
private const val DEFAULT_BACKEND_IP = "192.168.1.172"
private const val DEFAULT_BACKEND_PORT = "8000"
private const val DEFAULT_BACKEND_PREFIX = "/warehouse18/api"
private const val DEFAULT_BASE_URL = "http://192.168.1.172:8000/warehouse18/api"

private const val DEFAULT_READER_ID = "zebra-mc3300r-01"
private const val EPC_DEDUPE_MS = 700L

private const val DATAWEDGE_BARCODE_ACTION = "com.adrian.warehouse18mobile.BARCODE"
private const val DATAWEDGE_DATA_STRING = "com.symbol.datawedge.data_string"
private const val DATAWEDGE_LABEL_TYPE = "com.symbol.datawedge.label_type"

enum class AppScreen {
    MAIN_MENU,
    INVENTORY_BY_LOCATION,
    SEARCH_ITEM,
    PROGRAM_TAG,
    SETTINGS
}

data class BackendConfig(
    val ip: String,
    val port: String,
    val prefix: String
) {
    val baseUrl: String
        get() = AppSettingsStore.buildBaseUrl(ip, port, prefix)
}

object AppSettingsStore {
    private const val PREFS_NAME = "warehouse18_mobile_settings"
    private const val KEY_BACKEND_IP = "backend_ip"
    private const val KEY_BACKEND_PORT = "backend_port"
    private const val KEY_BACKEND_PREFIX = "backend_prefix"

    fun load(context: Context): BackendConfig {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        return BackendConfig(
            ip = prefs.getString(KEY_BACKEND_IP, DEFAULT_BACKEND_IP) ?: DEFAULT_BACKEND_IP,
            port = prefs.getString(KEY_BACKEND_PORT, DEFAULT_BACKEND_PORT) ?: DEFAULT_BACKEND_PORT,
            prefix = prefs.getString(KEY_BACKEND_PREFIX, DEFAULT_BACKEND_PREFIX) ?: DEFAULT_BACKEND_PREFIX
        )
    }

    fun save(
        context: Context,
        ip: String,
        port: String,
        prefix: String
    ) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_BACKEND_IP, ip.trim())
            .putString(KEY_BACKEND_PORT, port.trim())
            .putString(KEY_BACKEND_PREFIX, normalizePrefix(prefix))
            .apply()
    }

    fun buildBaseUrl(
        ip: String,
        port: String,
        prefix: String
    ): String {
        val cleanIp = ip.trim().removePrefix("http://").removePrefix("https://").substringBefore("/")
        val cleanPort = port.trim().ifBlank { DEFAULT_BACKEND_PORT }
        val cleanPrefix = normalizePrefix(prefix)

        return "http://$cleanIp:$cleanPort$cleanPrefix"
    }

    private fun normalizePrefix(prefix: String): String {
        val clean = prefix.trim().ifBlank { DEFAULT_BACKEND_PREFIX }
        return "/" + clean.trim('/').trimEnd('/')
    }
}

enum class InventoryStatus(val label: String) {
    PENDING("Pending"),
    PARTIAL("Partial"),
    OK("Ok"),
    EXTRA("Extra")
}

data class InventoryTableRow(
    val itemCode: String,
    val qty: Int = 1,
    val reads: Int = 0,
    val status: InventoryStatus = InventoryStatus.PENDING,
    val readEpcs: Set<String> = emptySet()
)

data class ScanValidationResult(
    val isValidTagFormat: Boolean,
    val itemCode: String?
)


enum class ProgramRfidMode {
    IDLE,
    DETECTING,
    VERIFYING
}

enum class SearchRfidMode {
    IDLE,
    DISCOVERING,
    LOCATING
}

data class ProgramTagTarget(
    val displayLabel: String,
    val barcode: String,
    val currentEpc: String,
    val tidHex: String,
    val tidTailHex: String,
    val classCodeHex: String,
    val objectId: Long,
    val epc: String
)

data class ProgramDetectedTagInfo(
    val epc: String,
    val rssi: Int?,
    val reads: Int,
    val lastSeenAt: Long
)

data class SearchRegisteredLocationInfo(
    val locationName: String,
    val lastMovementAt: String
)

sealed class SearchRegisteredLocationState {
    object Idle : SearchRegisteredLocationState()
    object Loading : SearchRegisteredLocationState()
    data class Found(val info: SearchRegisteredLocationInfo) : SearchRegisteredLocationState()
    data class NotFound(val barcode: String) : SearchRegisteredLocationState()
    data class Error(val message: String) : SearchRegisteredLocationState()
}

data class SearchCandidateTagInfo(
    val epc: String,
    val rssi: Int?,
    val reads: Int,
    val lastSeenAt: Long
)

class MainActivity : ComponentActivity(), RfidEventsListener {

    private var serverBaseUrl by mutableStateOf(DEFAULT_BASE_URL)

    private var settingsBackendIp by mutableStateOf(DEFAULT_BACKEND_IP)
    private var settingsBackendPort by mutableStateOf(DEFAULT_BACKEND_PORT)
    private var settingsBackendPrefix by mutableStateOf(DEFAULT_BACKEND_PREFIX)
    private var settingsMessage by mutableStateOf("")

    private var currentScreen by mutableStateOf(AppScreen.MAIN_MENU)

    private var locationNameText by mutableStateOf("")
    private var selectedLocationId by mutableStateOf<Long?>(null)
    private var selectedLocationLabel by mutableStateOf("")

    private var message by mutableStateOf("Scan location barcode first.")
    private var isReaderConnected by mutableStateOf(false)
    private var isInventoryRunning by mutableStateOf(false)
    private var isLoadingExpected by mutableStateOf(false)
    private var isValidating by mutableStateOf(false)
    private var isSubmittingInventory by mutableStateOf(false)

    private val loadedRows = mutableStateMapOf<String, InventoryTableRow>()

    private var searchItemText by mutableStateOf("")
    private var searchItemMessage by mutableStateOf("Enter or scan an item/asset code or full EPC.")
    private var isSearchingItem by mutableStateOf(false)

    private var locateTargetEpc by mutableStateOf("")
    private var locateDistance by mutableStateOf<Int?>(null)
    private var locateRssi by mutableStateOf<Int?>(null)
    private var isLocatingTag by mutableStateOf(false)
    private var searchResolvedEpc by mutableStateOf("")
    private var searchExpectedPrefix by mutableStateOf("")
    private var searchCandidateOptions by mutableStateOf<List<SearchCandidateTagInfo>>(emptyList())
    private var searchRegisteredLocationState by mutableStateOf<SearchRegisteredLocationState>(SearchRegisteredLocationState.Idle)

    private var searchRfidMode = SearchRfidMode.IDLE
    private var searchDiscoverSessionToken = 0
    private val searchCandidateEpcs = mutableSetOf<String>()
    private val searchCandidateTagInfos = mutableMapOf<String, SearchCandidateTagInfo>()

    private val locateProximitySamples = mutableListOf<Int>()
    private var smoothedLocateProximity: Float? = null

    private var programItemText by mutableStateOf("")
    private var programEpcText by mutableStateOf("")
    private var programTagMessage by mutableStateOf("Scan or enter a barcode, then read one RFID tag.")
    private var programSelectedTarget by mutableStateOf<ProgramTagTarget?>(null)
    private var programDetectedTagEpc by mutableStateOf("")
    private var programTidTailText by mutableStateOf("")
    private var programCandidateOptions by mutableStateOf<List<ProgramDetectedTagInfo>>(emptyList())
    private var isDetectingProgramTag by mutableStateOf(false)
    private var isProgrammingTag by mutableStateOf(false)
    private var isProgramTriggerReading by mutableStateOf(false)

    private var programRfidMode = ProgramRfidMode.IDLE
    private var programReadSessionToken = 0
    private val programDetectedEpcs = mutableMapOf<String, ProgramDetectedTagInfo>()

    private var readers: Readers? = null
    private var rfidReader: RFIDReader? = null

    private var toneGenerator: ToneGenerator? = null

    @Volatile
    private var locateBeepLoopRunning = false

    @Volatile
    private var latestLocateProximity: Int = 0

    private var locateBeepThread: Thread? = null

    private val recentEpcs = mutableMapOf<String, Long>()
    private val epcValidationCache = mutableMapOf<String, ScanValidationResult>()
    private val pendingEpcValidations = mutableSetOf<String>()

    private val barcodeReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            Log.d(TAG, "Barcode receiver called. Action=${intent?.action}")

            if (intent?.action != DATAWEDGE_BARCODE_ACTION) {
                Log.d(TAG, "Ignored intent action: ${intent?.action}")
                return
            }

            val barcode = intent.getStringExtra(DATAWEDGE_DATA_STRING)
                ?.trim()
                .orEmpty()

            val labelType = intent.getStringExtra(DATAWEDGE_LABEL_TYPE)
                ?.trim()
                .orEmpty()

            Log.d(TAG, "Barcode received. barcode='$barcode', labelType='$labelType'")

            if (barcode.isBlank()) {
                runOnUiThread {
                    when (currentScreen) {
                        AppScreen.INVENTORY_BY_LOCATION -> {
                            message = "Barcode intent received, but barcode was empty."
                        }

                        AppScreen.SEARCH_ITEM -> {
                            searchItemMessage = "Barcode intent received, but barcode was empty."
                        }

                        AppScreen.PROGRAM_TAG -> {
                            programTagMessage = "Barcode intent received, but barcode was empty."
                        }

                        AppScreen.MAIN_MENU,
                        AppScreen.SETTINGS -> {
                            // Keep quiet on screens where a barcode is not expected.
                        }
                    }
                }
                return
            }

            runOnUiThread {
                handleBarcodeByCurrentScreen(
                    barcode = barcode,
                    labelType = labelType
                )
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        loadSettingsFromStore()

        registerBarcodeReceiver()
        setupBackHandler()
        initToneGenerator()
        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = Color(0xFFF5F7FA)
                ) {
                    when (currentScreen) {
                        AppScreen.MAIN_MENU -> {
                            MainMenuScreen(
                                onInventoryByLocation = {
                                    currentScreen = AppScreen.INVENTORY_BY_LOCATION
                                },
                                onSearchItem = {
                                    currentScreen = AppScreen.SEARCH_ITEM
                                },
                                onProgramTag = {
                                    currentScreen = AppScreen.PROGRAM_TAG
                                },
                                onSettings = {
                                    settingsMessage = ""
                                    currentScreen = AppScreen.SETTINGS
                                }
                            )
                        }

                        AppScreen.INVENTORY_BY_LOCATION -> {
                            Warehouse18Screen(
                                locationNameText = locationNameText,
                                onLocationNameChange = {
                                    locationNameText = it
                                    selectedLocationId = null
                                    selectedLocationLabel = ""
                                    loadedRows.clear()
                                    clearRuntimeCaches()

                                    if (isReaderConnected || isInventoryRunning) {
                                        disconnectReaderAsync()
                                    }

                                    message = "Location changed. Press ↻ to load."
                                },
                                selectedLocationLabel = selectedLocationLabel,
                                message = message,
                                isLoadingExpected = isLoadingExpected,
                                isInventoryRunning = isInventoryRunning,
                                isReaderConnected = isReaderConnected,
                                isSubmittingInventory = isSubmittingInventory,
                                rows = getVisibleRows(),
                                onLoadExpected = { loadExpectedItemsForLocation() },
                                onClearReads = { clearTable() },
                                onSubmitInventory = { submitInventoryResult() }
                            )
                        }

                        AppScreen.SEARCH_ITEM -> {
                            SearchItemScreen(
                                itemText = searchItemText,
                                onItemTextChange = {
                                    searchItemText = it
                                    searchItemMessage = "Enter or scan an item/asset code or full EPC."
                                    locateDistance = null
                                    locateRssi = null
                                    locateTargetEpc = ""
                                    searchResolvedEpc = ""
                                    searchExpectedPrefix = ""
                                    searchCandidateOptions = emptyList()
                                    searchRegisteredLocationState = SearchRegisteredLocationState.Idle
                                    clearSearchCandidates()
                                },
                                message = searchItemMessage,
                                isSearching = isSearchingItem,
                                isLocating = isLocatingTag,
                                locateDistance = locateDistance,
                                locateRssi = locateRssi,
                                resolvedEpc = searchResolvedEpc.ifBlank { locateTargetEpc },
                                candidateEpcs = searchCandidateOptions,
                                registeredLocationState = searchRegisteredLocationState,
                                onSearch = { searchItem() },
                                onLocate = { startLocateSelectedTag() },
                                onSelectCandidate = { selectedEpc -> selectSearchCandidate(selectedEpc) },
                                onStopLocate = { stopSearchOrLocateTag() },
                                onClear = { clearSearchItemFlow() },
                                onBack = {
                                    stopLocateTag()
                                    searchRfidMode = SearchRfidMode.IDLE
                                    currentScreen = AppScreen.MAIN_MENU
                                }
                            )
                        }

                        AppScreen.PROGRAM_TAG -> {
                            ProgramTagScreen(
                                itemText = programItemText,
                                selectedTarget = programSelectedTarget,
                                detectedTagEpc = programDetectedTagEpc,
                                tidTail = programTidTailText,
                                generatedEpc = programEpcText,
                                candidateTags = programCandidateOptions,
                                message = programTagMessage,
                                isDetectingTag = isDetectingProgramTag,
                                isProgrammingTag = isProgrammingTag,
                                onItemTextChange = {
                                    val cleanBarcode = it.trim()

                                    programItemText = it
                                    programSelectedTarget = null
                                    programDetectedTagEpc = ""
                                    programTidTailText = ""
                                    programEpcText = ""
                                    programCandidateOptions = emptyList()
                                    clearProgramDetectedTags()

                                    programTagMessage = if (cleanBarcode.isBlank()) {
                                        "Scan or enter a barcode before reading RFID."
                                    } else {
                                        "Barcode loaded. Hold the trigger to read RFID tags; release it to stop."
                                    }
                                },
                                onDetectTag = { detectSingleProgramTag() },
                                onSelectCandidate = { epc -> selectProgramCandidateForProgramming(epc) },
                                onProgramTag = { programDetectedTag() },
                                onClear = { clearProgramTagFlow() },
                                onBack = {
                                    stopProgramRfidOperations()
                                    currentScreen = AppScreen.MAIN_MENU
                                }
                            )
                        }

                        AppScreen.SETTINGS -> {
                            SettingsScreen(
                                backendIp = settingsBackendIp,
                                backendPort = settingsBackendPort,
                                backendPrefix = settingsBackendPrefix,
                                currentBaseUrl = serverBaseUrl,
                                message = settingsMessage,
                                onBackendIpChange = {
                                    settingsBackendIp = it
                                    settingsMessage = ""
                                },
                                onBackendPortChange = {
                                    settingsBackendPort = it
                                    settingsMessage = ""
                                },
                                onBackendPrefixChange = {
                                    settingsBackendPrefix = it
                                    settingsMessage = ""
                                },
                                onOpenWifiSettings = { openWifiSettingsFromApp() },
                                onTestConnection = { testBackendConnectionFromSettings() },
                                onSave = { saveSettingsFromScreen() },
                                onBack = {
                                    loadSettingsFromStore()
                                    currentScreen = AppScreen.MAIN_MENU
                                }
                            )
                        }
                    }
                }
            }
        }

        /*
         * Important:
         * Do NOT connect RFID here.
         *
         * First step is barcode/location.
         * RFID is connected only after expected inventory has been loaded.
         */
    }

    private fun loadSettingsFromStore() {
        val config = AppSettingsStore.load(this)

        settingsBackendIp = config.ip
        settingsBackendPort = config.port
        settingsBackendPrefix = config.prefix
        serverBaseUrl = config.baseUrl
    }

    private fun saveSettingsFromScreen() {
        val cleanIp = settingsBackendIp.trim()
        val cleanPort = settingsBackendPort.trim()
        val cleanPrefix = settingsBackendPrefix.trim()

        if (cleanIp.isBlank()) {
            settingsMessage = "Backend IP cannot be empty."
            return
        }

        if (cleanPort.toIntOrNull() == null) {
            settingsMessage = "Backend port must be a number."
            return
        }

        val newBaseUrl = AppSettingsStore.buildBaseUrl(
            ip = cleanIp,
            port = cleanPort,
            prefix = cleanPrefix
        )

        AppSettingsStore.save(
            context = this,
            ip = cleanIp,
            port = cleanPort,
            prefix = cleanPrefix
        )

        serverBaseUrl = newBaseUrl
        settingsMessage = "Backend saved and active: $serverBaseUrl"
    }

    private fun openWifiSettingsFromApp() {
        try {
            startActivity(Intent(AndroidSettings.ACTION_WIFI_SETTINGS))
            settingsMessage = "Opening Wi-Fi settings..."
        } catch (ex: Exception) {
            settingsMessage = "Could not open Wi-Fi settings: ${ex.message}"
        }
    }

    private fun testBackendConnectionFromSettings() {
        val testBaseUrl = AppSettingsStore.buildBaseUrl(
            ip = settingsBackendIp,
            port = settingsBackendPort,
            prefix = settingsBackendPrefix
        )

        settingsMessage = "Testing backend: $testBaseUrl"

        thread {
            val resultMessage = try {
                httpGet("$testBaseUrl/locations?page=1&page_size=1")
                runOnUiThread {
                    serverBaseUrl = testBaseUrl
                }
                "Connection OK. Backend active for this session: $testBaseUrl"
            } catch (ex: Exception) {
                "Connection failed: ${ex.message}"
            }

            runOnUiThread {
                settingsMessage = resultMessage
            }
        }
    }

    private fun setupBackHandler() {
        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    when (currentScreen) {
                        AppScreen.MAIN_MENU -> {
                            isEnabled = false
                            onBackPressedDispatcher.onBackPressed()
                        }

                        AppScreen.INVENTORY_BY_LOCATION -> {
                            if (isInventoryRunning) {
                                message = "Stop RFID reading before going back to menu."
                            } else {
                                currentScreen = AppScreen.MAIN_MENU
                            }
                        }

                        AppScreen.SEARCH_ITEM -> {
                            stopLocateTag()
                            currentScreen = AppScreen.MAIN_MENU
                        }

                        AppScreen.PROGRAM_TAG -> {
                            stopProgramRfidOperations()
                            currentScreen = AppScreen.MAIN_MENU
                        }

                        AppScreen.SETTINGS -> {
                            loadSettingsFromStore()
                            currentScreen = AppScreen.MAIN_MENU
                        }
                    }
                }
            }
        )
    }

    private fun handleBarcodeByCurrentScreen(
        barcode: String,
        labelType: String
    ) {
        when (currentScreen) {
            AppScreen.MAIN_MENU,
            AppScreen.SETTINGS -> {
                // Do nothing. User must choose a feature first.
            }

            AppScreen.INVENTORY_BY_LOCATION -> {
                handleLocationBarcode(
                    barcode = barcode,
                    labelType = labelType
                )
            }

            AppScreen.SEARCH_ITEM -> {
                val cleanBarcode = barcode.trim()
                searchItemText = cleanBarcode
                searchItemMessage = "Barcode loaded. Starting RFID search automatically..."

                android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                    if (currentScreen == AppScreen.SEARCH_ITEM &&
                        searchItemText.trim().equals(cleanBarcode, ignoreCase = true) &&
                        !isSearchingItem &&
                        !isLocatingTag
                    ) {
                        searchItem()
                    }
                }, 300L)
            }

            AppScreen.PROGRAM_TAG -> {
                val cleanBarcode = barcode.trim()
                val alreadyLoadedBarcode = programItemText.trim()

                if (alreadyLoadedBarcode.isNotBlank()) {
                    if (isProgramTriggerReading || isDetectingProgramTag) {
                        Log.d(TAG, "Program tag barcode intent ignored while RFID reading is active.")
                        return
                    }

                    programTagMessage = if (alreadyLoadedBarcode.equals(cleanBarcode, ignoreCase = true)) {
                        "Barcode already loaded. Hold the trigger to read RFID tags; release it to stop."
                    } else {
                        "Barcode already loaded: $alreadyLoadedBarcode. Press ✕ to load another barcode."
                    }
                    return
                }

                prepareProgramTagAfterBarcodeLoaded(
                    barcode = barcode,
                    labelType = labelType
                )
            }
        }
    }

    private fun prepareProgramTagAfterBarcodeLoaded(
        barcode: String,
        labelType: String
    ) {
        val cleanBarcode = barcode.trim()

        if (cleanBarcode.isBlank()) {
            programTagMessage = "Barcode intent received, but barcode was empty."
            return
        }

        if (isProgrammingTag) {
            programTagMessage = "Wait until tag programming finishes before scanning another barcode."
            return
        }

        stopProgramRfidOperations()

        programItemText = cleanBarcode
        programSelectedTarget = null
        programDetectedTagEpc = ""
        programTidTailText = ""
        programEpcText = ""
        programCandidateOptions = emptyList()
        clearProgramDetectedTags()

        val barcodeText = if (labelType.isBlank()) {
            "Barcode scanned: $cleanBarcode."
        } else {
            "Barcode scanned: $cleanBarcode ($labelType)."
        }

        programTagMessage = "$barcodeText Preparing RFID trigger..."

        connectReaderForProgramIfNeeded {
            if (currentScreen != AppScreen.PROGRAM_TAG) {
                return@connectReaderForProgramIfNeeded
            }

            if (!programItemText.trim().equals(cleanBarcode, ignoreCase = true)) {
                return@connectReaderForProgramIfNeeded
            }

            programTagMessage = "$barcodeText Hold the trigger to read RFID tags; release it to stop."
        }
    }

    private fun getVisibleRows(): List<InventoryTableRow> {
        return loadedRows.values.sortedWith(
            compareBy<InventoryTableRow> { it.status == InventoryStatus.OK }
                .thenBy { it.status == InventoryStatus.EXTRA }
                .thenBy { it.itemCode }
        )
    }

    private fun statusForInventoryRow(qty: Int, reads: Int): InventoryStatus {
        return when {
            reads <= 0 -> InventoryStatus.PENDING
            reads < qty -> InventoryStatus.PARTIAL
            reads == qty -> InventoryStatus.OK
            else -> InventoryStatus.EXTRA
        }
    }

    private fun loadExpectedItemsForLocation() {
        val locationText = locationNameText.trim()

        if (locationText.isBlank()) {
            message = "Enter or scan a location name."
            return
        }

        if (isInventoryRunning) {
            message = "Stop RFID reading before loading another location."
            return
        }

        isLoadingExpected = true
        message = "Searching location '$locationText'..."

        thread {
            val t0 = System.currentTimeMillis()

            try {
                if (isReaderConnected) {
                    val tDisconnect0 = System.currentTimeMillis()
                    disconnectReaderSync(updateUi = false)
                    Log.d(TAG, "TIME disconnectReaderSync=${System.currentTimeMillis() - tDisconnect0} ms")
                }

                val tResolve0 = System.currentTimeMillis()
                val resolved = resolveLocationIdByNameOrCode(locationText)
                Log.d(TAG, "TIME resolveLocation=${System.currentTimeMillis() - tResolve0} ms")

                val locationId = resolved.first
                val locationLabel = resolved.second

                val tInventory0 = System.currentTimeMillis()
                val url = buildUrl("/locations/$locationId/handheld-inventory")
                val response = httpGet(url)
                Log.d(TAG, "TIME handheldInventory GET=${System.currentTimeMillis() - tInventory0} ms")

                val tParse0 = System.currentTimeMillis()
                val json = JSONObject(response)
                val loadedCodes = extractExpectedItemCodes(json)
                Log.d(TAG, "TIME parseExpectedItems=${System.currentTimeMillis() - tParse0} ms")

                runOnUiThread {
                    selectedLocationId = locationId
                    selectedLocationLabel = locationLabel

                    loadedRows.clear()
                    clearRuntimeCaches()

                    val groupedCodes = loadedCodes
                        .map { normalizeItemCode(it) }
                        .filter { it.isNotBlank() }
                        .groupingBy { it }
                        .eachCount()
                        .toSortedMap()

                    groupedCodes.forEach { (itemCode, qty) ->
                        loadedRows[itemCode] = InventoryTableRow(
                            itemCode = itemCode,
                            qty = qty,
                            reads = 0,
                            status = InventoryStatus.PENDING,
                            readEpcs = emptySet()
                        )
                    }

                    isLoadingExpected = false

                    message = if (loadedRows.isEmpty()) {
                        "Location loaded: $locationLabel, but no items were found."
                    } else {
                        "Location loaded: $locationLabel. ${loadedRows.size} item(s) loaded. Connecting RFID..."
                    }

                    Log.d(TAG, "TIME total before connectReader=${System.currentTimeMillis() - t0} ms")

                    if (loadedRows.isNotEmpty()) {
                        val tConnect0 = System.currentTimeMillis()
                        connectReader()
                        Log.d(TAG, "TIME connectReader called after ${System.currentTimeMillis() - tConnect0} ms")
                    }
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error loading expected items", ex)

                runOnUiThread {
                    message = "Error loading location: ${ex.message}"
                    isLoadingExpected = false
                }
            }
        }
    }

    private fun resolveLocationIdByNameOrCode(locationText: String): Pair<Long, String> {
        val query = URLEncoder.encode(locationText.trim(), "UTF-8")

        val candidateUrls = listOf(
            buildUrl("/locations/?q=$query&page=1&page_size=20"),
            buildUrl("/locations?q=$query&page=1&page_size=20")
        )

        var lastError: Exception? = null

        for (url in candidateUrls) {
            try {
                val response = httpGet(url)
                val json = JSONObject(response)
                val locations = extractLocationArray(json)

                if (locations.length() == 0) {
                    continue
                }

                val normalizedInput = locationText.trim().uppercase(Locale.ROOT)
                var selected: JSONObject? = null

                for (i in 0 until locations.length()) {
                    val loc = locations.optJSONObject(i) ?: continue

                    val idText = loc.optLong("id").toString()
                    val code = loc.optString("code").trim().uppercase(Locale.ROOT)
                    val name = loc.optString("name").trim().uppercase(Locale.ROOT)

                    if (
                        idText == normalizedInput ||
                        code == normalizedInput ||
                        name == normalizedInput
                    ) {
                        selected = loc
                        break
                    }
                }

                if (selected == null && locations.length() == 1) {
                    selected = locations.optJSONObject(0)
                }

                if (selected == null) {
                    val matches = mutableListOf<String>()

                    for (i in 0 until locations.length()) {
                        val loc = locations.optJSONObject(i) ?: continue

                        matches.add(
                            "${loc.optLong("id")} | ${loc.optString("code")} | ${loc.optString("name")}"
                        )
                    }

                    throw RuntimeException(
                        "Multiple similar locations were found. Enter a more specific location: ${
                            matches.joinToString(", ")
                        }"
                    )
                }

                val id = selected.optLong("id")
                val code = selected.optString("code")
                val name = selected.optString("name")

                if (id <= 0) {
                    throw RuntimeException("The selected location does not have a valid ID.")
                }

                val label = when {
                    code.isNotBlank() && name.isNotBlank() -> "$code - $name"
                    name.isNotBlank() -> name
                    code.isNotBlank() -> code
                    else -> "Location $id"
                }

                return id to label
            } catch (ex: Exception) {
                lastError = ex
            }
        }

        throw RuntimeException(
            lastError?.message ?: "No location was found for '$locationText'"
        )
    }

    private fun extractLocationArray(json: JSONObject): JSONArray {
        json.optJSONArray("items")?.let { return it }
        json.optJSONArray("data")?.let { return it }
        json.optJSONArray("results")?.let { return it }
        json.optJSONArray("locations")?.let { return it }

        val dataObject = json.optJSONObject("data")
        if (dataObject != null) {
            dataObject.optJSONArray("items")?.let { return it }
            dataObject.optJSONArray("data")?.let { return it }
            dataObject.optJSONArray("results")?.let { return it }
            dataObject.optJSONArray("locations")?.let { return it }
        }

        return JSONArray()
    }

    private fun registerBarcodeReceiver() {
        val filter = IntentFilter().apply {
            addAction(DATAWEDGE_BARCODE_ACTION)
            addCategory(Intent.CATEGORY_DEFAULT)
        }

        AndroidXContextCompat.registerReceiver(
            this,
            barcodeReceiver,
            filter,
            AndroidXContextCompat.RECEIVER_EXPORTED
        )

        Log.d(TAG, "Barcode receiver registered with action=$DATAWEDGE_BARCODE_ACTION")
    }

    private fun handleLocationBarcode(
        barcode: String,
        labelType: String
    ) {
        val cleanBarcode = barcode.trim()

        if (cleanBarcode.isBlank()) {
            return
        }

        if (isInventoryRunning) {
            message = "Stop RFID reading before changing location with barcode."
            return
        }

        if (isSubmittingInventory) {
            message = "Wait until inventory submit finishes."
            return
        }

        locationNameText = cleanBarcode
        selectedLocationId = null
        selectedLocationLabel = ""

        loadedRows.clear()
        clearRuntimeCaches()

        message = if (labelType.isBlank()) {
            "Barcode scanned: $cleanBarcode. Loading location..."
        } else {
            "Barcode scanned: $cleanBarcode ($labelType). Loading location..."
        }

        loadExpectedItemsForLocation()
    }

    private fun connectReader() {
        if (isReaderConnected) {
            message = "RFID reader already connected. Press trigger to read tags."
            return
        }

        if (selectedLocationId == null || loadedRows.isEmpty()) {
            message = "Load a location before connecting RFID."
            return
        }

        message = "Connecting RFID reader..."

        thread {
            try {
                readers = Readers(this@MainActivity, ENUM_TRANSPORT.SERVICE_SERIAL)
                val availableReaders = readers?.GetAvailableRFIDReaderList()

                if (availableReaders.isNullOrEmpty()) {
                    runOnUiThread {
                        message = "No RFID reader was found on the Zebra device."
                        isReaderConnected = false
                    }
                    return@thread
                }

                rfidReader = availableReaders[0].rfidReader

                if (rfidReader?.isConnected != true) {
                    rfidReader?.connect()
                }

                rfidReader?.Events?.addEventsListener(this@MainActivity)
                rfidReader?.Events?.setTagReadEvent(true)
                rfidReader?.Events?.setAttachTagDataWithReadEvent(false)
                rfidReader?.Events?.setHandheldEvent(true)

                runOnUiThread {
                    isReaderConnected = true
                    message = "RFID ready. Press trigger to read tags."
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error connecting RFID reader", ex)

                runOnUiThread {
                    isReaderConnected = false
                    message = "Error connecting RFID reader: ${ex.message}"
                }
            }
        }
    }

    private fun disconnectReaderAsync() {
        thread {
            disconnectReaderSync(updateUi = true)
        }
    }

    private fun disconnectReaderSync(updateUi: Boolean = true) {
        try {
            stopInventoryInternal()

            try {
                rfidReader?.Events?.removeEventsListener(this@MainActivity)
            } catch (_: Exception) {
            }

            if (rfidReader?.isConnected == true) {
                rfidReader?.disconnect()
            }

            readers?.Dispose()
            readers = null
            rfidReader = null

            if (updateUi) {
                runOnUiThread {
                    isReaderConnected = false
                    isInventoryRunning = false
                    message = "RFID disconnected. Scan location barcode first."
                }
            } else {
                isReaderConnected = false
                isInventoryRunning = false
            }
        } catch (ex: Exception) {
            Log.e(TAG, "Error disconnecting reader", ex)

            if (updateUi) {
                runOnUiThread {
                    message = "Error disconnecting RFID reader: ${ex.message}"
                }
            }
        }
    }

    private fun startInventoryFromTrigger() {
        val reader = rfidReader

        if (reader == null || !isReaderConnected) {
            runOnUiThread {
                message = "RFID reader is not connected."
            }
            return
        }

        if (selectedLocationId == null) {
            runOnUiThread {
                message = "Load a valid location first."
            }
            return
        }

        if (loadedRows.isEmpty()) {
            runOnUiThread {
                message = "The location is loaded, but there are no loaded items."
            }
            return
        }

        if (isInventoryRunning) {
            return
        }

        if (isSubmittingInventory) {
            runOnUiThread {
                message = "Wait until inventory submit finishes."
            }
            return
        }

        thread {
            try {
                useBufferedReadEvents()
                reader.Actions.Inventory.perform()

                runOnUiThread {
                    isInventoryRunning = true
                    message = "Reading RFID..."
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error starting RFID inventory from trigger", ex)

                runOnUiThread {
                    isInventoryRunning = false
                    message = "Error starting RFID inventory: ${ex.message}"
                }
            }
        }
    }

    private fun stopInventoryFromTrigger() {
        if (!isInventoryRunning) {
            return
        }

        thread {
            try {
                stopInventoryInternal()

                runOnUiThread {
                    isInventoryRunning = false
                    message = "Reading stopped. Press trigger to read again."
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error stopping RFID inventory from trigger", ex)

                runOnUiThread {
                    message = "Error stopping RFID inventory: ${ex.message}"
                }
            }
        }
    }

    private fun stopInventoryInternal() {
        try {
            rfidReader?.Actions?.Inventory?.stop()
        } catch (_: Exception) {
        }
    }

    private fun submitInventoryResult() {
        val locationId = selectedLocationId

        if (locationId == null) {
            message = "Load a valid location before submitting inventory."
            return
        }

        if (isInventoryRunning) {
            message = "Stop RFID reading before submitting inventory."
            return
        }

        if (isLoadingExpected) {
            message = "Wait until location finishes loading."
            return
        }

        if (isSubmittingInventory) {
            return
        }

        if (loadedRows.isEmpty()) {
            message = "There are no inventory rows to submit."
            return
        }

        isSubmittingInventory = true
        message = "Submitting inventory result..."

        val rowsArray = JSONArray()

        getVisibleRows().forEach { row ->
            rowsArray.put(
                JSONObject()
                    .put("item_code", row.itemCode)
                    .put("reads", row.reads)
                    .put("status", row.status.name)
            )
        }

        val totalItems = loadedRows.values.sumOf { it.qty }
        val okItems = loadedRows.values.sumOf { row -> row.reads.coerceAtMost(row.qty) }
        val pendingItems = (totalItems - okItems).coerceAtLeast(0)

        val body = JSONObject()
            .put("location_id", locationId)
            .put("location_label", selectedLocationLabel)
            .put("reader_id", DEFAULT_READER_ID)
            .put("total_items", totalItems)
            .put("ok_items", okItems)
            .put("pending_items", pendingItems)
            .put("rows", rowsArray)
            .toString()

        thread {
            try {
                val url = buildUrl("/locations/$locationId/handheld-inventory/submit")
                val response = httpPostJson(url, body)

                Log.d(TAG, "Inventory submit response: $response")

                runOnUiThread {
                    isSubmittingInventory = false
                    message = "Inventory result submitted successfully."
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error submitting inventory result", ex)

                runOnUiThread {
                    isSubmittingInventory = false
                    message = "Error submitting inventory result: ${ex.message}"
                }
            }
        }
    }

    private fun clearTable() {
        if (isInventoryRunning) {
            message = "Stop RFID reading before clearing the table."
            return
        }

        if (isSubmittingInventory) {
            message = "Wait until inventory submit finishes."
            return
        }

        loadedRows.clear()
        selectedLocationId = null
        selectedLocationLabel = ""
        locationNameText = ""

        clearRuntimeCaches()

        if (isReaderConnected) {
            disconnectReaderAsync()
        } else {
            message = "Table cleared. Scan location barcode first."
        }
    }

    private fun clearRuntimeCaches() {
        synchronized(recentEpcs) {
            recentEpcs.clear()
        }

        synchronized(epcValidationCache) {
            epcValidationCache.clear()
        }

        synchronized(pendingEpcValidations) {
            pendingEpcValidations.clear()
        }
    }

    override fun eventReadNotify(rfidReadEvents: RfidReadEvents?) {
        try {
            val tags = readTagsFromEventOrBuffer(rfidReadEvents)

            if (tags.isEmpty()) {
                if (isLocatingTag) {
                    Log.d(TAG, "Locate read event received, but no TagData was available.")
                }
                return
            }

            for (tag in tags) {
                handleRfidTagData(tag)
            }
        } catch (ex: Exception) {
            Log.e(TAG, "Error reading RFID tags", ex)
        }
    }

    private fun readTagsFromEventOrBuffer(rfidReadEvents: RfidReadEvents?): List<TagData> {
        val result = mutableListOf<TagData>()

        /*
         * Zebra has two read-event modes:
         * - setAttachTagDataWithReadEvent(false): use reader.Actions.getReadTags(...)
         * - setAttachTagDataWithReadEvent(true): TagData can come inside RfidReadEvents
         *
         * Search-by-prefix works better with buffered reads.
         * Locate can require attached reads in some SDK/device combinations.
         * So we support both. Yes, two paths for the same tag event, because apparently one
         * straight road was too dignified.
         */
        if (rfidReadEvents != null) {
            val attachedTags = extractAttachedTagData(rfidReadEvents)

            if (attachedTags.isNotEmpty()) {
                Log.d(TAG, "Attached RFID tag data count=${attachedTags.size}")
                result.addAll(attachedTags)
            }
        }

        try {
            val bufferedTags = rfidReader?.Actions?.getReadTags(100)

            if (bufferedTags != null && bufferedTags.isNotEmpty()) {
                Log.d(TAG, "Buffered RFID tag data count=${bufferedTags.size}")
                result.addAll(bufferedTags)
            }
        } catch (ex: Exception) {
            Log.d(TAG, "Buffered RFID tag data was not available: ${ex.message}")
        }

        return result
            .filter { !it.tagID.isNullOrBlank() }
            .groupBy { it.tagID.trim().uppercase(Locale.ROOT) }
            .values
            .map { sameEpcTags ->
                sameEpcTags.firstOrNull { it.isContainsLocationInfo } ?: sameEpcTags.first()
            }
    }

    private fun extractAttachedTagData(rfidReadEvents: RfidReadEvents): List<TagData> {
        val result = mutableListOf<TagData>()

        fun addTagData(value: Any?) {
            when (value) {
                null -> return
                is TagData -> result.add(value)
                is Array<*> -> value.forEach { addTagData(it) }
                is Iterable<*> -> value.forEach { addTagData(it) }
            }
        }

        fun inspectObject(source: Any?) {
            if (source == null) return

            addTagData(source)

            try {
                source.javaClass.fields
                    .filter {
                        it.name.equals("ReadEventData", ignoreCase = true) ||
                                it.name.equals("TagData", ignoreCase = true) ||
                                it.name.equals("tagData", ignoreCase = true)
                    }
                    .forEach { field ->
                        try {
                            val value = field.get(source)
                            addTagData(value)

                            if (field.name.equals("ReadEventData", ignoreCase = true)) {
                                inspectObject(value)
                            }
                        } catch (ex: Exception) {
                            Log.d(TAG, "RFID attached field read failed: ${field.name}: ${ex.message}")
                        }
                    }
            } catch (ex: Exception) {
                Log.d(TAG, "RFID attached field inspection failed: ${ex.message}")
            }

            try {
                source.javaClass.methods
                    .filter {
                        it.parameterCount == 0 &&
                                (
                                        it.name.equals("getReadEventData", ignoreCase = true) ||
                                                it.name.equals("GetReadEventData", ignoreCase = true) ||
                                                it.name.equals("getTagData", ignoreCase = true) ||
                                                it.name.equals("GetTagData", ignoreCase = true)
                                        )
                    }
                    .forEach { method ->
                        try {
                            val value = method.invoke(source)
                            addTagData(value)

                            if (method.name.equals("getReadEventData", ignoreCase = true) ||
                                method.name.equals("GetReadEventData", ignoreCase = true)
                            ) {
                                inspectObject(value)
                            }
                        } catch (ex: Exception) {
                            Log.d(TAG, "RFID attached method read failed: ${method.name}: ${ex.message}")
                        }
                    }
            } catch (ex: Exception) {
                Log.d(TAG, "RFID attached method inspection failed: ${ex.message}")
            }
        }

        inspectObject(rfidReadEvents)

        return result.distinctBy { it.tagID?.trim()?.uppercase(Locale.ROOT).orEmpty() }
    }

    private fun handleRfidTagData(tag: TagData) {
        val epc = tag.tagID?.trim()?.uppercase(Locale.ROOT)

        if (epc.isNullOrBlank()) {
            return
        }

        if (isLocatingTag) {
            try {
                val target = locateTargetEpc.trim().uppercase(Locale.ROOT)
                val isTarget = target.isBlank() || epc == target

                Log.d(
                    TAG,
                    "LOCATE EVENT. epc=$epc target=$target isTarget=$isTarget hasLocation=${tag.isContainsLocationInfo}"
                )

                if (!isTarget) {
                    Log.d(TAG, "LOCATE EVENT IGNORED. Event EPC does not match target. epc=$epc target=$target")
                    return
                }

                if (tag.isContainsLocationInfo) {
                    val distance = tag.LocationInfo.relativeDistance.toInt().coerceIn(0, 100)
                    val rssi = readPeakRssi(tag)

                    Log.d(TAG, "LOCATE DISTANCE. epc=$epc distance=$distance rssi=$rssi")

                    runOnUiThread {
                        val stableDistance = stableLocateProximityFrom(distance)
                        locateDistance = stableDistance
                        locateRssi = rssi
                        maybeBeepForProximity(stableDistance)
                        searchItemMessage = "Locating target tag. Move slowly and follow the signal."
                    }
                } else {
                    val rssi = readPeakRssi(tag)
                    val proximity = rssiToProximityPercent(rssi)

                    Log.d(TAG, "LOCATE RSSI. epc=$epc rssi=$rssi proximity=$proximity")

                    runOnUiThread {
                        val stableProximity = stableLocateProximityFrom(proximity)
                        locateDistance = stableProximity
                        locateRssi = rssi
                        maybeBeepForProximity(stableProximity)
                        searchItemMessage = "Locating target tag. Move slowly and follow the signal."
                    }
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error reading location info", ex)
            }

            return
        }

        if (currentScreen == AppScreen.SEARCH_ITEM && searchRfidMode == SearchRfidMode.DISCOVERING) {
            val prefix = searchExpectedPrefix

            if (prefix.isNotBlank() && epc.startsWith(prefix) && hasValidWarehouse18Checksum(epc)) {
                val rssi = readPeakRssi(tag)
                val now = System.currentTimeMillis()

                synchronized(searchCandidateEpcs) {
                    searchCandidateEpcs.add(epc)

                    val existing = searchCandidateTagInfos[epc]
                    searchCandidateTagInfos[epc] = if (existing == null) {
                        SearchCandidateTagInfo(
                            epc = epc,
                            rssi = rssi,
                            reads = 1,
                            lastSeenAt = now
                        )
                    } else {
                        existing.copy(
                            rssi = rssi,
                            reads = existing.reads + 1,
                            lastSeenAt = now
                        )
                    }
                }

                runOnUiThread {
                    val candidates = sortedSearchCandidates()
                    val count = candidates.size

                    searchCandidateOptions = candidates

                    searchItemMessage = if (count == 1) {
                        "Matching RFID tag found."
                    } else {
                        "Multiple matching RFID tags found ($count). Tap one to locate."
                    }
                }
            }

            return
        }

        if (currentScreen == AppScreen.PROGRAM_TAG && programRfidMode != ProgramRfidMode.IDLE) {
            val rssi = readPeakRssi(tag)
            val now = System.currentTimeMillis()

            synchronized(programDetectedEpcs) {
                val existing = programDetectedEpcs[epc]

                programDetectedEpcs[epc] = if (existing == null) {
                    ProgramDetectedTagInfo(
                        epc = epc,
                        rssi = rssi,
                        reads = 1,
                        lastSeenAt = now
                    )
                } else {
                    existing.copy(
                        rssi = rssi,
                        reads = existing.reads + 1,
                        lastSeenAt = now
                    )
                }
            }

            runOnUiThread {
                when (programRfidMode) {
                    ProgramRfidMode.DETECTING -> {
                        val candidates = sortedProgramDetectedTags()
                        val count = candidates.size

                        programCandidateOptions = candidates
                        programDetectedTagEpc = if (count == 1) candidates.first().epc else ""

                        programTagMessage = if (count == 1) {
                            "RFID tag detected. Release the trigger to use it:\n${candidates.first().epc}"
                        } else {
                            "Multiple RFID tags detected ($count). Release the trigger and select the tag to program."
                        }
                    }

                    ProgramRfidMode.VERIFYING -> {
                        programTagMessage = "Verifying programmed EPC..."
                    }

                    ProgramRfidMode.IDLE -> {
                        // Nothing.
                    }
                }
            }

            return
        }

        if (currentScreen == AppScreen.INVENTORY_BY_LOCATION) {
            handleRawEpc(epc)
        }
    }

    override fun eventStatusNotify(rfidStatusEvents: RfidStatusEvents?) {
        try {
            val statusData = rfidStatusEvents?.StatusEventData ?: return
            val eventType = statusData.statusEventType

            if (eventType == STATUS_EVENT_TYPE.HANDHELD_TRIGGER_EVENT) {
                when (val triggerEvent = statusData.HandheldTriggerEventData.handheldEvent) {
                    HANDHELD_TRIGGER_EVENT_TYPE.HANDHELD_TRIGGER_PRESSED -> {
                        when (currentScreen) {
                            AppScreen.INVENTORY_BY_LOCATION -> {
                                startInventoryFromTrigger()
                            }

                            AppScreen.SEARCH_ITEM -> {
                                handleSearchTriggerPressed()
                            }

                            AppScreen.PROGRAM_TAG -> {
                                startProgramTagReadFromTriggerIfReady()
                            }

                            else -> {
                                Log.d(TAG, "Trigger pressed ignored on screen: $currentScreen")
                            }
                        }
                    }

                    HANDHELD_TRIGGER_EVENT_TYPE.HANDHELD_TRIGGER_RELEASED -> {
                        when (currentScreen) {
                            AppScreen.INVENTORY_BY_LOCATION -> {
                                stopInventoryFromTrigger()
                            }

                            AppScreen.SEARCH_ITEM -> {
                                // Do nothing on release. Press starts or stops Search tag.
                            }

                            AppScreen.PROGRAM_TAG -> {
                                stopProgramTagReadFromTriggerIfRunning()
                            }

                            else -> {
                                Log.d(TAG, "Trigger released ignored on screen: $currentScreen")
                            }
                        }
                    }

                    else -> {
                        Log.d(TAG, "Trigger event ignored: $triggerEvent")
                    }
                }
            }
        } catch (ex: Exception) {
            Log.e(TAG, "Error handling RFID status event", ex)
        }
    }

    private fun generateWarehouse18Epc(
        classCodeHex: String,
        objectId: Long,
        tidTailHex: String
    ): String {
        val prefix = "18"
        val cleanClass = classCodeHex.trim().uppercase(Locale.ROOT).padStart(2, '0').takeLast(2)
        val cleanObjectId = objectId.toString(16).uppercase(Locale.ROOT).padStart(6, '0').takeLast(6)
        val cleanTidTail = tidTailHex.trim().uppercase(Locale.ROOT).padStart(12, '0').takeLast(12)

        val withoutChecksum = prefix + cleanClass + cleanObjectId + cleanTidTail

        if (!isHexString(withoutChecksum) || withoutChecksum.length != 22) {
            throw RuntimeException("Invalid EPC body generated: $withoutChecksum")
        }

        val checksum = xorChecksumHex(withoutChecksum)

        return withoutChecksum + checksum
    }

    private fun buildProgramTargetFromBarcodeAndTid(
        barcode: String,
        currentEpc: String,
        tidHex: String
    ): ProgramTagTarget {
        val cleanBarcode = barcode.trim().uppercase(Locale.ROOT)

        if (cleanBarcode.isBlank()) {
            throw RuntimeException("Barcode is empty.")
        }

        val classCode = classCodeFromBarcode(cleanBarcode)
        val objectId = objectIdFromBarcode(cleanBarcode)
        val tidTail = tidTailFromTid(tidHex)

        val generatedEpc = generateWarehouse18Epc(
            classCodeHex = classCode,
            objectId = objectId,
            tidTailHex = tidTail
        )

        return ProgramTagTarget(
            displayLabel = cleanBarcode,
            barcode = cleanBarcode,
            currentEpc = currentEpc.trim().uppercase(Locale.ROOT),
            tidHex = normalizeHex(tidHex),
            tidTailHex = tidTail,
            classCodeHex = classCode,
            objectId = objectId,
            epc = generatedEpc
        )
    }

    private fun classCodeFromBarcode(barcode: String): String {
        val value = barcode.trim().uppercase(Locale.ROOT)

        return when {
            value.startsWith("CN235") || value.startsWith("235") -> "0B"
            value.startsWith("C295") || value.startsWith("295") -> "0C"
            value.startsWith("A400M") || value.startsWith("A400") -> "0D"
            value.startsWith("A330") -> "0E"
            else -> "0B"
        }
    }

    private fun objectIdFromBarcode(barcode: String): Long {
        val clean = barcode.trim().uppercase(Locale.ROOT)

        val suffixAfterDash = clean.substringAfterLast('-', missingDelimiterValue = "")
        val suffixNumber = Regex("\\d+").find(suffixAfterDash)?.value?.toLongOrNull()

        val numericObjectId = suffixNumber
            ?: Regex("\\d+").findAll(clean).lastOrNull()?.value?.toLongOrNull()

        val objectId = numericObjectId ?: stableBarcodeHash24(clean)

        if (objectId <= 0L || objectId > 0xFFFFFFL) {
            throw RuntimeException("Object ID '$objectId' does not fit in 3 bytes for barcode: $barcode")
        }

        return objectId
    }

    private fun stableBarcodeHash24(value: String): Long {
        var hash = 0x811C9DC5.toInt()

        value.encodeToByteArray().forEach { byte ->
            hash = hash xor (byte.toInt() and 0xFF)
            hash *= 0x01000193
        }

        return (hash.toLong() and 0xFFFFFFL).coerceAtLeast(1L)
    }

    private fun tidTailFromTid(tidHex: String): String {
        val cleanTid = normalizeHex(tidHex)

        if (cleanTid.length < 12) {
            throw RuntimeException("TID is too short. Expected at least 6 bytes, got: $cleanTid")
        }

        return cleanTid.takeLast(12)
    }

    private fun xorChecksumHex(hexWithoutChecksum: String): String {
        if (hexWithoutChecksum.length % 2 != 0) {
            throw RuntimeException("Checksum input must have even hex length.")
        }

        var checksum = 0

        for (i in hexWithoutChecksum.indices step 2) {
            val byteValue = hexWithoutChecksum.substring(i, i + 2).toInt(16)
            checksum = checksum xor byteValue
        }

        return checksum.toString(16).uppercase(Locale.ROOT).padStart(2, '0')
    }

    private fun isValidHexEpc(value: String): Boolean {
        val clean = value.trim().uppercase(Locale.ROOT)

        return clean.isNotBlank() &&
                clean.length % 2 == 0 &&
                clean.length % 4 == 0 &&
                isHexString(clean)
    }

    private fun isHexString(value: String): Boolean {
        return Regex("^[0-9A-Fa-f]+$").matches(value)
    }

    private fun normalizeHex(value: String): String {
        return value
            .trim()
            .replace(" ", "")
            .replace(":", "")
            .replace("-", "")
            .uppercase(Locale.ROOT)
    }

    private fun expectedEpcPrefixFromBarcode(barcode: String): String {
        val cleanBarcode = barcode.trim().uppercase(Locale.ROOT)

        if (cleanBarcode.isBlank()) {
            throw RuntimeException("Input is empty.")
        }

        val classCode = classCodeFromBarcode(cleanBarcode)
        val objectId = objectIdFromBarcode(cleanBarcode)
        val objectIdHex = objectId
            .toString(16)
            .uppercase(Locale.ROOT)
            .padStart(6, '0')
            .takeLast(6)

        return "18$classCode$objectIdHex"
    }

    private fun looksLikeWarehouse18FullEpc(value: String): Boolean {
        val clean = normalizeHex(value)

        return clean.startsWith("18") &&
                clean.length == 24 &&
                clean.length % 4 == 0 &&
                isHexString(clean) &&
                hasValidWarehouse18Checksum(clean)
    }

    private fun hasValidWarehouse18Checksum(epc: String): Boolean {
        val clean = normalizeHex(epc)

        if (clean.length < 4 || clean.length % 2 != 0) {
            return false
        }

        val body = clean.dropLast(2)
        val expectedChecksum = clean.takeLast(2)

        return try {
            xorChecksumHex(body) == expectedChecksum
        } catch (_: Exception) {
            false
        }
    }

    private fun handleRawEpc(epc: String, bypassDedupe: Boolean = false) {
        val cleanEpc = epc.trim().uppercase(Locale.ROOT)

        if (!bypassDedupe && !shouldProcessEpc(cleanEpc)) {
            return
        }

        val locationId = selectedLocationId

        if (locationId == null) {
            runOnUiThread {
                message = "Load a valid location first."
            }
            return
        }

        val cachedValidation = synchronized(epcValidationCache) {
            epcValidationCache[cleanEpc]
        }

        if (cachedValidation != null) {
            runOnUiThread {
                applyScanValidation(cachedValidation, cleanEpc)
            }
            return
        }

        val shouldStartValidation = synchronized(pendingEpcValidations) {
            if (pendingEpcValidations.contains(cleanEpc)) {
                false
            } else {
                pendingEpcValidations.add(cleanEpc)
                true
            }
        }

        if (!shouldStartValidation) {
            return
        }

        isValidating = true

        thread {
            try {
                val url = buildUrl("/locations/$locationId/handheld-inventory/validate-scan")

                val body = JSONObject()
                    .put("epc", cleanEpc)
                    .put("reader_id", DEFAULT_READER_ID)
                    .toString()

                val response = httpPostJson(url, body)
                val json = JSONObject(response)
                val validation = parseScanValidation(json)

                synchronized(epcValidationCache) {
                    epcValidationCache[cleanEpc] = validation
                }

                runOnUiThread {
                    applyScanValidation(validation, cleanEpc)
                    isValidating = false
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error validating EPC", ex)

                runOnUiThread {
                    isValidating = false
                    message = "Error validating EPC: ${ex.message}"
                }
            } finally {
                synchronized(pendingEpcValidations) {
                    pendingEpcValidations.remove(cleanEpc)
                }
            }
        }
    }

    private fun shouldProcessEpc(epc: String): Boolean {
        val now = System.currentTimeMillis()

        synchronized(recentEpcs) {
            val lastSeen = recentEpcs[epc]

            if (lastSeen != null && now - lastSeen < EPC_DEDUPE_MS) {
                return false
            }

            recentEpcs[epc] = now

            val oldKeys = recentEpcs
                .filterValues { now - it > 30_000L }
                .keys
                .toList()

            oldKeys.forEach { recentEpcs.remove(it) }

            return true
        }
    }

    private fun applyScanValidation(validation: ScanValidationResult, epc: String) {
        if (!validation.isValidTagFormat) {
            message = "Invalid Warehouse18 tag format."
            return
        }

        val itemCode = normalizeItemCode(validation.itemCode ?: "")

        if (itemCode.isBlank()) {
            message = "RFID tag read, but backend returned no item code."
            return
        }

        val loadedRow = loadedRows[itemCode]

        if (loadedRow == null) {
            Log.d(TAG, "Ignored read: $itemCode is not loaded in current table.")
            message = "RFID tag read: $itemCode, but it is not expected in this location."
            return
        }

        val cleanEpc = normalizeHex(epc)

        if (cleanEpc.isBlank()) {
            message = "RFID tag read for $itemCode, but EPC was empty."
            return
        }

        if (cleanEpc in loadedRow.readEpcs) {
            message = "RFID tag already counted for: $itemCode"
            return
        }

        val newReadEpcs = loadedRow.readEpcs + cleanEpc
        val newReads = newReadEpcs.size

        loadedRows[itemCode] = loadedRow.copy(
            reads = newReads,
            status = statusForInventoryRow(
                qty = loadedRow.qty,
                reads = newReads
            ),
            readEpcs = newReadEpcs
        )

        message = "Loaded item read: $itemCode ($newReads/${loadedRow.qty})"
    }

    private fun parseScanValidation(json: JSONObject): ScanValidationResult {
        val status = readStringDeep(
            json,
            listOf("status", "result", "scan_status", "validation_status")
        ).lowercase(Locale.ROOT)

        val validBoolean = readBooleanDeep(
            json,
            listOf("valid", "is_valid", "valid_epc", "isValid")
        )

        val invalidByText =
            status.contains("invalid") ||
                    status.contains("invalid_epc") ||
                    status.contains("bad_epc") ||
                    status.contains("error_epc")

        val isValidTagFormat = when {
            invalidByText -> false
            validBoolean != null -> validBoolean
            else -> true
        }

        val itemCode = extractItemCodeFromScan(json)

        return ScanValidationResult(
            isValidTagFormat = isValidTagFormat,
            itemCode = itemCode
        )
    }

    private fun extractExpectedItemCodes(json: JSONObject): List<String> {
        val result = mutableListOf<String>()

        fun addCode(value: String?) {
            val normalized = normalizeItemCode(value ?: "")

            if (normalized.isNotBlank()) {
                result.add(normalized)
            }
        }

        fun addFromItemObject(item: JSONObject?) {
            if (item == null) return

            addCode(
                item.optString("item_code")
                    .ifBlank { item.optString("itemCode") }
                    .ifBlank { item.optString("code") }
                    .ifBlank { item.optString("part_number") }
                    .ifBlank { item.optString("partNumber") }
            )
        }

        fun addFromLine(line: JSONObject) {
            addCode(
                line.optString("item_code")
                    .ifBlank { line.optString("itemCode") }
                    .ifBlank { line.optString("part_number") }
                    .ifBlank { line.optString("partNumber") }
            )

            addFromItemObject(line.optJSONObject("item"))

            val asset = line.optJSONObject("asset")

            if (asset != null) {
                addCode(
                    asset.optString("item_code")
                        .ifBlank { asset.optString("itemCode") }
                )

                val assetCode = asset.optString("asset_code")
                    .ifBlank { asset.optString("assetCode") }
                    .ifBlank { asset.optString("code") }

                if (looksLikeItemCode(assetCode)) {
                    addCode(assetCode)
                }

                addFromItemObject(asset.optJSONObject("item"))
            }

            val container = line.optJSONObject("container")
                ?: line.optJSONObject("stock_container")
                ?: line.optJSONObject("stockContainer")

            if (container != null) {
                addCode(
                    container.optString("item_code")
                        .ifBlank { container.optString("itemCode") }
                )

                addFromItemObject(container.optJSONObject("item"))
            }
        }

        fun readArray(array: JSONArray?) {
            if (array == null) return

            for (i in 0 until array.length()) {
                val line = array.optJSONObject(i)

                if (line != null) {
                    addFromLine(line)
                }
            }
        }

        readArray(json.optJSONArray("stock_lines"))
        readArray(json.optJSONArray("stockLines"))
        readArray(json.optJSONArray("assets"))
        readArray(json.optJSONArray("asset_lines"))
        readArray(json.optJSONArray("assetLines"))
        readArray(json.optJSONArray("containers"))
        readArray(json.optJSONArray("stock_containers"))
        readArray(json.optJSONArray("stockContainers"))
        readArray(json.optJSONArray("container_stock"))
        readArray(json.optJSONArray("containerStock"))


        json.optJSONArray("data")?.let { dataArray ->
            readArray(dataArray)
        }

        json.optJSONObject("data")?.let { dataObject ->
            readArray(dataObject.optJSONArray("stock_lines"))
            readArray(dataObject.optJSONArray("stockLines"))
            readArray(dataObject.optJSONArray("assets"))
            readArray(dataObject.optJSONArray("asset_lines"))
            readArray(dataObject.optJSONArray("assetLines"))
            readArray(dataObject.optJSONArray("containers"))
            readArray(dataObject.optJSONArray("stock_containers"))
            readArray(dataObject.optJSONArray("stockContainers"))
            readArray(dataObject.optJSONArray("container_stock"))
            readArray(dataObject.optJSONArray("containerStock"))
        }

        return result
    }

    private fun extractItemCodeFromScan(json: JSONObject): String? {
        val direct = json.optString("item_code")
            .ifBlank { json.optString("itemCode") }
            .ifBlank { json.optString("part_number") }
            .ifBlank { json.optString("partNumber") }

        if (direct.isNotBlank()) {
            return direct
        }

        val item = json.optJSONObject("item")

        if (item != null) {
            val itemCode = item.optString("item_code")
                .ifBlank { item.optString("itemCode") }
                .ifBlank { item.optString("code") }

            if (itemCode.isNotBlank()) {
                return itemCode
            }
        }

        val asset = json.optJSONObject("asset")

        if (asset != null) {
            val assetItemCode = asset.optString("item_code")
                .ifBlank { asset.optString("itemCode") }

            if (assetItemCode.isNotBlank()) {
                return assetItemCode
            }

            val assetCode = asset.optString("asset_code")
                .ifBlank { asset.optString("assetCode") }
                .ifBlank { asset.optString("code") }

            if (looksLikeItemCode(assetCode)) {
                return assetCode
            }

            val assetItem = asset.optJSONObject("item")

            if (assetItem != null) {
                val code = assetItem.optString("item_code")
                    .ifBlank { assetItem.optString("itemCode") }
                    .ifBlank { assetItem.optString("code") }

                if (code.isNotBlank()) {
                    return code
                }
            }
        }

        val container = json.optJSONObject("container")
            ?: json.optJSONObject("stock_container")
            ?: json.optJSONObject("stockContainer")

        if (container != null) {
            val containerItemCode = container.optString("item_code")
                .ifBlank { container.optString("itemCode") }

            if (containerItemCode.isNotBlank()) {
                return containerItemCode
            }

            val containerItem = container.optJSONObject("item")

            if (containerItem != null) {
                val code = containerItem.optString("item_code")
                    .ifBlank { containerItem.optString("itemCode") }
                    .ifBlank { containerItem.optString("code") }

                if (code.isNotBlank()) {
                    return code
                }
            }
        }

        json.optJSONObject("data")?.let { dataObject ->
            return extractItemCodeFromScan(dataObject)
        }

        val code = json.optString("code")

        if (looksLikeItemCode(code)) {
            return code
        }

        return null
    }

    private fun initToneGenerator() {
        try {
            toneGenerator?.release()
        } catch (_: Exception) {
        }

        try {
            toneGenerator = ToneGenerator(AudioManager.STREAM_MUSIC, 100)
            Log.d(TAG, "ToneGenerator initialized.")
        } catch (ex: Exception) {
            Log.e(TAG, "Error creating ToneGenerator", ex)
            toneGenerator = null
        }
    }

    private fun maybeBeepForProximity(proximity: Int) {
        latestLocateProximity = proximity.coerceIn(0, 100)

        if (isLocatingTag && !locateBeepLoopRunning) {
            startLocateBeepLoop()
        }
    }

    private fun resetLocateBeep() {
        latestLocateProximity = 0
        locateProximitySamples.clear()
        smoothedLocateProximity = null
    }

    private fun startLocateBeepLoop() {
        if (locateBeepLoopRunning) {
            return
        }

        if (toneGenerator == null) {
            initToneGenerator()
        }

        locateBeepLoopRunning = true

        locateBeepThread = thread(start = true, name = "Warehouse18LocateBeepLoop") {
            Log.d(TAG, "Locate beep loop started.")

            while (locateBeepLoopRunning) {
                val proximity = latestLocateProximity.coerceIn(0, 100)
                val intervalMs = locateBeepIntervalMs(proximity)

                try {
                    toneGenerator?.startTone(
                        ToneGenerator.TONE_PROP_BEEP,
                        60
                    )

                    Log.d(TAG, "Locate beep. proximity=$proximity intervalMs=$intervalMs")
                } catch (ex: Exception) {
                    Log.d(TAG, "Could not play locate beep: ${ex.message}")
                }

                try {
                    Thread.sleep(intervalMs)
                } catch (_: InterruptedException) {
                    return@thread
                }
            }

            Log.d(TAG, "Locate beep loop stopped.")
        }
    }

    private fun stopLocateBeepLoop() {
        locateBeepLoopRunning = false

        try {
            locateBeepThread?.interrupt()
        } catch (_: Exception) {
        }

        locateBeepThread = null

        try {
            toneGenerator?.stopTone()
        } catch (_: Exception) {
        }
    }

    private fun locateBeepIntervalMs(proximity: Int): Long {
        val cleanProximity = proximity.coerceIn(0, 100)

        val maxIntervalMs = 1200L
        val minIntervalMs = 90L

        return maxIntervalMs - ((maxIntervalMs - minIntervalMs) * cleanProximity / 100L)
    }

    private fun readPeakRssi(tag: TagData): Int {
        return try {
            tag.peakRSSI.toInt()
        } catch (ex: Exception) {
            Log.d(TAG, "Could not read tag RSSI: ${ex.message}")
            -80
        }
    }

    private fun stableLocateProximityFrom(rawProximity: Int): Int {
        val raw = rawProximity.coerceIn(0, 100)

        locateProximitySamples.add(raw)
        while (locateProximitySamples.size > 9) {
            locateProximitySamples.removeAt(0)
        }

        val sortedSamples = locateProximitySamples.sorted()
        val median = sortedSamples[sortedSamples.size / 2]

        val previous = smoothedLocateProximity
        val filtered = if (previous == null) {
            median.toFloat()
        } else {
            val alpha = if (median > previous) 0.35f else 0.18f
            val next = previous + alpha * (median - previous)

            if (kotlin.math.abs(next - previous) < 2.0f) {
                previous
            } else {
                next
            }
        }

        smoothedLocateProximity = filtered
        return filtered.toInt().coerceIn(0, 100)
    }

    private fun rssiToProximityPercent(rssi: Int): Int {
        val normalized = if (rssi >= 0) {
            val minPositiveRssi = 35f
            val maxPositiveRssi = 80f
            ((rssi.toFloat() - minPositiveRssi) / (maxPositiveRssi - minPositiveRssi))
        } else {
            val minDbmRssi = -80f
            val maxDbmRssi = -35f
            ((rssi.toFloat() - minDbmRssi) / (maxDbmRssi - minDbmRssi))
        }.coerceIn(0f, 1f)

        return (java.lang.Math.pow(normalized.toDouble(), 0.85).toFloat() * 100f)
            .toInt()
            .coerceIn(0, 100)
    }


    private fun readStringDeep(json: JSONObject, keys: List<String>): String {
        for (key in keys) {
            val value = json.optString(key)

            if (value.isNotBlank()) {
                return value
            }
        }

        json.optJSONObject("data")?.let { dataObject ->
            val value = readStringDeep(dataObject, keys)

            if (value.isNotBlank()) {
                return value
            }
        }

        return ""
    }

    private fun readBooleanDeep(json: JSONObject, keys: List<String>): Boolean? {
        for (key in keys) {
            if (json.has(key)) {
                when (val raw = json.opt(key)) {
                    is Boolean -> return raw

                    is String -> {
                        if (raw.equals("true", ignoreCase = true)) return true
                        if (raw.equals("false", ignoreCase = true)) return false
                    }

                    is Number -> return raw.toInt() != 0
                }
            }
        }

        json.optJSONObject("data")?.let { dataObject ->
            return readBooleanDeep(dataObject, keys)
        }

        return null
    }

    private fun handleSearchTriggerPressed() {
        if (isSearchingItem || isLocatingTag) {
            stopSearchOrLocateTag()
            return
        }

        val hasTargetToResume =
            searchResolvedEpc.isNotBlank() ||
                    locateTargetEpc.isNotBlank()

        if (hasTargetToResume) {
            startLocateSelectedTag()
        } else {
            searchItem()
        }
    }

    private fun stopSearchOrLocateTag(): Boolean {
        if (isSearchingItem) {
            return stopSearchItemDiscovery()
        }

        if (isLocatingTag) {
            stopLocateTag()
            return true
        }

        return false
    }

    private fun stopSearchItemDiscovery(showMessage: Boolean = true): Boolean {
        if (!isSearchingItem && searchRfidMode != SearchRfidMode.DISCOVERING) {
            return false
        }

        searchDiscoverSessionToken += 1
        isSearchingItem = false
        searchRfidMode = SearchRfidMode.IDLE

        thread {
            try {
                rfidReader?.Actions?.Inventory?.stop()
            } catch (ex: Exception) {
                Log.d(TAG, "Inventory stop ignored while stopping search discovery: ${ex.message}")
            }
        }

        if (showMessage) {
            searchItemMessage = "RFID search stopped."
        }

        return true
    }


    private fun startLocateSelectedTag() {
        val target = searchResolvedEpc
            .ifBlank { locateTargetEpc }
            .ifBlank { searchItemText.trim().uppercase(Locale.ROOT) }

        if (target.isBlank()) {
            searchItemMessage = "Enter or scan an item/asset code or full EPC."
            return
        }

        if (!looksLikeWarehouse18FullEpc(target)) {
            searchItem()
            return
        }

        if (isInventoryRunning) {
            searchItemMessage = "Stop inventory reading before locating a tag."
            return
        }

        ensureReaderConnectedForLocate {
            startLocateInternal(target)
        }
    }

    private fun ensureReaderConnectedForLocate(afterConnected: () -> Unit) {
        val alreadyConnected = rfidReader?.isConnected == true && isReaderConnected

        if (alreadyConnected) {
            afterConnected()
            return
        }

        searchItemMessage = "Connecting RFID reader for tag location..."

        thread {
            try {
                readers = Readers(this@MainActivity, ENUM_TRANSPORT.SERVICE_SERIAL)
                val availableReaders = readers?.GetAvailableRFIDReaderList()

                if (availableReaders.isNullOrEmpty()) {
                    runOnUiThread {
                        isReaderConnected = false
                        isSearchingItem = false
                        searchRfidMode = SearchRfidMode.IDLE
                        searchItemMessage = "No RFID reader was found on the Zebra device."
                    }
                    return@thread
                }

                rfidReader = availableReaders[0].rfidReader

                if (rfidReader?.isConnected != true) {
                    rfidReader?.connect()
                }

                rfidReader?.Events?.addEventsListener(this@MainActivity)
                rfidReader?.Events?.setTagReadEvent(true)
                rfidReader?.Events?.setAttachTagDataWithReadEvent(false)
                rfidReader?.Events?.setHandheldEvent(true)

                runOnUiThread {
                    isReaderConnected = true
                    searchItemMessage = "RFID ready for tag location."
                    afterConnected()
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error connecting RFID reader for locate", ex)

                runOnUiThread {
                    isReaderConnected = false
                    isSearchingItem = false
                    searchRfidMode = SearchRfidMode.IDLE
                    searchItemMessage = "Error connecting RFID reader: ${ex.message}"
                }
            }
        }
    }

    private fun startLocateInternal(epc: String) {
        val cleanEpc = epc.trim().uppercase(Locale.ROOT)

        runOnUiThread {
            stopLocateBeepLoop()
            locateTargetEpc = cleanEpc
            locateDistance = null
            locateRssi = null
            resetLocateBeep()
            isLocatingTag = true
            searchRfidMode = SearchRfidMode.LOCATING
            startLocateBeepLoop()
            searchItemMessage = "Starting tag location...\n$cleanEpc"
        }

        thread {
            try {
                val reader = rfidReader
                    ?: throw RuntimeException("RFID reader is not initialized.")

                if (!reader.isConnected) {
                    throw RuntimeException("RFID reader is not connected.")
                }

                Log.d(TAG, "START LOCATE BY INVENTORY RSSI. epc=$cleanEpc")

                try {
                    reader.Actions.TagLocationing.Stop()
                    Log.d(TAG, "Previous TagLocationing stopped before RSSI locate.")
                } catch (ex: Exception) {
                    Log.d(TAG, "Previous TagLocationing stop ignored: ${ex.message}")
                }

                try {
                    reader.Actions.Inventory.stop()
                    Log.d(TAG, "Inventory stopped before RSSI locate.")
                } catch (ex: Exception) {
                    Log.d(TAG, "Inventory stop ignored before RSSI locate: ${ex.message}")
                }

                useBufferedReadEvents()

                Log.d(TAG, "Starting continuous inventory for selected EPC=$cleanEpc")
                reader.Actions.Inventory.perform()
                Log.d(TAG, "Continuous inventory started for RSSI locate.")

                runOnUiThread {
                    searchItemMessage =
                        "Locating EPC:\n$cleanEpc\nMove slowly and follow the signal proximity."
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error starting RSSI tag location", ex)

                runOnUiThread {
                    isLocatingTag = false
                    locateDistance = null
                    stopLocateBeepLoop()
                    resetLocateBeep()
                    searchRfidMode = SearchRfidMode.IDLE
                    searchItemMessage = "Error starting tag location: ${ex.message}"
                }
            }
        }
    }

    private fun stopLocateTag(showMessage: Boolean = true) {
        if (!isLocatingTag) {
            return
        }

        thread {
            try {
                try {
                    rfidReader?.Actions?.Inventory?.stop()
                    Log.d(TAG, "RSSI locate inventory stopped.")
                } catch (ex: Exception) {
                    Log.d(TAG, "Inventory stop ignored while stopping locate: ${ex.message}")
                }

                try {
                    rfidReader?.Actions?.TagLocationing?.Stop()
                    Log.d(TAG, "TagLocationing stopped while stopping locate.")
                } catch (ex: Exception) {
                    Log.d(TAG, "TagLocationing stop ignored while stopping locate: ${ex.message}")
                }

                runOnUiThread {
                    isLocatingTag = false
                    locateRssi = null
                    stopLocateBeepLoop()
                    resetLocateBeep()
                    searchRfidMode = SearchRfidMode.IDLE

                    if (showMessage) {
                        searchItemMessage = if (locateTargetEpc.isBlank()) {
                            "Tag location paused."
                        } else {
                            "Tag location stopped. Tap the tag again or press Find nearby tags to search again."
                        }
                    }
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error stopping tag location", ex)

                runOnUiThread {
                    isLocatingTag = false
                    locateRssi = null
                    stopLocateBeepLoop()
                    resetLocateBeep()
                    searchRfidMode = SearchRfidMode.IDLE

                    if (showMessage) {
                        searchItemMessage = "Error stopping RFID location: ${ex.message}"
                    }
                }
            }
        }
    }

    private fun lookupRegisteredLocationForSearch(barcode: String) {
        val cleanBarcode = barcode.trim()

        if (cleanBarcode.isBlank()) {
            searchRegisteredLocationState = SearchRegisteredLocationState.Idle
            return
        }

        thread {
            val result = try {
                val encoded = URLEncoder.encode(cleanBarcode, "UTF-8")
                val response = httpGet("$serverBaseUrl/handheld/resolve-item?q=$encoded")
                parseSearchRegisteredLocationResponse(response)
            } catch (ex: Exception) {
                if (ex.message.orEmpty().contains("HTTP 404")) {
                    SearchRegisteredLocationState.NotFound(cleanBarcode)
                } else {
                    SearchRegisteredLocationState.Error(ex.message ?: "Unknown backend error")
                }
            }

            runOnUiThread {
                if (currentScreen == AppScreen.SEARCH_ITEM &&
                    searchItemText.trim().equals(cleanBarcode, ignoreCase = true)
                ) {
                    searchRegisteredLocationState = result
                }
            }
        }
    }

    private fun parseSearchRegisteredLocationResponse(body: String): SearchRegisteredLocationState {
        val root = JSONObject(body.trim())
        val data = root.optJSONObject("data") ?: root

        val location = data.optJSONObject("location")
            ?: data.optJSONObject("current_location")
            ?: data.optJSONObject("currentLocation")
            ?: data.optJSONObject("registered_location")
            ?: data.optJSONObject("registeredLocation")

        val locationName = location?.optString("name", "").orEmpty()
            .ifBlank { data.optString("location_name") }
            .ifBlank { data.optString("locationName") }
            .ifBlank { data.optString("current_location_name") }
            .ifBlank { data.optString("currentLocationName") }
            .ifBlank { data.optString("registered_location_name") }
            .ifBlank { data.optString("registeredLocationName") }

        val lastMovementAt = data.optString("last_movement_at")
            .ifBlank { data.optString("lastMovementAt") }
            .ifBlank { data.optString("updated_at") }
            .ifBlank { data.optString("updatedAt") }
            .ifBlank { data.optString("since") }

        return SearchRegisteredLocationState.Found(
            SearchRegisteredLocationInfo(
                locationName = locationName,
                lastMovementAt = lastMovementAt
            )
        )
    }

    private fun searchItem() {
        val input = searchItemText.trim().uppercase(Locale.ROOT)

        if (input.isBlank()) {
            searchItemMessage = "Enter or scan an item/asset code or full EPC."
            searchRegisteredLocationState = SearchRegisteredLocationState.Idle
            return
        }

        if (isInventoryRunning) {
            searchItemMessage = "Stop inventory reading before searching a tag."
            return
        }

        if (isLocatingTag) {
            searchItemMessage = "Stop current tag location before starting another search."
            return
        }

        locateDistance = null
        locateTargetEpc = ""
        searchResolvedEpc = ""
        searchExpectedPrefix = ""
        searchCandidateOptions = emptyList()
        searchRegisteredLocationState = SearchRegisteredLocationState.Loading
        clearSearchCandidates()
        lookupRegisteredLocationForSearch(input)

        val normalizedInput = normalizeHex(input)

        if (looksLikeWarehouse18FullEpc(normalizedInput)) {
            searchResolvedEpc = normalizedInput
            locateTargetEpc = normalizedInput
            searchItemMessage = "Full EPC detected. Starting location..."

            ensureReaderConnectedForLocate {
                startLocateInternal(normalizedInput)
            }

            return
        }

        if (normalizedInput.startsWith("18") && normalizedInput.length == 24 && isHexString(normalizedInput)) {
            searchItemMessage = "Full EPC detected, but checksum is invalid. Check the EPC and try again."
            return
        }

        val expectedPrefix = try {
            expectedEpcPrefixFromBarcode(input)
        } catch (ex: Exception) {
            searchItemMessage = "Invalid item/asset code: ${ex.message}"
            return
        }

        searchExpectedPrefix = expectedPrefix
        isSearchingItem = true
        val discoverToken = ++searchDiscoverSessionToken
        searchItemMessage = "Barcode loaded. Find nearby tags, then tap one to locate it."

        ensureReaderConnectedForLocate {
            discoverFullEpcByPrefix(expectedPrefix, discoverToken)
        }
    }

    private fun discoverFullEpcByPrefix(expectedPrefix: String, discoverToken: Int) {
        thread {
            try {
                clearSearchCandidates()
                searchRfidMode = SearchRfidMode.DISCOVERING

                try {
                    rfidReader?.Actions?.TagLocationing?.Stop()
                } catch (_: Exception) {
                }

                try {
                    rfidReader?.Actions?.Inventory?.stop()
                } catch (_: Exception) {
                }

                useBufferedReadEvents()
                rfidReader?.Actions?.Inventory?.perform()

                val startedAt = System.currentTimeMillis()
                while (System.currentTimeMillis() - startedAt < 1_500L) {
                    if (discoverToken != searchDiscoverSessionToken || !isSearchingItem) {
                        try {
                            rfidReader?.Actions?.Inventory?.stop()
                        } catch (_: Exception) {
                        }
                        return@thread
                    }
                    Thread.sleep(80L)
                }

                try {
                    rfidReader?.Actions?.Inventory?.stop()
                } catch (_: Exception) {
                }

                val candidates = sortedSearchCandidates()

                runOnUiThread {
                    if (discoverToken == searchDiscoverSessionToken && isSearchingItem) {
                        isSearchingItem = false
                        searchRfidMode = SearchRfidMode.IDLE

                        when {
                            candidates.isEmpty() -> {
                                searchResolvedEpc = ""
                                locateTargetEpc = ""
                                searchCandidateOptions = emptyList()
                                searchItemMessage =
                                    "No nearby RFID tag found. Check the registered location and try there."
                            }

                            candidates.size == 1 -> {
                                val fullEpc = candidates.first().epc
                                searchResolvedEpc = fullEpc
                                locateTargetEpc = fullEpc
                                searchCandidateOptions = emptyList()
                                searchItemMessage =
                                    "One matching RFID tag found. Starting locate automatically..."
                                startLocateInternal(fullEpc)
                            }

                            else -> {
                                searchResolvedEpc = ""
                                locateTargetEpc = ""
                                searchCandidateOptions = candidates
                                searchItemMessage =
                                    "${candidates.size} matching tags found. Tap one to locate."
                            }
                        }
                    } else {
                        isSearchingItem = false
                        searchRfidMode = SearchRfidMode.IDLE
                        searchItemMessage = "RFID search stopped."
                    }
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error discovering RFID tag by prefix", ex)

                runOnUiThread {
                    isSearchingItem = false
                    searchRfidMode = SearchRfidMode.IDLE
                    searchItemMessage = "RFID search error: ${ex.message}"
                }
            }
        }
    }

    private fun searchCandidateSignalPercent(rssi: Int?, reads: Int): Int {
        return if (rssi != null) {
            rssiToProximityPercent(rssi)
        } else {
            (reads * 8).coerceIn(5, 100)
        }
    }

    private fun sortedSearchCandidates(): List<SearchCandidateTagInfo> {
        return synchronized(searchCandidateEpcs) {
            searchCandidateTagInfos.values.toList()
        }.sortedWith(
            compareByDescending<SearchCandidateTagInfo> { searchCandidateSignalPercent(it.rssi, it.reads) }
                .thenByDescending { it.reads }
                .thenByDescending { it.lastSeenAt }
                .thenBy { it.epc }
        )
    }

    private fun clearSearchCandidates() {
        synchronized(searchCandidateEpcs) {
            searchCandidateEpcs.clear()
            searchCandidateTagInfos.clear()
        }
    }

    private fun clearSearchItemFlow() {
        if (isSearchingItem) {
            stopSearchItemDiscovery(showMessage = false)
        }

        if (isLocatingTag) {
            stopLocateTag(showMessage = false)
        } else {
            stopLocateBeepLoop()
        }

        searchItemText = ""
        searchItemMessage = "Scan or enter an item/asset code or full EPC."

        locateTargetEpc = ""
        locateDistance = null
        locateRssi = null

        searchResolvedEpc = ""
        searchExpectedPrefix = ""
        searchCandidateOptions = emptyList()
        searchRegisteredLocationState = SearchRegisteredLocationState.Idle
        searchRfidMode = SearchRfidMode.IDLE
        searchDiscoverSessionToken += 1

        clearSearchCandidates()
        resetLocateBeep()
    }


    private fun useBufferedReadEvents() {
        try {
            rfidReader?.Events?.setAttachTagDataWithReadEvent(false)
        } catch (ex: Exception) {
            Log.w(TAG, "Could not set buffered RFID read events", ex)
        }
    }

    private fun useAttachedReadEventsForLocate() {
        try {
            /*
             * Zebra's own Locate tutorial reads locationing results using
             * reader.Actions.getReadTags(100) from eventReadNotify.
             * For that path, AttachTagDataWithReadEvent must stay false.
             *
             * If we set it to true, some SDK/device combinations stop filling the
             * getReadTags buffer, and then Locate appears to start but no distance
             * ever reaches the UI. Delightful little trap.
             */
            rfidReader?.Events?.setAttachTagDataWithReadEvent(false)
            Log.d(TAG, "Locate read mode set to buffered getReadTags().")
        } catch (ex: Exception) {
            Log.w(TAG, "Could not set buffered RFID read events for locate", ex)
        }
    }

    private fun selectSearchCandidate(epc: String) {
        val cleanEpc = epc.trim().uppercase(Locale.ROOT)

        if (!looksLikeWarehouse18FullEpc(cleanEpc)) {
            searchItemMessage = "Selected EPC is not a valid Warehouse18 EPC."
            return
        }

        if (isSearchingItem) {
            searchItemMessage = "Wait until the current search finishes."
            return
        }

        val wasLocating = isLocatingTag

        if (wasLocating) {
            isLocatingTag = false
            searchRfidMode = SearchRfidMode.IDLE
            stopLocateBeepLoop()
            resetLocateBeep()

            thread {
                try {
                    rfidReader?.Actions?.Inventory?.stop()
                } catch (ex: Exception) {
                    Log.d(TAG, "Inventory stop ignored while switching locate target: ${ex.message}")
                }

                try {
                    rfidReader?.Actions?.TagLocationing?.Stop()
                } catch (ex: Exception) {
                    Log.d(TAG, "TagLocationing stop ignored while switching locate target: ${ex.message}")
                }

                runOnUiThread {
                    startSelectedSearchCandidate(cleanEpc)
                }
            }

            return
        }

        startSelectedSearchCandidate(cleanEpc)
    }

    private fun startSelectedSearchCandidate(cleanEpc: String) {
        locateDistance = null
        locateRssi = null
        resetLocateBeep()
        searchResolvedEpc = cleanEpc
        locateTargetEpc = cleanEpc
        searchItemMessage = "Tag selected. Locate mode starts automatically."

        ensureReaderConnectedForLocate {
            startLocateInternal(cleanEpc)
        }
    }

    private fun sortedProgramDetectedTags(): List<ProgramDetectedTagInfo> {
        return synchronized(programDetectedEpcs) {
            programDetectedEpcs.values.toList()
        }.sortedWith(
            compareByDescending<ProgramDetectedTagInfo> { programTagSignalPercent(it.rssi, it.reads) }
                .thenByDescending { it.reads }
                .thenByDescending { it.lastSeenAt }
                .thenBy { it.epc }
        )
    }

    private fun startProgramTagReadFromTriggerIfReady(): Boolean {
        if (currentScreen != AppScreen.PROGRAM_TAG) {
            return false
        }

        val barcode = programItemText.trim()

        if (barcode.isBlank()) {
            programTagMessage = "Trigger detected. Scan or enter a barcode before reading RFID."
            return true
        }

        if (isProgrammingTag) {
            programTagMessage = "Wait until tag programming finishes."
            return true
        }

        if (isInventoryRunning || isLocatingTag) {
            programTagMessage = "Stop the current RFID operation before reading a program tag."
            return true
        }

        if (isProgramTriggerReading || isDetectingProgramTag) {
            programTagMessage = "RFID tag reading is already running. Release the trigger to stop."
            return true
        }

        val sessionToken = ++programReadSessionToken

        clearProgramDetectedTags()
        programCandidateOptions = emptyList()
        programSelectedTarget = null
        programDetectedTagEpc = ""
        programTidTailText = ""
        programEpcText = ""
        programRfidMode = ProgramRfidMode.DETECTING
        isProgramTriggerReading = true
        isDetectingProgramTag = true
        programTagMessage = "Trigger pressed. Reading RFID tags. Release the trigger to stop."

        connectReaderForProgramIfNeeded {
            if (
                sessionToken != programReadSessionToken ||
                !isProgramTriggerReading ||
                currentScreen != AppScreen.PROGRAM_TAG
            ) {
                thread {
                    try {
                        rfidReader?.Actions?.Inventory?.stop()
                    } catch (_: Exception) {
                    }
                }
                return@connectReaderForProgramIfNeeded
            }

            thread {
                try {
                    try {
                        rfidReader?.Actions?.Inventory?.stop()
                    } catch (_: Exception) {
                    }

                    useBufferedReadEvents()
                    rfidReader?.Actions?.Inventory?.perform()

                    runOnUiThread {
                        if (sessionToken == programReadSessionToken && isProgramTriggerReading) {
                            programTagMessage = "Reading RFID tags. Release the trigger to stop and select the tag."
                        }
                    }
                } catch (ex: Exception) {
                    Log.e(TAG, "Error starting Program tag trigger read", ex)

                    runOnUiThread {
                        if (sessionToken == programReadSessionToken) {
                            isProgramTriggerReading = false
                            isDetectingProgramTag = false
                            programRfidMode = ProgramRfidMode.IDLE
                            programTagMessage = "RFID read error: ${ex.message}"
                        }
                    }
                }
            }
        }

        return true
    }

    private fun stopProgramTagReadFromTriggerIfRunning(): Boolean {
        if (currentScreen != AppScreen.PROGRAM_TAG) {
            return false
        }

        if (!isProgramTriggerReading && !(isDetectingProgramTag && programRfidMode == ProgramRfidMode.DETECTING)) {
            return true
        }

        programReadSessionToken += 1
        isProgramTriggerReading = false
        programTagMessage = "Trigger released. Stopping RFID read..."

        thread {
            try {
                try {
                    rfidReader?.Actions?.Inventory?.stop()
                } catch (_: Exception) {
                }

                val detected = sortedProgramDetectedTags()

                runOnUiThread {
                    isDetectingProgramTag = false
                    programRfidMode = ProgramRfidMode.IDLE
                    handleProgramDetectedTagsAfterRead(
                        detected = detected,
                        emptyMessage = "No RFID tag detected. Place one tag close to the reader, press and hold the trigger, then release."
                    )
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error stopping Program tag trigger read", ex)

                runOnUiThread {
                    isDetectingProgramTag = false
                    programRfidMode = ProgramRfidMode.IDLE
                    programTagMessage = "RFID stop error: ${ex.message}"
                }
            }
        }

        return true
    }

    private fun handleProgramDetectedTagsAfterRead(
        detected: List<ProgramDetectedTagInfo>,
        emptyMessage: String
    ) {
        val candidates = detected
            .filter { it.epc.isNotBlank() }
            .distinctBy { it.epc }
            .sortedWith(
                compareByDescending<ProgramDetectedTagInfo> { programTagSignalPercent(it.rssi, it.reads) }
                    .thenByDescending { it.reads }
                    .thenByDescending { it.lastSeenAt }
                    .thenBy { it.epc }
            )

        programCandidateOptions = candidates

        when {
            candidates.isEmpty() -> {
                programSelectedTarget = null
                programDetectedTagEpc = ""
                programTidTailText = ""
                programEpcText = ""
                programTagMessage = emptyMessage
            }

            candidates.size == 1 -> {
                selectProgramCandidateForProgramming(candidates.first().epc)
            }

            else -> {
                programSelectedTarget = null
                programDetectedTagEpc = ""
                programTidTailText = ""
                programEpcText = ""
                programTagMessage = "Multiple RFID tags detected (${candidates.size}). Select the tag the operator wants to program."
            }
        }
    }

    private fun selectProgramCandidateForProgramming(epc: String) {
        val barcode = programItemText.trim()
        val cleanEpc = epc.trim().uppercase(Locale.ROOT)

        if (barcode.isBlank()) {
            programTagMessage = "Scan or enter a barcode before selecting an RFID tag."
            return
        }

        if (isProgrammingTag) {
            programTagMessage = "Wait until tag programming finishes."
            return
        }

        if (isProgramTriggerReading) {
            programTagMessage = "Release the trigger before selecting a tag."
            return
        }

        val existingCandidate = programCandidateOptions.firstOrNull {
            it.epc.equals(cleanEpc, ignoreCase = true)
        } ?: ProgramDetectedTagInfo(
            epc = cleanEpc,
            rssi = null,
            reads = 0,
            lastSeenAt = System.currentTimeMillis()
        )

        programCandidateOptions = (programCandidateOptions + existingCandidate)
            .distinctBy { it.epc.uppercase(Locale.ROOT) }
            .sortedWith(
                compareByDescending<ProgramDetectedTagInfo> { programTagSignalPercent(it.rssi, it.reads) }
                    .thenByDescending { it.reads }
                    .thenByDescending { it.lastSeenAt }
                    .thenBy { it.epc }
            )

        programSelectedTarget = null
        programDetectedTagEpc = cleanEpc
        programTidTailText = ""
        programEpcText = ""
        isDetectingProgramTag = true
        programRfidMode = ProgramRfidMode.IDLE
        programTagMessage = "Selected RFID tag. Reading TID...\n$cleanEpc"

        thread {
            try {
                val tidHex = readTidHexFromTag(cleanEpc)
                val target = buildProgramTargetFromBarcodeAndTid(
                    barcode = barcode,
                    currentEpc = cleanEpc,
                    tidHex = tidHex
                )

                runOnUiThread {
                    isDetectingProgramTag = false
                    programSelectedTarget = target
                    programDetectedTagEpc = cleanEpc
                    programTidTailText = target.tidTailHex
                    programEpcText = target.epc
                    programTagMessage =
                        """
                        RFID tag ready. EPC generated from barcode and TID.

                        Barcode: ${target.barcode}
                        Current EPC: $cleanEpc
                        TID tail: ${target.tidTailHex}
                        Generated EPC: ${target.epc}
                        """.trimIndent()
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error preparing selected Program tag", ex)

                runOnUiThread {
                    isDetectingProgramTag = false
                    programSelectedTarget = null
                    programTidTailText = ""
                    programEpcText = ""
                    programTagMessage = "Selected tag, but TID/EPC generation failed: ${ex.message}"
                }
            }
        }
    }

    private fun detectSingleProgramTag() {
        val barcode = programItemText.trim()

        if (barcode.isBlank()) {
            programTagMessage = "Scan or enter a barcode before reading RFID."
            return
        }

        if (isProgrammingTag) {
            programTagMessage = "Wait until tag programming finishes."
            return
        }

        if (isInventoryRunning) {
            programTagMessage = "Stop inventory reading before detecting a program tag."
            return
        }

        connectReaderForProgramIfNeeded {
            startProgramTagDetectionInternal()
        }
    }

    private fun connectReaderForProgramIfNeeded(afterConnected: () -> Unit) {
        val alreadyConnected = rfidReader?.isConnected == true && isReaderConnected

        if (alreadyConnected) {
            afterConnected()
            return
        }

        programTagMessage = "Connecting RFID reader..."

        thread {
            try {
                readers = Readers(this@MainActivity, ENUM_TRANSPORT.SERVICE_SERIAL)
                val availableReaders = readers?.GetAvailableRFIDReaderList()

                if (availableReaders.isNullOrEmpty()) {
                    runOnUiThread {
                        isReaderConnected = false
                        programTagMessage = "No RFID reader was found on the Zebra device."
                    }
                    return@thread
                }

                rfidReader = availableReaders[0].rfidReader

                if (rfidReader?.isConnected != true) {
                    rfidReader?.connect()
                }

                rfidReader?.Events?.addEventsListener(this@MainActivity)
                rfidReader?.Events?.setTagReadEvent(true)
                rfidReader?.Events?.setAttachTagDataWithReadEvent(false)
                rfidReader?.Events?.setHandheldEvent(true)
                rfidReader?.Events?.setReaderDisconnectEvent(true)
                rfidReader?.Events?.setInventoryStartEvent(true)
                rfidReader?.Events?.setInventoryStopEvent(true)

                runOnUiThread {
                    isReaderConnected = true
                    programTagMessage = "RFID reader ready."
                    afterConnected()
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error connecting RFID reader for program tag", ex)

                runOnUiThread {
                    isReaderConnected = false
                    programTagMessage = "RFID connection error: ${ex.message}"
                }
            }
        }
    }

    private fun startProgramTagDetectionInternal() {
        val barcode = programItemText.trim()

        clearProgramDetectedTags()

        programRfidMode = ProgramRfidMode.DETECTING
        isDetectingProgramTag = true
        programSelectedTarget = null
        programDetectedTagEpc = ""
        programTidTailText = ""
        programEpcText = ""
        programTagMessage = "Reading nearby RFID tag. Keep only one tag close to the reader."

        thread {
            try {
                try {
                    rfidReader?.Actions?.Inventory?.stop()
                } catch (_: Exception) {
                }

                useBufferedReadEvents()
                rfidReader?.Actions?.Inventory?.perform()

                Thread.sleep(1_200L)

                try {
                    rfidReader?.Actions?.Inventory?.stop()
                } catch (_: Exception) {
                }

                val detected = sortedProgramDetectedTags()

                runOnUiThread {
                    isDetectingProgramTag = false
                    programRfidMode = ProgramRfidMode.IDLE
                    handleProgramDetectedTagsAfterRead(
                        detected = detected,
                        emptyMessage = "No RFID tag detected. Place one tag close to the reader and try again."
                    )
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error detecting program tag", ex)

                runOnUiThread {
                    isDetectingProgramTag = false
                    programRfidMode = ProgramRfidMode.IDLE
                    programTagMessage = "RFID detection error: ${ex.message}"
                }
            }
        }
    }

    private fun readTidHexFromTag(currentTagEpc: String): String {
        val reader = rfidReader
            ?: throw RuntimeException("RFID reader is not initialized.")

        if (!reader.isConnected) {
            throw RuntimeException("RFID reader is not connected.")
        }

        val tagAccess = TagAccess()
        val readParams = tagAccess.ReadAccessParams()

        readParams.setMemoryBank(MEMORY_BANK.MEMORY_BANK_TID)
        readParams.setOffset(0)
        readParams.setCount(8)

        val tagData = reader.Actions.TagAccess.readWait(
            currentTagEpc,
            readParams,
            null
        )

        val tidHex = normalizeHex(tagData.memoryBankData ?: "")

        if (tidHex.isBlank()) {
            throw RuntimeException("TID could not be read from tag.")
        }

        return tidHex
    }

    private fun programDetectedTag() {
        val target = programSelectedTarget
        val currentTagEpc = programDetectedTagEpc.trim().uppercase(Locale.ROOT)
        val expectedEpc = programEpcText.trim().uppercase(Locale.ROOT)

        if (programItemText.isBlank()) {
            programTagMessage = "Scan or enter a barcode before programming."
            return
        }

        if (target == null) {
            programTagMessage = "Read one RFID tag before programming."
            return
        }

        if (currentTagEpc.isBlank()) {
            programTagMessage = "Read one RFID tag before programming."
            return
        }

        if (!isValidHexEpc(currentTagEpc)) {
            programTagMessage = "Detected tag EPC is not valid hex:\n$currentTagEpc"
            return
        }

        if (!isValidHexEpc(expectedEpc)) {
            programTagMessage = "Generated EPC is not valid hex:\n$expectedEpc"
            return
        }

        if (isProgrammingTag) {
            return
        }

        connectReaderForProgramIfNeeded {
            programTagWriteInternal(
                target = target,
                currentTagEpc = currentTagEpc,
                expectedEpc = expectedEpc
            )
        }
    }

    private fun programTagWriteInternal(
        target: ProgramTagTarget,
        currentTagEpc: String,
        expectedEpc: String
    ) {
        isProgrammingTag = true
        programTagMessage =
            """
            Programming tag...

            Barcode:
            ${target.barcode}

            Current EPC:
            $currentTagEpc

            New EPC:
            $expectedEpc
            """.trimIndent()

        thread {
            try {
                val reader = rfidReader
                    ?: throw RuntimeException("RFID reader is not initialized.")

                if (!reader.isConnected) {
                    throw RuntimeException("RFID reader is not connected.")
                }

                try {
                    reader.Actions.Inventory.stop()
                } catch (_: Exception) {
                }

                writeEpcToTag(
                    currentTagEpc = currentTagEpc,
                    newEpc = expectedEpc
                )

                runOnUiThread {
                    programTagMessage = "Write completed. Re-reading tag to verify..."
                }

                val verified = verifyProgrammedTagBlocking(expectedEpc)

                if (!verified) {
                    runOnUiThread {
                        isProgrammingTag = false
                        val readTagsText = synchronized(programDetectedEpcs) {
                            programDetectedEpcs.keys.joinToString("\n").ifBlank { "None" }
                        }

                        programTagMessage =
                            """
                            Tag write verification failed.

                            Expected:
                            $expectedEpc

                            Read tags:
                            $readTagsText
                            """.trimIndent()
                    }
                    return@thread
                }

                runOnUiThread {
                    isProgrammingTag = false
                    programDetectedTagEpc = expectedEpc
                    programTagMessage =
                        """
                        Tag programmed successfully

                        Barcode: ${target.barcode}
                        EPC: $expectedEpc
                        TID tail: ${target.tidTailHex}
                        """.trimIndent()
                }
            } catch (ex: Exception) {
                Log.e(TAG, "Error programming RFID tag", ex)

                runOnUiThread {
                    isProgrammingTag = false
                    programRfidMode = ProgramRfidMode.IDLE
                    programTagMessage = "Programming error: ${ex.message}"
                }
            }
        }
    }

    private fun writeEpcToTag(
        currentTagEpc: String,
        newEpc: String
    ) {
        val reader = rfidReader
            ?: throw RuntimeException("RFID reader is not initialized.")

        if (!reader.isConnected) {
            throw RuntimeException("RFID reader is not connected.")
        }

        val tagAccess = TagAccess()
        val writeParams = tagAccess.WriteAccessParams()

        writeParams.setMemoryBank(MEMORY_BANK.MEMORY_BANK_EPC)
        writeParams.setOffset(2)
        writeParams.setWriteData(newEpc)
        writeParams.setWriteDataLength(newEpc.length / 4)
        writeParams.setAccessPassword(0L)
        writeParams.setWriteRetries(3)

        reader.Actions.TagAccess.writeWait(
            currentTagEpc,
            writeParams,
            null,
            null,
            true,
            false
        )
    }

    private fun verifyProgrammedTagBlocking(expectedEpc: String): Boolean {
        clearProgramDetectedTags()

        programRfidMode = ProgramRfidMode.VERIFYING

        try {
            rfidReader?.Actions?.Inventory?.perform()

            Thread.sleep(1_400L)

            try {
                rfidReader?.Actions?.Inventory?.stop()
            } catch (_: Exception) {
            }

            val detected = synchronized(programDetectedEpcs) {
                programDetectedEpcs.keys.map { it.uppercase(Locale.ROOT) }.toSet()
            }

            return detected.contains(expectedEpc.uppercase(Locale.ROOT))
        } finally {
            programRfidMode = ProgramRfidMode.IDLE
        }
    }

    private fun stopProgramRfidOperations() {
        programReadSessionToken += 1
        isProgramTriggerReading = false

        try {
            if (programRfidMode != ProgramRfidMode.IDLE) {
                rfidReader?.Actions?.Inventory?.stop()
            }
        } catch (_: Exception) {
        }

        programRfidMode = ProgramRfidMode.IDLE
        isDetectingProgramTag = false
    }

    private fun clearProgramTagFlow() {
        if (isProgrammingTag || isDetectingProgramTag) {
            programTagMessage = "Wait until the current RFID operation finishes."
            return
        }

        stopProgramRfidOperations()

        programItemText = ""
        programEpcText = ""
        programSelectedTarget = null
        programDetectedTagEpc = ""
        programTidTailText = ""
        clearProgramDetectedTags()
        programTagMessage = "Scan or enter a barcode, then hold the trigger to read RFID tags."
    }

    private fun clearProgramDetectedTags() {
        synchronized(programDetectedEpcs) {
            programDetectedEpcs.clear()
        }
        programCandidateOptions = emptyList()
    }

    private fun extractGenericArray(json: JSONObject): JSONArray {
        json.optJSONArray("items")?.let { return it }
        json.optJSONArray("data")?.let { return it }
        json.optJSONArray("results")?.let { return it }

        val dataObject = json.optJSONObject("data")

        if (dataObject != null) {
            dataObject.optJSONArray("items")?.let { return it }
            dataObject.optJSONArray("data")?.let { return it }
            dataObject.optJSONArray("results")?.let { return it }
        }

        return JSONArray()
    }

    private fun normalizeItemCode(value: String): String {
        return value.trim().uppercase(Locale.ROOT)
    }

    private fun looksLikeItemCode(value: String?): Boolean {
        if (value.isNullOrBlank()) return false

        val normalized = value.trim().uppercase(Locale.ROOT)

        return Regex("^[A-Z0-9]+-[0-9A-Z]+$").matches(normalized)
    }

    private fun buildUrl(path: String): String {
        val cleanBase = serverBaseUrl.trim().trimEnd('/')
        val cleanPath = path.trimStart('/')

        return "$cleanBase/$cleanPath"
    }

    private fun httpGet(urlText: String): String {
        val connection = URL(urlText).openConnection() as HttpURLConnection

        connection.requestMethod = "GET"
        connection.connectTimeout = 10_000
        connection.readTimeout = 15_000
        connection.setRequestProperty("Accept", "application/json")

        val statusCode = connection.responseCode

        val stream = if (statusCode in 200..299) {
            connection.inputStream
        } else {
            connection.errorStream
        }

        val response = BufferedReader(InputStreamReader(stream)).use { reader ->
            reader.readText()
        }

        connection.disconnect()

        if (statusCode !in 200..299) {
            throw RuntimeException("HTTP $statusCode: $response")
        }

        return response
    }

    private fun httpPostJson(urlText: String, body: String): String {
        val connection = URL(urlText).openConnection() as HttpURLConnection

        connection.requestMethod = "POST"
        connection.connectTimeout = 10_000
        connection.readTimeout = 15_000
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "application/json")
        connection.setRequestProperty("Accept", "application/json")

        OutputStreamWriter(connection.outputStream).use { writer ->
            writer.write(body)
            writer.flush()
        }

        val statusCode = connection.responseCode

        val stream = if (statusCode in 200..299) {
            connection.inputStream
        } else {
            connection.errorStream
        }

        val response = BufferedReader(InputStreamReader(stream)).use { reader ->
            reader.readText()
        }

        connection.disconnect()

        if (statusCode !in 200..299) {
            throw RuntimeException("HTTP $statusCode: $response")
        }

        return response
    }

    override fun onDestroy() {
        super.onDestroy()

        try {
            unregisterReceiver(barcodeReceiver)
        } catch (_: Exception) {
        }

        disconnectReaderSync(updateUi = false)

        stopLocateBeepLoop()

        try {
            toneGenerator?.release()
        } catch (_: Exception) {
        } finally {
            toneGenerator = null
        }
    }
}

@Composable
fun MainMenuScreen(
    onInventoryByLocation: () -> Unit,
    onSearchItem: () -> Unit,
    onProgramTag: () -> Unit,
    onSettings: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F8FB))
    ) {
        Button(
            onClick = onSettings,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(top = 12.dp, end = 12.dp)
                .size(46.dp),
            shape = RoundedCornerShape(23.dp),
            contentPadding = PaddingValues(0.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF334155),
                contentColor = Color.White
            )
        ) {
            Image(
                painter = painterResource(id = R.drawable.ic_program_tag),
                contentDescription = "Settings",
                modifier = Modifier.size(27.dp),
                contentScale = ContentScale.Fit
            )
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(18.dp))

            Image(
                painter = painterResource(id = R.drawable.logorfid1),
                contentDescription = "Warehouse18 logo",
                modifier = Modifier
                    .fillMaxWidth(0.76f)
                    .height(140.dp),
                contentScale = ContentScale.Fit
            )

            /*Text(
                text = "Select a feature",
                color = Color(0xFF334155),
                style = MaterialTheme.typography.bodyMedium
            )*/

            Spacer(modifier = Modifier.height(5.dp))

            MenuButton(
                text = "Inventory by location",
                iconRes = R.drawable.ic_inventory,
                onClick = onInventoryByLocation,
                color = Color(0xFF0B5CAD)
            )

            MenuButton(
                text = "Search tag",
                iconRes = R.drawable.ic_locate_tag,
                onClick = onSearchItem,
                color = Color(0xFF15803D)
            )

            MenuButton(
                text = "Program tag",
                iconRes = R.drawable.ic_pencil_write,
                onClick = onProgramTag,
                color = Color(0xFF475569)
            )
        }
    }
}

@Composable
fun MenuButton(
    text: String,
    @DrawableRes iconRes: Int,
    onClick: () -> Unit,
    color: Color
) {
    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .height(64.dp),
        colors = ButtonDefaults.buttonColors(containerColor = color),
        shape = RoundedCornerShape(14.dp)
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Image(
                painter = painterResource(id = iconRes),
                contentDescription = null,
                modifier = Modifier.size(38.dp),
                contentScale = ContentScale.Fit
            )

            Spacer(modifier = Modifier.width(14.dp))

            Text(
                text = text,
                fontWeight = FontWeight.Bold,
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
        }
    }
}

@Composable
fun SettingsScreen(
    backendIp: String,
    backendPort: String,
    backendPrefix: String,
    currentBaseUrl: String,
    message: String,
    onBackendIpChange: (String) -> Unit,
    onBackendPortChange: (String) -> Unit,
    onBackendPrefixChange: (String) -> Unit,
    onOpenWifiSettings: () -> Unit,
    onTestConnection: () -> Unit,
    onSave: () -> Unit,
    onBack: () -> Unit
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = "Settings",
            color = Color(0xFF082B4A),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.headlineSmall
        )

        Text(
            text = "Network",
            color = Color(0xFF334155),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.titleMedium
        )

        Button(
            onClick = onOpenWifiSettings,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0B5CAD)),
            shape = RoundedCornerShape(14.dp)
        ) {
            Text("Open Wi-Fi settings", fontWeight = FontWeight.Bold)
        }

        Text(
            text = "Backend",
            color = Color(0xFF334155),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.titleMedium
        )

        OutlinedTextField(
            value = backendIp,
            onValueChange = onBackendIpChange,
            modifier = Modifier.fillMaxWidth(),
            textStyle = MaterialTheme.typography.bodyLarge.copy(color = Color.Black),
            label = { Text("Backend IP", color = Color.Black) },
            placeholder = { Text(DEFAULT_BACKEND_IP, color = Color(0xFF64748B)) },
            singleLine = true
        )

        OutlinedTextField(
            value = backendPort,
            onValueChange = onBackendPortChange,
            modifier = Modifier.fillMaxWidth(),
            textStyle = MaterialTheme.typography.bodyLarge.copy(color = Color.Black),
            label = { Text("Port", color = Color.Black) },
            placeholder = { Text(DEFAULT_BACKEND_PORT, color = Color(0xFF64748B)) },
            singleLine = true
        )

        OutlinedTextField(
            value = backendPrefix,
            onValueChange = onBackendPrefixChange,
            modifier = Modifier.fillMaxWidth(),
            textStyle = MaterialTheme.typography.bodyLarge.copy(color = Color.Black),
            label = { Text("API prefix", color = Color.Black) },
            placeholder = { Text(DEFAULT_BACKEND_PREFIX, color = Color(0xFF64748B)) },
            singleLine = true
        )

        Text(
            text = "Current URL: $currentBaseUrl",
            color = Color(0xFF64748B),
            style = MaterialTheme.typography.bodySmall
        )

        val previewUrl = AppSettingsStore.buildBaseUrl(
            ip = backendIp,
            port = backendPort,
            prefix = backendPrefix
        )

        Text(
            text = "Preview URL: $previewUrl",
            color = Color(0xFF64748B),
            style = MaterialTheme.typography.bodySmall
        )

        if (message.isNotBlank()) {
            Text(
                text = message,
                color = if (message.startsWith("Connection OK") || message.startsWith("Backend saved")) {
                    Color(0xFF15803D)
                } else {
                    Color(0xFFB45309)
                },
                fontWeight = FontWeight.Bold,
                style = MaterialTheme.typography.bodyMedium
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = onTestConnection,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED)),
                shape = RoundedCornerShape(14.dp)
            ) {
                Text("Test", fontWeight = FontWeight.Bold)
            }

            Button(
                onClick = onSave,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF15803D)),
                shape = RoundedCornerShape(14.dp)
            ) {
                Text("Save", fontWeight = FontWeight.Bold)
            }
        }

        Button(
            onClick = onBack,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF475569)),
            shape = RoundedCornerShape(14.dp)
        ) {
            Text("Back", fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
fun StatusMessagePanel(
    message: String,
    modifier: Modifier = Modifier
) {
    if (message.isBlank()) return

    Text(
        text = message,
        color = Color(0xFF334155),
        fontWeight = FontWeight.Bold,
        style = MaterialTheme.typography.bodyMedium ,
        modifier = modifier.fillMaxWidth()
    )
}

@Composable
fun Warehouse18Screen(
    locationNameText: String,
    onLocationNameChange: (String) -> Unit,
    selectedLocationLabel: String,
    message: String,
    isLoadingExpected: Boolean,
    isInventoryRunning: Boolean,
    isReaderConnected: Boolean,
    isSubmittingInventory: Boolean,
    rows: List<InventoryTableRow>,
    onLoadExpected: () -> Unit,
    onClearReads: () -> Unit,
    onSubmitInventory: () -> Unit
) {
    val scrollState = rememberScrollState()

    val instructionText = when {
        selectedLocationLabel.isBlank() -> {
            "Scan location barcode first. You can also type the location and press ↻."
        }

        isSubmittingInventory -> {
            "Submitting inventory result..."
        }

        isInventoryRunning -> {
            "Reading RFID. Release the trigger to stop."
        }

        isReaderConnected -> {
            "Location loaded. Press the RFID trigger to read tags."
        }

        else -> {
            "Location loaded. Connecting RFID reader..."
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(38.dp),
            contentAlignment = Alignment.CenterStart
        ) {
            Image(
                painter = painterResource(id = R.drawable.w18inventory),
                contentDescription = "W18 Inventory logo",
                modifier = Modifier
                    .width(90.dp)
                    .height(38.dp)
                    .graphicsLayer {
                        scaleX = 2.5f
                        scaleY = 2.5f
                        transformOrigin = TransformOrigin(0f, 0.5f)
                    },
                contentScale = ContentScale.Fit
            )
        }

        //Spacer(modifier = Modifier.height(2.dp))
        /*Text(
            text = "Warehouse18 RFID",
            fontWeight = FontWeight.Bold,
            color = Color(0xFF082B4A),
            style = MaterialTheme.typography.titleLarge
        )*/

        Text(
            text = instructionText,
            color = Color(0xFF334155),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold
        )

        /*Text(
            text = message,
            color = Color(0xFF334155),
            style = MaterialTheme.typography.bodyMedium
        )*/

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = locationNameText,
                onValueChange = onLocationNameChange,
                modifier = Modifier.weight(1f),
                label = { Text("Location name") },
                placeholder = { Text("Scan CN235 9C") },
                singleLine = true
            )

            Button(
                onClick = onLoadExpected,
                enabled = !isLoadingExpected && !isInventoryRunning && !isSubmittingInventory,
                modifier = Modifier.size(48.dp),
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0B5CAD))
            ) {
                Text(
                    text = if (isLoadingExpected) "…" else "↻",
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.titleLarge
                )
            }

            Button(
                onClick = onSubmitInventory,
                enabled = rows.isNotEmpty() && !isLoadingExpected && !isInventoryRunning && !isSubmittingInventory,
                modifier = Modifier.size(48.dp),
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF15803D))
            ) {
                Text(
                    text = if (isSubmittingInventory) "…" else "✓",
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.titleLarge
                )
            }

            Button(
                onClick = onClearReads,
                enabled = !isInventoryRunning && !isSubmittingInventory,
                modifier = Modifier.size(48.dp),
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF475569))
            ) {
                Text(
                    text = "✕",
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.titleLarge
                )
            }
        }

        /*if (selectedLocationLabel.isNotBlank()) {
            Text(
                text = "Selected: $selectedLocationLabel",
                color = Color(0xFF334155),
                style = MaterialTheme.typography.bodySmall
            )
        }*/

        /*Text(
            text = instructionText,
            color = Color(0xFF334155),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold
        )*/

        InventoryStats(rows = rows)

        InventoryTable(
            rows = rows,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(20.dp))
    }
}

@Composable
fun SearchItemScreen(
    itemText: String,
    onItemTextChange: (String) -> Unit,
    message: String,
    isSearching: Boolean,
    isLocating: Boolean,
    locateDistance: Int?,
    locateRssi: Int?,
    resolvedEpc: String,
    candidateEpcs: List<SearchCandidateTagInfo>,
    registeredLocationState: SearchRegisteredLocationState,
    onSearch: () -> Unit,
    onLocate: () -> Unit,
    onSelectCandidate: (String) -> Unit,
    onStopLocate: () -> Unit,
    onClear: () -> Unit,
    onBack: () -> Unit
) {
    val scrollState = rememberScrollState()

    val instructionText = when {
        isLocating -> "Locating the selected tag. Move slowly and follow the signal."
        isSearching -> "Searching nearby RFID tags..."
        resolvedEpc.isNotBlank() -> "Tag selected. Locate mode starts automatically."
        itemText.isNotBlank() -> "Barcode loaded. Find nearby tags, then tap one to locate it."
        else -> "Scan or type the item barcode first. Then search nearby tags and tap one to locate it."
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(
                start = 16.dp,
                end = 16.dp,
                top = 8.dp,
                bottom = 16.dp
            ),
        verticalArrangement = Arrangement.spacedBy(10.dp),
        horizontalAlignment = Alignment.Start
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(78.dp),
            contentAlignment = Alignment.CenterStart
        ) {
            Image(
                painter = painterResource(id = R.drawable.w18search),
                contentDescription = "W18 Search tag",
                modifier = Modifier
                    .height(68.dp)
                    .widthIn(max = 320.dp),
                contentScale = ContentScale.Fit,
                alignment = Alignment.CenterStart
            )
        }

        Text(
            text = instructionText,
            color = Color(0xFF1E293B),
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedTextField(
                value = itemText,
                onValueChange = onItemTextChange,
                modifier = Modifier
                    .weight(1f)
                    .height(70.dp),
                placeholder = { Text("Barcode / Item / Asset") },
                singleLine = true
            )

            Button(
                onClick = onClear,
                enabled = !isSearching,
                modifier = Modifier.size(64.dp),
                shape = RoundedCornerShape(50.dp),
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF4B5C6E),
                    contentColor = Color.White,
                    disabledContainerColor = Color(0xFFD7D9DD),
                    disabledContentColor = Color(0xFF8B95A1)
                )
            ) {
                Text(
                    text = "×",
                    fontWeight = FontWeight.Bold,
                    fontSize = 30.sp,
                    color = Color.White
                )
            }
        }

        if (registeredLocationState !is SearchRegisteredLocationState.Idle) {
            SearchRegisteredLocationPanel(state = registeredLocationState)
        }

        if (isLocating || locateDistance != null) {
            SignalGauge(
                proximity = locateDistance,
                rssi = locateRssi,
                isLocating = isLocating
            )
        }

        if (itemText.isNotBlank()) {
            if (isSearching || isLocating) {
                Button(
                    onClick = onStopLocate,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFB91C1C))
                ) {
                    Text(if (isSearching) "Stop search" else "Stop locate", fontWeight = FontWeight.Bold)
                }
            } else {
                Button(
                    onClick = onSearch,
                    enabled = itemText.isNotBlank(),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF1267B1),
                        contentColor = Color.White,
                        disabledContainerColor = Color(0xFFD7D9DD),
                        disabledContentColor = Color(0xFF8B95A1)
                    )
                ) {
                    Text("Find nearby tags", fontWeight = FontWeight.Bold)
                }
            }
        }

        if (candidateEpcs.isNotEmpty()) {
            CandidateEpcList(
                candidates = candidateEpcs,
                selectedEpc = resolvedEpc,
                onSelectCandidate = onSelectCandidate
            )
        }
    }
}


@Composable
fun SearchRegisteredLocationPanel(
    state: SearchRegisteredLocationState
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(14.dp))
            .border(1.dp, Color(0xFFCBD5E1), RoundedCornerShape(14.dp))
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        when (state) {
            SearchRegisteredLocationState.Idle -> {
                InlineSearchInfoRow(
                    label = "Registered location:",
                    value = "Scan barcode first",
                    valueColor = Color(0xFF64748B)
                )
            }

            SearchRegisteredLocationState.Loading -> {
                InlineSearchInfoRow(
                    label = "Registered location:",
                    value = "Checking...",
                    valueColor = Color(0xFF64748B)
                )
            }

            is SearchRegisteredLocationState.Found -> {
                InlineSearchInfoRow(
                    label = "Registered location:",
                    value = state.info.locationName.ifBlank { "Location name not returned by backend" },
                    valueColor = if (state.info.locationName.isBlank()) Color(0xFFB45309) else Color(0xFF15803D)
                )

                val formattedLastMovement = formatSearchLastMovement(state.info.lastMovementAt)
                if (formattedLastMovement.isNotBlank()) {
                    InlineSearchInfoRow(
                        label = "Last movement:",
                        value = formattedLastMovement,
                        valueColor = Color(0xFF334155)
                    )
                }
            }

            is SearchRegisteredLocationState.NotFound -> {
                InlineSearchInfoRow(
                    label = "Registered location:",
                    value = "Not found",
                    valueColor = Color(0xFFB45309)
                )
            }

            is SearchRegisteredLocationState.Error -> {
                InlineSearchInfoRow(
                    label = "Registered location:",
                    value = "Check failed",
                    valueColor = Color(0xFFB45309)
                )
                Text(
                    text = state.message,
                    color = Color(0xFF64748B),
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}

@Composable
fun InlineSearchInfoRow(
    label: String,
    value: String,
    valueColor: Color
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            color = Color(0xFF082B4A),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = value,
            color = valueColor,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold
        )
    }
}

fun formatSearchLastMovement(value: String): String {
    val clean = value.trim()
    if (clean.isBlank()) return ""

    val match = Regex("""^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?$""")
        .find(clean)

    if (match != null) {
        val year = match.groupValues[1]
        val month = match.groupValues[2]
        val day = match.groupValues[3]
        val hour = match.groupValues[4]
        val minute = match.groupValues[5]
        return "$day/$month/$year · $hour:$minute"
    }

    return clean
        .replace("T", " ")
        .substringBefore(".")
        .substringBefore("+")
        .removeSuffix("Z")
        .trim()
}


@Composable
fun SignalGauge(
    proximity: Int?,
    rssi: Int?,
    isLocating: Boolean
) {
    val value = (proximity ?: 0).coerceIn(0, 100)
    val label = proximityLabel(value, proximity != null)
    val arcColor = proximityColor(value, proximity != null)

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(14.dp))
            .border(1.dp, Color(0xFFCBD5E1), RoundedCornerShape(14.dp))
            .padding(14.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Text(
            text = "Signal proximity",
            color = Color(0xFF082B4A),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.titleMedium
        )

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(220.dp),
            contentAlignment = Alignment.Center
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val strokeWidth = 22.dp.toPx()
                val diameter = minOf(size.width, size.height) * 0.78f
                val topLeft = Offset(
                    x = (size.width - diameter) / 2f,
                    y = (size.height - diameter) / 2f
                )
                val arcSize = Size(diameter, diameter)

                drawArc(
                    color = Color(0xFFE2E8F0),
                    startAngle = 135f,
                    sweepAngle = 270f,
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                )

                drawArc(
                    color = arcColor,
                    startAngle = 135f,
                    sweepAngle = 270f * (value / 100f),
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                )
            }

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(
                    text = if (proximity == null) "--%" else "$value%",
                    color = Color(0xFF082B4A),
                    fontWeight = FontWeight.Bold,
                    fontSize = 44.sp
                )

                Text(
                    text = label,
                    color = arcColor,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.titleMedium
                )

                if (proximity == null) {
                    Text(
                        text = if (isLocating) "Waiting for signal..." else "No signal yet",
                        color = Color(0xFF64748B),
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
    }
}

private fun proximityLabel(value: Int, hasSignal: Boolean): String {
    if (!hasSignal) return "Waiting"

    return when (value) {
        in 0..20 -> "Very far"
        in 21..45 -> "Far"
        in 46..70 -> "Getting closer"
        in 71..90 -> "Close"
        else -> "Very close"
    }
}

private fun proximityColor(value: Int, hasSignal: Boolean): Color {
    if (!hasSignal) return Color(0xFF94A3B8)

    return when (value) {
        in 0..20 -> Color(0xFF64748B)
        in 21..45 -> Color(0xFF2563EB)
        in 46..70 -> Color(0xFFF59E0B)
        in 71..90 -> Color(0xFF16A34A)
        else -> Color(0xFF15803D)
    }
}

fun rssiToSearchSignalPercent(rssi: Int): Int {
    val normalized = if (rssi >= 0) {
        val minPositiveRssi = 35f
        val maxPositiveRssi = 80f
        ((rssi.toFloat() - minPositiveRssi) / (maxPositiveRssi - minPositiveRssi))
    } else {
        val minDbmRssi = -80f
        val maxDbmRssi = -35f
        ((rssi.toFloat() - minDbmRssi) / (maxDbmRssi - minDbmRssi))
    }.coerceIn(0f, 1f)

    return (java.lang.Math.pow(normalized.toDouble(), 0.85).toFloat() * 100f)
        .toInt()
        .coerceIn(0, 100)
}

@Composable
fun CandidateEpcList(
    candidates: List<SearchCandidateTagInfo>,
    selectedEpc: String,
    onSelectCandidate: (String) -> Unit
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = "Detected tag(s): ${candidates.size} · tap one to locate",
            color = Color(0xFF082B4A),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.bodyMedium
        )

        candidates.forEachIndexed { index, candidate ->
            val selected = candidate.epc.equals(selectedEpc, ignoreCase = true)
            val signal = if (candidate.rssi != null) {
                rssiToSearchSignalPercent(candidate.rssi)
            } else {
                (candidate.reads * 8).coerceIn(5, 100)
            }
            val title = when {
                selected -> "SELECTED"
                index == 0 && selectedEpc.isBlank() -> "SUGGESTED · strongest signal"
                else -> "RFID tag"
            }

            Button(
                onClick = { onSelectCandidate(candidate.epc) },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (selected) Color(0xFF1D8F3E) else Color.White,
                    contentColor = if (selected) Color.White else Color(0xFF082B4A)
                ),
                border = BorderStroke(1.dp, if (selected) Color(0xFF1D8F3E) else Color(0xFFCBD5E1)),
                contentPadding = PaddingValues(12.dp)
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.Start
                ) {
                    Text(
                        text = title,
                        fontWeight = FontWeight.Bold,
                        style = MaterialTheme.typography.bodySmall,
                        color = if (selected) Color.White else Color(0xFF334155)
                    )
                    Text(
                        text = "Signal: $signal%",
                        style = MaterialTheme.typography.bodySmall,
                        color = if (selected) Color(0xFFEAF8EE) else Color(0xFF64748B)
                    )
                    Text(
                        text = candidate.epc,
                        style = MaterialTheme.typography.bodySmall,
                        color = if (selected) Color.White else Color(0xFF334155)
                    )
                }
            }
        }
    }
}


@Composable
fun ProgramTagScreen(
    itemText: String,
    selectedTarget: ProgramTagTarget?,
    detectedTagEpc: String,
    tidTail: String,
    generatedEpc: String,
    candidateTags: List<ProgramDetectedTagInfo>,
    message: String,
    isDetectingTag: Boolean,
    isProgrammingTag: Boolean,
    onItemTextChange: (String) -> Unit,
    onDetectTag: () -> Unit,
    onSelectCandidate: (String) -> Unit,
    onProgramTag: () -> Unit,
    onClear: () -> Unit,
    onBack: () -> Unit
) {
    val scrollState = rememberScrollState()

    val canDetectTag =
        itemText.isNotBlank() &&
                !isDetectingTag &&
                !isProgrammingTag

    val canProgram =
        selectedTarget != null &&
                detectedTagEpc.isNotBlank() &&
                generatedEpc.isNotBlank() &&
                !isDetectingTag &&
                !isProgrammingTag

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(38.dp),
            contentAlignment = Alignment.CenterStart
        ) {
            Image(
                painter = painterResource(id = R.drawable.w18program),
                contentDescription = "W18 Inventory logo",
                modifier = Modifier
                    .width(90.dp)
                    .height(38.dp)
                    .graphicsLayer {
                        scaleX = 2.5f
                        scaleY = 2.5f
                        transformOrigin = TransformOrigin(0f, 0.5f)
                    },
                contentScale = ContentScale.Fit
            )
        }
        Text(
            text = "Scan or type a barcode, read one nearby RFID tag, generate the EPC from barcode + TID, then program it.",
            color = Color(0xFF334155),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold
        )

        OutlinedTextField(
            value = itemText,
            onValueChange = onItemTextChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Barcode / Item / Asset") },
            placeholder = { Text("CN235-015771") },
            singleLine = true
        )

        InfoPanel(
            title = "RFID Tag",
            value = when {
                isDetectingTag -> "Reading nearby tag..."
                detectedTagEpc.isNotBlank() -> detectedTagEpc
                candidateTags.size > 1 -> "${candidateTags.size} tags detected. Select one below."
                else -> "Waiting for tag..."
            }
        )

        InfoPanel(
            title = "Generated EPC",
            value = generatedEpc.ifBlank { "No EPC generated yet" }
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = onDetectTag,
                enabled = canDetectTag,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED))
            ) {
                if (isDetectingTag) {
                    Text(
                        text = "...",
                        fontWeight = FontWeight.Bold,
                        fontSize = 22.sp,
                        color = Color.White
                    )
                } else {
                    Icon(
                        imageVector = Icons.Filled.Search,
                        contentDescription = "Read RFID tag",
                        modifier = Modifier.size(26.dp),
                        tint = Color.White
                    )
                }
            }

            Button(
                onClick = onProgramTag,
                enabled = canProgram,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF15803D))
            ) {
                if (isProgrammingTag) {
                    Text(
                        text = "...",
                        fontWeight = FontWeight.Bold,
                        fontSize = 22.sp,
                        color = Color.White
                    )
                } else {
                    Icon(
                        imageVector = Icons.Filled.Edit,
                        contentDescription = "Program tag",
                        modifier = Modifier.size(26.dp),
                        tint = Color.White
                    )
                }
            }

            Button(
                onClick = onClear,
                enabled = !isDetectingTag && !isProgrammingTag,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF475569))
            ) {
                Text(
                    text = "✕",
                    fontWeight = FontWeight.Bold,
                    fontSize = 24.sp,
                    color = Color.White
                )
            }
        }

        Text(
            text = message,
            color = Color(0xFF334155),
            style = MaterialTheme.typography.bodyMedium
        )

        if (candidateTags.isNotEmpty()) {
            ProgramCandidateEpcList(
                candidates = candidateTags,
                selectedEpc = detectedTagEpc,
                isBusy = isDetectingTag || isProgrammingTag,
                onSelectCandidate = onSelectCandidate
            )
        }

        Spacer(modifier = Modifier.height(20.dp))
    }
}

@Composable
fun ProgramCandidateEpcList(
    candidates: List<ProgramDetectedTagInfo>,
    selectedEpc: String,
    isBusy: Boolean,
    onSelectCandidate: (String) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(10.dp))
            .border(1.dp, Color(0xFFCBD5E1), RoundedCornerShape(10.dp))
            .padding(10.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = "Detected tag(s): ${candidates.size}",
            color = Color(0xFF082B4A),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.bodyMedium
        )

        candidates.take(6).forEachIndexed { index, candidate ->
            val selected = candidate.epc.equals(selectedEpc, ignoreCase = true)
            val signal = programTagSignalPercent(candidate.rssi, candidate.reads)
            val title = when {
                selected -> "SELECTED"
                index == 0 && candidates.size > 1 -> "SUGGESTED · strongest signal"
                else -> "RFID tag"
            }

            Button(
                onClick = { onSelectCandidate(candidate.epc) },
                enabled = !isBusy,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(10.dp),
                border = BorderStroke(1.dp, if (selected) Color(0xFF15803D) else Color(0xFFCBD5E1)),
                contentPadding = PaddingValues(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (selected) Color(0xFF15803D) else Color.White,
                    contentColor = if (selected) Color.White else Color(0xFF334155),
                    disabledContainerColor = if (selected) Color(0xFF15803D) else Color(0xFFF1F5F9),
                    disabledContentColor = Color(0xFF64748B)
                )
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.Start
                ) {
                    Text(
                        text = title,
                        fontWeight = FontWeight.Bold,
                        style = MaterialTheme.typography.bodySmall
                    )
                    Text(
                        text = "Signal: $signal% · Reads: ${candidate.reads}${candidate.rssi?.let { " · RSSI: $it" }.orEmpty()}",
                        style = MaterialTheme.typography.bodySmall
                    )
                    Text(
                        text = candidate.epc,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }

        if (candidates.size > 6) {
            Text(
                text = "+${candidates.size - 6} more tag(s). Move extra tags away and read again if needed.",
                color = Color(0xFF64748B),
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

private fun programTagSignalPercent(rssi: Int?, reads: Int): Int {
    if (rssi != null) {
        if (rssi >= 0) return rssi.coerceIn(0, 100)

        val minRssi = -80
        val maxRssi = -35

        return (((rssi - minRssi).toFloat() / (maxRssi - minRssi).toFloat()) * 100f)
            .toInt()
            .coerceIn(0, 100)
    }

    return (reads * 8).coerceIn(5, 100)
}

@Composable
fun InfoPanel(
    title: String,
    value: String
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(10.dp))
            .border(1.dp, Color(0xFFCBD5E1), RoundedCornerShape(10.dp))
            .padding(10.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Text(
            text = title,
            color = Color(0xFF082B4A),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.bodyMedium
        )

        Text(
            text = value,
            color = Color(0xFF334155),
            style = MaterialTheme.typography.bodyMedium
        )
    }
}

@Composable
fun InventoryStats(rows: List<InventoryTableRow>) {
    val loadedTotal = rows.sumOf { it.qty }
    val loadedOk = rows.sumOf { row -> row.reads.coerceAtMost(row.qty) }
    val pending = (loadedTotal - loadedOk).coerceAtLeast(0)

    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        SmallStat("Loaded", loadedTotal.toString(), Color(0xFFE0F2FE), Modifier.weight(1f))
        SmallStat("Ok", loadedOk.toString(), Color(0xFFC7EFC2), Modifier.weight(1f))
        SmallStat("Pending", pending.toString(), Color(0xFFF7C7A6), Modifier.weight(1f))
    }
}

@Composable
fun SmallStat(
    label: String,
    value: String,
    background: Color,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .background(background, RoundedCornerShape(10.dp))
            .padding(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = value,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF082B4A)
        )

        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = Color(0xFF334155)
        )
    }
}

@Composable
fun InventoryTable(
    rows: List<InventoryTableRow>,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .border(1.dp, Color(0xFFCBD5E1))
            .background(Color.White)
    ) {
        InventoryHeaderRow()

        if (rows.isEmpty()) {
            Text(
                text = "No items loaded yet.",
                modifier = Modifier.padding(10.dp),
                color = Color(0xFF64748B)
            )
        } else {
            rows.forEach { row ->
                InventoryDataRow(row = row)
            }
        }
    }
}

@Composable
fun InventoryHeaderRow() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White)
            .border(0.5.dp, Color(0xFFE2E8F0))
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = "Item",
            modifier = Modifier
                .weight(1.35f)
                .padding(horizontal = 6.dp),
            fontWeight = FontWeight.Bold,
            fontSize = 13.sp,
            color = Color.Black
        )

        Text(
            text = "Qty",
            modifier = Modifier
                .weight(0.5f)
                .padding(horizontal = 6.dp),
            fontWeight = FontWeight.Bold,
            fontSize = 13.sp,
            color = Color.Black
        )

        Text(
            text = "Read",
            modifier = Modifier
                .weight(0.55f)
                .padding(horizontal = 6.dp),
            fontWeight = FontWeight.Bold,
            fontSize = 13.sp,
            color = Color.Black
        )

        Text(
            text = "Status",
            modifier = Modifier
                .weight(0.75f)
                .padding(horizontal = 6.dp),
            fontWeight = FontWeight.Bold,
            fontSize = 13.sp,
            color = Color.Black
        )
    }
}

@Composable
fun InventoryDataRow(row: InventoryTableRow) {
    val backgroundColor = when (row.status) {
        InventoryStatus.OK -> Color(0xFFBDE8B1)
        InventoryStatus.PARTIAL -> Color(0xFFFFE08A)
        InventoryStatus.EXTRA -> Color(0xFFFFA3A3)
        InventoryStatus.PENDING -> Color(0xFFF7C7A6)
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(backgroundColor)
            .border(0.5.dp, Color(0xFFE2E8F0))
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = row.itemCode,
            modifier = Modifier
                .weight(1.35f)
                .padding(horizontal = 6.dp),
            color = Color.Black,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold
        )

        Text(
            text = row.qty.toString(),
            modifier = Modifier
                .weight(0.5f)
                .padding(horizontal = 6.dp),
            color = Color.Black,
            fontSize = 13.sp
        )

        Text(
            text = if (row.reads == 0) "" else row.reads.toString(),
            modifier = Modifier
                .weight(0.55f)
                .padding(horizontal = 6.dp),
            color = Color.Black,
            fontSize = 13.sp
        )

        Text(
            text = row.status.label,
            modifier = Modifier
                .weight(0.75f)
                .padding(horizontal = 6.dp),
            color = Color.Black,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold
        )
    }
}
