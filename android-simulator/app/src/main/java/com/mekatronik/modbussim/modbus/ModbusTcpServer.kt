package com.mekatronik.modbussim.modbus

import kotlinx.coroutines.*
import java.io.DataInputStream
import java.io.DataOutputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.CopyOnWriteArrayList

/**
 * Modbus TCP Server — runs on Android as a device simulator.
 *
 * Listens for incoming Modbus TCP connections and responds to:
 *   FC03 — Read Holding Registers
 *   FC04 — Read Input Registers
 *   FC06 — Write Single Register
 *   FC16 — Write Multiple Registers
 *
 * Thread-safe register access via synchronized blocks.
 */
class ModbusTcpServer(
    private val deviceId: Int = 1,
    private val port: Int = 502,
) {
    // Register storage: 0..122 covers both measurement and config blocks
    private val registerSize = 123
    private val holdingRegisters = IntArray(registerSize)
    private val inputRegisters = IntArray(registerSize)
    private val registerLock = Any()

    private var serverSocket: ServerSocket? = null
    private var serverJob: Job? = null
    private val clientJobs = CopyOnWriteArrayList<Job>()

    var isRunning: Boolean = false
        private set

    var connectedClients: Int = 0
        private set

    var onClientCountChanged: ((Int) -> Unit)? = null
    var onRegisterWritten: ((address: Int, value: Int) -> Unit)? = null

    fun start(scope: CoroutineScope) {
        if (isRunning) return
        serverJob = scope.launch(Dispatchers.IO) {
            try {
                val ss = ServerSocket(port, 5, InetAddress.getByName("0.0.0.0"))
                serverSocket = ss
                isRunning = true

                while (isActive) {
                    val client = ss.accept()
                    client.soTimeout = 30000
                    val job = launch { handleClient(client) }
                    clientJobs.add(job)
                    job.invokeOnCompletion { clientJobs.remove(job) }
                }
            } catch (_: Exception) {
                // Server socket closed
            } finally {
                isRunning = false
            }
        }
    }

    fun stop() {
        clientJobs.forEach { it.cancel() }
        clientJobs.clear()
        try { serverSocket?.close() } catch (_: Exception) {}
        serverSocket = null
        serverJob?.cancel()
        serverJob = null
        isRunning = false
        connectedClients = 0
        onClientCountChanged?.invoke(0)
    }

    /** Write simulation values into holding and input registers. */
    fun setRegister(address: Int, value: Int, holdingOnly: Boolean = false) {
        synchronized(registerLock) {
            if (address in 0 until registerSize) {
                holdingRegisters[address] = value and 0xFFFF
                if (!holdingOnly) {
                    inputRegisters[address] = value and 0xFFFF
                }
            }
        }
    }

    /** Read a register value from holding registers (for config read-back). */
    fun getHoldingRegister(address: Int): Int {
        synchronized(registerLock) {
            return if (address in 0 until registerSize) holdingRegisters[address] else 0
        }
    }

    /** Write a FLOAT32 value (2 registers). */
    fun setFloat32(address: Int, value: Float, holdingOnly: Boolean = false) {
        val (hi, lo) = encodeFloat32(value)
        setRegister(address, hi, holdingOnly)
        setRegister(address + 1, lo, holdingOnly)
    }

    /** Write a UINT32 value (2 registers). */
    fun setUint32(address: Int, value: Long, holdingOnly: Boolean = false) {
        val (hi, lo) = encodeUint32(value)
        setRegister(address, hi, holdingOnly)
        setRegister(address + 1, lo, holdingOnly)
    }

    // ── Client handling ──────────────────────────────────────────────

    private suspend fun handleClient(socket: Socket) {
        connectedClients++
        onClientCountChanged?.invoke(connectedClients)
        try {
            val input = DataInputStream(socket.getInputStream())
            val output = DataOutputStream(socket.getOutputStream())

            while (currentCoroutineContext().isActive && !socket.isClosed) {
                // Read MBAP header (7 bytes)
                val mbap = ByteArray(7)
                try {
                    input.readFully(mbap)
                } catch (_: Exception) {
                    break
                }

                val txIdHi = mbap[0].toInt() and 0xFF
                val txIdLo = mbap[1].toInt() and 0xFF
                val length = ((mbap[4].toInt() and 0xFF) shl 8) or (mbap[5].toInt() and 0xFF)
                val unitId = mbap[6].toInt() and 0xFF

                val pduSize = length - 1
                if (pduSize <= 0 || pduSize > 260) break

                val pdu = ByteArray(pduSize)
                input.readFully(pdu)

                val functionCode = pdu[0].toInt() and 0xFF
                val response = processRequest(unitId, functionCode, pdu)

                // Build response MBAP + PDU
                val respLength = response.size + 1
                val respMbap = ByteArray(7)
                respMbap[0] = txIdHi.toByte()
                respMbap[1] = txIdLo.toByte()
                respMbap[2] = 0
                respMbap[3] = 0
                respMbap[4] = ((respLength shr 8) and 0xFF).toByte()
                respMbap[5] = (respLength and 0xFF).toByte()
                respMbap[6] = unitId.toByte()

                output.write(respMbap)
                output.write(response)
                output.flush()
            }
        } catch (_: Exception) {
            // Client disconnected
        } finally {
            try { socket.close() } catch (_: Exception) {}
            connectedClients--
            onClientCountChanged?.invoke(connectedClients)
        }
    }

    private fun processRequest(unitId: Int, fc: Int, pdu: ByteArray): ByteArray {
        return when (fc) {
            0x03 -> handleReadRegisters(fc, pdu, holdingRegisters)
            0x04 -> handleReadRegisters(fc, pdu, inputRegisters)
            0x06 -> handleWriteSingleRegister(pdu)
            0x10 -> handleWriteMultipleRegisters(pdu)
            else -> byteArrayOf((fc or 0x80).toByte(), 0x01) // Illegal function
        }
    }

    private fun handleReadRegisters(fc: Int, pdu: ByteArray, registers: IntArray): ByteArray {
        if (pdu.size < 5) return byteArrayOf((fc or 0x80).toByte(), 0x03)

        val startAddr = ((pdu[1].toInt() and 0xFF) shl 8) or (pdu[2].toInt() and 0xFF)
        val quantity = ((pdu[3].toInt() and 0xFF) shl 8) or (pdu[4].toInt() and 0xFF)

        if (quantity < 1 || quantity > 125) {
            return byteArrayOf((fc or 0x80).toByte(), 0x03) // Illegal data value
        }
        if (startAddr + quantity > registerSize) {
            return byteArrayOf((fc or 0x80).toByte(), 0x02) // Illegal data address
        }

        val byteCount = quantity * 2
        val response = ByteArray(2 + byteCount)
        response[0] = fc.toByte()
        response[1] = byteCount.toByte()

        synchronized(registerLock) {
            for (i in 0 until quantity) {
                val value = registers[startAddr + i]
                response[2 + i * 2] = ((value shr 8) and 0xFF).toByte()
                response[2 + i * 2 + 1] = (value and 0xFF).toByte()
            }
        }
        return response
    }

    private fun handleWriteSingleRegister(pdu: ByteArray): ByteArray {
        if (pdu.size < 5) return byteArrayOf(0x86.toByte(), 0x03)

        val address = ((pdu[1].toInt() and 0xFF) shl 8) or (pdu[2].toInt() and 0xFF)
        val value = ((pdu[3].toInt() and 0xFF) shl 8) or (pdu[4].toInt() and 0xFF)

        if (address >= registerSize) {
            return byteArrayOf(0x86.toByte(), 0x02)
        }

        synchronized(registerLock) {
            holdingRegisters[address] = value and 0xFFFF
        }
        onRegisterWritten?.invoke(address, value)

        // Echo request as response (FC06 protocol)
        return pdu.copyOf(5)
    }

    private fun handleWriteMultipleRegisters(pdu: ByteArray): ByteArray {
        if (pdu.size < 6) return byteArrayOf(0x90.toByte(), 0x03)

        val startAddr = ((pdu[1].toInt() and 0xFF) shl 8) or (pdu[2].toInt() and 0xFF)
        val quantity = ((pdu[3].toInt() and 0xFF) shl 8) or (pdu[4].toInt() and 0xFF)
        val byteCount = pdu[5].toInt() and 0xFF

        if (quantity < 1 || quantity > 123 || byteCount != quantity * 2) {
            return byteArrayOf(0x90.toByte(), 0x03)
        }
        if (startAddr + quantity > registerSize || pdu.size < 6 + byteCount) {
            return byteArrayOf(0x90.toByte(), 0x02)
        }

        synchronized(registerLock) {
            for (i in 0 until quantity) {
                val hi = pdu[6 + i * 2].toInt() and 0xFF
                val lo = pdu[6 + i * 2 + 1].toInt() and 0xFF
                holdingRegisters[startAddr + i] = (hi shl 8) or lo
            }
        }

        for (i in 0 until quantity) {
            val hi = pdu[6 + i * 2].toInt() and 0xFF
            val lo = pdu[6 + i * 2 + 1].toInt() and 0xFF
            onRegisterWritten?.invoke(startAddr + i, (hi shl 8) or lo)
        }

        // Response: FC + start address + quantity
        val response = ByteArray(5)
        response[0] = 0x10.toByte()
        response[1] = pdu[1]
        response[2] = pdu[2]
        response[3] = pdu[3]
        response[4] = pdu[4]
        return response
    }
}
