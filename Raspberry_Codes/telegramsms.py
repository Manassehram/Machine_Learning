import requests

# === CONFIGURATION ===
BOT_TOKEN = "7808083933:AAGsjdu-mmZuM4VTTpk1pkcab7w8CYGpB-I"  # Replace with your Telegram bot token
CHAT_ID = 6193395930               # Replace with your chat ID
GPS_DATA_FILE = "/home/alpha/Desktop/project/gps_data.txt"  # Path to GPS data file

# === FUNCTION TO READ GPS DATA ===
def read_gps_coordinates(file_path):
    try:
        with open(file_path, "r") as file:
            line = file.readline().strip()
            if not line:
                return None, None
            parts = line.split(",")
            if len(parts) >= 2:
                latitude = parts[0].strip()
                longitude = parts[1].strip()
                return latitude, longitude
            else:
                return None, None
    except Exception as e:
        print(f"[ERROR] Failed to read GPS file: {e}")
        return None, None

# === FUNCTION TO SEND MESSAGE TO TELEGRAM ===
def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("[INFO] Message sent successfully!")
    else:
        print(f"[ERROR] Failed to send message: {response.text}")

# === MAIN LOGIC ===
latitude, longitude = read_gps_coordinates(GPS_DATA_FILE)

if latitude and longitude:
    google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
    message = f"📍 GPS Location:\n{google_maps_url}"
    send_telegram_message(BOT_TOKEN, CHAT_ID, message)
else:
    print("[WARNING] GPS coordinates not available or file is empty.")
