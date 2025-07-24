# 🧠 Model Definitions

This directory contains all trained and exported machine learning models used in the Smart Blind Stick project. These models are responsible for real-time terrain classification on edge devices like the Raspberry Pi Zero WH.

---

## 📦 Model Categories

### 🔹 Custom Neural Networks (Pre-Quantized)
These models are trained from scratch based on a **custom lightweight CNN inspired by MobileNetV2**, and quantized **after training** to `.tflite` format using **post-training quantization** (PTQ).

- **Input size:** (120, 160, 3)
- **Architecture highlights:**
  - Depthwise Separable Convolutions
  - Global Average Pooling
  - Dropout Regularization
- **Target device:** Raspberry Pi Zero WH
- **Use case:** Efficient terrain recognition with low latency

---

### 🔹 Post-Training Quantized (PTQ) Models

These models were trained in full precision and later **converted to 8-bit INT using TensorFlow Lite post-training quantization**.

- ✅ Very small model size (~60KB)
- ✅ Fast inference on constrained devices
- ⚠️ Slight accuracy drop compared to float models
- ✅ No change to the original training code

**Advantages:**
- Simple to implement
- Runs with high efficiency
- Compatible with TensorFlow Lite Micro and embedded devices

---

### 🔹 Quantization-Aware Trained (QAT) Models

These models were trained **with quantization simulated during training**, resulting in models that are more resilient to the lower numerical precision of INT8 inference.

- ✅ Higher accuracy than PTQ models
- ✅ Same size as post-training quantized models
- ✅ Better calibration of weights and activations
- ⚠️ Requires special training setup using `tfmot.quantization.keras.quantize_model`

---

## 🧮 Model Architecture Summary
Input shape: (120, 160, 3)
Total Parameters: 15,479 (60.46 KB)
Trainable: 14,743 (57.59 KB)
Non-Trainable: 736 (2.88 KB)

| Layer                          | Output Shape          | Parameters |
|-------------------------------|------------------------|------------|
| InputLayer                    | (None, 120, 160, 3)    | 0          |
| Conv2D                        | (None, 60, 80, 8)      | 216        |
| BatchNorm + ReLU              | (None, 60, 80, 8)      | 32         |
| DepthwiseConv2D               | (None, 60, 80, 8)      | 72         |
| BatchNorm + ReLU              | (None, 60, 80, 8)      | 32         |
| Conv2D                        | (None, 60, 80, 16)     | 128        |
| BatchNorm + ReLU              | (None, 60, 80, 16)     | 64         |
| DepthwiseConv2D               | (None, 30, 40, 16)     | 144        |
| BatchNorm + ReLU              | (None, 30, 40, 16)     | 64         |
| Conv2D                        | (None, 30, 40, 32)     | 512        |
| BatchNorm + ReLU              | (None, 30, 40, 32)     | 128        |
| DepthwiseConv2D               | (None, 30, 40, 32)     | 288        |
| BatchNorm + ReLU              | (None, 30, 40, 32)     | 128        |
| Conv2D                        | (None, 30, 40, 32)     | 1,024      |
| BatchNorm + ReLU              | (None, 30, 40, 32)     | 128        |
| DepthwiseConv2D               | (None, 15, 20, 32)     | 288        |
| BatchNorm + ReLU              | (None, 15, 20, 32)     | 128        |
| Conv2D                        | (None, 15, 20, 64)     | 2,048      |
| BatchNorm + ReLU              | (None, 15, 20, 64)     | 256        |
| DepthwiseConv2D               | (None, 15, 20, 64)     | 576        |
| BatchNorm + ReLU              | (None, 15, 20, 64)     | 256        |
| Conv2D                        | (None, 15, 20, 64)     | 4,096      |
| BatchNorm + ReLU              | (None, 15, 20, 64)     | 256        |
| GlobalAveragePooling2D       | (None, 64)             | 0          |
| Dense (64 units)              | (None, 64)             | 4,160      |
| Dropout                       | (None, 64)             | 0          |
| Dense (7 classes)             | (None, 7)              | 455        |

> Designed to run efficiently on Raspberry Pi Zero WH while maintaining high accuracy.

---

## 🗂️ Model Files in This Folder

| Filename                        | Type                      | Notes                         |
|----------------------------------|----------------------------|-------------------------------|
| `model_pretrained.h5`           | Keras full-precision model| Base model for conversion     |
| `model_quantized.tflite`        | Post-training quantized   | Best for deployment           |
| `model_qat_int8.tflite`         | QAT + full INT8 quantized | Highest accuracy & speed      |
| `model_metadata.json` (opt.)    | Info about model configs  | Layer types, optimizer, etc.  |

---

## 📌 Summary

All models here are optimized for:
- Low size (<100 KB)
- Fast inference (under 100ms)
- Edge deployment on low-power hardware


## 📌 Summary

All models here are optimized for:
- Low size (<100 KB)
- Fast inference (under 100ms)
- Edge deployment on low-power hardware
