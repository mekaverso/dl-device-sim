"""Mekatronik Modbus Master/Client — Test tool for ModbusDeviceSIM.

Connects to Modbus devices over RTU (serial) or TCP (Ethernet),
reads/writes registers, and displays live-polled values.
"""

from __future__ import annotations

import asyncio
import struct
import threading
import time
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
from PIL import Image

from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient

# ── Mekatronik Brand Colors ──────────────────────────────────────────
BG_DARK = "#0A1628"
BG_PANEL = "#0F2035"
BG_CARD = "#162A45"
BG_INPUT = "#1A3250"
BRAND_BLUE = "#0066FF"
BRAND_BLUE_HOVER = "#0052CC"
BRAND_BLUE_LIGHT = "#3D8BFF"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8899AA"
TEXT_DIM = "#556677"
ACCENT_GREEN = "#4ADE80"
ACCENT_RED = "#EF4444"
ACCENT_PEACH = "#EF8E5E"
ACCENT_LIME = "#D8E16D"
ACCENT_GOLD = "#EFCB1D"
BORDER_COLOR = "#1E3A5F"

BRAND_DIR = Path(__file__).parent.parent / "brand"
LOGO_PATH = BRAND_DIR / "Marca-Completa-Mekatronik-Colorido-cropped.png"


def decode_float32(high: int, low: int) -> float:
    packed = struct.pack(">HH", high, low)
    return struct.unpack(">f", packed)[0]


def decode_uint32(high: int, low: int) -> int:
    return (high << 16) | low


# ── Energy Monitor register map (mirrors the simulator) ─────────────
# Format: (address, name, unit, data_type, writable)
REGISTER_MAP = [
    # ── Measurement Registers (read-only) ────────────────────────────
    (0,  "Voltage L1-N",           "V",     "float32", False),
    (2,  "Voltage L2-N",           "V",     "float32", False),
    (4,  "Voltage L3-N",           "V",     "float32", False),
    (6,  "Voltage L1-L2",          "V",     "float32", False),
    (8,  "Voltage L2-L3",          "V",     "float32", False),
    (10, "Voltage L3-L1",          "V",     "float32", False),
    (12, "Current L1",             "A",     "float32", False),
    (14, "Current L2",             "A",     "float32", False),
    (16, "Current L3",             "A",     "float32", False),
    (18, "Current Neutral",        "A",     "float32", False),
    (20, "Active Power L1",        "kW",    "float32", False),
    (22, "Active Power L2",        "kW",    "float32", False),
    (24, "Active Power L3",        "kW",    "float32", False),
    (26, "Active Power Total",     "kW",    "float32", False),
    (28, "Reactive Power L1",      "kVAr",  "float32", False),
    (30, "Reactive Power L2",      "kVAr",  "float32", False),
    (32, "Reactive Power L3",      "kVAr",  "float32", False),
    (34, "Reactive Power Total",   "kVAr",  "float32", False),
    (36, "Apparent Power L1",      "kVA",   "float32", False),
    (38, "Apparent Power L2",      "kVA",   "float32", False),
    (40, "Apparent Power L3",      "kVA",   "float32", False),
    (42, "Apparent Power Total",   "kVA",   "float32", False),
    (44, "Power Factor L1",        "",      "float32", False),
    (46, "Power Factor L2",        "",      "float32", False),
    (48, "Power Factor L3",        "",      "float32", False),
    (50, "Power Factor Total",     "",      "float32", False),
    (52, "Frequency",              "Hz",    "float32", False),
    (54, "Active Energy",          "kWh",   "uint32",  False),
    (56, "Reactive Energy",        "kVArh", "uint32",  False),
    (58, "Active Energy Export",   "kWh",   "uint32",  False),
    (60, "Apparent Energy",        "kVAh",  "uint32",  False),
    (62, "Voltage L1 THD",         "%",     "float32", False),
    (64, "Voltage L2 THD",         "%",     "float32", False),
    (66, "Voltage L3 THD",         "%",     "float32", False),
    (68, "Current L1 THD",         "%",     "float32", False),
    (70, "Current L2 THD",         "%",     "float32", False),
    (72, "Current L3 THD",         "%",     "float32", False),
    (74, "Max Demand Power",       "kW",    "float32", False),
    (76, "Max Demand Current",     "A",     "float32", False),
    (78, "Avg Voltage L-N",        "V",     "float32", False),
    (80, "Avg Voltage L-L",        "V",     "float32", False),
    (82, "Avg Current",            "A",     "float32", False),
    (84, "Voltage Unbalance",      "%",     "float32", False),
    (86, "Current Unbalance",      "%",     "float32", False),
    (88, "Run Hours",              "h",     "uint32",  False),
    (90, "Alarm Status",           "",      "uint16",  False),
    (91, "Device Status",          "",      "uint16",  False),

    # ── Configuration Registers (read/write) ─────────────────────────
    (100, "CT Primary",            "A",     "uint16",  True),
    (101, "CT Secondary",          "A",     "uint16",  True),
    (102, "VT Primary",            "V",     "uint16",  True),
    (103, "VT Secondary",          "V",     "uint16",  True),
    (104, "System Type",           "",      "uint16",  True),
    (105, "Nominal Frequency",     "Hz",    "uint16",  True),
    (106, "Demand Period",         "min",   "uint16",  True),
    (107, "Over-Voltage Threshold", "V",    "float32", True),
    (109, "Under-Voltage Threshold","V",    "float32", True),
    (111, "Over-Current Threshold", "A",    "float32", True),
    (113, "Low PF Threshold",      "",      "float32", True),
    (115, "Over-Power Threshold",  "kW",    "float32", True),
    (117, "Alarm Enable Mask",     "",      "uint16",  True),
    (118, "Energy Reset Cmd",      "",      "uint16",  True),
    (119, "Demand Reset Cmd",      "",      "uint16",  True),
    (120, "Backlight Timeout",     "s",     "uint16",  True),
    (121, "Password",              "",      "uint32",  True),
]


