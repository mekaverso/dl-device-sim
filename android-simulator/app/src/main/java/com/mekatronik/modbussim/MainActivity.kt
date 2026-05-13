package com.mekatronik.modbussim

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.NavigateBefore
import androidx.compose.material.icons.automirrored.filled.NavigateNext
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.Image
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mekatronik.modbussim.modbus.*
import com.mekatronik.modbussim.ui.theme.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MekatronikTheme {
                SimulatorScreen()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SimulatorScreen(vm: SimulatorViewModel = viewModel()) {
    val state by vm.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(state.deviceType.modelId, fontWeight = FontWeight.Bold, color = BrandBlue)
                        Spacer(Modifier.width(8.dp))
                        Text("Device Simulator", color = TextSecondary, fontSize = 14.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = BgDark),
            )
        },
        containerColor = BgDark,
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Device selector
            DeviceSelectorCard(state, vm)
            // Server control card
            ServerControlCard(state, vm)
            // Device panel (LCD + LEDs)
            DevicePanelCard(state, vm)
            // Register view
            if (state.isRunning) {
                RegisterListCard(state)
            }
        }
    }
}

@Composable
fun DeviceSelectorCard(state: SimulatorUiState, vm: SimulatorViewModel) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BgPanel),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Device Type", fontWeight = FontWeight.Bold, color = TextPrimary, fontSize = 13.sp)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                for (type in DeviceType.entries) {
                    val selected = state.deviceType == type
                    val enabled = !state.isRunning
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(8.dp))
                            .then(
                                if (enabled) Modifier.clickable { vm.selectDevice(type) }
                                else Modifier
                            ),
                        color = if (selected) BrandBlue else BgCard,
                        shape = RoundedCornerShape(8.dp),
                        tonalElevation = if (selected) 4.dp else 0.dp,
                    ) {
                        Column(
                            Modifier.padding(12.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            Text(
                                type.modelId,
                                fontWeight = FontWeight.Bold,
                                fontSize = 14.sp,
                                color = if (selected) Color.White
                                    else if (enabled) TextPrimary else TextDim,
                            )
                            Text(
                                type.displayName.substringAfter(" "),
                                fontSize = 11.sp,
                                color = if (selected) Color.White.copy(alpha = 0.8f)
                                    else TextSecondary,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ServerControlCard(state: SimulatorUiState, vm: SimulatorViewModel) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BgPanel),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Modbus TCP Server", fontWeight = FontWeight.Bold, color = TextPrimary)

            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        StatusDot(if (state.isRunning) AccentGreen else AccentRed)
                        Spacer(Modifier.width(8.dp))
                        Text(
                            if (state.isRunning) "RUNNING" else "STOPPED",
                            color = if (state.isRunning) AccentGreen else AccentRed,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                        )
                    }
                    if (state.isRunning) {
                        Spacer(Modifier.height(4.dp))
                        Text(
                            "${state.ipAddress}:${state.serverPort}",
                            color = AccentCyan,
                            fontFamily = FontFamily.Monospace,
                            fontSize = 13.sp,
                        )
                        Text(
                            "Clients: ${state.connectedClients}",
                            color = TextSecondary,
                            fontSize = 12.sp,
                        )
                    }
                }

                Button(
                    onClick = { if (state.isRunning) vm.stopSimulation() else vm.startSimulation(5020) },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (state.isRunning) AccentRed else AccentGreen,
                    ),
                    shape = RoundedCornerShape(8.dp),
                ) {
                    Icon(
                        if (state.isRunning) Icons.Default.Stop else Icons.Default.PlayArrow,
                        contentDescription = null,
                        tint = if (state.isRunning) Color.White else BgDark,
                    )
                    Spacer(Modifier.width(4.dp))
                    Text(
                        if (state.isRunning) "STOP" else "START",
                        color = if (state.isRunning) Color.White else BgDark,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }
    }
}

