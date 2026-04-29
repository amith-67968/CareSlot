"""
CareSlot — Skin Disease Detection Model
MobileNetV2 fine-tuned on HAM10000 dataset for skin lesion classification.
"""

import numpy as np
from typing import Dict, Any
from app.config import get_settings
import logging
import os

logger = logging.getLogger(__name__)

_model = None

SKIN_CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]

SKIN_CLASS_NAMES = {
    "akiec": "Actinic Keratoses / Intraepithelial Carcinoma",
    "bcc": "Basal Cell Carcinoma",
    "bkl": "Benign Keratosis",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic Nevi (Mole)",
    "vasc": "Vascular Lesion",
}

SKIN_CLASS_SEVERITY = {
    "akiec": "severe", "bcc": "severe", "bkl": "mild",
    "df": "mild", "mel": "severe", "nv": "mild", "vasc": "moderate",
}

SKIN_CLASS_URGENCY = {
    "akiec": True, "bcc": True, "bkl": False,
    "df": False, "mel": True, "nv": False, "vasc": False,
}


def load_skin_model():
    """Load MobileNetV2 model fine-tuned on HAM10000."""
    global _model
    if _model is not None:
        return _model

    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2  # type: ignore[import-untyped]
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout  # type: ignore[import-untyped]
    from tensorflow.keras.models import Model  # type: ignore[import-untyped]

    settings = get_settings()
    model_path = settings.SKIN_MODEL_PATH

    if os.path.exists(model_path):
        logger.info(f"Loading fine-tuned skin model from: {model_path}")
        _model = tf.keras.models.load_model(model_path)
    else:
        logger.warning(f"Fine-tuned model not found at {model_path}. Creating base MobileNetV2.")
        base_model = MobileNetV2(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
        base_model.trainable = False
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(256, activation="relu")(x)
        x = Dropout(0.5)(x)
        x = Dense(128, activation="relu")(x)
        x = Dropout(0.3)(x)
        predictions = Dense(len(SKIN_CLASSES), activation="softmax")(x)
        _model = Model(inputs=base_model.input, outputs=predictions)
        os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)

    logger.info("Skin disease model loaded successfully")
    return _model


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Preprocess an image for MobileNetV2 inference."""
    from PIL import Image
    import io
    import tensorflow as tf

    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize((224, 224), Image.Resampling.LANCZOS)
    img_array = np.array(image, dtype=np.float32)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array


def predict_skin_disease(image_bytes: bytes) -> Dict[str, Any]:
    """Run skin disease prediction on an uploaded image."""
    model = load_skin_model()
    img_array = preprocess_image(image_bytes)
    predictions = model.predict(img_array, verbose=0)
    probs = predictions[0]

    top_idx = int(np.argmax(probs))
    predicted_class = SKIN_CLASSES[top_idx]
    confidence = float(probs[top_idx])

    all_predictions = {cls: float(probs[i]) for i, cls in enumerate(SKIN_CLASSES)}
    all_predictions = dict(sorted(all_predictions.items(), key=lambda x: x[1], reverse=True))

    return {
        "predicted_class": predicted_class,
        "predicted_condition": SKIN_CLASS_NAMES[predicted_class],
        "confidence": confidence,
        "severity": SKIN_CLASS_SEVERITY[predicted_class],
        "is_urgent": SKIN_CLASS_URGENCY[predicted_class],
        "all_predictions": all_predictions,
    }
