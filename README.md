# circuitpython-uart-pasthrough
A circuitpython program providing passthrough from the USB to a UART

I wrote this while debugging a esp32-c3 running the espressif AT command
set, which outputs over the UART.  This allows you to connect a circuitpython
board (e.g. Adafruit Feather M4 Express in my case) to the UART tx/rx of
the device and type at it with the USB connection on computer.  

This also translates `\r` characters on USB input into `\r\n` sequences 
since the espressif AT command set (and probably others) expect `\r\n`
to terminate commands, but the "screen" terminal program on MacOS only
outputs `\r` by default.  Rather than try and figure out how to fix screen 
it's easier to just do it here.  It's disabled with a boolean flag below.  

The neopixel is used for status: 
* white: no USB connected 
* blue: USB connected, idle
* green: reading bytes from USB 
* red: reading bytes from UART   

Your circuitpython board needs these libraries in `/lib` 
``` 
adafruit_bus_device
adafruit_pixelbuf.mpy
neopixel.mpy    
```
Note that for this to work you MUST have this in boot.py on 
circuitpython, to enable the usb_cdc connection:
```
import usb_cdc
usb_cdc.enable(console=True, data=True)
```
Note that if you change boot.py you must reset the board with the reset
button or power cycle to take effect.  

This will make a *second* USB device different from the circuitpython REPL
console.   ie - console is `/dev/ttyACM0` and the passthrough port is `/dev/ttyACM1`
(on Linux, names will be different on different systems).  You want to connect
your terminal program to the passthrough port, e.g:
		`screen /dev/ttyACM1`
on MacOS.  

Steven Cogswell November 2022 https://github.com/scogswell

References: 

https://learn.adafruit.com/adafruit-feather-m4-express-atsamd51/circuitpython-uart-serial
https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html
https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/AT_Command_Set/Basic_AT_Commands.html