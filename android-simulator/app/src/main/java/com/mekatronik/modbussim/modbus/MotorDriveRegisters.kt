package com.mekatronik.modbussim.modbus

/**
 * MK-VFD7 Motor Drive — Register Map
 *
 * Mirrors the register definitions from the Python motor_drive.py.
 */

val VFD_MEASUREMENT_REGISTERS = listOf(
    // Output
    RegisterDef(0, "Output Frequency", "Hz", DataType.FLOAT32, default = 0.0, minValue = 0.0, maxValue = 60.0),
    RegisterDef(2, "Output Voltage", "V", DataType.FLOAT32, default = 0.0, minValue = 0.0, maxValue = 380.0),
    RegisterDef(4, "Output Current", "A", DataType.FLOAT32, default = 0.0, minValue = 0.0, maxValue = 25.0),
    RegisterDef(6, "Output Power", "kW", DataType.FLOAT32, default = 0.0, minValue = 0.0, maxValue = 10.0),
    // Motor
    RegisterDef(8, "Motor Speed", "RPM", DataType.FLOAT32, default = 0.0, minValue = 0.0, maxValue = 1800.0),
    RegisterDef(10, "Motor Torque", "%", DataType.FLOAT32, default = 0.0, minValue = 0.0, maxValue = 150.0),
    // Drive Internals
    RegisterDef(12, "DC Bus Voltage", "V", DataType.FLOAT32, default = 540.0, minValue = 300.0, maxValue = 700.0),
    RegisterDef(14, "Drive Temperature", "°C", DataType.FLOAT32, default = 35.0, minValue = 20.0, maxValue = 100.0),
    RegisterDef(16, "Motor Temperature", "°C", DataType.FLOAT32, default = 40.0, minValue = 20.0, maxValue = 120.0),
    // Counters
    RegisterDef(18, "Run Time", "h", DataType.UINT32),
    RegisterDef(20, "Energy Consumed", "kWh", DataType.UINT32),
    // Derived
    RegisterDef(22, "Power Factor", "", DataType.FLOAT32, default = 0.0, minValue = 0.0, maxValue = 1.0),
    RegisterDef(24, "Input Power", "kW", DataType.FLOAT32, default = 0.0, minValue = 0.0, maxValue = 12.0),
    // Status
    RegisterDef(26, "Drive Status", "", DataType.UINT16),
    RegisterDef(27, "Fault Code", "", DataType.UINT16),
    RegisterDef(28, "Warning Code", "", DataType.UINT16),
)

val VFD_CONFIG_REGISTERS = listOf(
    RegisterDef(100, "Control Word", "", DataType.UINT16, writable = true),
    RegisterDef(101, "Frequency Reference", "Hz", DataType.FLOAT32, writable = true, default = 30.0),
    RegisterDef(103, "Acceleration Time", "s", DataType.FLOAT32, writable = true, default = 10.0),
    RegisterDef(105, "Deceleration Time", "s", DataType.FLOAT32, writable = true, default = 10.0),
    RegisterDef(107, "Max Frequency", "Hz", DataType.FLOAT32, writable = true, default = 60.0),
    RegisterDef(109, "Min Frequency", "Hz", DataType.FLOAT32, writable = true, default = 0.5),
    RegisterDef(111, "Motor Rated Voltage", "V", DataType.UINT16, writable = true, default = 380.0),
    RegisterDef(112, "Motor Rated Current", "A", DataType.FLOAT32, writable = true, default = 15.0),
    RegisterDef(114, "Motor Rated Frequency", "Hz", DataType.UINT16, writable = true, default = 60.0),
    RegisterDef(115, "Motor Rated Speed", "RPM", DataType.UINT16, writable = true, default = 1750.0),
    RegisterDef(116, "Motor Rated Power", "kW", DataType.FLOAT32, writable = true, default = 7.5),
    RegisterDef(118, "V/F Pattern", "", DataType.UINT16, writable = true),
    RegisterDef(119, "Over-Current Threshold", "A", DataType.FLOAT32, writable = true, default = 25.0),
    RegisterDef(121, "Over-Voltage Threshold", "V", DataType.FLOAT32, writable = true, default = 420.0),
    RegisterDef(123, "Under-Voltage Threshold", "V", DataType.FLOAT32, writable = true, default = 320.0),
    RegisterDef(125, "Over-Temp Threshold", "°C", DataType.FLOAT32, writable = true, default = 85.0),
    RegisterDef(127, "Fault Reset Cmd", "", DataType.UINT16, writable = true),
    RegisterDef(128, "Energy Reset Cmd", "", DataType.UINT16, writable = true),
)

val VFD_ALL_REGISTERS = VFD_MEASUREMENT_REGISTERS + VFD_CONFIG_REGISTERS

// Drive Status Word bits (register 26)
const val VFD_STATUS_RUNNING = 0x0001
const val VFD_STATUS_FORWARD = 0x0002
const val VFD_STATUS_REVERSE = 0x0004
const val VFD_STATUS_AT_REF  = 0x0008
const val VFD_STATUS_ACCEL   = 0x0010
const val VFD_STATUS_DECEL   = 0x0020
const val VFD_STATUS_FAULT   = 0x0040
const val VFD_STATUS_WARNING = 0x0080
const val VFD_STATUS_JOG     = 0x0100

// Control Word bits (register 100)
const val VFD_CTRL_RUN       = 0x0001
const val VFD_CTRL_REVERSE   = 0x0002
const val VFD_CTRL_JOG       = 0x0004
const val VFD_CTRL_FAULT_RST = 0x0008
const val VFD_CTRL_ESTOP     = 0x0010

// Fault codes
const val VFD_FAULT_NONE         = 0
const val VFD_FAULT_OVERCURRENT  = 1
const val VFD_FAULT_OVERVOLTAGE  = 2
const val VFD_FAULT_UNDERVOLTAGE = 3
const val VFD_FAULT_OVERTEMP_DRV = 4
const val VFD_FAULT_OVERTEMP_MOT = 5

// Warning codes
const val VFD_WARN_NONE         = 0
const val VFD_WARN_HIGH_TEMP    = 1
const val VFD_WARN_HIGH_CURRENT = 2
const val VFD_WARN_HIGH_VOLTAGE = 3

const val VFD_RESET_MAGIC = 0x1234
