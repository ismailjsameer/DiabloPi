import requests
import time
import os
import keyboard
from picamera2 import Picamera2

MY_IP = "192.168.86.36:5000"

URL = "http://192.168.86.36:5000/scan"

KEY_TO_PRESS = 's'

picam2 = Picamera2()
config = picam2.create_still_configuration({"size": (640,480)})
picam2.configure(config)
picam2.start()

print(f"Camera Ready, Waitin for user...")
print(f"Sending to {URL}")

def take_photo():
	print("Sending Photo...")
	photo = picam2.capture_array()
	filename = 'temp.jpg'
	picam2.capture_file(filename)

	try: 
		with open(filename, 'rb') as f:response = requests.post(URL, files = {'image': f }, timeout=10)
		if response.status_code == 200:
			print("Sent Successfully!")
			print(f"Response: {response.json()}")
		else:
			print("Error:{response.status_code}")
	except Exception as e:
		print(f"Error sending{e}")

keyboard.add_hotkey(KEY_TO_PRESS, take_photo)
keyboard.wait()
