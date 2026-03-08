"""Base device model and register definitions."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from pymodbus.datastore import ModbusDeviceContext, ModbusSequentialDataBlock


class DataType(Enum):
    """Modbus register data types."""
    UINT16 = "uint16"      # 1 register
    INT16 = "int16"        # 1 register
    UINT32 = "uint32"      # 2 registers, big-endian word order
    INT32 = "int32"        # 2 registers, big-endian word order
    FLOAT32 = "float32"    # 2 registers, IEEE 754, big-endian word order

    @property
    def register_count(self) -> int:
        if self in (DataType.UINT16, DataType.INT16):
            return 1
        return 2


@dataclass
class RegisterDefinition:
    """Defines a single register (or register pair) in a device."""
    address: int                # 0-based register address
    name: str                   # Human-readable parameter name
    data_type: DataType         # How the value is encoded
    unit: str = ""              # Engineering unit (V, A, kW, etc.)
    default: float = 0.0        # Default/initial value
    min_value: float = 0.0      # Minimum simulation range
    max_value: float = 0.0      # Maximum simulation range
    writable: bool = False      # Whether master can write this register
    scale_factor: float = 1.0   # Multiplier applied before encoding


def encode_float32(value: float) -> tuple[int, int]:
    """Encode a float as two 16-bit registers (big-endian word order)."""
    packed = struct.pack(">f", value)
    high = struct.unpack(">H", packed[0:2])[0]
    low = struct.unpack(">H", packed[2:4])[0]
    return high, low


def decode_float32(high: int, low: int) -> float:
    """Decode two 16-bit registers back to a float (big-endian word order)."""
    packed = struct.pack(">HH", high, low)
    return struct.unpack(">f", packed)[0]


def encode_uint32(value: int) -> tuple[int, int]:
    """Encode a uint32 as two 16-bit registers (big-endian word order)."""
    high = (value >> 16) & 0xFFFF
    low = value & 0xFFFF
    return high, low


def encode_int16(value: int) -> int:
    """Encode a signed int16 as an unsigned 16-bit register value."""
    return struct.unpack(">H", struct.pack(">h", value))[0]


class DeviceModel:
    """Base class for all simulated Modbus devices.

    Subclasses define their register map and simulation behavior.
    """

    name: str = "Generic Device"
    description: str = "A generic Modbus device"
    default_slave_id: int = 1

    def __init__(self, slave_id: int | None = None):
        self.slave_id = slave_id or self.default_slave_id
        self.registers: list[RegisterDefinition] = []
        self.current_values: dict[int, float] = {}  # address -> current value
        self._define_registers()
        self._init_values()

    def _define_registers(self):
        """Override in subclass to define the register map."""
        raise NotImplementedError

    def _init_values(self):
        """Set initial values for all registers."""
        for reg in self.registers:
            self.current_values[reg.address] = reg.default

    def get_register_info(self) -> list[dict]:
        """Get current register values as a list of dicts for display."""
        result = []
        for reg in self.registers:
            result.append({
                "address": reg.address,
                "name": reg.name,
                "value": self.current_values.get(reg.address, 0.0),
                "unit": reg.unit,
                "data_type": reg.data_type.value,
            })
        return result

    def create_slave_context(self) -> ModbusDeviceContext:
        """Create a pymodbus slave context from current register values.

        Maps all registers into Holding Registers (function code 3/6/16)
        and mirrors them as Input Registers (function code 4) for read-only access.
        """
        max_addr = 0
        for reg in self.registers:
            end = reg.address + reg.data_type.register_count
            if end > max_addr:
                max_addr = end

        # Create register arrays (1-indexed internally in pymodbus)
        hr_values = [0] * (max_addr + 1)
        ir_values = [0] * (max_addr + 1)

        for reg in self.registers:
            self._write_register_to_array(hr_values, reg, self.current_values[reg.address])
            self._write_register_to_array(ir_values, reg, self.current_values[reg.address])

        return ModbusDeviceContext(
            di=ModbusSequentialDataBlock(0, [0] * 16),   # Discrete Inputs
            co=ModbusSequentialDataBlock(0, [0] * 16),   # Coils
            hr=ModbusSequentialDataBlock(0, hr_values),   # Holding Registers
            ir=ModbusSequentialDataBlock(0, ir_values),   # Input Registers
        )

    def update_slave_context(self, context: ModbusDeviceContext):
        """Write current simulation values into the slave context.

        - Read-only registers are written to both HR (FC03) and IR (FC04).
        - Writable config registers are only written to HR (FC03) so that
          values written by the master are not overwritten in IR.
        """
        for reg in self.registers:
            value = self.current_values[reg.address]
            if reg.data_type == DataType.FLOAT32:
                high, low = encode_float32(value * reg.scale_factor)
                if not reg.writable:
                    context.setValues(3, reg.address, [high, low])  # HR
                    context.setValues(4, reg.address, [high, low])  # IR
                else:
                    context.setValues(3, reg.address, [high, low])  # HR only
            elif reg.data_type == DataType.UINT32:
                high, low = encode_uint32(int(value * reg.scale_factor))
                if not reg.writable:
                    context.setValues(3, reg.address, [high, low])
                    context.setValues(4, reg.address, [high, low])
                else:
                    context.setValues(3, reg.address, [high, low])
            elif reg.data_type == DataType.INT16:
                encoded = encode_int16(int(value * reg.scale_factor))
                if not reg.writable:
                    context.setValues(3, reg.address, [encoded])
                    context.setValues(4, reg.address, [encoded])
                else:
                    context.setValues(3, reg.address, [encoded])
            else:  # UINT16
                encoded = int(value * reg.scale_factor) & 0xFFFF
                if not reg.writable:
                    context.setValues(3, reg.address, [encoded])
                    context.setValues(4, reg.address, [encoded])
                else:
                    context.setValues(3, reg.address, [encoded])

    def _write_register_to_array(self, array: list[int], reg: RegisterDefinition, value: float):
        """Write a value into a register array at the correct position."""
        if reg.data_type == DataType.FLOAT32:
            high, low = encode_float32(value * reg.scale_factor)
            array[reg.address] = high
            array[reg.address + 1] = low
        elif reg.data_type == DataType.UINT32:
            high, low = encode_uint32(int(value * reg.scale_factor))
            array[reg.address] = high
            array[reg.address + 1] = low
        elif reg.data_type == DataType.INT16:
            array[reg.address] = encode_int16(int(value * reg.scale_factor))
        else:
            array[reg.address] = int(value * reg.scale_factor) & 0xFFFF
