"""Modbus RTU (serial) transport server."""

from __future__ import annotations

import logging

from pymodbus.server import ModbusSerialServer
from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext

from modbusdevicesim.brand import console

log = logging.getLogger(__name__)


class RTUServer:
    """Modbus RTU slave server over a serial port."""

    def __init__(
        self,
        context: ModbusDeviceContext,
        slave_id: int = 1,
        port: str = "COM10",
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
    ):
        self.slave_id = slave_id
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.server_context = ModbusServerContext(
            devices={slave_id: context}, single=False
        )
        self._server: ModbusSerialServer | None = None

    async def start(self):
        """Start the RTU server (blocking — run as a background task)."""
        console.print(
            f"  [transport.rtu]RTU[/transport.rtu] Starting on [value]{self.port}[/value] "
            f"({self.baudrate} {self.bytesize}{self.parity}{self.stopbits})"
        )
        self._server = ModbusSerialServer(
            context=self.server_context,
            port=self.port,
            baudrate=self.baudrate,
            bytesize=self.bytesize,
            parity=self.parity,
            stopbits=self.stopbits,
        )
        await self._server.listen()
        console.print(
            f"  [transport.rtu]RTU[/transport.rtu] [status.running]● LISTENING[/status.running] on {self.port}"
        )

    async def stop(self):
        """Stop the RTU server."""
        if self._server:
            await self._server.shutdown()
            console.print("  [transport.rtu]RTU[/transport.rtu] Server stopped")
