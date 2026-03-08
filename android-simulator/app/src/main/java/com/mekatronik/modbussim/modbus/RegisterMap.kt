package com.mekatronik.modbussim.modbus

/**
 * MK-EM3P Energy Monitor — Register Map
 *
 * Mirrors the register definitions from the Python simulator.
 * Addresses match the Modbus holding/input register addresses.
 */

enum class DataType(val registerCount: Int) {
    FLOAT32(2), UINT32(2), UINT16(1)
}

data class RegisterDef(
    val address: Int,
    val name: String,
    val unit: String,
    val dataType: DataType,
    val writable: Boolean = false,
    val default: Double = 0.0,
    val minValue: Double = 0.0,
    val maxValue: Double = 0.0,
)

/** All measurement registers (read-only, addresses 0–91). */
val MEASUREMENT_REGISTERS = listOf(
    // Voltage
    RegisterDef(0, "Voltage L1-N", "V", DataType.FLOAT32, default = 220.0, minValue = 210.0, maxValue = 230.0),
    RegisterDef(2, "Voltage L2-N", "V", DataType.FLOAT32, default = 220.0, minValue = 210.0, maxValue = 230.0),
    RegisterDef(4, "Voltage L3-N", "V", DataType.FLOAT32, default = 220.0, minValue = 210.0, maxValue = 230.0),
    RegisterDef(6, "Voltage L1-L2", "V", DataType.FLOAT32, default = 380.0, minValue = 363.0, maxValue = 398.0),
    RegisterDef(8, "Voltage L2-L3", "V", DataType.FLOAT32, default = 380.0, minValue = 363.0, maxValue = 398.0),
    RegisterDef(10, "Voltage L3-L1", "V", DataType.FLOAT32, default = 380.0, minValue = 363.0, maxValue = 398.0),
    // Current
    RegisterDef(12, "Current L1", "A", DataType.FLOAT32, default = 15.0, minValue = 5.0, maxValue = 25.0),
    RegisterDef(14, "Current L2", "A", DataType.FLOAT32, default = 15.0, minValue = 5.0, maxValue = 25.0),
    RegisterDef(16, "Current L3", "A", DataType.FLOAT32, default = 15.0, minValue = 5.0, maxValue = 25.0),
    RegisterDef(18, "Current Neutral", "A", DataType.FLOAT32, default = 1.0, minValue = 0.0, maxValue = 5.0),
    // Active Power
    RegisterDef(20, "Active Power L1", "kW", DataType.FLOAT32, default = 3.3, minValue = 1.0, maxValue = 5.5),
    RegisterDef(22, "Active Power L2", "kW", DataType.FLOAT32, default = 3.3, minValue = 1.0, maxValue = 5.5),
    RegisterDef(24, "Active Power L3", "kW", DataType.FLOAT32, default = 3.3, minValue = 1.0, maxValue = 5.5),
    RegisterDef(26, "Active Power Total", "kW", DataType.FLOAT32, default = 9.9, minValue = 3.0, maxValue = 16.5),
    // Reactive Power
    RegisterDef(28, "Reactive Power L1", "kVAr", DataType.FLOAT32, default = 0.8, minValue = 0.1, maxValue = 2.0),
    RegisterDef(30, "Reactive Power L2", "kVAr", DataType.FLOAT32, default = 0.8, minValue = 0.1, maxValue = 2.0),
    RegisterDef(32, "Reactive Power L3", "kVAr", DataType.FLOAT32, default = 0.8, minValue = 0.1, maxValue = 2.0),
    RegisterDef(34, "Reactive Power Total", "kVAr", DataType.FLOAT32, default = 2.4, minValue = 0.3, maxValue = 6.0),
    // Apparent Power
    RegisterDef(36, "Apparent Power L1", "kVA", DataType.FLOAT32, default = 3.4, minValue = 1.0, maxValue = 5.8),
    RegisterDef(38, "Apparent Power L2", "kVA", DataType.FLOAT32, default = 3.4, minValue = 1.0, maxValue = 5.8),
    RegisterDef(40, "Apparent Power L3", "kVA", DataType.FLOAT32, default = 3.4, minValue = 1.0, maxValue = 5.8),
    RegisterDef(42, "Apparent Power Total", "kVA", DataType.FLOAT32, default = 10.2, minValue = 3.0, maxValue = 17.4),
    // Power Factor
    RegisterDef(44, "Power Factor L1", "", DataType.FLOAT32, default = 0.97, minValue = 0.85, maxValue = 1.0),
    RegisterDef(46, "Power Factor L2", "", DataType.FLOAT32, default = 0.97, minValue = 0.85, maxValue = 1.0),
    RegisterDef(48, "Power Factor L3", "", DataType.FLOAT32, default = 0.97, minValue = 0.85, maxValue = 1.0),
    RegisterDef(50, "Power Factor Total", "", DataType.FLOAT32, default = 0.97, minValue = 0.85, maxValue = 1.0),
    // Frequency
    RegisterDef(52, "Frequency", "Hz", DataType.FLOAT32, default = 60.0, minValue = 59.90, maxValue = 60.10),
    // Energy
    RegisterDef(54, "Active Energy", "kWh", DataType.UINT32),
    RegisterDef(56, "Reactive Energy", "kVArh", DataType.UINT32),
    RegisterDef(58, "Active Energy Export", "kWh", DataType.UINT32),
    RegisterDef(60, "Apparent Energy", "kVAh", DataType.UINT32),
    // THD
    RegisterDef(62, "Voltage L1 THD", "%", DataType.FLOAT32, default = 2.5, minValue = 1.0, maxValue = 5.0),
    RegisterDef(64, "Voltage L2 THD", "%", DataType.FLOAT32, default = 2.5, minValue = 1.0, maxValue = 5.0),
    RegisterDef(66, "Voltage L3 THD", "%", DataType.FLOAT32, default = 2.5, minValue = 1.0, maxValue = 5.0),
    RegisterDef(68, "Current L1 THD", "%", DataType.FLOAT32, default = 8.0, minValue = 3.0, maxValue = 15.0),
    RegisterDef(70, "Current L2 THD", "%", DataType.FLOAT32, default = 8.0, minValue = 3.0, maxValue = 15.0),
    RegisterDef(72, "Current L3 THD", "%", DataType.FLOAT32, default = 8.0, minValue = 3.0, maxValue = 15.0),
    // Demand
    RegisterDef(74, "Max Demand Power", "kW", DataType.FLOAT32, default = 12.0, minValue = 0.0, maxValue = 20.0),
    RegisterDef(76, "Max Demand Current", "A", DataType.FLOAT32, default = 18.0, minValue = 0.0, maxValue = 30.0),
    // Averages
    RegisterDef(78, "Avg Voltage L-N", "V", DataType.FLOAT32, default = 220.0, minValue = 200.0, maxValue = 240.0),
    RegisterDef(80, "Avg Voltage L-L", "V", DataType.FLOAT32, default = 380.0, minValue = 346.0, maxValue = 415.0),
    RegisterDef(82, "Avg Current", "A", DataType.FLOAT32, default = 15.0, minValue = 0.0, maxValue = 30.0),
    // Unbalance
    RegisterDef(84, "Voltage Unbalance", "%", DataType.FLOAT32, default = 1.0, minValue = 0.0, maxValue = 10.0),
    RegisterDef(86, "Current Unbalance", "%", DataType.FLOAT32, default = 2.0, minValue = 0.0, maxValue = 20.0),
    // Counters
    RegisterDef(88, "Run Hours", "h", DataType.UINT32),
    // Status
    RegisterDef(90, "Alarm Status", "", DataType.UINT16),
    RegisterDef(91, "Device Status", "", DataType.UINT16),
)

