package com.adrian.warehouse18mobile

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.graphics.drawable.GradientDrawable
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings as AndroidSettings
import android.text.Editable
import android.text.InputType
import android.text.TextWatcher
import android.view.Gravity
import android.view.KeyEvent
import android.view.inputmethod.InputMethodManager
import android.widget.EditText
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.Locale
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.BackHandler
import androidx.activity.OnBackPressedCallback
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.concurrent.thread
import com.adrian.warehouse18mobile.rfid.Warehouse18Epc

private val W18Background = Color(0xFF06101D)
private val W18Panel = Color(0xFF0B1728)
private val W18PanelSoft = Color(0xFF101F35)
private val W18Blue = Color(0xFF0B67D1)
private val W18BlueDark = Color(0xFF063B78)
private val W18Text = Color(0xFFEAF2FF)
private val W18MutedText = Color(0xFFA9BAD3)
private val W18Border = Color(0xFF204B78)

private const val DEFAULT_BACKEND_IP = "192.168.1.172"
private const val DEFAULT_BACKEND_PORT = "8000"
private const val DEFAULT_BACKEND_PREFIX = ""
private const val BACKEND_BASE_URL = "http://192.168.1.172:8000"

private data class BackendConfig(
    val ip: String,
    val port: String,
    val prefix: String
) {
    val baseUrl: String
        get() = AppSettingsStore.buildBaseUrl(ip, port, prefix)
}

private object AppSettingsStore {
    private const val PREFS_NAME = "warehouse18_chafon_settings"
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
        val rawHost = ip.trim()
            .removePrefix("http://")
            .removePrefix("https://")
            .substringBefore("/")
            .ifBlank { DEFAULT_BACKEND_IP }

        val cleanIp = rawHost.substringBefore(":").ifBlank { DEFAULT_BACKEND_IP }
        val embeddedPort = rawHost.substringAfter(":", "")
        val cleanPort = port.trim()
            .ifBlank { embeddedPort }
            .ifBlank { DEFAULT_BACKEND_PORT }

        val cleanPrefix = normalizePrefix(prefix)

        return "http://$cleanIp:$cleanPort$cleanPrefix"
    }

    private fun normalizePrefix(prefix: String): String {
        val clean = prefix.trim().trim('/')

        if (clean.isBlank()) {
            return ""
        }

        val withoutApiSuffix = if (clean.equals("api", ignoreCase = true)) {
            ""
        } else if (clean.endsWith("/api", ignoreCase = true)) {
            clean.substringBeforeLast("/api")
        } else {
            clean
        }

        return if (withoutApiSuffix.isBlank()) {
            ""
        } else {
            "/${withoutApiSuffix.trim('/')}"
        }
    }
}

private data class RfidInventoryTag(
    val epc: String,
    val rssi: Int?,
    val decodedObjectCode: String,
    val reads: Int
)

private data class LocateCandidate(
    val epc: String,
    val decodedObjectCode: String,
    val rssi: Int?,
    val reads: Int,
    val lastSeenAt: Long
)

private data class LocateRegisteredLocationInfo(
    val objectType: String,
    val displayCode: String,
    val itemCode: String,
    val epc: String,
    val locationId: Int?,
    val locationCode: String,
    val locationName: String,
    val locationLabel: String,
    val lastMovementAt: String,
    val objectId: Int? = null
)

private sealed class LocateRegisteredLocationState {
    object Idle : LocateRegisteredLocationState()
    object Loading : LocateRegisteredLocationState()
    data class Found(val info: LocateRegisteredLocationInfo) : LocateRegisteredLocationState()
    data class NotFound(val barcode: String) : LocateRegisteredLocationState()
    data class Error(val message: String) : LocateRegisteredLocationState()
}

private sealed class LocateRegisteredLocationResult {
    data class Success(val info: LocateRegisteredLocationInfo) : LocateRegisteredLocationResult()
    object NotFound : LocateRegisteredLocationResult()
    data class Failure(val message: String) : LocateRegisteredLocationResult()
}

private data class ProgramDetectedTag(
    val epc: String,
    val rssi: Int?,
    val reads: Int,
    val lastSeenAt: Long
)

private data class RfidScanValidation(
    val epc: String,
    val status: String,
    val validation: String,
    val severity: String,
    val message: String,
    val objectType: String,
    val assetId: Int? = null,
    val containerId: Int? = null,
    val itemId: Int? = null,
    val resolvedKey: String = "",
    val assetCode: String = "",
    val containerCode: String = "",
    val itemCode: String = "",
    val displayCode: String = ""
)

private sealed class RfidScanValidationResult {
    data class Success(val validation: RfidScanValidation) : RfidScanValidationResult()
    data class Failure(val message: String) : RfidScanValidationResult()
}

private data class LocationInfo(
    val id: Int,
    val code: String,
    val name: String,
    val type: String,
    val isActive: Boolean
)

private data class ExpectedAssetInfo(
    val id: Int,
    val objectType: String,
    val displayCode: String,
    val assetCode: String,
    val containerCode: String,
    val itemId: Int,
    val itemCode: String,
    val itemName: String,
    val serialNumber: String,
    val status: String,
    val epc: String,
    val quantity: Double? = null
)

private data class InventoryGroupedRow(
    val itemCode: String,
    val itemName: String,
    val qty: Double,
    val read: Double,
    val status: String
)

private sealed class ExpectedAssetsState {
    object Idle : ExpectedAssetsState()
    object Loading : ExpectedAssetsState()
    data class Loaded(val assets: List<ExpectedAssetInfo>) : ExpectedAssetsState()
    object Empty : ExpectedAssetsState()
    data class Error(val message: String) : ExpectedAssetsState()
}

private sealed class ExpectedAssetsLookupResult {
    data class Success(val assets: List<ExpectedAssetInfo>) : ExpectedAssetsLookupResult()
    data class Failure(val message: String) : ExpectedAssetsLookupResult()
}

private sealed class InventorySubmitState {
    object Idle : InventorySubmitState()
    object Submitting : InventorySubmitState()
    data class Submitted(val message: String) : InventorySubmitState()
    data class Error(val message: String) : InventorySubmitState()
}

private sealed class InventorySubmitResult {
    data class Success(val message: String) : InventorySubmitResult()
    data class Failure(val message: String) : InventorySubmitResult()
}

private sealed class InventoryLookupState {
    object Idle : InventoryLookupState()
    object Loading : InventoryLookupState()
    data class Found(val location: LocationInfo) : InventoryLookupState()
    data class NotFound(val barcode: String) : InventoryLookupState()
    data class Error(val message: String) : InventoryLookupState()
}

private sealed class LocationLookupResult {
    data class Success(val location: LocationInfo) : LocationLookupResult()
    object NotFound : LocationLookupResult()
    data class Failure(val message: String) : LocationLookupResult()
}

private val locateProximitySamples = mutableListOf<Int>()
private var smoothedLocateProximity: Float? = null

class MainActivity : ComponentActivity() {

    private var selectedMenuOption by mutableStateOf<MenuOption?>(null)
    private var showSettings by mutableStateOf(false)

    private var settingsBackendIp by mutableStateOf(DEFAULT_BACKEND_IP)
    private var settingsBackendPort by mutableStateOf(DEFAULT_BACKEND_PORT)
    private var settingsBackendPrefix by mutableStateOf(DEFAULT_BACKEND_PREFIX)
    private var settingsMessage by mutableStateOf("")

    private var capturedBarcode by mutableStateOf("")
    private var barcodeCaptured by mutableStateOf(false)
    private var statusText by mutableStateOf("Select an operation from the menu")
    private var resetBarcodeCounter by mutableIntStateOf(0)
    private var inventoryLookupState by mutableStateOf<InventoryLookupState>(InventoryLookupState.Idle)
    private var expectedAssetsState by mutableStateOf<ExpectedAssetsState>(ExpectedAssetsState.Idle)
    private var rfidTagsRead by mutableStateOf<List<RfidInventoryTag>>(emptyList())
    private var rfidScanValidations by mutableStateOf<Map<String, RfidScanValidation>>(emptyMap())
    private var rfidStatusText by mutableStateOf("RFID inventory not started.")
    private var rfidRunning by mutableStateOf(false)
    private var rfidConnecting by mutableStateOf(false)
    private var rfidInventorySessionToken = 0
    private var inventorySubmitState by mutableStateOf<InventorySubmitState>(InventorySubmitState.Idle)

    private var locateStatusText by mutableStateOf("Scan item barcode first.")
    private var locateExpectedPrefix by mutableStateOf("")
    private var locateTargetEpc by mutableStateOf("")
    private var locateCandidates by mutableStateOf<List<LocateCandidate>>(emptyList())
    private var locateSearching by mutableStateOf(false)
    private var locateRunning by mutableStateOf(false)
    private var locateConnecting by mutableStateOf(false)
    private var locateProximity by mutableStateOf<Int?>(null)
    private var locateRssi by mutableStateOf<Int?>(null)
    private var locateTargetReads by mutableIntStateOf(0)
    private var locateRegisteredLocationState by mutableStateOf<LocateRegisteredLocationState>(LocateRegisteredLocationState.Idle)
    private var pendingAutoLocateSearchToken = 0
    private var locateSearchSessionToken = 0

    private var programStatusText by mutableStateOf("Scan barcode first, then read one RFID tag.")
    private var programDetectedTags by mutableStateOf<List<ProgramDetectedTag>>(emptyList())
    private var programDetectedEpc by mutableStateOf("")
    private var programDetectedRssi by mutableStateOf<Int?>(null)
    private var programTidHex by mutableStateOf("")
    private var programTidTail by mutableStateOf("")
    private var programGeneratedEpc by mutableStateOf("")
    private var programReadingTag by mutableStateOf(false)
    private var programConnecting by mutableStateOf(false)
    private var programWritingTag by mutableStateOf(false)
    private var programConfirmingWrite by mutableStateOf(false)
    private var programTagProgrammed by mutableStateOf(false)
    private var programReadSessionToken = 0

    @Volatile
    private var locateBeepLoopRunning = false

    @Volatile
    private var latestLocateProximity = 0

    @Volatile
    private var latestLocateSeenAtMs = 0L

    private var locateBeepThread: Thread? = null
    private var toneGenerator: ToneGenerator? = null

    private val rfidController: RfidController by lazy { ChafonRfidController(this) }

    private fun stopLocateFromTriggerIfRunning(): Boolean {
        if (selectedMenuOption != MenuOption.LocateItem) {
            return false
        }

        if (!locateRunning && !locateSearching && !locateConnecting) {
            return false
        }

        locateSearchSessionToken += 1
        locateStatusText = "Stopping RFID search..."
        stopLocate()
        return true
    }

    private fun startInventoryFromTriggerIfReady(): Boolean {
        if (selectedMenuOption != MenuOption.InventoryByLocation) {
            return false
        }

        val locationLoaded = inventoryLookupState is InventoryLookupState.Found
        val expectedLoaded = expectedAssetsState is ExpectedAssetsState.Loaded
        val submitBusy = inventorySubmitState is InventorySubmitState.Submitting ||
                inventorySubmitState is InventorySubmitState.Submitted

        if (!barcodeCaptured) {
            statusText = "Trigger detected. Scan location barcode first."
            return true
        }

        if (!locationLoaded || !expectedLoaded) {
            statusText = "Trigger detected, but location is not fully loaded yet."
            return true
        }

        if (submitBusy) {
            statusText = "Trigger ignored. Inventory is already submitted or submitting."
            return true
        }

        if (rfidRunning || rfidConnecting) {
            rfidStatusText = "RFID inventory is already running."
            return true
        }

        startRfidInventoryForCurrentLocation()
        return true
    }

    private fun stopInventoryFromTriggerIfRunning(): Boolean {
        if (selectedMenuOption != MenuOption.InventoryByLocation) {
            return false
        }

        if (!rfidRunning && !rfidConnecting) {
            return true
        }

        stopRfidInventory()
        return true
    }

    private fun startProgramTagReadFromTriggerIfReady(): Boolean {
        if (selectedMenuOption != MenuOption.ProgramTag) {
            return false
        }

        val barcode = capturedBarcode.trim().uppercase(Locale.ROOT)

        if (!barcodeCaptured || barcode.isBlank()) {
            programStatusText = "Trigger detected. Scan barcode before reading RFID."
            return true
        }

        if (programWritingTag) {
            programStatusText = "Trigger ignored. Wait until tag programming finishes."
            return true
        }

        if (programTagProgrammed) {
            programStatusText = "This tag is already marked as programmed. Press ✕ to start another tag."
            return true
        }

        if (programReadingTag || programConnecting) {
            programStatusText = "RFID tag read is already running. Release trigger to stop."
            return true
        }

        val sessionToken = ++programReadSessionToken

        programDetectedTags = emptyList()
        programDetectedEpc = ""
        programDetectedRssi = null
        programTidHex = ""
        programTidTail = ""
        programGeneratedEpc = ""
        programWritingTag = false
        programConfirmingWrite = false
        programTagProgrammed = false
        programReadingTag = true
        programConnecting = true
        programStatusText = "Connecting Chafon RFID reader. Keep only one tag close to the antenna."

        lifecycleScope.launch {
            val errorMessage = withContext(Dispatchers.IO) {
                try {
                    if (!rfidController.isConnected) {
                        rfidController.connect()
                    }

                    rfidController.startInventory()
                    null
                } catch (exception: Exception) {
                    runCatching { rfidController.stopInventory() }
                    exception.message ?: "Unknown RFID read error."
                }
            }

            if (sessionToken != programReadSessionToken || selectedMenuOption != MenuOption.ProgramTag) {
                withContext(Dispatchers.IO) {
                    runCatching { rfidController.stopInventory() }
                }
                programConnecting = false
                programReadingTag = false
                return@launch
            }

            programConnecting = false

            if (errorMessage != null) {
                programReadingTag = false
                programStatusText = "RFID read error: $errorMessage"
                return@launch
            }

            programReadingTag = true
            programStatusText = "Reading RFID tag. Release the trigger to stop."
        }

        return true
    }

    private fun stopProgramTagReadFromTriggerIfRunning(): Boolean {
        if (selectedMenuOption != MenuOption.ProgramTag) {
            return false
        }

        if (!programReadingTag && !programConnecting) {
            return true
        }

        val stopToken = ++programReadSessionToken

        programConnecting = false
        programReadingTag = false

        lifecycleScope.launch {
            withContext(Dispatchers.IO) {
                runCatching { rfidController.stopInventory() }
            }

            if (stopToken != programReadSessionToken || selectedMenuOption != MenuOption.ProgramTag) {
                return@launch
            }

            val tags = sortProgramDetectedTags(programDetectedTags)
            programDetectedTags = tags

            when {
                tags.isEmpty() -> {
                    programStatusText = "No RFID tag detected. Place one tag close to the reader and try again."
                }

                tags.size > 1 -> {
                    val suggested = tags.first()
                    programStatusText = "Multiple RFID tags detected (${tags.size}). Select the tag to program. Suggested: strongest signal ${suggested.epc}."
                }

                else -> {
                    val tag = tags.first()
                    selectProgramDetectedTagForProgramming(tag.epc)
                }
            }
        }

        return true
    }

    private fun goBackToMainMenuOrExit() {
        if (showSettings) {
            loadSettingsFromStore()
            showSettings = false
            selectedMenuOption = null
            return
        }

        if (selectedMenuOption == null) {
            finish()
            return
        }

        resetBarcodeState(null)
        selectedMenuOption = null
    }

    private fun loadSettingsFromStore() {
        val config = AppSettingsStore.load(this)

        settingsBackendIp = config.ip
        settingsBackendPort = config.port
        settingsBackendPrefix = config.prefix

        Warehouse18Api.setBaseUrl(config.baseUrl)
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

        Warehouse18Api.setBaseUrl(newBaseUrl)
        settingsMessage = "Backend saved and active: ${Warehouse18Api.getBaseUrl()}"
    }

    private fun openWifiSettingsFromApp() {
        try {
            startActivity(Intent(AndroidSettings.ACTION_WIFI_SETTINGS))
            settingsMessage = "Opening Wi-Fi settings..."
        } catch (exception: Exception) {
            settingsMessage = "Could not open Wi-Fi settings: ${exception.message}"
        }
    }

