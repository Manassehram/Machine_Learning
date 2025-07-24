# Raspberry Pi Smart Blind Stick Integration

This folder contains the core Python scripts that run on the Raspberry Pi to provide intelligent navigation and safety features for the smart blind stick. These components interface with machine learning models, GPS data, obstacle sensors, and even Telegram alerts for real-time communication.

---

## 🔧 Core Scripts and Their Functionality

### `runproject.py`
- The **main execution script**.
- Orchestrates all key functionalities: sensor data collection, ML inference, audio feedback, and GPS integration.
- Should be launched on system boot or manually to activate the device.

---

### `ml_model.py`
- Loads the trained **quantized terrain classification model** (.tflite).
- Captures images from a connected camera.
- Performs inference and returns the predicted terrain type (e.g., grass, stairs, tarmac).
- Lightweight and optimized for Raspberry Pi Zero using TensorFlow Lite.

---

### `gps_to_mp3.py`
- Converts live **GPS coordinates** into spoken location using **text-to-speech**.
- Useful for guiding the user with verbal feedback on their current position.
- May use tools like gTTS or pyttsx3 depending on implementation.

---

### `gpswithplacename.py`
- Translates raw GPS coordinates into **human-readable place names** using reverse geocoding.
- Enhances the spoken location feedback by turning latitude/longitude into landmarks or area names.

---

### `allsensors.py`
- Reads data from **multiple sensors**:
  - **Moisture sensor** for detecting wet or muddy surfaces.
  - **Ultrasonic sensor** for measuring distance to nearby obstacles.
  - **GPS module** for location tracking.
- Combines readings in a clean JSON-style output for integration with the main logic.

#### Example Output:
```json
{
  "place": "Kenyatta Avenue",
  "latitude": -1.2921,
  "longitude": 36.8219,
  "distance_cm": 58.4,
  "surface": "Wet or muddy surface"
}
```
### `telegramspy.py`
Sends location alerts to a predefined Telegram chat using a bot.
Periodically reads the latest GPS data from a file and generates a Google Maps link.
Helps guardians or caretakers track the user's location in real time.

### 💡 How Everything Works Together  
runproject.py initiates:
Real-time terrain classification using ml_model.py.
Audio instructions using gps_to_mp3.py or gpswithplacename.py.
Periodic sensor checks using allsensors.py.
Emergency alerts using telegramspy.py.
Sensor and model outputs are combined to provide contextual feedback to the user through audio or buzzer cues.

### 📎 Notes
GPS data is shared across scripts via gps_data.txt.
Ensure all hardware (sensors, camera, GPS module) is connected properly.
Telegram bot token and chat ID should be kept secure and placed in environment variables or config files for production use.

### 📂 Folder Setup
project/
│
├── runproject.py
├── ml_model.py
├── gps_to_mp3.py
├── gpswithplacename.py
├── telegramspy.py
├── allsensors.py
└── gps_data.txt
