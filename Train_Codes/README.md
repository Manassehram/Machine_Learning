# 🧠 Machine Learning Model Training for Smart Blind Stick

This directory contains all the necessary scripts and configurations to train a lightweight and optimized image classification model for terrain recognition. The model is designed to run efficiently on a Raspberry Pi Zero WH using TensorFlow Lite.

---

## 📁 Folder Structure
training/
│
├── train_model.ipynb # Main training notebook (with QAT support)
├── datasets/
│ ├── Train/
│ ├── Validation/
│ └── Test/
├── model/
│ ├── terrain_model.h5
│ ├── terrain_model.tflite
│ └── terrain_model_int8.tflite
├── utils/
│ └── preprocessing.py # Image augmentation and data prep functions
├── class_map.json # Mapping of class indices to labels
└── results/
├── training_plot.png
└── predictions_examples/


---

## ✅ Classes

The model is trained to classify the following terrain types:

- `Grass_Paths`
- `Gravel_Stony`
- `PaveTile`
- `Stairs`
- `Tarmac`

---

## 🔧 Key Features

### `train_model.ipynb`
- End-to-end training pipeline using TensorFlow and Keras.
- Image resizing to 224x168 for Raspberry Pi efficiency.
- Heavy image augmentation using `tf.keras.preprocessing` and `imgaug`.
- Balanced training using **class weights**.
- Adaptive learning rate via `ReduceLROnPlateau`.
- Early stopping and model checkpointing for best validation accuracy.
- Integrated **Quantization-Aware Training (QAT)** for deployment optimization.
- Exports model in three formats:
  - `.h5` — Full Keras model
  - `.tflite` — Standard TFLite model
  - `int8 .tflite` — Fully quantized INT8 model for low-power devices

---

### `preprocessing.py` (in `utils/`)
- Contains:
  - Custom augmentation pipelines
  - Class balancing and distribution visualization
  - Optional letterboxing
  - Dataset preparation helpers

---

## 📊 Evaluation & Visualization

- Accuracy and loss plotted across epochs.
- Test images visualized with predicted probabilities.
- Class-wise performance breakdown available via classification report and confusion matrix.

---

## 🚀 Deployment

Use the `terrain_model_int8.tflite` model for deployment on Raspberry Pi Zero WH with:
- TFLite Interpreter
- Python 3.9+
- OpenCV or PiCamera for image capture

---

## 📦 Dependencies

- TensorFlow 2.x
- NumPy
- scikit-learn
- Matplotlib
- imgaug
- OpenCV (optional for previewing test images)

Install all dependencies using:

```bash
pip install -r requirements.txt
```
##📌 Tips
Ensure your dataset is well balanced across terrain types.
Use tf.data for faster loading on large datasets.
Always validate your INT8 model’s accuracy before deploying.
# most importantly, DO NOT QUANTIZE YOUR MODEL IF YOU CAN HELP IT