    private fun testBackendConnectionFromSettings() {
        val testBaseUrl = AppSettingsStore.buildBaseUrl(
            ip = settingsBackendIp,
            port = settingsBackendPort,
            prefix = settingsBackendPrefix
        )

        settingsMessage = "Testing backend: $testBaseUrl"

        lifecycleScope.launch {
            val testSucceeded = withContext(Dispatchers.IO) {
                runCatching {
                    Warehouse18Api.testConnection(testBaseUrl)
                }.isSuccess
            }

            if (testSucceeded) {
                Warehouse18Api.setBaseUrl(testBaseUrl)
                settingsMessage = "Connection OK. Backend active for this session: ${Warehouse18Api.getBaseUrl()}"
            } else {
                val errorMessage = withContext(Dispatchers.IO) {
                    runCatching {
                        Warehouse18Api.testConnection(testBaseUrl)
                    }.exceptionOrNull()?.message ?: "Unknown backend error"
                }
                settingsMessage = "Connection failed: $errorMessage"
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        loadSettingsFromStore()
        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    goBackToMainMenuOrExit()
                }
            }
        )
        rfidController.setListener(object : RfidController.Listener {
            override fun onTagRead(tag: RfidTag) {
                runOnUiThread { handleRfidTagRead(tag) }
            }

            override fun onTriggerPressed() {
                runOnUiThread {
                    if (!startProgramTagReadFromTriggerIfReady()) {
                        startInventoryFromTriggerIfReady()
                    }
                }
            }

            override fun onTriggerReleased() {
                runOnUiThread {
                    if (!stopProgramTagReadFromTriggerIfRunning()) {
                        stopInventoryFromTriggerIfRunning()
                    }
                }
            }
        })

        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = W18Blue,
                    secondary = W18BlueDark,
                    background = W18Background,
                    surface = W18Panel,
                    onPrimary = Color.White,
                    onSecondary = Color.White,
                    onBackground = W18Text,
                    onSurface = W18Text
                )
            ) {
                val currentOption = selectedMenuOption

                BackHandler(enabled = currentOption != null || showSettings) {
                    goBackToMainMenuOrExit()
                }

                if (showSettings) {
                    SettingsScreen(
                        backendIp = settingsBackendIp,
                        backendPort = settingsBackendPort,
                        backendPrefix = settingsBackendPrefix,
                        currentBaseUrl = Warehouse18Api.getBaseUrl(),
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
                        onBack = { goBackToMainMenuOrExit() }
                    )
                } else if (currentOption == null) {
                    MainMenuScreen(
                        onOptionSelected = { option ->
                            selectedMenuOption = option
                            resetBarcodeState(option)
                        },
                        onSettingsSelected = {
                            settingsMessage = ""
                            showSettings = true
                            selectedMenuOption = null
                        }
                    )
                } else {
                    ChafonBarcodeReaderScreen(
                        menuOption = currentOption,
                        capturedBarcode = capturedBarcode,
                        barcodeCaptured = barcodeCaptured,
                        statusText = statusText,
                        resetCounter = resetBarcodeCounter,
                        inventoryLookupState = inventoryLookupState,
                        expectedAssetsState = expectedAssetsState,
                        rfidTagsRead = rfidTagsRead,
                        rfidScanValidations = rfidScanValidations,
                        rfidStatusText = rfidStatusText,
                        rfidRunning = rfidRunning,
                        rfidConnecting = rfidConnecting,
                        inventorySubmitState = inventorySubmitState,
                        locateStatusText = locateStatusText,
                        locateExpectedPrefix = locateExpectedPrefix,
                        locateTargetEpc = locateTargetEpc,
                        locateCandidates = locateCandidates,
                        locateSearching = locateSearching,
                        locateRunning = locateRunning,
                        locateConnecting = locateConnecting,
                        locateProximity = locateProximity,
                        locateRssi = locateRssi,
                        locateTargetReads = locateTargetReads,
                        locateRegisteredLocationState = locateRegisteredLocationState,
                        programStatusText = programStatusText,
                        programDetectedTags = programDetectedTags,
                        programDetectedEpc = programDetectedEpc,
                        programDetectedRssi = programDetectedRssi,
                        programTidHex = programTidHex,
                        programTidTail = programTidTail,
                        programGeneratedEpc = programGeneratedEpc,
                        programReadingTag = programReadingTag,
                        programConnecting = programConnecting,
                        programWritingTag = programWritingTag,
                        programConfirmingWrite = programConfirmingWrite,
                        programTagProgrammed = programTagProgrammed,
                        onStartProgramTagRead = {
                            readSingleProgramTagForCurrentBarcode()
                        },
                        onSelectProgramDetectedTag = { epc ->
                            selectProgramDetectedTagForProgramming(epc)
                        },
                        onProgramTagWrite = {
                            writeGeneratedProgramTag()
                        },
                        onStartLocateSearch = {
                            startLocateSearch()
                        },
                        onStartLocateCandidate = { epc ->
                            startLocateSelectedTag(epc)
                        },
                        onStopLocate = {
                            stopLocate()
                        },
                        onStartRfidInventory = {
                            startRfidInventoryForCurrentLocation()
                        },
                        onStopRfidInventory = {
                            stopRfidInventory()
                        },
                        onSubmitInventoryResult = {
                            submitInventoryResultForCurrentLocation()
                        },
                        onNewInventory = {
                            resetBarcodeState(currentOption)
                        },
                        onReloadInventoryLocation = {
                            if (capturedBarcode.isNotBlank()) {
                                lookupInventoryLocation(capturedBarcode)
                            }
                        },
                        onTriggerDetected = {
                            val handledByLocateTrigger = stopLocateFromTriggerIfRunning()
                            val handledByProgramTrigger = if (handledByLocateTrigger) {
                                true
                            } else {
                                startProgramTagReadFromTriggerIfReady()
                            }
                            val handledByInventoryTrigger = if (handledByProgramTrigger) {
                                true
                            } else {
                                startInventoryFromTriggerIfReady()
                            }

                            if (!handledByInventoryTrigger) {
                                statusText = if (barcodeCaptured) {
                                    currentOption.extraReadsIgnoredStatus
                                } else {
                                    currentOption.waitingStatus
                                }
                            }
                        },
                        onTriggerReleased = {
                            if (!stopLocateFromTriggerIfRunning()) {
                                if (!stopProgramTagReadFromTriggerIfRunning()) {
                                    stopInventoryFromTriggerIfRunning()
                                }
                            }
                        },
                        onBarcodeCaptured = { barcode ->
                            if (!barcodeCaptured) {
                                capturedBarcode = barcode
                                barcodeCaptured = true
                                statusText = currentOption.capturedStatus

                                when (currentOption) {
                                    MenuOption.InventoryByLocation -> lookupInventoryLocation(barcode)
                                    MenuOption.LocateItem -> handleLocateBarcodeCaptured(barcode)
                                    MenuOption.ProgramTag -> handleProgramBarcodeCaptured(barcode)
                                }
                            }
                        },
                        onClearBarcode = {
                            resetBarcodeState(currentOption)
                        },
                        onBackToMenu = {
                            goBackToMainMenuOrExit()
                        }
                    )
                }
            }
        }
    }

    private fun resetBarcodeState(option: MenuOption?) {
        capturedBarcode = ""
        barcodeCaptured = false
        statusText = option?.idleStatus ?: "Select an operation from the menu"
        inventoryLookupState = InventoryLookupState.Idle
        expectedAssetsState = ExpectedAssetsState.Idle
        rfidTagsRead = emptyList()
        rfidScanValidations = emptyMap()
        rfidStatusText = "RFID inventory not started."
        inventorySubmitState = InventorySubmitState.Idle
        resetLocateState(stopRfid = true)
        resetProgramTagState(stopRfid = true)
        stopRfidInventory(silent = true)
        resetBarcodeCounter += 1
    }

    private fun resetLocateState(stopRfid: Boolean = true) {
        pendingAutoLocateSearchToken += 1
        locateSearchSessionToken += 1
        locateStatusText = "Scan item barcode first."
        locateExpectedPrefix = ""
        locateTargetEpc = ""
        locateCandidates = emptyList()
        locateSearching = false
        locateRunning = false
        locateConnecting = false
        locateProximity = null
        locateRssi = null
        locateTargetReads = 0
        locateRegisteredLocationState = LocateRegisteredLocationState.Idle
        stopLocateBeepLoop()
        latestLocateProximity = 0
        latestLocateSeenAtMs = 0L
        locateProximitySamples.clear()
        smoothedLocateProximity = null

        if (stopRfid) {
            lifecycleScope.launch {
                withContext(Dispatchers.IO) {
                    runCatching { rfidController.stopInventory() }
                }
            }
        }
    }

    private fun resetProgramTagState(stopRfid: Boolean = true) {
        programReadSessionToken += 1
        programStatusText = "Scan barcode first, then read one RFID tag."
        programDetectedTags = emptyList()
        programDetectedEpc = ""
        programDetectedRssi = null
        programTidHex = ""
        programTidTail = ""
        programGeneratedEpc = ""
        programReadingTag = false
        programConnecting = false
        programWritingTag = false
        programConfirmingWrite = false
        programTagProgrammed = false

        if (stopRfid) {
            lifecycleScope.launch {
                withContext(Dispatchers.IO) {
                    runCatching { rfidController.stopInventory() }
                }
            }
        }
    }

    private fun lookupInventoryLocation(locationBarcode: String) {
        inventoryLookupState = InventoryLookupState.Loading
        expectedAssetsState = ExpectedAssetsState.Idle
        rfidTagsRead = emptyList()
        rfidScanValidations = emptyMap()
        rfidStatusText = "RFID inventory not started."
        inventorySubmitState = InventorySubmitState.Idle
        stopRfidInventory(silent = true)
        statusText = "Loading location from backend..."

        lifecycleScope.launch {
            val locationResult = withContext(Dispatchers.IO) {
                Warehouse18Api.findLocationByName(locationBarcode)
            }

            when (locationResult) {
                is LocationLookupResult.Success -> {
                    val location = locationResult.location

                    inventoryLookupState = InventoryLookupState.Found(location)
                    expectedAssetsState = ExpectedAssetsState.Loading
                    statusText = "Location found. Loading expected items..."

                    val assetsResult = withContext(Dispatchers.IO) {
                        Warehouse18Api.findExpectedAssetsByLocation(location.id)
                    }

                    when (assetsResult) {
                        is ExpectedAssetsLookupResult.Success -> {
                            val assets = assetsResult.assets

                            expectedAssetsState = if (assets.isEmpty()) {
                                ExpectedAssetsState.Empty
                            } else {
                                ExpectedAssetsState.Loaded(assets)
                            }

                            statusText = if (assets.isEmpty()) {
                                "Location found. No expected items in this location."
                            } else {
                                "Expected items loaded for this location."
                            }
                        }

                        is ExpectedAssetsLookupResult.Failure -> {
                            expectedAssetsState = ExpectedAssetsState.Error(assetsResult.message)
                            statusText = "Location found, but expected items could not be loaded."
                        }
                    }
                }

                LocationLookupResult.NotFound -> {
                    inventoryLookupState = InventoryLookupState.NotFound(locationBarcode)
                    expectedAssetsState = ExpectedAssetsState.Idle
                    statusText = "Location not found in backend."
                }

                is LocationLookupResult.Failure -> {
                    inventoryLookupState = InventoryLookupState.Error(locationResult.message)
                    expectedAssetsState = ExpectedAssetsState.Idle
                    statusText = "Backend error while loading location."
                }
            }
        }
    }

    private fun startRfidInventoryForCurrentLocation() {
        val loadedAssets = (expectedAssetsState as? ExpectedAssetsState.Loaded)?.assets.orEmpty()

        if (loadedAssets.isEmpty()) {
            rfidStatusText = "Load expected items before starting RFID inventory."
            return
        }

        if (rfidRunning || rfidConnecting) return

        val sessionToken = ++rfidInventorySessionToken
        rfidConnecting = true
        rfidStatusText = "Connecting Chafon RFID reader..."

        lifecycleScope.launch {
            val errorMessage = withContext(Dispatchers.IO) {
                try {
                    if (!rfidController.isConnected) {
                        rfidController.connect()
                    }
                    rfidController.startInventory()
                    null
                } catch (exception: Exception) {
                    exception.message ?: "Unknown RFID error."
                }
            }

            if (sessionToken != rfidInventorySessionToken || selectedMenuOption != MenuOption.InventoryByLocation) {
                withContext(Dispatchers.IO) {
                    runCatching { rfidController.stopInventory() }
                }
                rfidConnecting = false
                rfidRunning = false
                rfidStatusText = "RFID inventory stopped."
                return@launch
            }

            rfidConnecting = false

            if (errorMessage == null) {
                rfidRunning = true
                rfidStatusText = "RFID inventory running. Move the reader slowly around the location."
            } else {
                rfidRunning = false
                rfidStatusText = "RFID error: $errorMessage"
            }
        }
    }

    private fun stopRfidInventory(silent: Boolean = false) {
        rfidInventorySessionToken += 1

        val wasRunningOrConnecting = rfidRunning || rfidConnecting
        rfidRunning = false
        rfidConnecting = false

        lifecycleScope.launch {
            withContext(Dispatchers.IO) {
                runCatching { rfidController.stopInventory() }
            }

            if (!silent) {
                rfidStatusText = if (wasRunningOrConnecting) {
                    "RFID inventory stopped. ${rfidTagsRead.size} unique tag${if (rfidTagsRead.size == 1) "" else "s"} read."
                } else {
                    "RFID inventory is not running."
                }
            }
        }
    }

    private fun handleRfidTagRead(tag: RfidTag) {
        val epc = normalizeRfidKey(tag.epc)
        if (epc.isBlank()) return

        val decodedObjectCode = when (val decoded = Warehouse18Epc.decode(epc)) {
            is Warehouse18Epc.DecodeResult.Valid -> decoded.objectCode
            else -> ""
        }

        if (selectedMenuOption == MenuOption.LocateItem) {
            handleLocateRfidTagRead(
                epc = epc,
                decodedObjectCode = decodedObjectCode,
                rssi = tag.rssi
            )
            return
        }

        if (selectedMenuOption == MenuOption.ProgramTag) {
            handleProgramRfidTagRead(
                epc = epc,
                rssi = tag.rssi
            )
            return
        }

        val existing = rfidTagsRead.firstOrNull { it.epc == epc }

        rfidTagsRead = if (existing == null) {
            rfidTagsRead + RfidInventoryTag(
                epc = epc,
                rssi = tag.rssi,
                decodedObjectCode = decodedObjectCode,
                reads = 1
            )
        } else {
            rfidTagsRead.map { current ->
                if (current.epc == epc) {
                    current.copy(
                        rssi = tag.rssi ?: current.rssi,
                        decodedObjectCode = current.decodedObjectCode.ifBlank { decodedObjectCode },
                        reads = current.reads + 1
                    )
                } else {
                    current
                }
            }
        }

        val location = (inventoryLookupState as? InventoryLookupState.Found)?.location
        if (location != null && !rfidScanValidations.containsKey(epc)) {
            rfidScanValidations = rfidScanValidations + (epc to RfidScanValidation(
                epc = epc,
                status = "loading",
                validation = "validating",
                severity = "info",
                message = "Validating tag with Warehouse18...",
                objectType = ""
            ))
            validateRfidScanWithBackend(location.id, epc)
        }

        val loadedAssets = (expectedAssetsState as? ExpectedAssetsState.Loaded)?.assets.orEmpty()
        val foundCount = loadedAssets.count { expected ->
            rfidScanValidations.values.any { validation -> expectedItemMatchesValidation(expected, validation) }
        }

        rfidStatusText = "Last RFID tag read. Found $foundCount/${loadedAssets.size}. Unique tags: ${rfidTagsRead.size}."
        inventorySubmitState = InventorySubmitState.Idle
    }

    private fun validateRfidScanWithBackend(locationId: Int, epc: String) {
        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                Warehouse18Api.validateHandheldScanForLocation(
                    locationId = locationId,
                    epc = epc
                )
            }

            if ((inventoryLookupState as? InventoryLookupState.Found)?.location?.id != locationId) {
                return@launch
            }

            when (result) {
                is RfidScanValidationResult.Success -> {
                    rfidScanValidations = rfidScanValidations + (epc to result.validation)

                    val loadedItems = (expectedAssetsState as? ExpectedAssetsState.Loaded)?.assets.orEmpty()
                    val foundCount = loadedItems.count { expected ->
                        rfidScanValidations.values.any { validation -> expectedItemMatchesValidation(expected, validation) }
                    }
                    val issueCount = rfidScanValidations.values.count { validation ->
                        validation.severity.equals("warning", ignoreCase = true) ||
                                validation.severity.equals("error", ignoreCase = true)
                    }

                    rfidStatusText = "Backend validated RFID tag. Found $foundCount/${loadedItems.size}. Issues: $issueCount."
                }

                is RfidScanValidationResult.Failure -> {
                    rfidScanValidations = rfidScanValidations + (epc to RfidScanValidation(
                        epc = epc,
                        status = "error",
                        validation = "validation_failed",
                        severity = "error",
                        message = result.message,
                        objectType = ""
                    ))
                    rfidStatusText = "RFID backend validation failed: ${result.message}"
                }
            }
        }
    }

    private fun handleLocateBarcodeCaptured(barcode: String) {
        prepareLocateItem(barcode)
        lookupRegisteredLocationForLocate(barcode)

        val clean = barcode.trim().uppercase(Locale.ROOT)
        if (clean.isBlank()) return

        val normalizedHex = normalizeRfidKey(clean)

        // Zebra starts the RFID search immediately after a barcode scan.
        // Chafon needs a short pause because the scan wedge / trigger path can still be releasing
        // the hardware when the text reaches this EditText. Without the pause, Connect() can fail
        // on /dev/ttyHSL0 even though the same reader works a moment later. Tiny timing goblin.
        val token = ++pendingAutoLocateSearchToken
        locateStatusText = if (looksLikeWarehouse18FullEpc(normalizedHex)) {
            "Full EPC captured. Starting locate automatically..."
        } else {
            "Barcode captured. Starting RFID search automatically..."
        }

        lifecycleScope.launch {
            kotlinx.coroutines.delay(1_000L)

            if (token != pendingAutoLocateSearchToken) return@launch
            if (selectedMenuOption != MenuOption.LocateItem) return@launch
            if (!barcodeCaptured || capturedBarcode.trim() != barcode.trim()) return@launch

            if (looksLikeWarehouse18FullEpc(normalizedHex)) {
                startLocateSelectedTag(normalizedHex)
            } else {
                startLocateSearch()
            }
        }
    }

    private fun lookupRegisteredLocationForLocate(barcode: String) {
        val cleanBarcode = barcode.trim().uppercase(Locale.ROOT)

        if (cleanBarcode.isBlank()) {
            locateRegisteredLocationState = LocateRegisteredLocationState.Idle
            return
        }

        locateRegisteredLocationState = LocateRegisteredLocationState.Loading

        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                Warehouse18Api.findRegisteredLocationForBarcode(cleanBarcode)
            }

            if (selectedMenuOption != MenuOption.LocateItem) return@launch
            if (!barcodeCaptured || capturedBarcode.trim().uppercase(Locale.ROOT) != cleanBarcode) return@launch

            locateRegisteredLocationState = when (result) {
                is LocateRegisteredLocationResult.Success -> LocateRegisteredLocationState.Found(result.info)
                LocateRegisteredLocationResult.NotFound -> LocateRegisteredLocationState.NotFound(cleanBarcode)
                is LocateRegisteredLocationResult.Failure -> LocateRegisteredLocationState.Error(result.message)
            }
        }
    }

    private fun prepareLocateItem(barcode: String) {
        val clean = barcode.trim().uppercase(Locale.ROOT)
        resetLocateState(stopRfid = false)

        if (clean.isBlank()) {
            locateStatusText = "Scan or type an item barcode first."
            return
        }

        val normalizedHex = normalizeRfidKey(clean)

        if (looksLikeWarehouse18FullEpc(normalizedHex)) {
            locateTargetEpc = normalizedHex
            locateExpectedPrefix = normalizedHex.take(10)
            locateStatusText = "Full EPC captured. Starting locate automatically..."
            return
        }

        locateExpectedPrefix = runCatching { expectedEpcPrefixFromBarcode(clean) }
            .getOrElse { "" }

        locateStatusText = if (locateExpectedPrefix.isBlank()) {
            "Barcode captured. Searching nearby Warehouse18 tags..."
        } else {
            "Barcode captured. Searching nearby tags for prefix: $locateExpectedPrefix"
        }
    }

    private fun startLocateSearch() {
        val barcode = capturedBarcode.trim().uppercase(Locale.ROOT)

        if (barcode.isBlank()) {
            locateStatusText = "Scan an item barcode before searching."
            return
        }

        if (locateSearching || locateRunning || locateConnecting) return

        if (locateExpectedPrefix.isBlank() && locateTargetEpc.isBlank()) {
            prepareLocateItem(barcode)
        }

        val searchToken = ++locateSearchSessionToken

        locateSearching = true
        locateCandidates = emptyList()
        locateProximity = null
        locateRssi = null
        locateStatusText = "Searching nearby RFID tags for this item..."

        lifecycleScope.launch {
            val errorMessage = withContext(Dispatchers.IO) {
                try {
                    if (!rfidController.isConnected) {
                        rfidController.connect()
                    }

                    if (searchToken != locateSearchSessionToken) {
                        runCatching { rfidController.stopInventory() }
                        return@withContext null
                    }

                    rfidController.startInventory()

                    val startedAt = System.currentTimeMillis()
                    while (System.currentTimeMillis() - startedAt < 1_600L) {
                        if (searchToken != locateSearchSessionToken || !locateSearching) {
                            runCatching { rfidController.stopInventory() }
                            return@withContext null
                        }
                        Thread.sleep(80L)
                    }

                    rfidController.stopInventory()
                    null
                } catch (exception: Exception) {
                    runCatching { rfidController.stopInventory() }
                    exception.message ?: "Unknown RFID search error."
                }
            }

            if (searchToken != locateSearchSessionToken || !locateSearching) {
                locateSearching = false
                locateStatusText = "RFID search stopped."
                return@launch
            }

            locateSearching = false

            if (errorMessage != null) {
                locateStatusText = "RFID search error: $errorMessage"
                return@launch
            }

            val candidates = locateCandidates.sortedWith(
                compareByDescending<LocateCandidate> { it.reads }
                    .thenByDescending { it.rssi ?: -999 }
                    .thenBy { it.epc }
            )
            locateCandidates = candidates

            when {
                locateTargetEpc.isNotBlank() -> {
                    locateStatusText = "Target EPC ready. Starting locate automatically..."
                    startLocateSelectedTag(locateTargetEpc)
                }

                candidates.isEmpty() -> {
                    locateStatusText = "No matching RFID tag found for this barcode. Move closer, remove unrelated tags, and tap Find nearby tags again."
                }

                candidates.size == 1 -> {
                    val candidate = candidates.first()
                    locateTargetEpc = candidate.epc
                    locateProximity = proximityFromRssiOrReads(candidate.rssi, candidate.reads)
                    locateRssi = candidate.rssi
                    locateTargetReads = candidate.reads
                    locateStatusText = "One matching tag found. Starting locate automatically..."
                    startLocateSelectedTag(candidate.epc)
                }

                else -> {
                    locateStatusText = "${candidates.size} matching tags found. Select one to locate."
                }
            }
        }
    }

    private fun startLocateSelectedTag(epc: String = locateTargetEpc) {
        val cleanEpc = normalizeRfidKey(epc)

        if (cleanEpc.isBlank()) {
            locateStatusText = "Select or find a tag before starting locate."
            return
        }

        if (locateSearching || locateConnecting) return

        locateSearchSessionToken += 1
        locateTargetEpc = cleanEpc
        locateRunning = false
        locateConnecting = true
        locateProximity = null
        locateRssi = null
        locateTargetReads = 0
        latestLocateProximity = 0
        latestLocateSeenAtMs = 0L
        locateProximitySamples.clear()
        smoothedLocateProximity = null
        locateStatusText = "Connecting RFID reader for location mode..."

        lifecycleScope.launch {
            val errorMessage = withContext(Dispatchers.IO) {
                try {
                    if (!rfidController.isConnected) {
                        rfidController.connect()
                    }
                    rfidController.startInventory()
                    null
                } catch (exception: Exception) {
                    exception.message ?: "Unknown RFID locate error."
                }
            }

            locateConnecting = false

            if (errorMessage == null) {
                locateRunning = true
                startLocateBeepLoop()
                locateStatusText = "Locating tag. Move slowly and follow the signal."
            } else {
                locateRunning = false
                locateStatusText = "RFID locate error: $errorMessage"
            }
        }
    }

    private fun stopLocate() {
        if (!locateRunning && !locateConnecting && !locateSearching) {
            locateStatusText = "Locate is not running."
            return
        }

        locateSearchSessionToken += 1
        locateRunning = false
        locateConnecting = false
        locateSearching = false
        stopLocateBeepLoop()

        lifecycleScope.launch {
            withContext(Dispatchers.IO) {
                runCatching { rfidController.stopInventory() }
            }
            locateStatusText = if (locateTargetEpc.isBlank()) {
                "RFID search stopped."
            } else {
                "Locate stopped. Tap the tag again or press Find nearby tags to search again."
            }
        }
    }

    private fun handleLocateRfidTagRead(
        epc: String,
        decodedObjectCode: String,
        rssi: Int?
    ) {
        if (!locateSearching && !locateRunning) return

        val cleanEpc = normalizeRfidKey(epc)
        val expectedPrefix = locateExpectedPrefix.trim().uppercase(Locale.ROOT)
        val target = locateTargetEpc.trim().uppercase(Locale.ROOT)

        val matchesTarget = when {
            target.isNotBlank() -> cleanEpc == target
            expectedPrefix.isNotBlank() -> cleanEpc.startsWith(expectedPrefix)
            else -> decodedObjectCode.isNotBlank()
        }

        if (!matchesTarget) return

        val now = System.currentTimeMillis()
        val existing = locateCandidates.firstOrNull { it.epc == cleanEpc }
        locateCandidates = if (existing == null) {
            locateCandidates + LocateCandidate(
                epc = cleanEpc,
                decodedObjectCode = decodedObjectCode,
                rssi = rssi,
                reads = 1,
                lastSeenAt = now
            )
        } else {
            locateCandidates.map { candidate ->
                if (candidate.epc == cleanEpc) {
                    candidate.copy(
                        decodedObjectCode = candidate.decodedObjectCode.ifBlank { decodedObjectCode },
                        rssi = rssi ?: candidate.rssi,
                        reads = candidate.reads + 1,
                        lastSeenAt = now
                    )
                } else {
                    candidate
                }
            }
        }

        if (target.isNotBlank() && cleanEpc == target) {
            val current = locateCandidates.firstOrNull { it.epc == cleanEpc }
            val reads = current?.reads ?: 1
            val rawProximity = proximityFromRssiOrReads(rssi ?: current?.rssi, reads)
            val proximity = stableLocateProximityFrom(rawProximity)

            locateProximity = proximity
            locateRssi = rssi ?: current?.rssi
            locateTargetReads = reads
            latestLocateProximity = proximity
            latestLocateSeenAtMs = now
            locateStatusText = "Target tag detected. Move slowly and follow the signal."
        } else if (locateSearching) {
            locateStatusText = "Matching tag detected. Keep scanning to isolate the target."
        }
    }

    private fun startLocateBeepLoop() {
        if (locateBeepLoopRunning) return

        if (toneGenerator == null) {
            toneGenerator = runCatching { ToneGenerator(AudioManager.STREAM_MUSIC, 100) }.getOrNull()
        }

        locateBeepLoopRunning = true
        locateBeepThread = thread(start = true, name = "ChafonLocateBeepLoop") {
            while (locateBeepLoopRunning) {
                val ageMs = if (latestLocateSeenAtMs <= 0L) Long.MAX_VALUE else System.currentTimeMillis() - latestLocateSeenAtMs
                val proximity = if (ageMs > 2_500L) 0 else latestLocateProximity.coerceIn(0, 100)
                val intervalMs = locateBeepIntervalMs(proximity)

                runCatching {
                    toneGenerator?.startTone(ToneGenerator.TONE_PROP_BEEP, 55)
                }

                try {
                    Thread.sleep(intervalMs)
                } catch (_: InterruptedException) {
                    return@thread
                }
            }
        }
    }

    private fun stopLocateBeepLoop() {
        locateBeepLoopRunning = false
        runCatching { locateBeepThread?.interrupt() }
        locateBeepThread = null
        runCatching { toneGenerator?.stopTone() }
    }

    private fun locateBeepIntervalMs(proximity: Int): Long {
        val clean = proximity.coerceIn(0, 100)
        val maxIntervalMs = 1200L
        val minIntervalMs = 90L
        return maxIntervalMs - ((maxIntervalMs - minIntervalMs) * clean / 100L)
    }

    private fun handleProgramBarcodeCaptured(barcode: String) {
        val clean = barcode.trim().uppercase(Locale.ROOT)
        resetProgramTagState(stopRfid = false)

        programStatusText = if (clean.isBlank()) {
            "Scan barcode first, then read one RFID tag."
        } else {
            "Barcode captured. Keep only one tag close to the reader, then press Read RFID tag."
        }
    }

    private fun readSingleProgramTagForCurrentBarcode() {
        val barcode = capturedBarcode.trim().uppercase(Locale.ROOT)

        if (barcode.isBlank()) {
            programStatusText = "Scan barcode before reading RFID."
            return
        }

        if (programReadingTag || programConnecting || programWritingTag) return

        programDetectedTags = emptyList()
        programDetectedEpc = ""
        programDetectedRssi = null
        programTidHex = ""
        programTidTail = ""
        programGeneratedEpc = ""
        programWritingTag = false
        programConfirmingWrite = false
        programTagProgrammed = false
        programReadingTag = true
        programConnecting = true
        programStatusText = "Connecting Chafon RFID reader. Keep only one tag close to the antenna."

        lifecycleScope.launch {
            val errorMessage = withContext(Dispatchers.IO) {
                try {
                    if (!rfidController.isConnected) {
                        rfidController.connect()
                    }
                    rfidController.startInventory()
                    Thread.sleep(1_300L)
                    rfidController.stopInventory()
                    null
                } catch (exception: Exception) {
                    runCatching { rfidController.stopInventory() }
                    exception.message ?: "Unknown RFID read error."
                }
            }

            programConnecting = false
            programReadingTag = false

            if (errorMessage != null) {
                programStatusText = "RFID read error: $errorMessage"
                return@launch
            }

            val tags = sortProgramDetectedTags(programDetectedTags)
            programDetectedTags = tags

            when {
                tags.isEmpty() -> {
                    programStatusText = "No RFID tag detected. Place one tag close to the reader and try again."
                }

                tags.size > 1 -> {
                    val suggested = tags.first()
                    programStatusText = "Multiple RFID tags detected (${tags.size}). Select the tag to program. Suggested: strongest signal ${suggested.epc}."
                }

                else -> {
                    val tag = tags.first()
                    selectProgramDetectedTagForProgramming(tag.epc)
                }
            }
        }
    }

    private fun handleProgramRfidTagRead(epc: String, rssi: Int?) {
        if (!programReadingTag && !programConnecting) return

        val cleanEpc = normalizeRfidKey(epc)
        if (cleanEpc.isBlank()) return

        val now = System.currentTimeMillis()
        val existing = programDetectedTags.firstOrNull { it.epc == cleanEpc }

        programDetectedTags = if (existing == null) {
            programDetectedTags + ProgramDetectedTag(
                epc = cleanEpc,
                rssi = rssi,
                reads = 1,
                lastSeenAt = now
            )
        } else {
            programDetectedTags.map { current ->
                if (current.epc == cleanEpc) {
                    current.copy(
                        rssi = rssi ?: current.rssi,
                        reads = current.reads + 1,
                        lastSeenAt = now
                    )
                } else {
                    current
                }
            }
        }

        val visibleTags = sortProgramDetectedTags(programDetectedTags)
        programStatusText = if (visibleTags.size == 1) {
            "RFID tag detected. Keep it close until reading finishes."
        } else {
            "Multiple RFID tags detected. The strongest signal will be suggested, but you can select the tag manually."
        }
    }

    private fun sortProgramDetectedTags(tags: List<ProgramDetectedTag>): List<ProgramDetectedTag> {
        return tags.sortedWith(
            compareByDescending<ProgramDetectedTag> { it.rssi ?: -999 }
                .thenByDescending { it.reads }
                .thenByDescending { it.lastSeenAt }
                .thenBy { it.epc }
        )
    }

    private fun selectProgramDetectedTagForProgramming(epc: String) {
        val barcode = capturedBarcode.trim().uppercase(Locale.ROOT)
        val cleanEpc = normalizeRfidKey(epc)

        if (barcode.isBlank()) {
            programStatusText = "Scan barcode before selecting an RFID tag."
            return
        }

        if (programReadingTag || programConnecting || programWritingTag) {
            programStatusText = "Wait until the current RFID operation finishes."
            return
        }

        val sortedTags = sortProgramDetectedTags(programDetectedTags)
        val tag = sortedTags.firstOrNull { normalizeRfidKey(it.epc) == cleanEpc }

        if (tag == null) {
            programStatusText = "Selected RFID tag was not found in the last read. Read nearby tags again."
            return
        }

        programDetectedTags = sortedTags
        programDetectedEpc = tag.epc
        programDetectedRssi = tag.rssi
        programTidHex = ""
        programTidTail = ""
        programGeneratedEpc = ""
        programStatusText = "Selected tag. Reading TID for:\n${tag.epc}"

        readTidAndGenerateProgramEpc(barcode = barcode, epc = tag.epc)
    }

    private fun readTidAndGenerateProgramEpc(barcode: String, epc: String) {
        programReadingTag = true

        lifecycleScope.launch {
            val tidResult = withContext(Dispatchers.IO) {
                try {
                    if (!rfidController.isConnected) {
                        rfidController.connect()
                    }
                    val tid = rfidController.readTid(epc)
                    if (tid.isBlank()) {
                        Result.failure<String>(RuntimeException("TID was empty. The tag may be too far, locked, or the SDK read method needs adjustment."))
                    } else {
                        Result.success(tid)
                    }
                } catch (exception: Exception) {
                    Result.failure(exception)
                }
            }

            programReadingTag = false

            tidResult.fold(
                onSuccess = { tid ->
                    val cleanTid = normalizeRfidKey(tid)
                    val tidTail = cleanTid.padStart(12, '0').takeLast(12)
                    programTidHex = cleanTid
                    programTidTail = tidTail

                    val generated = runCatching {
                        generateWarehouse18EpcFromBarcodeAndTid(
                            barcode = barcode,
                            tidHex = cleanTid
                        )
                    }

                    generated.fold(
                        onSuccess = { epcGenerated ->
                            programGeneratedEpc = epcGenerated
                            programConfirmingWrite = false
                            programTagProgrammed = false
                            programStatusText = if (normalizeRfidKey(epcGenerated) == normalizeRfidKey(epc)) {
                                "Generated EPC is the same as the current EPC. No write is needed unless you read a different tag."
                            } else {
                                "Tag ready. EPC generated from barcode + TID. Review the details, then press Program tag."
                            }
                        },
                        onFailure = { error ->
                            programGeneratedEpc = ""
                            programStatusText = "TID read, but EPC could not be generated: ${error.message}"
                        }
                    )
                },
                onFailure = { error ->
                    programTidHex = ""
                    programTidTail = ""
                    programGeneratedEpc = ""
                    programStatusText = "Tag detected, but TID could not be read: ${error.message}"
                }
            )
        }
    }


    private fun writeGeneratedProgramTag() {
        val currentEpc = normalizeRfidKey(programDetectedEpc)
        val newEpc = normalizeRfidKey(programGeneratedEpc)

        if (programReadingTag || programConnecting || programWritingTag) return

        if (programTagProgrammed) {
            programStatusText = "This tag is already marked as programmed. Press Clear barcode to start another tag."
            return
        }

        if (currentEpc.isBlank()) {
            programStatusText = "Read one RFID tag before programming."
            return
        }

        if (newEpc.isBlank()) {
            programStatusText = "Generated EPC is empty. Read the tag/TID again before programming."
            return
        }

        if (!looksLikeWarehouse18FullEpc(newEpc)) {
            programStatusText = "Generated EPC is not a valid Warehouse18 EPC. Do not program this tag."
            return
        }

        if (programTidHex.isBlank() || programTidTail.isBlank()) {
            programStatusText = "TID is missing. Read the tag again before programming."
            return
        }

        if (currentEpc == newEpc) {
            programConfirmingWrite = false
            programStatusText = "Generated EPC is already equal to the current EPC. No write was sent."
            return
        }

        if (!programConfirmingWrite) {
            programConfirmingWrite = true
            programStatusText = "Program selected tag? Review Barcode, Current EPC, New EPC and RSSI, then press Confirm program."
            return
        }

        programConfirmingWrite = false
        programWritingTag = true
        programStatusText = "Programming selected tag. Keep only this tag close to the antenna."

        lifecycleScope.launch {
            val writeError = withContext(Dispatchers.IO) {
                try {
                    if (!rfidController.isConnected) {
                        rfidController.connect()
                    }

                    runCatching { rfidController.stopInventory() }
                    Thread.sleep(250L)

                    rfidController.writeEpc(
                        currentEpc = currentEpc,
                        newEpc = newEpc
                    )

                    null
                } catch (exception: Exception) {
                    exception.message ?: "Unknown EPC write error."
                }
            }

            if (writeError != null) {
                programWritingTag = false
                programConfirmingWrite = false
                programStatusText = "Tag programming failed: $writeError"
                return@launch
            }

            programStatusText = "Write sent. Verifying programmed EPC..."
            programDetectedTags = emptyList()
            programReadingTag = true

            val verifyError = withContext(Dispatchers.IO) {
                try {
                    runCatching { rfidController.stopInventory() }
                    Thread.sleep(350L)
                    rfidController.startInventory()
                    Thread.sleep(1_500L)
                    rfidController.stopInventory()
                    null
                } catch (exception: Exception) {
                    runCatching { rfidController.stopInventory() }
                    exception.message ?: "Unknown verification error."
                }
            }

            programReadingTag = false
            programWritingTag = false

            if (verifyError != null) {
                programConfirmingWrite = false
                programStatusText = "Write sent, but verification failed: $verifyError"
                return@launch
            }

            val detectedAfterWrite = programDetectedTags
                .map { normalizeRfidKey(it.epc) }
                .toSet()

            if (detectedAfterWrite.contains(newEpc)) {
                programDetectedEpc = newEpc
                programDetectedRssi = programDetectedTags
                    .firstOrNull { normalizeRfidKey(it.epc) == newEpc }
                    ?.rssi
                programConfirmingWrite = false
                programTagProgrammed = true
                programStatusText = "Tag programmed and verified successfully. This tag is marked as Programmed."
            } else {
                val readText = detectedAfterWrite.joinToString("\n").ifBlank { "No tag read during verification." }
                programConfirmingWrite = false
                programStatusText = "Write sent, but verification did not read the expected EPC. Expected:\n$newEpc\n\nRead:\n$readText"
            }
        }
    }

    private fun submitInventoryResultForCurrentLocation() {
        val location = (inventoryLookupState as? InventoryLookupState.Found)?.location
        val expectedAssets = (expectedAssetsState as? ExpectedAssetsState.Loaded)?.assets.orEmpty()

        if (location == null) {
            inventorySubmitState = InventorySubmitState.Error("Load a valid location before submitting inventory.")
            return
        }

        if (expectedAssets.isEmpty()) {
            inventorySubmitState = InventorySubmitState.Error("There are no expected items to submit for this location.")
            return
        }

        when (inventorySubmitState) {
            InventorySubmitState.Submitting -> return
            is InventorySubmitState.Submitted -> {
                inventorySubmitState = InventorySubmitState.Error("Inventory already submitted. Press New inventory to start another scan.")
                return
            }
            else -> Unit
        }

        if (rfidRunning || rfidConnecting) {
            stopRfidInventory(silent = true)
        }

        inventorySubmitState = InventorySubmitState.Submitting
        rfidStatusText = "Submitting inventory result to Warehouse18..."

        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                Warehouse18Api.submitInventoryByLocation(
                    location = location,
                    expectedAssets = expectedAssets,
                    readTags = rfidTagsRead,
                    scanValidations = rfidScanValidations
                )
            }

            when (result) {
                is InventorySubmitResult.Success -> {
                    inventorySubmitState = InventorySubmitState.Submitted(result.message)
                    rfidStatusText = result.message
                }

                is InventorySubmitResult.Failure -> {
                    inventorySubmitState = InventorySubmitState.Error(result.message)
                    rfidStatusText = "Inventory submit failed."
                }
            }
        }
    }

    @SuppressLint("GestureBackNavigation")
    override fun onKeyDown(keyCode: Int, event: KeyEvent): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            goBackToMainMenuOrExit()
            return true
        }

        if (isChafonTriggerKey(keyCode, event.scanCode)) {
            if (event.repeatCount == 0) {
                if (!stopLocateFromTriggerIfRunning()) {
                    if (!startProgramTagReadFromTriggerIfReady()) {
                        startInventoryFromTriggerIfReady()
                    }
                }
            }
            return true
        }

        return super.onKeyDown(keyCode, event)
    }

    @SuppressLint("GestureBackNavigation")
    override fun onKeyUp(keyCode: Int, event: KeyEvent): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            return true
        }

        if (isChafonTriggerKey(keyCode, event.scanCode)) {
            if (!stopLocateFromTriggerIfRunning()) {
                if (!stopProgramTagReadFromTriggerIfRunning()) {
                    stopInventoryFromTriggerIfRunning()
                }
            }
            return true
        }

        if (selectedMenuOption == MenuOption.LocateItem && (locateRunning || locateSearching || locateConnecting)) {
            stopLocateFromTriggerIfRunning()
            return true
        }

        if (selectedMenuOption == MenuOption.InventoryByLocation && (rfidRunning || rfidConnecting)) {
            stopInventoryFromTriggerIfRunning()
            return true
        }

        if (selectedMenuOption == MenuOption.ProgramTag && (programReadingTag || programConnecting)) {
            stopProgramTagReadFromTriggerIfRunning()
            return true
        }

        return super.onKeyUp(keyCode, event)
    }

    @SuppressLint("GestureBackNavigation", "MissingSuperCall")
    @Deprecated("Use OnBackPressedDispatcher")
    override fun onBackPressed() {
        goBackToMainMenuOrExit()
    }

    override fun onDestroy() {
        runCatching { rfidController.stopInventory() }
        runCatching { rfidController.disconnect() }
        rfidController.setListener(null)
        stopLocateBeepLoop()
        runCatching { toneGenerator?.release() }
        toneGenerator = null
        super.onDestroy()
    }

}

