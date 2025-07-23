#!/usr/bin/env python3
import time
import subprocess
import os
import glob
import threading
from collections import deque
import RPi.GPIO as GPIO
from allSensorsConsolidated import get_sensor_data

# === CONSTANTS ===  78:15:2D:37:51:87 F4:46:47:A3:D9:E5
AUDIO_FILES = {
    "init": "systemInitialized.wav",
    "ok": "allSystemsWorking.wav",
    "wet": "wetSurface.wav",
    "object": "ObjectAhead.wav",
    "dry": "Drysurface.wav",
    "gps_not_locked": "GpsNotLocked.wav",
    "location_sent": "locationSent.wav",
    "location_not_sent": "locationNotSent.wav",
    "obwet": "obWet.wav",
    "shutdown": "poweroff.wav"
}


AUDIO_PATH = "/dev/shm/warnings/"
GPS_MP3_FOLDER = "/home/alpha/Desktop/project/gpsWav/"
GPS_DATA_FILE = "/home/alpha/Desktop/project/gps_data.txt"
BUTTON_PIN = 26
BUZZER_PIN = 25
TARGET_BT_MAC = "78:15:2D:37:51:87"
ML_LOG_FILE = "/home/alpha/Desktop/project/ml_log.txt"

# === SETUP ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.output(BUZZER_PIN, False)

bluetooth_connected = False
buzzer_in_bt_alert = False
obstacle_cooldown = 0
gps_audio_lock = threading.Lock()
interruptible_audio = None
interrupted = False
gps_audio_resumed_once = False
replay_after_interrupt_used = False
distance_cm = 200
terrain_label = "Unknown"

# === AUDIO FUNCTIONS (OPTIMIZED) ===
def stop_audio_playback():
    """More aggressive audio process termination"""
    subprocess.call(['pkill', '-9', 'aplay'])
    subprocess.call(['pkill', '-9', 'mpg123'])
    time.sleep(0.05) # Small delay to ensure processes are terminated

def play_audio(filename, blocking=False, priority=False):
    """Improved audio playback with priority option"""
    filepath = os.path.join(AUDIO_PATH, filename)
    if not os.path.exists(filepath):
        pass # Removed: print(f"[ERROR] Missing audio file: {filepath}")
        return

    def _play():
        pass # Removed: print(f"[INFO] Playing: {filename}")
        if priority:
            # Use higher priority for obstacle warnings
            subprocess.run(['nice', '-n', '-10', 'aplay', filepath], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['aplay', filepath], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)

    if blocking:
        _play()
    else:
        threading.Thread(target=_play, daemon=True).start()

