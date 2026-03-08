"""Motor Drive (Frequency Inverter / VFD) device model.

Simulates a 3-phase variable frequency drive with register map inspired by
industry-standard drives (ABB ACS580, Siemens G120, Danfoss FC302).

Register Map (0-based addresses):
══════════════════════════════════════════════════════════════════════════

MEASUREMENT / STATUS REGISTERS (Read-Only — Input Registers FC04)
─────────────────────────────────────────────────────────────
  Addr  Parameter                 Type      Unit
  0-1   Output Frequency          FLOAT32   Hz
  2-3   Output Voltage            FLOAT32   V
  4-5   Output Current            FLOAT32   A
  6-7   Output Power              FLOAT32   kW
  8-9   Motor Speed               FLOAT32   RPM
 10-11  Motor Torque              FLOAT32   %
 12-13  DC Bus Voltage            FLOAT32   V
 14-15  Drive Temperature         FLOAT32   °C
 16-17  Motor Temperature         FLOAT32   °C
 18-19  Run Time                  UINT32    h
 20-21  Energy Consumed           UINT32    kWh
 22-23  Power Factor              FLOAT32   —
 24-25  Input Power               FLOAT32   kW
 26     Drive Status Word         UINT16    —  (bitmask)
 27     Active Fault Code         UINT16    —
 28     Active Warning Code       UINT16    —

CONTROL / CONFIGURATION REGISTERS (Read/Write — Holding Registers FC03/06/16)
─────────────────────────────────────────────────────────────
  Addr  Parameter                 Type      Unit    Default
 100    Control Word              UINT16    —       0
 101-102 Frequency Reference      FLOAT32   Hz      30.0
 103-104 Acceleration Time        FLOAT32   s       10.0
 105-106 Deceleration Time        FLOAT32   s       10.0
 107-108 Max Frequency            FLOAT32   Hz      60.0
 109-110 Min Frequency            FLOAT32   Hz      0.5
 111    Motor Rated Voltage       UINT16    V       380
 112-113 Motor Rated Current      FLOAT32   A       15.0
 114    Motor Rated Frequency     UINT16    Hz      60
 115    Motor Rated Speed         UINT16    RPM     1750
 116-117 Motor Rated Power        FLOAT32   kW      7.5
 118    V/F Pattern               UINT16    —       0 (0=linear,1=square,2=custom)
 119-120 Over-Current Threshold   FLOAT32   A       25.0
 121-122 Over-Voltage Threshold   FLOAT32   V       420.0
 123-124 Under-Voltage Threshold  FLOAT32   V       320.0
 125-126 Over-Temp Threshold      FLOAT32   °C      85.0
 127    Fault Reset Command       UINT16    —       0  (write 0x1234 to reset)
 128    Energy Reset Command      UINT16    —       0  (write 0x1234 to reset)
"""

from __future__ import annotations

from .base import DeviceModel, RegisterDefinition, DataType


# ── Drive Status Word bits (register 26) ─────────────────────────────
STATUS_RUNNING     = 0x0001  # Bit 0: drive is running
STATUS_FORWARD     = 0x0002  # Bit 1: forward direction
STATUS_REVERSE     = 0x0004  # Bit 2: reverse direction
STATUS_AT_REF      = 0x0008  # Bit 3: output frequency = reference
STATUS_ACCEL       = 0x0010  # Bit 4: accelerating
STATUS_DECEL       = 0x0020  # Bit 5: decelerating
STATUS_FAULT       = 0x0040  # Bit 6: fault active
STATUS_WARNING     = 0x0080  # Bit 7: warning active
STATUS_JOG         = 0x0100  # Bit 8: jog mode active

# ── Control Word bits (register 100) ─────────────────────────────────
CTRL_RUN           = 0x0001  # Bit 0: run command
CTRL_REVERSE       = 0x0002  # Bit 1: reverse direction
CTRL_JOG           = 0x0004  # Bit 2: jog mode
CTRL_FAULT_RESET   = 0x0008  # Bit 3: reset faults
CTRL_ESTOP         = 0x0010  # Bit 4: emergency stop

# ── Fault codes (register 27) ────────────────────────────────────────
FAULT_NONE         = 0
FAULT_OVERCURRENT  = 1
FAULT_OVERVOLTAGE  = 2
FAULT_UNDERVOLTAGE = 3
FAULT_OVERTEMP_DRV = 4
FAULT_OVERTEMP_MOT = 5
FAULT_COMM_LOSS    = 6
FAULT_MOTOR_OVERLD = 7

# ── Warning codes (register 28) ──────────────────────────────────────
WARN_NONE          = 0
WARN_HIGH_TEMP     = 1
WARN_HIGH_CURRENT  = 2
WARN_HIGH_VOLTAGE  = 3

# Magic value to trigger reset commands
RESET_MAGIC = 0x1234