private enum class MenuOption(
    val title: String,
    val subtitle: String,
    val prompt: String,
    val barcodeLabel: String,
    val idleStatus: String,
    val waitingStatus: String,
    val capturedStatus: String,
    val extraReadsIgnoredStatus: String,
    val resultTitle: String,
    val nextStepHint: String,
    val imageRes: Int
) {
    InventoryByLocation(
        title = "Inventory by Location",
        subtitle = "Scan location barcode",
        prompt = "Scan the location barcode",
        barcodeLabel = "Location barcode",
        idleStatus = "Press trigger to scan the location barcode",
        waitingStatus = "Trigger detected. Waiting for location barcode...",
        capturedStatus = "Location barcode captured. Extra reads ignored.",
        extraReadsIgnoredStatus = "Location already captured. Extra reads ignored.",
        resultTitle = "Location captured",
        nextStepHint = "Next step: load the expected items for this location.",
        imageRes = R.drawable.w18inventory
    ),
    LocateItem(
        title = "Locate Item",
        subtitle = "Scan item barcode",
        prompt = "Scan the item barcode",
        barcodeLabel = "Item barcode",
        idleStatus = "Press trigger to scan the item barcode",
        waitingStatus = "Trigger detected. Waiting for item barcode...",
        capturedStatus = "Item barcode captured. Extra reads ignored.",
        extraReadsIgnoredStatus = "Item already captured. Extra reads ignored.",
        resultTitle = "Item captured",
        nextStepHint = "Next step: resolve the item/EPC and start RFID location mode.",
        imageRes = R.drawable.w18search
    ),
    ProgramTag(
        title = "Program Tag",
        subtitle = "Scan barcode before programming",
        prompt = "Scan the barcode to program",
        barcodeLabel = "Barcode to program",
        idleStatus = "Press trigger to scan the barcode to program",
        waitingStatus = "Trigger detected. Waiting for barcode to program...",
        capturedStatus = "Programming barcode captured. Extra reads ignored.",
        extraReadsIgnoredStatus = "Programming barcode already captured. Extra reads ignored.",
        resultTitle = "Programming barcode captured",
        nextStepHint = "Next step: read or write the RFID tag using this barcode.",
        imageRes = R.drawable.w18program
    )
}

@Composable
private fun MainMenuScreen(
    onOptionSelected: (MenuOption) -> Unit,
    onSettingsSelected: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F8FB))
    ) {
        Button(
            onClick = onSettingsSelected,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(top = 12.dp, end = 12.dp)
                .size(46.dp),
            shape = RoundedCornerShape(23.dp),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF334155),
                contentColor = Color.White
            ),
            elevation = ButtonDefaults.buttonElevation(defaultElevation = 0.dp)
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
                .padding(horizontal = 24.dp, vertical = 22.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            //Spacer(modifier = Modifier.height(20.dp))

            Image(
                painter = painterResource(id = R.drawable.logorfid1),
                contentDescription = "Warehouse18 logo",
                modifier = Modifier
                    .fillMaxWidth(0.78f)
                    .height(250.dp),
                contentScale = ContentScale.Fit
            )

            //Spacer(modifier = Modifier.height(12.dp))

            ZebraStyleMenuButton(
                title = "Inventory by location",
                iconRes = R.drawable.ic_inventory,
                backgroundColor = Color(0xFF1064AD),
                onClick = { onOptionSelected(MenuOption.InventoryByLocation) }
            )

            ZebraStyleMenuButton(
                title = "Search tag",
                iconRes = R.drawable.ic_locate_tag,
                backgroundColor = Color(0xFF14843D),
                onClick = { onOptionSelected(MenuOption.LocateItem) }
            )

            ZebraStyleMenuButton(
                title = "Program tag",
                iconRes = R.drawable.ic_pencil_write,
                backgroundColor = Color(0xFF4B5C6E),
                onClick = { onOptionSelected(MenuOption.ProgramTag) }
            )
        }
    }
}

@Composable
private fun ZebraStyleMenuButton(
    title: String,
    iconRes: Int,
    backgroundColor: Color,
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .height(96.dp),
        shape = RoundedCornerShape(18.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = backgroundColor,
            contentColor = Color.White
        ),
        elevation = ButtonDefaults.buttonElevation(defaultElevation = 0.dp),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 26.dp, vertical = 0.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Image(
                painter = painterResource(id = iconRes),
                contentDescription = null,
                modifier = Modifier.size(56.dp),
                contentScale = ContentScale.Fit
            )

            Spacer(modifier = Modifier.width(24.dp))

            Text(
                text = title,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
        }
    }
}


@Composable
private fun SettingsScreen(
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
    val previewUrl = AppSettingsStore.buildBaseUrl(
        ip = backendIp,
        port = backendPort,
        prefix = backendPrefix
    )

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = Color(0xFFF5F8FB)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFFF5F8FB))
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 18.dp, vertical = 18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            horizontalAlignment = Alignment.Start
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
                    .height(54.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0B5CAD))
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
                label = { Text("Backend prefix before /api", color = Color.Black) },
                placeholder = { Text("empty or /warehouse18", color = Color(0xFF64748B)) },
                singleLine = true
            )

            Text(
                text = "Current URL: $currentBaseUrl",
                color = Color(0xFF64748B),
                style = MaterialTheme.typography.bodySmall
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
                        .height(54.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED))
                ) {
                    Text("Test", fontWeight = FontWeight.Bold)
                }

                Button(
                    onClick = onSave,
                    modifier = Modifier
                        .weight(1f)
                        .height(54.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF15803D))
                ) {
                    Text("Save", fontWeight = FontWeight.Bold)
                }
            }

            Button(
                onClick = onBack,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF475569))
            ) {
                Text("Back", fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun W18TopOperationLogo(
    imageRes: Int,
    contentDescription: String
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(78.dp),
        contentAlignment = Alignment.CenterStart
    ) {
        Image(
            painter = painterResource(id = imageRes),
            contentDescription = contentDescription,
            modifier = Modifier
                .height(68.dp)
                .widthIn(max = 320.dp),
            contentScale = ContentScale.Fit,
            alignment = Alignment.CenterStart
        )
    }
}

@Composable
private fun W18InventoryByLocationLightScreen(
    capturedBarcode: String,
    barcodeCaptured: Boolean,
    statusText: String,
    resetCounter: Int,
    inventoryLookupState: InventoryLookupState,
    expectedAssetsState: ExpectedAssetsState,
    rfidTagsRead: List<RfidInventoryTag>,
    rfidScanValidations: Map<String, RfidScanValidation>,
    rfidStatusText: String,
    rfidRunning: Boolean,
    rfidConnecting: Boolean,
    inventorySubmitState: InventorySubmitState,
    screenBusy: Boolean,
    onTriggerDetected: () -> Unit,
    onTriggerReleased: () -> Unit,
    onBarcodeCaptured: (String) -> Unit,
    onReloadInventoryLocation: () -> Unit,
    onStartRfidInventory: () -> Unit,
    onStopRfidInventory: () -> Unit,
    onSubmitInventoryResult: () -> Unit,
    onNewInventory: () -> Unit,
    onClearBarcode: () -> Unit
) {
    val lightBackground = Color(0xFFF5F8FB)
    val darkText = Color(0xFF263447)
    val headerText = Color(0xFF082B4A)
    val mutedText = Color(0xFF617085)
    val expectedAssets = (expectedAssetsState as? ExpectedAssetsState.Loaded)?.assets.orEmpty()
    val foundCount = expectedAssets.count { expected ->
        rfidScanValidations.values.any { validation -> expectedItemMatchesValidation(expected, validation) }
    }
    val pendingCount = (expectedAssets.size - foundCount).coerceAtLeast(0)
    val submitDone = inventorySubmitState is InventorySubmitState.Submitted
    val canReload = capturedBarcode.isNotBlank() &&
            !rfidRunning &&
            !rfidConnecting &&
            inventorySubmitState !is InventorySubmitState.Submitting
    val canSubmit = expectedAssets.isNotEmpty() &&
            !rfidRunning &&
            !rfidConnecting &&
            inventorySubmitState !is InventorySubmitState.Submitting &&
            inventorySubmitState !is InventorySubmitState.Submitted
    val instructionText = when {
        inventorySubmitState is InventorySubmitState.Submitting -> "Submitting inventory result..."
        submitDone -> "Inventory submitted. Press New inventory to scan another location."
        rfidRunning -> "Reading RFID. Stop the inventory before submitting."
        rfidConnecting -> "Connecting RFID reader..."
        inventoryLookupState is InventoryLookupState.Found -> "Location loaded. Start RFID inventory and submit when finished."
        inventoryLookupState is InventoryLookupState.Loading -> "Loading location and expected inventory..."
        else -> "Scan location barcode first. You can also type the location and press ↻."
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = lightBackground
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(lightBackground)
                .verticalScroll(rememberScrollState())
                .padding(
                    start = 16.dp,
                    end = 16.dp,
                    top = 8.dp,
                    bottom = 16.dp
                ),
            verticalArrangement = Arrangement.spacedBy(3.dp),
            horizontalAlignment = Alignment.Start

        ) {
            W18TopOperationLogo(
                imageRes = R.drawable.w18inventory,
                contentDescription = "W18 Inventory"
            )

            Text(
                text = instructionText,
                color = darkText,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(top = 0.dp)
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                ChafonBarcodeEditText(
                    modifier = Modifier.weight(1f),
                    inputHint = "Location name",
                    capturedBarcode = capturedBarcode,
                    barcodeCaptured = barcodeCaptured,
                    resetCounter = resetCounter,
                    heightDp = 60,
                    cornerRadiusDp = 6,
                    textColorHex = "#333333",
                    hintColorHex = "#555B66",
                    backgroundColorHex = "#F5F8FB",
                    strokeColorHex = "#6D6F78",
                    onTriggerDetected = onTriggerDetected,
                    onTriggerReleased = onTriggerReleased,
                    onBarcodeCaptured = onBarcodeCaptured
                )

                W18RoundInventoryButton(
                    text = "↻",
                    enabled = canReload,
                    backgroundColor = Color(0xFF1267B1),
                    disabledBackgroundColor = Color(0xFFD7D9DD),
                    onClick = onReloadInventoryLocation
                )

                W18RoundInventoryButton(
                    text = "✓",
                    enabled = canSubmit,
                    backgroundColor = Color(0xFF15803D),
                    disabledBackgroundColor = Color(0xFFD7D9DD),
                    onClick = onSubmitInventoryResult
                )

                W18RoundInventoryButton(
                    text = "×",
                    enabled = !screenBusy,
                    backgroundColor = Color(0xFF4B5C6E),
                    disabledBackgroundColor = Color(0xFFD7D9DD),
                    onClick = onClearBarcode
                )
            }
            Spacer(modifier = Modifier.height(12.dp))
            /*W18InventoryLightStatus(
                statusText = statusText,
                rfidStatusText = rfidStatusText,
                lookupState = inventoryLookupState,
                expectedAssetsState = expectedAssetsState,
                submitState = inventorySubmitState,
                textColor = mutedText
            )*/

            /*if (expectedAssets.isNotEmpty() && inventorySubmitState !is InventorySubmitState.Submitted) {
                if (rfidRunning || rfidConnecting) {
                    Button(
                        onClick = onStopRfidInventory,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFFB91C1C),
                            contentColor = Color.White
                        )
                    ) {
                        Text(if (rfidConnecting) "Cancel RFID inventory" else "Stop RFID inventory", fontWeight = FontWeight.Bold)
                    }
                } else {
                    Button(
                        onClick = onStartRfidInventory,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF1267B1),
                            contentColor = Color.White
                        )
                    ) {
                        Text("Start RFID inventory", fontWeight = FontWeight.Bold)
                    }
                }
            }*/

            if (inventorySubmitState is InventorySubmitState.Submitted) {
                Button(
                    onClick = onNewInventory,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF1267B1),
                        contentColor = Color.White
                    )
                ) {
                    Text("New inventory", fontWeight = FontWeight.Bold)
                }
            }

            W18InventoryLightStats(
                loaded = expectedAssets.size,
                ok = foundCount,
                pending = pendingCount
            )

            W18InventoryLightTable(
                expectedAssets = expectedAssets,
                rfidTagsRead = rfidTagsRead,
                rfidScanValidations = rfidScanValidations
            )
        }
    }
}

