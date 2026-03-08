"""Mekatronik brand identity — colors, logo, and rich console styling."""

import sys
import os

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.system("")  # Enable VT100 escape sequences on Windows 10+
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

# ── Mekatronik Brand Colors ──────────────────────────────────────────
PRIMARY_BLUE = "#0066FF"
DARK_TEAL = "#0A3D5C"
GRAY = "#888888"
BLACK = "#000000"
WHITE = "#FFFFFF"

# Accent palette
RED = "#DB311B"
LIME = "#D8E16D"
LAVENDER = "#C1BAFD"
GOLD = "#EFCB1D"
PEACH = "#EF8E5E"

# ── Rich Theme ───────────────────────────────────────────────────────
MEKATRONIK_THEME = Theme({
    "brand": f"bold {PRIMARY_BLUE}",
    "brand.dim": GRAY,
    "brand.accent": GOLD,
    "brand.success": LIME,
    "brand.error": RED,
    "brand.warn": PEACH,
    "info": f"{PRIMARY_BLUE}",
    "info.label": f"bold {WHITE}",
    "device": f"bold {LAVENDER}",
    "register": GRAY,
    "value": f"bold {WHITE}",
    "unit": "dim",
    "transport.rtu": f"bold {PEACH}",
    "transport.tcp": f"bold {LIME}",
    "status.running": f"bold {LIME}",
    "status.stopped": f"bold {RED}",
})

console = Console(theme=MEKATRONIK_THEME)

# ── ASCII Logo ───────────────────────────────────────────────────────
LOGO = r"""
 ┏┓┏┓  ┏┓┏┓ ┏┓ ┏┓┏━┓┏━┓┏━┓┏┓ ┏┓┏┓┏┓┏┓ ┏┓
 ┃┗┛┃  ┃┗┛┃ ┃┗┓┃┃┃ ┃┃ ┃┃ ┃┃┗┓┃┃┃┃┃┗┛┃ ┃┃
 ┃┏┓┃┏━┃┏┓┃ ┃┏┛┃┃┃ ┃┃ ┃┃ ┃┃┏┛┃┃┃┃┃┏┓┃ ┃┃
 ┗┛┗┛┗━┗┛┗┛ ┗┛ ┗┛┗━┛┗━┛┗━┛┗┛ ┗┛┗┛┗┛┗┛ ┗┛
"""

LOGO_SIMPLE = """
  ╔╦╗╔═╗╦╔═╔═╗╔╦╗╦═╗╔═╗╔╗╔╦╦╔═
  ║║║║╣ ╠╩╗╠═╣ ║ ╠╦╝║ ║║║║║╠╩╗
  ╩ ╩╚═╝╩ ╩╩ ╩ ╩ ╩╚═╚═╝╝╚╝╩╩ ╩
"""

TAGLINE = "ADVANCED ENGINEERING"


def print_banner():
    """Print the branded application banner."""
    logo_text = Text(LOGO_SIMPLE, style="brand")
    tagline = Text(f"  {TAGLINE}\n", style="brand.dim")

    console.print()
    console.print(logo_text, end="")
    console.print(tagline)
    console.print(
        Panel(
            "[brand]ModbusDeviceSIM[/brand] [brand.dim]v0.1.0[/brand.dim]\n"
            "[brand.dim]Virtual Modbus Device Simulator[/brand.dim]",
            border_style="blue",
            padding=(0, 2),
        )
    )
    console.print()


def print_device_info(device_name: str, slave_id: int, description: str):
    """Print device information panel."""
    console.print(
        Panel(
            f"[device]{device_name}[/device]\n"
            f"[brand.dim]{description}[/brand.dim]\n"
            f"[info.label]Slave ID:[/info.label] [value]{slave_id}[/value]",
            title="[brand]Device[/brand]",
            border_style="blue",
            padding=(0, 2),
        )
    )


def print_transport_status(rtu_port: str | None, tcp_port: int | None, tcp_host: str = "0.0.0.0"):
    """Print transport status panel."""
    lines = []
    if rtu_port:
        lines.append(f"[transport.rtu]RTU[/transport.rtu]  Serial port [value]{rtu_port}[/value]  [status.running]● LISTENING[/status.running]")
    else:
        lines.append(f"[transport.rtu]RTU[/transport.rtu]  [status.stopped]● DISABLED[/status.stopped]")

    if tcp_port:
        lines.append(f"[transport.tcp]TCP[/transport.tcp]  {tcp_host}:[value]{tcp_port}[/value]  [status.running]● LISTENING[/status.running]")
    else:
        lines.append(f"[transport.tcp]TCP[/transport.tcp]  [status.stopped]● DISABLED[/status.stopped]")

    console.print(
        Panel(
            "\n".join(lines),
            title="[brand]Transport[/brand]",
            border_style="blue",
            padding=(0, 2),
        )
    )


def print_register_table(registers: list[dict]):
    """Print a formatted table of register values."""
    table = Table(
        title="[brand]Register Values[/brand]",
        border_style="blue",
        header_style="brand",
        show_lines=False,
        padding=(0, 1),
    )
    table.add_column("Address", style="register", justify="right", width=8)
    table.add_column("Parameter", style="info.label", width=28)
    table.add_column("Value", style="value", justify="right", width=12)
    table.add_column("Unit", style="unit", width=8)

    for reg in registers:
        table.add_row(
            str(reg["address"]),
            reg["name"],
            f"{reg['value']:.2f}" if isinstance(reg["value"], float) else str(reg["value"]),
            reg.get("unit", ""),
        )

    console.print(table)
