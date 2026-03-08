"""Modbus TCP (Ethernet) transport server."""

from __future__ import annotations

import logging

from pymodbus.server import ModbusTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext

from modbusdevicesim.brand import console

log = logging.getLogger(__name__)


class TCPServer:
    """Modbus TCP slave server over Ethernet."""

    def __init__(
        self,
        context: ModbusDeviceContext,
        slave_id: int = 1,
        host: str = "0.0.0.0",
        port: int = 502,
    ):
        self.slave_id = slave_id
        self.host = host
        self.port = port
        self.server_context = ModbusServerContext(
            devices={slave_id: context}, single=False
        )
        self._server: ModbusTcpServer | None = None

    async def start(self):
        """Start the TCP server (blocking — run as a background task)."""
        console.print(
            f"  [transport.tcp]TCP[/transport.tcp] Starting on [value]{self.host}:{self.port}[/value]"
        )
        self._server = ModbusTcpServer(
            context=self.server_context,
            address=(self.host, self.port),
        )
        await self._server.listen()
        console.print(
            f"  [transport.tcp]TCP[/transport.tcp] [status.running]● LISTENING[/status.running] on {self.host}:{self.port}"
        )

    async def stop(self):
        """Stop the TCP server."""
        if self._server:
            await self._server.shutdown()
            console.print("  [transport.tcp]TCP[/transport.tcp] Server stopped")
