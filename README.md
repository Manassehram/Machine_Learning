# 👁️‍🗨️ Smart Blind Stick for Visually Impaired Persons

This project is a **Machine Learning-powered Smart Blind Stick** that assists visually impaired individuals in safely navigating different terrains and obstacles. The system combines lightweight deep learning, embedded computing, and sensory feedback for real-time assistance in outdoor environments.

---

## 🧠 Project Overview

This blind assistive system uses a combination of:

- **ESP32-S3-EYE** camera module
- **Raspberry Pi Zero WH** for ML inference
- **Bluetooth headset** for audio feedback
- **Ultrasonic sensors + buzzer** for obstacle detection
- A trained and quantized **terrain classification model** (TFLite INT8)

The stick detects surrounding terrain types and obstacles and communicates the results via **audio alerts and vibrations**, empowering users with real-time feedback.

---

## 🔧 Components Used

| Component             | Function                                                       |
|-----------------------|----------------------------------------------------------------|
| 🧠 Raspberry Pi Zero WH | Runs the quantized terrain classification ML model (TFLite)     |
| 📷 ESP32-S3-EYE         | Captures camera frames and sends them to the Pi via HTTP       |
| 🦻 Bluetooth Headset    | Delivers terrain audio feedback to the user                   |
| 🔊 Buzzer               | Activates for immediate obstacle alerts                        |
| 📏 Ultrasonic Sensor    | Measures distance to obstacles (e.g. HC-SR04)                  |
| 🔋 Power Bank/Battery   | Powers both ESP32 and Raspberry Pi systems                    |

---

## ⚙️ Functionality

1. **Terrain Classification**
   - Uses a custom-trained, lightweight CNN model
   - Classes include: `Grass_Paths`, `Gravel_Stony`, `PaveTile`, `Stairs`, and `Tarmac`
   - Real-time prediction on Raspberry Pi using quantized `.tflite` model

2. **Obstacle Detection**
   - Ultrasonic sensors detect nearby obstacles
   - Triggers buzzer alerts when obstacles are within danger range

3. **Audio Feedback**
   - Bluetooth headset announces terrain types (e.g., "Grass Path", "Stairs Ahead")
   - Prioritizes terrain safety warnings

4. **Low Power Design**
   - Designed for efficient operation using Pi Zero WH and ESP32
   - ESP32 handles camera duties only; ML runs on the Pi for better control

---

## 🧠 Machine Learning Model

- Framework: TensorFlow / Keras
- Optimized with: Quantization-Aware Training (QAT)
- Exported formats:
  - `.h5` for original Keras model
  - `.tflite` for Raspberry Pi deployment
  - Fully quantized `.tflite` (INT8) for efficient inference

---

## 📁 Folder Structure