@Composable
fun DevicePanelCard(state: SimulatorUiState, vm: SimulatorViewModel) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BgPanel),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            // Device header
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Image(
                        painter = painterResource(id = R.drawable.mekatronik_logo),
                        contentDescription = "Mekatronik",
                        modifier = Modifier.height(22.dp),
                        contentScale = ContentScale.FillHeight,
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        "${state.deviceType.modelId} ${state.deviceType.displayName.substringAfter(" ")}",
                        color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 15.sp,
                    )
                }
                // LED indicators — device-specific
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    when (state.deviceType) {
                        DeviceType.ENERGY_MONITOR -> {
                            LedIndicator("PWR", if (state.isRunning) AccentGreen else TextDim)
                            LedIndicator("COM", if (state.connectedClients > 0) AccentCyan else TextDim)
                            LedIndicator("ALM",
                                if (state.isRunning && (state.registerValues[90]?.toInt() ?: 0) > 0) AccentRed else TextDim
                            )
                        }
                        DeviceType.MOTOR_DRIVE -> {
                            val vfdStatus = state.registerValues[26]?.toInt() ?: 0
                            val vfdFault = state.registerValues[27]?.toInt() ?: 0
                            LedIndicator("PWR", if (state.isRunning) AccentGreen else TextDim)
                            LedIndicator("RUN", if (vfdStatus and VFD_STATUS_RUNNING != 0) AccentGreen else TextDim)
                            LedIndicator("FLT", if (vfdFault > 0) AccentRed else TextDim)
                            LedIndicator("FWD", if (vfdStatus and VFD_STATUS_FORWARD != 0) AccentCyan else TextDim)
                            LedIndicator("REV", if (vfdStatus and VFD_STATUS_REVERSE != 0) AccentPeach else TextDim)
                            LedIndicator("LOC", if (state.isLocalMode) AccentGold else TextDim)
                        }
                    }
                }
            }

            // LCD Display
            LcdDisplay(state, vm)

            // Local control panel (VFD only)
            if (state.deviceType == DeviceType.MOTOR_DRIVE && state.isRunning) {
                VfdLocalControlPanel(state, vm)
            }

            // Status LEDs row
            if (state.isRunning) {
                when (state.deviceType) {
                    DeviceType.ENERGY_MONITOR -> StatusLedsRowEM(state)
                    DeviceType.MOTOR_DRIVE -> StatusLedsRowVFD(state)
                }
            }
        }
    }
}

@Composable
fun LcdDisplay(state: SimulatorUiState, vm: SimulatorViewModel) {
    val pages = getLcdPages(state.deviceType)
    val page = pages.getOrNull(state.lcdPage) ?: return

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(LcdBg)
            .border(2.dp, Color(0xFF003322), RoundedCornerShape(8.dp))
            .padding(12.dp),
    ) {
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (state.isLocalMode && state.deviceType == DeviceType.MOTOR_DRIVE) {
                Text(
                    "LOC",
                    color = Color(0xFFFFAA00),
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                )
                Spacer(Modifier.width(6.dp))
            }
            Text(
                page.title,
                color = LcdTextDim,
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
            )
        }
        Spacer(Modifier.height(8.dp))

        for (row in page.rows) {
            val value = state.registerValues[row.address] ?: 0.0
            val formatted = try { String.format(row.format, value) } catch (_: Exception) { "---" }
            Row(
                Modifier.fillMaxWidth().padding(vertical = 2.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(row.label, color = LcdText, fontFamily = FontFamily.Monospace, fontSize = 14.sp)
                Text(
                    "$formatted ${row.unit}",
                    color = LcdText, fontFamily = FontFamily.Monospace, fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                )
            }
        }

        Spacer(Modifier.height(8.dp))
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = { vm.prevLcdPage() }, modifier = Modifier.size(32.dp)) {
                Icon(Icons.AutoMirrored.Filled.NavigateBefore, null, tint = LcdText)
            }
            Text(
                "${state.lcdPage + 1}/${pages.size}",
                color = LcdTextDim, fontFamily = FontFamily.Monospace, fontSize = 11.sp,
            )
            IconButton(onClick = { vm.nextLcdPage() }, modifier = Modifier.size(32.dp)) {
                Icon(Icons.AutoMirrored.Filled.NavigateNext, null, tint = LcdText)
            }
        }
    }
}

@Composable
fun StatusLedsRowEM(state: SimulatorUiState) {
    val status = state.registerValues[91]?.toInt() ?: 0
    val alarm = state.registerValues[90]?.toInt() ?: 0
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
        MiniLed("RUN", status and STATUS_RUNNING != 0, AccentGreen)
        MiniLed("TCP", status and STATUS_TCP_ACTIVE != 0, AccentCyan)
        MiniLed("OV", alarm and ALARM_OVER_VOLTAGE != 0, AccentRed)
        MiniLed("UV", alarm and ALARM_UNDER_VOLTAGE != 0, AccentPeach)
        MiniLed("OC", alarm and ALARM_OVER_CURRENT != 0, AccentRed)
        MiniLed("OP", alarm and ALARM_OVER_POWER != 0, AccentGold)
    }
}

