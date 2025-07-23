#!/usr/bin/env python3
import pigpio
import time
import requests
import os
import sys

# === CONFIGURATION ===
RX_GPIO = 23
BAUD = 9600
GPS_DATA_FILE = "/home/alpha/Desktop/project/gps_data.txt"
pi = None  # Global instance for cleanup

# === HELPERS ===
def parse_GPGGA(sentence):
    try:
        parts = sentence.split(',')
        if len(parts) >= 7 and parts[0] == '$GPGGA':
            fix_quality = parts[6]
            if fix_quality == '0':
                return None, None  # No GPS fix

            lat_raw = parts[2]
            lat_dir = parts[3]
            lon_raw = parts[4]
            lon_dir = parts[5]
            if not lat_raw or not lon_raw:
                return None, None  # Missing data

            lat = float(lat_raw[:2]) + float(lat_raw[2:]) / 60.0
            if lat_dir == 'S':
                lat = -lat
            lon = float(lon_raw[:3]) + float(lon_raw[3:]) / 60.0
            if lon_dir == 'W':
                lon = -lon
            return lat, lon
    except Exception as e:
        print(f"[ERROR] GPGGA Parse Error: {e}")
    return None, None

def reverse_geocode(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'zoom': 18,
            'addressdetails': 1
        }
        headers = {'User-Agent': 'RaspberryPi-GPS-App'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('display_name', 'Unknown location')
        return f"HTTP error {response.status_code}"
    except Exception as e:
        return f"Request error: {e}"

def write_gps_data(lat, lon, location):
    try:
        with open(GPS_DATA_FILE, 'w') as f:
            f.write(f"{lat:.6f},{lon:.6f},{location}\n")
        os.chmod(GPS_DATA_FILE, 0o666)
        print(f"[INFO] GPS Data Written: {lat:.6f},{lon:.6f},{location}")
    except Exception as e:
        print(f"[ERROR] Writing GPS data: {e}")

def ensure_pigpio_connection():
    global pi
    while True:
        pi = pigpio.pi()
        if pi.connected:
            return pi
        print("[ERROR] Could not connect to pigpio. Retrying in 5s...")
        time.sleep(5)

# === MAIN LOOP ===
def main_loop():
    global pi
    pi = ensure_pigpio_connection()
    pi.bb_serial_read_open(RX_GPIO, BAUD)
    buffer = ""
    last_fix_time = 0
    last_query_time = 0
    last_written = ""
    first_fix = False

    print("[INFO] GPS reader running...")

    # ?? Immediately say "No fix" until proven otherwise
    write_gps_data(0, 0, "No fix")
    last_written = "0.000000,0.000000"

    while True:
        try:
            (count, data) = pi.bb_serial_read(RX_GPIO)
            if count:
                buffer += data.decode('utf-8', errors='ignore')
                lines = buffer.split('\n')
                buffer = lines[-1] if lines else ""
                for line in lines[:-1]:
                    if line.startswith('$GPGGA'):
                        lat, lon = parse_GPGGA(line.strip())
                        if lat is not None and lon is not None:
                            first_fix = True
                            last_fix_time = time.time()
                            if time.time() - last_query_time >= 5:
                                location = reverse_geocode(lat, lon)
                                last_query_time = time.time()
                                current = f"{lat:.6f},{lon:.6f}"
                                if current != last_written:
                                    write_gps_data(lat, lon, location)
                                    last_written = current

            # Fallback if fix lost after being seen
            if first_fix and time.time() - last_fix_time > 30:
                if not last_written.startswith("0.000000"):
                    write_gps_data(0, 0, "No fix")
                    last_written = "0.000000,0.000000"

            time.sleep(0.2)

        except Exception as inner:
            print(f"[ERROR] Loop exception: {inner}")
            time.sleep(2)

# === ENTRY POINT WITH CLEANUP ===
if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("[INFO] GPS script interrupted by user.")
    except Exception as e:
        print(f"[FATAL] Error in GPS script: {e}")
    finally:
        if pi:
            try:
                pi.bb_serial_read_close(RX_GPIO)
            except pigpio.error:
                pass  # Ignore if already closed
            pi.stop()
            print("[INFO] pigpio cleaned up properly.")
