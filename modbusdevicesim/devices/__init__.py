"""Device models and registry."""

from modbusdevicesim.devices.energy_monitor import EnergyMonitor
from modbusdevicesim.devices.motor_drive import MotorDrive

# Device registry: display name -> class
DEVICE_REGISTRY = {
    "MK-EM3P Energy Monitor": EnergyMonitor,
    "MK-VFD7 Motor Drive": MotorDrive,
}