@Composable
fun StatusLedsRowVFD(state: SimulatorUiState) {
    val status = state.registerValues[26]?.toInt() ?: 0
    val fault = state.registerValues[27]?.toInt() ?: 0
    val warn = state.registerValues[28]?.toInt() ?: 0
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
        MiniLed("RUN", status and VFD_STATUS_RUNNING != 0, AccentGreen)
        MiniLed("REF", status and VFD_STATUS_AT_REF != 0, AccentCyan)
        MiniLed("ACC", status and VFD_STATUS_ACCEL != 0, AccentGold)
        MiniLed("DEC", status and VFD_STATUS_DECEL != 0, AccentPeach)
        MiniLed("FLT", fault > 0, AccentRed)
        MiniLed("WRN", warn > 0, AccentGold)
    }
}

@Composable
fun RegisterListCard(state: SimulatorUiState) {
    val registers = getRegisters(state.deviceType)

    Card(
        colors = CardDefaults.cardColors(containerColor = BgPanel),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text("Live Registers", fontWeight = FontWeight.Bold, color = TextPrimary)
            Spacer(Modifier.height(8.dp))

            Row(
                Modifier
                    .fillMaxWidth()
                    .background(BgCard, RoundedCornerShape(4.dp))
                    .padding(horizontal = 8.dp, vertical = 4.dp),
            ) {
                Text("Addr", Modifier.width(44.dp), color = TextSecondary, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                Text("Parameter", Modifier.weight(1f), color = TextSecondary, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                Text("Value", Modifier.width(80.dp), color = TextSecondary, fontSize = 11.sp, fontWeight = FontWeight.Bold, textAlign = TextAlign.End)
                Text("Unit", Modifier.width(44.dp), color = TextSecondary, fontSize = 11.sp, fontWeight = FontWeight.Bold, textAlign = TextAlign.End)
            }

            registers.forEach { reg ->
                val value = state.registerValues[reg.address] ?: reg.default
                val formatted = when {
                    reg.unit == "" && reg.dataType == DataType.UINT16 -> String.format("%.0f", value)
                    reg.dataType == DataType.UINT32 -> String.format("%.0f", value)
                    else -> String.format("%.2f", value)
                }
                val nameColor = if (reg.writable) AccentGreen else TextPrimary
                val bgColor = if (reg.writable) Color(0x10408040) else Color.Transparent

                Row(
                    Modifier
                        .fillMaxWidth()
                        .background(bgColor)
                        .padding(horizontal = 8.dp, vertical = 3.dp),
                ) {
                    Text("${reg.address}", Modifier.width(44.dp), color = TextDim, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                    Text(reg.name, Modifier.weight(1f), color = nameColor, fontSize = 11.sp)
                    Text(formatted, Modifier.width(80.dp), color = AccentCyan, fontSize = 11.sp, fontFamily = FontFamily.Monospace, textAlign = TextAlign.End)
                    Text(reg.unit, Modifier.width(44.dp), color = TextSecondary, fontSize = 11.sp, textAlign = TextAlign.End)
                }
            }
        }
    }
}

// ── VFD Local Control Panel ──────────────────────────────────────────

@Composable
fun VfdLocalControlPanel(state: SimulatorUiState, vm: SimulatorViewModel) {
    val isLocal = state.isLocalMode
    val isRunning = state.localRun
    val isReverse = state.localReverse
    val hasFault = (state.registerValues[27]?.toInt() ?: 0) > 0

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        // LOCAL/REMOTE toggle
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Control Mode", color = TextSecondary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    if (isLocal) "LOCAL" else "REMOTE",
                    color = if (isLocal) AccentGold else AccentCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    fontFamily = FontFamily.Monospace,
                )
                Spacer(Modifier.width(8.dp))
                Switch(
                    checked = isLocal,
                    onCheckedChange = { vm.toggleLocalMode() },
                    colors = SwitchDefaults.colors(
                        checkedTrackColor = AccentGold,
                        checkedThumbColor = Color.White,
                        uncheckedTrackColor = BgCard,
                        uncheckedThumbColor = TextDim,
                    ),
                )
            }
        }

        if (isLocal) {
            // Frequency reference display
            Box(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(6.dp))
                    .background(LcdBg)
                    .border(1.dp, Color(0xFF003322), RoundedCornerShape(6.dp))
                    .padding(horizontal = 12.dp, vertical = 8.dp),
            ) {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("FREQ REF", color = LcdTextDim, fontFamily = FontFamily.Monospace, fontSize = 11.sp)
                    Text(
                        String.format("%.1f Hz", state.localFreqRef),
                        color = LcdText,
                        fontFamily = FontFamily.Monospace,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }

            // Frequency adjustment buttons
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                FreqButton("<<", Modifier.weight(1f)) { vm.localFreqAdjust(-10.0) }
                FreqButton("−", Modifier.weight(1f)) { vm.localFreqAdjust(-1.0) }
                FreqButton("−.1", Modifier.weight(1f)) { vm.localFreqAdjust(-0.1) }
                FreqButton("+.1", Modifier.weight(1f)) { vm.localFreqAdjust(0.1) }
                FreqButton("+", Modifier.weight(1f)) { vm.localFreqAdjust(1.0) }
                FreqButton(">>", Modifier.weight(1f)) { vm.localFreqAdjust(10.0) }
            }

            // Control buttons row
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                // RUN / STOP
                Button(
                    onClick = { vm.localRunStop() },
                    modifier = Modifier.weight(1f).height(48.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isRunning) AccentRed else AccentGreen,
                    ),
                    shape = RoundedCornerShape(8.dp),
                    enabled = !hasFault,
                ) {
                    Icon(
                        if (isRunning) Icons.Default.Stop else Icons.Default.PlayArrow,
                        contentDescription = null,
                        tint = if (isRunning) Color.White else BgDark,
                        modifier = Modifier.size(20.dp),
                    )
                    Spacer(Modifier.width(4.dp))
                    Text(
                        if (isRunning) "STOP" else "RUN",
                        color = if (isRunning) Color.White else BgDark,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                    )
                }

                // FWD / REV
                Button(
                    onClick = { vm.localFwdRev() },
                    modifier = Modifier.weight(1f).height(48.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isReverse) AccentPeach else AccentCyan,
                    ),
                    shape = RoundedCornerShape(8.dp),
                ) {
                    Icon(
                        if (isReverse) Icons.Default.KeyboardArrowLeft else Icons.Default.KeyboardArrowRight,
                        contentDescription = null,
                        tint = BgDark,
                        modifier = Modifier.size(20.dp),
                    )
                    Text(
                        if (isReverse) "REV" else "FWD",
                        color = BgDark,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                    )
                }
            }

            // JOG and FAULT RESET row
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                // JOG (press & hold)
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .height(44.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(if (state.localJog) AccentGold else BgCard)
                        .pointerInput(Unit) {
                            detectTapGestures(
                                onPress = {
                                    vm.localJogPress()
                                    tryAwaitRelease()
                                    vm.localJogRelease()
                                },
                            )
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        "JOG",
                        color = if (state.localJog) BgDark else TextPrimary,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                    )
                }

                // FAULT RESET
                Button(
                    onClick = { vm.localFaultReset() },
                    modifier = Modifier.weight(1f).height(44.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = BgCard),
                    shape = RoundedCornerShape(8.dp),
                    enabled = hasFault,
                ) {
                    Icon(
                        Icons.Default.Refresh,
                        contentDescription = null,
                        tint = if (hasFault) AccentRed else TextDim,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(Modifier.width(4.dp))
                    Text(
                        "RST",
                        color = if (hasFault) AccentRed else TextDim,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                    )
                }
            }
        }
    }
}

@Composable
fun FreqButton(label: String, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Surface(
        modifier = modifier
            .height(36.dp)
            .clip(RoundedCornerShape(6.dp))
            .clickable(onClick = onClick),
        color = BgCard,
        shape = RoundedCornerShape(6.dp),
    ) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
            Text(
                label,
                color = TextPrimary,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
            )
        }
    }
}

// ── Small composable components ──────────────────────────────────────

@Composable
fun StatusDot(color: Color) {
    Box(Modifier.size(10.dp).clip(CircleShape).background(color))
}

@Composable
fun LedIndicator(label: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.size(8.dp).clip(CircleShape).background(color))
        Text(label, color = TextDim, fontSize = 8.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun MiniLed(label: String, active: Boolean, activeColor: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.size(6.dp).clip(CircleShape).background(if (active) activeColor else TextDim))
        Text(label, color = if (active) activeColor else TextDim, fontSize = 9.sp)
    }
}