/** Configuration registers (read/write, addresses 100–122). */
val CONFIG_REGISTERS = listOf(
    RegisterDef(100, "CT Primary", "A", DataType.UINT16, writable = true, default = 100.0),
    RegisterDef(101, "CT Secondary", "A", DataType.UINT16, writable = true, default = 5.0),
    RegisterDef(102, "VT Primary", "V", DataType.UINT16, writable = true, default = 220.0),
    RegisterDef(103, "VT Secondary", "V", DataType.UINT16, writable = true, default = 220.0),
    RegisterDef(104, "System Type", "", DataType.UINT16, writable = true),
    RegisterDef(105, "Nominal Frequency", "Hz", DataType.UINT16, writable = true, default = 60.0),
    RegisterDef(106, "Demand Period", "min", DataType.UINT16, writable = true, default = 15.0),
    RegisterDef(107, "Over-Voltage Threshold", "V", DataType.FLOAT32, writable = true, default = 253.0),
    RegisterDef(109, "Under-Voltage Threshold", "V", DataType.FLOAT32, writable = true, default = 198.0),
    RegisterDef(111, "Over-Current Threshold", "A", DataType.FLOAT32, writable = true, default = 30.0),
    RegisterDef(113, "Low PF Threshold", "", DataType.FLOAT32, writable = true, default = 0.85),
    RegisterDef(115, "Over-Power Threshold", "kW", DataType.FLOAT32, writable = true, default = 15.0),
    RegisterDef(117, "Alarm Enable Mask", "", DataType.UINT16, writable = true, default = 31.0),
    RegisterDef(118, "Energy Reset Cmd", "", DataType.UINT16, writable = true),
    RegisterDef(119, "Demand Reset Cmd", "", DataType.UINT16, writable = true),
    RegisterDef(120, "Backlight Timeout", "s", DataType.UINT16, writable = true, default = 60.0),
    RegisterDef(121, "Password", "", DataType.UINT32, writable = true),
)

val ALL_REGISTERS = MEASUREMENT_REGISTERS + CONFIG_REGISTERS

// Alarm bit masks
const val ALARM_OVER_VOLTAGE = 0x0001
const val ALARM_UNDER_VOLTAGE = 0x0002
const val ALARM_OVER_CURRENT = 0x0004
const val ALARM_LOW_PF = 0x0008
const val ALARM_OVER_POWER = 0x0010
const val ALARM_PHASE_LOSS = 0x0020
const val ALARM_THD_HIGH = 0x0080

// Device status bits
const val STATUS_RUNNING = 0x0001
const val STATUS_TCP_ACTIVE = 0x0002
const val STATUS_ALARM_ACTIVE = 0x0008

const val RESET_MAGIC = 0x1234

// ── IEEE 754 Float32 decode/encode ───────────────────────────────────

fun decodeFloat32(high: Int, low: Int): Float {
    val bits = (high shl 16) or low
    return Float.fromBits(bits)
}

fun encodeFloat32(value: Float): Pair<Int, Int> {
    val bits = value.toBits()
    return Pair((bits ushr 16) and 0xFFFF, bits and 0xFFFF)
}

fun decodeUint32(high: Int, low: Int): Long {
    return ((high.toLong() and 0xFFFF) shl 16) or (low.toLong() and 0xFFFF)
}

fun encodeUint32(value: Long): Pair<Int, Int> {
    return Pair(((value ushr 16) and 0xFFFF).toInt(), (value and 0xFFFF).toInt())
}
