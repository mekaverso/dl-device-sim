package com.mekatronik.modbussim

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.mekatronik.modbussim.modbus.*
import com.mekatronik.modbussim.simulation.MotorDriveEngine
import com.mekatronik.modbussim.simulation.SimulationEngine
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.net.NetworkInterface

enum class DeviceType(val displayName: String, val modelId: String) {
    ENERGY_MONITOR("MK-EM3P Energy Monitor", "MK-EM3P"),
    MOTOR_DRIVE("MK-VFD7 Motor Drive", "MK-VFD7"),
}

data class SimulatorUiState(
    val isRunning: Boolean = false,
    val deviceType: DeviceType = DeviceType.ENERGY_MONITOR,
    val serverPort: Int = 502,
    val connectedClients: Int = 0,
    val ipAddress: String = "---",
    val registerValues: Map<Int, Double> = emptyMap(),
    val lcdPage: Int = 0,
    val isLocalMode: Boolean = false,
    val localRun: Boolean = false,
    val localReverse: Boolean = false,
    val localFreqRef: Double = 30.0,
    val localJog: Boolean = false,
)

class SimulatorViewModel(app: Application) : AndroidViewModel(app) {

    private val _uiState = MutableStateFlow(SimulatorUiState())
    val uiState: StateFlow<SimulatorUiState> = _uiState

    private var server: ModbusTcpServer? = null
    private var emEngine: SimulationEngine? = null
    private var vfdEngine: MotorDriveEngine? = null
    private var simulationJob: Job? = null

    fun selectDevice(type: DeviceType) {
        if (_uiState.value.isRunning) return
        _uiState.value = _uiState.value.copy(deviceType = type, lcdPage = 0)
    }

    fun startSimulation(port: Int = 502) {
        if (_uiState.value.isRunning) return

        val deviceType = _uiState.value.deviceType
        val srv = ModbusTcpServer(deviceId = 1, port = port)

        srv.onClientCountChanged = { count ->
            _uiState.value = _uiState.value.copy(connectedClients = count)
        }

        server = srv
        srv.start(viewModelScope)

        _uiState.value = _uiState.value.copy(
            isRunning = true,
            serverPort = port,
            ipAddress = getDeviceIpAddress(),
        )

        simulationJob = viewModelScope.launch(Dispatchers.Default) {
            when (deviceType) {
                DeviceType.ENERGY_MONITOR -> {
                    val eng = SimulationEngine(srv)
                    emEngine = eng
                    while (isActive) {
                        eng.readConfigFromServer()
                        eng.update()
                        _uiState.value = _uiState.value.copy(
                            registerValues = eng.currentValues.toMap()
                        )
                        delay(1000)
                    }
                }
                DeviceType.MOTOR_DRIVE -> {
                    val eng = MotorDriveEngine(srv)
                    vfdEngine = eng
                    while (isActive) {
                        if (!_uiState.value.isLocalMode) {
                            eng.readConfigFromServer()
                        }
                        eng.update()
                        _uiState.value = _uiState.value.copy(
                            registerValues = eng.currentValues.toMap()
                        )
                        delay(1000)
                    }
                }
            }
        }
    }

    fun stopSimulation() {
        simulationJob?.cancel()
        simulationJob = null
        server?.stop()
        server = null
        emEngine = null
        vfdEngine = null
        _uiState.value = _uiState.value.copy(
            isRunning = false,
            connectedClients = 0,
            registerValues = emptyMap(),
        )
    }

    fun nextLcdPage() {
        val pages = getLcdPages(_uiState.value.deviceType)
        val current = _uiState.value.lcdPage
        _uiState.value = _uiState.value.copy(lcdPage = (current + 1) % pages.size)
    }

    fun prevLcdPage() {
        val pages = getLcdPages(_uiState.value.deviceType)
        val current = _uiState.value.lcdPage
        _uiState.value = _uiState.value.copy(
            lcdPage = if (current == 0) pages.size - 1 else current - 1
        )
    }

    // ── Local control mode ─────────────────────────────────────────────

    fun toggleLocalMode() {
        val s = _uiState.value
        if (s.deviceType != DeviceType.MOTOR_DRIVE) return
        _uiState.value = s.copy(
            isLocalMode = !s.isLocalMode,
            localRun = false, localJog = false,
        )
        if (s.isLocalMode) {
            // Switching back to REMOTE — clear local run
            writeLocalCtrlWord(run = false, reverse = s.localReverse, jog = false)
        }
    }

