#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import os
import threading

# GPIO Pin Definitions
MOISTURE_PIN = 24
TRIG_PIN = 27
ECHO_PIN = 22
GPS_DATA_FILE = "/home/alpha/Desktop/project/gps_data.txt"

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(MOISTURE_PIN, GPIO.IN)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Distance caching
last_distance = 999.0
last_distance_time = 0
DISTANCE_CACHE_DURATION = 0.05  # Cache for 50ms

# GPS caching
last_gps_data = (0.0, 0.0, "Unknown")
last_gps_read_time = 0
GPS_READ_INTERVAL = 1.0  # Cache for 1 second

def get_moisture_status():
    return "Dry surface" if GPIO.input(MOISTURE_PIN) == 1 else "Wet or muddy surface"

def get_distance(timeout=0.03):  # Increased timeout for reliability
    global last_distance, last_distance_time
    current_time = time.time()
    if current_time - last_distance_time < DISTANCE_CACHE_DURATION:
        return last_distance

    GPIO.output(TRIG_PIN, False)
    time.sleep(0.002)  # Reduced from 0.05
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    start_time = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        if time.time() - start_time > timeout:
            last_distance = 999.0
            last_distance_time = current_time
            return last_distance
    pulse_start = time.time()

    while GPIO.input(ECHO_PIN) == 1:
        if time.time() - pulse_start > timeout:
            last_distance = 999.0
            last_distance_time = current_time
            return last_distance
    pulse_end = time.time()

    elapsed = pulse_end - pulse_start
    distance = (elapsed * 34300) / 2
    last_distance = round(distance, 2)
    last_distance_time = current_time
    return last_distance

def get_latest_gps_info():
    global last_gps_data, last_gps_read_time
    current_time = time.time()
    if current_time - last_gps_read_time < GPS_READ_INTERVAL:
        return last_gps_data
    try:
        if not os.path.exists(GPS_DATA_FILE):
            print(f"[ERROR] GPS data file does not exist: {GPS_DATA_FILE}")
            return None, None, "Unknown"
        with open(GPS_DATA_FILE, 'r') as f:
            line = f.readline().strip()
            if not line:
                print(f"[WARNING] GPS data file is empty: {GPS_DATA_FILE}")
                return None, None, "Unknown"
            parts = line.split(',')
            if len(parts) < 3:
                return None, None, "Unknown"
            lat = float(parts[0])
            lon = float(parts[1])
            location = ','.join(parts[2:]).strip()
            last_gps_data = (lat, lon, location)
            last_gps_read_time = current_time
            return lat, lon, location
    except Exception as e:
        print(f"[ERROR] Reading GPS data: {e}")
        return None, None, "Unknown"

def get_sensor_data():
    moisture_result = ["Dry surface"]
    distance_result = [999.0]

    def read_moisture():
        moisture_result[0] = get_moisture_status()

    def read_distance():
        distance_result[0] = get_distance()

    t1 = threading.Thread(target=read_moisture)
    t2 = threading.Thread(target=read_distance)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    lat, lon, location = get_latest_gps_info()
    if lat is None or lon is None:
        lat, lon, location = 0.0, 0.0, "Unknown"

    return {
        "place": location,
        "latitude": lat,
        "longitude": lon,
        "distance_cm": distance_result[0],
        "surface": moisture_result[0]
    }

if __name__ == "__main__":
    try:
        print(get_sensor_data())
    finally:
        GPIO.cleanup()