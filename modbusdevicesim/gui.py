"""Mekatronik ModbusDeviceSIM — Branded Desktop GUI.

Runs the Modbus device simulator with a graphical interface styled
with Mekatronik's visual identity (blue/gray theme, logo, accent colors).

Two view modes:
  - Register View: full register table with raw values
  - Device Panel: realistic hardware meter front-panel with LCD display
"""

from __future__ import annotations

import asyncio
import math
import os
import sys
import threading
import time
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from modbusdevicesim.devices import DEVICE_REGISTRY
from modbusdevicesim.devices.base import DeviceModel, ModbusDeviceContext
from modbusdevicesim.simulation.engine import SimulationEngine, SimulationConfig
from modbusdevicesim.simulation.motor_drive_engine import MotorDriveEngine, MotorDriveSimConfig
from modbusdevicesim.transport.rtu_server import RTUServer
from modbusdevicesim.transport.tcp_server import TCPServer

# ── Mekatronik Brand Colors ──────────────────────────────────────────
BG_DARK = "#0A1628"         # Main background (dark navy)
BG_PANEL = "#0F2035"        # Panel background
BG_CARD = "#162A45"         # Card/section background
BG_INPUT = "#1A3250"        # Input field background
BRAND_BLUE = "#0066FF"      # Primary blue
BRAND_BLUE_HOVER = "#0052CC"
BRAND_BLUE_LIGHT = "#3D8BFF"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8899AA"
TEXT_DIM = "#556677"
ACCENT_GREEN = "#4ADE80"    # Running / success
ACCENT_RED = "#EF4444"      # Stopped / error
ACCENT_PEACH = "#EF8E5E"    # RTU accent
ACCENT_LIME = "#D8E16D"     # TCP accent
ACCENT_GOLD = "#EFCB1D"     # Warning / highlight
BORDER_COLOR = "#1E3A5F"

# ── Device Panel Colors (realistic hardware look) ────────────────────
HOUSING_DARK = "#1A1A2E"    # Outer housing
HOUSING_MID = "#16213E"     # Inner housing
LCD_BG = "#0B1622"          # LCD background (deep dark)
LCD_TEXT = "#00E5FF"         # LCD cyan text
LCD_TEXT_DIM = "#005566"     # LCD dimmed text
LCD_LABEL = "#4FC3F7"       # LCD labels
LCD_ACCENT = "#80DEEA"      # LCD accent values
LED_OFF = "#2A2A3E"         # LED off color
NAMEPLATE_BG = "#0D1B2A"    # Nameplate background

# ── Logo path ────────────────────────────────────────────────────────
BRAND_DIR = Path(__file__).parent.parent / "brand"
LOGO_PATH = BRAND_DIR / "Marca-Completa-Mekatronik-Colorido-cropped.png"


# ═════════════════════════════════════════════════════════════════════
# Register View Components
# ═════════════════════════════════════════════════════════════════════

