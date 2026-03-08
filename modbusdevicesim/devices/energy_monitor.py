"""Energy Monitor device model.

Simulates a 3-phase energy monitoring device with register map inspired by
industry-standard meters (Schneider PM5xxx, Carlo Gavazzi EM series).

Register Map (0-based addresses):
══════════════════════════════════════════════════════════════════════════

MEASUREMENT REGISTERS (Read-Only — Input Registers FC04)
─────────────────────────────────────────────────────────────
  Addr  Parameter                 Type      Unit
  0-1   Voltage L1-N              FLOAT32   V
  2-3   Voltage L2-N              FLOAT32   V
  4-5   Voltage L3-N              FLOAT32   V
  6-7   Voltage L1-L2             FLOAT32   V
  8-9   Voltage L2-L3             FLOAT32   V
 10-11  Voltage L3-L1             FLOAT32   V
 12-13  Current L1                FLOAT32   A
 14-15  Current L2                FLOAT32   A
 16-17  Current L3                FLOAT32   A
 18-19  Current Neutral           FLOAT32   A
 20-21  Active Power L1           FLOAT32   kW
 22-23  Active Power L2           FLOAT32   kW
 24-25  Active Power L3           FLOAT32   kW
 26-27  Active Power Total        FLOAT32   kW
 28-29  Reactive Power L1         FLOAT32   kVAr
 30-31  Reactive Power L2         FLOAT32   kVAr
 32-33  Reactive Power L3         FLOAT32   kVAr
 34-35  Reactive Power Total      FLOAT32   kVAr
 36-37  Apparent Power L1         FLOAT32   kVA
 38-39  Apparent Power L2         FLOAT32   kVA
 40-41  Apparent Power L3         FLOAT32   kVA
 42-43  Apparent Power Total      FLOAT32   kVA
 44-45  Power Factor L1           FLOAT32   —
 46-47  Power Factor L2           FLOAT32   —
 48-49  Power Factor L3           FLOAT32   —
 50-51  Power Factor Total        FLOAT32   —
 52-53  Frequency                 FLOAT32   Hz
 54-55  Active Energy             UINT32    kWh
 56-57  Reactive Energy           UINT32    kVArh
 58-59  Active Energy Export      UINT32    kWh
 60-61  Apparent Energy           UINT32    kVAh
 62-63  Voltage L1 THD            FLOAT32   %
 64-65  Voltage L2 THD            FLOAT32   %
 66-67  Voltage L3 THD            FLOAT32   %
 68-69  Current L1 THD            FLOAT32   %
 70-71  Current L2 THD            FLOAT32   %
 72-73  Current L3 THD            FLOAT32   %
 74-75  Max Demand Active Power   FLOAT32   kW
 76-77  Max Demand Current        FLOAT32   A
 78-79  Avg Voltage L-N           FLOAT32   V
 80-81  Avg Voltage L-L           FLOAT32   V
 82-83  Avg Current               FLOAT32   A
 84-85  Voltage Unbalance         FLOAT32   %
 86-87  Current Unbalance         FLOAT32   %
 88-89  Run Hours                 UINT32    h
 90-91  Alarm Status Word         UINT16    —  (bitmask, read-only)
 92     Device Status Word        UINT16    —  (bitmask, read-only)

CONFIGURATION REGISTERS (Read/Write — Holding Registers FC03/06/16)
─────────────────────────────────────────────────────────────
  Addr  Parameter                 Type      Unit    Default
 100    CT Primary                UINT16    A       100
 101    CT Secondary              UINT16    A       5
 102    VT Primary                UINT16    V       220
 103    VT Secondary              UINT16    V       220
 104    System Type               UINT16    —       0 (0=3P4W, 1=3P3W, 2=1P2W)
 105    Nominal Frequency         UINT16    Hz      60
 106    Demand Period             UINT16    min     15
 107-108 Over-Voltage Threshold   FLOAT32   V       253.0
 109-110 Under-Voltage Threshold  FLOAT32   V       198.0
 111-112 Over-Current Threshold   FLOAT32   A       30.0
 113-114 Low PF Threshold         FLOAT32   —       0.85
 115-116 Over-Power Threshold     FLOAT32   kW      15.0
 117    Alarm Enable Mask         UINT16    —       0x001F (all enabled)
 118    Energy Reset Command      UINT16    —       0  (write 0x1234 to reset)
 119    Max Demand Reset Command  UINT16    —       0  (write 0x1234 to reset)
 120    Display Backlight         UINT16    s       60 (0=always on)
 121-122 Password                 UINT32    —       0
"""

