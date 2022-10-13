# A USB-to-UART passthrough program for Circuitpython
# 
# I wrote this while debugging a esp32-c3 running the espressif AT command
# set, which outputs over the UART.  This allows you to connect a circuitpython
# board (e.g. Adafruit Feather M4 Express in my case) to the UART tx/rx of
# the device and type at it with the USB connection on computer.  
#
# This also translates \r characters on USB input into \r\n sequences 
# since the espressif AT command set (and probably others) expect \r\n
# to terminate commands, but the "screen" terminal program on MacOS only
# outputs \r by default.  Rather than try and figure out how to fix screen 
# it's easier to just do it here.  It's disabled with a boolean flag below.  
#
# The neopixel is used for status: 
# white: no USB connected 
# blue: USB connected, idle
# green: reading bytes from USB 
# red: reading bytes from UART   
#
# Your circuitpython board needs these libraries in /lib 
# adafruit_bus_device
# adafruit_pixelbuf.mpy
# neopixel.mpy    
#
# Note that for this to work you MUST have this in boot.py on 
# circuitpython, to enable the usb_cdc connection:
#
# ---the two lines below this, without the "#"
#import usb_cdc
#usb_cdc.enable(console=True, data=True)
# ---the two lines above this, without the "#"
# Note that if you change boot.py you must reset the board with the reset
# button or power cycle to take effect.  
#
# This will make a *second* USB device different from the circuitpython REPL
# console.   ie - console is /dev/ttyACM0 and the passthrough port is /dev/ttyACM1
# (on Linux, names will be different on different systems).  You want to connect
# your terminal program to the passthrough port, e.g:
# 		screen /dev/ttyACM1   
# on MacOS.  
#
# Steven Cogswell November 2022 https://github.com/scogswell
#
# References: 
# https://learn.adafruit.com/adafruit-feather-m4-express-atsamd51/circuitpython-uart-serial
# https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html
# https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/AT_Command_Set/Basic_AT_Commands.html

"""CircuitPython Feather UART Passthrough"""
import board
import busio
import digitalio
import usb_cdc
import neopixel
import sys

# If your terminal program (e.g. screen on MacOS) doesn't automatically
# add "\n" to "\r" then you can make this True and if you push enter
# it will send a "\r\n\", which is important for things like the 
# espressif AT command set which expects \r\n for the ends of lines
# and saves you trying to figure out how to reconfigure screen
# or your terminal program.
#
# If your terminal program sends "\r\n" for enter already, or you 
# don't want this behaviour change ADD_SLASHN_TO_SLASHR to False 
ADD_SLASHN_TO_SLASHR = True

# Set this to True if you want to see what you're typing and the 
# passthrough device does not echo it back.  Set it to false 
# if you're seeing two of every character (your device is echoing already)
LOCAL_ECHO = False

# For most CircuitPython boards, the little led (not the neopixel) 
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# The neopixel on the Feather board itself, damn that thing is bright
num_pixels = 1
pixels = neopixel.NeoPixel(board.NEOPIXEL, num_pixels, brightness=0.1, auto_write=True)

# This is the UART connection (to the device we're passing-through to)
# Note on the Feather M4 Express at 115200 bps this had to be 128 to work correctly, a 64 byte
# buffer would miss characters.  "Your mileage may vary"
uart = busio.UART(board.TX, board.RX, baudrate=115200, receiver_buffer_size=128, timeout=0.1)
# This is the USB connection (to the user's terminal program) 
serial = usb_cdc.data

# Wait for a USB connection (e.g. screen /dev/ttyACM1), show a white neopixel in the meantime
print(f"\nThis is the console output, you want to connect to the other port for Passthrough")
print(f"e.g. screen /dev/ttyACM1\n")
try:
	# Show a white neopixel while waiting for USB connection 
	while serial.connected == False:   
		pixels[0]=(255,255,255)
except:
	print(f"Can't create the USB CDC device for passthrough")
	print(f"Make sure your boot.py has these two lines in it:\n")
	print(f"import usb_cdc")
	print(f"usb_cdc.enable(console=True, data=True)\n")
	print(f"You must also push the RESET button the board to reload boot.py if you make changes to it.\n\n")
	sys.exit()

print(f"Connected on passthrough port")
# show a blue neopixel when connected
pixels[0]=(0,0,255)
serial.write(b"Passthrough Connected\r\n")

while True:
	# If the USB connection is still active, show the blue neopixel, otherwise
	# show it as white to indicate a disconnect
	if serial.connected == True:
		pixels[0]=(0,0,255)
	else:
		pixels[0]=(255,255,255)

	# Check for incoming bytes from the USB port (user typing)
	if serial.in_waiting > 0:
		pixels[0]=(0,255,0)  # Neopixel green on user typing input received  
		led.value = True     # Also light up the board led to show activity
		bbyte = serial.read(1)
		# If we get a \r, also send a \n because things like the 
		# espressif AT commands set want to see \r\n on the ends
		# of commands but things like "screen" on MacOS just sends
		# the \r.  This saves having to reprogram screen or your
		# terminal command.  Change behaviour by setting
		# ADD_SLASHN_TO_SLASHR True or False at the top of the program.
		if bbyte == b'\r' and ADD_SLASHN_TO_SLASHR == True: 
			uart.write(b'\r\n')
		else:
			if LOCAL_ECHO == True: 
				serial.write(bbyte)  # send the byte back to the user if asked
			uart.write(bbyte)        # send the byte to the UART device 
		led.value = False 

    # Check for incoming bytes from the UART device (Modem, whatever)
	if uart.in_waiting > 0:
		led.value = True      # board led shows activity
		pixels[0]=(255,0,0)   # Neopixel red on UART being received
		data = uart.read(uart.in_waiting)  # read all bytes available
		if data is not None:
			led.value = True
			serial.write(data)
		led.value = False
