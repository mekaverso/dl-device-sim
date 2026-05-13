# Lab Guide — Modbus TCP with CODESYS
## ModbusDeviceSIM (Android) ↔ CODESYS SoftPLC

**Mekatronik — Advanced Engineering**

---

## Overview

```
┌─────────────────────────────────────────┐       ┌──────────────────┐
│              Laptop                     │       │   Android Phone  │
│                                         │       │                  │
│  ┌──────────────────┐   loopback        │       │  ModbusDeviceSIM │
│  │ CODESYS IDE      │◄─────────────────►│       │  MK-EM3P /       │
│  │ (Dev. System V3) │   127.0.0.1       │       │  MK-VFD7         │
│  └──────────────────┘                   │  WiFi │                  │
│  ┌──────────────────┐                   │◄─────►│  Modbus TCP      │
│  │ CODESYS Control  │◄──────────────────┘       │  Server :5020    │
│  │ Win (SoftPLC)    │   Modbus TCP Client        │  Unit ID: 1      │
│  └──────────────────┘                           └──────────────────┘
└─────────────────────────────────────────┘
```

The SoftPLC (**CODESYS Control Win**) runs on your laptop and acts as the Modbus TCP master (client). It polls the Android app, which acts as the Modbus TCP slave (server).

---

## Prerequisites

| Software | Where to get it |
|----------|-----------------|
| CODESYS Development System V3 | CODESYS Store → free download |
| CODESYS Control Win V3 | CODESYS Store → free 2-hour trial runtime |

Both must be installed on the student laptop. The Development System is the IDE; Control Win is the SoftPLC runtime that executes the PLC program.

> **Note:** CODESYS Control Win runs as a Windows service. After installation, start it from the system tray icon or via **Start → CODESYS → CODESYS Control Win → Start**.

---

## Part 1 — Start the Android App

1. Open **ModbusDeviceSIM** on the phone.
2. Select the device: **MK-EM3P** (energy monitor) or **MK-VFD7** (motor drive).
3. Tap **START** — the server status turns green.
4. Note the IP address displayed, e.g.: `192.168.1.45:5020`
5. Keep the screen on throughout the lab.

---

## Part 2 — Create a New CODESYS Project

1. Open **CODESYS Development System**.
2. Go to **File → New Project**.
3. Select **Standard Project**, click **OK**.
4. In the dialog:
   - **Device:** `CODESYS Control Win V3 x64` (or x86 — match your installation)
   - **PLC_PRG language:** `Structured Text (ST)`
5. Click **OK**.

---

## Part 3 — Connect the IDE to the SoftPLC

1. In the menu, go to **Online → Communication Settings**.
2. Click **Add Gateway** → select **Local (TCP/IP)** → confirm with **OK**.
3. Click **Scan Network**. CODESYS Control Win should appear in the list.
4. Double-click it to select it as the active communication path.
5. Click **OK**.

> **Test the connection:** Go to **Online → Login** (Ctrl+L). The IDE connects to the SoftPLC. Go to **Online → Logout** afterwards — you'll log in again after adding devices.

---

## Part 4 — Add a Modbus TCP Master

The **Device Tree** is on the left panel (tab: **Devices**).

1. Right-click the root device (e.g., `CODESYS Control Win`) → **Add Device…**
2. In the catalog, navigate to:
   `Fieldbuses → Modbus → Modbus TCP → Modbus TCP Master`
3. Select it and click **Add Device**.

> The Modbus TCP Master represents the SoftPLC's role as the Modbus **client** — it initiates the connection to the phone.

---

## Part 5 — Add the Phone as a Modbus TCP Slave

> **Naming note:** In the CODESYS device tree, "Modbus TCP Slave" means the remote device being polled — in this case, the phone. This follows Modbus terminology (the phone is the Modbus slave/server).

1. Right-click **Modbus_TCP_Master** → **Add Device…**
2. Navigate to: `Fieldbuses → Modbus → Modbus TCP → Modbus TCP Slave`
3. Click **Add Device**. A `Modbus_TCP_Slave` node appears under the master.
4. Double-click **Modbus_TCP_Slave** to open its configuration.
5. In the **General** tab, set:

| Field           | Value                             |
|-----------------|-----------------------------------|
| IP Address      | Phone's IP (e.g. `192.168.1.45`) |
| Port            | `5020`                            |
| Unit Identifier | `1`                               |