class LogEntry(ctk.CTkFrame):
    """A single log line in the communications log."""

    def __init__(self, master, timestamp: str, direction: str, message: str, is_error: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", height=22, **kwargs)
        self.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            self, text=timestamp, font=("Consolas", 10), text_color=TEXT_DIM, width=70,
        ).grid(row=0, column=0, padx=(4, 2), sticky="w")

        dir_color = ACCENT_LIME if direction == "TX" else BRAND_BLUE_LIGHT if direction == "RX" else ACCENT_RED
        ctk.CTkLabel(
            self, text=direction, font=("Consolas", 10, "bold"), text_color=dir_color, width=30,
        ).grid(row=0, column=1, padx=2, sticky="w")

        msg_color = ACCENT_RED if is_error else TEXT_SECONDARY
        ctk.CTkLabel(
            self, text=message, font=("Consolas", 10), text_color=msg_color, anchor="w",
        ).grid(row=0, column=2, padx=2, sticky="ew")


class RegisterValueRow(ctk.CTkFrame):
    """A row in the register values display."""

    def __init__(self, master, address: int, name: str, unit: str, **kwargs):
        super().__init__(master, fg_color="transparent", height=26, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        self.address = address

        ctk.CTkLabel(
            self, text=str(address), width=45, anchor="e",
            font=("Consolas", 11), text_color=TEXT_DIM,
        ).grid(row=0, column=0, padx=(6, 4), sticky="e")

        ctk.CTkLabel(
            self, text=name, anchor="w",
            font=("Segoe UI", 11), text_color=TEXT_SECONDARY,
        ).grid(row=0, column=1, padx=4, sticky="w")

        self.value_label = ctk.CTkLabel(
            self, text="---", width=90, anchor="e",
            font=("Consolas", 12, "bold"), text_color=TEXT_DIM,
        )
        self.value_label.grid(row=0, column=2, padx=4, sticky="e")

        ctk.CTkLabel(
            self, text=unit, width=50, anchor="w",
            font=("Segoe UI", 10), text_color=TEXT_DIM,
        ).grid(row=0, column=3, padx=(2, 6), sticky="w")

        self._prev_value = None

    def update_value(self, value: str):
        self.value_label.configure(text=value, text_color=TEXT_PRIMARY)
        self._prev_value = value

    def set_error(self):
        self.value_label.configure(text="ERR", text_color=ACCENT_RED)


class ModbusMasterGUI(ctk.CTk):
    """Modbus Master/Client test application."""

    def __init__(self):
        super().__init__()

        self.title("Mekatronik Modbus Master")
        self.geometry("1050x750")
        self.minsize(950, 650)
        self.configure(fg_color=BG_DARK)

        # State
        self._client = None
        self._connected = False
        self._polling = False
        self._async_loop: asyncio.AbstractEventLoop | None = None
        self._async_thread: threading.Thread | None = None
        self._register_rows: list[RegisterValueRow] = []
        self._poll_count = 0
        self._error_count = 0

        self._build_header()
        self._build_main()
        self._build_status_bar()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Header ───────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG_PANEL, height=70, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        if LOGO_PATH.exists():
            try:
                logo_img = ctk.CTkImage(
                    light_image=Image.open(LOGO_PATH),
                    dark_image=Image.open(LOGO_PATH),
                    size=(180, 42),
                )
                ctk.CTkLabel(header, image=logo_img, text="").pack(side="left", padx=16, pady=14)
            except Exception:
                ctk.CTkLabel(header, text="MEKATRONIK", font=("Segoe UI Bold", 20),
                              text_color=BRAND_BLUE).pack(side="left", padx=16)
        else:
            ctk.CTkLabel(header, text="MEKATRONIK", font=("Segoe UI Bold", 20),
                          text_color=BRAND_BLUE).pack(side="left", padx=16)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="right", padx=16, pady=8)
        ctk.CTkLabel(title_frame, text="Modbus Master", font=("Segoe UI Semibold", 16),
                      text_color=TEXT_PRIMARY).pack(anchor="e")
        ctk.CTkLabel(title_frame, text="Device Test Client", font=("Segoe UI", 10),
                      text_color=TEXT_SECONDARY).pack(anchor="e")

    # ── Main area ────────────────────────────────────────────────────
    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=6)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_connection_panel(main)
        self._build_register_panel(main)
        self._build_log_panel(main)

    # ── Connection panel (top-left) ──────────────────────────────────
    def _build_connection_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_PANEL, width=300, corner_radius=10)
        panel.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 6))
        panel.grid_propagate(False)

        # Transport type
        ctk.CTkLabel(panel, text="  CONNECTION", font=("Segoe UI Semibold", 12),
                      text_color=BRAND_BLUE_LIGHT).pack(anchor="w", padx=8, pady=(12, 4))

        type_frame = ctk.CTkFrame(panel, fg_color=BG_CARD, corner_radius=8)
        type_frame.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(type_frame, text="Transport", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 0))

        self.transport_var = ctk.StringVar(value="TCP")
        transport_frame = ctk.CTkFrame(type_frame, fg_color="transparent")
        transport_frame.pack(fill="x", padx=12, pady=4)

        self.tcp_radio = ctk.CTkRadioButton(
            transport_frame, text="TCP", variable=self.transport_var, value="TCP",
            font=("Segoe UI", 12), text_color=TEXT_PRIMARY,
            fg_color=BRAND_BLUE, hover_color=BRAND_BLUE_HOVER,
            command=self._on_transport_change,
        )
        self.tcp_radio.pack(side="left", padx=(0, 16))

        self.rtu_radio = ctk.CTkRadioButton(
            transport_frame, text="RTU", variable=self.transport_var, value="RTU",
            font=("Segoe UI", 12), text_color=TEXT_PRIMARY,
            fg_color=BRAND_BLUE, hover_color=BRAND_BLUE_HOVER,
            command=self._on_transport_change,
        )
        self.rtu_radio.pack(side="left")

        # TCP settings
        self.tcp_frame = ctk.CTkFrame(type_frame, fg_color="transparent")
        self.tcp_frame.pack(fill="x", padx=12, pady=(4, 8))

        ctk.CTkLabel(self.tcp_frame, text="Host", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w")
        self.tcp_host = ctk.CTkEntry(
            self.tcp_frame, placeholder_text="127.0.0.1", fg_color=BG_INPUT,
            border_color=BORDER_COLOR, text_color=TEXT_PRIMARY,
            font=("Consolas", 12), width=200,
        )
        self.tcp_host.insert(0, "127.0.0.1")
        self.tcp_host.pack(anchor="w", pady=2)

        ctk.CTkLabel(self.tcp_frame, text="Port", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))
        self.tcp_port = ctk.CTkEntry(
            self.tcp_frame, placeholder_text="502", fg_color=BG_INPUT,
            border_color=BORDER_COLOR, text_color=TEXT_PRIMARY,
            font=("Consolas", 12), width=80,
        )
        self.tcp_port.insert(0, "502")
        self.tcp_port.pack(anchor="w", pady=2)

        # RTU settings (hidden by default)
        self.rtu_frame = ctk.CTkFrame(type_frame, fg_color="transparent")

        ctk.CTkLabel(self.rtu_frame, text="Serial Port", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w")
        self.rtu_port = ctk.CTkEntry(
            self.rtu_frame, placeholder_text="COM11", fg_color=BG_INPUT,
            border_color=BORDER_COLOR, text_color=TEXT_PRIMARY,
            font=("Consolas", 12), width=120,
        )
        self.rtu_port.pack(anchor="w", pady=2)

        ctk.CTkLabel(self.rtu_frame, text="Baud Rate", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))
        self.rtu_baud = ctk.CTkComboBox(
            self.rtu_frame, values=["9600", "19200", "38400", "57600", "115200"],
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            button_color=BRAND_BLUE, button_hover_color=BRAND_BLUE_HOVER,
            dropdown_fg_color=BG_CARD, dropdown_hover_color=BRAND_BLUE,
            text_color=TEXT_PRIMARY, font=("Consolas", 12), width=120,
        )
        self.rtu_baud.set("9600")
        self.rtu_baud.pack(anchor="w", pady=2)

        # Device ID
        device_frame = ctk.CTkFrame(panel, fg_color=BG_CARD, corner_radius=8)
        device_frame.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(device_frame, text="Device ID (Slave)", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 0))
        self.device_id = ctk.CTkEntry(
            device_frame, placeholder_text="1", fg_color=BG_INPUT,
            border_color=BORDER_COLOR, text_color=TEXT_PRIMARY,
            font=("Consolas", 13), width=80,
        )
        self.device_id.insert(0, "1")
        self.device_id.pack(anchor="w", padx=12, pady=(4, 8))

        # Function code
        ctk.CTkLabel(device_frame, text="Function Code", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(4, 0))
        self.func_code = ctk.CTkComboBox(
            device_frame,
            values=["FC03 - Read Holding Registers", "FC04 - Read Input Registers"],
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            button_color=BRAND_BLUE, button_hover_color=BRAND_BLUE_HOVER,
            dropdown_fg_color=BG_CARD, dropdown_hover_color=BRAND_BLUE,
            text_color=TEXT_PRIMARY, font=("Segoe UI", 11), width=250,
        )
        self.func_code.set("FC03 - Read Holding Registers")
        self.func_code.pack(anchor="w", padx=12, pady=(4, 12))

        # Connect button
        self.connect_btn = ctk.CTkButton(
            panel, text="CONNECT", font=("Segoe UI Semibold", 13),
            fg_color=BRAND_BLUE, hover_color=BRAND_BLUE_HOVER,
            text_color=TEXT_PRIMARY, height=38, corner_radius=8,
            command=self._toggle_connection,
        )
        self.connect_btn.pack(fill="x", padx=8, pady=(4, 4))

        # Poll controls
        poll_frame = ctk.CTkFrame(panel, fg_color=BG_CARD, corner_radius=8)
        poll_frame.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(poll_frame, text="  AUTO-POLL", font=("Segoe UI Semibold", 11),
                      text_color=BRAND_BLUE_LIGHT).pack(anchor="w", padx=4, pady=(8, 4))

        interval_frame = ctk.CTkFrame(poll_frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=12)
        ctk.CTkLabel(interval_frame, text="Interval (ms)", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(side="left")
        self.poll_interval = ctk.CTkEntry(
            interval_frame, placeholder_text="1000", fg_color=BG_INPUT,
            border_color=BORDER_COLOR, text_color=TEXT_PRIMARY,
            font=("Consolas", 12), width=70,
        )
        self.poll_interval.insert(0, "1000")
        self.poll_interval.pack(side="right")

        self.poll_btn = ctk.CTkButton(
            poll_frame, text="▶  START POLLING", font=("Segoe UI Semibold", 12),
            fg_color="#1A5C1A", hover_color="#237023",
            text_color=TEXT_PRIMARY, height=34, corner_radius=6,
            command=self._toggle_polling, state="disabled",
        )
        self.poll_btn.pack(fill="x", padx=12, pady=(8, 12))

        # Single read button
        self.read_btn = ctk.CTkButton(
            panel, text="READ ONCE", font=("Segoe UI Semibold", 12),
            fg_color=BG_CARD, hover_color=BORDER_COLOR, border_width=1,
            border_color=BRAND_BLUE, text_color=BRAND_BLUE_LIGHT,
            height=34, corner_radius=6,
            command=self._read_once, state="disabled",
        )
        self.read_btn.pack(fill="x", padx=8, pady=4)

    # ── Register panel (top-right) ───────────────────────────────────
    def _build_register_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_PANEL, corner_radius=10)
        panel.grid(row=0, column=1, sticky="nsew", pady=(0, 3))
        parent.grid_rowconfigure(0, weight=3)

        # Title bar
        title_bar = ctk.CTkFrame(panel, fg_color=BG_CARD, height=36, corner_radius=0)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(title_bar, text="  REGISTER VALUES", font=("Segoe UI Semibold", 12),
                      text_color=BRAND_BLUE_LIGHT).pack(side="left", padx=8)

        self.poll_counter = ctk.CTkLabel(
            title_bar, text="Polls: 0  Errors: 0", font=("Consolas", 10),
            text_color=TEXT_DIM,
        )
        self.poll_counter.pack(side="right", padx=12)

        # Header row
        hdr = ctk.CTkFrame(panel, fg_color="transparent", height=24)
        hdr.pack(fill="x", padx=4, pady=(2, 0))
        hdr.grid_columnconfigure(1, weight=1)
        for col, (text, w, anc) in enumerate([
            ("Addr", 45, "e"), ("Parameter", 200, "w"), ("Value", 90, "e"), ("Unit", 50, "w"),
        ]):
            ctk.CTkLabel(hdr, text=text, width=w, anchor=anc,
                          font=("Segoe UI Semibold", 10), text_color=TEXT_DIM,
                          ).grid(row=0, column=col, padx=4, sticky="ew" if col == 1 else anc)

        ctk.CTkFrame(panel, fg_color=BORDER_COLOR, height=1).pack(fill="x", padx=6, pady=1)

        # Scrollable register list
        scroll = ctk.CTkScrollableFrame(
            panel, fg_color="transparent",
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=BRAND_BLUE,
        )
        scroll.pack(fill="both", expand=True, padx=4, pady=2)

        self._register_rows = []
        for i, (addr, name, unit, dtype, writable) in enumerate(REGISTER_MAP):
            row = RegisterValueRow(scroll, address=addr, name=name, unit=unit)
            row.pack(fill="x", pady=1)
            # Config registers get distinct background
            if writable:
                row.configure(fg_color="#1A2A20" if i % 2 == 0 else "transparent")
            elif i % 2 == 0:
                row.configure(fg_color=BG_CARD)
            self._register_rows.append(row)

    # ── Log panel (bottom-right) ─────────────────────────────────────
    def _build_log_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_PANEL, corner_radius=10)
        panel.grid(row=1, column=1, sticky="nsew", pady=(3, 0))

        title_bar = ctk.CTkFrame(panel, fg_color=BG_CARD, height=30, corner_radius=0)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(title_bar, text="  COMMUNICATIONS LOG", font=("Segoe UI Semibold", 11),
                      text_color=BRAND_BLUE_LIGHT).pack(side="left", padx=8)

        ctk.CTkButton(
            title_bar, text="Clear", font=("Segoe UI", 10), width=50, height=22,
            fg_color=BG_INPUT, hover_color=BORDER_COLOR, text_color=TEXT_SECONDARY,
            corner_radius=4, command=self._clear_log,
        ).pack(side="right", padx=8, pady=4)

        self.log_scroll = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", height=120,
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=BRAND_BLUE,
        )
        self.log_scroll.pack(fill="both", expand=True, padx=4, pady=2)

    # ── Status bar ───────────────────────────────────────────────────
    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, fg_color=BG_PANEL, height=28, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.conn_status = ctk.CTkLabel(
            bar, text="● DISCONNECTED", font=("Consolas", 11), text_color=ACCENT_RED,
        )
        self.conn_status.pack(side="left", padx=12)

        self.conn_info = ctk.CTkLabel(
            bar, text="", font=("Consolas", 10), text_color=TEXT_DIM,
        )
        self.conn_info.pack(side="left", padx=8)

        ctk.CTkLabel(bar, text="Mekatronik — Advanced Engineering",
                      font=("Segoe UI", 10), text_color=TEXT_DIM).pack(side="right", padx=12)

    # ── Transport toggle ─────────────────────────────────────────────
    def _on_transport_change(self):
        if self.transport_var.get() == "TCP":
            self.rtu_frame.pack_forget()
            self.tcp_frame.pack(fill="x", padx=12, pady=(4, 8))
        else:
            self.tcp_frame.pack_forget()
            self.rtu_frame.pack(fill="x", padx=12, pady=(4, 8))

    # ── Connection ───────────────────────────────────────────────────
    def _toggle_connection(self):
        if self._connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        # Start async loop
        self._async_loop = asyncio.new_event_loop()
        self._async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._async_thread.start()

        transport = self.transport_var.get()
        dev_id = int(self.device_id.get() or "1")

        if transport == "TCP":
            host = self.tcp_host.get() or "127.0.0.1"
            port = int(self.tcp_port.get() or "502")
            self._log("TX", f"Connecting TCP to {host}:{port}...")
            future = asyncio.run_coroutine_threadsafe(
                self._async_connect_tcp(host, port), self._async_loop
            )
        else:
            port = self.rtu_port.get() or "COM11"
            baud = int(self.rtu_baud.get() or "9600")
            self._log("TX", f"Connecting RTU to {port} ({baud} baud)...")
            future = asyncio.run_coroutine_threadsafe(
                self._async_connect_rtu(port, baud), self._async_loop
            )

        # Check connection result after a short delay
        self.after(1500, lambda: self._check_connection(future))

    async def _async_connect_tcp(self, host: str, port: int):
        self._client = AsyncModbusTcpClient(host, port=port)
        await self._client.connect()
        return self._client.connected

    async def _async_connect_rtu(self, port: str, baudrate: int):
        self._client = AsyncModbusSerialClient(port, baudrate=baudrate)
        await self._client.connect()
        return self._client.connected

    def _check_connection(self, future):
        try:
            connected = future.result(timeout=0.5)
        except Exception as e:
            self._log("ERR", f"Connection failed: {e}", is_error=True)
            self._set_disconnected()
            return

        if connected:
            self._connected = True
            transport = self.transport_var.get()
            if transport == "TCP":
                info = f"{self.tcp_host.get()}:{self.tcp_port.get()}"
            else:
                info = f"{self.rtu_port.get()} ({self.rtu_baud.get()})"

            self.conn_status.configure(text="● CONNECTED", text_color=ACCENT_GREEN)
            self.conn_info.configure(text=f"{transport} → {info}  Device ID: {self.device_id.get()}")
            self.connect_btn.configure(text="DISCONNECT", fg_color=ACCENT_RED, hover_color="#DC2626")
            self.poll_btn.configure(state="normal")
            self.read_btn.configure(state="normal")
            self._log("RX", f"Connected successfully via {transport}")
        else:
            self._log("ERR", "Connection failed — no response", is_error=True)
            self._set_disconnected()

    def _disconnect(self):
        if self._polling:
            self._toggle_polling()

        if self._client and self._async_loop:
            asyncio.run_coroutine_threadsafe(self._async_disconnect(), self._async_loop)

        self.after(300, self._finish_disconnect)

    async def _async_disconnect(self):
        if self._client:
            self._client.close()

    def _finish_disconnect(self):
        if self._async_loop:
            self._async_loop.call_soon_threadsafe(self._async_loop.stop)
        self._set_disconnected()
        self._log("TX", "Disconnected")

    def _set_disconnected(self):
        self._connected = False
        self._client = None
        self.conn_status.configure(text="● DISCONNECTED", text_color=ACCENT_RED)
        self.conn_info.configure(text="")
        self.connect_btn.configure(text="CONNECT", fg_color=BRAND_BLUE, hover_color=BRAND_BLUE_HOVER)
        self.poll_btn.configure(state="disabled")
        self.read_btn.configure(state="disabled")

    def _run_async_loop(self):
        asyncio.set_event_loop(self._async_loop)
        self._async_loop.run_forever()

    # ── Polling ──────────────────────────────────────────────────────
    def _toggle_polling(self):
        if self._polling:
            self._polling = False
            self.poll_btn.configure(
                text="▶  START POLLING", fg_color="#1A5C1A", hover_color="#237023",
            )
        else:
            self._polling = True
            self.poll_btn.configure(
                text="■  STOP POLLING", fg_color=ACCENT_RED, hover_color="#DC2626",
            )
            self._poll_loop()

    def _poll_loop(self):
        if not self._polling or not self._connected:
            return
        self._do_read()
        interval = int(self.poll_interval.get() or "1000")
        self.after(interval, self._poll_loop)

    def _read_once(self):
        if self._connected:
            self._do_read()

    def _do_read(self):
        """Read all registers from the device in two blocks (measurement + config)."""
        if not self._client or not self._async_loop:
            return

        dev_id = int(self.device_id.get() or "1")
        fc = 3 if "FC03" in self.func_code.get() else 4

        # Block 1: Measurement registers 0–91 (92 registers)
        # Block 2: Configuration registers 100–122 (23 registers)
        future = asyncio.run_coroutine_threadsafe(
            self._async_read_all(fc, dev_id), self._async_loop
        )
        self.after(300, lambda: self._process_read_result(future, fc))

    async def _async_read(self, fc: int, address: int, count: int, device_id: int):
        if fc == 3:
            return await self._client.read_holding_registers(address, count=count, device_id=device_id)
        else:
            return await self._client.read_input_registers(address, count=count, device_id=device_id)

    async def _async_read_all(self, fc: int, device_id: int):
        """Read both measurement and config register blocks."""
        r1 = await self._async_read(fc, 0, 92, device_id)
        r2 = await self._async_read(fc, 100, 23, device_id)
        return r1, r2

    def _process_read_result(self, future, fc: int):
        try:
            result = future.result(timeout=2.0)
        except Exception as e:
            self._error_count += 1
            self._log("ERR", f"Read failed: {e}", is_error=True)
            self._update_counter()
            return

        r1, r2 = result

        if r1.isError():
            self._error_count += 1
            self._log("ERR", f"Modbus error (block 1): {r1}", is_error=True)
            self._update_counter()
            return

        self._poll_count += 1
        fc_name = "FC03" if fc == 3 else "FC04"

        # Build combined register map: address → raw value
        regs = {}
        for i, val in enumerate(r1.registers):
            regs[i] = val
        if not r2.isError():
            for i, val in enumerate(r2.registers):
                regs[100 + i] = val

        # Decode and update each register row
        values_summary = []
        for i, (addr, name, unit, dtype, writable) in enumerate(REGISTER_MAP):
            try:
                if dtype == "float32" and addr in regs and (addr + 1) in regs:
                    val = decode_float32(regs[addr], regs[addr + 1])
                    val_str = f"{val:.2f}"
                elif dtype == "uint32" and addr in regs and (addr + 1) in regs:
                    val = decode_uint32(regs[addr], regs[addr + 1])
                    val_str = str(val)
                elif dtype == "uint16" and addr in regs:
                    val_str = str(regs[addr])
                else:
                    continue
                self._register_rows[i].update_value(val_str)
                if i < 3:
                    values_summary.append(f"{name}={val_str}")
            except (KeyError, IndexError):
                pass

        summary = ", ".join(values_summary)
        self._log("RX", f"{fc_name} Read OK ({len(regs)} regs) — {summary}...")
        self._update_counter()

    def _update_counter(self):
        self.poll_counter.configure(text=f"Polls: {self._poll_count}  Errors: {self._error_count}")

    # ── Logging ──────────────────────────────────────────────────────
    def _log(self, direction: str, message: str, is_error: bool = False):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = LogEntry(self.log_scroll, ts, direction, message, is_error)
        entry.pack(fill="x", pady=1)
        # Auto-scroll to bottom
        self.log_scroll._parent_canvas.yview_moveto(1.0)

    def _clear_log(self):
        for widget in self.log_scroll.winfo_children():
            widget.destroy()
        self._poll_count = 0
        self._error_count = 0
        self._update_counter()

    # ── Cleanup ──────────────────────────────────────────────────────
    def _on_close(self):
        if self._connected:
            self._polling = False
            if self._client and self._async_loop:
                try:
                    asyncio.run_coroutine_threadsafe(self._async_disconnect(), self._async_loop)
                except Exception:
                    pass
            if self._async_loop:
                self._async_loop.call_soon_threadsafe(self._async_loop.stop)
        self.destroy()


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ModbusMasterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
