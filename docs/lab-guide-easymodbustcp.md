# Lab Guide — Modbus TCP Communication
## ModbusDeviceSIM (Android) ↔ EasyModbusTCP (PC)

**Mekatronik — Advanced Engineering**

---

## Overview

```
[ Android Phone ]                    [ Laptop ]
  MK-EM3P or MK-VFD7          EasyModbusTCP Client
  Modbus TCP Server  ←──WiFi──→  Modbus TCP Client
  Port 502                        (same subnet)
```

The phone acts as a **Modbus TCP server** (the device). The laptop acts as the **master/client** that polls and writes registers.

---

## Part 1 — Android App Setup

1. Open the **ModbusDeviceSIM** app on your phone.
2. In the **Device Type** card, tap either:
   - **MK-EM3P** — 3-phase energy monitor
   - **MK-VFD7** — variable frequency drive (motor drive)
3. Tap **START**. The status changes to **RUNNING** in green.
4. Note the address shown below the status, e.g.:
   ```
   192.168.1.45:502
   ```
   This is your **server IP** — write it down.
5. Keep the screen on (prevent sleep) while the lab is running.

> **Tip:** Make sure your phone's WiFi is connected to the **same network** as your laptop before pressing START.

---

## Part 2 — Network Verification

Both devices must be on the same local network (same WiFi router).

**Check your laptop's IP:**
- Windows: open `cmd` → type `ipconfig`
- Look for the **IPv4 Address** under your WiFi adapter, e.g. `192.168.1.20`

**The first three octets must match the phone's IP:**

| Phone IP       | Laptop IP      | Same network? |
|----------------|----------------|---------------|
| 192.168.1.45   | 192.168.1.20   | ✅ Yes        |
| 192.168.1.45   | 10.0.0.15      | ❌ No         |

**Quick connectivity test:**
Open `cmd` and ping the phone:
```
ping 192.168.1.45
```
If you get replies, you're ready to proceed.

> **If ping fails:** Check that both are on the same WiFi network. Some phones block ICMP (ping) — that's OK. Proceed to Part 3 and try to connect anyway.

---

## Part 3 — Connecting with EasyModbusTCP

1. Open **EasyModbusTCP** on your laptop.
2. Fill in the connection fields:

| Field       | Value                             |
|-------------|-----------------------------------|
| IP Address  | Phone's IP (e.g. `192.168.1.45`) |
| Port        | `502`                             |
| Unit ID     | `1`                               |

3. Click **Connect**. The status indicator should turn green.
4. On the phone, the **Clients** counter increments to `1` — confirming the connection.

---

## Part 4 — MK-EM3P Energy Monitor

### Register Map Summary

All float values use **IEEE 754 FLOAT32** spread across **2 consecutive 16-bit registers** (big-endian word order).

**Measurement Registers — read with FC04 (Read Input Registers)**

| Address | Parameter          | Type    | Unit | Notes      |
|---------|--------------------|---------|------|------------|
| 0–1     | Voltage L1-N       | FLOAT32 | V    | ~220 V     |
| 2–3     | Voltage L2-N       | FLOAT32 | V    |            |
| 4–5     | Voltage L3-N       | FLOAT32 | V    |            |
| 6–7     | Voltage L1-L2      | FLOAT32 | V    | ~380 V     |
| 8–9     | Voltage L2-L3      | FLOAT32 | V    |            |
| 10–11   | Voltage L3-L1      | FLOAT32 | V    |            |
| 12–13   | Current L1         | FLOAT32 | A    |            |
| 14–15   | Current L2         | FLOAT32 | A    |            |
| 16–17   | Current L3         | FLOAT32 | A    |            |
| 18–19   | Current Neutral    | FLOAT32 | A    |            |
| 20–21   | Active Power L1    | FLOAT32 | kW   |            |
| 22–23   | Active Power L2    | FLOAT32 | kW   |            |
| 24–25   | Active Power L3    | FLOAT32 | kW   |            |
| 26–27   | Active Power Total | FLOAT32 | kW   |            |
| 28–29   | Reactive Power L1  | FLOAT32 | kVAr |            |
| 34–35   | Reactive Power Total| FLOAT32| kVAr |            |
| 36–37   | Apparent Power L1  | FLOAT32 | kVA  |            |
| 42–43   | Apparent Power Total| FLOAT32| kVA  |            |
| 44–45   | Power Factor L1    | FLOAT32 | —    | 0.85–1.00  |
| 50–51   | Power Factor Total | FLOAT32 | —    |            |
| 52–53   | Frequency          | FLOAT32 | Hz   | ~60 Hz     |
| 54–55   | Active Energy      | UINT32  | kWh  |            |
| 56–57   | Reactive Energy    | UINT32  | kVArh|            |
| 62–63   | Voltage L1 THD     | FLOAT32 | %    |            |
| 68–69   | Current L1 THD     | FLOAT32 | %    |            |
| 74–75   | Max Demand Power   | FLOAT32 | kW   |            |
| 78–79   | Avg Voltage L-N    | FLOAT32 | V    |            |
| 82–83   | Avg Current        | FLOAT32 | A    |            |
| 84–85   | Voltage Unbalance  | FLOAT32 | %    |            |
| 86–87   | Current Unbalance  | FLOAT32 | %    |            |
| 88–89   | Run Hours          | UINT32  | h    |            |
| 90      | Alarm Status       | UINT16  | —    | bitmask    |
| 91      | Device Status      | UINT16  | —    | bitmask    |

