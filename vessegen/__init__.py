"""A program for running Vessegen's Bioreactor."""
import RPi.GPIO as GPIO  # pylint: disable=consider-using-from-import

# Declare the amount that should occur in a media change
MEDIA_VOL = 40.0

# Declare the icon path for the windows
ICON_PATH = '/usr/bin/vessegen.png'

# Create a list of dictionaries to keep track of which GPIO pins are for which
# chamber
GPIO_PINS = [
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
    },
    {
        "add": 33,
        "remove": 35
    },
    {
        "add": 36,
        "remove": 38
    }
]

# Disable GPIO warnings (very common to do)
GPIO.setwarnings(False)  # pylint: disable=no-member

# Set up the GPIO pins
GPIO.setmode(GPIO.BOARD)  # pylint: disable=no-member
for chamber in GPIO_PINS:
    GPIO.setup(chamber["add"], GPIO.OUT)  # pylint: disable=no-member
    GPIO.setup(chamber["remove"], GPIO.OUT)  # pylint: disable=no-member
    GPIO.output(chamber["add"], GPIO.LOW)  # pylint: disable=no-member
    GPIO.output(chamber["remove"], GPIO.LOW)  # pylint: disable=no-member