---

## Part 6 — Add Communication Channels

Channels define which registers to read or write and how to map them to PLC variables. Each channel corresponds to one Modbus request.

Open **Modbus_TCP_Slave**, go to the **Modbus Slave Channel** tab, and click **Add Channel** for each entry below.

### For MK-EM3P — Energy Monitor

#### Channel 1: Read Measurements (FC04)

| Field             | Value                           |
|-------------------|---------------------------------|
| Name              | `ReadMeasurements`              |
| Access            | Read                            |
| Trigger           | Cyclic                          |
| Cycle time        | `100 ms`                        |
| Function code     | `Read Input Registers (FC04)`   |
| Offset (address)  | `0`                             |
| Length            | `92`                            |
| Variable          | `GVL.emMeasure` *(see Part 7)*  |

#### Channel 2: Read Configuration (FC03)

| Field             | Value                           |
|-------------------|---------------------------------|
| Name              | `ReadConfig`                    |
| Access            | Read                            |
| Trigger           | Cyclic                          |
| Cycle time        | `500 ms`                        |
| Function code     | `Read Holding Registers (FC03)` |
| Offset (address)  | `100`                           |
| Length            | `22`                            |
| Variable          | `GVL.emConfig`                  |

#### Channel 3: Write Configuration (FC16)

| Field             | Value                              |
|-------------------|------------------------------------|
| Name              | `WriteConfig`                      |
| Access            | Write                              |
| Trigger           | Cyclic                             |
| Cycle time        | `500 ms`                           |
| Function code     | `Write Multiple Registers (FC16)`  |
| Offset (address)  | `100`                              |
| Length            | `22`                               |
| Variable          | `GVL.emConfigWrite`                |

---

### For MK-VFD7 — Motor Drive

Use a separate CODESYS project (or replace the slave channels) with these:

#### Channel 1: Read Measurements (FC04)

| Field             | Value                           |
|-------------------|---------------------------------|
| Name              | `ReadVFD`                       |
| Access            | Read                            |
| Trigger           | Cyclic                          |
| Cycle time        | `100 ms`                        |
| Function code     | `Read Input Registers (FC04)`   |
| Offset (address)  | `0`                             |
| Length            | `29`                            |
| Variable          | `GVL.vfdMeasure`                |

#### Channel 2: Read Configuration (FC03)

| Field             | Value                           |
|-------------------|---------------------------------|
| Name              | `ReadVFDConfig`                 |
| Access            | Read                            |
| Trigger           | Cyclic                          |
| Cycle time        | `500 ms`                        |
| Function code     | `Read Holding Registers (FC03)` |
| Offset (address)  | `100`                           |
| Length            | `23`                            |
| Variable          | `GVL.vfdConfig`                 |

#### Channel 3: Write Control Word + Config (FC16)

| Field             | Value                              |
|-------------------|------------------------------------|
| Name              | `WriteVFDConfig`                   |
| Access            | Write                              |
| Trigger           | Cyclic                             |
| Cycle time        | `100 ms`                           |
| Function code     | `Write Multiple Registers (FC16)`  |
| Offset (address)  | `100`                              |
| Length            | `23`                               |
| Variable          | `GVL.vfdConfigWrite`               |

> **Address range note:** The Control Word (address 100) and Frequency Reference (addresses 101–102) are the most important writable registers. This channel covers addresses 100–122. The Fault Reset register (address 127) is outside the simulator's addressable range in the current version and must be triggered from the phone's local panel.

---

## Part 7 — Global Variable List (GVL)

In the project tree, right-click **Application → Add Object → Global Variable List**.
Name it `GVL`. Paste the following declarations:

```iecst
VAR_GLOBAL

    (* ── MK-EM3P: Raw register buffers ─────────────────────────── *)
    emMeasure     : ARRAY[0..91] OF WORD;   (* FC04 read, addr 0–91   *)
    emConfig      : ARRAY[0..21] OF WORD;   (* FC03 read, addr 100–121 *)
    emConfigWrite : ARRAY[0..21] OF WORD;   (* FC16 write, addr 100–121 *)

    (* ── MK-EM3P: Decoded measurement values ────────────────────── *)
    em_VoltL1_N   : REAL;   (* V   — addr 0–1   *)
    em_VoltL2_N   : REAL;   (* V   — addr 2–3   *)
    em_VoltL3_N   : REAL;   (* V   — addr 4–5   *)
    em_VoltL1_L2  : REAL;   (* V   — addr 6–7   *)
    em_CurrL1     : REAL;   (* A   — addr 12–13 *)
    em_CurrL2     : REAL;   (* A   — addr 14–15 *)
    em_CurrL3     : REAL;   (* A   — addr 16–17 *)
    em_PwrTotal   : REAL;   (* kW  — addr 26–27 *)
    em_PF_Total   : REAL;   (* —   — addr 50–51 *)
    em_Frequency  : REAL;   (* Hz  — addr 52–53 *)
    em_AlarmStatus : WORD;  (* bitmask — addr 90 *)
    em_DevStatus   : WORD;  (* bitmask — addr 91 *)

    (* ── MK-VFD7: Raw register buffers ─────────────────────────── *)
    vfdMeasure    : ARRAY[0..28] OF WORD;   (* FC04 read, addr 0–28   *)
    vfdConfig     : ARRAY[0..22] OF WORD;   (* FC03 read, addr 100–122 *)
    vfdConfigWrite: ARRAY[0..22] OF WORD;   (* FC16 write, addr 100–122 *)

    (* ── MK-VFD7: Decoded measurement values ────────────────────── *)
    vfd_OutFreq   : REAL;   (* Hz  — addr 0–1   *)
    vfd_OutVolt   : REAL;   (* V   — addr 2–3   *)
    vfd_OutCurr   : REAL;   (* A   — addr 4–5   *)
    vfd_OutPower  : REAL;   (* kW  — addr 6–7   *)
    vfd_Speed     : REAL;   (* RPM — addr 8–9   *)
    vfd_Torque    : REAL;   (* %   — addr 10–11 *)
    vfd_DCBus     : REAL;   (* V   — addr 12–13 *)
    vfd_TempDrive : REAL;   (* °C  — addr 14–15 *)
    vfd_Status    : WORD;   (* bitmask — addr 26 *)
    vfd_FaultCode : WORD;   (*          addr 27 *)

    (* ── VFD control helpers (written into vfdConfigWrite) ───────── *)
    vfd_CtrlWord  : WORD;   (* maps to vfdConfigWrite[0]  = addr 100 *)
    vfd_FreqRefHz : REAL;   (* maps to vfdConfigWrite[1..2] = addr 101–102 *)

END_VAR
```

---

## Part 8 — FLOAT32 Decode Function

The simulator encodes all REAL values as **IEEE 754 FLOAT32** in **big-endian word order**: the high word (bits 31–16) comes first in the register map, followed by the low word (bits 15–0). On x86 CODESYS Control Win (little-endian), the REAL type stores the low word at the lower address, so the words must be swapped.

### Step 8.1 — Create the Union Type

In the project tree, right-click **Application → Add Object → DUT (Data Unit Type)**. Name it `T_FLOAT_UNION`.

```iecst
TYPE T_FLOAT_UNION :
UNION
    r : REAL;
    w : ARRAY[0..1] OF WORD;  (* w[0] = low word, w[1] = high word *)
END_UNION
END_TYPE
```

### Step 8.2 — Create the Decode Function

Right-click **Application → Add Object → POU → Function**. Name it `WordsToReal`, return type `REAL`.

```iecst
FUNCTION WordsToReal : REAL
VAR_INPUT
    wHigh : WORD;   (* register at address N     — high word *)
    wLow  : WORD;   (* register at address N + 1 — low word  *)
END_VAR
VAR
    u : T_FLOAT_UNION;
END_VAR

u.w[1] := wHigh;
u.w[0] := wLow;
WordsToReal := u.r;
```

### Step 8.3 — Create the Encode Function

Name it `RealToWords`, for writing FLOAT32 back to the device.

```iecst
FUNCTION RealToWords : BOOL
VAR_INPUT
    value   : REAL;
    destArr : REFERENCE TO ARRAY[0..1] OF WORD;
END_VAR
VAR
    u : T_FLOAT_UNION;
END_VAR

u.r        := value;
destArr[0] := u.w[1];   (* high word → first register *)
destArr[1] := u.w[0];   (* low word  → second register *)
RealToWords := TRUE;
```

---

## Part 9 — Main Program (PLC_PRG)