**Configuration Registers — read/write with FC03 (Read Holding Registers)**

| Address  | Parameter               | Type    | Default |
|----------|-------------------------|---------|---------|
| 100      | CT Primary              | UINT16  | 100 A   |
| 101      | CT Secondary            | UINT16  | 5 A     |
| 102      | VT Primary              | UINT16  | 220 V   |
| 103      | VT Secondary            | UINT16  | 220 V   |
| 104      | System Type             | UINT16  | 0       |
| 105      | Nominal Frequency       | UINT16  | 60 Hz   |
| 106      | Demand Period           | UINT16  | 15 min  |
| 107–108  | Over-Voltage Threshold  | FLOAT32 | 253 V   |
| 109–110  | Under-Voltage Threshold | FLOAT32 | 198 V   |
| 111–112  | Over-Current Threshold  | FLOAT32 | 30 A    |
| 113–114  | Low PF Threshold        | FLOAT32 | 0.85    |
| 115–116  | Over-Power Threshold    | FLOAT32 | 15 kW   |
| 117      | Alarm Enable Mask       | UINT16  | 0x001F  |
| 118      | Energy Reset Cmd        | UINT16  | —       |
| 119      | Demand Reset Cmd        | UINT16  | —       |
| 120      | Backlight Timeout       | UINT16  | 60 s    |

**Alarm Status Bits — Register 90**

| Bit | Mask   | Alarm              |
|-----|--------|--------------------|
| 0   | 0x0001 | Over-Voltage       |
| 1   | 0x0002 | Under-Voltage      |
| 2   | 0x0004 | Over-Current       |
| 3   | 0x0008 | Low Power Factor   |
| 4   | 0x0010 | Over-Power         |
| 5   | 0x0020 | Phase Loss         |
| 7   | 0x0080 | THD High           |

---

### Exercise 4.1 — Read All Measurements

In EasyModbusTCP, go to the **Read Input Registers (FC04)** tab:

| Field            | Value |
|------------------|-------|
| Start Address    | `0`   |
| Number of values | `92`  |

Click **Read**. You will see 92 raw 16-bit values.

> **Reading FLOAT32 values:** Each parameter uses 2 consecutive registers. To decode:
> - Take registers at address N and N+1
> - Combine as: `bits = (reg[N] << 16) | reg[N+1]`
> - Interpret the 32-bit result as an IEEE 754 float
>
> EasyModbusTCP can display values as floats — select **"Float (ABCD)"** in the data type dropdown if available.

**Example — Voltage L1-N (address 0):**
- If you see `0x4360` at address 0 and `0x0000` at address 1
- Combined: `0x43600000` → **224.0 V** ✓

---

### Exercise 4.2 — Read Config Registers

Go to **Read Holding Registers (FC03)** tab:

| Field            | Value |
|------------------|-------|
| Start Address    | `100` |
| Number of values | `22`  |

Click **Read**. You will see the current CT/VT ratios, thresholds, and alarm mask.

---

### Exercise 4.3 — Write a Config Register

Change the **CT Primary** ratio (address 100) to 200 A.

Go to **Write Single Register (FC06)** tab:

| Field    | Value |
|----------|-------|
| Register | `100` |
| Value    | `200` |

Click **Write**. Read the holding registers again (Exercise 4.2) — register 100 should now show `200`.

---

### Exercise 4.4 — Change Over-Voltage Threshold (FLOAT32 Write)

The threshold at address 107–108 is FLOAT32. To write **260.0 V**:

1. Convert `260.0` to IEEE 754: `0x43820000`
   - High word: `0x4382` = **17282**
   - Low word:  `0x0000` = **0**

2. Go to **Write Multiple Registers (FC16)** tab:

| Field            | Value   |
|------------------|---------|
| Start Address    | `107`   |
| Number of values | `2`     |
| Value 1          | `17282` |
| Value 2          | `0`     |

Click **Write**, then read back to confirm.

> **FLOAT32 converter tool:** Use any online IEEE 754 converter, or use the Windows Calculator in Programmer mode.

---

## Part 5 — MK-VFD7 Motor Drive

### Register Map Summary

**Measurement Registers — FC04 (Read Input Registers)**

| Address | Parameter        | Type    | Unit | Notes                     |
|---------|------------------|---------|------|---------------------------|
| 0–1     | Output Frequency | FLOAT32 | Hz   | 0 when stopped            |
| 2–3     | Output Voltage   | FLOAT32 | V    |                           |
| 4–5     | Output Current   | FLOAT32 | A    |                           |
| 6–7     | Output Power     | FLOAT32 | kW   |                           |
| 8–9     | Motor Speed      | FLOAT32 | RPM  |                           |
| 10–11   | Motor Torque     | FLOAT32 | %    |                           |
| 12–13   | DC Bus Voltage   | FLOAT32 | V    | ~540 V                    |
| 14–15   | Drive Temperature| FLOAT32 | °C   |                           |
| 16–17   | Motor Temperature| FLOAT32 | °C   |                           |
| 18–19   | Run Time         | UINT32  | h    |                           |
| 20–21   | Energy Consumed  | UINT32  | kWh  |                           |
| 22–23   | Power Factor     | FLOAT32 | —    |                           |
| 24–25   | Input Power      | FLOAT32 | kW   |                           |
| 26      | Drive Status     | UINT16  | —    | bitmask (see table below) |
| 27      | Fault Code       | UINT16  | —    | 0 = no fault              |
| 28      | Warning Code     | UINT16  | —    | 0 = no warning            |

**Drive Status Word — Register 26**

| Bit | Mask   | Meaning       |
|-----|--------|---------------|
| 0   | 0x0001 | Running       |
| 1   | 0x0002 | Forward       |
| 2   | 0x0004 | Reverse       |
| 3   | 0x0008 | At reference  |
| 4   | 0x0010 | Accelerating  |
| 5   | 0x0020 | Decelerating  |
| 6   | 0x0040 | Fault active  |
| 7   | 0x0080 | Warning active|
| 8   | 0x0100 | Jog active    |

**Configuration / Control Registers — FC03 (Read/Write Holding Registers)**

| Address  | Parameter             | Type    | Default  |
|----------|-----------------------|---------|----------|
| 100      | Control Word          | UINT16  | 0        |
| 101–102  | Frequency Reference   | FLOAT32 | 30.0 Hz  |
| 103–104  | Acceleration Time     | FLOAT32 | 10.0 s   |
| 105–106  | Deceleration Time     | FLOAT32 | 10.0 s   |
| 107–108  | Max Frequency         | FLOAT32 | 60.0 Hz  |
| 109–110  | Min Frequency         | FLOAT32 | 0.5 Hz   |
| 111      | Motor Rated Voltage   | UINT16  | 380 V    |
| 112–113  | Motor Rated Current   | FLOAT32 | 15.0 A   |
| 114      | Motor Rated Frequency | UINT16  | 60 Hz    |
| 115      | Motor Rated Speed     | UINT16  | 1750 RPM |
| 116–117  | Motor Rated Power     | FLOAT32 | 7.5 kW   |
| 118      | V/F Pattern           | UINT16  | 0        |
| 119–120  | Over-Current Threshold| FLOAT32 | 25.0 A   |
| 121–122  | Over-Voltage Threshold| FLOAT32 | 420.0 V  |
| 123–124  | Under-Voltage Threshold| FLOAT32| 320.0 V  |
| 125–126  | Over-Temp Threshold   | FLOAT32 | 85.0 °C  |
| 127      | Fault Reset Cmd       | UINT16  | —        |
| 128      | Energy Reset Cmd      | UINT16  | —        |

**Control Word — Register 100**

| Bit | Mask   | Action              |
|-----|--------|---------------------|
| 0   | 0x0001 | RUN (1 = run)       |
| 1   | 0x0002 | REVERSE direction   |
| 2   | 0x0004 | JOG                 |
| 3   | 0x0008 | Fault Reset         |
| 4   | 0x0010 | Emergency Stop      |

---

### Exercise 5.1 — Read Drive Status

In **Read Input Registers (FC04)**:

| Field            | Value |
|------------------|-------|
| Start Address    | `0`   |
| Number of values | `29`  |