@Composable
private fun W18RoundInventoryButton(
    text: String,
    enabled: Boolean,
    backgroundColor: Color,
    disabledBackgroundColor: Color,
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.size(50.dp),
        shape = RoundedCornerShape(36.dp),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = backgroundColor,
            contentColor = Color.White,
            disabledContainerColor = disabledBackgroundColor,
            disabledContentColor = Color(0xFF9AA1AC)
        ),
        elevation = ButtonDefaults.buttonElevation(defaultElevation = 0.dp)
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = text,
                modifier = Modifier.padding(
                    bottom = if (text == "↻") 4.dp else 0.dp
                ),
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center
            )
        }
    }
}

@Composable
private fun W18InventoryLightStats(
    loaded: Int,
    ok: Int,
    pending: Int
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        W18InventoryLightStatCard("Loaded", loaded.toString(), Color(0xFFDDF2FF), Modifier.weight(1f))
        W18InventoryLightStatCard("Ok", ok.toString(), Color(0xFFCFF4C9), Modifier.weight(1f))
        W18InventoryLightStatCard("Pending", pending.toString(), Color(0xFFFFCCA7), Modifier.weight(1f))
    }
}

@Composable
private fun W18InventoryLightStatCard(
    label: String,
    value: String,
    backgroundColor: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.height(84.dp),
        shape = RoundedCornerShape(10.dp),
        colors = CardDefaults.cardColors(containerColor = backgroundColor),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = value,
                color = Color(0xFF082B4A),
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = label,
                color = Color(0xFF263447),
                style = MaterialTheme.typography.bodyLarge
            )
        }
    }
}

@Composable
private fun W18InventoryLightTable(
    expectedAssets: List<ExpectedAssetInfo>,
    rfidTagsRead: List<RfidInventoryTag>,
    rfidScanValidations: Map<String, RfidScanValidation>
) {
    val groupedRows = buildInventoryGroupedRows(
        expectedAssets = expectedAssets,
        rfidTagsRead = rfidTagsRead,
        rfidScanValidations = rfidScanValidations
    )

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(0.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Color(0xFFCBD5E1)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.White)
                    .padding(horizontal = 8.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Item", modifier = Modifier.weight(1.35f), color = Color.Black, fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)
                Text("Qty", modifier = Modifier.weight(0.55f), color = Color.Black, fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
                Text("Read", modifier = Modifier.weight(0.55f), color = Color.Black, fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
                Text("Status", modifier = Modifier.weight(0.85f), color = Color.Black, fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
            }

            if (groupedRows.isEmpty()) {
                Text(
                    text = "No items loaded yet.",
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color.White)
                        .padding(horizontal = 14.dp, vertical = 18.dp),
                    color = Color(0xFF64748B),
                    style = MaterialTheme.typography.titleMedium
                )
            } else {
                groupedRows.forEach { row ->
                    W18InventoryLightGroupedDataRow(row = row)
                }
            }
        }
    }
}

@Composable
private fun W18InventoryLightGroupedDataRow(
    row: InventoryGroupedRow
) {
    val background = when (row.status) {
        "Ok" -> Color(0xFFBDE8B1)
        "Partial" -> Color(0xFFFFE08A)
        "Extra" -> Color(0xFFFFB4B4)
        else -> Color(0xFFFFCCA7)
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(background)
            .padding(horizontal = 8.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(
            modifier = Modifier.weight(1.35f)
        ) {
            Text(
                text = row.itemCode,
                color = Color.Black,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Bold
            )

            if (row.itemName.isNotBlank() && row.itemName != row.itemCode) {
                Text(
                    text = row.itemName,
                    color = Color(0xFF334155),
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }

        Text(
            text = formatInventoryQuantity(row.qty),
            modifier = Modifier.weight(0.55f),
            color = Color.Black,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center
        )

        Text(
            text = formatInventoryQuantity(row.read),
            modifier = Modifier.weight(0.55f),
            color = Color.Black,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center
        )

        Text(
            text = row.status,
            modifier = Modifier.weight(0.85f),
            color = Color.Black,
            style = MaterialTheme.typography.bodyLarge,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center
        )
    }
}

private fun buildInventoryGroupedRows(
    expectedAssets: List<ExpectedAssetInfo>,
    rfidTagsRead: List<RfidInventoryTag>,
    rfidScanValidations: Map<String, RfidScanValidation>
): List<InventoryGroupedRow> {
    data class MutableInventoryGroup(
        val itemCode: String,
        val itemName: String,
        var qty: Double = 0.0,
        var read: Double = 0.0
    )

    val groups = linkedMapOf<String, MutableInventoryGroup>()

    expectedAssets.forEach { asset ->
        val key = inventoryGroupedItemKey(asset)
        val qty = expectedQuantityForGroupedInventory(asset)
        val isRead = expectedAssetHasBeenRead(
            asset = asset,
            rfidTagsRead = rfidTagsRead,
            rfidScanValidations = rfidScanValidations
        )

        val group = groups.getOrPut(key) {
            MutableInventoryGroup(
                itemCode = inventoryGroupedItemDisplayCode(asset),
                itemName = asset.itemName
            )
        }

        group.qty += qty
        if (isRead) {
            group.read += qty
        }
    }

    return groups.values.map { group ->
        InventoryGroupedRow(
            itemCode = group.itemCode,
            itemName = group.itemName,
            qty = group.qty,
            read = group.read,
            status = inventoryGroupedStatus(group.qty, group.read)
        )
    }.sortedBy { row -> normalizeInventoryComparisonKey(row.itemCode) }
}

private fun expectedAssetHasBeenRead(
    asset: ExpectedAssetInfo,
    rfidTagsRead: List<RfidInventoryTag>,
    rfidScanValidations: Map<String, RfidScanValidation>
): Boolean {
    val matchedEpcs = rfidScanValidations
        .filter { (_, validation) -> expectedItemMatchesValidation(asset, validation) }
        .keys
        .map { normalizeRfidKey(it) }
        .toSet()

    if (matchedEpcs.isNotEmpty()) {
        return rfidTagsRead.any { tag -> normalizeRfidKey(tag.epc) in matchedEpcs } ||
                rfidScanValidations.values.any { validation -> expectedItemMatchesValidation(asset, validation) }
    }

    return rfidTagsRead.any { tag -> assetMatchesReadTag(asset, tag) }
}

private fun inventoryGroupedItemKey(asset: ExpectedAssetInfo): String {
    return listOf(
        asset.itemCode,
        asset.itemId.takeIf { it > 0 }?.toString().orEmpty(),
        asset.displayCode,
        asset.assetCode,
        asset.containerCode,
        asset.epc,
        asset.serialNumber
    ).firstOrNull { it.isNotBlank() }
        ?.let { normalizeInventoryComparisonKey(it) }
        ?: "${asset.objectType.uppercase(Locale.ROOT)}-${asset.id}"
}

private fun inventoryGroupedItemDisplayCode(asset: ExpectedAssetInfo): String {
    return listOf(
        asset.itemCode,
        asset.displayCode,
        asset.assetCode,
        asset.containerCode,
        asset.epc,
        asset.serialNumber
    ).firstOrNull { it.isNotBlank() }
        ?: "${asset.objectType.uppercase(Locale.ROOT)}-${asset.id}"
}

private fun expectedQuantityForGroupedInventory(asset: ExpectedAssetInfo): Double {
    val type = asset.objectType.lowercase(Locale.ROOT)

    return when (type) {
        // A container represents one physical RFID tag, even if the container has quantity 65,
        // 100 or whatever amount of screws, bolts or tiny metallic chaos inside it.
        // The inventory table is checking tag presence, not counting every unit inside the box.
        "container" -> 1.0

        // Stock rows can still represent quantity if the backend sends stock without a container.
        // If stock is also represented by a tagged container, it should arrive as objectType="container".
        "stock" -> asset.quantity?.takeIf { it > 0.0 } ?: 1.0

        else -> 1.0
    }
}

private fun inventoryGroupedStatus(qty: Double, read: Double): String {
    val cleanQty = qty.coerceAtLeast(0.0)
    val cleanRead = read.coerceAtLeast(0.0)
    val tolerance = 0.0001

    return when {
        cleanQty <= tolerance && cleanRead <= tolerance -> "Pending"
        cleanRead <= tolerance -> "Pending"
        cleanRead + tolerance < cleanQty -> "Partial"
        cleanRead <= cleanQty + tolerance -> "Ok"
        else -> "Extra"
    }
}

private fun formatInventoryQuantity(value: Double): String {
    val rounded = kotlin.math.round(value)

    return if (kotlin.math.abs(value - rounded) < 0.0001) {
        rounded.toLong().toString()
    } else {
        String.format(Locale.ROOT, "%.2f", value).trimEnd('0').trimEnd('.')
    }
}

@Composable
private fun W18InventoryLightStatus(
    statusText: String,
    rfidStatusText: String,
    lookupState: InventoryLookupState,
    expectedAssetsState: ExpectedAssetsState,
    submitState: InventorySubmitState,
    textColor: Color
) {
    val lines = mutableListOf<String>()

    when (lookupState) {
        InventoryLookupState.Idle -> Unit
        InventoryLookupState.Loading -> lines.add("Loading location...")
        is InventoryLookupState.Found -> lines.add("Selected: ${lookupState.location.code} - ${lookupState.location.name}".trim().trim('-').trim())
        is InventoryLookupState.NotFound -> lines.add("No active location found for: ${lookupState.barcode}")
        is InventoryLookupState.Error -> lines.add(lookupState.message)
    }

    when (expectedAssetsState) {
        ExpectedAssetsState.Idle -> Unit
        ExpectedAssetsState.Loading -> lines.add("Loading expected inventory...")
        is ExpectedAssetsState.Loaded -> lines.add("${expectedAssetsState.assets.size} expected item${if (expectedAssetsState.assets.size == 1) "" else "s"} loaded.")
        ExpectedAssetsState.Empty -> lines.add("Location loaded, but no expected items were returned.")
        is ExpectedAssetsState.Error -> lines.add(expectedAssetsState.message)
    }

    if (rfidStatusText.isNotBlank()) {
        lines.add(rfidStatusText)
    }

    when (submitState) {
        InventorySubmitState.Idle -> Unit
        InventorySubmitState.Submitting -> lines.add("Submitting inventory result...")
        is InventorySubmitState.Submitted -> lines.add(submitState.message)
        is InventorySubmitState.Error -> lines.add(submitState.message)
    }

    val text = lines.joinToString("\n").ifBlank { statusText }

    if (text.isNotBlank()) {
        Text(
            text = text,
            color = textColor,
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.Bold
        )
    }
}

private fun inventoryDisplayCode(asset: ExpectedAssetInfo): String {
    return listOf(
        asset.displayCode,
        asset.itemCode,
        asset.assetCode,
        asset.containerCode,
        asset.epc,
        asset.serialNumber
    ).firstOrNull { it.isNotBlank() } ?: "${asset.objectType.replaceFirstChar { it.titlecase(Locale.ROOT) }} #${asset.id}"
}

@Composable
private fun ChafonBarcodeReaderScreen(
    menuOption: MenuOption,
    capturedBarcode: String,
    barcodeCaptured: Boolean,
    statusText: String,
    resetCounter: Int,
    inventoryLookupState: InventoryLookupState,
    expectedAssetsState: ExpectedAssetsState,
    rfidTagsRead: List<RfidInventoryTag>,
    rfidScanValidations: Map<String, RfidScanValidation>,
    rfidStatusText: String,
    rfidRunning: Boolean,
    rfidConnecting: Boolean,
    inventorySubmitState: InventorySubmitState,
    locateStatusText: String,
    locateExpectedPrefix: String,
    locateTargetEpc: String,
    locateCandidates: List<LocateCandidate>,
    locateSearching: Boolean,
    locateRunning: Boolean,
    locateConnecting: Boolean,
    locateProximity: Int?,
    locateRssi: Int?,
    locateTargetReads: Int,
    locateRegisteredLocationState: LocateRegisteredLocationState,
    programStatusText: String,
    programDetectedTags: List<ProgramDetectedTag>,
    programDetectedEpc: String,
    programDetectedRssi: Int?,
    programTidHex: String,
    programTidTail: String,
    programGeneratedEpc: String,
    programReadingTag: Boolean,
    programConnecting: Boolean,
    programWritingTag: Boolean,
    programConfirmingWrite: Boolean,
    programTagProgrammed: Boolean,
    onStartProgramTagRead: () -> Unit,
    onSelectProgramDetectedTag: (String) -> Unit,
    onProgramTagWrite: () -> Unit,
    onStartLocateSearch: () -> Unit,
    onStartLocateCandidate: (String) -> Unit,
    onStopLocate: () -> Unit,
    onStartRfidInventory: () -> Unit,
    onStopRfidInventory: () -> Unit,
    onSubmitInventoryResult: () -> Unit,
    onNewInventory: () -> Unit,
    onReloadInventoryLocation: () -> Unit,
    onTriggerDetected: () -> Unit,
    onTriggerReleased: () -> Unit,
    onBarcodeCaptured: (String) -> Unit,
    onClearBarcode: () -> Unit,
    onBackToMenu: () -> Unit
) {
    val screenBusy = rfidRunning ||
            rfidConnecting ||
            locateSearching ||
            locateRunning ||
            locateConnecting ||
            programReadingTag ||
            programConnecting ||
            programWritingTag ||
            inventorySubmitState is InventorySubmitState.Submitting

    if (menuOption == MenuOption.InventoryByLocation) {
        W18InventoryByLocationLightScreen(
            capturedBarcode = capturedBarcode,
            barcodeCaptured = barcodeCaptured,
            statusText = statusText,
            resetCounter = resetCounter,
            inventoryLookupState = inventoryLookupState,
            expectedAssetsState = expectedAssetsState,
            rfidTagsRead = rfidTagsRead,
            rfidScanValidations = rfidScanValidations,
            rfidStatusText = rfidStatusText,
            rfidRunning = rfidRunning,
            rfidConnecting = rfidConnecting,
            inventorySubmitState = inventorySubmitState,
            screenBusy = screenBusy,
            onTriggerDetected = onTriggerDetected,
            onTriggerReleased = onTriggerReleased,
            onBarcodeCaptured = onBarcodeCaptured,
            onReloadInventoryLocation = onReloadInventoryLocation,
            onStartRfidInventory = onStartRfidInventory,
            onStopRfidInventory = onStopRfidInventory,
            onSubmitInventoryResult = onSubmitInventoryResult,
            onNewInventory = onNewInventory,
            onClearBarcode = onClearBarcode
        )
        return
    }

    if (menuOption == MenuOption.LocateItem) {
        W18LocateItemLightScreen(
            capturedBarcode = capturedBarcode,
            barcodeCaptured = barcodeCaptured,
            statusText = statusText,
            resetCounter = resetCounter,
            locateStatusText = locateStatusText,
            expectedPrefix = locateExpectedPrefix,
            targetEpc = locateTargetEpc,
            candidates = locateCandidates,
            searching = locateSearching,
            running = locateRunning,
            connecting = locateConnecting,
            proximity = locateProximity,
            rssi = locateRssi,
            locateTargetReads = locateTargetReads,
            registeredLocationState = locateRegisteredLocationState,
            screenBusy = screenBusy,
            onTriggerDetected = onTriggerDetected,
            onTriggerReleased = onTriggerReleased,
            onBarcodeCaptured = onBarcodeCaptured,
            onFindNearbyTags = onStartLocateSearch,
            onStartLocate = {
                if (locateTargetEpc.isNotBlank()) onStartLocateCandidate(locateTargetEpc)
            },
            onStopLocate = onStopLocate,
            onSelectCandidate = onStartLocateCandidate,
            onClearBarcode = onClearBarcode
        )
        return
    }

    if (menuOption == MenuOption.ProgramTag) {
        W18ProgramTagLightScreen(
            capturedBarcode = capturedBarcode,
            barcodeCaptured = barcodeCaptured,
            statusText = statusText,
            resetCounter = resetCounter,
            programStatusText = programStatusText,
            detectedTags = programDetectedTags,
            detectedEpc = programDetectedEpc,
            detectedRssi = programDetectedRssi,
            tidHex = programTidHex,
            tidTail = programTidTail,
            generatedEpc = programGeneratedEpc,
            readingTag = programReadingTag,
            connecting = programConnecting,
            writingTag = programWritingTag,
            confirmingWrite = programConfirmingWrite,
            programmed = programTagProgrammed,
            screenBusy = screenBusy,
            onTriggerDetected = onTriggerDetected,
            onTriggerReleased = onTriggerReleased,
            onBarcodeCaptured = onBarcodeCaptured,
            onReadTag = onStartProgramTagRead,
            onSelectTag = onSelectProgramDetectedTag,
            onProgramTag = onProgramTagWrite,
            onClearBarcode = onClearBarcode
        )
        return
    }

    W18ScreenContainer {
        W18Header(
            title = menuOption.title,
            subtitle = menuOption.prompt,
            imageRes = menuOption.imageRes
        )

        Spacer(modifier = Modifier.height(24.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(24.dp),
            border = BorderStroke(1.dp, W18Border),
            colors = CardDefaults.cardColors(
                containerColor = W18Panel
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Chafon Barcode Reader",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = W18Text
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = menuOption.barcodeLabel,
                    style = MaterialTheme.typography.bodyMedium,
                    color = W18MutedText
                )

                Spacer(modifier = Modifier.height(20.dp))

                ChafonBarcodeEditText(
                    modifier = Modifier.fillMaxWidth(),
                    inputHint = menuOption.prompt,
                    capturedBarcode = capturedBarcode,
                    barcodeCaptured = barcodeCaptured,
                    resetCounter = resetCounter,
                    onTriggerDetected = onTriggerDetected,
                    onBarcodeCaptured = onBarcodeCaptured
                )

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = statusText,
                    modifier = Modifier.fillMaxWidth(),
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = if (!barcodeCaptured) FontWeight.Bold else FontWeight.Normal,
                    color = if (!barcodeCaptured) W18Text else W18MutedText,
                    textAlign = TextAlign.Center
                )

                if (barcodeCaptured && capturedBarcode.isNotBlank()) {
                    Spacer(modifier = Modifier.height(16.dp))

                    W18CapturedBarcodeSummary(
                        menuOption = menuOption,
                        capturedBarcode = capturedBarcode
                    )

                    if (menuOption == MenuOption.InventoryByLocation) {
                        Spacer(modifier = Modifier.height(12.dp))

                        W18InventoryLocationLookupCard(
                            state = inventoryLookupState,
                            expectedAssetsState = expectedAssetsState,
                            rfidTagsRead = rfidTagsRead,
                            rfidScanValidations = rfidScanValidations,
                            rfidStatusText = rfidStatusText,
                            rfidRunning = rfidRunning,
                            rfidConnecting = rfidConnecting,
                            inventorySubmitState = inventorySubmitState,
                            onStartRfidInventory = onStartRfidInventory,
                            onStopRfidInventory = onStopRfidInventory,
                            onSubmitInventoryResult = onSubmitInventoryResult,
                            onNewInventory = onNewInventory
                        )
                    }

                    if (menuOption == MenuOption.LocateItem) {
                        Spacer(modifier = Modifier.height(12.dp))

                        W18LocateItemPanel(
                            statusText = locateStatusText,
                            expectedPrefix = locateExpectedPrefix,
                            targetEpc = locateTargetEpc,
                            candidates = locateCandidates,
                            searching = locateSearching,
                            running = locateRunning,
                            connecting = locateConnecting,
                            proximity = locateProximity,
                            rssi = locateRssi,
                            locateTargetReads = locateTargetReads,
                            onFindNearbyTags = onStartLocateSearch,
                            onStartLocate = {
                                if (locateTargetEpc.isNotBlank()) onStartLocateCandidate(locateTargetEpc)
                            },
                            onStopLocate = onStopLocate,
                            onSelectCandidate = onStartLocateCandidate
                        )
                    }

                    if (menuOption == MenuOption.ProgramTag) {
                        Spacer(modifier = Modifier.height(12.dp))

                        W18ProgramTagReadPanel(
                            statusText = programStatusText,
                            detectedTags = programDetectedTags,
                            detectedEpc = programDetectedEpc,
                            detectedRssi = programDetectedRssi,
                            tidHex = programTidHex,
                            tidTail = programTidTail,
                            generatedEpc = programGeneratedEpc,
                            readingTag = programReadingTag,
                            connecting = programConnecting,
                            writingTag = programWritingTag,
                            confirmingWrite = programConfirmingWrite,
                            programmed = programTagProgrammed,
                            barcode = capturedBarcode,
                            onReadTag = onStartProgramTagRead,
                            onSelectTag = onSelectProgramDetectedTag,
                            onProgramTag = onProgramTagWrite
                        )
                    }
                }

                Spacer(modifier = Modifier.height(18.dp))

                Button(
                    onClick = onClearBarcode,
                    enabled = !screenBusy,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = W18Blue,
                        contentColor = Color.White,
                        disabledContainerColor = Color(0xFF274333),
                        disabledContentColor = W18MutedText
                    )
                ) {
                    Text("Clear barcode")
                }

                Spacer(modifier = Modifier.height(10.dp))

                OutlinedButton(
                    onClick = onBackToMenu,
                    enabled = !screenBusy,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    border = BorderStroke(1.dp, W18Border),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = W18Text,
                        disabledContentColor = W18MutedText
                    )
                ) {
                    Text("Back to menu")
                }

                if (screenBusy) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Stop the current RFID operation before clearing or returning to the menu.",
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText,
                        textAlign = TextAlign.Center
                    )
                }
            }
        }
    }
}