class RegisterRow(ctk.CTkFrame):
    """A single row in the register display table."""

    def __init__(self, master, address: str, name: str, value: str, unit: str,
                 writable: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", height=28, **kwargs)
        self.grid_columnconfigure(1, weight=1)

        self.addr_label = ctk.CTkLabel(
            self, text=address, width=50, anchor="e",
            font=("Consolas", 12), text_color=TEXT_DIM,
        )
        self.addr_label.grid(row=0, column=0, padx=(8, 4), sticky="e")

        name_color = "#7EC8A0" if writable else TEXT_SECONDARY
        self.name_label = ctk.CTkLabel(
            self, text=name, anchor="w",
            font=("Segoe UI", 12), text_color=name_color,
        )
        self.name_label.grid(row=0, column=1, padx=4, sticky="w")

        self.value_label = ctk.CTkLabel(
            self, text=value, width=90, anchor="e",
            font=("Consolas", 13, "bold"), text_color=TEXT_PRIMARY,
        )
        self.value_label.grid(row=0, column=2, padx=4, sticky="e")

        self.unit_label = ctk.CTkLabel(
            self, text=unit, width=50, anchor="w",
            font=("Segoe UI", 11), text_color=TEXT_DIM,
        )
        self.unit_label.grid(row=0, column=3, padx=(2, 8), sticky="w")

    def update_value(self, value: str):
        self.value_label.configure(text=value)


class SectionHeader(ctk.CTkFrame):
    """Colored section header bar."""

    def __init__(self, master, title: str, color: str = BRAND_BLUE, **kwargs):
        super().__init__(master, fg_color=color, height=30, corner_radius=6, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self, text=f"  {title}", anchor="w",
            font=("Segoe UI Semibold", 12), text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="ew", padx=4)


# ═════════════════════════════════════════════════════════════════════
# Device Panel — Realistic Hardware Meter Face
# ═════════════════════════════════════════════════════════════════════

# LCD display page definitions — per device type
DEVICE_LCD_PAGES = {}

# ── Energy Monitor LCD pages ──────────────────────────────────────────
DEVICE_LCD_PAGES["MK-EM3P Energy Monitor"] = [
    {
        "title": "VOLTAGE L-N",
        "rows": [
            ("L1", 0, "V"),
            ("L2", 2, "V"),
            ("L3", 4, "V"),
        ],
    },
    {
        "title": "VOLTAGE L-L",
        "rows": [
            ("L1-L2", 6, "V"),
            ("L2-L3", 8, "V"),
            ("L3-L1", 10, "V"),
        ],
    },
    {
        "title": "CURRENT",
        "rows": [
            ("L1", 12, "A"),
            ("L2", 14, "A"),
            ("L3", 16, "A"),
            ("N", 18, "A"),
        ],
    },
    {
        "title": "ACTIVE POWER",
        "rows": [
            ("L1", 20, "kW"),
            ("L2", 22, "kW"),
            ("L3", 24, "kW"),
            ("TOT", 26, "kW"),
        ],
    },
    {
        "title": "REACTIVE POWER",
        "rows": [
            ("L1", 28, "kVAr"),
            ("L2", 30, "kVAr"),
            ("L3", 32, "kVAr"),
            ("TOT", 34, "kVAr"),
        ],
    },
    {
        "title": "APPARENT POWER",
        "rows": [
            ("L1", 36, "kVA"),
            ("L2", 38, "kVA"),
            ("L3", 40, "kVA"),
            ("TOT", 42, "kVA"),
        ],
    },
    {
        "title": "POWER FACTOR",
        "rows": [
            ("L1", 44, ""),
            ("L2", 46, ""),
            ("L3", 48, ""),
            ("TOT", 50, ""),
        ],
    },
    {
        "title": "FREQUENCY",
        "rows": [
            ("Hz", 52, "Hz"),
        ],
    },
    {
        "title": "ENERGY",
        "rows": [
            ("kWh", 54, "kWh"),
            ("kVArh", 56, "kVArh"),
            ("Exp", 58, "kWh"),
            ("kVAh", 60, "kVAh"),
        ],
    },
    {
        "title": "THD VOLTAGE",
        "rows": [
            ("V L1", 62, "%"),
            ("V L2", 64, "%"),
            ("V L3", 66, "%"),
        ],
    },
    {
        "title": "THD CURRENT",
        "rows": [
            ("I L1", 68, "%"),
            ("I L2", 70, "%"),
            ("I L3", 72, "%"),
        ],
    },
    {
        "title": "DEMAND / AVERAGES",
        "rows": [
            ("Pmax", 74, "kW"),
            ("Imax", 76, "A"),
            ("Vavg", 78, "V"),
            ("Iavg", 82, "A"),
        ],
    },
    {
        "title": "SYSTEM STATUS",
        "rows": [
            ("Alarm", 90, ""),
            ("Status", 91, ""),
            ("RunH", 88, "h"),
        ],
    },
]

# ── Motor Drive LCD pages ─────────────────────────────────────────────
DEVICE_LCD_PAGES["MK-VFD7 Motor Drive"] = [
    {
        "title": "OVERVIEW",
        "type": "overview",
        "rows": [],
    },
    {
        "title": "OUTPUT",
        "rows": [
            ("Freq", 0, "Hz"),
            ("Volt", 2, "V"),
            ("Curr", 4, "A"),
            ("Powr", 6, "kW"),
        ],
    },
    {
        "title": "MOTOR",
        "rows": [
            ("Speed", 8, "RPM"),
            ("Torq", 10, "%"),
        ],
    },
    {
        "title": "DRIVE",
        "rows": [
            ("DC Bus", 12, "V"),
            ("Drv T", 14, "°C"),
            ("Mot T", 16, "°C"),
        ],
    },
    {
        "title": "POWER / ENERGY",
        "rows": [
            ("Pin", 24, "kW"),
            ("Pout", 6, "kW"),
            ("PF", 22, ""),
            ("kWh", 20, "kWh"),
        ],
    },
    {
        "title": "REFERENCE",
        "rows": [
            ("Ref", 101, "Hz"),
            ("Out", 0, "Hz"),
            ("Acc", 103, "s"),
            ("Dec", 105, "s"),
        ],
    },
    {
        "title": "LIMITS",
        "rows": [
            ("Fmax", 107, "Hz"),
            ("Fmin", 109, "Hz"),
            ("OC", 119, "A"),
            ("OV", 121, "V"),
        ],
    },
    {
        "title": "MOTOR NAMEPLATE",
        "rows": [
            ("Vrat", 111, "V"),
            ("Irat", 112, "A"),
            ("Frat", 114, "Hz"),
            ("RPM", 115, "RPM"),
        ],
    },
    {
        "title": "STATUS",
        "rows": [
            ("Stat", 26, ""),
            ("Fault", 27, ""),
            ("Warn", 28, ""),
            ("RunH", 18, "h"),
        ],
    },
]

# Default fallback
LCD_PAGES = DEVICE_LCD_PAGES.get("MK-EM3P Energy Monitor", [])

# Device-specific panel info
DEVICE_PANEL_INFO = {
    "MK-EM3P Energy Monitor": {
        "model": "MK-EM3P",
        "subtitle": "Energy Monitor",
        "leds": ["PWR", "COM", "ALM", "RTU", "TCP"],
    },
    "MK-VFD7 Motor Drive": {
        "model": "MK-VFD7",
        "subtitle": "Motor Drive",
        "leds": ["PWR", "RUN", "FLT", "FWD", "REV", "LOC"],
    },
}


class LEDIndicator(ctk.CTkFrame):
    """A small LED indicator with label — mimics a real hardware LED."""

    def __init__(self, master, label: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on = False

        self.led = ctk.CTkFrame(self, width=12, height=12, corner_radius=6, fg_color=LED_OFF)
        self.led.pack(side="left", padx=(0, 4))
        self.led.pack_propagate(False)

        ctk.CTkLabel(
            self, text=label, font=("Consolas", 10, "bold"), text_color=TEXT_DIM,
        ).pack(side="left")

    def set_on(self, color: str = ACCENT_GREEN):
        self._on = True
        self.led.configure(fg_color=color)

    def set_off(self):
        self._on = False
        self.led.configure(fg_color=LED_OFF)


class DevicePanel(ctk.CTkFrame):
    """Realistic hardware device front panel — adapts to selected device."""

    def __init__(self, master, device_name: str = "MK-EM3P Energy Monitor",
                 write_callback=None, **kwargs):
        super().__init__(master, fg_color=HOUSING_DARK, corner_radius=16, **kwargs)

        self._device_name = device_name
        self._write_callback = write_callback
        self._lcd_pages = DEVICE_LCD_PAGES.get(device_name, LCD_PAGES)
        self._panel_info = DEVICE_PANEL_INFO.get(device_name, DEVICE_PANEL_INFO["MK-EM3P Energy Monitor"])
        self._current_page = 0
        self._lcd_value_labels: list[tuple[ctk.CTkLabel, ctk.CTkLabel, ctk.CTkLabel]] = []
        self._overview_canvas: tk.Canvas | None = None
        self._overview_items: dict[str, int] = {}
        self._motor_angle: float = 0.0
        self._anim_id: str | None = None

        # Local control state (VFD only)
        self._local_mode = False
        self._local_run = False
        self._local_reverse = False
        self._local_freq_ref = 30.0

        self._build_panel()

    def _build_panel(self):
        # Outer housing frame (simulates device casing)
        housing = ctk.CTkFrame(self, fg_color=HOUSING_MID, corner_radius=14)
        housing.pack(fill="both", expand=True, padx=12, pady=12)

        # ── Top nameplate ─────────────────────────────────────────────
        nameplate = ctk.CTkFrame(housing, fg_color=NAMEPLATE_BG, height=60, corner_radius=8)
        nameplate.pack(fill="x", padx=16, pady=(16, 8))
        nameplate.pack_propagate(False)

        # Logo on nameplate
        if LOGO_PATH.exists():
            try:
                logo_img = ctk.CTkImage(
                    light_image=Image.open(LOGO_PATH),
                    dark_image=Image.open(LOGO_PATH),
                    size=(140, 33),
                )
                ctk.CTkLabel(nameplate, image=logo_img, text="").pack(side="left", padx=12, pady=8)
            except Exception:
                ctk.CTkLabel(
                    nameplate, text="MEKATRONIK", font=("Consolas", 14, "bold"),
                    text_color=BRAND_BLUE,
                ).pack(side="left", padx=12, pady=8)
        else:
            ctk.CTkLabel(
                nameplate, text="MEKATRONIK", font=("Consolas", 14, "bold"),
                text_color=BRAND_BLUE,
            ).pack(side="left", padx=12, pady=8)

        # Model label
        model_frame = ctk.CTkFrame(nameplate, fg_color="transparent")
        model_frame.pack(side="right", padx=12, pady=4)
        ctk.CTkLabel(
            model_frame, text=self._panel_info["model"], font=("Consolas", 16, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="e")
        ctk.CTkLabel(
            model_frame, text=self._panel_info["subtitle"], font=("Segoe UI", 10),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="e")

        # ── LCD Display ───────────────────────────────────────────────
        lcd_outer = ctk.CTkFrame(housing, fg_color="#061018", corner_radius=10)
        lcd_outer.pack(fill="both", expand=True, padx=16, pady=8)

        self.lcd_frame = ctk.CTkFrame(lcd_outer, fg_color=LCD_BG, corner_radius=6)
        self.lcd_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # LCD header row (page title + page number)
        lcd_header = ctk.CTkFrame(self.lcd_frame, fg_color="transparent", height=30)
        lcd_header.pack(fill="x", padx=12, pady=(10, 2))
        lcd_header.pack_propagate(False)

        self.lcd_title = ctk.CTkLabel(
            lcd_header, text="VOLTAGE L-N", anchor="w",
            font=("Consolas", 14, "bold"), text_color=LCD_LABEL,
        )
        self.lcd_title.pack(side="left")

        self.lcd_page_num = ctk.CTkLabel(
            lcd_header, text="1/13", anchor="e",
            font=("Consolas", 11), text_color=LCD_TEXT_DIM,
        )
        self.lcd_page_num.pack(side="right")

        # Separator
        ctk.CTkFrame(self.lcd_frame, fg_color=LCD_TEXT_DIM, height=1).pack(fill="x", padx=12, pady=2)

        # LCD value rows container
        self.lcd_values_frame = ctk.CTkFrame(self.lcd_frame, fg_color="transparent")
        self.lcd_values_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self._render_lcd_page()

        # ── LED Indicators ────────────────────────────────────────────
        led_bar = ctk.CTkFrame(housing, fg_color="transparent", height=30)
        led_bar.pack(fill="x", padx=20, pady=(4, 4))

        self.leds = {}
        led_names = self._panel_info.get("leds", ["PWR", "COM", "ALM", "RTU", "TCP"])
        for i, name in enumerate(led_names):
            led = LEDIndicator(led_bar, name)
            led.pack(side="left", padx=(0, 20) if i < len(led_names) - 1 else (0, 0))
            self.leds[name] = led

        # ── Local Control Panel (VFD only) ────────────────────────────
        if self._device_name == "MK-VFD7 Motor Drive":
            self._build_local_controls(housing)

        # ── Navigation Buttons ────────────────────────────────────────
        btn_bar = ctk.CTkFrame(housing, fg_color="transparent", height=44)
        btn_bar.pack(fill="x", padx=16, pady=(4, 16))

        btn_style = {
            "font": ("Consolas", 14, "bold"),
            "fg_color": "#1C2940",
            "hover_color": "#2A3D5C",
            "text_color": LCD_TEXT,
            "corner_radius": 6,
            "width": 52,
            "height": 36,
        }

        # Center the buttons
        btn_center = ctk.CTkFrame(btn_bar, fg_color="transparent")
        btn_center.pack(anchor="center")

        ctk.CTkButton(
            btn_center, text="\u25C0", command=self._page_prev, **btn_style,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_center, text="\u25B2", command=self._page_first, **btn_style,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_center, text="\u25BC", command=self._page_last, **btn_style,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_center, text="\u25B6", command=self._page_next, **btn_style,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_center, text="ENTER",
            font=("Consolas", 11, "bold"),
            fg_color=BRAND_BLUE, hover_color=BRAND_BLUE_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=6,
            width=72, height=36,
            command=self._page_next,
        ).pack(side="left", padx=(12, 4))

    def _render_lcd_page(self):
        """Render the current LCD page."""
        # Cancel any running overview animation
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None

        # Clear previous value rows
        for widget in self.lcd_values_frame.winfo_children():
            widget.destroy()
        self._lcd_value_labels.clear()
        self._overview_canvas = None
        self._overview_items.clear()

        page = self._lcd_pages[self._current_page]
        self.lcd_title.configure(text=page["title"])
        mode_tag = " LOC" if self._local_mode else ""
        self.lcd_page_num.configure(text=f"{mode_tag} {self._current_page + 1}/{len(self._lcd_pages)}")

        if page.get("type") == "overview":
            self._render_overview_page()
            return

        for label_text, addr, unit in page["rows"]:
            row = ctk.CTkFrame(self.lcd_values_frame, fg_color="transparent", height=36)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            lbl = ctk.CTkLabel(
                row, text=label_text, anchor="w", width=60,
                font=("Consolas", 15), text_color=LCD_TEXT_DIM,
            )
            lbl.pack(side="left", padx=(8, 0))

            val = ctk.CTkLabel(
                row, text="---", anchor="e",
                font=("Consolas", 22, "bold"), text_color=LCD_TEXT,
            )
            val.pack(side="right", padx=(0, 8))

            unit_lbl = ctk.CTkLabel(
                row, text=unit, anchor="e", width=50,
                font=("Consolas", 13), text_color=LCD_LABEL,
            )
            unit_lbl.pack(side="right", padx=(0, 4))

            self._lcd_value_labels.append((val, addr, unit))

    # ── Local Control Mode (VFD) ─────────────────────────────────────

    @property
    def is_local_mode(self) -> bool:
        return self._local_mode

    def _build_local_controls(self, housing):
        """Build the local control panel for VFD operation."""
        ctrl_frame = ctk.CTkFrame(housing, fg_color=BG_CARD, corner_radius=8)
        ctrl_frame.pack(fill="x", padx=16, pady=(4, 4))
        self._ctrl_frame = ctrl_frame

        # ── LOCAL / REMOTE switch ────────────────────────────────────
        switch_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        switch_row.pack(fill="x", padx=10, pady=(8, 4))

        self._local_switch = ctk.CTkSwitch(
            switch_row, text="LOCAL CONTROL", font=("Consolas", 11, "bold"),
            text_color=TEXT_SECONDARY, fg_color=TEXT_DIM,
            progress_color=ACCENT_GOLD, button_color=TEXT_PRIMARY,
            width=40, command=self._toggle_local_mode,
        )
        self._local_switch.pack(side="left")

        self._mode_label = ctk.CTkLabel(
            switch_row, text="REMOTE", font=("Consolas", 10, "bold"),
            text_color=LCD_TEXT_DIM,
        )
        self._mode_label.pack(side="right", padx=4)

        # ── Control buttons ──────────────────────────────────────────
        self._controls_inner = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        self._controls_inner.pack(fill="x", padx=10, pady=(2, 8))

        btn_row = ctk.CTkFrame(self._controls_inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=2)

        ctrl_btn = {
            "font": ("Consolas", 11, "bold"),
            "corner_radius": 6,
            "height": 32,
        }

        self._run_btn = ctk.CTkButton(
            btn_row, text="\u25B6 RUN", width=80,
            fg_color="#1A5C1A", hover_color="#237023",
            text_color=ACCENT_GREEN, state="disabled",
            command=self._on_run_stop, **ctrl_btn,
        )
        self._run_btn.pack(side="left", padx=(0, 4))

        self._dir_btn = ctk.CTkButton(
            btn_row, text="FWD", width=60,
            fg_color="#1C2940", hover_color="#2A3D5C",
            text_color=LCD_LABEL, state="disabled",
            command=self._on_fwd_rev, **ctrl_btn,
        )
        self._dir_btn.pack(side="left", padx=4)

        self._fault_btn = ctk.CTkButton(
            btn_row, text="RST", width=50,
            fg_color="#3D1A1A", hover_color="#5C2323",
            text_color=ACCENT_RED, state="disabled",
            command=self._on_fault_reset, **ctrl_btn,
        )
        self._fault_btn.pack(side="left", padx=4)

        self._jog_btn = ctk.CTkButton(
            btn_row, text="JOG", width=50,
            fg_color="#1C2940", hover_color="#2A3D5C",
            text_color=ACCENT_GOLD, state="disabled", **ctrl_btn,
        )
        self._jog_btn.pack(side="left", padx=4)
        # Bind press/release for JOG
        self._jog_btn.bind("<ButtonPress-1>", lambda e: self._on_jog_press())
        self._jog_btn.bind("<ButtonRelease-1>", lambda e: self._on_jog_release())

        # ── Frequency reference ──────────────────────────────────────
        freq_row = ctk.CTkFrame(self._controls_inner, fg_color="transparent")
        freq_row.pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(
            freq_row, text="REF", font=("Consolas", 10),
            text_color=LCD_TEXT_DIM, width=30,
        ).pack(side="left")

        freq_btn = {
            "font": ("Consolas", 12, "bold"),
            "fg_color": "#1C2940", "hover_color": "#2A3D5C",
            "text_color": LCD_TEXT, "corner_radius": 4,
            "width": 34, "height": 28,
        }

        self._freq_btns = []
        for text, delta in [("\u00AB", -5.0), ("\u2212", -0.5)]:
            b = ctk.CTkButton(
                freq_row, text=text, state="disabled",
                command=lambda d=delta: self._on_freq_adjust(d), **freq_btn,
            )
            b.pack(side="left", padx=2)
            self._freq_btns.append(b)

        self._freq_display = ctk.CTkLabel(
            freq_row, text="30.0 Hz", font=("Consolas", 14, "bold"),
            text_color=LCD_TEXT, width=90,
        )
        self._freq_display.pack(side="left", padx=4)

        for text, delta in [("+", 0.5), ("\u00BB", 5.0)]:
            b = ctk.CTkButton(
                freq_row, text=text, state="disabled",
                command=lambda d=delta: self._on_freq_adjust(d), **freq_btn,
            )
            b.pack(side="left", padx=2)
            self._freq_btns.append(b)

    def _toggle_local_mode(self):
        """Toggle between LOCAL and REMOTE control."""
        self._local_mode = bool(self._local_switch.get())

        if self._local_mode:
            self._mode_label.configure(text="LOCAL", text_color=ACCENT_GOLD)
            btn_state = "normal"
        else:
            self._mode_label.configure(text="REMOTE", text_color=LCD_TEXT_DIM)
            btn_state = "disabled"

        # Enable/disable control buttons
        for widget in [self._run_btn, self._dir_btn, self._fault_btn, self._jog_btn]:
            widget.configure(state=btn_state)
        for btn in self._freq_btns:
            btn.configure(state=btn_state)

    def _write_ctrl_word(self):
        """Build and write the control word from local state."""
        if not self._write_callback:
            return
        ctrl = 0
        if self._local_run:
            ctrl |= 0x0001  # CTRL_RUN
        if self._local_reverse:
            ctrl |= 0x0002  # CTRL_REVERSE
        if getattr(self, '_local_jog', False):
            ctrl |= 0x0004  # CTRL_JOG
        self._write_callback(100, float(ctrl))

    def _on_run_stop(self):
        """Toggle RUN / STOP."""
        self._local_run = not self._local_run
        if self._local_run:
            self._run_btn.configure(
                text="\u25A0 STOP", fg_color="#5C1A1A", hover_color="#7A2323",
                text_color=ACCENT_RED,
            )
        else:
            self._run_btn.configure(
                text="\u25B6 RUN", fg_color="#1A5C1A", hover_color="#237023",
                text_color=ACCENT_GREEN,
            )
        self._write_ctrl_word()

    def _on_fwd_rev(self):
        """Toggle FWD / REV."""
        self._local_reverse = not self._local_reverse
        if self._local_reverse:
            self._dir_btn.configure(text="REV", text_color=ACCENT_PEACH)
        else:
            self._dir_btn.configure(text="FWD", text_color=LCD_LABEL)
        self._write_ctrl_word()

    def _on_freq_adjust(self, delta: float):
        """Adjust frequency reference by delta Hz."""
        self._local_freq_ref = max(0.0, min(60.0, self._local_freq_ref + delta))
        self._freq_display.configure(text=f"{self._local_freq_ref:.1f} Hz")
        if self._write_callback:
            self._write_callback(101, self._local_freq_ref)

    def _on_fault_reset(self):
        """Send fault reset command."""
        if self._write_callback:
            self._write_callback(127, float(0x1234))

    def _on_jog_press(self):
        """JOG button pressed — set jog bit."""
        if not self._local_mode:
            return
        self._local_jog = True
        self._write_ctrl_word()

    def _on_jog_release(self):
        """JOG button released — clear jog bit."""
        if not self._local_mode:
            return
        self._local_jog = False
        self._write_ctrl_word()

    # ── Overview HMI Page ──────────────────────────────────────────────

    def _render_overview_page(self):
        """Create the canvas for the SCADA/HMI overview."""
        canvas = tk.Canvas(
            self.lcd_values_frame,
            bg=LCD_BG,
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill="both", expand=True)
        self._overview_canvas = canvas
        canvas.bind("<Configure>", lambda e: self._draw_overview())

    def _draw_overview(self):
        """Draw / redraw all overview elements on the canvas."""
        canvas = self._overview_canvas
        if not canvas or not canvas.winfo_exists():
            return

        canvas.delete("all")
        self._overview_items.clear()

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10 or h < 10:
            return

        items = self._overview_items

        # ── Layout constants ──────────────────────────────────────────
        cx = w * 0.50          # motor center x
        cy = h * 0.34          # motor center y
        r = min(w, h) * 0.19   # motor outer radius
        r_hub = r * 0.25       # inner hub radius
        r_stator = r * 0.92    # stator ring radius

        # ── Motor body ────────────────────────────────────────────────
        # Stator ring (outer)
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=LCD_TEXT_DIM, width=2, fill="",
        )
        # Stator ring (inner accent)
        canvas.create_oval(
            cx - r_stator, cy - r_stator, cx + r_stator, cy + r_stator,
            outline="#003344", width=1, fill="",
        )
        # Hub circle
        canvas.create_oval(
            cx - r_hub, cy - r_hub, cx + r_hub, cy + r_hub,
            outline=LCD_TEXT_DIM, width=1, fill=LCD_BG,
        )
        # Shaft dot
        canvas.create_oval(
            cx - 3, cy - 3, cx + 3, cy + 3,
            fill=LCD_TEXT_DIM, outline="",
        )

        # ── Rotor markers (3 lines at 120° intervals) ────────────────
        for i in range(3):
            angle_rad = math.radians(self._motor_angle + i * 120)
            x1 = cx + r_hub * math.cos(angle_rad)
            y1 = cy + r_hub * math.sin(angle_rad)
            x2 = cx + (r - 6) * math.cos(angle_rad)
            y2 = cy + (r - 6) * math.sin(angle_rad)
            item = canvas.create_line(
                x1, y1, x2, y2,
                fill=LCD_TEXT, width=2, capstyle="round",
            )
            items[f"marker_{i}"] = item

        # ── Direction label in motor center ───────────────────────────
        items["dir_text"] = canvas.create_text(
            cx, cy + r + 14,
            text="", font=("Consolas", 9, "bold"),
            fill=LCD_LABEL, anchor="center",
        )

        # ── Parameter readouts — left column ─────────────────────────
        lx = w * 0.06
        ly_start = cy - r * 0.7
        ly_gap = max(28, h * 0.09)

        left_params = [
            ("FREQ", "val_freq", "Hz"),
            ("CURR", "val_curr", "A"),
            ("POWER", "val_power", "kW"),
        ]
        for i, (label, key, unit) in enumerate(left_params):
            y = ly_start + i * ly_gap
            canvas.create_text(
                lx, y, text=label, font=("Consolas", 9),
                fill=LCD_TEXT_DIM, anchor="w",
            )
            items[key] = canvas.create_text(
                lx + 2, y + 15, text="---", font=("Consolas", 16, "bold"),
                fill=LCD_TEXT, anchor="w",
            )
            canvas.create_text(
                lx + 80, y + 15, text=unit, font=("Consolas", 10),
                fill=LCD_LABEL, anchor="w",
            )

        # ── Parameter readouts — right column ─────────────────────────
        rx = w * 0.95
        ry_start = ly_start

        right_params = [
            ("SPEED", "val_speed", "RPM"),
            ("TORQUE", "val_torque", "%"),
            ("TEMP", "val_temp", "°C"),
        ]
        for i, (label, key, unit) in enumerate(right_params):
            y = ry_start + i * ly_gap
            canvas.create_text(
                rx, y, text=label, font=("Consolas", 9),
                fill=LCD_TEXT_DIM, anchor="e",
            )
            items[key] = canvas.create_text(
                rx - 2, y + 15, text="---", font=("Consolas", 16, "bold"),
                fill=LCD_TEXT, anchor="e",
            )
            canvas.create_text(
                rx - 62, y + 15, text=unit, font=("Consolas", 10),
                fill=LCD_LABEL, anchor="e",
            )

        # ── Torque bar gauge ──────────────────────────────────────────
        bar_y = h * 0.72
        bar_h = 14
        bar_x1 = w * 0.12
        bar_x2 = w * 0.78
        bar_label_x = w * 0.06

        canvas.create_text(
            bar_label_x, bar_y + bar_h / 2, text="LOAD",
            font=("Consolas", 9), fill=LCD_TEXT_DIM, anchor="w",
        )

        # Background
        items["torque_bg"] = canvas.create_rectangle(
            bar_x1, bar_y, bar_x2, bar_y + bar_h,
            fill="#0A2030", outline=LCD_TEXT_DIM, width=1,
        )
        # Fill
        items["torque_bar"] = canvas.create_rectangle(
            bar_x1, bar_y, bar_x1, bar_y + bar_h,
            fill=LCD_TEXT, outline="",
        )
        # Percentage text
        items["torque_pct"] = canvas.create_text(
            bar_x2 + 8, bar_y + bar_h / 2, text="0%",
            font=("Consolas", 11, "bold"), fill=LCD_TEXT, anchor="w",
        )

        # ── 100% tick mark on bar ─────────────────────────────────────
        tick_x = bar_x1 + (bar_x2 - bar_x1) * (100.0 / 150.0)
        canvas.create_line(
            tick_x, bar_y - 2, tick_x, bar_y + bar_h + 2,
            fill=LCD_TEXT_DIM, width=1, dash=(2, 2),
        )

        # ── Status bar at bottom ──────────────────────────────────────
        status_y = h * 0.88
        status_gap = w * 0.22

        # Status badges
        items["status_text"] = canvas.create_text(
            w * 0.18, status_y, text="STOPPED",
            font=("Consolas", 12, "bold"), fill=ACCENT_RED, anchor="center",
        )
        items["status_dir"] = canvas.create_text(
            w * 0.42, status_y, text="FWD",
            font=("Consolas", 11, "bold"), fill=LCD_LABEL, anchor="center",
        )
        items["status_atref"] = canvas.create_text(
            w * 0.62, status_y, text="",
            font=("Consolas", 10), fill=ACCENT_GREEN, anchor="center",
        )
        items["status_accel"] = canvas.create_text(
            w * 0.80, status_y, text="",
            font=("Consolas", 10), fill=ACCENT_GOLD, anchor="center",
        )

    def _animate_overview(self):
        """Fast animation tick for motor rotation (runs at ~80ms)."""
        if self._overview_canvas is None:
            self._anim_id = None
            return
        canvas = self._overview_canvas
        if not canvas.winfo_exists():
            self._anim_id = None
            return

        items = self._overview_items
        if not items or "marker_0" not in items:
            self._anim_id = self.after(80, self._animate_overview)
            return

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        cx = w * 0.50
        cy = h * 0.34
        r = min(w, h) * 0.19
        r_hub = r * 0.25

        for i in range(3):
            angle_rad = math.radians(self._motor_angle + i * 120)
            x1 = cx + r_hub * math.cos(angle_rad)
            y1 = cy + r_hub * math.sin(angle_rad)
            x2 = cx + (r - 6) * math.cos(angle_rad)
            y2 = cy + (r - 6) * math.sin(angle_rad)
            canvas.coords(items[f"marker_{i}"], x1, y1, x2, y2)

        self._anim_id = self.after(80, self._animate_overview)

    def _page_next(self):
        self._current_page = (self._current_page + 1) % len(self._lcd_pages)
        self._render_lcd_page()

    def _page_prev(self):
        self._current_page = (self._current_page - 1) % len(self._lcd_pages)
        self._render_lcd_page()

    def _page_first(self):
        self._current_page = 0
        self._render_lcd_page()

    def _page_last(self):
        self._current_page = len(self._lcd_pages) - 1
        self._render_lcd_page()

    def update_values(self, current_values: dict[int, float]):
        """Update LCD display with current simulation values."""
        if self._overview_canvas is not None:
            self._update_overview(current_values)
            return

        for val_label, addr, unit in self._lcd_value_labels:
            value = current_values.get(addr, 0.0)
            if isinstance(value, float) and value != int(value):
                val_str = f"{value:.2f}"
            else:
                val_str = str(int(value))
            val_label.configure(text=val_str)

    def _update_overview(self, cv: dict[int, float]):
        """Update the overview HMI canvas with current simulation values."""
        from modbusdevicesim.devices.motor_drive import (
            STATUS_RUNNING, STATUS_FORWARD, STATUS_REVERSE,
            STATUS_AT_REF, STATUS_ACCEL, STATUS_DECEL, STATUS_FAULT,
        )
        canvas = self._overview_canvas
        if not canvas or not canvas.winfo_exists():
            return

        items = self._overview_items
        if not items:
            return

        # Extract values
        freq = cv.get(0, 0.0)
        speed = cv.get(8, 0.0)
        current = cv.get(4, 0.0)
        power = cv.get(6, 0.0)
        torque = cv.get(10, 0.0)
        temp = cv.get(14, 0.0)
        status = int(cv.get(26, 0))

        # Update parameter text
        canvas.itemconfigure(items["val_freq"], text=f"{freq:.1f}")
        canvas.itemconfigure(items["val_speed"], text=f"{speed:.0f}")
        canvas.itemconfigure(items["val_curr"], text=f"{current:.1f}")
        canvas.itemconfigure(items["val_power"], text=f"{power:.2f}")
        canvas.itemconfigure(items["val_torque"], text=f"{torque:.1f}")

        # Temperature with color coding
        temp_color = LCD_TEXT
        if temp > 70:
            temp_color = ACCENT_GOLD
        if temp > 80:
            temp_color = ACCENT_RED
        canvas.itemconfigure(items["val_temp"], text=f"{temp:.1f}", fill=temp_color)

        # Rotate motor markers based on speed
        # At 1800 RPM → 30 rev/s → at 80ms ticks, ~8.6° per tick
        rpm_visual = speed / 60.0
        angle_step = rpm_visual * 360.0 * 0.08  # 80ms tick interval
        if status & STATUS_REVERSE:
            angle_step = -angle_step
        self._motor_angle = (self._motor_angle + angle_step) % 360

        # Start animation timer if not already running
        if self._anim_id is None:
            self._anim_id = self.after(80, self._animate_overview)

        # Update direction label
        if status & STATUS_RUNNING:
            dir_text = "\u25C0 REV" if (status & STATUS_REVERSE) else "FWD \u25B6"
            dir_color = ACCENT_PEACH if (status & STATUS_REVERSE) else ACCENT_GREEN
        else:
            dir_text = "\u25CF STOP"
            dir_color = LCD_TEXT_DIM
        canvas.itemconfigure(items["dir_text"], text=dir_text, fill=dir_color)

        # Update torque bar
        bar_coords = canvas.coords(items["torque_bg"])
        if bar_coords:
            bx1, by1, bx2, by2 = bar_coords
            bar_width = bx2 - bx1
            fill_frac = min(torque / 150.0, 1.0)
            canvas.coords(items["torque_bar"], bx1, by1, bx1 + fill_frac * bar_width, by2)
            if torque > 100:
                bar_color = ACCENT_RED
            elif torque > 80:
                bar_color = ACCENT_GOLD
            else:
                bar_color = LCD_TEXT
            canvas.itemconfigure(items["torque_bar"], fill=bar_color)
            canvas.itemconfigure(items["torque_pct"], text=f"{torque:.0f}%")

        # Update status bar
        if status & STATUS_FAULT:
            canvas.itemconfigure(items["status_text"], text="\u26A0 FAULT", fill=ACCENT_RED)
        elif status & STATUS_RUNNING:
            canvas.itemconfigure(items["status_text"], text="\u25B6 RUNNING", fill=ACCENT_GREEN)
        else:
            canvas.itemconfigure(items["status_text"], text="\u25A0 STOPPED", fill=ACCENT_RED)

        dir_str = "REV" if (status & STATUS_REVERSE) else "FWD"
        canvas.itemconfigure(items["status_dir"], text=dir_str,
                             fill=ACCENT_PEACH if (status & STATUS_REVERSE) else LCD_LABEL)

        if status & STATUS_AT_REF:
            canvas.itemconfigure(items["status_atref"], text="AT REF", fill=ACCENT_GREEN)
        else:
            canvas.itemconfigure(items["status_atref"], text="")

        # Accel/decel indicator
        if status & STATUS_ACCEL:
            canvas.itemconfigure(items["status_accel"], text="\u25B2 ACCEL", fill=ACCENT_GOLD)
        elif status & STATUS_DECEL:
            canvas.itemconfigure(items["status_accel"], text="\u25BC DECEL", fill=ACCENT_PEACH)
        else:
            canvas.itemconfigure(items["status_accel"], text="")

    def update_leds(self, running: bool, rtu_active: bool, tcp_active: bool,
                    alarm_status: int, current_values: dict[int, float] | None = None):
        """Update LED indicators — adapts to device type."""
        if self._device_name == "MK-VFD7 Motor Drive":
            self._update_leds_vfd(running, current_values or {})
        else:
            self._update_leds_em(running, rtu_active, tcp_active, alarm_status)

    def _update_leds_em(self, running, rtu_active, tcp_active, alarm_status):
        """Energy monitor LED logic."""
        if running:
            self.leds.get("PWR", LEDIndicator(self, "")).set_on(ACCENT_GREEN)
            self.leds.get("COM", LEDIndicator(self, "")).set_on(BRAND_BLUE_LIGHT)
        else:
            for name in ("PWR", "COM"):
                if name in self.leds: self.leds[name].set_off()
        if rtu_active:
            if "RTU" in self.leds: self.leds["RTU"].set_on(ACCENT_PEACH)
        else:
            if "RTU" in self.leds: self.leds["RTU"].set_off()
        if tcp_active:
            if "TCP" in self.leds: self.leds["TCP"].set_on(ACCENT_LIME)
        else:
            if "TCP" in self.leds: self.leds["TCP"].set_off()
        if alarm_status > 0:
            if "ALM" in self.leds: self.leds["ALM"].set_on(ACCENT_RED)
        else:
            if "ALM" in self.leds: self.leds["ALM"].set_off()

    def _update_leds_vfd(self, running, cv):
        """Motor drive LED logic."""
        from modbusdevicesim.devices.motor_drive import (
            STATUS_RUNNING, STATUS_FORWARD, STATUS_REVERSE, STATUS_FAULT,
        )
        status = int(cv.get(26, 0))
        fault = int(cv.get(27, 0))
        if running:
            if "PWR" in self.leds: self.leds["PWR"].set_on(ACCENT_GREEN)
        else:
            if "PWR" in self.leds: self.leds["PWR"].set_off()
        if status & STATUS_RUNNING:
            if "RUN" in self.leds: self.leds["RUN"].set_on(ACCENT_LIME)
        else:
            if "RUN" in self.leds: self.leds["RUN"].set_off()
        if fault > 0:
            if "FLT" in self.leds: self.leds["FLT"].set_on(ACCENT_RED)
        else:
            if "FLT" in self.leds: self.leds["FLT"].set_off()
        if status & STATUS_FORWARD:
            if "FWD" in self.leds: self.leds["FWD"].set_on(BRAND_BLUE_LIGHT)
        else:
            if "FWD" in self.leds: self.leds["FWD"].set_off()
        if status & STATUS_REVERSE:
            if "REV" in self.leds: self.leds["REV"].set_on(ACCENT_PEACH)
        else:
            if "REV" in self.leds: self.leds["REV"].set_off()
        if self._local_mode:
            if "LOC" in self.leds: self.leds["LOC"].set_on(ACCENT_GOLD)
        else:
            if "LOC" in self.leds: self.leds["LOC"].set_off()


# ═════════════════════════════════════════════════════════════════════
# Main Application Window
# ═════════════════════════════════════════════════════════════════════

class ModbusDeviceGUI(ctk.CTk):
    """Main application window with tabbed interface."""

    def __init__(self):
        super().__init__()

        # ── Window setup ─────────────────────────────────────────────
        self.title("Mekatronik ModbusDeviceSIM")
        self.geometry("1080x820")
        self.minsize(960, 720)
        self.configure(fg_color=BG_DARK)

        # Set icon if available
        ico_path = BRAND_DIR / "Marca-Completa-Mekatronik-Colorido.png"
        if ico_path.exists():
            self.iconbitmap(default="")

        # ── State ────────────────────────────────────────────────────
        self.device: DeviceModel | None = None
        self.engine: SimulationEngine | None = None
        self.slave_context: ModbusDeviceContext | None = None
        self.rtu_server: RTUServer | None = None
        self.tcp_server: TCPServer | None = None
        self._running = False
        self._async_loop: asyncio.AbstractEventLoop | None = None
        self._async_thread: threading.Thread | None = None
        self.register_rows: list[RegisterRow] = []
        self.device_panel: DevicePanel | None = None

        # ── Build UI ────────────────────────────────────────────────
        self._build_header()
        self._build_main_area()
        self._build_status_bar()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Header ───────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG_PANEL, height=80, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Logo
        if LOGO_PATH.exists():
            try:
                logo_img = ctk.CTkImage(
                    light_image=Image.open(LOGO_PATH),
                    dark_image=Image.open(LOGO_PATH),
                    size=(220, 52),
                )
                logo_label = ctk.CTkLabel(header, image=logo_img, text="")
                logo_label.pack(side="left", padx=20, pady=14)
            except Exception:
                ctk.CTkLabel(
                    header, text="MEKATRONIK", font=("Segoe UI Bold", 24),
                    text_color=BRAND_BLUE,
                ).pack(side="left", padx=20, pady=14)
        else:
            ctk.CTkLabel(
                header, text="MEKATRONIK", font=("Segoe UI Bold", 24),
                text_color=BRAND_BLUE,
            ).pack(side="left", padx=20, pady=14)

        # App title (right side)
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="right", padx=20, pady=10)
        ctk.CTkLabel(
            title_frame, text="ModbusDeviceSIM",
            font=("Segoe UI Semibold", 18), text_color=TEXT_PRIMARY,
        ).pack(anchor="e")
        ctk.CTkLabel(
            title_frame, text="Virtual Modbus Device Simulator",
            font=("Segoe UI", 11), text_color=TEXT_SECONDARY,
        ).pack(anchor="e")

    # ── Main area (config panel + tabbed view) ────────────────────────
    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=8)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self._build_config_panel(main)
        self._build_tabbed_view(main)

    # ── Config panel (left — shared by both tabs) ─────────────────────
    def _build_config_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_PANEL, width=280, corner_radius=10)
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        panel.grid_propagate(False)

        # Scrollable inner container so START button is always reachable
        inner = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", width=260,
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=BRAND_BLUE,
        )
        inner.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Device section ───────────────────────────────────────────
        SectionHeader(inner, "DEVICE").pack(fill="x", padx=8, pady=(12, 6))

        device_frame = ctk.CTkFrame(inner, fg_color=BG_CARD, corner_radius=8)
        device_frame.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(device_frame, text="Device Type", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 0))
        self.device_combo = ctk.CTkComboBox(
            device_frame, values=list(DEVICE_REGISTRY.keys()),
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            button_color=BRAND_BLUE, button_hover_color=BRAND_BLUE_HOVER,
            dropdown_fg_color=BG_CARD, dropdown_hover_color=BRAND_BLUE,
            text_color=TEXT_PRIMARY, font=("Segoe UI", 12), width=240,
            command=self._on_device_changed,
        )
        self.device_combo.pack(padx=12, pady=4)

        ctk.CTkLabel(device_frame, text="Slave ID", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8, 0))
        self.slave_id_entry = ctk.CTkEntry(
            device_frame, placeholder_text="1",
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, font=("Consolas", 13), width=80,
        )
        self.slave_id_entry.insert(0, "1")
        self.slave_id_entry.pack(anchor="w", padx=12, pady=(4, 12))

        # ── RTU section ──────────────────────────────────────────────
        SectionHeader(inner, "MODBUS RTU (SERIAL)", color="#6B4226").pack(fill="x", padx=8, pady=(12, 6))

        rtu_frame = ctk.CTkFrame(inner, fg_color=BG_CARD, corner_radius=8)
        rtu_frame.pack(fill="x", padx=8, pady=4)

        self.rtu_enabled = ctk.CTkSwitch(
            rtu_frame, text="Enable RTU", font=("Segoe UI", 12),
            text_color=TEXT_PRIMARY, fg_color=TEXT_DIM,
            progress_color=ACCENT_PEACH, button_color=TEXT_PRIMARY,
        )
        self.rtu_enabled.pack(anchor="w", padx=12, pady=(8, 4))

        ctk.CTkLabel(rtu_frame, text="Serial Port", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(4, 0))
        self.rtu_port_entry = ctk.CTkEntry(
            rtu_frame, placeholder_text="COM10",
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, font=("Consolas", 13), width=120,
        )
        self.rtu_port_entry.pack(anchor="w", padx=12, pady=4)

        ctk.CTkLabel(rtu_frame, text="Baud Rate", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(4, 0))
        self.rtu_baud_combo = ctk.CTkComboBox(
            rtu_frame, values=["9600", "19200", "38400", "57600", "115200"],
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            button_color=BRAND_BLUE, button_hover_color=BRAND_BLUE_HOVER,
            dropdown_fg_color=BG_CARD, dropdown_hover_color=BRAND_BLUE,
            text_color=TEXT_PRIMARY, font=("Consolas", 12), width=120,
        )
        self.rtu_baud_combo.set("9600")
        self.rtu_baud_combo.pack(anchor="w", padx=12, pady=(4, 12))

        # ── TCP section ──────────────────────────────────────────────
        SectionHeader(inner, "MODBUS TCP (ETHERNET)", color="#2D5F2D").pack(fill="x", padx=8, pady=(12, 6))

        tcp_frame = ctk.CTkFrame(inner, fg_color=BG_CARD, corner_radius=8)
        tcp_frame.pack(fill="x", padx=8, pady=4)

        self.tcp_enabled = ctk.CTkSwitch(
            tcp_frame, text="Enable TCP", font=("Segoe UI", 12),
            text_color=TEXT_PRIMARY, fg_color=TEXT_DIM,
            progress_color=ACCENT_LIME, button_color=TEXT_PRIMARY,
        )
        self.tcp_enabled.select()  # TCP on by default
        self.tcp_enabled.pack(anchor="w", padx=12, pady=(8, 4))

        ctk.CTkLabel(tcp_frame, text="Host", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(4, 0))
        self.tcp_host_entry = ctk.CTkEntry(
            tcp_frame, placeholder_text="0.0.0.0",
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, font=("Consolas", 13), width=160,
        )
        self.tcp_host_entry.insert(0, "0.0.0.0")
        self.tcp_host_entry.pack(anchor="w", padx=12, pady=4)

        ctk.CTkLabel(tcp_frame, text="Port", font=("Segoe UI", 11),
                      text_color=TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(4, 0))
        self.tcp_port_entry = ctk.CTkEntry(
            tcp_frame, placeholder_text="502",
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, font=("Consolas", 13), width=80,
        )
        self.tcp_port_entry.insert(0, "502")
        self.tcp_port_entry.pack(anchor="w", padx=12, pady=(4, 12))

        # ── Start / Stop button ──────────────────────────────────────
        self.start_btn = ctk.CTkButton(
            inner, text="\u25B6  START SIMULATOR", font=("Segoe UI Semibold", 14),
            fg_color=BRAND_BLUE, hover_color=BRAND_BLUE_HOVER,
            text_color=TEXT_PRIMARY, height=44, corner_radius=8,
            command=self._toggle_simulation,
        )
        self.start_btn.pack(fill="x", padx=8, pady=(16, 8))

    # ── Tabbed view (right side) ──────────────────────────────────────
    def _build_tabbed_view(self, parent):
        self.tabview = ctk.CTkTabview(
            parent, fg_color=BG_PANEL, corner_radius=10,
            segmented_button_fg_color=BG_CARD,
            segmented_button_selected_color=BRAND_BLUE,
            segmented_button_selected_hover_color=BRAND_BLUE_HOVER,
            segmented_button_unselected_color=BG_CARD,
            segmented_button_unselected_hover_color=BORDER_COLOR,
        )
        self.tabview.grid(row=0, column=1, sticky="nsew")

        # Create tabs
        tab_register = self.tabview.add("Register View")
        tab_device = self.tabview.add("Device Panel")

        # Configure tab backgrounds
        tab_register.configure(fg_color=BG_PANEL)
        tab_device.configure(fg_color=BG_DARK)

        # Build tab contents
        self._build_register_tab(tab_register)
        self._build_device_tab(tab_device)

    # ── Tab 1: Register View ──────────────────────────────────────────
    def _build_register_tab(self, parent):
        # Title bar
        title_bar = ctk.CTkFrame(parent, fg_color=BG_CARD, height=40, corner_radius=0)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(
            title_bar, text="  REGISTER VALUES", font=("Segoe UI Semibold", 13),
            text_color=BRAND_BLUE_LIGHT,
        ).pack(side="left", padx=8, pady=4)

        self.status_indicator = ctk.CTkLabel(
            title_bar, text="\u25CF STOPPED", font=("Segoe UI Semibold", 12),
            text_color=ACCENT_RED,
        )
        self.status_indicator.pack(side="right", padx=12, pady=4)

        # Column headers
        header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=28)
        header_frame.pack(fill="x", padx=4, pady=(4, 0))
        header_frame.grid_columnconfigure(1, weight=1)

        for col, (text, width, anchor) in enumerate([
            ("Addr", 50, "e"), ("Parameter", 200, "w"),
            ("Value", 90, "e"), ("Unit", 50, "w"),
        ]):
            ctk.CTkLabel(
                header_frame, text=text, width=width,
                anchor=anchor, font=("Segoe UI Semibold", 11), text_color=TEXT_DIM,
            ).grid(row=0, column=col, padx=4 if col != 1 else 0, sticky="ew" if col == 1 else anchor)

        # Separator
        ctk.CTkFrame(parent, fg_color=BORDER_COLOR, height=1).pack(fill="x", padx=8, pady=2)

        # Scrollable register list
        self.register_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=BRAND_BLUE,
        )
        self.register_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Populate with register rows
        self._populate_register_rows()

    def _populate_register_rows(self):
        """Create register rows for the selected device."""
        device_name = self.device_combo.get()
        device_cls = DEVICE_REGISTRY.get(device_name, list(DEVICE_REGISTRY.values())[0])
        device = device_cls(slave_id=1)
        self.register_rows.clear()

        for widget in self.register_scroll.winfo_children():
            widget.destroy()

        for i, reg in enumerate(device.registers):
            val = device.current_values.get(reg.address, 0.0)
            val_str = f"{val:.2f}" if isinstance(val, float) and val != int(val) else str(int(val))

            # Add section separator for config registers
            if reg.address == 100 and i > 0:
                sep = ctk.CTkFrame(self.register_scroll, fg_color=ACCENT_LIME, height=2)
                sep.pack(fill="x", padx=8, pady=6)
                lbl = ctk.CTkLabel(
                    self.register_scroll, text="  CONFIGURATION (Read/Write)",
                    font=("Segoe UI Semibold", 11), text_color=ACCENT_LIME, anchor="w",
                )
                lbl.pack(fill="x", padx=8, pady=(0, 4))

            row = RegisterRow(
                self.register_scroll,
                address=str(reg.address),
                name=reg.name,
                value=val_str,
                unit=reg.unit,
                writable=reg.writable,
            )
            row.pack(fill="x", pady=1)

            # Alternating row background — config registers get a green tint
            if reg.writable:
                row.configure(fg_color="#0F2218" if i % 2 == 0 else "transparent")
            elif i % 2 == 0:
                row.configure(fg_color=BG_CARD)

            self.register_rows.append(row)

    # ── Tab 2: Device Panel ───────────────────────────────────────────
    def _build_device_tab(self, parent):
        self._device_tab = parent
        device_name = self.device_combo.get()
        self.device_panel = DevicePanel(
            parent, device_name=device_name,
            write_callback=self._write_register,
        )
        self.device_panel.pack(fill="both", expand=True, padx=8, pady=8)

    def _on_device_changed(self, _value=None):
        """Rebuild register view and device panel when device selection changes."""
        if self._running:
            return  # don't change while running
        self._populate_register_rows()
        # Rebuild device panel
        if self.device_panel:
            self.device_panel.destroy()
        device_name = self.device_combo.get()
        self.device_panel = DevicePanel(
            self._device_tab, device_name=device_name,
            write_callback=self._write_register,
        )
        self.device_panel.pack(fill="both", expand=True, padx=8, pady=8)

    # ── Status bar ───────────────────────────────────────────────────
    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, fg_color=BG_PANEL, height=32, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.rtu_status = ctk.CTkLabel(
            bar, text="RTU: OFF", font=("Consolas", 11), text_color=TEXT_DIM,
        )
        self.rtu_status.pack(side="left", padx=12)

        self.tcp_status = ctk.CTkLabel(
            bar, text="TCP: OFF", font=("Consolas", 11), text_color=TEXT_DIM,
        )
        self.tcp_status.pack(side="left", padx=12)

        ctk.CTkLabel(
            bar, text="Mekatronik \u2014 Advanced Engineering",
            font=("Segoe UI", 10), text_color=TEXT_DIM,
        ).pack(side="right", padx=12)

    # ── Simulation control ───────────────────────────────────────────
    def _toggle_simulation(self):
        if self._running:
            self._stop_simulation()
        else:
            self._start_simulation()

    def _start_simulation(self):
        """Start the Modbus servers and simulation engine."""
        try:
            slave_id = int(self.slave_id_entry.get() or "1")
        except ValueError:
            slave_id = 1

        rtu_enabled = self.rtu_enabled.get()
        tcp_enabled = self.tcp_enabled.get()

        if not rtu_enabled and not tcp_enabled:
            self.status_indicator.configure(text="\u25CF NO TRANSPORT", text_color=ACCENT_GOLD)
            return

        rtu_port = self.rtu_port_entry.get() or None
        rtu_baudrate = int(self.rtu_baud_combo.get() or "9600")
        tcp_host = self.tcp_host_entry.get() or "0.0.0.0"
        try:
            tcp_port = int(self.tcp_port_entry.get() or "502")
        except ValueError:
            tcp_port = 502

        # Create device and engine based on selection
        device_name = self.device_combo.get()
        device_cls = DEVICE_REGISTRY.get(device_name, list(DEVICE_REGISTRY.values())[0])
        self.device = device_cls(slave_id=slave_id)

        if device_name == "MK-VFD7 Motor Drive":
            self.engine = MotorDriveEngine(self.device, MotorDriveSimConfig())
        else:
            self.engine = SimulationEngine(self.device, SimulationConfig())
        self.slave_context = self.device.create_slave_context()

        # Start async loop in background thread
        self._async_loop = asyncio.new_event_loop()
        self._async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._async_thread.start()

        # Start servers
        rtu_active = False
        tcp_active = False

        if rtu_enabled and rtu_port:
            self.rtu_server = RTUServer(
                context=self.slave_context, slave_id=slave_id,
                port=rtu_port, baudrate=rtu_baudrate,
            )
            asyncio.run_coroutine_threadsafe(self.rtu_server.start(), self._async_loop)
            self.rtu_status.configure(text=f"RTU: {rtu_port} ({rtu_baudrate})", text_color=ACCENT_PEACH)
            rtu_active = True
        else:
            self.rtu_status.configure(text="RTU: OFF", text_color=TEXT_DIM)

        if tcp_enabled:
            self.tcp_server = TCPServer(
                context=self.slave_context, slave_id=slave_id,
                host=tcp_host, port=tcp_port,
            )
            asyncio.run_coroutine_threadsafe(self.tcp_server.start(), self._async_loop)
            self.tcp_status.configure(text=f"TCP: {tcp_host}:{tcp_port}", text_color=ACCENT_LIME)
            tcp_active = True
        else:
            self.tcp_status.configure(text="TCP: OFF", text_color=TEXT_DIM)

        # Update UI state
        self._running = True
        self._rtu_active = rtu_active
        self._tcp_active = tcp_active
        self.start_btn.configure(
            text="\u25A0  STOP SIMULATOR",
            fg_color=ACCENT_RED, hover_color="#DC2626",
        )
        self.status_indicator.configure(text="\u25CF RUNNING", text_color=ACCENT_GREEN)

        # Disable config inputs
        self._set_config_state("disabled")

        # Start simulation update loop
        self._update_simulation()

    def _stop_simulation(self):
        """Stop the Modbus servers and simulation."""
        self._running = False

        # Stop servers
        if self._async_loop:
            if self.rtu_server:
                asyncio.run_coroutine_threadsafe(self.rtu_server.stop(), self._async_loop)
                self.rtu_server = None
            if self.tcp_server:
                asyncio.run_coroutine_threadsafe(self.tcp_server.stop(), self._async_loop)
                self.tcp_server = None

            # Stop the event loop
            self._async_loop.call_soon_threadsafe(self._async_loop.stop)
            self._async_loop = None

        # Update UI
        self.start_btn.configure(
            text="\u25B6  START SIMULATOR",
            fg_color=BRAND_BLUE, hover_color=BRAND_BLUE_HOVER,
        )
        self.status_indicator.configure(text="\u25CF STOPPED", text_color=ACCENT_RED)
        self.rtu_status.configure(text="RTU: OFF", text_color=TEXT_DIM)
        self.tcp_status.configure(text="TCP: OFF", text_color=TEXT_DIM)

        # Update device panel LEDs
        if self.device_panel:
            self.device_panel.update_leds(False, False, False, 0)

        # Re-enable config inputs
        self._set_config_state("normal")

    def _set_config_state(self, state: str):
        """Enable/disable config inputs."""
        for widget in [
            self.slave_id_entry, self.rtu_port_entry, self.rtu_baud_combo,
            self.tcp_host_entry, self.tcp_port_entry,
        ]:
            widget.configure(state=state)

    def _run_async_loop(self):
        """Run the asyncio event loop in a background thread."""
        asyncio.set_event_loop(self._async_loop)
        self._async_loop.run_forever()

    def _write_register(self, address: int, value: float):
        """Write a value from the local panel into the simulation."""
        if self.device:
            self.device.current_values[address] = value

    def _update_simulation(self):
        """Update simulation values and refresh both views."""
        if not self._running or not self.engine or not self.device:
            return

        # Read config values that the master may have written
        # In LOCAL mode, skip so local commands aren't overridden
        if self.device_panel and self.device_panel.is_local_mode:
            pass  # local controls write directly to device.current_values
        else:
            self.engine.read_config_from_context(self.slave_context)

        # Advance simulation
        self.engine.update()
        self.device.update_slave_context(self.slave_context)

        # Update register view
        reg_info = self.device.get_register_info()
        for i, info in enumerate(reg_info):
            if i < len(self.register_rows):
                val = info["value"]
                val_str = f"{val:.2f}" if isinstance(val, float) and val != int(val) else str(int(val))
                self.register_rows[i].update_value(val_str)

        # Update device panel
        if self.device_panel:
            self.device_panel.update_values(self.device.current_values)
            alarm_status = int(self.device.current_values.get(90, 0))
            self.device_panel.update_leds(
                self._running,
                getattr(self, '_rtu_active', False),
                getattr(self, '_tcp_active', False),
                alarm_status,
                current_values=self.device.current_values,
            )

        # Schedule next update
        if self._running:
            self.after(1000, self._update_simulation)

    def _on_close(self):
        """Handle window close."""
        if self._running:
            self._stop_simulation()
        self.destroy()


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ModbusDeviceGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
