"""Simulation engine for the Motor Drive (VFD).

Simulates realistic motor drive behavior:
- Ramp-up / ramp-down following accel/decel times
- V/F curve voltage control
- Motor speed from frequency with slip simulation
- Load-dependent current and torque
- DC bus voltage with ripple
- Thermal model for drive and motor temperature
- Fault/warning detection based on thresholds
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from modbusdevicesim.devices.base import DeviceModel, DataType, decode_float32
from modbusdevicesim.devices.motor_drive import (
    STATUS_RUNNING, STATUS_FORWARD, STATUS_REVERSE, STATUS_AT_REF,
    STATUS_ACCEL, STATUS_DECEL, STATUS_FAULT, STATUS_WARNING, STATUS_JOG,
    CTRL_RUN, CTRL_REVERSE, CTRL_JOG, CTRL_FAULT_RESET, CTRL_ESTOP,
    FAULT_NONE, FAULT_OVERCURRENT, FAULT_OVERVOLTAGE, FAULT_UNDERVOLTAGE,
    FAULT_OVERTEMP_DRV, FAULT_OVERTEMP_MOT,
    WARN_NONE, WARN_HIGH_TEMP, WARN_HIGH_CURRENT, WARN_HIGH_VOLTAGE,
    RESET_MAGIC,
)


@dataclass
class MotorDriveSimConfig:
    update_interval: float = 1.0
    noise_scale: float = 0.01
    drift_speed: float = 0.1
    energy_time_factor: float = 1.0
    ambient_temp: float = 25.0      # ambient temperature °C
    thermal_time_const: float = 300  # thermal time constant (seconds)


class MotorDriveEngine:
    """Generates realistic values for a variable frequency drive."""

    def __init__(self, device: DeviceModel, config: MotorDriveSimConfig | None = None):
        self.device = device
        self.config = config or MotorDriveSimConfig()
        self._time_offset = random.uniform(0, 1000)
        self._last_update = time.time()
        self._start_time = time.time()

        # Internal state
        self._output_freq = 0.0         # current output frequency (Hz)
        self._drive_temp = self.config.ambient_temp + 10.0
        self._motor_temp = self.config.ambient_temp + 15.0
        self._energy_kwh = 0.0
        self._run_hours = 0.0
        self._fault_code = FAULT_NONE
        self._fault_latched = False     # fault stays until reset

        for reg in device.registers:
            if reg.address not in device.current_values:
                device.current_values[reg.address] = reg.default

    def _smooth_noise(self, t: float, phase: float) -> float:
        return (
            0.5 * math.sin(t * 0.7 + phase) +
            0.25 * math.sin(t * 1.3 + phase * 2.1) +
            0.15 * math.sin(t * 2.9 + phase * 0.7) +
            0.10 * math.sin(t * 5.1 + phase * 1.3)
        )

    def read_config_from_context(self, context):
        """Read writable config registers back from the Modbus context."""
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
                else:
                    vals = context.getValues(3, reg.address, 1)
                    value = float(vals[0])
                self.device.current_values[reg.address] = value
            except Exception:
                pass

        # Handle fault reset
        fault_reset = int(self.device.current_values.get(127, 0))
        if fault_reset == RESET_MAGIC:
            self._fault_code = FAULT_NONE
            self._fault_latched = False
            self.device.current_values[127] = 0.0

        # Handle energy reset
        energy_reset = int(self.device.current_values.get(128, 0))
        if energy_reset == RESET_MAGIC:
            self._energy_kwh = 0.0
            self.device.current_values[20] = 0.0
            self.device.current_values[128] = 0.0

    def update(self):
        """Advance the motor drive simulation by one tick."""
        now = time.time()
        dt = now - self._last_update
        self._last_update = now
        t = (now + self._time_offset) * self.config.drift_speed

        cv = self.device.current_values

        # ── Read control word ─────────────────────────────────────
        ctrl = int(cv.get(100, 0))
        run_cmd = bool(ctrl & CTRL_RUN) and not bool(ctrl & CTRL_ESTOP)
        reverse = bool(ctrl & CTRL_REVERSE)
        jog = bool(ctrl & CTRL_JOG)

        # Read config parameters
        freq_ref = cv.get(101, 30.0)
        accel_time = max(0.1, cv.get(103, 10.0))
        decel_time = max(0.1, cv.get(105, 10.0))
        max_freq = cv.get(107, 60.0)
        min_freq = cv.get(109, 0.5)
        motor_rated_v = cv.get(111, 380.0)
        motor_rated_i = cv.get(112, 15.0)
        motor_rated_freq = cv.get(114, 60.0)
        motor_rated_speed = cv.get(115, 1750.0)
        motor_rated_power = cv.get(116, 7.5)
        vf_pattern = int(cv.get(118, 0))

        # Clamp frequency reference
        freq_ref = max(0.0, min(max_freq, freq_ref))

        # ── Fault check (stop if faulted) ─────────────────────────
        if self._fault_latched:
            run_cmd = False

        # ── Frequency ramping ─────────────────────────────────────
        target_freq = 0.0
        if run_cmd:
            if jog:
                target_freq = min_freq * 2  # jog at 2× min freq
            else:
                target_freq = freq_ref

        ramp_rate_up = max_freq / accel_time   # Hz/s
        ramp_rate_down = max_freq / decel_time  # Hz/s

        is_accel = False
        is_decel = False

        if self._output_freq < target_freq:
            self._output_freq = min(target_freq, self._output_freq + ramp_rate_up * dt)
            is_accel = True
        elif self._output_freq > target_freq:
            self._output_freq = max(target_freq, self._output_freq - ramp_rate_down * dt)
            is_decel = True

        at_ref = abs(self._output_freq - target_freq) < 0.05

        # Clamp
        if self._output_freq < 0.1:
            self._output_freq = 0.0

        cv[0] = self._output_freq

        # ── Output Voltage (V/F curve) ────────────────────────────
        if motor_rated_freq > 0 and self._output_freq > 0:
            freq_ratio = self._output_freq / motor_rated_freq
            if vf_pattern == 0:     # Linear V/F
                v_ratio = freq_ratio
            elif vf_pattern == 1:   # Square (fan/pump)
                v_ratio = freq_ratio ** 2
            else:                   # Custom — similar to linear with boost
                v_ratio = 0.05 + 0.95 * freq_ratio
            output_voltage = min(motor_rated_v, motor_rated_v * v_ratio)
        else:
            output_voltage = 0.0

        # Add small noise
        output_voltage += self._smooth_noise(t, 1.0) * 0.5
        cv[2] = max(0.0, output_voltage)

        # ── Motor Speed (frequency → RPM with slip) ──────────────
        if self._output_freq > 0 and motor_rated_freq > 0:
            # Synchronous speed at current frequency
            sync_speed = motor_rated_speed * (motor_rated_freq / (motor_rated_freq - (motor_rated_freq - motor_rated_speed * motor_rated_freq / (motor_rated_speed if motor_rated_speed > 0 else 1))))
            # Simplified: RPM ≈ rated_speed × (output_freq / rated_freq) with slip noise
            speed = motor_rated_speed * (self._output_freq / motor_rated_freq)
            # Add slip variation (1-3% of sync speed)
            slip_noise = self._smooth_noise(t * 0.3, 5.0) * speed * 0.015
            speed = max(0, speed - abs(slip_noise))
        else:
            speed = 0.0
        cv[8] = speed

        # ── Load simulation (sinusoidal load variation) ───────────
        base_load = 0.6  # 60% of rated load as baseline
        load_variation = self._smooth_noise(t * 0.2, 3.0) * 0.15
        load_factor = base_load + load_variation  # 0.45 to 0.75 of rated

        # ── Output Current ────────────────────────────────────────
        if self._output_freq > 0:
            # Current proportional to load, with magnetizing component
            mag_current = motor_rated_i * 0.3  # magnetizing current ≈ 30% rated
            load_current = motor_rated_i * load_factor * (self._output_freq / motor_rated_freq)
            output_current = math.sqrt(mag_current ** 2 + load_current ** 2)
            output_current += self._smooth_noise(t, 2.0) * 0.2
            output_current = max(0, output_current)
        else:
            output_current = 0.0
        cv[4] = output_current

        # ── Output Power ──────────────────────────────────────────
        if self._output_freq > 0:
            output_power = output_voltage * output_current * math.sqrt(3) / 1000.0
            output_power *= 0.95  # approximate power factor
        else:
            output_power = 0.0
        cv[6] = max(0, output_power)

        # ── Motor Torque (%) ──────────────────────────────────────
        if self._output_freq > 0 and motor_rated_power > 0:
            # Torque = Power / Speed, normalized to rated
            rated_torque_nm = motor_rated_power * 1000 / (motor_rated_speed * 2 * math.pi / 60) if motor_rated_speed > 0 else 1
            actual_torque_nm = output_power * 1000 / (speed * 2 * math.pi / 60) if speed > 0 else 0
            torque_pct = (actual_torque_nm / rated_torque_nm) * 100 if rated_torque_nm > 0 else 0
        else:
            torque_pct = 0.0
        cv[10] = max(0, min(150, torque_pct))

        # ── DC Bus Voltage ────────────────────────────────────────
        dc_nominal = motor_rated_v * math.sqrt(2)  # ≈ 537V for 380V supply
        dc_ripple = self._smooth_noise(t * 2.0, 7.0) * 3.0
        dc_bus = dc_nominal + dc_ripple
        cv[12] = max(0, dc_bus)

        # ── Temperature simulation (first-order thermal model) ───
        # Drive temp: rises with current^2, cools toward ambient
        drive_heat = (output_current / motor_rated_i) ** 2 * 40.0  # max 40°C rise
        drive_target = self.config.ambient_temp + 10.0 + drive_heat
        tau = self.config.thermal_time_const
        alpha = dt / (tau + dt)
        self._drive_temp += alpha * (drive_target - self._drive_temp)
        self._drive_temp += self._smooth_noise(t * 0.1, 8.0) * 0.2
        cv[14] = self._drive_temp

        # Motor temp: rises more slowly, higher base
        motor_heat = (output_current / motor_rated_i) ** 2 * 55.0  # max 55°C rise
        motor_target = self.config.ambient_temp + 15.0 + motor_heat
        self._motor_temp += alpha * (motor_target - self._motor_temp)
        self._motor_temp += self._smooth_noise(t * 0.08, 9.0) * 0.3
        cv[16] = self._motor_temp

        # ── Run Time ──────────────────────────────────────────────
        if self._output_freq > 0:
            self._run_hours += dt / 3600.0
        cv[18] = int(self._run_hours)

        # ── Energy ────────────────────────────────────────────────
        self._energy_kwh += output_power * (dt / 3600.0) * self.config.energy_time_factor
        cv[20] = int(self._energy_kwh)

        # ── Power Factor ──────────────────────────────────────────
        if self._output_freq > 0:
            # PF improves with load
            pf = 0.6 + load_factor * 0.35
            pf += self._smooth_noise(t * 0.15, 10.0) * 0.02
            cv[22] = max(0.0, min(1.0, pf))
        else:
            cv[22] = 0.0

        # ── Input Power ──────────────────────────────────────────
        if output_power > 0:
            cv[24] = output_power / 0.95  # drive efficiency ~95%
        else:
            cv[24] = 0.0

        # ── Fault / Warning detection ─────────────────────────────
        oc_thresh = cv.get(119, 25.0)
        ov_thresh = cv.get(121, 420.0)
        uv_thresh = cv.get(123, 320.0)
        ot_thresh = cv.get(125, 85.0)

        warning = WARN_NONE
        if not self._fault_latched:
            # Check over-current
            if output_current > oc_thresh:
                self._fault_code = FAULT_OVERCURRENT
                self._fault_latched = True
            # Check DC bus over-voltage
            elif dc_bus > ov_thresh * math.sqrt(2):
                self._fault_code = FAULT_OVERVOLTAGE
                self._fault_latched = True
            # Check DC bus under-voltage
            elif dc_bus < uv_thresh * math.sqrt(2) * 0.9 and self._output_freq > 0:
                self._fault_code = FAULT_UNDERVOLTAGE
                self._fault_latched = True
            # Check drive over-temperature
            elif self._drive_temp > ot_thresh:
                self._fault_code = FAULT_OVERTEMP_DRV
                self._fault_latched = True
            # Check motor over-temperature
            elif self._motor_temp > ot_thresh + 15:
                self._fault_code = FAULT_OVERTEMP_MOT
                self._fault_latched = True

        # Warnings (non-latching)
        if self._drive_temp > ot_thresh * 0.85:
            warning = WARN_HIGH_TEMP
        elif output_current > oc_thresh * 0.85:
            warning = WARN_HIGH_CURRENT
        elif dc_bus > ov_thresh * math.sqrt(2) * 0.9:
            warning = WARN_HIGH_VOLTAGE

        cv[27] = float(self._fault_code)
        cv[28] = float(warning)

        # ── Drive Status Word ─────────────────────────────────────
        status = 0
        if self._output_freq > 0:
            status |= STATUS_RUNNING
            if reverse:
                status |= STATUS_REVERSE
            else:
                status |= STATUS_FORWARD
            if at_ref:
                status |= STATUS_AT_REF
            if is_accel:
                status |= STATUS_ACCEL
            if is_decel:
                status |= STATUS_DECEL
            if jog:
                status |= STATUS_JOG

        if self._fault_latched:
            status |= STATUS_FAULT
        if warning != WARN_NONE:
            status |= STATUS_WARNING

        cv[26] = float(status)