@Composable
private fun W18LocateItemLightScreen(
    capturedBarcode: String,
    barcodeCaptured: Boolean,
    statusText: String,
    resetCounter: Int,
    locateStatusText: String,
    expectedPrefix: String,
    targetEpc: String,
    candidates: List<LocateCandidate>,
    searching: Boolean,
    running: Boolean,
    connecting: Boolean,
    proximity: Int?,
    rssi: Int?,
    locateTargetReads: Int,
    registeredLocationState: LocateRegisteredLocationState,
    screenBusy: Boolean,
    onTriggerDetected: () -> Unit,
    onTriggerReleased: () -> Unit,
    onBarcodeCaptured: (String) -> Unit,
    onFindNearbyTags: () -> Unit,
    onStartLocate: () -> Unit,
    onStopLocate: () -> Unit,
    onSelectCandidate: (String) -> Unit,
    onClearBarcode: () -> Unit
) {
    val lightBackground = Color(0xFFF5F8FB)
    val darkText = Color(0xFF263447)
    val mutedText = Color(0xFF617085)
    val instructionText = when {
        running -> "Locating the selected tag. Move slowly and follow the signal."
        connecting -> "Connecting RFID reader..."
        searching -> "Searching nearby RFID tags..."
        targetEpc.isNotBlank() -> "Tag selected. Locate mode starts automatically."
        barcodeCaptured -> "Barcode loaded. Find nearby tags, then tap one to locate it."
        else -> "Scan or type the item barcode first. Then search nearby tags and tap one to locate it."
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = lightBackground
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(lightBackground)
                .verticalScroll(rememberScrollState())
                .padding(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            horizontalAlignment = Alignment.Start
        ) {
            W18TopOperationLogo(
                imageRes = R.drawable.w18search,
                contentDescription = "W18 Search tag"
            )

            Text(
                text = instructionText,
                color = darkText,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                ChafonBarcodeEditText(
                    modifier = Modifier.weight(1f),
                    inputHint = "Barcode / Item / Asset",
                    capturedBarcode = capturedBarcode,
                    barcodeCaptured = barcodeCaptured,
                    resetCounter = resetCounter,
                    heightDp = 58,
                    cornerRadiusDp = 6,
                    textColorHex = "#333333",
                    hintColorHex = "#555B66",
                    backgroundColorHex = "#F5F8FB",
                    strokeColorHex = "#6D6F78",
                    onTriggerDetected = onTriggerDetected,
                    onTriggerReleased = onTriggerReleased,
                    onBarcodeCaptured = onBarcodeCaptured
                )

                W18RoundInventoryButton(
                    text = "×",
                    enabled = !screenBusy,
                    backgroundColor = Color(0xFF4B5C6E),
                    disabledBackgroundColor = Color(0xFFD7D9DD),
                    onClick = onClearBarcode
                )
            }

            W18LocateRegisteredLocationLightPanel(
                state = registeredLocationState,
                barcode = capturedBarcode
            )

            if (barcodeCaptured) {
                val selectedCandidate = candidates.firstOrNull { it.epc == targetEpc }
                val canFind = !searching && !running && !connecting


                if (running || connecting || proximity != null) {
                    W18LocateSignalLightCard(
                        proximity = proximity,
                        running = running,
                        rssi = rssi,
                        locateTargetReads = locateTargetReads,
                        selectedCandidate = selectedCandidate
                    )
                }

                if (running || connecting || searching) {
                    Button(
                        onClick = onStopLocate,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFFB91C1C),
                            contentColor = Color.White
                        )
                    ) {
                        Text(
                            when {
                                searching -> "Stop search"
                                connecting -> "Cancel locate"
                                else -> "Stop locate now"
                            },
                            fontWeight = FontWeight.Bold
                        )
                    }
                } else {
                    Button(
                        onClick = onFindNearbyTags,
                        enabled = canFind,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF1267B1),
                            contentColor = Color.White
                        )
                    ) {
                        Text("Find nearby tags", fontWeight = FontWeight.Bold)
                    }
                }

                if (candidates.isNotEmpty()) {
                    Text(
                        text = "Detected tag(s): ${candidates.size} · tap one to locate",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF082B4A)
                    )

                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        candidates.take(8).forEachIndexed { index, candidate ->
                            W18LocateCandidateLightRow(
                                candidate = candidate,
                                selected = candidate.epc == targetEpc,
                                suggested = index == 0 && targetEpc.isBlank(),
                                onSelect = { onSelectCandidate(candidate.epc) }
                            )
                        }
                    }
                } else {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(14.dp),
                        border = BorderStroke(1.dp, Color(0xFFD6E0EA)),
                        colors = CardDefaults.cardColors(containerColor = Color.White)
                    ) {
                        Text(
                            text = if (barcodeCaptured) "No nearby RFID tags detected yet." else "Scan a barcode to start.",
                            modifier = Modifier.padding(14.dp),
                            color = mutedText,
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                }
            }
        }
    }
}


private fun formatLocateLastMovement(value: String): String {
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
private fun W18LocateRegisteredLocationLightPanel(
    state: LocateRegisteredLocationState,
    barcode: String
) {
    if (state is LocateRegisteredLocationState.Idle && barcode.isBlank()) return

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, Color(0xFFD6E0EA)),
        colors = CardDefaults.cardColors(containerColor = Color.White)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            when (state) {
                LocateRegisteredLocationState.Idle -> {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Registered location:",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF082B4A)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Scan barcode first",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color(0xFF617085)
                        )
                    }
                }

                LocateRegisteredLocationState.Loading -> {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Registered location:",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF082B4A)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            color = Color(0xFF1267B1),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Checking...",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color(0xFF617085)
                        )
                    }
                }

                is LocateRegisteredLocationState.Found -> {
                    val info = state.info
                    val visibleLocationName = info.locationName.ifBlank {
                        info.locationLabel
                            .substringAfter(" - ", missingDelimiterValue = "")
                            .takeIf { value ->
                                value.isNotBlank() &&
                                        value != info.locationLabel &&
                                        !value.startsWith("Location ", ignoreCase = true)
                            }
                            .orEmpty()
                    }
                    val formattedLastMovement = formatLocateLastMovement(info.lastMovementAt)

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Registered location:",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF082B4A)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = visibleLocationName.ifBlank { "Location name not returned by backend" },
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = if (visibleLocationName.isBlank()) Color(0xFFB45309) else Color(0xFF15803D)
                        )
                    }

                    if (formattedLastMovement.isNotBlank()) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Last movement:",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF082B4A)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = formattedLastMovement,
                                style = MaterialTheme.typography.bodyMedium,
                                color = Color(0xFF334155),
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }

                is LocateRegisteredLocationState.NotFound -> {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Registered location:",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF082B4A)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Not found for ${state.barcode}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color(0xFFB45309),
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                is LocateRegisteredLocationState.Error -> {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Registered location:",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF082B4A)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Check failed",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color(0xFFB45309),
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Text(
                        text = state.message,
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFF617085)
                    )
                }
            }
        }
    }
}

@Composable
private fun W18LocateSignalLightCard(
    proximity: Int?,
    running: Boolean,
    rssi: Int?,
    locateTargetReads: Int,
    selectedCandidate: LocateCandidate?
) {
    val signal = proximity?.coerceIn(0, 100) ?: 0
    val signalLabel = locateSignalLabel(proximity, running)

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, Color(0xFFD6E0EA)),
        colors = CardDefaults.cardColors(containerColor = Color.White)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = if (proximity == null) "--%" else "$signal%",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF15803D)
            )
            Text(
                text = signalLabel,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF082B4A)
            )
            Spacer(modifier = Modifier.height(8.dp))
            LinearProgressIndicator(
                progress = { signal / 100f },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(12.dp)
                    .clip(RoundedCornerShape(8.dp)),
                color = Color(0xFF15803D),
                trackColor = Color(0xFFE2E8F0)
            )
        }
    }
}

@Composable
private fun W18LocateCandidateLightRow(
    candidate: LocateCandidate,
    selected: Boolean,
    suggested: Boolean,
    onSelect: () -> Unit
) {
    val signal = proximityFromRssiOrReads(candidate.rssi, candidate.reads)
    val title = when {
        selected -> "SELECTED"
        suggested -> "SUGGESTED · strongest signal"
        else -> "RFID tag"
    }

    Button(
        onClick = onSelect,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (selected) Color(0xFF1D8F3E) else Color.White,
            contentColor = if (selected) Color.White else Color(0xFF082B4A)
        ),
        border = BorderStroke(1.dp, if (selected) Color(0xFF1D8F3E) else Color(0xFFD6E0EA)),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(12.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold,
                color = if (selected) Color.White else Color(0xFF334155)
            )
            Text(
                text = "Signal: $signal%",
                style = MaterialTheme.typography.bodySmall,
                color = if (selected) Color(0xFFEAF8EE) else Color(0xFF617085)
            )
            Text(
                text = candidate.epc,
                style = MaterialTheme.typography.bodySmall,
                color = if (selected) Color.White else Color(0xFF334155)
            )
            if (candidate.decodedObjectCode.isNotBlank()) {
                Text(
                    text = candidate.decodedObjectCode,
                    style = MaterialTheme.typography.bodySmall,
                    color = if (selected) Color(0xFFEAF8EE) else Color(0xFF617085)
                )
            }
        }
    }
}

@Composable
private fun W18LocateItemPanel(
    statusText: String,
    expectedPrefix: String,
    targetEpc: String,
    candidates: List<LocateCandidate>,
    searching: Boolean,
    running: Boolean,
    connecting: Boolean,
    proximity: Int?,
    rssi: Int?,
    locateTargetReads: Int,
    onFindNearbyTags: () -> Unit,
    onStartLocate: () -> Unit,
    onStopLocate: () -> Unit,
    onSelectCandidate: (String) -> Unit
) {
    val canFind = !searching && !running && !connecting
    val canStartLocate = targetEpc.isNotBlank() && !searching && !running && !connecting
    val signal = proximity?.coerceIn(0, 100) ?: 0
    val signalLabel = locateSignalLabel(proximity, running)
    val selectedCandidate = candidates.firstOrNull { it.epc == targetEpc }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, W18Border),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF071525)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = "RFID tag location",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = W18Text
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = statusText,
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )

            if (expectedPrefix.isNotBlank()) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Expected prefix: $expectedPrefix",
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }

            if (targetEpc.isNotBlank()) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Target EPC:",
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Bold,
                    color = W18Text
                )
                Text(
                    text = targetEpc,
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White
                )
            }

            if (running || proximity != null) {
                Spacer(modifier = Modifier.height(12.dp))

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    border = BorderStroke(1.dp, W18Border),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF0B1D33))
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = if (proximity == null) "--%" else "$signal%",
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF8CFFB0)
                        )

                        Text(
                            text = signalLabel,
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = W18Text
                        )

                        Spacer(modifier = Modifier.height(8.dp))

                        LinearProgressIndicator(
                            progress = { signal / 100f },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(12.dp)
                                .clip(RoundedCornerShape(8.dp)),
                            color = Color(0xFF8CFFB0),
                            trackColor = Color(0xFF10243D)
                        )

                        Spacer(modifier = Modifier.height(8.dp))

                        Text(
                            text = buildString {
                                append("Reads: ")
                                append(locateTargetReads)
                                if (rssi != null) append(" · RSSI: $rssi")
                                if (selectedCandidate != null) {
                                    append(" · Last seen: ")
                                    append(formatLocateLastSeen(selectedCandidate.lastSeenAt))
                                }
                            },
                            style = MaterialTheme.typography.bodySmall,
                            color = W18MutedText
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            if (running || connecting || searching) {
                OutlinedButton(
                    onClick = onStopLocate,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    border = BorderStroke(1.dp, W18Border),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = W18Text
                    )
                ) {
                    Text(
                        text = when {
                            searching -> "Stop search"
                            connecting -> "Cancel locate"
                            else -> "Stop locate now"
                        }
                    )
                }
            } else {
                Button(
                    onClick = onFindNearbyTags,
                    enabled = canFind,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = W18Blue,
                        contentColor = Color.White
                    )
                ) {
                    Text(if (searching) "Searching..." else "Find nearby tags")
                }

                Spacer(modifier = Modifier.height(8.dp))

                Button(
                    onClick = onStartLocate,
                    enabled = canStartLocate,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF15803D),
                        contentColor = Color.White,
                        disabledContainerColor = Color(0xFF274333),
                        disabledContentColor = W18MutedText
                    )
                ) {
                    Text("Start locate")
                }
            }

            if (candidates.isNotEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = "Candidates",
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Bold,
                    color = W18Text
                )

                Spacer(modifier = Modifier.height(8.dp))

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    candidates.take(8).forEach { candidate ->
                        W18LocateCandidateRow(
                            candidate = candidate,
                            selected = candidate.epc == targetEpc,
                            onSelect = { onSelectCandidate(candidate.epc) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun W18LocateCandidateRow(
    candidate: LocateCandidate,
    selected: Boolean,
    onSelect: () -> Unit
) {
    val label = candidate.decodedObjectCode.ifBlank { candidate.epc }

    Button(
        onClick = onSelect,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (selected) Color(0xFF15803D) else Color(0xFF0B1D33),
            contentColor = Color.White
        ),
        border = BorderStroke(1.dp, W18Border),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(10.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = if (selected) "SELECTED · $label" else label,
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Reads: ${candidate.reads} · Signal: ${proximityFromRssiOrReads(candidate.rssi, candidate.reads)}%${candidate.rssi?.let { " · RSSI: $it" }.orEmpty()}",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )
            if (candidate.decodedObjectCode.isNotBlank()) {
                Text(
                    text = candidate.epc,
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }
        }
    }
}


@Composable
private fun W18ProgramTagLightScreen(
    capturedBarcode: String,
    barcodeCaptured: Boolean,
    statusText: String,
    resetCounter: Int,
    programStatusText: String,
    detectedTags: List<ProgramDetectedTag>,
    detectedEpc: String,
    detectedRssi: Int?,
    tidHex: String,
    tidTail: String,
    generatedEpc: String,
    readingTag: Boolean,
    connecting: Boolean,
    writingTag: Boolean,
    confirmingWrite: Boolean,
    programmed: Boolean,
    screenBusy: Boolean,
    onTriggerDetected: () -> Unit,
    onTriggerReleased: () -> Unit,
    onBarcodeCaptured: (String) -> Unit,
    onReadTag: () -> Unit,
    onSelectTag: (String) -> Unit,
    onProgramTag: () -> Unit,
    onClearBarcode: () -> Unit
) {
    val lightBackground = Color(0xFFF5F8FB)
    val darkText = Color(0xFF334155)
    val headerText = Color(0xFF082B4A)
    val mutedText = Color(0xFF64748B)
    val busy = readingTag || connecting || writingTag
    val currentEpc = normalizeRfidKey(detectedEpc)
    val newEpc = normalizeRfidKey(generatedEpc)
    val generatedEqualsCurrent = currentEpc.isNotBlank() && newEpc.isNotBlank() && currentEpc == newEpc
    val hasMultipleDetectedTags = detectedTags.size > 1
    val canReadTag = barcodeCaptured && capturedBarcode.isNotBlank() && !busy && !programmed
    val canProgram = generatedEpc.isNotBlank() &&
            detectedEpc.isNotBlank() &&
            !busy &&
            !generatedEqualsCurrent &&
            !programmed
    val sortedTags = detectedTags.sortedWith(
        compareByDescending<ProgramDetectedTag> { it.rssi ?: -999 }
            .thenByDescending { it.reads }
            .thenByDescending { it.lastSeenAt }
            .thenBy { it.epc }
    )
    val instructionText = when {
        writingTag -> "Programming tag. Keep only this tag close to the antenna."
        connecting -> "Connecting RFID reader..."
        readingTag -> "Reading nearby RFID tag. Keep only one tag close to the antenna."
        programmed -> "Tag programmed successfully. Press ✕ to start another tag."
        barcodeCaptured -> "Barcode loaded. Read one nearby RFID tag, review the EPC, then program it."
        else -> "Scan or type a barcode, read one nearby RFID tag, generate the EPC from barcode + TID, then program it."
    }
    val rfidTagValue = when {
        connecting -> "Connecting RFID reader..."
        readingTag -> "Reading nearby tag..."
        detectedEpc.isNotBlank() -> detectedEpc
        detectedTags.size > 1 -> "${detectedTags.size} tags detected. Select the correct one below."
        else -> "Waiting for tag..."
    }
    val generatedEpcValue = generatedEpc.ifBlank { "No EPC generated yet" }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = lightBackground
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(lightBackground)
                .verticalScroll(rememberScrollState())
                .padding(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            horizontalAlignment = Alignment.Start
        ) {
            W18TopOperationLogo(
                imageRes = R.drawable.w18program,
                contentDescription = "W18 Program tag"
            )

            Text(
                text = instructionText,
                color = darkText,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold
            )

            ChafonBarcodeEditText(
                modifier = Modifier.fillMaxWidth(),
                inputHint = "Barcode / Item / Asset",
                capturedBarcode = capturedBarcode,
                barcodeCaptured = barcodeCaptured,
                resetCounter = resetCounter,
                heightDp = 58,
                cornerRadiusDp = 6,
                textColorHex = "#333333",
                hintColorHex = "#555B66",
                backgroundColorHex = "#F5F8FB",
                strokeColorHex = "#6D6F78",
                onTriggerDetected = onTriggerDetected,
                onTriggerReleased = onTriggerReleased,
                onBarcodeCaptured = onBarcodeCaptured
            )

            W18ProgramLightInfoPanel(
                title = "RFID Tag",
                value = rfidTagValue
            )

            W18ProgramLightInfoPanel(
                title = "Generated EPC",
                value = generatedEpcValue
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = onReadTag,
                    enabled = canReadTag,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                    shape = RoundedCornerShape(12.dp),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF7C3AED),
                        contentColor = Color.White,
                        disabledContainerColor = Color(0xFFD7D9DD),
                        disabledContentColor = Color(0xFF9AA1AC)
                    )
                ) {
                    if (connecting || readingTag) {
                        Text("...", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleLarge)
                    } else {
                        Image(
                            painter = painterResource(id = R.drawable.ic_locate_tag),
                            contentDescription = "Read RFID tag",
                            modifier = Modifier.size(28.dp),
                            contentScale = ContentScale.Fit
                        )
                    }
                }

                Button(
                    onClick = onProgramTag,
                    enabled = canProgram,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                    shape = RoundedCornerShape(12.dp),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF15803D),
                        contentColor = Color.White,
                        disabledContainerColor = Color(0xFFD7D9DD),
                        disabledContentColor = Color(0xFF9AA1AC)
                    )
                ) {
                    when {
                        writingTag -> Text("...", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleLarge)
                        confirmingWrite -> Text("✓", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleLarge)
                        programmed -> Text("✓", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleLarge)
                        else -> Image(
                            painter = painterResource(id = R.drawable.ic_program_tag),
                            contentDescription = "Program tag",
                            modifier = Modifier.size(28.dp),
                            contentScale = ContentScale.Fit
                        )
                    }
                }

                Button(
                    onClick = onClearBarcode,
                    enabled = !screenBusy,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                    shape = RoundedCornerShape(12.dp),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF475569),
                        contentColor = Color.White,
                        disabledContainerColor = Color(0xFFD7D9DD),
                        disabledContentColor = Color(0xFF9AA1AC)
                    )
                ) {
                    Text("✕", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleLarge)
                }
            }

            if (busy) {
                LinearProgressIndicator(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(8.dp)),
                    color = Color(0xFF15803D),
                    trackColor = Color(0xFFDDE7F0)
                )
            }

            Text(
                text = programStatusText.ifBlank { statusText },
                color = darkText,
                style = MaterialTheme.typography.bodyMedium
            )

            if (sortedTags.isNotEmpty()) {
                W18ProgramDetectedTagsLightPanel(
                    detectedTags = sortedTags,
                    detectedEpc = detectedEpc,
                    busy = busy,
                    onSelectTag = onSelectTag
                )
            }

            if (capturedBarcode.isNotBlank() || detectedEpc.isNotBlank() || detectedRssi != null || tidHex.isNotBlank() || tidTail.isNotBlank()) {
                W18ProgramDetailsLightPanel(
                    barcode = capturedBarcode,
                    detectedEpc = detectedEpc,
                    detectedRssi = detectedRssi,
                    tidHex = tidHex,
                    tidTail = tidTail,
                    generatedEpc = generatedEpc,
                    programmed = programmed,
                    generatedEqualsCurrent = generatedEqualsCurrent,
                    hasMultipleDetectedTags = hasMultipleDetectedTags,
                    confirmingWrite = confirmingWrite
                )
            }
        }
    }
}

