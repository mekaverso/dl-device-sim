"""CLI entry point for ModbusDeviceSIM.

Usage:
    python -m modbusdevicesim [options]

Examples:
    # TCP only (default, port 502)
    python -m modbusdevicesim

    # TCP on custom port
    python -m modbusdevicesim --tcp-port 5020

    # RTU only on COM10
    python -m modbusdevicesim --rtu-port COM10 --no-tcp

    # Both RTU and TCP
    python -m modbusdevicesim --rtu-port COM10 --tcp-port 502

    # Custom slave ID and faster energy accumulation
    python -m modbusdevicesim --slave-id 5 --energy-speed 100

    # Launch the graphical interface
    python -m modbusdevicesim --gui
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from modbusdevicesim.app import ModbusDeviceApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="modbusdevicesim",
        description="Mekatronik ModbusDeviceSIM — Virtual Modbus Device Simulator",
    )

    parser.add_argument(
        "--gui", action="store_true",
        help="Launch the device simulator GUI",
    )
    parser.add_argument(
        "--master", action="store_true",
        help="Launch the Modbus master/client test tool",
    )
    parser.add_argument(
        "--slave-id", type=int, default=1,
        help="Modbus slave ID (default: 1)",
    )

    # RTU options
    rtu = parser.add_argument_group("Modbus RTU (Serial)")
    rtu.add_argument(
        "--rtu-port", type=str, default=None,
        help="Serial port for RTU (e.g., COM10, /dev/ttyUSB0). Disabled if not set.",
    )
    rtu.add_argument(
        "--rtu-baudrate", type=int, default=9600,
        help="Baud rate (default: 9600)",
    )

    # TCP options
    tcp = parser.add_argument_group("Modbus TCP (Ethernet)")
    tcp.add_argument(
        "--tcp-host", type=str, default="0.0.0.0",
        help="TCP bind address (default: 0.0.0.0)",
    )
    tcp.add_argument(
        "--tcp-port", type=int, default=502,
        help="TCP port (default: 502)",
    )
    tcp.add_argument(
        "--no-tcp", action="store_true",
        help="Disable TCP transport",
    )

    # Simulation options
    sim = parser.add_argument_group("Simulation")
    sim.add_argument(
        "--update-interval", type=float, default=1.0,
        help="Simulation update interval in seconds (default: 1.0)",
    )
    sim.add_argument(
        "--energy-speed", type=float, default=1.0,
        help="Energy accumulation speed multiplier (default: 1.0, use 100 for fast demo)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Launch GUI mode
    if args.gui:
        from modbusdevicesim.gui import main as gui_main
        gui_main()
        return

    # Launch Master/Client tool
    if args.master:
        from modbusdevicesim.master import main as master_main
        master_main()
        return

    tcp_port = None if args.no_tcp else args.tcp_port

    if not args.rtu_port and not tcp_port:
        print("Error: No transport enabled. Use --rtu-port and/or --tcp-port.")
        sys.exit(1)

    app = ModbusDeviceApp(
        slave_id=args.slave_id,
        rtu_port=args.rtu_port,
        rtu_baudrate=args.rtu_baudrate,
        tcp_host=args.tcp_host,
        tcp_port=tcp_port,
        update_interval=args.update_interval,
        energy_time_factor=args.energy_speed,
    )

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
