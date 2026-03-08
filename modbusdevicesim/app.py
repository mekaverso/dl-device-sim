"""Main application orchestrator — ties device, simulation, and transport together."""

from __future__ import annotations

import asyncio
import signal
import sys

from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from modbusdevicesim.brand import (
    console, print_banner, print_device_info, print_transport_status,
    PRIMARY_BLUE, GRAY,
)
from modbusdevicesim.devices.energy_monitor import EnergyMonitor
from modbusdevicesim.simulation.engine import SimulationEngine, SimulationConfig
from modbusdevicesim.transport.rtu_server import RTUServer
from modbusdevicesim.transport.tcp_server import TCPServer


class ModbusDeviceApp:
    """Main application that runs the Modbus device simulator."""

    def __init__(
        self,
        slave_id: int = 1,
        rtu_port: str | None = None,
        rtu_baudrate: int = 9600,
        tcp_host: str = "0.0.0.0",
        tcp_port: int | None = 502,
        update_interval: float = 1.0,
        energy_time_factor: float = 1.0,
    ):
        self.device = EnergyMonitor(slave_id=slave_id)
        self.sim_config = SimulationConfig(
            update_interval=update_interval,
            energy_time_factor=energy_time_factor,
        )
        self.engine = SimulationEngine(self.device, self.sim_config)
        self.rtu_port = rtu_port
        self.rtu_baudrate = rtu_baudrate
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.rtu_server: RTUServer | None = None
        self.tcp_server: TCPServer | None = None
        self._running = False

    def _build_live_table(self) -> Table:
        """Build the register values table for live display."""
        table = Table(
            border_style="blue",
            header_style="bold bright_blue",
            show_lines=False,
            padding=(0, 1),
            expand=True,
        )
        table.add_column("Addr", style="dim", justify="right", width=5)
        table.add_column("Parameter", style="bold white", width=24)
        table.add_column("Value", style="bold bright_white", justify="right", width=12)
        table.add_column("Unit", style="dim", width=6)
        table.add_column("", width=2)  # spacer
        table.add_column("Addr", style="dim", justify="right", width=5)
        table.add_column("Parameter", style="bold white", width=24)
        table.add_column("Value", style="bold bright_white", justify="right", width=12)
        table.add_column("Unit", style="dim", width=6)

        regs = self.device.get_register_info()
        half = (len(regs) + 1) // 2

        for i in range(half):
            left = regs[i]
            right = regs[i + half] if (i + half) < len(regs) else None

            left_val = f"{left['value']:.2f}" if isinstance(left['value'], float) else str(int(left['value']))
            row = [
                str(left['address']),
                left['name'],
                left_val,
                left.get('unit', ''),
                "│",
            ]

            if right:
                right_val = f"{right['value']:.2f}" if isinstance(right['value'], float) else str(int(right['value']))
                row += [
                    str(right['address']),
                    right['name'],
                    right_val,
                    right.get('unit', ''),
                ]
            else:
                row += ["", "", "", ""]

            table.add_row(*row)

        return table

    def _build_display(self) -> Panel:
        """Build the full branded display panel."""
        table = self._build_live_table()

        # Transport status line
        parts = []
        if self.rtu_port:
            parts.append(f"[bold #EF8E5E]RTU[/bold #EF8E5E] {self.rtu_port} ({self.rtu_baudrate})")
        if self.tcp_port:
            parts.append(f"[bold #D8E16D]TCP[/bold #D8E16D] {self.tcp_host}:{self.tcp_port}")
        transport_line = "  │  ".join(parts) if parts else "[dim]No transport configured[/dim]"

        header = (
            f"[bold bright_blue]{self.device.name}[/bold bright_blue]  "
            f"[dim]Slave ID {self.device.slave_id}[/dim]  │  "
            f"{transport_line}  │  "
            f"[bold #D8E16D]● RUNNING[/bold #D8E16D]"
        )

        return Panel(
            table,
            title=f"[bold bright_blue]MEKATRONIK[/bold bright_blue] [dim]ModbusDeviceSIM[/dim]",
            subtitle="[dim]Press Ctrl+C to stop[/dim]",
            border_style="blue",
            padding=(0, 1),
            subtitle_align="center",
            title_align="center",
        )

    async def run(self):
        """Start the application — servers + simulation loop + live display."""
        print_banner()
        print_device_info(self.device.name, self.device.slave_id, self.device.description)

        # Create shared slave context
        slave_context = self.device.create_slave_context()

        # Start transport servers as background tasks
        server_tasks = []

        if self.rtu_port:
            self.rtu_server = RTUServer(
                context=slave_context,
                slave_id=self.device.slave_id,
                port=self.rtu_port,
                baudrate=self.rtu_baudrate,
            )
            server_tasks.append(asyncio.create_task(self.rtu_server.start()))

        if self.tcp_port:
            self.tcp_server = TCPServer(
                context=slave_context,
                slave_id=self.device.slave_id,
                host=self.tcp_host,
                port=self.tcp_port,
            )
            server_tasks.append(asyncio.create_task(self.tcp_server.start()))

        print_transport_status(self.rtu_port, self.tcp_port, self.tcp_host)
        console.print()

        # Wait briefly for servers to initialize
        if server_tasks:
            await asyncio.sleep(0.5)

        # Run simulation + live display
        self._running = True
        console.print("[brand.dim]Starting simulation...[/brand.dim]\n")

        try:
            with Live(self._build_display(), console=console, refresh_per_second=2, transient=False) as live:
                while self._running:
                    self.engine.read_config_from_context(slave_context)
                    self.engine.update()
                    self.device.update_slave_context(slave_context)
                    live.update(self._build_display())
                    await asyncio.sleep(self.sim_config.update_interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            console.print("\n[brand.dim]Shutting down...[/brand.dim]")
            self._running = False
            if self.rtu_server:
                try:
                    await self.rtu_server.stop()
                except Exception:
                    pass
            if self.tcp_server:
                try:
                    await self.tcp_server.stop()
                except Exception:
                    pass
            console.print("[brand]Mekatronik ModbusDeviceSIM stopped.[/brand]")
