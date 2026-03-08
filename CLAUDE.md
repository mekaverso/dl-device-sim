# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ModbusDeviceSIM** is a Modbus device simulator by **Mekatronik — Advanced Engineering**, designed as an educational tool for students learning industrial protocols. It simulates a 3-phase energy monitor (MK-EM3P) that communicates via Modbus RTU (serial) and Modbus TCP (Ethernet).

Two implementations exist:
1. **Python desktop app** — full-featured with GUI (CustomTkinter), simulation engine, and Modbus server
2. **Android app** — native Kotlin/Jetpack Compose device simulator running a Modbus TCP server on mobile

## Tech Stack

### Python (Desktop)
- **Language:** Python 3.10+
- **Modbus:** `pymodbus` 3.12+ — async slave/server for RTU and TCP
- **GUI:** `customtkinter` — branded dark theme with tabbed interface
- **Serial:** `pyserial` — COM port communication
- **Virtual Serial (Windows):** com0com driver creates virtual COM port pairs

### Android
- **Language:** Kotlin, min SDK 26, target SDK 35
- **UI:** Jetpack Compose + Material 3
- **Architecture:** MVVM (AndroidViewModel + StateFlow)
- **Modbus:** Custom raw-socket Modbus TCP server (no external library)
- **Source:** `android-simulator/` directory (package: `com.mekatronik.modbussim`)

## Architecture

### Python Simulator
The simulator exposes **virtual Modbus slave devices** with realistic register maps. Each device type defines its register layout, data types, and value simulation logic.

**Key modules:**
- `devices/energy_monitor.py` — register map (47 measurement + 17 config registers)
- `devices/base.py` — DeviceModel base class, IEEE 754 encode/decode
- `simulation/engine.py` — layered sine-wave noise for realistic value fluctuation
- `gui.py` — tabbed GUI: Register View + Device Panel (LCD with 13 pages)
- `master.py` — standalone Modbus master/client for testing
- `app.py` — async orchestration (Modbus servers + simulation loop)

**Transport layer:** Simultaneous Modbus RTU (serial) + Modbus TCP (port 502).

### Android Simulator
Mirrors the Python simulator as a mobile app:
- `modbus/ModbusTcpServer.kt` — Modbus TCP server accepting FC03/04/06/16
- `modbus/RegisterMap.kt` — register definitions matching Python (ALL_REGISTERS)
- `simulation/SimulationEngine.kt` — port of Python engine (smooth noise, correlated values)
- `SimulatorViewModel.kt` — MVVM state management + LCD page definitions
- `MainActivity.kt` — Compose UI (server controls, LCD panel, register list)

### Register Map (MK-EM3P)
- **Measurement registers** (0–91, read-only): Voltage, Current, Power (active/reactive/apparent), PF, Frequency, Energy, THD, Demand, Averages, Unbalance, Run Hours, Alarm/Status
- **Configuration registers** (100–122, read/write): CT/VT ratios, thresholds, alarm mask, reset commands
- Non-contiguous blocks require two-block reads in master (0–91 then 100–122)
- IEEE 754 FLOAT32 in big-endian word order across 2 registers
- Alarm system: bitmask enable/status with 8 alarm types, RESET_MAGIC = 0x1234

## Brand

Company: **Mekatronik — Advanced Engineering**
- Brand assets in `brand/`
- Primary color: Blue (`#0070F0` approx)
- Accent palette: `#db311b`, `#d8e16d`, `#c1bafd`, `#efcb1d`, `#ef8e5e`
- Background variants: Blue, dark teal, gray, black — all use white logo
- Short form: **meka**

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the simulator (GUI + Modbus servers)
python -m modbusdevicesim

# Run the standalone master/client for testing
python -m modbusdevicesim.master

# Run tests
pytest

# Run a single test
pytest tests/test_energy_monitor.py -v

# Package as .exe (Windows)
pyinstaller --onefile modbusdevicesim/__main__.py -n ModbusDeviceSIM
```

### Android
Open `android-simulator/` in Android Studio. Build with Gradle (AGP 8.7.3, Kotlin 2.1.0).

## Key Conventions

- Device register maps should mirror real-world industrial devices (e.g., Schneider PM5xxx, Carlo Gavazzi EM series for energy monitors)
- Register addresses use 0-based indexing internally; documentation references 1-based Modbus convention
- All floating-point values stored as IEEE 754 in two consecutive 16-bit registers (big-endian word order)
- Device profiles are defined declaratively (register address, data type, unit, simulation range)
- Writable config registers are only written to HR (FC03), not IR (FC04), so master-written values persist
- Simulation engine reads config back from Modbus context each tick (bidirectional config flow)
- Android app is a **device simulator** (Modbus TCP server), NOT an HMI client