    fun localRunStop() {
        val s = _uiState.value
        if (!s.isLocalMode) return
        val newRun = !s.localRun
        _uiState.value = s.copy(localRun = newRun, localJog = false)
        writeLocalCtrlWord(run = newRun, reverse = s.localReverse, jog = false)
    }

    fun localFwdRev() {
        val s = _uiState.value
        if (!s.isLocalMode) return
        val newReverse = !s.localReverse
        _uiState.value = s.copy(localReverse = newReverse)
        writeLocalCtrlWord(run = s.localRun, reverse = newReverse, jog = s.localJog)
    }

    fun localFreqAdjust(delta: Double) {
        val s = _uiState.value
        if (!s.isLocalMode) return
        val maxFreq = s.registerValues.getOrDefault(107, 60.0)
        val newFreq = (s.localFreqRef + delta).coerceIn(0.0, maxFreq)
        _uiState.value = s.copy(localFreqRef = newFreq)
        // Write frequency reference to engine
        vfdEngine?.currentValues?.set(101, newFreq)
        server?.setFloat32(101, newFreq.toFloat(), holdingOnly = true)
    }

    fun localFaultReset() {
        val s = _uiState.value
        if (!s.isLocalMode) return
        vfdEngine?.currentValues?.set(127, VFD_RESET_MAGIC.toDouble())
        _uiState.value = s.copy(localRun = false, localJog = false)
    }

    fun localJogPress() {
        val s = _uiState.value
        if (!s.isLocalMode || s.localRun) return
        _uiState.value = s.copy(localJog = true)
        writeLocalCtrlWord(run = false, reverse = s.localReverse, jog = true)
    }

    fun localJogRelease() {
        val s = _uiState.value
        if (!s.isLocalMode) return
        _uiState.value = s.copy(localJog = false)
        writeLocalCtrlWord(run = s.localRun, reverse = s.localReverse, jog = false)
    }

    private fun writeLocalCtrlWord(run: Boolean, reverse: Boolean, jog: Boolean) {
        var ctrl = 0
        if (run || jog) ctrl = ctrl or VFD_CTRL_RUN
        if (reverse) ctrl = ctrl or VFD_CTRL_REVERSE
        if (jog) ctrl = ctrl or VFD_CTRL_JOG
        vfdEngine?.currentValues?.set(100, ctrl.toDouble())
        server?.setRegister(100, ctrl, holdingOnly = true)
    }

    override fun onCleared() {
        stopSimulation()
        super.onCleared()
    }

    private fun getDeviceIpAddress(): String {
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            for (intf in interfaces) {
                val addresses = intf.inetAddresses
                for (addr in addresses) {
                    if (!addr.isLoopbackAddress && addr.hostAddress?.contains('.') == true) {
                        return addr.hostAddress ?: "---"
                    }
                }
            }
        } catch (_: Exception) {}
        return "127.0.0.1"
    }
}

// ── LCD page definitions ─────────────────────────────────────────────

data class LcdPage(val title: String, val rows: List<LcdRow>)
data class LcdRow(val label: String, val address: Int, val unit: String, val format: String = "%.2f")

fun getLcdPages(type: DeviceType): List<LcdPage> = when (type) {
    DeviceType.ENERGY_MONITOR -> EM_LCD_PAGES
    DeviceType.MOTOR_DRIVE -> VFD_LCD_PAGES
}

fun getRegisters(type: DeviceType): List<RegisterDef> = when (type) {
    DeviceType.ENERGY_MONITOR -> ALL_REGISTERS
    DeviceType.MOTOR_DRIVE -> VFD_ALL_REGISTERS
}

