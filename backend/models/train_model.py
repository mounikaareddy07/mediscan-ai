"""
MediScan AI - Model Training Script
Trains real CNN models for medical image classification using Transfer Learning.
Uses MobileNetV2 pre-trained on ImageNet as the base model.
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

# ─── Configuration ───────────────────────────────────────────────────
IMG_SIZE = 150  # Smaller size for faster CPU training
BATCH_SIZE = 16
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, '..', 'datasets')
MODEL_DIR = os.path.join(BASE_DIR)

os.makedirs(DATASET_DIR, exist_ok=True)


def build_model(num_classes, input_shape=(IMG_SIZE, IMG_SIZE, 3)):
    """Build a transfer learning model using MobileNetV2."""
    base_model = MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_shape=input_shape
    )
    # Freeze base model layers
    base_model.trainable = False

    # Add custom classification head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = BatchNormalization()(x)
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.2)(x)
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)
    return model


def train_model(model, train_dir, val_dir, model_name, classes, epochs=10):
    """Train a model on the given dataset."""
    print(f"\n{'='*60}")
    print(f"  Training: {model_name}")
    print(f"  Classes: {classes}")
    print(f"  Epochs: {epochs}")
    print(f"{'='*60}\n")

    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode='nearest'
    )

    val_datagen = ImageDataGenerator(rescale=1./255)

    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=classes,
        shuffle=True
    )

    val_generator = val_datagen.flow_from_directory(
        val_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=classes,
        shuffle=False
    )

    # Compile
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # Callbacks
    callbacks = [
        EarlyStopping(monitor='val_accuracy', patience=3, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', patience=2, factor=0.5, min_lr=1e-6),
        ModelCheckpoint(
            os.path.join(MODEL_DIR, f'{model_name}_best.keras'),
            monitor='val_accuracy', save_best_only=True
        )
    ]

    # Train
    history = model.fit(
        train_generator,
        epochs=epochs,
        validation_data=val_generator,
        callbacks=callbacks,
        verbose=1
    )

    # Save final model
    model_path = os.path.join(MODEL_DIR, f'{model_name}.keras')
    model.save(model_path)

    # Save class mapping
    class_map = {v: k for k, v in train_generator.class_indices.items()}
    with open(os.path.join(MODEL_DIR, f'{model_name}_classes.json'), 'w') as f:
        json.dump(class_map, f, indent=2)

    # Print results
    best_acc = max(history.history.get('val_accuracy', [0]))
    print(f"\n{'='*60}")
    print(f"  {model_name} Training Complete!")
    print(f"  Best Validation Accuracy: {best_acc*100:.1f}%")
    print(f"  Model saved to: {model_path}")
    print(f"{'='*60}\n")

    return history


# ─── Dataset Preparation Functions ───────────────────────────────────

def prepare_chest_xray_dataset():
    """Download and prepare chest X-ray dataset."""
    dataset_path = os.path.join(DATASET_DIR, 'chest_xray')
    if os.path.exists(dataset_path) and os.listdir(dataset_path):
        print("[Dataset] Chest X-ray dataset already exists.")
        return dataset_path

    print("[Dataset] Downloading Chest X-ray dataset...")
    print("[Dataset] Trying Kaggle API...")

    try:
        import kaggle
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(
            'paultimothymooney/chest-xray-pneumonia',
            path=DATASET_DIR,
            unzip=True
        )
        # Reorganize if needed
        src = os.path.join(DATASET_DIR, 'chest_xray')
        if os.path.exists(src):
            print("[Dataset] Chest X-ray dataset downloaded successfully!")
            return src
    except Exception as e:
        print(f"[Dataset] Kaggle download failed: {e}")

    # Fallback: Create synthetic dataset structure with instructions
    print("[Dataset] Creating dataset structure...")
    print("[Dataset] Please download manually from:")
    print("  https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia")
    print(f"  Extract to: {dataset_path}")

    # Create directory structure
    for split in ['train', 'val']:
        for cls in ['NORMAL', 'PNEUMONIA']:
            os.makedirs(os.path.join(dataset_path, split, cls), exist_ok=True)

    return dataset_path


def prepare_brain_tumor_dataset():
    """Download and prepare brain tumor MRI dataset."""
    dataset_path = os.path.join(DATASET_DIR, 'brain_tumor')
    if os.path.exists(dataset_path) and len(os.listdir(dataset_path)) > 0:
        print("[Dataset] Brain tumor dataset already exists.")
        return dataset_path

    print("[Dataset] Downloading Brain Tumor MRI dataset...")
    try:
        import kaggle
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(
            'masoudnickparvar/brain-tumor-mri-dataset',
            path=os.path.join(DATASET_DIR, 'brain_tumor_raw'),
            unzip=True
        )
        # Reorganize
        raw_path = os.path.join(DATASET_DIR, 'brain_tumor_raw')
        if os.path.exists(raw_path):
            _reorganize_brain_dataset(raw_path, dataset_path)
            print("[Dataset] Brain tumor dataset ready!")
            return dataset_path
    except Exception as e:
        print(f"[Dataset] Kaggle download failed: {e}")

    os.makedirs(dataset_path, exist_ok=True)
    for split in ['train', 'val']:
        for cls in ['glioma', 'meningioma', 'notumor', 'pituitary']:
            os.makedirs(os.path.join(dataset_path, split, cls), exist_ok=True)

    return dataset_path


def prepare_skin_lesion_dataset():
    """Download and prepare skin lesion dataset."""
    dataset_path = os.path.join(DATASET_DIR, 'skin_lesion')
    if os.path.exists(dataset_path) and len(os.listdir(dataset_path)) > 0:
        print("[Dataset] Skin lesion dataset already exists.")
        return dataset_path

    print("[Dataset] Downloading Skin Lesion dataset...")
    try:
        import kaggle
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(
            'kmader/skin-cancer-mnist-ham10000',
            path=os.path.join(DATASET_DIR, 'skin_raw'),
            unzip=True
        )
        raw_path = os.path.join(DATASET_DIR, 'skin_raw')
        if os.path.exists(raw_path):
            _reorganize_skin_dataset(raw_path, dataset_path)
            print("[Dataset] Skin lesion dataset ready!")
            return dataset_path
    except Exception as e:
        print(f"[Dataset] Kaggle download failed: {e}")

    os.makedirs(dataset_path, exist_ok=True)
    for split in ['train', 'val']:
        for cls in ['benign', 'malignant']:
            os.makedirs(os.path.join(dataset_path, split, cls), exist_ok=True)

    return dataset_path


def prepare_retinal_dataset():
    """Download and prepare retinal scan dataset."""
    dataset_path = os.path.join(DATASET_DIR, 'retinal')
    if os.path.exists(dataset_path) and len(os.listdir(dataset_path)) > 0:
        print("[Dataset] Retinal dataset already exists.")
        return dataset_path

    print("[Dataset] Downloading Retinal scan dataset...")
    try:
        import kaggle
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(
            'jr2ngb/cataractdataset',
            path=os.path.join(DATASET_DIR, 'retinal_raw'),
            unzip=True
        )
        raw_path = os.path.join(DATASET_DIR, 'retinal_raw')
        if os.path.exists(raw_path):
            _reorganize_retinal_dataset(raw_path, dataset_path)
            print("[Dataset] Retinal dataset ready!")
            return dataset_path
    except Exception as e:
        print(f"[Dataset] Kaggle download failed: {e}")

    os.makedirs(dataset_path, exist_ok=True)
    for split in ['train', 'val']:
        for cls in ['normal', 'cataract']:
            os.makedirs(os.path.join(dataset_path, split, cls), exist_ok=True)

    return dataset_path


# ─── Helper: Reorganize datasets into train/val structure ────────────

def _reorganize_brain_dataset(raw_path, dest_path):
    """Reorganize brain tumor dataset into train/val split."""
    import shutil, random
    classes = ['glioma', 'meningioma', 'notumor', 'pituitary']

    for split in ['train', 'val']:
        for cls in classes:
            os.makedirs(os.path.join(dest_path, split, cls), exist_ok=True)

    # Look for Training and Testing folders
    for folder_name in os.listdir(raw_path):
        folder_path = os.path.join(raw_path, folder_name)
        if os.path.isdir(folder_path):
            if 'train' in folder_name.lower():
                target_split = 'train'
            elif 'test' in folder_name.lower():
                target_split = 'val'
            else:
                continue
            for cls in os.listdir(folder_path):
                cls_path = os.path.join(folder_path, cls)
                if os.path.isdir(cls_path):
                    cls_lower = cls.lower().replace(' ', '')
                    if cls_lower in classes:
                        for img in os.listdir(cls_path):
                            src = os.path.join(cls_path, img)
                            dst = os.path.join(dest_path, target_split, cls_lower, img)
                            if os.path.isfile(src):
                                shutil.copy2(src, dst)


def _reorganize_skin_dataset(raw_path, dest_path):
    """Reorganize skin dataset into train/val with benign/malignant classes."""
    import shutil, random
    import csv

    for split in ['train', 'val']:
        for cls in ['benign', 'malignant']:
            os.makedirs(os.path.join(dest_path, split, cls), exist_ok=True)

    # Read metadata CSV to classify images
    malignant_types = ['mel', 'bcc', 'akiec']  # melanoma, basal cell, actinic keratoses
    benign_types = ['nv', 'bkl', 'df', 'vasc']  # nevus, benign keratosis, dermatofibroma, vascular

    metadata_file = None
    for f in os.listdir(raw_path):
        if f.endswith('.csv') and 'metadata' in f.lower():
            metadata_file = os.path.join(raw_path, f)
            break

    # Find image directories
    img_dirs = []
    for f in os.listdir(raw_path):
        fp = os.path.join(raw_path, f)
        if os.path.isdir(fp) and 'ham' in f.lower():
            img_dirs.append(fp)

    if metadata_file and img_dirs:
        image_classes = {}
        with open(metadata_file, 'r') as csvf:
            reader = csv.DictReader(csvf)
            for row in reader:
                img_id = row.get('image_id', '')
                dx = row.get('dx', '').lower()
                if dx in malignant_types:
                    image_classes[img_id] = 'malignant'
                elif dx in benign_types:
                    image_classes[img_id] = 'benign'

        all_images = []
        for img_dir in img_dirs:
            for img in os.listdir(img_dir):
                if img.endswith(('.jpg', '.png', '.jpeg')):
                    img_id = os.path.splitext(img)[0]
                    if img_id in image_classes:
                        all_images.append((os.path.join(img_dir, img), image_classes[img_id]))

        random.shuffle(all_images)
        split_idx = int(len(all_images) * 0.8)
        for img_path, cls in all_images[:split_idx]:
            shutil.copy2(img_path, os.path.join(dest_path, 'train', cls, os.path.basename(img_path)))
        for img_path, cls in all_images[split_idx:]:
            shutil.copy2(img_path, os.path.join(dest_path, 'val', cls, os.path.basename(img_path)))


def _reorganize_retinal_dataset(raw_path, dest_path):
    """Reorganize retinal dataset into train/val split."""
    import shutil, random

    for split in ['train', 'val']:
        for cls in ['normal', 'cataract']:
            os.makedirs(os.path.join(dest_path, split, cls), exist_ok=True)

    # Walk through and find images
    all_images = {'normal': [], 'cataract': []}
    for root, dirs, files in os.walk(raw_path):
        folder = os.path.basename(root).lower()
        for f in files:
            if f.endswith(('.jpg', '.png', '.jpeg')):
                fpath = os.path.join(root, f)
                if 'normal' in folder:
                    all_images['normal'].append(fpath)
                elif 'cataract' in folder:
                    all_images['cataract'].append(fpath)

    for cls, images in all_images.items():
        random.shuffle(images)
        split_idx = int(len(images) * 0.8)
        for img in images[:split_idx]:
            shutil.copy2(img, os.path.join(dest_path, 'train', cls, os.path.basename(img)))
        for img in images[split_idx:]:
            shutil.copy2(img, os.path.join(dest_path, 'val', cls, os.path.basename(img)))


# ─── Main Training Pipeline ─────────────────────────────────────────

def count_images(directory):
    """Count images in a directory tree."""
    count = 0
    if os.path.exists(directory):
        for root, dirs, files in os.walk(directory):
            count += len([f for f in files if f.endswith(('.jpg', '.jpeg', '.png'))])
    return count


def train_all_models():
    """Train all models sequentially."""
    print("\n" + "=" * 60)
    print("  MediScan AI - Model Training Pipeline")
    print("  Using MobileNetV2 Transfer Learning")
    print("=" * 60)

    results = {}

    # ── 1. Chest X-ray Model ────────────────────────────────────────
    print("\n[1/4] Preparing Chest X-ray dataset...")
    chest_path = prepare_chest_xray_dataset()
    train_dir = os.path.join(chest_path, 'train')
    val_dir = os.path.join(chest_path, 'val')

    if os.path.exists(val_dir) and count_images(val_dir) < 10:
        val_dir = os.path.join(chest_path, 'test')  # Some datasets use 'test' instead of 'val'

    train_count = count_images(train_dir)
    val_count = count_images(val_dir)

    if train_count >= 10:
        print(f"[Dataset] Train: {train_count} images, Val: {val_count} images")
        classes = sorted(os.listdir(train_dir))
        classes = [c for c in classes if os.path.isdir(os.path.join(train_dir, c))]
        model = build_model(len(classes))
        history = train_model(model, train_dir, val_dir, 'chest_xray_model', classes, epochs=8)
        results['chest_xray'] = max(history.history.get('val_accuracy', [0]))
    else:
        print(f"[Skip] Not enough images ({train_count}). Download the dataset first.")

    # ── 2. Brain Tumor Model ────────────────────────────────────────
    print("\n[2/4] Preparing Brain Tumor dataset...")
    brain_path = prepare_brain_tumor_dataset()
    train_dir = os.path.join(brain_path, 'train')
    val_dir = os.path.join(brain_path, 'val')

    if os.path.exists(val_dir) and count_images(val_dir) < 10:
        val_dir = os.path.join(brain_path, 'test')

    train_count = count_images(train_dir)
    val_count = count_images(val_dir)

    if train_count >= 10:
        print(f"[Dataset] Train: {train_count} images, Val: {val_count} images")
        classes = sorted(os.listdir(train_dir))
        classes = [c for c in classes if os.path.isdir(os.path.join(train_dir, c))]
        model = build_model(len(classes))
        history = train_model(model, train_dir, val_dir, 'brain_tumor_model', classes, epochs=8)
        results['brain_tumor'] = max(history.history.get('val_accuracy', [0]))
    else:
        print(f"[Skip] Not enough images ({train_count}). Download the dataset first.")

    # ── 3. Skin Lesion Model ────────────────────────────────────────
    print("\n[3/4] Preparing Skin Lesion dataset...")
    skin_path = prepare_skin_lesion_dataset()
    train_dir = os.path.join(skin_path, 'train')
    val_dir = os.path.join(skin_path, 'val')

    train_count = count_images(train_dir)
    val_count = count_images(val_dir)

    if train_count >= 10:
        print(f"[Dataset] Train: {train_count} images, Val: {val_count} images")
        classes = sorted(os.listdir(train_dir))
        classes = [c for c in classes if os.path.isdir(os.path.join(train_dir, c))]
        model = build_model(len(classes))
        history = train_model(model, train_dir, val_dir, 'skin_lesion_model', classes, epochs=8)
        results['skin_lesion'] = max(history.history.get('val_accuracy', [0]))
    else:
        print(f"[Skip] Not enough images ({train_count}). Download the dataset first.")

    # ── 4. Retinal Scan Model ───────────────────────────────────────
    print("\n[4/4] Preparing Retinal Scan dataset...")
    retinal_path = prepare_retinal_dataset()
    train_dir = os.path.join(retinal_path, 'train')
    val_dir = os.path.join(retinal_path, 'val')

    train_count = count_images(train_dir)
    val_count = count_images(val_dir)

    if train_count >= 10:
        print(f"[Dataset] Train: {train_count} images, Val: {val_count} images")
        classes = sorted(os.listdir(train_dir))
        classes = [c for c in classes if os.path.isdir(os.path.join(train_dir, c))]
        model = build_model(len(classes))
        history = train_model(model, train_dir, val_dir, 'retinal_model', classes, epochs=8)
        results['retinal'] = max(history.history.get('val_accuracy', [0]))
    else:
        print(f"[Skip] Not enough images ({train_count}). Download the dataset first.")

    # ── Summary ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Training Summary")
    print("=" * 60)
    for name, acc in results.items():
        print(f"  {name:20s} : {acc*100:.1f}% accuracy")
    if not results:
        print("  No models trained. Please download datasets first.")
    print("=" * 60)


if __name__ == '__main__':
    train_all_models()