class MotorDrive(DeviceModel):
    """3-phase Variable Frequency Drive (VFD) / Frequency Inverter."""

    name = "MK-VFD7 Motor Drive"
    description = "Variable Frequency Drive — Speed, Torque, V/F Control"
    default_slave_id = 1

    def _define_registers(self):
        self.registers = [
            # ══════════════════════════════════════════════════════════
            # MEASUREMENT / STATUS REGISTERS (read-only)
            # ══════════════════════════════════════════════════════════

            # ── Output ──────────────────────────────────────────────
            RegisterDefinition(0,  "Output Frequency",  DataType.FLOAT32, "Hz",   0.0,   0.0,   60.0),
            RegisterDefinition(2,  "Output Voltage",     DataType.FLOAT32, "V",    0.0,   0.0,  380.0),
            RegisterDefinition(4,  "Output Current",     DataType.FLOAT32, "A",    0.0,   0.0,   25.0),
            RegisterDefinition(6,  "Output Power",       DataType.FLOAT32, "kW",   0.0,   0.0,   10.0),

            # ── Motor ───────────────────────────────────────────────
            RegisterDefinition(8,  "Motor Speed",        DataType.FLOAT32, "RPM",  0.0,   0.0, 1800.0),
            RegisterDefinition(10, "Motor Torque",       DataType.FLOAT32, "%",    0.0,   0.0,  150.0),

            # ── Drive Internals ─────────────────────────────────────
            RegisterDefinition(12, "DC Bus Voltage",     DataType.FLOAT32, "V",  540.0, 300.0,  700.0),
            RegisterDefinition(14, "Drive Temperature",  DataType.FLOAT32, "°C",  35.0,  20.0,  100.0),
            RegisterDefinition(16, "Motor Temperature",  DataType.FLOAT32, "°C",  40.0,  20.0,  120.0),

            # ── Counters ────────────────────────────────────────────
            RegisterDefinition(18, "Run Time",           DataType.UINT32, "h",    0.0,   0.0, 999999.0),
            RegisterDefinition(20, "Energy Consumed",    DataType.UINT32, "kWh",  0.0,   0.0, 999999.0),

            # ── Derived ─────────────────────────────────────────────
            RegisterDefinition(22, "Power Factor",       DataType.FLOAT32, "",    0.0,   0.0,    1.0),
            RegisterDefinition(24, "Input Power",        DataType.FLOAT32, "kW",  0.0,   0.0,   12.0),

            # ── Status ──────────────────────────────────────────────
            RegisterDefinition(26, "Drive Status",       DataType.UINT16, "",     0.0,   0.0, 65535.0),
            RegisterDefinition(27, "Fault Code",         DataType.UINT16, "",     0.0,   0.0,   255.0),
            RegisterDefinition(28, "Warning Code",       DataType.UINT16, "",     0.0,   0.0,   255.0),

            # ══════════════════════════════════════════════════════════
            # CONTROL / CONFIGURATION REGISTERS (read/write)
            # ══════════════════════════════════════════════════════════

            # ── Control ─────────────────────────────────────────────
            RegisterDefinition(100, "Control Word",          DataType.UINT16,  "",    0.0,   0.0, 65535.0, writable=True),
            RegisterDefinition(101, "Frequency Reference",   DataType.FLOAT32, "Hz", 30.0,   0.0,   60.0, writable=True),

            # ── Ramp Times ──────────────────────────────────────────
            RegisterDefinition(103, "Acceleration Time",     DataType.FLOAT32, "s",  10.0,   0.1,  600.0, writable=True),
            RegisterDefinition(105, "Deceleration Time",     DataType.FLOAT32, "s",  10.0,   0.1,  600.0, writable=True),

            # ── Frequency Limits ────────────────────────────────────
            RegisterDefinition(107, "Max Frequency",         DataType.FLOAT32, "Hz", 60.0,  10.0,  120.0, writable=True),
            RegisterDefinition(109, "Min Frequency",         DataType.FLOAT32, "Hz",  0.5,   0.0,   10.0, writable=True),

            # ── Motor Nameplate ─────────────────────────────────────
            RegisterDefinition(111, "Motor Rated Voltage",   DataType.UINT16, "V",  380.0, 100.0,  690.0, writable=True),
            RegisterDefinition(112, "Motor Rated Current",   DataType.FLOAT32, "A",  15.0,   0.5,  100.0, writable=True),
            RegisterDefinition(114, "Motor Rated Frequency", DataType.UINT16, "Hz",  60.0,  50.0,   60.0, writable=True),
            RegisterDefinition(115, "Motor Rated Speed",     DataType.UINT16, "RPM", 1750.0, 100.0, 3600.0, writable=True),
            RegisterDefinition(116, "Motor Rated Power",     DataType.FLOAT32, "kW",   7.5,   0.1,   50.0, writable=True),

            # ── V/F Pattern ─────────────────────────────────────────
            RegisterDefinition(118, "V/F Pattern",           DataType.UINT16, "",     0.0,   0.0,    2.0, writable=True),

            # ── Protection Thresholds ───────────────────────────────
            RegisterDefinition(119, "Over-Current Threshold",  DataType.FLOAT32, "A",  25.0,   1.0, 200.0, writable=True),
            RegisterDefinition(121, "Over-Voltage Threshold",  DataType.FLOAT32, "V", 420.0, 200.0, 800.0, writable=True),
            RegisterDefinition(123, "Under-Voltage Threshold", DataType.FLOAT32, "V", 320.0, 100.0, 500.0, writable=True),
            RegisterDefinition(125, "Over-Temp Threshold",     DataType.FLOAT32, "°C", 85.0,  50.0, 120.0, writable=True),

            # ── Commands ────────────────────────────────────────────
            RegisterDefinition(127, "Fault Reset Cmd",       DataType.UINT16, "",    0.0,   0.0, 65535.0, writable=True),
            RegisterDefinition(128, "Energy Reset Cmd",      DataType.UINT16, "",    0.0,   0.0, 65535.0, writable=True),
        ]
