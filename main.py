import RPi.GPIO as GPIO
import time
import datetime
from ant.easy.node import Node

# Set GPIO mode (BCM or BOARD)
GPIO.setmode(GPIO.BCM)

# Set GPIO pins
PIN_11 = 11
PIN_13 = 13

# Set up GPIO pins as input
GPIO.setup(PIN_11, GPIO.IN)
GPIO.setup(PIN_13, GPIO.IN)

# Variables for speed calculation
wheel_circumference = 2.07  # Adjust this value according to your bike's wheel circumference
previous_time = datetime.datetime.now()
previous_count_11 = GPIO.input(PIN_11)
previous_count_13 = GPIO.input(PIN_13)
total_count = 0

# Function to handle Ant+ events
# def on_antplus_data(data):
#     # Implement your data processing logic here
#     # This function will be called whenever new data is received from the Ant+ device
#     # You can extract relevant data and update the speed calculation accordingly
#
# # Initialize the Ant+ node
# ant_node = Node()
# ant_node.start()
#
# # Attach the event listener for Ant+ data
# ant_node.attach(on_antplus_data)

try:
    while True:
        # Read current state of GPIO pins
        current_count_11 = GPIO.input(PIN_11)
        current_count_13 = GPIO.input(PIN_13)

        # Check for transitions on GPIO pin 11
        if current_count_11 != previous_count_11:
            total_count += 1

        # Check for transitions on GPIO pin 13
        if current_count_13 != previous_count_13:
            total_count -= 1

        # Calculate speed based on total counts and time elapsed
        current_time = datetime.datetime.now()
        time_diff = (current_time - previous_time).total_seconds()
        speed = (total_count * wheel_circumference) / time_diff

        # Update previous values
        previous_count_11 = current_count_11
        previous_count_13 = current_count_13
        previous_time = current_time

        # Print speed (for testing)
        print("Speed:", speed)

        # Add code here to send speed data to Zwift using Ant+ or Bluetooth protocol

        time.sleep(0.1)  # Adjust the sleep duration as needed to control the script's execution frequency

except KeyboardInterrupt:
    # Clean up GPIO and close Ant+ node on program exit
    GPIO.cleanup()
    ant_node.stop()
