"""
Quick evaluation script to check the accuracy of the trained skin model.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

DATA_DIR = Path("data/ham10000")
METADATA_FILE = DATA_DIR / "HAM10000_metadata.csv"
IMAGE_DIRS = [
    DATA_DIR / "HAM10000_images_part_1",
    DATA_DIR / "HAM10000_images_part_2",
]
MODEL_PATH = Path("ml_models/mobilenetv2_ham10000.h5")
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
VALIDATION_SPLIT = 0.2


def main():
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator  # type: ignore[import-unresolved]
    from sklearn.metrics import classification_report, confusion_matrix

    print("Loading model...")
    model = tf.keras.models.load_model(str(MODEL_PATH))

    print("Loading metadata...")
    df = pd.read_csv(METADATA_FILE)

    image_paths = {}
    for img_dir in IMAGE_DIRS:
        if img_dir.exists():
            for img_file in img_dir.glob("*.jpg"):
                image_paths[img_file.stem] = str(img_file)

    df["filepath"] = df["image_id"].map(image_paths)
    df = df.dropna(subset=["filepath"])
    df["label_idx"] = df["dx"].map({cls: i for i, cls in enumerate(CLASSES)})
    df = df.dropna(subset=["label_idx"])
    df["label_idx"] = df["label_idx"].astype(int)

    val_datagen = ImageDataGenerator(
        preprocessing_function=lambda x: (x / 127.5) - 1.0,
        validation_split=VALIDATION_SPLIT,
    )

    val_gen = val_datagen.flow_from_dataframe(
        dataframe=df,
        x_col="filepath",
        y_col="dx",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        classes=CLASSES,
        subset="validation",
        shuffle=False,
        seed=42,
    )

    print(f"\nEvaluating on {val_gen.n} validation samples...\n")

    # Get overall loss & accuracy
    loss, accuracy = model.evaluate(val_gen, verbose=1)
    print(f"\n{'='*50}")
    print(f"  Validation Loss:     {loss:.4f}")
    print(f"  Validation Accuracy: {accuracy:.4f}  ({accuracy*100:.2f}%)")
    print(f"{'='*50}")

    # Detailed per-class report
    val_gen.reset()
    predictions = model.predict(val_gen, verbose=1)
    y_pred = np.argmax(predictions, axis=1)
    y_true = val_gen.classes

    print("\nClassification Report:\n")
    print(classification_report(y_true, y_pred, target_names=CLASSES, digits=4))


if __name__ == "__main__":
    main()
