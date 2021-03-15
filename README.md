# py-ubnt-airviewer
Python UBNT airView client as alternative for the Java based client shipped with Ubiquiti airMax based products. Tested with:
* Bullet M2 (firmware 5.x)
* NanoStation M5 (firmware XM.v6.3.2)

![Screenshot](https://github.com/AnyWi/py-ubnt-airviewer/raw/trunk/screenshot.png)

Main reasons for creating the tool:
* Java gets more and more difficult to run due to security which is tightened by default.
* Logging and replay data for later analytics of data.
* Allow data collections without the need of a GUI application.



```
Usage:airviewer.py <live|replay FILENAME>

Options:
	live              	=	Process live data from device 192.168.1.20
	replay FILENAME   	=	Replay FILENAME
```
