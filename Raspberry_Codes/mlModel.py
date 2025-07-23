from flask import Flask, request
import os
from datetime import datetime
import uuid
import numpy as np
from PIL import Image
import tflite_micro_runtime.interpreter as tflite
import math

# Initialize Flask app
app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = '/home/alpha/Desktop/project/images'
MODEL_PATH = '/home/alpha/Desktop/project/second.tflite'
CLASS_NAMES = ['Grass_Paths', 'Gravel_Stony', 'PaveTile', 'Stairs', 'Tarmac']

# Ensure image directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Model Loading ---
try:
    interpreter = tflite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    EXPECTED_HEIGHT = input_details[0]['shape'][1]
    EXPECTED_WIDTH = input_details[0]['shape'][2]
    INPUT_DTYPE = input_details[0]['dtype']
    INPUT_QUANT_SCALE = input_details[0]['quantization'][0]
    INPUT_QUANT_ZERO_POINT = input_details[0]['quantization'][1]

    OUTPUT_DTYPE = output_details[0]['dtype']
    OUTPUT_QUANT_SCALE = output_details[0]['quantization'][0]
    OUTPUT_QUANT_ZERO_POINT = output_details[0]['quantization'][1]

    print(f"? TFLite model loaded from: {MODEL_PATH}")
    print(f"   Input shape: {input_details[0]['shape']}, dtype: {INPUT_DTYPE}")
    print(f"   Input quantization: scale={INPUT_QUANT_SCALE}, zero_point={INPUT_QUANT_ZERO_POINT}")
    print(f"   Output shape: {output_details[0]['shape']}, dtype: {OUTPUT_DTYPE}")
    print(f"   Output quantization: scale={OUTPUT_QUANT_SCALE}, zero_point={OUTPUT_QUANT_ZERO_POINT}")

except Exception as e:
    print(f"? Error loading TFLite model: {e}")
    import sys
    sys.exit(f"Failed to load model. Exiting. Error: {e}")

# --- Helper Function for Inference ---
def run_inference(image_path):
    print(f"Running inference on {image_path}...")

    img = Image.open(image_path).convert('RGB')
    img_resized = img.resize((EXPECTED_WIDTH, EXPECTED_HEIGHT))
    img_array = np.asarray(img_resized).astype(np.float32) / 255.0

    if INPUT_QUANT_SCALE != 0:
        input_data_processed = (img_array / INPUT_QUANT_SCALE + INPUT_QUANT_ZERO_POINT)
    else:
        input_data_processed = img_array

    input_data_processed = input_data_processed.astype(INPUT_DTYPE)
    input_data_processed = np.expand_dims(input_data_processed, axis=0)

    interpreter.set_tensor(input_details[0]['index'], input_data_processed)
    interpreter.invoke()

    raw_output = interpreter.get_tensor(output_details[0]['index'])[0].astype(np.float32)
    if OUTPUT_QUANT_SCALE != 0 or OUTPUT_QUANT_ZERO_POINT != 0:
        dequantized_output = (raw_output - OUTPUT_QUANT_ZERO_POINT) * OUTPUT_QUANT_SCALE
    else:
        dequantized_output = raw_output

    exp_output = np.exp(dequantized_output - np.max(dequantized_output))
    probabilities = exp_output / np.sum(exp_output)

    prediction_index = np.argmax(probabilities)
    confidence = probabilities[prediction_index] * 100
    label = CLASS_NAMES[prediction_index] if prediction_index < len(CLASS_NAMES) else f"Unknown Class Index: {prediction_index}"

    return label, confidence

# --- Flask Routes ---
@app.route('/upload', methods=['POST'])
def upload_image():
    if not request.data:
        print("? No image data found in request")
        return 'No image data found in request', 400

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        with open(filepath, 'wb') as f:
            f.write(request.data)
        print(f"? Image saved to {filepath}")

        label, confidence = run_inference(filepath)
        print(f"?? Detected terrain: {label} (Confidence: {confidence:.2f}%)")
        return f'Detected terrain: {label} (Confidence: {confidence:.2f}%)', 200

    except Exception as e:
        print(f"? Error processing image or during inference: {e}")
        return f'Error during image processing or inference: {e}', 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"?? Image {filename} deleted after analysis")

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

