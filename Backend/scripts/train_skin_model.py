"""
CareSlot -- MobileNetV2 Fine-Tuning on HAM10000
=================================================

This script fine-tunes a MobileNetV2 model on the HAM10000 skin lesion dataset
for 7-class skin disease classification.

HAM10000 Classes:
    akiec  - Actinic keratoses / Bowen's disease
    bcc    - Basal cell carcinoma
    bkl    - Benign keratosis
    df     - Dermatofibroma
    mel    - Melanoma
    nv     - Melanocytic nevi (moles)
    vasc   - Vascular lesions

Prerequisites:
    1. Download HAM10000 dataset from:
       https://www.kaggle.com/datasets/kmader/skin-cancer-mnist-ham10000
    2. Place files:
       - HAM10000_metadata.csv
       - HAM10000_images_part_1/ (folder with .jpg images)
       - HAM10000_images_part_2/ (folder with .jpg images)
       into: Backend/data/ham10000/

Usage:
    cd Backend
    python scripts/train_skin_model.py

Output:
    Trained model saved to: ml_models/skin_mobilenetv2.h5
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

# -- Configuration ---------------------------------------------------------------

DATA_DIR = Path("data/ham10000")
METADATA_FILE = DATA_DIR / "HAM10000_metadata.csv"
IMAGE_DIRS = [
    DATA_DIR / "HAM10000_images_part_1",
    DATA_DIR / "HAM10000_images_part_2",
]
OUTPUT_MODEL_PATH = Path("ml_models/mobilenetv2_ham10000.h5")

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_PHASE1 = 10   # Train only the top layers
EPOCHS_PHASE2 = 15   # Fine-tune with unfrozen layers
LEARNING_RATE_PHASE1 = 1e-3
LEARNING_RATE_PHASE2 = 1e-5
VALIDATION_SPLIT = 0.2

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
NUM_CLASSES = len(CLASSES)


def check_prerequisites():
    """Verify dataset files exist."""
    if not METADATA_FILE.exists():
        print("[ERROR] HAM10000_metadata.csv not found!")
        print(f"   Expected at: {METADATA_FILE.resolve()}")
        print()
        print("Download the HAM10000 dataset:")
        print("   https://www.kaggle.com/datasets/kmader/skin-cancer-mnist-ham10000")
        print()
        print("Expected folder structure:")
        print("   Backend/data/ham10000/")
        print("   |-- HAM10000_metadata.csv")
        print("   |-- HAM10000_images_part_1/  (folder with .jpg images)")
        print("   +-- HAM10000_images_part_2/  (folder with .jpg images)")
        sys.exit(1)

    found_dirs = [d for d in IMAGE_DIRS if d.exists()]
    if not found_dirs:
        print("[ERROR] No image directories found!")
        print("   Expected HAM10000_images_part_1/ and/or HAM10000_images_part_2/")
        sys.exit(1)

    print(f"[OK] Metadata file: {METADATA_FILE}")
    for d in found_dirs:
        count = len(list(d.glob("*.jpg")))
        print(f"[OK] Image dir: {d.name} ({count} images)")


def load_metadata():
    """Load and prepare the HAM10000 metadata."""
    df = pd.read_csv(METADATA_FILE)
    print(f"\nTotal samples in metadata: {len(df)}")
    print(f"   Columns: {list(df.columns)}")

    # Build image_id -> file path mapping
    image_paths = {}
    for img_dir in IMAGE_DIRS:
        if img_dir.exists():
            for img_file in img_dir.glob("*.jpg"):
                image_paths[img_file.stem] = str(img_file)

    # Map image_id to file path
    df["filepath"] = df["image_id"].map(image_paths)
    df = df.dropna(subset=["filepath"])
    print(f"   Matched images: {len(df)}")

    # Encode labels
    df["label_idx"] = df["dx"].map({cls: i for i, cls in enumerate(CLASSES)})
    df = df.dropna(subset=["label_idx"])
    df["label_idx"] = df["label_idx"].astype(int)

    # Show class distribution
    print("\nClass Distribution:")
    for cls in CLASSES:
        count = len(df[df["dx"] == cls])
        print(f"   {cls:6s} => {count:5d} samples")

    return df


def create_data_generators(df):
    """Create training and validation data generators with augmentation."""
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        preprocessing_function=lambda x: (x / 127.5) - 1.0,  # MobileNetV2 preprocessing
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        vertical_flip=True,
        fill_mode="nearest",
        validation_split=VALIDATION_SPLIT,
    )

    # No augmentation for validation
    val_datagen = ImageDataGenerator(
        preprocessing_function=lambda x: (x / 127.5) - 1.0,
        validation_split=VALIDATION_SPLIT,
    )

    train_gen = train_datagen.flow_from_dataframe(
        dataframe=df,
        x_col="filepath",
        y_col="dx",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        classes=CLASSES,
        subset="training",
        shuffle=True,
        seed=42,
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

    return train_gen, val_gen


def compute_class_weights(df):
    """Compute class weights to handle imbalanced dataset."""
    from sklearn.utils.class_weight import compute_class_weight

    labels = df["label_idx"].values
    weights = compute_class_weight("balanced", classes=np.unique(labels), y=labels)
    class_weight_dict = {i: w for i, w in enumerate(weights)}
    print("\nClass Weights (handling imbalance):")
    for i, cls in enumerate(CLASSES):
        print(f"   {cls:6s} => {class_weight_dict[i]:.3f}")
    return class_weight_dict


def build_model():
    """Build MobileNetV2 model with custom classification head."""
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
    from tensorflow.keras.models import Model

    print("\nBuilding MobileNetV2 model...")

    # Load MobileNetV2 backbone (pre-trained on ImageNet)
    base_model = MobileNetV2(
        weights="imagenet",
        include_top=False,
        input_shape=(224, 224, 3),
    )
    base_model.trainable = False  # Freeze for Phase 1

    # Custom classification head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.5)(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.3)(x)
    predictions = Dense(NUM_CLASSES, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=predictions)

    print(f"   Total params: {model.count_params():,}")
    trainable = sum(
        tf.keras.backend.count_params(w) for w in model.trainable_weights
    )
    print(f"   Trainable params: {trainable:,}")

    return model, base_model


def train_phase1(model, train_gen, val_gen, class_weights):
    """Phase 1: Train only the classification head (base frozen)."""
    import tensorflow as tf

    print("\n" + "=" * 60)
    print("PHASE 1: Training classification head (base frozen)")
    print("=" * 60)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE_PHASE1),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6
        ),
    ]

    history1 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_PHASE1,
        class_weight=class_weights,
        callbacks=callbacks,
    )
    return history1


def train_phase2(model, base_model, train_gen, val_gen, class_weights):
    """Phase 2: Fine-tune -- unfreeze last 30 layers of MobileNetV2."""
    import tensorflow as tf

    print("\n" + "=" * 60)
    print("PHASE 2: Fine-tuning (unfreezing last 30 layers)")
    print("=" * 60)

    # Unfreeze the last 30 layers of the base model
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    trainable = sum(
        tf.keras.backend.count_params(w) for w in model.trainable_weights
    )
    print(f"   Trainable params after unfreeze: {trainable:,}")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE_PHASE2),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-7
        ),
    ]

    history2 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_PHASE2,
        class_weight=class_weights,
        callbacks=callbacks,
    )
    return history2


def evaluate_model(model, val_gen):
    """Print classification report on validation data."""
    from sklearn.metrics import classification_report

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    val_gen.reset()
    predictions = model.predict(val_gen, verbose=1)
    y_pred = np.argmax(predictions, axis=1)
    y_true = val_gen.classes

    report = classification_report(y_true, y_pred, target_names=CLASSES, digits=4)
    print(report)


def save_model(model):
    """Save the trained model."""
    OUTPUT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(OUTPUT_MODEL_PATH))
    size_mb = OUTPUT_MODEL_PATH.stat().st_size / (1024 * 1024)
    print(f"\n[SAVED] Model saved to: {OUTPUT_MODEL_PATH}")
    print(f"   Size: {size_mb:.1f} MB")


def main():
    print("=" * 60)
    print("CareSlot -- MobileNetV2 Skin Disease Model Training")
    print("   Fine-tuning on HAM10000 (7-class classification)")
    print("=" * 60)

    # Step 0: Check prerequisites
    check_prerequisites()

    # Step 1: Load metadata
    df = load_metadata()

    # Step 2: Create data generators
    train_gen, val_gen = create_data_generators(df)
    print(f"\n   Training samples:   {train_gen.n}")
    print(f"   Validation samples: {val_gen.n}")

    # Step 3: Compute class weights
    class_weights = compute_class_weights(df)

    # Step 4: Build model
    model, base_model = build_model()

    # Step 5: Phase 1 -- Train head
    train_phase1(model, train_gen, val_gen, class_weights)

    # Step 6: Phase 2 -- Fine-tune
    train_phase2(model, base_model, train_gen, val_gen, class_weights)

    # Step 7: Evaluate
    evaluate_model(model, val_gen)

    # Step 8: Save
    save_model(model)

    print("\n" + "=" * 60)
    print("[DONE] Training complete!")
    print(f"   Model: {OUTPUT_MODEL_PATH}")
    print("   Use this model by setting SKIN_MODEL_PATH in .env")
    print("=" * 60)


if __name__ == "__main__":
    main()
