import sys
import numpy as np
import tensorflow as tf
import os
import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image

app = FastAPI(title="AI Image Detection API")

MODEL_PATH = "/content/MobileNetV2_finetuned_model(0.95 loss 0.11).keras"
model = None

def load_model_globally(model_path):
    global model
    if not os.path.exists(model_path):
        print(f"Warning: Model file not found at {model_path}")
        return False
    print(f"Loading model from {model_path}...")
    try:
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully.")
        return True
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    # Load the model once when the API starts
    load_model_globally(MODEL_PATH)

def process_and_predict(img, local_model):
    input_shape = local_model.input_shape
    if input_shape is None or input_shape[1] is None:
        target_size = (224, 224) 
    else:
        target_size = (input_shape[1], input_shape[2])
        
    img = img.resize(target_size)
    img_array = tf.keras.utils.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
    
    prediction = local_model.predict(img_array)
    return prediction

@app.post("/detect")
async def detect_image_api(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model is not loaded or not found.")
        
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")
        
    try:
        prediction = process_and_predict(img, model)
        
        result = {
            "raw_output": prediction.tolist(),
            "is_ai_generated": False,
            "confidence": 0.0,
            "message": ""
        }
        
        if prediction.shape[-1] == 1:
            prob = float(prediction[0][0])
            result["confidence"] = prob
            if prob > 0.5:
                result["is_ai_generated"] = True
                result["message"] = "Likely Class 1 (AI Generated)"
            else:
                result["is_ai_generated"] = False
                result["message"] = "Likely Class 0 (Real/Human)"
                
        elif prediction.shape[-1] == 2:
            class_idx = int(np.argmax(prediction[0]))
            result["confidence"] = float(prediction[0][class_idx])
            if class_idx == 0:
                result["is_ai_generated"] = False
                result["message"] = "Prediction: Class 0 (Real/Human)"
            else:
                result["is_ai_generated"] = True
                result["message"] = "Prediction: Class 1 (AI Generated)"
        else:
            class_idx = int(np.argmax(prediction[0]))
            result["confidence"] = float(prediction[0][class_idx])
            result["message"] = f"Predicted class index: {class_idx}"
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")


def detect_image(image_path, model_path):
    """Original standalone testing function preserved"""
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return
        
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return

    print(f"Loading model from {model_path}...")
    local_model = tf.keras.models.load_model(model_path)
    
    try:
        img = Image.open(image_path).convert('RGB')
    except Exception as e:
        print(f"Error loading image: {e}")
        return
        
    print("Running inference...")
    prediction = process_and_predict(img, local_model)
    
    print("\n" + "=" * 40)
    print("PREDICTION RESULTS")
    print("=" * 40)
    print(f"Raw model output: {prediction}")
    
    if prediction.shape[-1] == 1:
        prob = prediction[0][0]
        if prob > 0.5:
            print("=> Likely Class 1 (e.g., AI Generated)")
        else:
            print("=> Likely Class 0 (e.g., Real/Human)")
            
    elif prediction.shape[-1] == 2:
        class_idx = np.argmax(prediction[0])
        print(f"Class probabilities: {prediction[0]}")
        
        if class_idx == 0:
            print("=> Prediction: Class 0 (e.g., Real/Human)")
        else:
            print("=> Prediction: Class 1 (e.g., AI Generated)")
    else:
        class_idx = np.argmax(prediction[0])
        print(f"Predicted class index: {class_idx}")
        
    print("=" * 40)
    print("Note: Please verify the class mapping (0 vs 1) based on your training dataset.")

if __name__ == "__main__":
    import uvicorn
    
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        test_image_path = "/content/test_culture_kabyle copy.jpeg"
        detect_image(test_image_path, MODEL_PATH)
    else:
        print("Starting FastAPI server...")
        uvicorn.run("detect_ai_image:app", host="0.0.0.0", port=8000, reload=True)