@Composable
private fun W18ProgramLightInfoPanel(
    title: String,
    value: String
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(10.dp))
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
private fun W18ProgramDetectedTagsLightPanel(
    detectedTags: List<ProgramDetectedTag>,
    detectedEpc: String,
    busy: Boolean,
    onSelectTag: (String) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(10.dp))
            .padding(10.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = "Detected tag(s): ${detectedTags.size}",
            color = Color(0xFF082B4A),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.bodyMedium
        )

        detectedTags.take(6).forEachIndexed { index, tag ->
            val selected = tag.epc == detectedEpc
            val signal = proximityFromRssiOrReads(tag.rssi, tag.reads)
            val title = when {
                selected -> "SELECTED"
                index == 0 && detectedTags.size > 1 -> "SUGGESTED · strongest signal"
                else -> "RFID tag"
            }

            Button(
                onClick = { onSelectTag(tag.epc) },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(10.dp),
                border = BorderStroke(1.dp, if (selected) Color(0xFF15803D) else Color(0xFFCBD5E1)),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(10.dp),
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
                        text = "Signal: $signal% · Reads: ${tag.reads}${tag.rssi?.let { " · RSSI: $it" }.orEmpty()}",
                        style = MaterialTheme.typography.bodySmall
                    )
                    Text(
                        text = tag.epc,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }

        if (detectedTags.size > 6) {
            Text(
                text = "+${detectedTags.size - 6} more tag(s). Move extra tags away and read again if needed.",
                color = Color(0xFF64748B),
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

@Composable
private fun W18ProgramDetailsLightPanel(
    barcode: String,
    detectedEpc: String,
    detectedRssi: Int?,
    tidHex: String,
    tidTail: String,
    generatedEpc: String,
    programmed: Boolean,
    generatedEqualsCurrent: Boolean,
    hasMultipleDetectedTags: Boolean,
    confirmingWrite: Boolean
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(10.dp))
            .padding(10.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Text(
            text = "Details",
            color = Color(0xFF082B4A),
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.bodyMedium
        )

        W18ProgramLightDetailLine("Barcode", barcode.trim().uppercase(Locale.ROOT))
        W18ProgramLightDetailLine("Current EPC", detectedEpc)
        if (detectedRssi != null) W18ProgramLightDetailLine("RSSI", detectedRssi.toString())
        W18ProgramLightDetailLine("TID", tidHex)
        W18ProgramLightDetailLine("TID tail", tidTail)
        W18ProgramLightDetailLine("New EPC", generatedEpc)

        if (generatedEpc.isNotBlank()) {
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = when {
                    programmed -> "Programmed. The write was verified by reading the new EPC again."
                    generatedEqualsCurrent -> "Warning: the generated EPC is already equal to the current EPC. The app will not send a write."
                    hasMultipleDetectedTags -> "Warning: multiple tags are near the antenna. Confirm that the selected tag is the correct one before programming."
                    confirmingWrite -> "Press ✓ again to confirm and write this EPC."
                    else -> "Before programming, keep only this tag close to the antenna. The app will ask for confirmation before writing."
                },
                color = when {
                    programmed -> Color(0xFF15803D)
                    generatedEqualsCurrent || hasMultipleDetectedTags || confirmingWrite -> Color(0xFFB45309)
                    else -> Color(0xFF64748B)
                },
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun W18ProgramLightDetailLine(
    label: String,
    value: String
) {
    if (value.isBlank()) return

    Text(
        text = label,
        color = Color(0xFF082B4A),
        fontWeight = FontWeight.Bold,
        style = MaterialTheme.typography.bodySmall
    )
    Text(
        text = value,
        color = Color(0xFF334155),
        style = MaterialTheme.typography.bodySmall
    )
}

@Composable
private fun W18ProgramTagReadPanel(
    statusText: String,
    detectedTags: List<ProgramDetectedTag>,
    detectedEpc: String,
    detectedRssi: Int?,
    tidHex: String,
    tidTail: String,
    generatedEpc: String,
    readingTag: Boolean,
    connecting: Boolean,
    writingTag: Boolean,
    confirmingWrite: Boolean,
    programmed: Boolean,
    barcode: String,
    onReadTag: () -> Unit,
    onSelectTag: (String) -> Unit,
    onProgramTag: () -> Unit
) {
    val busy = readingTag || connecting || writingTag
    val currentEpc = normalizeRfidKey(detectedEpc)
    val newEpc = normalizeRfidKey(generatedEpc)
    val generatedEqualsCurrent = currentEpc.isNotBlank() && newEpc.isNotBlank() && currentEpc == newEpc
    val hasMultipleDetectedTags = detectedTags.size > 1

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, W18Border),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF071525)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = "RFID tag detection",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = W18Text
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = statusText,
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )

            Spacer(modifier = Modifier.height(12.dp))

            Button(
                onClick = onReadTag,
                enabled = !busy,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = W18Blue,
                    contentColor = Color.White,
                    disabledContainerColor = Color(0xFF274333),
                    disabledContentColor = W18MutedText
                )
            ) {
                Text(
                    text = when {
                        connecting -> "Connecting..."
                        readingTag -> "Reading..."
                        else -> "Read RFID tag"
                    }
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            Button(
                onClick = onProgramTag,
                enabled = generatedEpc.isNotBlank() && detectedEpc.isNotBlank() && !busy && !generatedEqualsCurrent && !programmed,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF15803D),
                    contentColor = Color.White,
                    disabledContainerColor = Color(0xFF274333),
                    disabledContentColor = W18MutedText
                )
            ) {
                Text(
                    text = when {
                        writingTag -> "Programming..."
                        programmed -> "Programmed"
                        confirmingWrite -> "Confirm program"
                        generatedEqualsCurrent -> "No write needed"
                        generatedEpc.isNotBlank() -> "Program tag"
                        else -> "Program tag disabled"
                    }
                )
            }

            if (busy) {
                Spacer(modifier = Modifier.height(10.dp))
                LinearProgressIndicator(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(8.dp)),
                    color = Color(0xFF8CFFB0),
                    trackColor = Color(0xFF10243D)
                )
            }

            if (detectedTags.isNotEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))
                Text(
                    text = "Detected tag(s): ${detectedTags.size}",
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Bold,
                    color = W18Text
                )

                Spacer(modifier = Modifier.height(6.dp))

                val sortedTags = detectedTags.sortedWith(
                    compareByDescending<ProgramDetectedTag> { it.rssi ?: -999 }
                        .thenByDescending { it.reads }
                        .thenByDescending { it.lastSeenAt }
                        .thenBy { it.epc }
                )

                sortedTags.take(6).forEachIndexed { index, tag ->
                    val selected = tag.epc == detectedEpc
                    ProgramDetectedTagButton(
                        tag = tag,
                        selected = selected,
                        suggested = index == 0 && sortedTags.size > 1,
                        enabled = !busy,
                        onClick = { onSelectTag(tag.epc) }
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                }

                if (sortedTags.size > 6) {
                    Text(
                        text = "+${sortedTags.size - 6} more tag(s). Move extra tags away and read again if needed.",
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText
                    )
                }
            }

            if (barcode.isNotBlank()) {
                Spacer(modifier = Modifier.height(12.dp))
                W18ProgramInfoLine(label = "Barcode", value = barcode.trim().uppercase(Locale.ROOT))
            }

            if (detectedEpc.isNotBlank()) {
                Spacer(modifier = Modifier.height(8.dp))
                W18ProgramInfoLine(label = "Current EPC", value = detectedEpc)
            }

            if (detectedRssi != null) {
                W18ProgramInfoLine(label = "RSSI", value = detectedRssi.toString())
            }

            if (tidHex.isNotBlank()) {
                W18ProgramInfoLine(label = "TID", value = tidHex)
            }

            if (tidTail.isNotBlank()) {
                W18ProgramInfoLine(label = "TID tail", value = tidTail)
            }

            if (generatedEpc.isNotBlank()) {
                Spacer(modifier = Modifier.height(8.dp))
                W18ProgramInfoLine(label = "New EPC", value = generatedEpc)

                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = when {
                        programmed -> "Programmed. The write was verified by reading the new EPC again."
                        generatedEqualsCurrent -> "Warning: the generated EPC is already equal to the current EPC. The app will not send a write."
                        hasMultipleDetectedTags -> "Warning: multiple tags are near the antenna. Confirm that the selected tag is the correct one before programming."
                        else -> "Before pressing Program tag, keep only this tag close to the antenna. The app will ask for confirmation before writing and will verify by reading again."
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = when {
                        programmed -> Color(0xFF8CFFB0)
                        generatedEqualsCurrent || hasMultipleDetectedTags -> Color(0xFFFFC069)
                        else -> Color(0xFFFFD27A)
                    }
                )

                if (confirmingWrite) {
                    Spacer(modifier = Modifier.height(10.dp))
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(14.dp),
                        border = BorderStroke(1.dp, Color(0xFFFFC069)),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF2A1D05))
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Text(
                                text = "Program selected tag?",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFFFFD27A)
                            )
                            Text("Barcode: ${barcode.trim().uppercase(Locale.ROOT)}", style = MaterialTheme.typography.bodySmall, color = W18Text)
                            Text("Current EPC: $detectedEpc", style = MaterialTheme.typography.bodySmall, color = W18Text)
                            Text("New EPC: $generatedEpc", style = MaterialTheme.typography.bodySmall, color = W18Text)
                            Text("Selected RSSI: ${detectedRssi?.toString() ?: "Not available"}", style = MaterialTheme.typography.bodySmall, color = W18Text)
                            Text(
                                text = "Press Confirm program to write. Press Read RFID tag to cancel and choose again.",
                                style = MaterialTheme.typography.bodySmall,
                                color = W18MutedText
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ProgramDetectedTagButton(
    tag: ProgramDetectedTag,
    selected: Boolean,
    suggested: Boolean,
    enabled: Boolean,
    onClick: () -> Unit
) {
    val signal = proximityFromRssiOrReads(tag.rssi, tag.reads)
    val title = when {
        selected -> "SELECTED"
        suggested -> "SUGGESTED · strongest signal"
        else -> "RFID tag"
    }

    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (selected) Color(0xFF15803D) else Color(0xFF0B1D33),
            contentColor = Color.White,
            disabledContainerColor = if (selected) Color(0xFF15803D) else Color(0xFF1F2937),
            disabledContentColor = W18MutedText
        ),
        border = BorderStroke(1.dp, if (selected) Color(0xFF8CFFB0) else W18Border),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(10.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Signal: $signal% · Reads: ${tag.reads}${tag.rssi?.let { " · RSSI: $it" }.orEmpty()}",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )
            Text(
                text = tag.epc,
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )
        }
    }
}

@Composable
private fun W18ProgramInfoLine(
    label: String,
    value: String
) {
    Spacer(modifier = Modifier.height(8.dp))
    Text(
        text = label,
        style = MaterialTheme.typography.bodySmall,
        fontWeight = FontWeight.Bold,
        color = W18Text
    )
    Text(
        text = value,
        style = MaterialTheme.typography.bodySmall,
        color = W18MutedText
    )
}

@Composable
private fun W18InventoryLocationLookupCard(
    state: InventoryLookupState,
    expectedAssetsState: ExpectedAssetsState,
    rfidTagsRead: List<RfidInventoryTag>,
    rfidScanValidations: Map<String, RfidScanValidation>,
    rfidStatusText: String,
    rfidRunning: Boolean,
    rfidConnecting: Boolean,
    inventorySubmitState: InventorySubmitState,
    onStartRfidInventory: () -> Unit,
    onStopRfidInventory: () -> Unit,
    onSubmitInventoryResult: () -> Unit,
    onNewInventory: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, W18Border),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF071525)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = "Backend location check",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = W18Text
            )

            Spacer(modifier = Modifier.height(8.dp))

            when (state) {
                InventoryLookupState.Idle -> {
                    Text(
                        text = "Waiting for a location barcode.",
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText
                    )
                }

                InventoryLookupState.Loading -> {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            color = W18Blue,
                            strokeWidth = 2.dp
                        )

                        Spacer(modifier = Modifier.width(10.dp))

                        Text(
                            text = "Checking location in Warehouse18...",
                            style = MaterialTheme.typography.bodySmall,
                            color = W18MutedText
                        )
                    }
                }

                is InventoryLookupState.Found -> {
                    val location = state.location

                    Text(
                        text = location.name,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "ID: ${location.id}",
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText
                    )

                    Text(
                        text = "Code: ${location.code.ifBlank { "-" }}",
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText
                    )

                    Text(
                        text = "Type: ${location.type.ifBlank { "-" }}",
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText
                    )

                    Text(
                        text = "Active: ${if (location.isActive) "Yes" else "No"}",
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "Expected items for this location",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Bold,
                        color = W18Text
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    W18ExpectedAssetsList(
                        state = expectedAssetsState,
                        rfidScanValidations = rfidScanValidations
                    )

                    if (expectedAssetsState is ExpectedAssetsState.Loaded) {
                        Spacer(modifier = Modifier.height(12.dp))

                        W18RfidInventoryPanel(
                            expectedAssets = expectedAssetsState.assets,
                            rfidTagsRead = rfidTagsRead,
                            rfidScanValidations = rfidScanValidations,
                            rfidStatusText = rfidStatusText,
                            rfidRunning = rfidRunning,
                            rfidConnecting = rfidConnecting,
                            inventorySubmitState = inventorySubmitState,
                            onStartRfidInventory = onStartRfidInventory,
                            onStopRfidInventory = onStopRfidInventory,
                            onSubmitInventoryResult = onSubmitInventoryResult,
                            onNewInventory = onNewInventory
                        )
                    }
                }

                is InventoryLookupState.NotFound -> {
                    Text(
                        text = "No active location found for: ${state.barcode}",
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText
                    )
                }

                is InventoryLookupState.Error -> {
                    Text(
                        text = state.message,
                        style = MaterialTheme.typography.bodySmall,
                        color = W18MutedText
                    )
                }
            }
        }
    }
}

@Composable
private fun W18ExpectedAssetsList(
    state: ExpectedAssetsState,
    rfidScanValidations: Map<String, RfidScanValidation>
) {
    when (state) {
        ExpectedAssetsState.Idle -> {
            Text(
                text = "Waiting for expected items.",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )
        }

        ExpectedAssetsState.Loading -> {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    color = W18Blue,
                    strokeWidth = 2.dp
                )

                Spacer(modifier = Modifier.width(10.dp))

                Text(
                    text = "Loading handheld inventory from Warehouse18...",
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }
        }

        is ExpectedAssetsState.Loaded -> {
            val assets = state.assets

            Text(
                text = "${assets.size} expected item${if (assets.size == 1) "" else "s"}",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )

            Spacer(modifier = Modifier.height(10.dp))

            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                assets.forEach { asset ->
                    W18ExpectedAssetRow(
                        asset = asset,
                        found = rfidScanValidations.values.any { validation -> expectedItemMatchesValidation(asset, validation) }
                    )
                }
            }
        }

        ExpectedAssetsState.Empty -> {
            Text(
                text = "No expected assets, containers or stock found in this location.",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )
        }

        is ExpectedAssetsState.Error -> {
            Text(
                text = state.message,
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )
        }
    }
}

@Composable
private fun W18ExpectedAssetRow(
    asset: ExpectedAssetInfo,
    found: Boolean
) {
    val title = when {
        asset.displayCode.isNotBlank() -> asset.displayCode
        asset.assetCode.isNotBlank() -> asset.assetCode
        asset.containerCode.isNotBlank() -> asset.containerCode
        asset.epc.isNotBlank() -> asset.epc
        asset.serialNumber.isNotBlank() -> asset.serialNumber
        else -> "${asset.objectType.replaceFirstChar { it.titlecase(Locale.ROOT) }} #${asset.id}"
    }

    val itemLabel = when {
        asset.itemName.isNotBlank() && asset.itemCode.isNotBlank() -> "${asset.itemCode} - ${asset.itemName}"
        asset.itemName.isNotBlank() -> asset.itemName
        asset.itemCode.isNotBlank() -> asset.itemCode
        asset.itemId > 0 -> "Item ID: ${asset.itemId}"
        else -> "Item details not returned by backend"
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        border = BorderStroke(1.dp, W18Border),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF0B1D33)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = if (found) "FOUND" else "PENDING",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = if (found) Color(0xFF8CFFB0) else W18Text
                )

                Spacer(modifier = Modifier.width(10.dp))

                Text(
                    text = title,
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = itemLabel,
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )

            Text(
                text = "Type: ${asset.objectType.ifBlank { "asset" }}",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )

            asset.quantity?.let { quantity ->
                Text(
                    text = "Quantity: $quantity",
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }

            if (asset.serialNumber.isNotBlank()) {
                Text(
                    text = "Serial: ${asset.serialNumber}",
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }

            if (asset.status.isNotBlank()) {
                Text(
                    text = "Status: ${asset.status}",
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }
        }
    }
}


@Composable
private fun W18RfidInventoryPanel(
    expectedAssets: List<ExpectedAssetInfo>,
    rfidTagsRead: List<RfidInventoryTag>,
    rfidScanValidations: Map<String, RfidScanValidation>,
    rfidStatusText: String,
    rfidRunning: Boolean,
    rfidConnecting: Boolean,
    inventorySubmitState: InventorySubmitState,
    onStartRfidInventory: () -> Unit,
    onStopRfidInventory: () -> Unit,
    onSubmitInventoryResult: () -> Unit,
    onNewInventory: () -> Unit
) {
    val foundCount = expectedAssets.count { expected ->
        rfidScanValidations.values.any { validation -> expectedItemMatchesValidation(expected, validation) }
    }
    val issueCount = rfidScanValidations.values.count { validation ->
        validation.severity.equals("warning", ignoreCase = true) ||
                validation.severity.equals("error", ignoreCase = true)
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, W18Border),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF071525)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = "RFID inventory",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = W18Text
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Found $foundCount/${expectedAssets.size} expected items · Issues: $issueCount",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = rfidStatusText,
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )

            Spacer(modifier = Modifier.height(12.dp))

            if (rfidRunning || rfidConnecting) {
                OutlinedButton(
                    onClick = onStopRfidInventory,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    border = BorderStroke(1.dp, W18Border),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = W18Text
                    )
                ) {
                    Text(if (rfidConnecting) "Cancel RFID inventory" else "Stop RFID inventory")
                }
            } else {
                Button(
                    onClick = onStartRfidInventory,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = W18Blue,
                        contentColor = Color.White
                    )
                ) {
                    Text("Start RFID inventory")
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            val canSubmitInventory = expectedAssets.isNotEmpty() &&
                    !rfidRunning &&
                    !rfidConnecting &&
                    inventorySubmitState !is InventorySubmitState.Submitting &&
                    inventorySubmitState !is InventorySubmitState.Submitted

            Button(
                onClick = onSubmitInventoryResult,
                enabled = canSubmitInventory,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF15803D),
                    contentColor = Color.White,
                    disabledContainerColor = Color(0xFF274333),
                    disabledContentColor = W18MutedText
                )
            ) {
                Text(
                    text = if (inventorySubmitState is InventorySubmitState.Submitting) {
                        "Submitting..."
                    } else {
                        "✓ Submit inventory result"
                    },
                    fontWeight = FontWeight.Bold
                )
            }

            W18InventorySubmitStatus(state = inventorySubmitState)

            if (inventorySubmitState is InventorySubmitState.Submitted) {
                Spacer(modifier = Modifier.height(8.dp))
                Button(
                    onClick = onNewInventory,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = W18Blue,
                        contentColor = Color.White
                    )
                ) {
                    Text("New inventory")
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = "Each RFID tag is validated through Warehouse18 /validate-scan and submitted through /handheld-inventory/submit.",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )

            if (rfidTagsRead.isNotEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = "Read tags",
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Bold,
                    color = W18Text
                )

                Spacer(modifier = Modifier.height(8.dp))

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    rfidTagsRead.take(12).forEach { tag ->
                        val validation = rfidScanValidations[tag.epc]
                        W18ReadTagRow(tag = tag, validation = validation)
                    }
                }
            }
        }
    }
}

@Composable
private fun W18InventorySubmitStatus(
    state: InventorySubmitState
) {
    when (state) {
        InventorySubmitState.Idle -> Unit

        InventorySubmitState.Submitting -> {
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                CircularProgressIndicator(
                    modifier = Modifier.size(18.dp),
                    color = W18Blue,
                    strokeWidth = 2.dp
                )

                Spacer(modifier = Modifier.width(8.dp))

                Text(
                    text = "Sending inventory result to backend...",
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }
        }

        is InventorySubmitState.Submitted -> {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = state.message,
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF8CFFB0)
            )
        }

        is InventorySubmitState.Error -> {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = state.message,
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold,
                color = Color(0xFFFFC069)
            )
        }
    }
}

@Composable
private fun W18ReadTagRow(
    tag: RfidInventoryTag,
    validation: RfidScanValidation?
) {
    val label = when {
        validation == null -> "READ"
        validation.validation.equals("validating", ignoreCase = true) -> "VALIDATING"
        validation.validation.equals("expected", ignoreCase = true) -> "EXPECTED"
        validation.validation.equals("expected_stock_item", ignoreCase = true) -> "EXPECTED"
        else -> validation.validation.uppercase(Locale.ROOT)
    }

    val labelColor = when {
        validation == null -> W18Text
        validation.severity.equals("success", ignoreCase = true) -> Color(0xFF8CFFB0)
        validation.severity.equals("warning", ignoreCase = true) -> Color(0xFFFFC069)
        validation.severity.equals("error", ignoreCase = true) -> Color(0xFFFF8C8C)
        else -> W18Text
    }

    val mainText = validation?.displayCode
        ?.takeIf { it.isNotBlank() }
        ?: tag.decodedObjectCode.ifBlank { tag.epc }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp, W18Border),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF0B1D33)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = label,
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = labelColor
                )

                Spacer(modifier = Modifier.width(10.dp))

                Text(
                    text = mainText,
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }

            validation?.message?.takeIf { it.isNotBlank() }?.let { message ->
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = message,
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }

            if (tag.decodedObjectCode.isNotBlank()) {
                Text(
                    text = tag.epc,
                    style = MaterialTheme.typography.bodySmall,
                    color = W18MutedText
                )
            }

            Text(
                text = "Reads: ${tag.reads}${tag.rssi?.let { " · RSSI: $it" }.orEmpty()}",
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )
        }
    }
}

@Composable
private fun W18CapturedBarcodeSummary(
    menuOption: MenuOption,
    capturedBarcode: String
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, W18BlueDark),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF081B30)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = menuOption.resultTitle,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = W18Text
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = capturedBarcode,
                modifier = Modifier.fillMaxWidth(),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = menuOption.nextStepHint,
                style = MaterialTheme.typography.bodySmall,
                color = W18MutedText
            )
        }
    }
}

@Composable
private fun W18ScreenContainer(
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = W18Background
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(W18Background)
                .padding(22.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally,
                content = content
            )
        }
    }
}

