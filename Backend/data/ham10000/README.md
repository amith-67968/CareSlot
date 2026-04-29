# HAM10000 Dataset — Skin Lesion Images

This folder should contain the HAM10000 dataset for training the skin disease detection model.

## Download

1. Go to: https://www.kaggle.com/datasets/kmader/skin-cancer-mnist-ham10000
2. Download and extract the following files here:

```
data/ham10000/
├── HAM10000_metadata.csv
├── HAM10000_images_part_1/     (5,000+ .jpg images)
└── HAM10000_images_part_2/     (5,000+ .jpg images)
```

## Training

After placing the dataset:

```bash
cd Backend
python scripts/train_skin_model.py
```

This will produce: `ml_models/skin_mobilenetv2.h5` (~15-20 MB)

## Classes (7)

| Code  | Condition |
|-------|-----------|
| akiec | Actinic Keratoses |
| bcc   | Basal Cell Carcinoma |
| bkl   | Benign Keratosis |
| df    | Dermatofibroma |
| mel   | Melanoma |
| nv    | Melanocytic Nevi |
| vasc  | Vascular Lesion |
