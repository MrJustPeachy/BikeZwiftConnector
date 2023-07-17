import random
import time
from datetime import datetime
from bluezero import async_tools
from bluezero import adapter
from bluezero import peripheral
import RPi.GPIO as GPIO
import threading

class RevolutionCounter:
    def __init__(self):
        self.revolutions = 0

    def increment(self):
        self.revolutions += 1

    def reset(self):
        self.revolutions = 0

    def get_count(self):
        return self.revolutions

data = []
revolutions = RevolutionCounter()
latest_cycle_time = datetime.now()

GPIO.setmode(GPIO.BCM)
gpioPin = 17
GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def gpio_callback(channel):
    if GPIO.input(channel) == GPIO.LOW:
        data.append(1)
        latest_cycle_time = datetime.now()
        revolutions.increment()
        print('Data stored:', 1)

# Add event detect
GPIO.add_event_detect(gpioPin, GPIO.BOTH, callback=gpio_callback, bouncetime=200)


def calculate_force(newtonForce):
    return newtonForce

def calculate_distance(crankLength, revolutions):
    return crankLength * revolutions * 2 * 3.14

def calculate_speed(flywheelCircumference):
    if len(data) == 0:
        return 0

    totalDistance = sum(data) * flywheelCircumference
    speed = (totalDistance / len(data)) * 3600
    return speed


# Custom Service UUID for Cycling Power
CYCLING_POWER_SRVC = '1818'

# Bluetooth SIG adopted UUID for Cycling Power Measurement characteristic
CYCLING_POWER_MEASUREMENT_CHRC = '2A63'

def create_ble_buffer(flags, power, revolutions, timestamp):
    bleBuffer = bytearray(8)  # Create an 8-byte buffer

    # Populate the buffer with little-endian representations of the values
    bleBuffer[0:2] = flags.to_bytes(2, 'little')
    bleBuffer[2:4] = power.to_bytes(2, 'little')
    bleBuffer[4:6] = revolutions.to_bytes(2, 'little')
    bleBuffer[6:8] = timestamp.to_bytes(2, 'little')

    # # Populate the buffer with little-endian representations of the values
    # bleBuffer[0] = flags & 0xff
    # bleBuffer[1] = (flags >> 8) & 0xff
    # bleBuffer[2] = power & 0xff
    # bleBuffer[3] = (power >> 8) & 0xff
    # bleBuffer[4] = revolutions & 0xff
    # bleBuffer[5] = (revolutions >> 8) & 0xff
    # bleBuffer[6] = timestamp & 0xff
    # bleBuffer[7] = (timestamp >> 8) & 0xff

    return list(bleBuffer)  # Convert to list for compatibility with bluezero

def read_value():
    global power
    global speed
    flags = 0x20  # 0x20 indicates that the power is in watts
    # power = random.randrange(0, 1000)
    # revolutions = random.randrange(0, 1000)
    timestamp = random.randrange(0, 1000)

    return create_ble_buffer(flags, power, revolutions.get_count(), timestamp)

# def read_value():
#     """
#     Callback for reading power value. Returns a random power value.
#     Power is a uint16 value and is expected to be in little endian format.
#     """
#     power_value = random.randrange(0, 1000)
#     print(power_value)
#     print('read')
#     return list(power_value.to_bytes(2, byteorder='little'))

def update_value(characteristic):
    """
    Callback for updating power value and sending notifications.
    """
    new_value = read_value()
    print(new_value)
    characteristic.set_value(new_value)
    return characteristic.is_notifying

def notify_callback(notifying, characteristic):
    """
    Notification callback to start a timer event
    which calls the update callback every 2 seconds
    """
    if notifying:
        async_tools.add_timer_seconds(2, update_value, characteristic)

def calculate_power_and_speed():
    while True:
        global power
        global speed
        force = calculate_force(105.28)
        distance = calculate_distance(.145, len(data))
        power = int((force * distance) / 3)
        # power = 30
        speed = int(calculate_speed(295.16))
        data.clear()
        print('Power:', power, 'watts')
        print('Speed:', speed, 'mph')
        time.sleep(3)

# Start calculating power and speed every 3 seconds
calculation_thread = threading.Thread(target=calculate_power_and_speed)
calculation_thread.start()

def main(adapter_address):
    """
    Creation of Peripheral
    """
    cycling_power_monitor = peripheral.Peripheral(adapter_address, 
                                                  local_name='Cycling Power Monitor', 
                                                  appearance=1344)

    # Add Cycling Power service
    cycling_power_monitor.add_service(srv_id=1, 
                                      uuid=CYCLING_POWER_SRVC, 
                                      primary=True)

    # Add Cycling Power Measurement characteristic
    cycling_power_monitor.add_characteristic(srv_id=1, 
                                             chr_id=1, 
                                             uuid=CYCLING_POWER_MEASUREMENT_CHRC,
                                             value=[], 
                                             notifying=False,
                                             flags=['read', 'notify'],
                                             read_callback=read_value,
                                             write_callback=None,
                                             notify_callback=notify_callback
                                             )

    # Publish peripheral and start event loop
    cycling_power_monitor.publish()

if __name__ == '__main__':
    # Get the default adapter address and pass it to main
    main(list(adapter.Adapter.available())[0].address)