val EM_LCD_PAGES = listOf(
    LcdPage("Voltage L-N", listOf(
        LcdRow("L1-N", 0, "V"), LcdRow("L2-N", 2, "V"), LcdRow("L3-N", 4, "V"),
    )),
    LcdPage("Voltage L-L", listOf(
        LcdRow("L1-L2", 6, "V"), LcdRow("L2-L3", 8, "V"), LcdRow("L3-L1", 10, "V"),
    )),
    LcdPage("Current", listOf(
        LcdRow("L1", 12, "A"), LcdRow("L2", 14, "A"),
        LcdRow("L3", 16, "A"), LcdRow("N", 18, "A"),
    )),
    LcdPage("Active Power", listOf(
        LcdRow("L1", 20, "kW"), LcdRow("L2", 22, "kW"),
        LcdRow("L3", 24, "kW"), LcdRow("Total", 26, "kW"),
    )),
    LcdPage("Reactive Power", listOf(
        LcdRow("L1", 28, "kVAr"), LcdRow("L2", 30, "kVAr"),
        LcdRow("L3", 32, "kVAr"), LcdRow("Total", 34, "kVAr"),
    )),
    LcdPage("Apparent Power", listOf(
        LcdRow("L1", 36, "kVA"), LcdRow("L2", 38, "kVA"),
        LcdRow("L3", 40, "kVA"), LcdRow("Total", 42, "kVA"),
    )),
    LcdPage("Power Factor", listOf(
        LcdRow("L1", 44, ""), LcdRow("L2", 46, ""),
        LcdRow("L3", 48, ""), LcdRow("Total", 50, ""),
    )),
    LcdPage("Frequency", listOf(
        LcdRow("Freq", 52, "Hz", "%.3f"),
    )),
    LcdPage("Energy", listOf(
        LcdRow("Active", 54, "kWh", "%.0f"), LcdRow("Reactive", 56, "kVArh", "%.0f"),
        LcdRow("Export", 58, "kWh", "%.0f"), LcdRow("Apparent", 60, "kVAh", "%.0f"),
    )),
    LcdPage("THD Voltage", listOf(
        LcdRow("L1", 62, "%"), LcdRow("L2", 64, "%"), LcdRow("L3", 66, "%"),
    )),
    LcdPage("THD Current", listOf(
        LcdRow("L1", 68, "%"), LcdRow("L2", 70, "%"), LcdRow("L3", 72, "%"),
    )),
    LcdPage("Demand / Avg", listOf(
        LcdRow("Max P", 74, "kW"), LcdRow("Max I", 76, "A"),
        LcdRow("Avg V", 78, "V"), LcdRow("Avg I", 82, "A"),
    )),
    LcdPage("System Status", listOf(
        LcdRow("Alarm", 90, "", "%.0f"), LcdRow("Status", 91, "", "%.0f"),
        LcdRow("Run h", 88, "h", "%.0f"),
    )),
)

val VFD_LCD_PAGES = listOf(
    LcdPage("Output", listOf(
        LcdRow("Freq", 0, "Hz"), LcdRow("Volt", 2, "V"),
        LcdRow("Curr", 4, "A"), LcdRow("Powr", 6, "kW"),
    )),
    LcdPage("Motor", listOf(
        LcdRow("Speed", 8, "RPM", "%.0f"), LcdRow("Torq", 10, "%"),
    )),
    LcdPage("Drive", listOf(
        LcdRow("DC Bus", 12, "V"), LcdRow("Drv T", 14, "°C"),
        LcdRow("Mot T", 16, "°C"),
    )),
    LcdPage("Power / Energy", listOf(
        LcdRow("Pin", 24, "kW"), LcdRow("Pout", 6, "kW"),
        LcdRow("PF", 22, ""), LcdRow("kWh", 20, "kWh", "%.0f"),
    )),
    LcdPage("Reference", listOf(
        LcdRow("Ref", 101, "Hz"), LcdRow("Out", 0, "Hz"),
        LcdRow("Acc", 103, "s"), LcdRow("Dec", 105, "s"),
    )),
    LcdPage("Limits", listOf(
        LcdRow("Fmax", 107, "Hz"), LcdRow("Fmin", 109, "Hz"),
        LcdRow("OC", 119, "A"), LcdRow("OV", 121, "V"),
    )),
    LcdPage("Motor Nameplate", listOf(
        LcdRow("Vrat", 111, "V", "%.0f"), LcdRow("Irat", 112, "A"),
        LcdRow("Frat", 114, "Hz", "%.0f"), LcdRow("RPM", 115, "RPM", "%.0f"),
    )),
    LcdPage("Status", listOf(
        LcdRow("Stat", 26, "", "%.0f"), LcdRow("Fault", 27, "", "%.0f"),
        LcdRow("Warn", 28, "", "%.0f"), LcdRow("RunH", 18, "h", "%.0f"),
    )),
)
