"""A program for running Vessegen's Bioreactor."""
import os
import RPi.GPIO as GPIO  # pylint: disable=consider-using-from-import

# Declare the icon path for the windows
ICON_PATH = os.path.join(os.path.dirname(__path__[0]),
                         'executable/vessegen.png')

# Create a list of dictionaries to keep track of which GPIO pins are for which
# chamber
GPIO_PINS = [
    {
        "add": 3,
        "remove": 5
    },
    {
        "add": 7,
        "remove": 8
    },
    {
        "add": 10,
        "remove": 12
    },
    {
        "add": 11,
        "remove": 13
    },
    {
        "add": 18,
        "remove": 19
    },
    {
        "add": 21,
        "remove": 22
    },
    {
        "add": 23,
        "remove": 24
    },
    {
        "add": 31,
        "remove": 32
    }
]

# Disable GPIO warnings (very common to do)
GPIO.setwarnings(False)  # pylint: disable=no-member

# Set up the GPIO pins
GPIO.setmode(GPIO.BOARD)  # pylint: disable=no-member
for chamber in GPIO_PINS:
    GPIO.setup(chamber["add"], GPIO.OUT)  # pylint: disable=no-member
    GPIO.setup(chamber["remove"], GPIO.OUT)  # pylint: disable=no-member