@Composable
private fun W18Header(
    title: String,
    subtitle: String,
    imageRes: Int? = null
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        if (imageRes == null) {
            Image(
                painter = painterResource(id = R.drawable.logorfid2),
                contentDescription = "Warehouse18 logo",
                modifier = Modifier
                    .fillMaxWidth()
                    .height(82.dp),
                contentScale = ContentScale.Fit
            )
        } else {
            Image(
                painter = painterResource(id = imageRes),
                contentDescription = title,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(72.dp),
                contentScale = ContentScale.Fit
            )
        }

        Spacer(modifier = Modifier.height(14.dp))

        Text(
            text = title,
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = W18Text,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(6.dp))

        Text(
            text = subtitle,
            style = MaterialTheme.typography.bodyMedium,
            color = W18MutedText,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
private fun ChafonBarcodeEditText(
    modifier: Modifier = Modifier,
    inputHint: String,
    capturedBarcode: String,
    barcodeCaptured: Boolean,
    resetCounter: Int,
    heightDp: Int = 58,
    cornerRadiusDp: Int = 16,
    textColorHex: String = "#EAF2FF",
    hintColorHex: String = "#6F86A6",
    backgroundColorHex: String = "#0F1F36",
    strokeColorHex: String = "#1F4D82",
    onTriggerDetected: () -> Unit,
    onTriggerReleased: () -> Unit = {},
    onBarcodeCaptured: (String) -> Unit
) {
    val context = LocalContext.current
    val handler = remember { Handler(Looper.getMainLooper()) }

    val latestCapturedBarcode by rememberUpdatedState(capturedBarcode)
    val latestBarcodeCaptured by rememberUpdatedState(barcodeCaptured)
    val latestOnTriggerDetected by rememberUpdatedState(onTriggerDetected)
    val latestOnTriggerReleased by rememberUpdatedState(onTriggerReleased)
    val latestOnBarcodeCaptured by rememberUpdatedState(onBarcodeCaptured)

    var editTextRef by remember {
        mutableStateOf<EditText?>(null)
    }

    var appliedResetCounter by remember {
        mutableIntStateOf(resetCounter)
    }

    LaunchedEffect(editTextRef) {
        editTextRef?.let { editText ->
            editText.requestFocus()
            editText.setSelection(editText.text.length)
            hideSoftKeyboard(context, editText)
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            handler.removeCallbacksAndMessages(null)
        }
    }

    AndroidView(
        modifier = modifier
            .height(heightDp.dp)
            .clip(RoundedCornerShape(cornerRadiusDp.dp)),
        factory = { viewContext ->
            val editText = EditText(viewContext)
            var internalChange = false

            fun setTextSafely(value: String) {
                internalChange = true
                editText.setText(value)
                editText.setSelection(editText.text.length)
                internalChange = false

                editText.requestFocus()
                hideSoftKeyboard(viewContext, editText)
            }

            fun processCurrentText() {
                if (internalChange) return

                val raw = editText.text?.toString().orEmpty()

                if (raw.isBlank()) return

                if (containsScannerTriggerUpCode(raw)) {
                    latestOnTriggerReleased()
                    setTextSafely(if (latestBarcodeCaptured) latestCapturedBarcode else "")
                    return
                }

                if (containsScannerTriggerDownCode(raw) || isScannerTriggerOnly(raw)) {
                    latestOnTriggerDetected()
                    setTextSafely(if (latestBarcodeCaptured) latestCapturedBarcode else "")
                    return
                }

                val candidate = normalizeBarcodeCandidate(raw)

                if (candidate.isBlank()) return

                if (containsScannerTriggerUpCode(candidate)) {
                    latestOnTriggerReleased()
                    setTextSafely(if (latestBarcodeCaptured) latestCapturedBarcode else "")
                    return
                }

                if (isScannerTriggerOnly(candidate) || containsScannerTriggerDownCode(candidate)) {
                    latestOnTriggerDetected()
                    setTextSafely(if (latestBarcodeCaptured) latestCapturedBarcode else "")
                    return
                }

                if (latestBarcodeCaptured) {
                    setTextSafely(latestCapturedBarcode)
                    return
                }

                latestOnBarcodeCaptured(candidate)
                setTextSafely(candidate)
            }

            editText.apply {
                hint = inputHint
                isSingleLine = true
                inputType = InputType.TYPE_CLASS_TEXT
                gravity = Gravity.CENTER_VERTICAL
                textSize = 18f

                isFocusable = true
                isFocusableInTouchMode = true
                isEnabled = true
                isCursorVisible = true
                showSoftInputOnFocus = false

                setTextColor(android.graphics.Color.parseColor(textColorHex))
                setHintTextColor(android.graphics.Color.parseColor(hintColorHex))
                setPadding(18, 0, 18, 0)
                background = GradientDrawable().apply {
                    shape = GradientDrawable.RECTANGLE
                    cornerRadius = cornerRadiusDp * 3f
                    setColor(android.graphics.Color.parseColor(backgroundColorHex))
                    setStroke(2, android.graphics.Color.parseColor(strokeColorHex))
                }

                setOnFocusChangeListener { _, hasFocus ->
                    if (hasFocus) {
                        hideSoftKeyboard(viewContext, this)
                    }
                }

                setOnClickListener {
                    requestFocus()
                    hideSoftKeyboard(viewContext, this)
                }

                setOnKeyListener { _, keyCode, event ->
                    if (event.action == KeyEvent.ACTION_UP) {
                        handler.removeCallbacksAndMessages(null)
                        latestOnTriggerReleased()
                        return@setOnKeyListener true
                    }

                    if (isChafonTriggerKey(keyCode, event.scanCode)) {
                        when (event.action) {
                            KeyEvent.ACTION_DOWN -> {
                                handler.removeCallbacksAndMessages(null)
                                latestOnTriggerDetected()
                                return@setOnKeyListener true
                            }

                            KeyEvent.ACTION_UP -> {
                                handler.removeCallbacksAndMessages(null)
                                latestOnTriggerReleased()
                                return@setOnKeyListener true
                            }
                        }
                    }

                    if (event.action == KeyEvent.ACTION_DOWN) {
                        if (
                            keyCode == KeyEvent.KEYCODE_ENTER ||
                            keyCode == KeyEvent.KEYCODE_NUMPAD_ENTER ||
                            keyCode == KeyEvent.KEYCODE_TAB
                        ) {
                            handler.removeCallbacksAndMessages(null)
                            processCurrentText()
                            return@setOnKeyListener true
                        }
                    }

                    false
                }

                addTextChangedListener(object : TextWatcher {
                    override fun beforeTextChanged(
                        s: CharSequence?,
                        start: Int,
                        count: Int,
                        after: Int
                    ) {
                    }

                    override fun onTextChanged(
                        s: CharSequence?,
                        start: Int,
                        before: Int,
                        count: Int
                    ) {
                        if (internalChange) return

                        handler.removeCallbacksAndMessages(null)
                        handler.postDelayed({
                            processCurrentText()
                        }, 80)
                    }

                    override fun afterTextChanged(s: Editable?) {
                    }
                })

                requestFocus()
            }

            editTextRef = editText
            editText
        },
        update = { editText ->
            editText.requestFocus()
            hideSoftKeyboard(context, editText)

            if (appliedResetCounter != resetCounter) {
                appliedResetCounter = resetCounter
                editText.setText("")
            } else if (barcodeCaptured && capturedBarcode.isNotBlank()) {
                val current = editText.text?.toString().orEmpty()

                if (current != capturedBarcode) {
                    editText.setText(capturedBarcode)
                    editText.setSelection(editText.text.length)
                }
            }
        }
    )
}

private object Warehouse18Api {
    private var baseUrl: String = BACKEND_BASE_URL

    fun setBaseUrl(value: String) {
        baseUrl = value.trim().trimEnd('/').ifBlank { BACKEND_BASE_URL }
    }

    fun getBaseUrl(): String = baseUrl

    fun testConnection(testBaseUrl: String) {
        val url = URL("${testBaseUrl.trim().trimEnd('/')}/api/locations?page=1&page_size=1")
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 6000
            readTimeout = 6000
            setRequestProperty("Accept", "application/json")
        }

        val statusCode = connection.responseCode
        val body = if (statusCode in 200..299) {
            connection.inputStream.bufferedReader().use { it.readText() }
        } else {
            connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
        }

        connection.disconnect()

        if (statusCode !in 200..299) {
            throw RuntimeException("HTTP $statusCode${if (body.isNotBlank()) ": $body" else ""}")
        }
    }

    fun findRegisteredLocationForBarcode(barcode: String): LocateRegisteredLocationResult {
        val cleanBarcode = barcode.trim()
        if (cleanBarcode.isBlank()) return LocateRegisteredLocationResult.NotFound

        val encodedBarcode = URLEncoder.encode(cleanBarcode, "UTF-8")
        val candidateRequests = listOf(
            "/api/handheld/resolve-item?q=$encodedBarcode" to "",
            "/api/assets?q=$encodedBarcode&include_inactive=false&page=1&page_size=20" to "asset",
            "/api/stock-containers?q=$encodedBarcode&include_inactive=false&page=1&page_size=20" to "container",
            "/api/stock_containers?q=$encodedBarcode&include_inactive=false&page=1&page_size=20" to "container",
            "/api/items?q=$encodedBarcode&include_inactive=false&page=1&page_size=20" to "item"
        )

        var lastError = ""

        for ((path, fallbackType) in candidateRequests) {
            val response = runCatching { httpGetRaw(path) }.getOrElse { exception ->
                val message = exception.message.orEmpty()
                if (!message.contains("HTTP 404")) {
                    lastError = message.ifBlank { "Unknown backend error." }
                }
                null
            } ?: continue

            val candidates = parseRegisteredLocationCandidates(
                body = response,
                fallbackType = fallbackType
            )

            val selected = selectBestRegisteredLocationCandidate(
                candidates = candidates,
                barcode = cleanBarcode
            )

            if (selected != null) {
                return LocateRegisteredLocationResult.Success(
                    enrichRegisteredLocationIfNeeded(
                        info = selected,
                        barcode = cleanBarcode
                    )
                )
            }
        }

        return if (lastError.isNotBlank()) {
            LocateRegisteredLocationResult.Failure(lastError)
        } else {
            LocateRegisteredLocationResult.NotFound
        }
    }

    private fun enrichRegisteredLocationIfNeeded(
        info: LocateRegisteredLocationInfo,
        barcode: String
    ): LocateRegisteredLocationInfo {
        if (info.locationLabel.isNotBlank()) {
            return info
        }

        val searchText = listOf(
            info.itemCode,
            info.displayCode,
            barcode
        ).firstOrNull { value -> value.isNotBlank() } ?: barcode

        val encodedSearchText = URLEncoder.encode(searchText, "UTF-8")
        val candidatePaths = mutableListOf<String>()

        info.objectId?.takeIf { it > 0 }?.let { itemId ->
            candidatePaths.add("/api/inventory-stock?item_id=$itemId&page=1&page_size=20")
            candidatePaths.add("/api/inventory_stock?item_id=$itemId&page=1&page_size=20")
            candidatePaths.add("/api/inventory-stock/by-item/$itemId")
            candidatePaths.add("/api/inventory_stock/by-item/$itemId")
            candidatePaths.add("/api/stock?item_id=$itemId&page=1&page_size=20")
            candidatePaths.add("/api/stock-containers?item_id=$itemId&include_inactive=false&page=1&page_size=20")
            candidatePaths.add("/api/stock_containers?item_id=$itemId&include_inactive=false&page=1&page_size=20")
            candidatePaths.add("/api/assets?item_id=$itemId&include_inactive=false&page=1&page_size=20")
        }

        if (searchText.isNotBlank()) {
            candidatePaths.add("/api/inventory-stock?q=$encodedSearchText&page=1&page_size=20")
            candidatePaths.add("/api/inventory_stock?q=$encodedSearchText&page=1&page_size=20")
            candidatePaths.add("/api/stock?q=$encodedSearchText&page=1&page_size=20")
            candidatePaths.add("/api/movements?q=$encodedSearchText&page=1&page_size=20")
        }

        candidatePaths.distinct().forEach { path ->
            val response = runCatching { httpGetRaw(path) }.getOrNull() ?: return@forEach

            val candidates = parseRegisteredLocationCandidates(
                body = response,
                fallbackType = "stock"
            )

            val withLocation = candidates.firstOrNull { candidate ->
                candidate.locationLabel.isNotBlank() ||
                        candidate.locationCode.isNotBlank() ||
                        candidate.locationName.isNotBlank() ||
                        candidate.locationId != null
            } ?: return@forEach

            val finalLabel = withLocation.locationLabel.ifBlank {
                when {
                    withLocation.locationCode.isNotBlank() && withLocation.locationName.isNotBlank() -> "${withLocation.locationCode} - ${withLocation.locationName}"
                    withLocation.locationName.isNotBlank() -> withLocation.locationName
                    withLocation.locationCode.isNotBlank() -> withLocation.locationCode
                    withLocation.locationId != null -> "Location ${withLocation.locationId}"
                    else -> ""
                }
            }

            return info.copy(
                locationId = withLocation.locationId ?: info.locationId,
                locationCode = withLocation.locationCode.ifBlank { info.locationCode },
                locationName = withLocation.locationName.ifBlank { info.locationName },
                locationLabel = finalLabel,
                lastMovementAt = info.lastMovementAt.ifBlank { withLocation.lastMovementAt },
                epc = info.epc.ifBlank { withLocation.epc },
                objectId = info.objectId ?: withLocation.objectId
            )
        }

        return info
    }

    private fun httpGetRaw(path: String): String {
        val url = URL("$baseUrl$path")
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 6000
            readTimeout = 6000
            setRequestProperty("Accept", "application/json")
        }

        val statusCode = connection.responseCode
        val body = if (statusCode in 200..299) {
            connection.inputStream.bufferedReader().use { it.readText() }
        } else {
            connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
        }

        connection.disconnect()

        if (statusCode !in 200..299) {
            throw RuntimeException("HTTP $statusCode${if (body.isNotBlank()) ": $body" else ""}")
        }

        return body
    }

    private fun parseRegisteredLocationCandidates(
        body: String,
        fallbackType: String
    ): List<LocateRegisteredLocationInfo> {
        val cleanBody = body.trim()
        if (cleanBody.isBlank()) return emptyList()

        return runCatching {
            when {
                cleanBody.startsWith("[") -> parseRegisteredLocationArray(JSONArray(cleanBody), fallbackType)
                cleanBody.startsWith("{") -> {
                    val root = JSONObject(cleanBody)

                    if (looksLikeRegisteredLocationObject(root)) {
                        listOf(parseRegisteredLocationObject(root, fallbackType))
                    } else {
                        val arrays = listOfNotNull(
                            root.optJSONArray("items"),
                            root.optJSONArray("data"),
                            root.optJSONArray("results"),
                            root.optJSONArray("rows"),
                            root.optJSONArray("records"),
                            root.optJSONArray("assets"),
                            root.optJSONArray("containers"),
                            root.optJSONArray("stock_containers"),
                            root.optJSONArray("stockContainers"),
                            root.optJSONArray("objects"),
                            root.optJSONArray("stock"),
                            root.optJSONArray("inventory_stock"),
                            root.optJSONArray("inventoryStock"),
                            root.optJSONArray("stock_items"),
                            root.optJSONArray("stockItems"),
                            root.optJSONArray("movements")
                        )

                        val nestedData = root.optJSONObject("data")
                        val nestedArrays = if (nestedData != null) {
                            listOfNotNull(
                                nestedData.optJSONArray("items"),
                                nestedData.optJSONArray("results"),
                                nestedData.optJSONArray("rows"),
                                nestedData.optJSONArray("assets"),
                                nestedData.optJSONArray("containers"),
                                nestedData.optJSONArray("stock_containers"),
                                nestedData.optJSONArray("stockContainers"),
                                nestedData.optJSONArray("stock"),
                                nestedData.optJSONArray("inventory_stock"),
                                nestedData.optJSONArray("inventoryStock"),
                                nestedData.optJSONArray("stock_items"),
                                nestedData.optJSONArray("stockItems"),
                                nestedData.optJSONArray("movements")
                            )
                        } else {
                            emptyList()
                        }

                        (arrays + nestedArrays).flatMap { array ->
                            parseRegisteredLocationArray(array, fallbackType)
                        }
                    }
                }
                else -> emptyList()
            }
        }.getOrElse { emptyList() }
    }

    private fun parseRegisteredLocationArray(
        array: JSONArray,
        fallbackType: String
    ): List<LocateRegisteredLocationInfo> {
        val result = mutableListOf<LocateRegisteredLocationInfo>()

        for (index in 0 until array.length()) {
            val item = array.optJSONObject(index) ?: continue
            result.add(parseRegisteredLocationObject(item, fallbackType))
        }

        return result
    }

    private fun looksLikeRegisteredLocationObject(json: JSONObject): Boolean {
        return json.has("object_type") ||
                json.has("asset_code") ||
                json.has("container_code") ||
                json.has("item_code") ||
                json.has("itemCode") ||
                json.has("epc") ||
                json.has("location") ||
                json.has("current_location") ||
                json.has("asset_location") ||
                json.has("stock_location") ||
                json.has("container") ||
                json.has("asset")
    }

    private fun parseRegisteredLocationObject(
        json: JSONObject,
        fallbackType: String
    ): LocateRegisteredLocationInfo {
        val asset = json.optJSONObject("asset")
        val container = json.optJSONObject("container")
            ?: json.optJSONObject("stock_container")
            ?: json.optJSONObject("stockContainer")
        val item = json.optJSONObject("item")
            ?: asset?.optJSONObject("item")
            ?: container?.optJSONObject("item")

        val stockLocation = json.optJSONObject("stock_location")
            ?: json.optJSONObject("stockLocation")
            ?: json.optJSONObject("inventory_stock")
            ?: json.optJSONObject("inventoryStock")

        val assetLocation = json.optJSONObject("asset_location")
            ?: json.optJSONObject("assetLocation")

        val lastMovement = json.optJSONObject("last_movement")
            ?: json.optJSONObject("lastMovement")
            ?: json.optJSONObject("movement")
            ?: json.optJSONObject("latest_movement")
            ?: json.optJSONObject("latestMovement")

        val movementToLocation = lastMovement?.optJSONObject("to_location")
            ?: lastMovement?.optJSONObject("toLocation")
            ?: lastMovement?.optJSONObject("location")
            ?: lastMovement?.optJSONObject("destination_location")
            ?: lastMovement?.optJSONObject("destinationLocation")

        val movementFromLocation = lastMovement?.optJSONObject("from_location")
            ?: lastMovement?.optJSONObject("fromLocation")

        val objectType = json.optString("object_type")
            .ifBlank { json.optString("objectType") }
            .ifBlank { fallbackType }
            .ifBlank {
                when {
                    asset != null || json.has("asset_code") || json.has("assetCode") || json.has("asset_id") -> "asset"
                    container != null || json.has("container_code") || json.has("containerCode") || json.has("container_id") -> "container"
                    stockLocation != null || json.has("quantity") -> "stock"
                    else -> "item"
                }
            }

        val objectId = when {
            json.has("object_id") && !json.isNull("object_id") -> json.optInt("object_id")
            json.has("objectId") && !json.isNull("objectId") -> json.optInt("objectId")
            objectType.equals("asset", ignoreCase = true) && json.has("asset_id") && !json.isNull("asset_id") -> json.optInt("asset_id")
            objectType.equals("asset", ignoreCase = true) && asset?.has("id") == true -> asset?.optInt("id") ?: 0
            objectType.equals("container", ignoreCase = true) && json.has("container_id") && !json.isNull("container_id") -> json.optInt("container_id")
            objectType.equals("container", ignoreCase = true) && container?.has("id") == true -> container?.optInt("id") ?: 0
            objectType.equals("stock", ignoreCase = true) && json.has("stock_id") && !json.isNull("stock_id") -> json.optInt("stock_id")
            item?.has("id") == true -> item?.optInt("id") ?: 0
            json.has("item_id") && !json.isNull("item_id") -> json.optInt("item_id")
            json.has("itemId") && !json.isNull("itemId") -> json.optInt("itemId")
            json.has("id") && !json.isNull("id") -> json.optInt("id")
            else -> 0
        }.takeIf { it > 0 }

        val assetCode = json.optString("asset_code")
            .ifBlank { json.optString("assetCode") }
            .ifBlank { asset?.optString("asset_code", "").orEmpty() }
            .ifBlank { asset?.optString("assetCode", "").orEmpty() }
            .ifBlank { asset?.optString("code", "").orEmpty() }

        val containerCode = json.optString("container_code")
            .ifBlank { json.optString("containerCode") }
            .ifBlank { container?.optString("container_code", "").orEmpty() }
            .ifBlank { container?.optString("containerCode", "").orEmpty() }
            .ifBlank { container?.optString("code", "").orEmpty() }

        val itemCode = json.optString("item_code")
            .ifBlank { json.optString("itemCode") }
            .ifBlank { json.optString("part_number") }
            .ifBlank { json.optString("partNumber") }
            .ifBlank { item?.optString("item_code", "").orEmpty() }
            .ifBlank { item?.optString("itemCode", "").orEmpty() }
            .ifBlank { item?.optString("code", "").orEmpty() }

        val epc = json.optString("epc")
            .ifBlank { json.optString("rfid_epc") }
            .ifBlank { json.optString("rfidEpc") }
            .ifBlank { json.optString("tag") }
            .ifBlank { json.optString("barcode") }
            .ifBlank { asset?.optString("epc", "").orEmpty() }
            .ifBlank { asset?.optString("barcode", "").orEmpty() }
            .ifBlank { container?.optString("epc", "").orEmpty() }
            .ifBlank { container?.optString("barcode", "").orEmpty() }

        val displayCode = json.optString("display_code")
            .ifBlank { json.optString("displayCode") }
            .ifBlank { json.optString("resolved_key") }
            .ifBlank { json.optString("code") }
            .ifBlank { assetCode }
            .ifBlank { containerCode }
            .ifBlank { itemCode }
            .ifBlank { epc }

        val rawLocation = json.opt("location")
        val rawCurrentLocation = json.opt("current_location")
        val rawRegisteredLocation = json.opt("registered_location")
        val locationText = when {
            rawLocation is String -> rawLocation
            rawCurrentLocation is String -> rawCurrentLocation
            rawRegisteredLocation is String -> rawRegisteredLocation
            else -> ""
        }

        val locationObject = json.optJSONObject("location")
            ?: json.optJSONObject("current_location")
            ?: json.optJSONObject("currentLocation")
            ?: json.optJSONObject("registered_location")
            ?: json.optJSONObject("registeredLocation")
            ?: stockLocation?.optJSONObject("location")
            ?: stockLocation
            ?: assetLocation?.optJSONObject("location")
            ?: assetLocation
            ?: movementToLocation
            ?: movementFromLocation
            ?: asset?.optJSONObject("location")
            ?: asset?.optJSONObject("current_location")
            ?: container?.optJSONObject("location")
            ?: container?.optJSONObject("current_location")

        val locationId = when {
            locationObject != null && locationObject.has("id") -> locationObject.optInt("id")
            json.has("location_id") -> json.optInt("location_id")
            json.has("locationId") -> json.optInt("locationId")
            json.has("current_location_id") -> json.optInt("current_location_id")
            json.has("currentLocationId") -> json.optInt("currentLocationId")
            json.has("registered_location_id") -> json.optInt("registered_location_id")
            json.has("registeredLocationId") -> json.optInt("registeredLocationId")
            json.has("to_location_id") -> json.optInt("to_location_id")
            json.has("toLocationId") -> json.optInt("toLocationId")
            lastMovement != null && lastMovement.has("to_location_id") -> lastMovement.optInt("to_location_id")
            lastMovement != null && lastMovement.has("toLocationId") -> lastMovement.optInt("toLocationId")
            lastMovement != null && lastMovement.has("location_id") -> lastMovement.optInt("location_id")
            else -> null
        }?.takeIf { it > 0 }

        val locationCode = locationObject?.optString("code", "").orEmpty()
            .ifBlank { locationObject?.optString("location_code", "").orEmpty() }
            .ifBlank { json.optString("location_code") }
            .ifBlank { json.optString("locationCode") }
            .ifBlank { json.optString("current_location_code") }
            .ifBlank { json.optString("currentLocationCode") }
            .ifBlank { json.optString("registered_location_code") }
            .ifBlank { json.optString("registeredLocationCode") }
            .ifBlank { json.optString("to_location_code") }
            .ifBlank { json.optString("toLocationCode") }
            .ifBlank { lastMovement?.optString("to_location_code", "").orEmpty() }
            .ifBlank { lastMovement?.optString("toLocationCode", "").orEmpty() }

        val locationName = locationObject?.optString("name", "").orEmpty()
            .ifBlank { locationObject?.optString("location_name", "").orEmpty() }
            .ifBlank { json.optString("location_name") }
            .ifBlank { json.optString("locationName") }
            .ifBlank { json.optString("current_location_name") }
            .ifBlank { json.optString("currentLocationName") }
            .ifBlank { json.optString("registered_location_name") }
            .ifBlank { json.optString("registeredLocationName") }
            .ifBlank { json.optString("to_location_name") }
            .ifBlank { json.optString("toLocationName") }
            .ifBlank { lastMovement?.optString("to_location_name", "").orEmpty() }
            .ifBlank { lastMovement?.optString("toLocationName", "").orEmpty() }
            .ifBlank { locationText }

        val locationLabel = json.optString("location_label")
            .ifBlank { json.optString("locationLabel") }
            .ifBlank { json.optString("current_location_label") }
            .ifBlank { json.optString("currentLocationLabel") }
            .ifBlank { json.optString("registered_location_label") }
            .ifBlank { json.optString("registeredLocationLabel") }
            .ifBlank { json.optString("to_location_label") }
            .ifBlank { json.optString("toLocationLabel") }
            .ifBlank { lastMovement?.optString("to_location_label", "").orEmpty() }
            .ifBlank { lastMovement?.optString("toLocationLabel", "").orEmpty() }
            .ifBlank {
                when {
                    locationCode.isNotBlank() && locationName.isNotBlank() && locationCode != locationName -> "$locationCode - $locationName"
                    locationName.isNotBlank() -> locationName
                    locationCode.isNotBlank() -> locationCode
                    locationId != null -> "Location $locationId"
                    else -> ""
                }
            }

        val lastMovementAt = json.optString("last_movement_at")
            .ifBlank { json.optString("lastMovementAt") }
            .ifBlank { lastMovement?.optString("created_at", "").orEmpty() }
            .ifBlank { lastMovement?.optString("createdAt", "").orEmpty() }
            .ifBlank { lastMovement?.optString("at", "").orEmpty() }
            .ifBlank { json.optString("updated_at") }
            .ifBlank { json.optString("updatedAt") }
            .ifBlank { json.optString("since") }

        return LocateRegisteredLocationInfo(
            objectType = objectType,
            displayCode = displayCode,
            itemCode = itemCode,
            epc = epc,
            locationId = locationId,
            locationCode = locationCode,
            locationName = locationName,
            locationLabel = locationLabel,
            lastMovementAt = lastMovementAt,
            objectId = objectId
        )
    }

    private fun selectBestRegisteredLocationCandidate(
        candidates: List<LocateRegisteredLocationInfo>,
        barcode: String
    ): LocateRegisteredLocationInfo? {
        if (candidates.isEmpty()) return null

        val normalizedBarcode = normalizeInventoryComparisonKey(barcode)
        val normalizedHexBarcode = normalizeRfidKey(barcode)

        return candidates.firstOrNull { candidate ->
            val keys = listOf(
                candidate.displayCode,
                candidate.itemCode,
                candidate.epc
            ).map { normalizeInventoryComparisonKey(it) }

            normalizedBarcode in keys ||
                    normalizedHexBarcode.isNotBlank() && normalizeRfidKey(candidate.epc) == normalizedHexBarcode
        } ?: candidates.firstOrNull()
    }

    fun findLocationByName(locationName: String): LocationLookupResult {
        return try {
            val encodedLocation = URLEncoder.encode(locationName.trim(), "UTF-8")
            val url = URL("$baseUrl/api/locations?q=$encodedLocation&include_inactive=false&page=1&page_size=20")
            val connection = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 6000
                readTimeout = 6000
                setRequestProperty("Accept", "application/json")
            }

            val statusCode = connection.responseCode
            val body = if (statusCode in 200..299) {
                connection.inputStream.bufferedReader().use { it.readText() }
            } else {
                connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
            }

            connection.disconnect()

            if (statusCode !in 200..299) {
                return LocationLookupResult.Failure("HTTP $statusCode while checking location.")
            }

            val locations = parseLocationsResponse(body)
            val normalizedSearch = locationName.trim()

            val exactLocation = locations.firstOrNull { location ->
                location.name.equals(normalizedSearch, ignoreCase = true) ||
                        location.code.equals(normalizedSearch, ignoreCase = true)
            }

            if (exactLocation == null) {
                LocationLookupResult.NotFound
            } else {
                LocationLookupResult.Success(exactLocation)
            }
        } catch (exception: Exception) {
            LocationLookupResult.Failure(exception.message ?: "Unknown backend error.")
        }
    }

    fun findExpectedAssetsByLocation(locationId: Int): ExpectedAssetsLookupResult {
        return try {
            val url = URL("$baseUrl/api/locations/$locationId/handheld-inventory")
            val connection = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 6000
                readTimeout = 6000
                setRequestProperty("Accept", "application/json")
            }

            val statusCode = connection.responseCode
            val body = if (statusCode in 200..299) {
                connection.inputStream.bufferedReader().use { it.readText() }
            } else {
                connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
            }

            connection.disconnect()

            if (statusCode !in 200..299) {
                return ExpectedAssetsLookupResult.Failure("HTTP $statusCode while loading handheld inventory.")
            }

            ExpectedAssetsLookupResult.Success(parseHandheldInventoryResponse(body))
        } catch (exception: Exception) {
            ExpectedAssetsLookupResult.Failure(exception.message ?: "Unknown backend error while loading handheld inventory.")
        }
    }

    fun validateHandheldScanForLocation(
        locationId: Int,
        epc: String
    ): RfidScanValidationResult {
        return try {
            val url = URL("$baseUrl/api/locations/$locationId/handheld-inventory/validate-scan")
            val payload = JSONObject().apply {
                put("epc", epc)
                put("reader_id", "chafon-mobile")
                put("operator_id", JSONObject.NULL)
            }

            val connection = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 6000
                readTimeout = 6000
                doOutput = true
                setRequestProperty("Accept", "application/json")
                setRequestProperty("Content-Type", "application/json; charset=utf-8")
            }

            val bytes = payload.toString().toByteArray(Charsets.UTF_8)
            connection.outputStream.use { output -> output.write(bytes) }

            val statusCode = connection.responseCode
            val body = if (statusCode in 200..299) {
                connection.inputStream.bufferedReader().use { it.readText() }
            } else {
                connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
            }

            connection.disconnect()

            if (statusCode !in 200..299) {
                return RfidScanValidationResult.Failure("HTTP $statusCode while validating EPC${if (body.isNotBlank()) ": $body" else ""}")
            }

            RfidScanValidationResult.Success(parseRfidScanValidation(body, epc))
        } catch (exception: Exception) {
            RfidScanValidationResult.Failure(exception.message ?: "Unknown backend error while validating EPC.")
        }
    }

    fun submitInventoryByLocation(
        location: LocationInfo,
        expectedAssets: List<ExpectedAssetInfo>,
        readTags: List<RfidInventoryTag>,
        scanValidations: Map<String, RfidScanValidation>
    ): InventorySubmitResult {
        val path = "/api/locations/${location.id}/handheld-inventory/submit"
        val payload = buildInventorySubmitPayload(
            location = location,
            expectedAssets = expectedAssets,
            readTags = readTags,
            scanValidations = scanValidations
        )

        return try {
            val url = URL("$baseUrl$path")
            val connection = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 6000
                readTimeout = 6000
                doOutput = true
                setRequestProperty("Accept", "application/json")
                setRequestProperty("Content-Type", "application/json; charset=utf-8")
            }

            val bytes = payload.toString().toByteArray(Charsets.UTF_8)
            connection.outputStream.use { output -> output.write(bytes) }

            val statusCode = connection.responseCode
            val body = if (statusCode in 200..299) {
                connection.inputStream.bufferedReader().use { it.readText() }
            } else {
                connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
            }

            connection.disconnect()

            if (statusCode in 200..299) {
                InventorySubmitResult.Success(buildSubmitSuccessMessage(body, path))
            } else {
                InventorySubmitResult.Failure("HTTP $statusCode on $path${if (body.isNotBlank()) ": $body" else ""}")
            }
        } catch (exception: Exception) {
            InventorySubmitResult.Failure(exception.message ?: "Unknown submit error on $path.")
        }
    }

    private fun buildInventorySubmitPayload(
        location: LocationInfo,
        expectedAssets: List<ExpectedAssetInfo>,
        readTags: List<RfidInventoryTag>,
        scanValidations: Map<String, RfidScanValidation>
    ): JSONObject {
        val rows = JSONArray()
        var foundCount = 0

        expectedAssets.forEach { asset ->
            val matchingTags = matchingReadTagsForExpected(
                expected = asset,
                readTags = readTags,
                scanValidations = scanValidations
            )

            val found = matchingTags.isNotEmpty()
            if (found) foundCount += 1

            rows.put(
                JSONObject().apply {
                    put("item_code", submitRowCodeForExpected(asset))
                    put("reads", matchingTags.sumOf { it.reads })
                    put("status", if (found) "OK" else "PENDING")
                }
            )
        }

        val pendingCount = expectedAssets.size - foundCount
        val label = when {
            location.code.isNotBlank() && location.name.isNotBlank() -> "${location.code} - ${location.name}"
            location.name.isNotBlank() -> location.name
            location.code.isNotBlank() -> location.code
            else -> "Location ${location.id}"
        }

        return JSONObject().apply {
            put("location_id", location.id)
            put("location_label", label)
            put("reader_id", "chafon-mobile")
            put("total_items", expectedAssets.size)
            put("ok_items", foundCount)
            put("pending_items", pendingCount)
            put("rows", rows)
        }
    }

    private fun matchingReadTagsForExpected(
        expected: ExpectedAssetInfo,
        readTags: List<RfidInventoryTag>,
        scanValidations: Map<String, RfidScanValidation>
    ): List<RfidInventoryTag> {
        val backendMatchedEpcs = scanValidations
            .filter { (_, validation) -> expectedItemMatchesValidation(expected, validation) }
            .keys
            .map { normalizeRfidKey(it) }
            .toSet()

        val backendMatches = readTags.filter { tag -> normalizeRfidKey(tag.epc) in backendMatchedEpcs }

        if (backendMatches.isNotEmpty()) {
            return backendMatches
        }

        return readTags.filter { tag -> assetMatchesReadTag(expected, tag) }
    }

    private fun submitRowCodeForExpected(expected: ExpectedAssetInfo): String {
        return listOf(
            expected.itemCode,
            expected.displayCode,
            expected.assetCode,
            expected.containerCode,
            expected.epc,
            expected.serialNumber
        ).firstOrNull { value -> value.isNotBlank() }
            ?: "${expected.objectType.uppercase(Locale.ROOT)}-${expected.id}"
    }

    private fun buildSubmitSuccessMessage(body: String, path: String): String {
        val cleanBody = body.trim()
        if (cleanBody.isBlank()) return "Inventory submitted successfully."

        return runCatching {
            val json = JSONObject(cleanBody)
            val auditId = json.optString("audit_id", json.optString("id", ""))
            val message = json.optString("message", "Inventory submitted successfully.")

            if (auditId.isNotBlank()) {
                "$message Audit ID: $auditId"
            } else {
                message
            }
        }.getOrElse {
            "Inventory submitted successfully via $path."
        }
    }

    private fun parseLocationsResponse(body: String): List<LocationInfo> {
        val cleanBody = body.trim()

        if (cleanBody.isBlank()) return emptyList()

        return when {
            cleanBody.startsWith("[") -> parseLocationsArray(JSONArray(cleanBody))
            cleanBody.startsWith("{") -> {
                val root = JSONObject(cleanBody)

                if (root.has("id")) {
                    listOf(parseLocationObject(root))
                } else {
                    val array = root.optJSONArray("items")
                        ?: root.optJSONArray("data")
                        ?: root.optJSONArray("results")
                        ?: root.optJSONArray("rows")
                        ?: root.optJSONArray("records")
                        ?: root.optJSONArray("locations")
                        ?: JSONArray()

                    parseLocationsArray(array)
                }
            }
            else -> emptyList()
        }
    }

    private fun parseLocationsArray(array: JSONArray): List<LocationInfo> {
        val locations = mutableListOf<LocationInfo>()

        for (index in 0 until array.length()) {
            val item = array.optJSONObject(index) ?: continue
            locations.add(parseLocationObject(item))
        }

        return locations
    }

    private fun parseLocationObject(json: JSONObject): LocationInfo {
        return LocationInfo(
            id = json.optInt("id", 0),
            code = json.optString("code", ""),
            name = json.optString("name", ""),
            type = json.optString("type", ""),
            isActive = json.optBoolean("is_active", true)
        )
    }

    private fun parseHandheldInventoryResponse(body: String): List<ExpectedAssetInfo> {
        val cleanBody = body.trim()
        if (cleanBody.isBlank()) return emptyList()

        val root = JSONObject(cleanBody)
        val expected = mutableListOf<ExpectedAssetInfo>()

        val assets = root.optJSONArray("assets") ?: JSONArray()
        for (index in 0 until assets.length()) {
            val asset = assets.optJSONObject(index) ?: continue
            expected.add(parseHandheldAssetObject(asset))
        }

        val containers = root.optJSONArray("containers") ?: JSONArray()
        for (index in 0 until containers.length()) {
            val container = containers.optJSONObject(index) ?: continue
            expected.add(parseHandheldContainerObject(container))
        }

        val stockItems = root.optJSONArray("stock_items") ?: JSONArray()
        for (index in 0 until stockItems.length()) {
            val stock = stockItems.optJSONObject(index) ?: continue
            expected.add(parseHandheldStockObject(stock))
        }

        return expected
    }

    private fun parseHandheldAssetObject(json: JSONObject): ExpectedAssetInfo {
        val nestedItem = json.optJSONObject("item")
        val assetCode = json.optString("asset_code", "")

        return ExpectedAssetInfo(
            id = json.optInt("asset_id", json.optInt("id", 0)),
            objectType = "asset",
            displayCode = assetCode,
            assetCode = assetCode,
            containerCode = "",
            itemId = nestedItem?.optInt("id", 0) ?: json.optInt("item_id", 0),
            itemCode = nestedItem?.optString("item_code", "").orEmpty(),
            itemName = nestedItem?.optString("name", "").orEmpty(),
            serialNumber = json.optString("serial_number", ""),
            status = json.optString("status", ""),
            epc = json.optString("epc", json.optString("barcode", json.optString("tag", ""))),
            quantity = null
        )
    }

    private fun parseHandheldContainerObject(json: JSONObject): ExpectedAssetInfo {
        val nestedItem = json.optJSONObject("item")
        val containerCode = json.optString("container_code", "")

        return ExpectedAssetInfo(
            id = json.optInt("container_id", json.optInt("id", 0)),
            objectType = "container",
            displayCode = containerCode,
            assetCode = "",
            containerCode = containerCode,
            itemId = nestedItem?.optInt("id", 0) ?: json.optInt("item_id", 0),
            itemCode = nestedItem?.optString("item_code", "").orEmpty(),
            itemName = nestedItem?.optString("name", "").orEmpty(),
            serialNumber = "",
            status = json.optString("status", json.optString("container_status", "")),
            epc = json.optString("epc", json.optString("barcode", json.optString("tag", ""))),
            quantity = if (json.has("quantity") && !json.isNull("quantity")) json.optDouble("quantity") else null
        )
    }

    private fun parseHandheldStockObject(json: JSONObject): ExpectedAssetInfo {
        val nestedItem = json.optJSONObject("item")
        val itemCode = nestedItem?.optString("item_code", "").orEmpty()

        return ExpectedAssetInfo(
            id = json.optInt("stock_id", json.optInt("id", 0)),
            objectType = "stock",
            displayCode = itemCode,
            assetCode = "",
            containerCode = "",
            itemId = nestedItem?.optInt("id", 0) ?: json.optInt("item_id", 0),
            itemCode = itemCode,
            itemName = nestedItem?.optString("name", "").orEmpty(),
            serialNumber = "",
            status = "stock",
            epc = json.optString("epc", json.optString("barcode", json.optString("tag", ""))),
            quantity = if (json.has("quantity") && !json.isNull("quantity")) json.optDouble("quantity") else null
        )
    }

    private fun parseRfidScanValidation(body: String, fallbackEpc: String): RfidScanValidation {
        val json = JSONObject(body.trim())
        val item = json.optJSONObject("item")
        val objectType = json.optString("object_type", "")
        val assetCode = json.optString("asset_code", "")
        val containerCode = json.optString("container_code", "")
        val itemCode = item?.optString("item_code", "").orEmpty()
        val resolvedKey = json.optString("resolved_key", "")
        val displayCode = when {
            assetCode.isNotBlank() -> assetCode
            containerCode.isNotBlank() -> containerCode
            resolvedKey.isNotBlank() -> resolvedKey
            itemCode.isNotBlank() -> itemCode
            else -> json.optString("epc", fallbackEpc)
        }

        return RfidScanValidation(
            epc = json.optString("epc", fallbackEpc),
            status = json.optString("status", ""),
            validation = json.optString("validation", ""),
            severity = json.optString("severity", ""),
            message = json.optString("message", ""),
            objectType = objectType,
            assetId = if (json.has("asset_id") && !json.isNull("asset_id")) json.optInt("asset_id") else null,
            containerId = if (json.has("container_id") && !json.isNull("container_id")) json.optInt("container_id") else null,
            itemId = item?.optInt("id", 0)?.takeIf { it > 0 },
            resolvedKey = resolvedKey,
            assetCode = assetCode,
            containerCode = containerCode,
            itemCode = itemCode,
            displayCode = displayCode
        )
    }

}