from __future__ import annotations

from .base import DeviceModel, RegisterDefinition, DataType


# Alarm bit positions for Alarm Enable Mask (reg 117) and Alarm Status (reg 90)
ALARM_OVER_VOLTAGE  = 0x0001  # Bit 0
ALARM_UNDER_VOLTAGE = 0x0002  # Bit 1
ALARM_OVER_CURRENT  = 0x0004  # Bit 2
ALARM_LOW_PF        = 0x0008  # Bit 3
ALARM_OVER_POWER    = 0x0010  # Bit 4
ALARM_PHASE_LOSS    = 0x0020  # Bit 5
ALARM_PHASE_SEQ     = 0x0040  # Bit 6
ALARM_THD_HIGH      = 0x0080  # Bit 7

# Device status bits for Device Status Word (reg 92)
STATUS_RUNNING      = 0x0001  # Bit 0: simulation active
STATUS_TCP_ACTIVE   = 0x0002  # Bit 1: TCP server listening
STATUS_RTU_ACTIVE   = 0x0004  # Bit 2: RTU server listening
STATUS_ALARM_ACTIVE = 0x0008  # Bit 3: at least one alarm active
STATUS_ENERGY_OVF   = 0x0010  # Bit 4: energy counter overflow

# Magic value to trigger reset commands
RESET_MAGIC = 0x1234


