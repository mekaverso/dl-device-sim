<p align="center">
  <img src="brand/Marca-Completa-Mekatronik-Colorido-cropped.png" alt="Mekatronik - Advanced Engineering" width="400">
</p>

<h1 align="center">ModbusDeviceSIM</h1>

<p align="center">
  <strong>Virtual Modbus Device Simulator</strong><br>
  Simulate industrial Modbus devices over Serial (RTU) and Ethernet (TCP)
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/modbus-RTU%20%7C%20TCP-green" alt="Modbus RTU | TCP">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Raspberry%20Pi-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-proprietary-red" alt="License">
</p>

---

## What is ModbusDeviceSIM?

ModbusDeviceSIM is a software-based simulator that emulates real industrial Modbus devices. It allows engineers, integrators, and developers to test SCADA systems, PLCs, Modbus masters, and custom applications **without needing physical hardware**.

The simulator creates virtual devices that respond to Modbus queries exactly like their real counterparts — with realistic register maps, proper data types, and dynamically fluctuating values that mimic real sensor behavior.

## Why?

Setting up a physical test bench with energy meters, flow sensors, and other industrial devices is expensive, slow, and often impractical during early development. ModbusDeviceSIM solves this by providing:

- **Instant device availability** — spin up virtual Modbus devices in seconds
- **Realistic simulation** — values drift, fluctuate, and correlate like real sensors
- **Dual transport** — test both serial (RTU) and Ethernet (TCP) from the same device model
- **Reproducible scenarios** — configure specific operating conditions for consistent testing
- **Cross-platform** — develop on Windows, deploy on Linux or Raspberry Pi

## Simulated Devices

### Energy Monitor

A 3-phase energy monitoring device inspired by industry-standard meters (Schneider PM5xxx, Carlo Gavazzi EM series). Provides:

| Register Group | Parameters |
|---|---|
| **Voltage** | L1, L2, L3 phase-to-neutral; L1-L2, L2-L3, L3-L1 phase-to-phase |
| **Current** | L1, L2, L3 per-phase; Neutral |
| **Active Power** | Per-phase (L1, L2, L3) and Total |
| **Reactive Power** | Per-phase (L1, L2, L3) and Total |
| **Apparent Power** | Per-phase (L1, L2, L3) and Total |
| **Power Factor** | Per-phase (L1, L2, L3) and Total |
| **Frequency** | System frequency (Hz) |
| **Energy** | Active (kWh), Reactive (kVArh) — cumulative accumulators |

> Additional device profiles (flow meters, temperature transmitters, motor drives, etc.) can be added following the same device model architecture.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   ModbusDeviceSIM                    │
│                                                     │
│  ┌─────────────┐   ┌─────────────────────────────┐  │
│  │   Device     │   │     Transport Layer          │  │
│  │   Models     │   │                             │  │
│  │             │   │  ┌─────────┐  ┌──────────┐  │  │
│  │  ┌────────┐ │   │  │ Modbus  │  │ Modbus   │  │  │
│  │  │ Energy │ │──▶│  │  RTU    │  │  TCP     │  │  │
│  │  │Monitor │ │   │  │ Server  │  │ Server   │  │  │
│  │  └────────┘ │   │  └────┬────┘  └────┬─────┘  │  │
│  │  ┌────────┐ │   │       │            │         │  │
│  │  │ Future │ │   └───────┼────────────┼─────────┘  │
│  │  │Devices │ │           │            │            │
│  │  └────────┘ │     ┌─────▼─────┐  ┌───▼────────┐  │
│  └─────────────┘     │  Serial   │  │  TCP Socket │  │
│                      │  Port     │  │  (port 502) │  │
│  ┌─────────────┐     │(com0com) │  └────────────┘  │
│  │  Simulation │     └───────────┘                   │
│  │  Engine     │                                     │
│  │  (value     │         ▲               ▲           │
│  │ fluctuation)│         │               │           │
│  └─────────────┘         │               │           │
└──────────────────────────┼───────────────┼───────────┘
                           │               │
                    ┌──────▼──┐     ┌──────▼──────┐
                    │ Modbus  │     │   Modbus    │
                    │ Master  │     │   Master    │
                    │ (Serial)│     │ (Ethernet)  │
                    └─────────┘     └─────────────┘