private fun expectedItemMatchesValidation(expected: ExpectedAssetInfo, validation: RfidScanValidation): Boolean {
    val validationKey = validation.validation.lowercase(Locale.ROOT)
    if (validationKey != "expected" && validationKey != "expected_stock_item") return false

    return when (expected.objectType.lowercase(Locale.ROOT)) {
        "asset" -> validation.assetId != null && validation.assetId == expected.id
        "container" -> validation.containerId != null && validation.containerId == expected.id
        "stock" -> {
            val sameItemId = expected.itemId > 0 && validation.itemId != null && validation.itemId == expected.itemId
            val sameItemCode = expected.itemCode.isNotBlank() &&
                    validation.itemCode.isNotBlank() &&
                    normalizeInventoryComparisonKey(expected.itemCode) == normalizeInventoryComparisonKey(validation.itemCode)
            sameItemId || sameItemCode
        }
        else -> {
            val expectedKeys = buildExpectedAssetKeys(expected)
            val validationKeys = buildValidationKeys(validation)
            expectedKeys.isNotEmpty() && expectedKeys.any { key -> key in validationKeys }
        }
    }
}

private fun buildValidationKeys(validation: RfidScanValidation): Set<String> {
    return listOf(
        validation.epc,
        validation.resolvedKey,
        validation.displayCode,
        validation.assetCode,
        validation.containerCode,
        validation.itemCode
    ).mapNotNull { value ->
        normalizeInventoryComparisonKey(value).takeIf { it.isNotBlank() }
    }.toSet()
}

private fun assetMatchesReadTag(asset: ExpectedAssetInfo, tag: RfidInventoryTag): Boolean {
    val expectedKeys = buildExpectedAssetKeys(asset)
    if (expectedKeys.isEmpty()) return false

    val readKeys = buildReadTagKeys(tag)
    return expectedKeys.any { key -> key in readKeys }
}

private fun buildExpectedAssetKeys(asset: ExpectedAssetInfo): Set<String> {
    return listOf(
        asset.epc,
        asset.displayCode,
        asset.assetCode,
        asset.containerCode,
        asset.itemCode,
        asset.serialNumber
    ).mapNotNull { value ->
        normalizeInventoryComparisonKey(value).takeIf { it.isNotBlank() }
    }.toSet()
}

private fun buildReadTagKeys(tag: RfidInventoryTag): Set<String> {
    return listOf(
        tag.epc,
        tag.decodedObjectCode
    ).mapNotNull { value ->
        normalizeInventoryComparisonKey(value).takeIf { it.isNotBlank() }
    }.toSet()
}

private fun normalizeRfidKey(value: String): String {
    return value
        .trim()
        .replace(" ", "")
        .replace(":", "")
        .replace("-", "")
        .uppercase(Locale.ROOT)
}

private fun normalizeInventoryComparisonKey(value: String): String {
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

private fun classCodeFromBarcode(barcode: String): String {
    val value = barcode.trim().uppercase(Locale.ROOT)

    return when {
        value.startsWith("CN235") || value.startsWith("235") -> "0B"
        value.startsWith("C295") || value.startsWith("295") -> "09"
        value.startsWith("A400M") -> "02"
        value.startsWith("A400") -> "03"
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

private fun looksLikeWarehouse18FullEpc(value: String): Boolean {
    val clean = normalizeRfidKey(value)
    return clean.startsWith("18") &&
            clean.length == 24 &&
            clean.length % 4 == 0 &&
            Regex("^[0-9A-Fa-f]+$").matches(clean) &&
            hasValidWarehouse18Checksum(clean)
}

private fun hasValidWarehouse18Checksum(epc: String): Boolean {
    val clean = normalizeRfidKey(epc)

    if (clean.length < 4 || clean.length % 2 != 0) return false

    val body = clean.dropLast(2)
    val expectedChecksum = clean.takeLast(2)

    return runCatching { xorChecksumHex(body) == expectedChecksum }.getOrDefault(false)
}

private fun generateWarehouse18EpcFromBarcodeAndTid(barcode: String, tidHex: String): String {
    val cleanBarcode = barcode.trim().uppercase(Locale.ROOT)
    val cleanTid = normalizeRfidKey(tidHex)

    if (cleanTid.length < 12) {
        throw RuntimeException("TID is too short. Expected at least 6 bytes, got: $cleanTid")
    }

    val classCode = classCodeFromBarcode(cleanBarcode)
    val objectIdHex = objectIdFromBarcode(cleanBarcode)
        .toString(16)
        .uppercase(Locale.ROOT)
        .padStart(6, '0')
        .takeLast(6)
    val tidTail = cleanTid.takeLast(12)
    val body = "18$classCode$objectIdHex$tidTail"

    if (body.length != 22 || !Regex("^[0-9A-Fa-f]+$").matches(body)) {
        throw RuntimeException("Generated EPC body is invalid: $body")
    }

    return body + xorChecksumHex(body)
}

private fun xorChecksumHex(hexWithoutChecksum: String): String {
    if (hexWithoutChecksum.length % 2 != 0) {
        throw RuntimeException("Checksum input must have even hex length.")
    }

    var checksum = 0

    for (index in hexWithoutChecksum.indices step 2) {
        val byteValue = hexWithoutChecksum.substring(index, index + 2).toInt(16)
        checksum = checksum xor byteValue
    }

    return checksum.toString(16).uppercase(Locale.ROOT).padStart(2, '0')
}


private fun locateSignalLabel(proximity: Int?, running: Boolean): String {
    if (proximity == null) {
        return if (running) "Waiting for target" else "No signal"
    }

    return when (proximity.coerceIn(0, 100)) {
        in 0..20 -> "Very far"
        in 21..45 -> "Far"
        in 46..70 -> "Getting closer"
        in 71..90 -> "Close"
        else -> "Very close"
    }
}

private fun formatLocateLastSeen(timestampMs: Long): String {
    val ageMs = (System.currentTimeMillis() - timestampMs).coerceAtLeast(0L)

    return when {
        ageMs < 1_500L -> "now"
        ageMs < 60_000L -> "${ageMs / 1_000L}s ago"
        else -> ">1 min ago"
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
        val alpha = if (median > previous) {
            0.35f
        } else {
            0.18f
        }

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

private fun proximityFromRssiOrReads(rssi: Int?, reads: Int): Int {
    return if (rssi != null) {
        rssiToProximityPercent(rssi)
    } else {
        (reads * 8).coerceIn(5, 100)
    }
}

private fun rssiToProximityPercent(rssi: Int): Int {
    /*
     * RSSI is not a distance percentage.
     *
     * Chafon normally reports a positive signal strength value, while many readers
     * report negative dBm values. In both cases we normalize the value to a rough
     * proximity range and apply a small curve so the UI does not show raw RSSI as if
     * it were distance. Because, shockingly, radio waves do not care about tidy UX.
     */
    val normalized = if (rssi >= 0) {
        val minChafonRssi = 35f
        val maxChafonRssi = 80f
        ((rssi.toFloat() - minChafonRssi) / (maxChafonRssi - minChafonRssi))
    } else {
        val minDbmRssi = -80f
        val maxDbmRssi = -35f
        ((rssi.toFloat() - minDbmRssi) / (maxDbmRssi - minDbmRssi))
    }.coerceIn(0f, 1f)

    return (java.lang.Math.pow(normalized.toDouble(), 0.85).toFloat() * 100f)
        .toInt()
        .coerceIn(0, 100)
}

private fun normalizeBarcodeCandidate(raw: String): String {
    val withoutLineBreaks = raw
        .replace("\n", "")
        .replace("\r", "")
        .trim()

    val withoutTriggerCodes = withoutLineBreaks
        .replace("B00+D", "", ignoreCase = true)
        .replace("B00D", "", ignoreCase = true)
        .replace("B00+U", "", ignoreCase = true)
        .replace("B00U", "", ignoreCase = true)
        .trim()

    return collapseConsecutiveRepeatedBarcode(withoutTriggerCodes)
}

private fun isScannerTriggerOnly(raw: String): Boolean {
    val clean = raw
        .replace("\n", "")
        .replace("\r", "")
        .trim()
        .uppercase()

    return clean == "B00+D" ||
            clean == "B00D" ||
            clean == "B00+U" ||
            clean == "B00U"
}

private fun containsScannerTriggerCode(raw: String): Boolean {
    return containsScannerTriggerDownCode(raw) || containsScannerTriggerUpCode(raw)
}

private fun containsScannerTriggerDownCode(raw: String): Boolean {
    val clean = raw
        .replace("\n", "")
        .replace("\r", "")
        .uppercase(Locale.ROOT)

    return clean.contains("B00+D") ||
            clean.contains("B00D")
}

private fun containsScannerTriggerUpCode(raw: String): Boolean {
    val clean = raw
        .replace("\n", "")
        .replace("\r", "")
        .uppercase(Locale.ROOT)

    return clean.contains("B00+U") ||
            clean.contains("B00U")
}

private fun isChafonTriggerKey(keyCode: Int, scanCode: Int): Boolean {
    val knownKeyCodes = setOf(
        KeyEvent.KEYCODE_F1,
        KeyEvent.KEYCODE_F2,
        KeyEvent.KEYCODE_F3,
        KeyEvent.KEYCODE_F4,
        KeyEvent.KEYCODE_F5,
        KeyEvent.KEYCODE_F6,
        KeyEvent.KEYCODE_F7,
        KeyEvent.KEYCODE_F8,
        KeyEvent.KEYCODE_F9,
        KeyEvent.KEYCODE_F10,
        KeyEvent.KEYCODE_F11,
        KeyEvent.KEYCODE_F12,
        KeyEvent.KEYCODE_BUTTON_A,
        KeyEvent.KEYCODE_BUTTON_B,
        KeyEvent.KEYCODE_BUTTON_L1,
        KeyEvent.KEYCODE_BUTTON_R1,
        KeyEvent.KEYCODE_CAMERA,
        KeyEvent.KEYCODE_FOCUS,
        139,
        280,
        281,
        293,
        294,
        520,
        521,
        522,
        523
    )

    val knownScanCodes = setOf(
        139,
        280,
        281,
        293,
        294,
        520,
        521,
        522,
        523
    )

    return keyCode in knownKeyCodes || scanCode in knownScanCodes
}

private fun collapseConsecutiveRepeatedBarcode(value: String): String {
    val clean = value.trim()

    if (clean.length < 8) return clean

    for (partLength in 4..(clean.length / 2)) {
        if (clean.length % partLength != 0) continue

        val candidate = clean.substring(0, partLength)
        val repetitions = clean.length / partLength

        if (repetitions < 2) continue

        if (candidate.repeat(repetitions) == clean) {
            return candidate.trim()
        }
    }

    return clean
}

private fun hideSoftKeyboard(context: Context, editText: EditText) {
    val imm = context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
    imm.hideSoftInputFromWindow(editText.windowToken, 0)
}