class EnergyMonitor(DeviceModel):
    """3-phase energy monitoring device."""

    name = "MK-EM3P Energy Monitor"
    description = "3-Phase Energy Monitor — Voltage, Current, Power, Energy, THD"
    default_slave_id = 1

    def _define_registers(self):
        self.registers = [
            # ══════════════════════════════════════════════════════════
            # MEASUREMENT REGISTERS (read-only)
            # ══════════════════════════════════════════════════════════

            # ── Voltage ──────────────────────────────────────────────
            RegisterDefinition(0,  "Voltage L1-N",    DataType.FLOAT32, "V",    220.0,  210.0,  230.0),
            RegisterDefinition(2,  "Voltage L2-N",    DataType.FLOAT32, "V",    220.0,  210.0,  230.0),
            RegisterDefinition(4,  "Voltage L3-N",    DataType.FLOAT32, "V",    220.0,  210.0,  230.0),
            RegisterDefinition(6,  "Voltage L1-L2",   DataType.FLOAT32, "V",    380.0,  363.0,  398.0),
            RegisterDefinition(8,  "Voltage L2-L3",   DataType.FLOAT32, "V",    380.0,  363.0,  398.0),
            RegisterDefinition(10, "Voltage L3-L1",   DataType.FLOAT32, "V",    380.0,  363.0,  398.0),

            # ── Current ──────────────────────────────────────────────
            RegisterDefinition(12, "Current L1",       DataType.FLOAT32, "A",   15.0,   5.0,    25.0),
            RegisterDefinition(14, "Current L2",       DataType.FLOAT32, "A",   15.0,   5.0,    25.0),
            RegisterDefinition(16, "Current L3",       DataType.FLOAT32, "A",   15.0,   5.0,    25.0),
            RegisterDefinition(18, "Current Neutral",  DataType.FLOAT32, "A",    1.0,   0.0,     5.0),

            # ── Active Power ─────────────────────────────────────────
            RegisterDefinition(20, "Active Power L1",     DataType.FLOAT32, "kW",   3.3,   1.0,   5.5),
            RegisterDefinition(22, "Active Power L2",     DataType.FLOAT32, "kW",   3.3,   1.0,   5.5),
            RegisterDefinition(24, "Active Power L3",     DataType.FLOAT32, "kW",   3.3,   1.0,   5.5),
            RegisterDefinition(26, "Active Power Total",  DataType.FLOAT32, "kW",   9.9,   3.0,   16.5),

            # ── Reactive Power ───────────────────────────────────────
            RegisterDefinition(28, "Reactive Power L1",    DataType.FLOAT32, "kVAr", 0.8,  0.1,   2.0),
            RegisterDefinition(30, "Reactive Power L2",    DataType.FLOAT32, "kVAr", 0.8,  0.1,   2.0),
            RegisterDefinition(32, "Reactive Power L3",    DataType.FLOAT32, "kVAr", 0.8,  0.1,   2.0),
            RegisterDefinition(34, "Reactive Power Total", DataType.FLOAT32, "kVAr", 2.4,  0.3,   6.0),

            # ── Apparent Power (all phases + total) ──────────────────
            RegisterDefinition(36, "Apparent Power L1",    DataType.FLOAT32, "kVA",  3.4,  1.0,   5.8),
            RegisterDefinition(38, "Apparent Power L2",    DataType.FLOAT32, "kVA",  3.4,  1.0,   5.8),
            RegisterDefinition(40, "Apparent Power L3",    DataType.FLOAT32, "kVA",  3.4,  1.0,   5.8),
            RegisterDefinition(42, "Apparent Power Total", DataType.FLOAT32, "kVA",  10.2, 3.0,   17.4),

            # ── Power Factor ─────────────────────────────────────────
            RegisterDefinition(44, "Power Factor L1",    DataType.FLOAT32, "",   0.97,  0.85,  1.00),
            RegisterDefinition(46, "Power Factor L2",    DataType.FLOAT32, "",   0.97,  0.85,  1.00),
            RegisterDefinition(48, "Power Factor L3",    DataType.FLOAT32, "",   0.97,  0.85,  1.00),
            RegisterDefinition(50, "Power Factor Total", DataType.FLOAT32, "",   0.97,  0.85,  1.00),

            # ── Frequency ────────────────────────────────────────────
            RegisterDefinition(52, "Frequency",  DataType.FLOAT32, "Hz",  60.0,  59.90, 60.10),

            # ── Energy Accumulators ──────────────────────────────────
            RegisterDefinition(54, "Active Energy",        DataType.UINT32, "kWh",   0.0, 0.0, 999999.0),
            RegisterDefinition(56, "Reactive Energy",      DataType.UINT32, "kVArh", 0.0, 0.0, 999999.0),
            RegisterDefinition(58, "Active Energy Export", DataType.UINT32, "kWh",   0.0, 0.0, 999999.0),
            RegisterDefinition(60, "Apparent Energy",      DataType.UINT32, "kVAh",  0.0, 0.0, 999999.0),

            # ── THD (Total Harmonic Distortion) ──────────────────────
            RegisterDefinition(62, "Voltage L1 THD",  DataType.FLOAT32, "%",  2.5,  1.0,  5.0),
            RegisterDefinition(64, "Voltage L2 THD",  DataType.FLOAT32, "%",  2.5,  1.0,  5.0),
            RegisterDefinition(66, "Voltage L3 THD",  DataType.FLOAT32, "%",  2.5,  1.0,  5.0),
            RegisterDefinition(68, "Current L1 THD",  DataType.FLOAT32, "%",  8.0,  3.0,  15.0),
            RegisterDefinition(70, "Current L2 THD",  DataType.FLOAT32, "%",  8.0,  3.0,  15.0),
            RegisterDefinition(72, "Current L3 THD",  DataType.FLOAT32, "%",  8.0,  3.0,  15.0),

            # ── Demand ───────────────────────────────────────────────
            RegisterDefinition(74, "Max Demand Power",    DataType.FLOAT32, "kW", 12.0,  0.0,  20.0),
            RegisterDefinition(76, "Max Demand Current",  DataType.FLOAT32, "A",  18.0,  0.0,  30.0),

            # ── Averages ─────────────────────────────────────────────
            RegisterDefinition(78, "Avg Voltage L-N",  DataType.FLOAT32, "V",   220.0, 200.0, 240.0),
            RegisterDefinition(80, "Avg Voltage L-L",  DataType.FLOAT32, "V",   380.0, 346.0, 415.0),
            RegisterDefinition(82, "Avg Current",      DataType.FLOAT32, "A",    15.0,   0.0,  30.0),

            # ── Unbalance ────────────────────────────────────────────
            RegisterDefinition(84, "Voltage Unbalance", DataType.FLOAT32, "%",   1.0, 0.0, 10.0),
            RegisterDefinition(86, "Current Unbalance", DataType.FLOAT32, "%",   2.0, 0.0, 20.0),

            # ── Counters ─────────────────────────────────────────────
            RegisterDefinition(88, "Run Hours",  DataType.UINT32, "h",  0.0, 0.0, 999999.0),

            # ── Alarm & Status ───────────────────────────────────────
            RegisterDefinition(90, "Alarm Status",   DataType.UINT16, "",  0.0, 0.0, 65535.0),
            RegisterDefinition(91, "Device Status",  DataType.UINT16, "",  0.0, 0.0, 65535.0),

            # ══════════════════════════════════════════════════════════
            # CONFIGURATION REGISTERS (read/write — HMI parameters)
            # ══════════════════════════════════════════════════════════

            # ── Transformer Ratios ───────────────────────────────────
            RegisterDefinition(100, "CT Primary",     DataType.UINT16, "A",   100.0, 1.0, 5000.0, writable=True),
            RegisterDefinition(101, "CT Secondary",   DataType.UINT16, "A",     5.0, 1.0,    5.0, writable=True),
            RegisterDefinition(102, "VT Primary",     DataType.UINT16, "V",   220.0, 1.0, 35000.0, writable=True),
            RegisterDefinition(103, "VT Secondary",   DataType.UINT16, "V",   220.0, 1.0,   220.0, writable=True),

            # ── System Configuration ─────────────────────────────────
            RegisterDefinition(104, "System Type",        DataType.UINT16, "",    0.0, 0.0, 2.0, writable=True),
            RegisterDefinition(105, "Nominal Frequency",  DataType.UINT16, "Hz", 60.0, 50.0, 60.0, writable=True),
            RegisterDefinition(106, "Demand Period",      DataType.UINT16, "min", 15.0, 1.0, 60.0, writable=True),

            # ── Alarm Thresholds ─────────────────────────────────────
            RegisterDefinition(107, "Over-Voltage Threshold",  DataType.FLOAT32, "V",     253.0, 200.0, 300.0, writable=True),
            RegisterDefinition(109, "Under-Voltage Threshold", DataType.FLOAT32, "V",     198.0, 100.0, 230.0, writable=True),
            RegisterDefinition(111, "Over-Current Threshold",  DataType.FLOAT32, "A",      30.0,   1.0, 100.0, writable=True),
            RegisterDefinition(113, "Low PF Threshold",        DataType.FLOAT32, "",        0.85,  0.50,  1.00, writable=True),
            RegisterDefinition(115, "Over-Power Threshold",    DataType.FLOAT32, "kW",     15.0,   1.0, 100.0, writable=True),

            # ── Alarm Enable & Commands ──────────────────────────────
            RegisterDefinition(117, "Alarm Enable Mask",       DataType.UINT16, "",   31.0, 0.0, 255.0, writable=True),
            RegisterDefinition(118, "Energy Reset Cmd",        DataType.UINT16, "",    0.0, 0.0, 65535.0, writable=True),
            RegisterDefinition(119, "Demand Reset Cmd",        DataType.UINT16, "",    0.0, 0.0, 65535.0, writable=True),

            # ── Display & Communication ──────────────────────────────
            RegisterDefinition(120, "Backlight Timeout",  DataType.UINT16, "s",   60.0, 0.0, 600.0, writable=True),
            RegisterDefinition(121, "Password",           DataType.UINT32, "",     0.0, 0.0, 4294967295.0, writable=True),
        ]