```

### Component Breakdown

**Device Models** define *what* is being simulated:
- Register map (addresses, data types, read/write permissions)
- Parameter metadata (name, unit, scaling, valid range)
- Relationships between parameters (e.g., power = voltage × current × power factor)

**Simulation Engine** makes values *behave realistically*:
- Base values with configurable noise and drift
- Correlated parameters (if voltage rises, current adjusts accordingly)
- Cumulative accumulators (energy counters that increment over time)
- Configurable operating scenarios (nominal load, overload, power outage, etc.)

**Transport Layer** handles *how* data is communicated:
- Modbus RTU Server — binds to a serial port, responds to RTU frames with CRC-16
- Modbus TCP Server — listens on a TCP socket, responds to MBAP-framed requests
- Both transports can run simultaneously from the same device model instance

### Register Encoding

All floating-point values are stored as **IEEE 754 32-bit floats** across two consecutive 16-bit Modbus registers in **big-endian word order** (high word first). This matches the most common convention in industrial devices.

| Data Type | Registers Used | Byte Order |
|---|---|---|
| INT16 | 1 register | Big-endian |
| UINT16 | 1 register | Big-endian |
| FLOAT32 | 2 registers | Big-endian (AB CD) |
| INT32 | 2 registers | Big-endian (AB CD) |
| UINT32 | 2 registers | Big-endian (AB CD) |

Register addresses use **0-based indexing** internally. Documentation and configuration files reference 1-based Modbus convention (as shown in device datasheets).

## Technology

| Component | Technology | Purpose |
|---|---|---|
| Runtime | Python 3.10+ | Cross-platform execution |
| Modbus Stack | `pymodbus` | Modbus RTU/TCP slave implementation |
| Serial I/O | `pyserial` | COM port communication |
| Virtual Serial | com0com (Windows) | Creates virtual COM port pairs |
| Packaging | PyInstaller | Standalone .exe distribution |
| Testing | pytest | Unit and integration tests |

### Virtual Serial Port Setup (com0com)

On Windows, [com0com](https://com0com.sourceforge.net/) creates virtual COM port pairs. When a pair is created (e.g., COM10 ↔ COM11):

```
┌──────────────┐     com0com pair     ┌──────────────┐
│ ModbusDevice │◄────────────────────►│ Modbus Master│
│ SIM (COM10)  │   virtual null-modem │  (COM11)     │
└──────────────┘                      └──────────────┘
```

- The simulator opens one end of the pair (COM10)
- The Modbus master application connects to the other end (COM11)
- Data flows through the virtual null-modem cable transparently

On **Linux**, the same effect is achieved with `socat` creating virtual PTY pairs, or by using a real serial port (e.g., `/dev/ttyUSB0` with an RS-485 adapter).

On **Raspberry Pi**, the hardware UART (`/dev/ttyAMA0`) can be used directly with an RS-485 transceiver, making the Pi behave as a physical Modbus RTU device on a real serial bus.

## Supported Modbus Functions

| Function Code | Name | Supported |
|---|---|---|
| 0x01 | Read Coils | Yes |
| 0x02 | Read Discrete Inputs | Yes |
| 0x03 | Read Holding Registers | Yes |
| 0x04 | Read Input Registers | Yes |
| 0x05 | Write Single Coil | Yes |
| 0x06 | Write Single Register | Yes |
| 0x0F | Write Multiple Coils | Yes |
| 0x10 | Write Multiple Registers | Yes |

## Getting Started

### Prerequisites

- Python 3.10 or higher
- com0com installed (Windows, for RTU simulation)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ModbusDeviceSIM

# Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Simulator

```bash
# Run with default configuration
python -m modbusdevicesim

# Run with a specific config file
python -m modbusdevicesim --config config/energy_monitor.yaml
```

### Packaging as Standalone Executable

```bash
pyinstaller --onefile modbusdevicesim/__main__.py -n ModbusDeviceSIM
```

The resulting `ModbusDeviceSIM.exe` can be distributed and run without a Python installation.

## Project Structure

```
ModbusDeviceSIM/
├── modbusdevicesim/          # Main package
│   ├── __main__.py           # CLI entry point
│   ├── devices/              # Device model definitions
│   │   └── energy_monitor.py # Energy monitor register map and simulation
│   ├── transport/            # Modbus transport servers
│   │   ├── rtu_server.py     # Modbus RTU (serial) server
│   │   └── tcp_server.py     # Modbus TCP (Ethernet) server
│   └── simulation/           # Value simulation engine
│       └── engine.py         # Realistic value fluctuation logic
├── config/                   # Device configuration files
├── tests/                    # Test suite
├── brand/                    # Mekatronik brand assets
├── requirements.txt
├── CLAUDE.md
└── README.md
```

## License

Proprietary — Mekatronik Advanced Engineering. All rights reserved.
