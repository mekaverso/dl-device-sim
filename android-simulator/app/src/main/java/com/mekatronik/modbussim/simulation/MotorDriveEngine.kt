package com.mekatronik.modbussim.simulation

import com.mekatronik.modbussim.modbus.*
import kotlin.math.*
import kotlin.random.Random

/**
 * Simulation engine for the MK-VFD7 Motor Drive.
 *
 * Simulates realistic VFD behavior: ramping, V/F curve, slip,
 * thermal model, and fault/warning detection.
 */
class MotorDriveEngine(
    private val server: ModbusTcpServer,
) {
    private val timeOffset = Random.nextDouble(0.0, 1000.0)
    private val driftSpeed = 0.1
    private val ambientTemp = 25.0
    private val thermalTimeConst = 300.0 // seconds

    private var lastUpdateMs = System.currentTimeMillis()
    private val startTimeMs = System.currentTimeMillis()

    private var outputFreq = 0.0
    private var driveTemp = ambientTemp + 10.0
    private var motorTemp = ambientTemp + 15.0
    private var energyKwh = 0.0
    private var runHours = 0.0
    private var faultCode = VFD_FAULT_NONE
    private var faultLatched = false

    val currentValues = mutableMapOf<Int, Double>()

    init {
        for (reg in VFD_ALL_REGISTERS) {
            currentValues[reg.address] = reg.default
        }
    }

    private fun smoothNoise(t: Double, phase: Double): Double {
        return (0.5 * sin(t * 0.7 + phase) +
                0.25 * sin(t * 1.3 + phase * 2.1) +
                0.15 * sin(t * 2.9 + phase * 0.7) +
                0.10 * sin(t * 5.1 + phase * 1.3))
    }

    fun readConfigFromServer() {
        for (reg in VFD_ALL_REGISTERS) {
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

        // Handle fault reset
        if (currentValues.getOrDefault(127, 0.0).toInt() == VFD_RESET_MAGIC) {
            faultCode = VFD_FAULT_NONE; faultLatched = false
            currentValues[127] = 0.0
        }
        // Handle energy reset
        if (currentValues.getOrDefault(128, 0.0).toInt() == VFD_RESET_MAGIC) {
            energyKwh = 0.0; currentValues[20] = 0.0; currentValues[128] = 0.0
        }
    }

    fun update() {
        val now = System.currentTimeMillis()
        val dt = (now - lastUpdateMs) / 1000.0
        lastUpdateMs = now
        val t = (now / 1000.0 + timeOffset) * driftSpeed

        val cv = currentValues

        // Read control word
        val ctrl = cv.getOrDefault(100, 0.0).toInt()
        var runCmd = (ctrl and VFD_CTRL_RUN != 0) && (ctrl and VFD_CTRL_ESTOP == 0)
        val reverse = ctrl and VFD_CTRL_REVERSE != 0
        val jog = ctrl and VFD_CTRL_JOG != 0

        // Read config
        val freqRef = cv.getOrDefault(101, 30.0).coerceIn(0.0, cv.getOrDefault(107, 60.0))
        val accelTime = cv.getOrDefault(103, 10.0).coerceAtLeast(0.1)
        val decelTime = cv.getOrDefault(105, 10.0).coerceAtLeast(0.1)
        val maxFreq = cv.getOrDefault(107, 60.0)
        val minFreq = cv.getOrDefault(109, 0.5)
        val motorRatedV = cv.getOrDefault(111, 380.0)
        val motorRatedI = cv.getOrDefault(112, 15.0)
        val motorRatedFreq = cv.getOrDefault(114, 60.0)
        val motorRatedSpeed = cv.getOrDefault(115, 1750.0)
        val motorRatedPower = cv.getOrDefault(116, 7.5)
        val vfPattern = cv.getOrDefault(118, 0.0).toInt()

        if (faultLatched) runCmd = false

        // Frequency ramping
        val targetFreq = if (runCmd) {
            if (jog) minFreq * 2 else freqRef
        } else 0.0

        val rampRateUp = maxFreq / accelTime
        val rampRateDown = maxFreq / decelTime
        var isAccel = false
        var isDecel = false

        if (outputFreq < targetFreq) {
            outputFreq = minOf(targetFreq, outputFreq + rampRateUp * dt)
            isAccel = true
        } else if (outputFreq > targetFreq) {
            outputFreq = maxOf(targetFreq, outputFreq - rampRateDown * dt)
            isDecel = true
        }
        val atRef = abs(outputFreq - targetFreq) < 0.05
        if (outputFreq < 0.1) outputFreq = 0.0
        cv[0] = outputFreq

        // Output voltage (V/F curve)
        val outputVoltage = if (motorRatedFreq > 0 && outputFreq > 0) {
            val freqRatio = outputFreq / motorRatedFreq
            val vRatio = when (vfPattern) {
                0 -> freqRatio           // Linear
                1 -> freqRatio * freqRatio // Square
                else -> 0.05 + 0.95 * freqRatio
            }
            minOf(motorRatedV, motorRatedV * vRatio) + smoothNoise(t, 1.0) * 0.5
        } else 0.0
        cv[2] = maxOf(0.0, outputVoltage)

        // Motor speed
        val speed = if (outputFreq > 0 && motorRatedFreq > 0) {
            val s = motorRatedSpeed * (outputFreq / motorRatedFreq)
            val slipNoise = smoothNoise(t * 0.3, 5.0) * s * 0.015
            maxOf(0.0, s - abs(slipNoise))
        } else 0.0
        cv[8] = speed

        // Load simulation
        val baseLoad = 0.6
        val loadVariation = smoothNoise(t * 0.2, 3.0) * 0.15
        val loadFactor = baseLoad + loadVariation

        // Output current
        val outputCurrent = if (outputFreq > 0) {
            val magCurrent = motorRatedI * 0.3
            val loadCurrent = motorRatedI * loadFactor * (outputFreq / motorRatedFreq)
            maxOf(0.0, sqrt(magCurrent * magCurrent + loadCurrent * loadCurrent) + smoothNoise(t, 2.0) * 0.2)
        } else 0.0
        cv[4] = outputCurrent

        // Output power
        val outputPower = if (outputFreq > 0) {
            maxOf(0.0, outputVoltage * outputCurrent * sqrt(3.0) / 1000.0 * 0.95)
        } else 0.0
        cv[6] = outputPower

        // Motor torque (%)
        cv[10] = if (outputFreq > 0 && motorRatedPower > 0 && speed > 0) {
            val ratedTorqueNm = if (motorRatedSpeed > 0)
                motorRatedPower * 1000 / (motorRatedSpeed * 2 * PI / 60) else 1.0
            val actualTorqueNm = outputPower * 1000 / (speed * 2 * PI / 60)
            ((actualTorqueNm / ratedTorqueNm) * 100).coerceIn(0.0, 150.0)
        } else 0.0

        // DC bus voltage
        val dcNominal = motorRatedV * sqrt(2.0)
        val dcBus = dcNominal + smoothNoise(t * 2.0, 7.0) * 3.0
        cv[12] = maxOf(0.0, dcBus)

        // Temperature simulation
        val alpha = dt / (thermalTimeConst + dt)
        val driveHeat = (outputCurrent / motorRatedI).let { it * it } * 40.0
        val driveTarget = ambientTemp + 10.0 + driveHeat
        driveTemp += alpha * (driveTarget - driveTemp) + smoothNoise(t * 0.1, 8.0) * 0.2
        cv[14] = driveTemp

        val motorHeat = (outputCurrent / motorRatedI).let { it * it } * 55.0
        val motorTarget = ambientTemp + 15.0 + motorHeat
        motorTemp += alpha * (motorTarget - motorTemp) + smoothNoise(t * 0.08, 9.0) * 0.3
        cv[16] = motorTemp

        // Run time & energy
        if (outputFreq > 0) runHours += dt / 3600.0
        cv[18] = runHours.toLong().toDouble()
        energyKwh += outputPower * (dt / 3600.0)
        cv[20] = energyKwh.toLong().toDouble()

        // Power factor
        cv[22] = if (outputFreq > 0)
            (0.6 + loadFactor * 0.35 + smoothNoise(t * 0.15, 10.0) * 0.02).coerceIn(0.0, 1.0)
        else 0.0

        // Input power
        cv[24] = if (outputPower > 0) outputPower / 0.95 else 0.0

        // Fault/warning detection
        val ocThresh = cv.getOrDefault(119, 25.0)
        val ovThresh = cv.getOrDefault(121, 420.0)
        val uvThresh = cv.getOrDefault(123, 320.0)
        val otThresh = cv.getOrDefault(125, 85.0)

        var warning = VFD_WARN_NONE
        if (!faultLatched) {
            when {
                outputCurrent > ocThresh -> { faultCode = VFD_FAULT_OVERCURRENT; faultLatched = true }
                dcBus > ovThresh * sqrt(2.0) -> { faultCode = VFD_FAULT_OVERVOLTAGE; faultLatched = true }
                dcBus < uvThresh * sqrt(2.0) * 0.9 && outputFreq > 0 -> { faultCode = VFD_FAULT_UNDERVOLTAGE; faultLatched = true }
                driveTemp > otThresh -> { faultCode = VFD_FAULT_OVERTEMP_DRV; faultLatched = true }
                motorTemp > otThresh + 15 -> { faultCode = VFD_FAULT_OVERTEMP_MOT; faultLatched = true }
            }
        }
        when {
            driveTemp > otThresh * 0.85 -> warning = VFD_WARN_HIGH_TEMP
            outputCurrent > ocThresh * 0.85 -> warning = VFD_WARN_HIGH_CURRENT
            dcBus > ovThresh * sqrt(2.0) * 0.9 -> warning = VFD_WARN_HIGH_VOLTAGE
        }
        cv[27] = faultCode.toDouble()
        cv[28] = warning.toDouble()

        // Drive status word
        var status = 0
        if (outputFreq > 0) {
            status = status or VFD_STATUS_RUNNING
            status = status or if (reverse) VFD_STATUS_REVERSE else VFD_STATUS_FORWARD
            if (atRef) status = status or VFD_STATUS_AT_REF
            if (isAccel) status = status or VFD_STATUS_ACCEL
            if (isDecel) status = status or VFD_STATUS_DECEL
            if (jog) status = status or VFD_STATUS_JOG
        }
        if (faultLatched) status = status or VFD_STATUS_FAULT
        if (warning != VFD_WARN_NONE) status = status or VFD_STATUS_WARNING
        cv[26] = status.toDouble()

        // Write to server
        writeToServer()
    }

    private fun writeToServer() {
        for (reg in VFD_ALL_REGISTERS) {
            val value = currentValues[reg.address] ?: continue
            val holdingOnly = reg.writable
            when (reg.dataType) {
                DataType.FLOAT32 -> server.setFloat32(reg.address, value.toFloat(), holdingOnly)
                DataType.UINT32 -> server.setUint32(reg.address, value.toLong(), holdingOnly)
                DataType.UINT16 -> server.setRegister(reg.address, value.toInt() and 0xFFFF, holdingOnly)
            }
        }
    }
}