Open **PLC_PRG** (Structured Text). This program runs every PLC cycle.

```iecst
PROGRAM PLC_PRG
VAR
    (* scratch union for FLOAT32 decode *)
    _u : T_FLOAT_UNION;
END_VAR

(* ════════════════════════════════════════════════════════════════
   MK-EM3P — Decode measurement registers
   Each FLOAT32 = 2 consecutive WORDs: [N] = high, [N+1] = low
   Array index = register address (channel starts at address 0)
   ════════════════════════════════════════════════════════════════ *)

GVL.em_VoltL1_N  := WordsToReal(GVL.emMeasure[0],  GVL.emMeasure[1]);
GVL.em_VoltL2_N  := WordsToReal(GVL.emMeasure[2],  GVL.emMeasure[3]);
GVL.em_VoltL3_N  := WordsToReal(GVL.emMeasure[4],  GVL.emMeasure[5]);
GVL.em_VoltL1_L2 := WordsToReal(GVL.emMeasure[6],  GVL.emMeasure[7]);
GVL.em_CurrL1    := WordsToReal(GVL.emMeasure[12], GVL.emMeasure[13]);
GVL.em_CurrL2    := WordsToReal(GVL.emMeasure[14], GVL.emMeasure[15]);
GVL.em_CurrL3    := WordsToReal(GVL.emMeasure[16], GVL.emMeasure[17]);
GVL.em_PwrTotal  := WordsToReal(GVL.emMeasure[26], GVL.emMeasure[27]);
GVL.em_PF_Total  := WordsToReal(GVL.emMeasure[50], GVL.emMeasure[51]);
GVL.em_Frequency := WordsToReal(GVL.emMeasure[52], GVL.emMeasure[53]);
GVL.em_AlarmStatus := GVL.emMeasure[90];
GVL.em_DevStatus   := GVL.emMeasure[91];

(* ════════════════════════════════════════════════════════════════
   MK-VFD7 — Decode measurement registers
   Channel starts at address 0, so array index = register address
   ════════════════════════════════════════════════════════════════ *)

GVL.vfd_OutFreq   := WordsToReal(GVL.vfdMeasure[0],  GVL.vfdMeasure[1]);
GVL.vfd_OutVolt   := WordsToReal(GVL.vfdMeasure[2],  GVL.vfdMeasure[3]);
GVL.vfd_OutCurr   := WordsToReal(GVL.vfdMeasure[4],  GVL.vfdMeasure[5]);
GVL.vfd_OutPower  := WordsToReal(GVL.vfdMeasure[6],  GVL.vfdMeasure[7]);
GVL.vfd_Speed     := WordsToReal(GVL.vfdMeasure[8],  GVL.vfdMeasure[9]);
GVL.vfd_Torque    := WordsToReal(GVL.vfdMeasure[10], GVL.vfdMeasure[11]);
GVL.vfd_DCBus     := WordsToReal(GVL.vfdMeasure[12], GVL.vfdMeasure[13]);
GVL.vfd_TempDrive := WordsToReal(GVL.vfdMeasure[14], GVL.vfdMeasure[15]);
GVL.vfd_Status    := GVL.vfdMeasure[26];
GVL.vfd_FaultCode := GVL.vfdMeasure[27];

(* ════════════════════════════════════════════════════════════════
   MK-VFD7 — Build write buffer from control helpers
   vfdConfigWrite[0]   = addr 100 = Control Word  (UINT16)
   vfdConfigWrite[1..2] = addr 101–102 = Freq Ref (FLOAT32)
   ════════════════════════════════════════════════════════════════ *)

GVL.vfdConfigWrite[0] := GVL.vfd_CtrlWord;
RealToWords(GVL.vfd_FreqRefHz, GVL.vfdConfigWrite[1]);
```

> **Array index vs register address:** When a channel starts at address N, `array[0]` maps to register address N, `array[1]` to N+1, and so on. The emMeasure channel starts at address 0, so `emMeasure[k]` = register k. The vfdConfig channel starts at address 100, so `vfdConfig[0]` = register 100, `vfdConfig[1]` = register 101, etc.

---

## Part 10 — Build and Deploy

1. **Build:** Go to **Build → Build** (F11). Fix any errors shown in the message pane.
2. **Login:** Go to **Online → Login** (Ctrl+L). If prompted to download, click **Yes**.
3. **Start:** Go to **Debug → Start** (F5). The PLC program begins executing.

