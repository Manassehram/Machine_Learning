#!/usr/bin/env python3
from gtts import gTTS
import os
import time
import socket
from datetime import datetime

# === PATHS ===
gps_data_path = "/home/alpha/Desktop/project/gps_data.txt"
output_folder = "/home/alpha/Desktop/project/gpsWav"
last_known_file = os.path.join(output_folder, "last_location.txt")

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# === INTERNET CHECK ===
def has_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

# === READ GPS TEXT FILE ===
def read_gps_data():
    try:
        with open(gps_data_path, "r") as f:
            line = f.readline().strip()
            if not line:
                return None, None
            parts = line.split(',')
            if len(parts) >= 3:
                return ','.join(parts).strip(), ', '.join(parts[2:]).strip()
    except FileNotFoundError:
        print("[ERROR] gps_data.txt not found.")
    except Exception as e:
        print(f"[ERROR] Failed to read GPS data: {e}")
    return None, None

# === CREATE MP3 FROM LOCATION ===
def generate_mp3(location_text):
    if not has_internet():
        print("[WARNING] No internet connection. Skipping audio generation.")
        return None
    try:
        # Delete previous MP3s
        for file in os.listdir(output_folder):
            if file.endswith(".mp3"):
                os.remove(os.path.join(output_folder, file))

        # Timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mp3_file = os.path.join(output_folder, f"location_{timestamp}.mp3")

        # Generate audio
        tts = gTTS(text=f"Your location is {location_text}", lang='en')
        tts.save(mp3_file)

        print(f"[INFO] New location spoken: {location_text}")
        print(f"[INFO] Audio saved to: {mp3_file}")
        return mp3_file
    except Exception as e:
        print(f"[ERROR] Failed to generate MP3: {e}")
        return None

# === MAIN LOOP ===
def main():
    previous_data = ""
    if os.path.exists(last_known_file):
        with open(last_known_file, "r") as f:
            previous_data = f.read().strip()

    print("[INFO] gpsTomp3 started. Monitoring for location changes...")

    while True:
        current_data, location = read_gps_data()

        if current_data and current_data != previous_data:
            if generate_mp3(location):
                with open(last_known_file, "w") as f:
                    f.write(current_data)
                previous_data = current_data
        else:
            print("[INFO] Location unchanged.")

        time.sleep(2)

# === ENTRY POINT ===
if __name__ == "__main__":
    main()