While the drive is idle (just started), register 26 should be `0` (not running). The frequency registers (0–1) should read approximately `0.0`.

---

### Exercise 5.2 — Start the Drive via Modbus (Remote Control)

> **Important:** Make sure the phone's VFD control is in **REMOTE** mode (the LOCAL/REMOTE toggle must be set to REMOTE).

**Step 1 — Set frequency reference to 45 Hz.**

Convert `45.0` to IEEE 754: `0x42340000`
- High word: `0x4234` = **16948**
- Low word:  `0x0000` = **0**

Write Multiple Registers (FC16):

| Field            | Value   |
|------------------|---------|
| Start Address    | `101`   |
| Number of values | `2`     |
| Value 1          | `16948` |
| Value 2          | `0`     |

**Step 2 — Send RUN command.**

Write Single Register (FC06):

| Field    | Value |
|----------|-------|
| Register | `100` |
| Value    | `1`   |

Bit 0 = RUN. On the phone, the **RUN** LED lights up and the LCD shows frequency and speed ramping up.

**Step 3 — Monitor acceleration.**

Read Input Registers FC04, start `0`, quantity `10`. Watch registers 0–1 (frequency) and 8–9 (speed) ramp up to the reference value.

**Step 4 — Stop the drive.**

Write Single Register FC06, register `100`, value `0`.

---

### Exercise 5.3 — Run in Reverse

Write Control Word (register 100) = `3`:
- bit 0 = RUN
- bit 1 = REVERSE

```
FC06 → Register 100 → Value 3
```

The **REV** LED on the phone lights up. Read the Drive Status Word (register 26) and verify bits 0 and 2 are set (`0x0005`).

---

### Exercise 5.4 — Change Acceleration Time

To set acceleration time to 5.0 seconds:

Convert `5.0` to IEEE 754: `0x40A00000`
- High word: `0x40A0` = **16544**
- Low word:  `0x0000` = **0**

Write Multiple Registers (FC16):

| Field            | Value   |
|------------------|---------|
| Start Address    | `103`   |
| Number of values | `2`     |
| Value 1          | `16544` |
| Value 2          | `0`     |

Start the drive and observe it reaches reference frequency faster than before.

---

### Exercise 5.5 — Fault Reset

If a fault occurs (register 27 ≠ 0):

1. Write the fault reset magic value:

```
FC06 → Register 127 → Value 4660   (= 0x1234)
```

2. Clear the control word:

```
FC06 → Register 100 → Value 0
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Cannot connect | Wrong IP or different subnet | Recheck `ipconfig` and the IP shown in the app |
| Connect OK but timeout on read | Phone screen off / app backgrounded | Wake phone, keep app in foreground |
| Values all zero | Server not running | Check phone — tap START |
| Wrote a register but value bounced back | Simulation overwrites measurement registers | Only config registers (100+) are persistently writable |
| FC06 write rejected | Writing to a read-only measurement register | Write only to addresses 100 and above |
| Drive does not respond to Control Word | Control mode is LOCAL | Switch phone toggle to REMOTE |

---

## Appendix — Common IEEE 754 Float Values

| Value (float) | Hex        | High word | Low word |
|---------------|------------|-----------|----------|
| 0.5 Hz        | 0x3F000000 | 16128     | 0        |
| 5.0 s         | 0x40A00000 | 16544     | 0        |
| 10.0 s        | 0x41200000 | 16672     | 0        |
| 30.0 Hz       | 0x41F00000 | 16880     | 0        |
| 45.0 Hz       | 0x42340000 | 16948     | 0        |
| 60.0 Hz       | 0x42700000 | 17008     | 0        |
| 198.0 V       | 0x43460000 | 17222     | 0        |
| 220.0 V       | 0x436C0000 | 17260     | 0        |
| 253.0 V       | 0x437D0000 | 17277     | 0        |
| 260.0 V       | 0x43820000 | 17282     | 0        |
| 380.0 V       | 0x43BE0000 | 17342     | 0        |
| 420.0 V       | 0x43D20000 | 17362     | 0        |
| 0.85 (PF)     | 0x3F59999A | 16217     | 39322    |
| 0.95 (PF)     | 0x3F733333 | 16243     | 13107    |
| 15.0 kW       | 0x41700000 | 16752     | 0        |
| 25.0 A        | 0x41C80000 | 16840     | 0        |
| 30.0 A        | 0x41F00000 | 16880     | 0        |

> **Tip:** To convert any float yourself, use an online IEEE 754 converter and enter the value. Copy the 8-digit hex result. Split it into the first 4 digits (high word) and last 4 digits (low word). Convert each from hex to decimal for EasyModbusTCP.
