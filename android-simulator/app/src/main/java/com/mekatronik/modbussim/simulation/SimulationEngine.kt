package com.mekatronik.modbussim.simulation

import com.mekatronik.modbussim.modbus.*
import kotlin.math.*
import kotlin.random.Random

/**
 * Simulation engine — generates realistic fluctuating values for device registers.
 *
 * Uses layered sine waves (Perlin-like smooth noise) to create natural-looking
 * sensor readings. Port of the Python SimulationEngine.
 */
class SimulationEngine(
    private val server: ModbusTcpServer,
    private val updateIntervalMs: Long = 1000,
    private val noiseScale: Double = 0.02,
    private val driftSpeed: Double = 0.1,
    private val energyTimeFactor: Double = 1.0,
) {
    private val timeOffset = Random.nextDouble(0.0, 1000.0)
    private val phaseOffsets = mutableMapOf<Int, Double>()

    private var lastUpdateMs = System.currentTimeMillis()
    private val startTimeMs = System.currentTimeMillis()

    // Internal accumulators
    private var energyKwh = 0.0
    private var energyKvarh = 0.0
    private var energyExportKwh = 0.0
    private var energyKvah = 0.0
    private var maxDemandPower = 0.0
    private var maxDemandCurrent = 0.0

    // Current simulation values (address -> value)
    val currentValues = mutableMapOf<Int, Double>()

    init {
        // Initialize all registers with defaults and assign random phase offsets
        for (reg in ALL_REGISTERS) {
            currentValues[reg.address] = reg.default
            phaseOffsets[reg.address] = Random.nextDouble(0.0, 2.0 * PI)
        }
    }

    /** Smooth noise using layered sine waves (cheap Perlin-like). */
    private fun smoothNoise(t: Double, phase: Double): Double {
        return (0.5 * sin(t * 0.7 + phase) +
                0.25 * sin(t * 1.3 + phase * 2.1) +
                0.15 * sin(t * 2.9 + phase * 0.7) +
                0.10 * sin(t * 5.1 + phase * 1.3))
    }

    /** Read writable config registers back from the Modbus server (master may have written). */
    fun readConfigFromServer() {
        for (reg in ALL_REGISTERS) {
            if (!reg.writable) continue
            when (reg.dataType) {
                DataType.FLOAT32 -> {
                    val hi = server.getHoldingRegister(reg.address)
                    val lo = server.getHoldingRegister(reg.address + 1)
                    currentValues[reg.address] = decodeFloat32(hi, lo).toDouble()
                }
                DataType.UINT32 -> {
                    val hi = server.getHoldingRegister(reg.address)
                    val lo = server.getHoldingRegister(reg.address + 1)
                    currentValues[reg.address] = decodeUint32(hi, lo).toDouble()
                }
                DataType.UINT16 -> {
                    currentValues[reg.address] = server.getHoldingRegister(reg.address).toDouble()
                }
            }
        }

        // Handle reset commands
        val energyReset = currentValues.getOrDefault(118, 0.0).toInt()
        if (energyReset == RESET_MAGIC) {
            energyKwh = 0.0; energyKvarh = 0.0; energyExportKwh = 0.0; energyKvah = 0.0
            currentValues[54] = 0.0; currentValues[56] = 0.0
            currentValues[58] = 0.0; currentValues[60] = 0.0
            currentValues[118] = 0.0
        }

        val demandReset = currentValues.getOrDefault(119, 0.0).toInt()
        if (demandReset == RESET_MAGIC) {
            maxDemandPower = 0.0; maxDemandCurrent = 0.0
            currentValues[74] = 0.0; currentValues[76] = 0.0
            currentValues[119] = 0.0
        }
    }

    /** Advance the simulation by one tick, updating all register values. */
    fun update() {
        val now = System.currentTimeMillis()
        val dt = (now - lastUpdateMs) / 1000.0
        lastUpdateMs = now

        val t = (now / 1000.0 + timeOffset) * driftSpeed

        // ── Phase Voltages (correlated — they share a grid) ──────────
        val vBase = smoothNoise(t, 0.0) * 0.3
        for (addr in intArrayOf(0, 2, 4)) {
            val reg = findRegister(addr) ?: continue
            val phase = phaseOffsets[addr] ?: 0.0
            val noise = vBase + smoothNoise(t, phase) * 0.15
            val value = reg.default + noise * (reg.maxValue - reg.minValue) * noiseScale * 10
            currentValues[addr] = value.coerceIn(reg.minValue, reg.maxValue)
        }

        // ── Line-to-Line Voltages (derived from phase voltages × √3) ─
        val vL1 = currentValues.getOrDefault(0, 220.0)
        val vL2 = currentValues.getOrDefault(2, 220.0)
        val vL3 = currentValues.getOrDefault(4, 220.0)
        currentValues[6] = (vL1 + vL2) / 2 * sqrt(3.0) + smoothNoise(t, 10.0) * 0.5
        currentValues[8] = (vL2 + vL3) / 2 * sqrt(3.0) + smoothNoise(t, 11.0) * 0.5
        currentValues[10] = (vL3 + vL1) / 2 * sqrt(3.0) + smoothNoise(t, 12.0) * 0.5

        for (addr in intArrayOf(6, 8, 10)) {
            val reg = findRegister(addr) ?: continue
            currentValues[addr] = currentValues[addr]!!.coerceIn(reg.minValue, reg.maxValue)
        }

        // ── Current (independent per phase, larger variation) ─────────
        for (addr in intArrayOf(12, 14, 16)) {
            val reg = findRegister(addr) ?: continue
            val phase = phaseOffsets[addr] ?: 0.0
            val noise = smoothNoise(t * 0.5, phase)
            val value = reg.default + noise * (reg.maxValue - reg.minValue) * 0.3
            currentValues[addr] = value.coerceIn(reg.minValue, reg.maxValue)
        }

        // Neutral current (small, derived from imbalance)
        val iL1 = currentValues.getOrDefault(12, 15.0)
        val iL2 = currentValues.getOrDefault(14, 15.0)
        val iL3 = currentValues.getOrDefault(16, 15.0)
        val iAvg = (iL1 + iL2 + iL3) / 3.0
        val neutral = abs(iL1 - iAvg) + abs(iL2 - iAvg) + abs(iL3 - iAvg)
        currentValues[18] = (neutral * 0.3).coerceIn(0.0, 5.0)

        // ── Power Factor (slow drift near unity) ─────────────────────
        for (addr in intArrayOf(44, 46, 48, 50)) {
            val reg = findRegister(addr) ?: continue
            val phase = phaseOffsets[addr] ?: 0.0
            val noise = smoothNoise(t * 0.3, phase)
            val value = reg.default + noise * 0.05
            currentValues[addr] = value.coerceIn(reg.minValue, reg.maxValue)
        }

        // ── Active Power (V × I × PF / 1000) per phase ──────────────
        val pfL1 = currentValues.getOrDefault(44, 0.97)
        val pfL2 = currentValues.getOrDefault(46, 0.97)
        val pfL3 = currentValues.getOrDefault(48, 0.97)
        val pL1 = vL1 * iL1 * pfL1 / 1000.0
        val pL2 = vL2 * iL2 * pfL2 / 1000.0
        val pL3 = vL3 * iL3 * pfL3 / 1000.0
        val pTotal = pL1 + pL2 + pL3
        currentValues[20] = pL1; currentValues[22] = pL2
        currentValues[24] = pL3; currentValues[26] = pTotal

        // ── Reactive Power (V × I × sin(acos(PF)) / 1000) ───────────
        val qL1 = vL1 * iL1 * sin(acos(pfL1.coerceAtMost(1.0))) / 1000.0
        val qL2 = vL2 * iL2 * sin(acos(pfL2.coerceAtMost(1.0))) / 1000.0
        val qL3 = vL3 * iL3 * sin(acos(pfL3.coerceAtMost(1.0))) / 1000.0
        val qTotal = qL1 + qL2 + qL3
        currentValues[28] = qL1; currentValues[30] = qL2
        currentValues[32] = qL3; currentValues[34] = qTotal

        // ── Apparent Power (V × I / 1000) ────────────────────────────
        val sL1 = vL1 * iL1 / 1000.0
        val sL2 = vL2 * iL2 / 1000.0
        val sL3 = vL3 * iL3 / 1000.0
        val sTotal = sL1 + sL2 + sL3
        currentValues[36] = sL1; currentValues[38] = sL2
        currentValues[40] = sL3; currentValues[42] = sTotal

        // ── Frequency (very small, slow drift) ───────────────────────
        findRegister(52)?.let { reg ->
            val noise = smoothNoise(t * 0.2, phaseOffsets[52] ?: 0.0)
            currentValues[52] = reg.default + noise * 0.05
        }

        // ── Energy Accumulators ──────────────────────────────────────
        energyKwh += pTotal * (dt / 3600.0) * energyTimeFactor
        energyKvarh += qTotal * (dt / 3600.0) * energyTimeFactor
        energyKvah += sTotal * (dt / 3600.0) * energyTimeFactor
        val exportNoise = smoothNoise(t * 0.1, 99.0)
        if (exportNoise > 0.8) energyExportKwh += 0.001 * energyTimeFactor

        currentValues[54] = energyKwh.toLong().toDouble()
        currentValues[56] = energyKvarh.toLong().toDouble()
        currentValues[58] = energyExportKwh.toLong().toDouble()
        currentValues[60] = energyKvah.toLong().toDouble()

        // ── Max Demand (track peak) ──────────────────────────────────
        if (pTotal > maxDemandPower) maxDemandPower = pTotal
        val maxPhaseCurrent = maxOf(iL1, iL2, iL3)
        if (maxPhaseCurrent > maxDemandCurrent) maxDemandCurrent = maxPhaseCurrent
        currentValues[74] = maxDemandPower
        currentValues[76] = maxDemandCurrent

        // ── Averages ─────────────────────────────────────────────────
        currentValues[78] = (vL1 + vL2 + vL3) / 3.0
        val vLL1 = currentValues.getOrDefault(6, 380.0)
        val vLL2 = currentValues.getOrDefault(8, 380.0)
        val vLL3 = currentValues.getOrDefault(10, 380.0)
        currentValues[80] = (vLL1 + vLL2 + vLL3) / 3.0
        currentValues[82] = iAvg

        // ── Unbalance (%) ────────────────────────────────────────────
        val vAvg = (vL1 + vL2 + vL3) / 3.0
        if (vAvg > 0) {
            val vMaxDev = maxOf(abs(vL1 - vAvg), abs(vL2 - vAvg), abs(vL3 - vAvg))
            currentValues[84] = (vMaxDev / vAvg) * 100.0
        }
        if (iAvg > 0) {
            val iMaxDev = maxOf(abs(iL1 - iAvg), abs(iL2 - iAvg), abs(iL3 - iAvg))
            currentValues[86] = (iMaxDev / iAvg) * 100.0
        }

        // ── Run Hours ────────────────────────────────────────────────
        val runHours = (now - startTimeMs) / 3600000.0
        currentValues[88] = runHours.toLong().toDouble()

        // ── THD values (gentle fluctuation) ──────────────────────────
        for (addr in intArrayOf(62, 64, 66, 68, 70, 72)) {
            val reg = findRegister(addr) ?: continue
            val phase = phaseOffsets[addr] ?: 0.0
            val noise = smoothNoise(t * 0.4, phase)
            val value = reg.default + noise * (reg.maxValue - reg.minValue) * 0.15
            currentValues[addr] = value.coerceIn(reg.minValue, reg.maxValue)
        }

        // ── Alarm Evaluation ─────────────────────────────────────────
        val alarmMask = currentValues.getOrDefault(117, 31.0).toInt()
        var alarmStatus = 0

        val ovThresh = currentValues.getOrDefault(107, 253.0)
        val uvThresh = currentValues.getOrDefault(109, 198.0)
        val ocThresh = currentValues.getOrDefault(111, 30.0)
        val pfThresh = currentValues.getOrDefault(113, 0.85)
        val opThresh = currentValues.getOrDefault(115, 15.0)

        if (maxOf(vL1, vL2, vL3) > ovThresh) alarmStatus = alarmStatus or ALARM_OVER_VOLTAGE
        if (minOf(vL1, vL2, vL3) < uvThresh) alarmStatus = alarmStatus or ALARM_UNDER_VOLTAGE
        if (maxOf(iL1, iL2, iL3) > ocThresh) alarmStatus = alarmStatus or ALARM_OVER_CURRENT
        val pfTotal = currentValues.getOrDefault(50, 0.97)
        if (pfTotal < pfThresh) alarmStatus = alarmStatus or ALARM_LOW_PF
        if (pTotal > opThresh) alarmStatus = alarmStatus or ALARM_OVER_POWER
        if (minOf(vL1, vL2, vL3) < 50.0) alarmStatus = alarmStatus or ALARM_PHASE_LOSS
        for (addr in intArrayOf(62, 64, 66)) {
            if (currentValues.getOrDefault(addr, 0.0) > 8.0) alarmStatus = alarmStatus or ALARM_THD_HIGH
        }

        alarmStatus = alarmStatus and alarmMask
        currentValues[90] = alarmStatus.toDouble()

        // ── Device Status Word ───────────────────────────────────────
        var deviceStatus = STATUS_RUNNING
        if (server.isRunning) deviceStatus = deviceStatus or STATUS_TCP_ACTIVE
        if (alarmStatus > 0) deviceStatus = deviceStatus or STATUS_ALARM_ACTIVE
        currentValues[91] = deviceStatus.toDouble()

        // ── Write all values to Modbus server registers ──────────────
        writeToServer()
    }

    /** Push current simulation values to the Modbus TCP server registers. */
    private fun writeToServer() {
        for (reg in ALL_REGISTERS) {
            val value = currentValues[reg.address] ?: continue
            val holdingOnly = reg.writable
            when (reg.dataType) {
                DataType.FLOAT32 -> server.setFloat32(reg.address, value.toFloat(), holdingOnly)
                DataType.UINT32 -> server.setUint32(reg.address, value.toLong(), holdingOnly)
                DataType.UINT16 -> server.setRegister(reg.address, value.toInt() and 0xFFFF, holdingOnly)
            }
        }
    }

    private fun findRegister(address: Int): RegisterDef? {
        return ALL_REGISTERS.find { it.address == address }
    }
}