---

## Part 11 — Online Monitoring

With the PLC running, you can watch live values in the IDE.

### Watch Window

1. Go to **Debug → Add Watch** (or right-click a variable → Add to Watch).
2. Add these variables:

```
GVL.em_VoltL1_N
GVL.em_VoltL2_N
GVL.em_VoltL3_N
GVL.em_PwrTotal
GVL.em_Frequency
GVL.em_PF_Total
GVL.em_AlarmStatus
```

Values should update every 100 ms and fluctuate — the simulation engine applies realistic noise.

### Monitoring VFD

Add to watch:
```
GVL.vfd_OutFreq
GVL.vfd_Speed
GVL.vfd_OutCurr
GVL.vfd_Status
GVL.vfd_FaultCode
GVL.vfd_CtrlWord
GVL.vfd_FreqRefHz
```

---

## Part 12 — Writing Values (Online Force / Write)

### Exercise: Change CT Primary Ratio (MK-EM3P)

The CT Primary ratio is a UINT16 at config register address 100, mapped to `emConfigWrite[0]`.

1. In the Watch window, right-click `GVL.emConfigWrite[0]` → **Force Value**.
2. Enter `200` → **OK**.
3. Wait one polling cycle (500 ms). Read back `GVL.emConfig[0]` — it should return `200`.

### Exercise: Write Over-Voltage Threshold (MK-EM3P, FLOAT32)

The Over-Voltage Threshold (FLOAT32) is at addresses 107–108. In the write array (which starts at address 100), this maps to indices 7 and 8.

```iecst
(* Add this to PLC_PRG to set the threshold to 260.0 V *)
RealToWords(260.0, GVL.emConfigWrite[7]);
```

After this runs for one cycle, the simulator picks up the new threshold.

### Exercise: Start the VFD Motor (MK-VFD7)

> **Make sure the phone is in REMOTE mode** before writing the Control Word.

In the Watch window:

1. Force `GVL.vfd_FreqRefHz` = `45.0` — this writes the frequency reference.
2. Force `GVL.vfd_CtrlWord` = `1` — bit 0 = RUN.

Watch `GVL.vfd_OutFreq` and `GVL.vfd_Speed` ramp up to reference over the configured acceleration time.

**VFD Control Word values:**

| Value | Bits set       | Action               |
|-------|----------------|----------------------|
| `0`   | none           | Stop                 |
| `1`   | bit 0 (RUN)    | Run forward          |
| `3`   | bits 0+1       | Run reverse          |
| `5`   | bits 0+2       | Jog forward          |
| `16`  | bit 4 (E-STOP) | Emergency stop       |

### Exercise: Change Acceleration Time (MK-VFD7, FLOAT32)

Acceleration Time is at register 103–104. In vfdConfigWrite (starts at 100), this is indices 3 and 4.

```iecst
(* Set acceleration time to 5.0 seconds *)
RealToWords(5.0, GVL.vfdConfigWrite[3]);
```

Start the drive and observe the frequency ramp is faster.

---

## Part 13 — Variable Mapping Reference

### MK-EM3P: emMeasure array index → register address

Since the channel starts at address 0, `emMeasure[N]` = register N.

| emMeasure index | Register | Parameter         | Decode        |
|-----------------|----------|-------------------|---------------|
| [0–1]           | 0–1      | Voltage L1-N      | FLOAT32       |
| [2–3]           | 2–3      | Voltage L2-N      | FLOAT32       |
| [4–5]           | 4–5      | Voltage L3-N      | FLOAT32       |
| [6–7]           | 6–7      | Voltage L1-L2     | FLOAT32       |
| [12–13]         | 12–13    | Current L1        | FLOAT32       |
| [14–15]         | 14–15    | Current L2        | FLOAT32       |
| [16–17]         | 16–17    | Current L3        | FLOAT32       |
| [26–27]         | 26–27    | Active Power Total| FLOAT32       |
| [44–45]         | 44–45    | Power Factor L1   | FLOAT32       |
| [50–51]         | 50–51    | Power Factor Total| FLOAT32       |
| [52–53]         | 52–53    | Frequency         | FLOAT32       |
| [54–55]         | 54–55    | Active Energy     | UINT32        |
| [88–89]         | 88–89    | Run Hours         | UINT32        |
| [90]            | 90       | Alarm Status      | UINT16 bitmask|
| [91]            | 91       | Device Status     | UINT16 bitmask|

