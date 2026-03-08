"""Simulation engine — generates realistic fluctuating values for device registers.

Uses Perlin-like smooth noise to create natural-looking sensor readings:
- Voltage drifts slowly around nominal
- Current varies with simulated load changes
- Power is computed from voltage × current × power factor
- Energy accumulators increment based on power over time
- Frequency has very small, slow drift
- THD values fluctuate gently
- Alarm status reacts to configurable thresholds
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from modbusdevicesim.devices.base import (
    DeviceModel, RegisterDefinition, DataType,
    decode_float32,
)
from modbusdevicesim.devices.energy_monitor import (
    ALARM_OVER_VOLTAGE, ALARM_UNDER_VOLTAGE, ALARM_OVER_CURRENT,
    ALARM_LOW_PF, ALARM_OVER_POWER, ALARM_PHASE_LOSS, ALARM_THD_HIGH,
    STATUS_RUNNING, STATUS_ALARM_ACTIVE,
    RESET_MAGIC,
)


@dataclass
class SimulationConfig:
    """Configuration for the simulation engine."""
    update_interval: float = 1.0    # seconds between updates
    noise_scale: float = 0.02       # base noise amplitude (fraction of range)
    drift_speed: float = 0.1        # how fast values drift (lower = slower)
    energy_time_factor: float = 1.0 # multiplier for energy accumulation speed


class SimulationEngine:
    """Generates realistic fluctuating values for a device model."""

    def __init__(self, device: DeviceModel, config: SimulationConfig | None = None):
        self.device = device
        self.config = config or SimulationConfig()
        self._time_offset = random.uniform(0, 1000)  # random phase offset
        self._phase_offsets: dict[int, float] = {}    # per-register phase
        self._last_update = time.time()
        self._start_time = time.time()
        self._energy_kwh = 0.0
        self._energy_kvarh = 0.0
        self._energy_export_kwh = 0.0
        self._energy_kvah = 0.0
        self._max_demand_power = 0.0
        self._max_demand_current = 0.0

        # Give each register its own random phase so they don't all move together
        for reg in device.registers:
            self._phase_offsets[reg.address] = random.uniform(0, 2 * math.pi)

    def _smooth_noise(self, t: float, phase: float) -> float:
        """Generate smooth noise using layered sine waves (cheap Perlin-like)."""
        return (
            0.5  * math.sin(t * 0.7 + phase) +
            0.25 * math.sin(t * 1.3 + phase * 2.1) +
            0.15 * math.sin(t * 2.9 + phase * 0.7) +
            0.10 * math.sin(t * 5.1 + phase * 1.3)
        )

    def read_config_from_context(self, context):
        """Read writable config registers back from the Modbus context.

        This allows the HMI/master to write configuration values (FC06/FC16)
        and have them take effect in the simulation.
        """
        for reg in self.device.registers:
            if not reg.writable:
                continue
            try:
                if reg.data_type == DataType.FLOAT32:
                    vals = context.getValues(3, reg.address, 2)
                    value = decode_float32(vals[0], vals[1])
                elif reg.data_type == DataType.UINT32:
                    vals = context.getValues(3, reg.address, 2)
                    value = float((vals[0] << 16) | vals[1])
                elif reg.data_type == DataType.UINT16:
                    vals = context.getValues(3, reg.address, 1)
                    value = float(vals[0])
                else:
                    vals = context.getValues(3, reg.address, 1)
                    value = float(vals[0])
                self.device.current_values[reg.address] = value
            except Exception:
                pass  # keep previous value if read fails

        # Handle reset commands
        energy_reset = int(self.device.current_values.get(118, 0))
        if energy_reset == RESET_MAGIC:
            self._energy_kwh = 0.0
            self._energy_kvarh = 0.0
            self._energy_export_kwh = 0.0
            self._energy_kvah = 0.0
            self.device.current_values[54] = 0.0
            self.device.current_values[56] = 0.0
            self.device.current_values[58] = 0.0
            self.device.current_values[60] = 0.0
            self.device.current_values[118] = 0.0  # auto-clear

        demand_reset = int(self.device.current_values.get(119, 0))
        if demand_reset == RESET_MAGIC:
            self._max_demand_power = 0.0
            self._max_demand_current = 0.0
            self.device.current_values[74] = 0.0
            self.device.current_values[76] = 0.0
            self.device.current_values[119] = 0.0  # auto-clear

    def update(self):
        """Advance the simulation by one tick, updating all register values."""
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        t = (now + self._time_offset) * self.config.drift_speed

        # ── Phase Voltages (correlated — they share a grid) ──────────
        v_base = self._smooth_noise(t, 0) * 0.3  # shared grid noise
        for addr in (0, 2, 4):  # L1-N, L2-N, L3-N
            reg = self._find_register(addr)
            if reg:
                phase = self._phase_offsets[addr]
                noise = v_base + self._smooth_noise(t, phase) * 0.15
                value = reg.default + noise * (reg.max_value - reg.min_value) * self.config.noise_scale * 10
                self.device.current_values[addr] = max(reg.min_value, min(reg.max_value, value))

        # ── Line-to-Line Voltages (derived from phase voltages × √3) ─
        v_l1 = self.device.current_values.get(0, 220.0)
        v_l2 = self.device.current_values.get(2, 220.0)
        v_l3 = self.device.current_values.get(4, 220.0)
        self.device.current_values[6]  = (v_l1 + v_l2) / 2 * math.sqrt(3) + self._smooth_noise(t, 10) * 0.5
        self.device.current_values[8]  = (v_l2 + v_l3) / 2 * math.sqrt(3) + self._smooth_noise(t, 11) * 0.5
        self.device.current_values[10] = (v_l3 + v_l1) / 2 * math.sqrt(3) + self._smooth_noise(t, 12) * 0.5

        # Clamp line-to-line voltages
        for addr in (6, 8, 10):
            reg = self._find_register(addr)
            if reg:
                self.device.current_values[addr] = max(reg.min_value, min(reg.max_value, self.device.current_values[addr]))

        # ── Current (independent per phase, larger variation) ─────────
        for addr in (12, 14, 16):
            reg = self._find_register(addr)
            if reg:
                phase = self._phase_offsets[addr]
                noise = self._smooth_noise(t * 0.5, phase)
                value = reg.default + noise * (reg.max_value - reg.min_value) * 0.3
                self.device.current_values[addr] = max(reg.min_value, min(reg.max_value, value))

        # Neutral current (small, derived from imbalance)
        i_l1 = self.device.current_values.get(12, 15.0)
        i_l2 = self.device.current_values.get(14, 15.0)
        i_l3 = self.device.current_values.get(16, 15.0)
        i_avg = (i_l1 + i_l2 + i_l3) / 3
        neutral = abs(i_l1 - i_avg) + abs(i_l2 - i_avg) + abs(i_l3 - i_avg)
        self.device.current_values[18] = max(0.0, min(5.0, neutral * 0.3))

        # ── Power Factor (slow drift near unity) ─────────────────────
        for addr in (44, 46, 48, 50):
            reg = self._find_register(addr)
            if reg:
                phase = self._phase_offsets[addr]
                noise = self._smooth_noise(t * 0.3, phase)
                value = reg.default + noise * 0.05
                self.device.current_values[addr] = max(reg.min_value, min(reg.max_value, value))

        # ── Active Power (V × I × PF / 1000) per phase ──────────────
        pf_l1 = self.device.current_values.get(44, 0.97)
        pf_l2 = self.device.current_values.get(46, 0.97)
        pf_l3 = self.device.current_values.get(48, 0.97)
        p_l1 = v_l1 * i_l1 * pf_l1 / 1000.0
        p_l2 = v_l2 * i_l2 * pf_l2 / 1000.0
        p_l3 = v_l3 * i_l3 * pf_l3 / 1000.0
        p_total = p_l1 + p_l2 + p_l3
        self.device.current_values[20] = p_l1
        self.device.current_values[22] = p_l2
        self.device.current_values[24] = p_l3
        self.device.current_values[26] = p_total

        # ── Reactive Power (V × I × sin(acos(PF)) / 1000) ───────────
        q_l1 = v_l1 * i_l1 * math.sin(math.acos(min(pf_l1, 1.0))) / 1000.0
        q_l2 = v_l2 * i_l2 * math.sin(math.acos(min(pf_l2, 1.0))) / 1000.0
        q_l3 = v_l3 * i_l3 * math.sin(math.acos(min(pf_l3, 1.0))) / 1000.0
        q_total = q_l1 + q_l2 + q_l3
        self.device.current_values[28] = q_l1
        self.device.current_values[30] = q_l2
        self.device.current_values[32] = q_l3
        self.device.current_values[34] = q_total

        # ── Apparent Power (V × I / 1000) — all phases ──────────────
        s_l1 = v_l1 * i_l1 / 1000.0
        s_l2 = v_l2 * i_l2 / 1000.0
        s_l3 = v_l3 * i_l3 / 1000.0
        s_total = s_l1 + s_l2 + s_l3
        self.device.current_values[36] = s_l1
        self.device.current_values[38] = s_l2
        self.device.current_values[40] = s_l3
        self.device.current_values[42] = s_total

        # ── Frequency (very small, slow drift) ───────────────────────
        reg_freq = self._find_register(52)
        if reg_freq:
            noise = self._smooth_noise(t * 0.2, self._phase_offsets[52])
            self.device.current_values[52] = reg_freq.default + noise * 0.05

        # ── Energy Accumulators ──────────────────────────────────────
        self._energy_kwh += p_total * (dt / 3600.0) * self.config.energy_time_factor
        self._energy_kvarh += q_total * (dt / 3600.0) * self.config.energy_time_factor
        self._energy_kvah += s_total * (dt / 3600.0) * self.config.energy_time_factor
        # Export energy: simulate small reverse flow occasionally
        export_noise = self._smooth_noise(t * 0.1, 99.0)
        if export_noise > 0.8:
            self._energy_export_kwh += 0.001 * self.config.energy_time_factor

        self.device.current_values[54] = int(self._energy_kwh)
        self.device.current_values[56] = int(self._energy_kvarh)
        self.device.current_values[58] = int(self._energy_export_kwh)
        self.device.current_values[60] = int(self._energy_kvah)

        # ── Max Demand (track peak) ──────────────────────────────────
        if p_total > self._max_demand_power:
            self._max_demand_power = p_total
        max_phase_current = max(i_l1, i_l2, i_l3)
        if max_phase_current > self._max_demand_current:
            self._max_demand_current = max_phase_current
        self.device.current_values[74] = self._max_demand_power
        self.device.current_values[76] = self._max_demand_current

        # ── Averages ─────────────────────────────────────────────────
        self.device.current_values[78] = (v_l1 + v_l2 + v_l3) / 3.0
        v_ll1 = self.device.current_values.get(6, 380.0)
        v_ll2 = self.device.current_values.get(8, 380.0)
        v_ll3 = self.device.current_values.get(10, 380.0)
        self.device.current_values[80] = (v_ll1 + v_ll2 + v_ll3) / 3.0
        self.device.current_values[82] = i_avg

        # ── Unbalance (%) ────────────────────────────────────────────
        v_avg = (v_l1 + v_l2 + v_l3) / 3.0
        if v_avg > 0:
            v_max_dev = max(abs(v_l1 - v_avg), abs(v_l2 - v_avg), abs(v_l3 - v_avg))
            self.device.current_values[84] = (v_max_dev / v_avg) * 100.0
        if i_avg > 0:
            i_max_dev = max(abs(i_l1 - i_avg), abs(i_l2 - i_avg), abs(i_l3 - i_avg))
            self.device.current_values[86] = (i_max_dev / i_avg) * 100.0

        # ── Run Hours ────────────────────────────────────────────────
        run_hours = (now - self._start_time) / 3600.0
        self.device.current_values[88] = int(run_hours)

        # ── THD values (gentle fluctuation) ──────────────────────────
        for addr in (62, 64, 66, 68, 70, 72):
            reg = self._find_register(addr)
            if reg:
                phase = self._phase_offsets[addr]
                noise = self._smooth_noise(t * 0.4, phase)
                value = reg.default + noise * (reg.max_value - reg.min_value) * 0.15
                self.device.current_values[addr] = max(reg.min_value, min(reg.max_value, value))

        # ── Alarm Evaluation ─────────────────────────────────────────
        alarm_mask = int(self.device.current_values.get(117, 0x001F))
        alarm_status = 0

        # Read thresholds from config registers
        ov_thresh = self.device.current_values.get(107, 253.0)
        uv_thresh = self.device.current_values.get(109, 198.0)
        oc_thresh = self.device.current_values.get(111, 30.0)
        pf_thresh = self.device.current_values.get(113, 0.85)
        op_thresh = self.device.current_values.get(115, 15.0)

        # Check over-voltage (any phase)
        if max(v_l1, v_l2, v_l3) > ov_thresh:
            alarm_status |= ALARM_OVER_VOLTAGE

        # Check under-voltage (any phase)
        if min(v_l1, v_l2, v_l3) < uv_thresh:
            alarm_status |= ALARM_UNDER_VOLTAGE

        # Check over-current (any phase)
        if max(i_l1, i_l2, i_l3) > oc_thresh:
            alarm_status |= ALARM_OVER_CURRENT

        # Check low power factor
        pf_total = self.device.current_values.get(50, 0.97)
        if pf_total < pf_thresh:
            alarm_status |= ALARM_LOW_PF

        # Check over-power
        if p_total > op_thresh:
            alarm_status |= ALARM_OVER_POWER

        # Check phase loss (voltage below 50V on any phase)
        if min(v_l1, v_l2, v_l3) < 50.0:
            alarm_status |= ALARM_PHASE_LOSS

        # Check high THD (any voltage THD > 8%)
        for addr in (62, 64, 66):
            if self.device.current_values.get(addr, 0) > 8.0:
                alarm_status |= ALARM_THD_HIGH

        # Apply enable mask
        alarm_status &= alarm_mask
        self.device.current_values[90] = float(alarm_status)

        # ── Device Status Word ───────────────────────────────────────
        device_status = STATUS_RUNNING
        if alarm_status > 0:
            device_status |= STATUS_ALARM_ACTIVE
        self.device.current_values[91] = float(device_status)

    def _find_register(self, address: int) -> RegisterDefinition | None:
        """Find a register definition by address."""
        for reg in self.device.registers:
            if reg.address == address:
                return reg
        return None