def play_interruptible_audio(path, is_resumed=False):
    global interruptible_audio, interrupted, gps_audio_resumed_once, replay_after_interrupt_used
    interruptible_audio = path

    if not is_resumed:
        gps_audio_resumed_once = False
        replay_after_interrupt_used = False

    def _play():
        global interruptible_audio, interrupted
        with gps_audio_lock:
            subprocess.run(['mpg123', path], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        interruptible_audio = None
        interrupted = False

    threading.Thread(target=_play, daemon=True).start()

def interrupt_and_play_priority(audio_key):
    global interrupted, gps_audio_resumed_once, replay_after_interrupt_used
    interrupted_audio = interruptible_audio
    
    # Immediately stop any ongoing audio
    stop_audio_playback()
    interrupted = True
    
    # Play obstacle audio with priority and without blocking
    play_audio(AUDIO_FILES[audio_key], blocking=False, priority=True)
    
    if interrupted_audio and not gps_audio_resumed_once and not replay_after_interrupt_used:
        gps_audio_resumed_once = True
        replay_after_interrupt_used = True
        time.sleep(0.1) # Small delay before resuming
        play_interruptible_audio(interrupted_audio, is_resumed=True)

# === GPS ===
def is_gps_data_available():
    if not os.path.exists(GPS_DATA_FILE):
        return False
    try:
        with open(GPS_DATA_FILE, 'r') as f:
            line = f.readline().strip()
            return line and not line.startswith("0,0") and not line.endswith("No fix")
    except:
        return False

def play_latest_gps_audio_or_warning():
    global interruptible_audio
    if not is_gps_data_available():
        play_audio(AUDIO_FILES["gps_not_locked"])
        return
    mp3_files = sorted(glob.glob(os.path.join(GPS_MP3_FOLDER, "location_*.mp3")), 
                             key=os.path.getmtime, reverse=True)
    if mp3_files:
        pass # Removed: print(f"[DEBUG] Playing GPS mp3: {mp3_files[0]}")
        play_interruptible_audio(mp3_files[0])
    else:
        play_audio(AUDIO_FILES["gps_not_locked"])

# === TELEGRAM ===
def send_gps_to_telegram():
    try:
        result = subprocess.run(["python3", "/home/alpha/Desktop/project/telegramsms.py"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "Message sent successfully" in result.stdout:
            interrupt_and_play_priority("location_sent")
        else:
            interrupt_and_play_priority("location_not_sent")
    except:
        interrupt_and_play_priority("location_not_sent")

# === BUTTON ===
def handle_button_press():
    time.sleep(0.3)
    second_timeout = 0.5
    start_time = time.time()
    while time.time() - start_time < second_timeout:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                time.sleep(0.01)
            threading.Thread(target=send_gps_to_telegram, daemon=True).start()
            return
    time.sleep(1.5)
    play_latest_gps_audio_or_warning()

# === BLUETOOTH ===
bt_buzzer_thread = None

def is_bluetooth_connected(mac):
    try:
        output = subprocess.check_output(["bluetoothctl", "info", mac], text=True)
        return "Connected: yes" in output
    except:
        return False

def bt_buzzer_alert():
    global buzzer_in_bt_alert
    buzzer_in_bt_alert = True
    while not bluetooth_connected:
        for _ in range(3):
            GPIO.output(BUZZER_PIN, True)
            time.sleep(0.05)  # Beep duration (kept at 0.1s as you suggested)
            GPIO.output(BUZZER_PIN, False)
            time.sleep(0.1) # Shorter silence between beeps in the burst
        time.sleep(2)    # Longer pause between bursts of 3 beeps
    GPIO.output(BUZZER_PIN, False)
    buzzer_in_bt_alert = False

# === BUZZER THREAD ===
def buzzer_distance_feedback():
    global distance_cm
    while True:
        if 0 < distance_cm < 106 and not buzzer_in_bt_alert:
            proximity = max(0.0, min(1.0, (106 - distance_cm) / 106.0))
            beep_duration = 0.05
            silence_duration = 0.05 + (0.25 * (1 - proximity))

            GPIO.output(BUZZER_PIN, True)
            time.sleep(beep_duration)

            if distance_cm >= 106:
                GPIO.output(BUZZER_PIN, False)
                continue

            GPIO.output(BUZZER_PIN, False)
            time.sleep(silence_duration)
        else:
            GPIO.output(BUZZER_PIN, False)
            time.sleep(0.01)

# === BACKGROUND SERVICES ===
def start_background_services():
    bg_pid_file = "/home/alpha/Desktop/project/bg_pids.txt"
    try:
        pids = []
        p1 = subprocess.Popen(["python3", "/home/alpha/Desktop/project/gps_withPlacename.py"],
                               stdout=open("/home/alpha/Desktop/project/gps_log.txt", "a"),
                               stderr=subprocess.STDOUT)
        pids.append(p1.pid)

        p2 = subprocess.Popen(["python3", "/home/alpha/Desktop/project/gpsTomp3.py"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pids.append(p2.pid)

        p3 = subprocess.Popen(["python3", "/home/alpha/Desktop/project/mlModel.py"],
                               stdout=open(ML_LOG_FILE, "a"),
                               stderr=subprocess.STDOUT)
        pids.append(p3.pid)

        with open(bg_pid_file, 'w') as f:
            for pid in pids:
                f.write(f"{pid}\n")

        pass # Removed: print("[INFO] Starting terrain detection service...")
        for _ in range(10):
            if os.path.exists(ML_LOG_FILE):
                with open(ML_LOG_FILE, "r") as f:
                    lines = f.readlines()
                    if any("Detected terrain" in line for line in lines):
                        pass # Removed: print("[INFO] TERRAIN DETECTION STARTED")
                        break
            time.sleep(0.5)
        else:
            pass # Removed: print("[WARNING] TERRAIN DETECTION NOT STARTED")
    except Exception as e:
        pass # Removed: print(f"[ERROR] Background service start failed: {e}")

terrain_history = deque(maxlen=10)
last_terrain_played = None
TERRAIN_AUDIO_FILES = {
    "Grass_Paths": "grass.wav",
    "Gravel_Stony": "gravel.wav",
    "PaveTile": "tile.wav",
    "Stairs": "stairs.wav",
    "Tarmac": "tarmac.wav"
}

def handle_terrain_audio(current_label):
    global terrain_history, last_terrain_played

    if current_label not in TERRAIN_AUDIO_FILES:
        terrain_history.clear()
        last_terrain_played = None
        return

    terrain_history.append(current_label)

    if current_label == "Stairs":
        if list(terrain_history)[-2:].count("Stairs") == 2 and last_terrain_played != "Stairs":
            play_audio(TERRAIN_AUDIO_FILES["Stairs"])
            last_terrain_played = "Stairs"
    else:
        if list(terrain_history)[-5:].count(current_label) == 5 and last_terrain_played != current_label:
            play_audio(TERRAIN_AUDIO_FILES[current_label])
            last_terrain_played = current_label

def stop_background_services():
    bg_pid_file = "/home/alpha/Desktop/project/bg_pids.txt"
    if not os.path.exists(bg_pid_file):
        pass # Removed: print("[INFO] No background PID file found.")
        return

    try:
        with open(bg_pid_file, 'r') as f:
            pids = [int(line.strip()) for line in f if line.strip().isdigit()]
        for pid in pids:
            try:
                os.kill(pid, 9)
                pass # Removed: print(f"[INFO] Killed background process with PID {pid}")
            except ProcessLookupError:
                pass # Removed: print(f"[WARNING] PID {pid} not running.")
        os.remove(bg_pid_file)
    except Exception as e:
        pass # Removed: print(f"[ERROR] Could not stop background services: {e}")

def play_shutdown_audio():
    """Plays the shutdown audio if available, blocking until complete."""
    if "shutdown" in AUDIO_FILES:
        filepath = os.path.join(AUDIO_PATH, AUDIO_FILES["shutdown"])
        if os.path.exists(filepath):
            pass # Removed: print("[INFO] Playing shutdown audio...")
            subprocess.run(['aplay', filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            pass # Removed: print(f"[WARNING] Shutdown audio file not found at {filepath}. Skipping audio.")
    else:
        pass # Removed: print("[WARNING] Shutdown audio key not in AUDIO_FILES.")


def main():
    global bluetooth_connected, obstacle_cooldown, distance_cm, terrain_label, bt_buzzer_thread

    pass # Removed: print("[INFO] System starting...")
    bluetooth_connected = is_bluetooth_connected(TARGET_BT_MAC)

    if not bluetooth_connected:
        pass # Removed: print("[INFO] Waiting up to 60 seconds for Bluetooth connection...")
        for i in range(60, 0, -1):
            if is_bluetooth_connected(TARGET_BT_MAC):
                bluetooth_connected = True
                pass # Removed: print("[INFO] Bluetooth connected.")
                break
            pass # Removed: print(f"[INFO] Waiting... {i}s remaining")
            time.sleep(1)

        if not bluetooth_connected:
            pass # Removed: print("[WARNING] Bluetooth not connected. Starting buzzer alert.")
            bt_buzzer_thread = threading.Thread(target=bt_buzzer_alert, daemon=True)
            bt_buzzer_thread.start()

    play_audio(AUDIO_FILES["init"], blocking=True)

    pass # Removed: print("[INFO] Checking sensors...")
    sensor_ready = gps_ok = distance_ok = surface_ok = False

    for _ in range(30):
        try:
            data = get_sensor_data()
            if not gps_ok and is_gps_data_available():
                gps_ok = True
                pass # Removed: print("[INFO] GPS STARTED")
            if not distance_ok and data["distance_cm"] > 0:
                distance_ok = True
                pass # Removed: print("[INFO] ULTRASONIC STARTED")
            if not surface_ok and data["surface"] in ["Dry surface", "Wet or muddy surface"]:
                surface_ok = True
                pass # Removed: print("[INFO] MOISTURE SENSOR STARTED")
            if distance_ok and surface_ok:
                sensor_ready = True
                break
        except Exception as e:
            pass # Removed: print(f"[WARNING] Sensor check failed: {e}")
        time.sleep(0.1)

    if sensor_ready:
        pass # Removed: print("[INFO] Sensors ready. System confirmed.")
        play_audio(AUDIO_FILES["ok"])
    else:
        pass # Removed: print("[WARNING] Sensors not fully ready. Skipping OK audio.")

    start_background_services()
    threading.Thread(target=buzzer_distance_feedback, daemon=True).start()

    state = {
        "wet_alert_played": False,
        "dry_alert_played": False,
        "surface_history": deque(maxlen=10),
        "system_initialized": False,
        "dry_check_start_time": time.time()
    }

    last_bt_check_time = time.time()

    while True:
        current_time = time.time()

        # === Sensor Data ===
        data = get_sensor_data()
        surface = data["surface"]
        distance = data["distance_cm"]
        distance_cm = distance

        try:
            with open(ML_LOG_FILE, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if "Detected terrain" in line:
                        terrain_label = line.strip().split("Detected terrain:")[-1].split("(")[0].strip()
                        break
        except Exception:
            terrain_label = "Unknown"

        pass # Removed: print(f"[DATA] Place: {data['place']}, Coords: ({data['latitude']}, {data['longitude']}), " f"Distance: {distance:.2f}, Surface: {surface} : Terrain {terrain_label}")

        handle_terrain_audio(terrain_label)

        # === Obstacle Detection and Alerts ===
        if surface == "Wet or muddy surface" and distance < 110.0 and current_time - obstacle_cooldown >= 5:
            stop_audio_playback()
            play_audio(AUDIO_FILES["obwet"], priority=True)
            obstacle_cooldown = current_time
            state["wet_alert_played"] = True
            state["dry_alert_played"] = False
            continue

        if distance < 110.0 and current_time - obstacle_cooldown >= 5:
            stop_audio_playback()
            play_audio(AUDIO_FILES["object"], priority=True)
            obstacle_cooldown = current_time

        # === Surface Logic ===
        state["surface_history"].append(surface)
        surface_str = "".join(['W' if s == "Wet or muddy surface" else 'D' for s in state["surface_history"]])
        wet_pattern = "WDW" in surface_str or "DWDW" in surface_str or surface_str.count('W') >= 5
        dry_pattern = surface_str.endswith("D" * 8) and len(state["surface_history"]) >= 8

        if not state["system_initialized"] and current_time - state["dry_check_start_time"] > 10:
            state["system_initialized"] = True

        if wet_pattern and not state["wet_alert_played"]:
            interrupt_and_play_priority("wet")
            state["wet_alert_played"] = True
            state["dry_alert_played"] = False

        if state["system_initialized"] and dry_pattern and not state["dry_alert_played"]:
            interrupt_and_play_priority("dry")
            state["dry_alert_played"] = True
            state["wet_alert_played"] = False

        time.sleep(0.05)

        # === Shutdown Press-and-Hold Detection ===
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            hold_start = time.time()
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                held_duration = time.time() - hold_start
                if held_duration >= 5:
                    pass # Removed: print("[INFO] Button held for 5s. Shutting down.")
                    stop_audio_playback()
                    play_shutdown_audio()
                    stop_background_services()
                    # REMOVED THIS LINE: subprocess.call(['pkill', '-f', 'runproject.py'])
                    subprocess.call(['sudo', 'shutdown', 'now'])
                    return
                time.sleep(0.1)

            # If released before 5s
            if time.time() - hold_start < 5:
                handle_button_press()
                time.sleep(0.5)

        # === Bluetooth Check ===
        if current_time - last_bt_check_time > 5:
            new_status = is_bluetooth_connected(TARGET_BT_MAC)
            if new_status != bluetooth_connected:
                bluetooth_connected = new_status
                if not bluetooth_connected:
                    pass # Removed: print("[WARNING] Bluetooth disconnected. Starting buzzer alert.")
                    if not bt_buzzer_thread or not bt_buzzer_thread.is_alive():
                        bt_buzzer_thread = threading.Thread(target=bt_buzzer_alert, daemon=True)
                        bt_buzzer_thread.start()
                else:
                    pass # Removed: print("[INFO] Bluetooth reconnected. Stopping buzzer alert.")
            last_bt_check_time = current_time

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass # Removed: print("[INFO] System interrupted.")
    finally:
        stop_background_services()
        GPIO.cleanup()