### MK-EM3P: emConfigWrite index → register address

Channel starts at address 100, so `emConfigWrite[N]` = register (100 + N).

| emConfigWrite index | Register | Parameter               | Type    |
|---------------------|----------|-------------------------|---------|
| [0]                 | 100      | CT Primary              | UINT16  |
| [1]                 | 101      | CT Secondary            | UINT16  |
| [2]                 | 102      | VT Primary              | UINT16  |
| [7–8]               | 107–108  | Over-Voltage Threshold  | FLOAT32 |
| [9–10]              | 109–110  | Under-Voltage Threshold | FLOAT32 |
| [11–12]             | 111–112  | Over-Current Threshold  | FLOAT32 |
| [17]                | 117      | Alarm Enable Mask       | UINT16  |

### MK-VFD7: vfdMeasure array index → register address

Channel starts at address 0, so `vfdMeasure[N]` = register N.

| vfdMeasure index | Register | Parameter        | Type    |
|------------------|----------|------------------|---------|
| [0–1]            | 0–1      | Output Frequency | FLOAT32 |
| [2–3]            | 2–3      | Output Voltage   | FLOAT32 |
| [4–5]            | 4–5      | Output Current   | FLOAT32 |
| [6–7]            | 6–7      | Output Power     | FLOAT32 |
| [8–9]            | 8–9      | Motor Speed      | FLOAT32 |
| [10–11]          | 10–11    | Motor Torque     | FLOAT32 |
| [12–13]          | 12–13    | DC Bus Voltage   | FLOAT32 |
| [14–15]          | 14–15    | Drive Temperature| FLOAT32 |
| [26]             | 26       | Drive Status     | UINT16  |
| [27]             | 27       | Fault Code       | UINT16  |
| [28]             | 28       | Warning Code     | UINT16  |

### MK-VFD7: vfdConfigWrite index → register address

Channel starts at address 100, so `vfdConfigWrite[N]` = register (100 + N).

| vfdConfigWrite index | Register  | Parameter           | Type    |
|----------------------|-----------|---------------------|---------|
| [0]                  | 100       | Control Word        | UINT16  |
| [1–2]                | 101–102   | Frequency Reference | FLOAT32 |
| [3–4]                | 103–104   | Acceleration Time   | FLOAT32 |
| [5–6]                | 105–106   | Deceleration Time   | FLOAT32 |
| [7–8]                | 107–108   | Max Frequency       | FLOAT32 |
| [9–10]               | 109–110   | Min Frequency       | FLOAT32 |
| [11]                 | 111       | Motor Rated Voltage | UINT16  |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Variables show `0` and don't update | SoftPLC not connected to phone | Check IP in slave config; verify phone server is running |
| `Online → Login` fails | CODESYS Control Win not running | Check system tray; start the service |
| Build error on `WordsToReal` | Function or type not found | Verify DUT and Function were added under the same Application node |
| Drive does not respond to CtrlWord | Phone is in LOCAL mode | Switch the phone toggle to REMOTE |
| Values all stuck at default | Phone screen turned off | Wake phone; prevent display timeout |
| Error exception on channel | Register address out of range | Ensure channel length + start address ≤ 123 |
| `em_VoltL1_N` reads garbage | Word order inverted | Confirm you used `WordsToReal(highWord, lowWord)` — high word is at the lower address |

---

## Appendix — FLOAT32 Decode: How It Works

The simulator uses **big-endian word order** (also called ABCD byte order):

```
Register N   (address 0):  0x4360  ← bits 31–16 of the IEEE 754 value
Register N+1 (address 1):  0x0000  ← bits 15–0 of the IEEE 754 value

Combined: 0x43600000 = 224.0 V
```

CODESYS Control Win runs on x86 (**little-endian**). The `REAL` type stores the least significant word at the lower memory address. The UNION maps `w[0]` to the low word and `w[1]` to the high word. Therefore:

```iecst
u.w[1] := wHigh;   (* bits 31–16 from register N   → high memory word *)
u.w[0] := wLow;    (* bits 15–0  from register N+1 → low memory word  *)
WordsToReal := u.r;
```

Swapping high and low is the essential step — without it, all decoded values will be wrong.
